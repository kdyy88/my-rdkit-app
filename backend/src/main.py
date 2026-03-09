"""AG2 Agent entry point coordinating MCP with users."""

import asyncio
import json
import os
import re
import shlex
import sys
from typing import Any

from autogen import AssistantAgent, UserProxyAgent
from autogen.llm_config import LLMConfig
from autogen.mcp import create_toolkit
from autogen.mcp.mcp_client import MCPClientSessionManager, StdioConfig
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rdkit import Chem
from rdkit.Chem import AllChem, Crippen, DataStructs, Descriptors, Lipinski

try:
    from chemistry import fetch_pubchem_xlogp, name_to_smiles, smiles_to_base64
    from models import ChatRequest, ChatResponse, MolecularProperties, MoleculeResponse, MoleculeResponseSchema, MoleculeVisualization, ToolResult
except ImportError:
    from .chemistry import fetch_pubchem_xlogp, name_to_smiles, smiles_to_base64
    from .models import ChatRequest, ChatResponse, MolecularProperties, MoleculeResponse, MoleculeResponseSchema, MoleculeVisualization, ToolResult


app = FastAPI(title="RDKit AI Platform API")

# Auto-load backend/.env for uvicorn runs without manual `source .env`
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_BACKEND_ROOT, ".env"), override=False)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

def _build_llm_config() -> LLMConfig:
    """Build AG2 LLM config for structured output."""
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://www.dmxapi.cn/v1/responses")
    if base_url.rstrip("/").endswith("/responses"):
        base_url = base_url.rstrip("/")[: -len("/responses")]

    return LLMConfig(
        {
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
        },
        temperature=0.2,
        max_tokens=1200,
        timeout=25,
        response_format=MoleculeResponseSchema,
    )


