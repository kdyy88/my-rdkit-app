"""Two-Agent AG2 orchestration: Natural language -> MCP tools -> structured JSON.

Run:
  cd backend/src
  uv run python3 ag2_two_agent.py "帮我画出阿司匹林并简要说明"
"""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import sys
from typing import Any

from autogen import AssistantAgent, UserProxyAgent
from autogen.llm_config import LLMConfig
from autogen.mcp import create_toolkit
from autogen.mcp.mcp_client import MCPClientSessionManager, StdioConfig
from pydantic import BaseModel, Field


class MoleculeLite(BaseModel):
    mol_name: str = Field(..., description="Molecule name")
    smiles: str = Field(..., description="Canonical SMILES")
    image_b64: str = Field(..., description="Base64 PNG (data:image/png;base64,...)" )


def _build_llm_config() -> LLMConfig:
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if base_url.rstrip("/").endswith("/responses"):
        base_url = base_url.rstrip("/")[: -len("/responses")]

    return LLMConfig(
        {
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": base_url,
        },
        temperature=0.1,
        max_tokens=900,
        timeout=25,
        response_format=MoleculeLite,
    )


def _extract_json_block(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        i, j = text.find("{"), text.rfind("}")
        if i >= 0 and j > i:
            return json.loads(text[i : j + 1])
        raise


def run_two_agent_chat(user_input: str, max_turns: int = 3) -> MoleculeLite:
    llm_config = _build_llm_config()

    planner = AssistantAgent(
        name="chemical_planner",
        llm_config=llm_config,
        system_message=(
            "你是 Chemical Planner。"
            "你必须优先调用 MCP 工具完成化学查询。"
            "步骤：1) 名称转 SMILES 2) 2D渲染。"
            "最终仅输出 JSON，字段必须为 mol_name, smiles, image_b64。"
        ),
    )

    # MCP Tool Proxy: 宿主执行工具
    mcp_proxy = UserProxyAgent(
        name="mcp_tool_proxy",
        human_input_mode="NEVER",
        code_execution_config=False,
    )

    async def _chat() -> Any:
        default_script = os.path.join(os.path.dirname(__file__), "mcp_server.py")
        mcp_command = os.getenv("MCP_SERVER_COMMAND", sys.executable)
        mcp_args = shlex.split(os.getenv("MCP_SERVER_ARGS", default_script))
        mcp_cwd = os.getenv("MCP_SERVER_CWD", os.path.dirname(__file__))

        manager = MCPClientSessionManager()
        cfg = StdioConfig(
            server_name="rdkit_tools",
            command=mcp_command,
            args=mcp_args,
            working_dir=mcp_cwd,
        )

        async with manager.open_session(cfg) as session:
            toolkit = await create_toolkit(session=session, use_mcp_tools=True, use_mcp_resources=False)
            toolkit.register_for_llm(planner)
            toolkit.register_for_execution(mcp_proxy)

            # 将阻塞会话放进线程，避免 asyncio cancel scope 问题
            return await asyncio.to_thread(
                mcp_proxy.initiate_chat,
                planner,
                message=user_input,
                max_turns=max_turns,
                summary_method="last_msg",
            )

    chat_result = asyncio.run(_chat())
    payload = _extract_json_block(chat_result.summary)
    return MoleculeLite.model_validate(payload)


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "帮我画出阿司匹林并给出结构化结果"
    result = run_two_agent_chat(prompt, max_turns=3)
    print(result.model_dump_json(ensure_ascii=False, indent=2))