def _extract_json(content: str) -> dict[str, Any]:
    """Extract JSON object from model content."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start : end + 1])
        raise


def _fallback_response(message: str) -> MoleculeResponse:
    """Fallback deterministic response when AG2 parsing fails."""
    raw = message.strip()
    candidate = name_to_smiles(raw)
    if not candidate:
        # Try Chinese phrase chunks first (for prompts like "帮我画出阿司匹林并标出乙酰基")
        zh_chunks = [x for x in re.split(r"[，。！？、\s并且和与对将把的地得了吧啊呀呢]", raw) if x]
        for chunk in sorted(zh_chunks, key=len, reverse=True):
            converted = name_to_smiles(chunk)
            if converted:
                candidate = converted
                break
    if not candidate:
        token_matches = re.findall(r"[A-Za-z0-9@+\-\[\]\(\)=#/\\]+", raw)
        token_candidates = [t.strip("()[]{}") for t in token_matches if t.strip("()[]{}")]
        # 1) prefer exact valid SMILES token
        for token in token_candidates:
            if Chem.MolFromSmiles(token):
                candidate = token
                break
        # 2) fallback to compound name lookup token-by-token
        if not candidate:
            for token in token_candidates:
                converted = name_to_smiles(token)
                if converted:
                    candidate = converted
                    break
        if not candidate:
            candidate = raw
    mol = Chem.MolFromSmiles(candidate)

    if not mol:
        return MoleculeResponse(
            compound_name=message,
            smiles="",
            summary="无法解析该输入为有效分子。请提供化合物名称或有效 SMILES。",
            tool_calls=[
                ToolResult(
                    tool_name="search_name_to_smiles",
                    success=False,
                    data={},
                    error="Invalid compound name/SMILES",
                )
            ],
        )

    rdkit_clogp = Crippen.MolLogP(mol)
    pubchem_xlogp = fetch_pubchem_xlogp(candidate)
    preferred_logp = pubchem_xlogp if pubchem_xlogp is not None else rdkit_clogp
    preferred_source = "PubChem XLogP" if pubchem_xlogp is not None else "RDKit Crippen.MolLogP"

    return MoleculeResponse(
        compound_name=message,
        smiles=candidate,
        properties=MolecularProperties(
            molecular_weight=round(Descriptors.MolWt(mol), 3),
            logp=round(preferred_logp, 3),
            logp_source=preferred_source,
            hydrogen_bond_donors=Lipinski.NumHDonors(mol),
            hydrogen_bond_acceptors=Lipinski.NumHAcceptors(mol),
            formula=Chem.rdMolDescriptors.CalcMolFormula(mol),
        ),
        visualization=MoleculeVisualization(
            image_base64=smiles_to_base64(candidate) or "",
            width=300,
            height=300,
        ),
        summary=f"已完成 {candidate} 的基础化学分析。",
        tool_calls=[
            ToolResult(tool_name="search_name_to_smiles", success=True, data={"input": message, "smiles": candidate}),
            ToolResult(tool_name="calculate_properties", success=True, data={"smiles": candidate}),
            ToolResult(tool_name="generate_molecule_viz", success=True, data={"smiles": candidate}),
        ],
    )


def run_ag2_with_mcp(message: str, max_turns: int = 5) -> ChatResponse:
    """Run AG2 `AssistantAgent` + `UserProxyAgent` with MCP-enabled llm_config."""
    if not os.getenv("OPENAI_API_KEY"):
        fallback = _fallback_response(message)
        fallback.tool_calls.append(
            ToolResult(
                tool_name="ag2_disabled_no_api_key",
                success=False,
                data={},
                error="OPENAI_API_KEY is not configured; returned local fallback result.",
            )
        )
        return ChatResponse(result=fallback, conversation_history=[], tokens_used=None)

    try:
        llm_config = _build_llm_config()
        assistant = AssistantAgent(
            name="chemistry_assistant",
            llm_config=llm_config,
            system_message=(
                "你是 Chemical Planner（化学专家）。"
                "当用户输入模糊意图时，必须先理解语义并拆解任务，不依赖硬编码词表。"
                "优先工具顺序：search_smiles_by_name -> rdkit_2d_render -> calculate_properties。"
                "如果用户要求高亮官能团，先在总结中说明高亮意图是否可执行。"
                "不要输出推理草稿。最终只输出严格 JSON，且字段必须符合 MoleculeResponse。"
            ),
        )
        user_proxy = UserProxyAgent(
            name="user_proxy",
            human_input_mode="NEVER",
            code_execution_config=False,
        )
    except Exception as exc:
        fallback = _fallback_response(message)
        fallback.tool_calls.append(
            ToolResult(
                tool_name="ag2_init",
                success=False,
                data={},
                error=str(exc),
            )
        )
        return ChatResponse(result=fallback, conversation_history=[], tokens_used=None)

    # AG2 当前版本不支持在 llm_config 中直接传 mcp_config/mcp_servers。
    # 使用 MCP 客户端会话 + toolkit 的官方路径挂载本地 MCP tools。
    try:
        default_script = os.path.join(os.path.dirname(__file__), "mcp_server.py")
        mcp_command = os.getenv("MCP_SERVER_COMMAND", sys.executable)
        mcp_args = shlex.split(os.getenv("MCP_SERVER_ARGS", default_script))
        mcp_cwd = os.getenv("MCP_SERVER_CWD", os.path.dirname(__file__))

        async def _chat_with_mcp() -> Any:
            manager = MCPClientSessionManager()
            cfg = StdioConfig(
                server_name="rdkit_tools",
                command=mcp_command,
                args=mcp_args,
                working_dir=mcp_cwd,
            )
            async with manager.open_session(cfg) as session:
                toolkit = await create_toolkit(session=session, use_mcp_tools=True, use_mcp_resources=False)
                toolkit.register_for_llm(assistant)
                toolkit.register_for_execution(user_proxy)
                return await asyncio.to_thread(
                    user_proxy.initiate_chat,
                    assistant,
                    message=message,
                    max_turns=max_turns,
                    summary_method="last_msg",
                )

        chat_result = asyncio.run(_chat_with_mcp())
    except Exception as exc:
        fallback = _fallback_response(message)
        fallback.tool_calls.append(
            ToolResult(
                tool_name="ag2_initiate_chat",
                success=False,
                data={},
                error=str(exc),
            )
        )
        return ChatResponse(result=fallback, conversation_history=[], tokens_used=None)

    try:
        payload = _extract_json(chat_result.summary)
        structured_llm = MoleculeResponseSchema.model_validate(payload)
        structured = MoleculeResponse(
            compound_name=structured_llm.compound_name,
            smiles=structured_llm.smiles,
            properties=structured_llm.properties,
            visualization=structured_llm.visualization,
            summary=structured_llm.summary,
            tool_calls=[
                ToolResult(
                    tool_name="ag2_structured_output",
                    success=True,
                    data={"source": "assistant_response_format"},
                )
            ],
        )
    except Exception:
        structured = _fallback_response(message)

    return ChatResponse(
        result=structured,
        conversation_history=[
            {"role": item.get("role", "assistant"), "content": str(item.get("content", ""))}
            for item in chat_result.chat_history
        ],
        tokens_used=None,
    )


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"status": "ok", "service": "RDKit AI Platform"}


@app.get("/calc")
def calculate_molecule(smiles: str = "CCO"):
    """
    Calculate molecular properties for a given SMILES string.
    
    Args:
        smiles: SMILES string representation of a molecule
        
    Returns:
        Dictionary containing molecular properties
    """
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return {"error": "SMILES 解析失败"}

    rdkit_clogp = Crippen.MolLogP(mol)
    pubchem_xlogp = fetch_pubchem_xlogp(smiles)
    preferred_logp = pubchem_xlogp if pubchem_xlogp is not None else rdkit_clogp
    preferred_source = "PubChem XLogP" if pubchem_xlogp is not None else "RDKit Crippen.MolLogP"

    return {
        "smiles": smiles,
        "mw": round(Descriptors.MolWt(mol), 3),
        "logp": preferred_logp,
        "logp_source": preferred_source,
        "hbd": Lipinski.NumHDonors(mol),
        "hba": Lipinski.NumHAcceptors(mol),
        "formula": Chem.rdMolDescriptors.CalcMolFormula(mol),
    }


@app.get("/similarity")
def get_similarity(smi1: str, smi2: str):
    """
    Calculate Tanimoto similarity between two molecules.
    
    Args:
        smi1: SMILES string of first molecule
        smi2: SMILES string of second molecule
        
    Returns:
        Dictionary containing similarity metrics
    """
    m1 = Chem.MolFromSmiles(smi1)
    m2 = Chem.MolFromSmiles(smi2)
    
    if not m1 or not m2:
        return {"error": "输入的 SMILES 无效"}
    
    fp1 = AllChem.GetMorganFingerprintAsBitVect(m1, 2, nBits=2048)
    fp2 = AllChem.GetMorganFingerprintAsBitVect(m2, 2, nBits=2048)
    
    score = DataStructs.TanimotoSimilarity(fp1, fp2)
    
    return {
        "score": round(score, 4),
        "percentage": f"{round(score * 100, 2)}%",
        "status": "High Similarity" if score > 0.8 else "Common" if score > 0.5 else "Low Similarity"
    }


@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat endpoint that coordinates AG2 agent with MCP tools.
    
    Args:
        request: ChatRequest containing message and max_turns
        
    Returns:
        Agent's response with tool results
    """
    endpoint_timeout = int(os.getenv("CHAT_ENDPOINT_TIMEOUT", "40"))
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(run_ag2_with_mcp, request.message, request.max_turns),
            timeout=endpoint_timeout,
        )
    except asyncio.TimeoutError:
        fallback = _fallback_response(request.message)
        fallback.tool_calls.append(
            ToolResult(
                tool_name="chat_endpoint_timeout",
                success=False,
                data={"timeout_seconds": endpoint_timeout},
                error="AG2/MCP execution timed out at API boundary; returned fallback result.",
            )
        )
        return ChatResponse(result=fallback, conversation_history=[], tokens_used=None)
