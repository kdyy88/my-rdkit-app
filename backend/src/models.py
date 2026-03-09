"""Pydantic models for structured data validation and API responses."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MolecularProperties(BaseModel):
    """Molecular property data model."""
    molecular_weight: float = Field(..., description="Molecular weight in g/mol")
    logp: float = Field(..., description="Partition coefficient (lipophilicity)")
    logp_source: str = Field(..., description="Source of LogP calculation")
    hydrogen_bond_donors: int = Field(..., description="Number of hydrogen bond donors")
    hydrogen_bond_acceptors: int = Field(..., description="Number of hydrogen bond acceptors")
    formula: str = Field(..., description="Molecular formula")


class MoleculeVisualization(BaseModel):
    """Molecule visualization data model."""
    image_base64: str = Field(..., description="Base64-encoded PNG image of molecule")
    width: int = Field(default=300, description="Image width in pixels")
    height: int = Field(default=300, description="Image height in pixels")


class ToolResult(BaseModel):
    """Generic tool execution result."""
    tool_name: str = Field(..., description="Name of the tool that was called")
    success: bool = Field(..., description="Whether the tool execution succeeded")
    data: Dict[str, Any] = Field(default_factory=dict, description="Tool result data")
    error: Optional[str] = Field(None, description="Error message if tool failed")


class MoleculeResponse(BaseModel):
    """
    Comprehensive molecule response model for AG2 Agent.
    
    This model ensures all frontend display fields are included
    and provides structured output for the AG2 agent system.
    """
    compound_name: Optional[str] = Field(None, description="Common name of the compound")
    smiles: str = Field(..., description="SMILES string representation")
    
    properties: Optional[MolecularProperties] = Field(None, description="Calculated molecular properties")
    visualization: Optional[MoleculeVisualization] = Field(None, description="Molecule structure visualization")
    
    summary: str = Field(..., description="Natural language summary of the analysis")
    tool_calls: List[ToolResult] = Field(default_factory=list, description="List of tool execution results")
    
    class Config:
        json_schema_extra = {
            "example": {
                "compound_name": "ethanol",
                "smiles": "CCO",
                "properties": {
                    "molecular_weight": 46.069,
                    "logp": -0.1,
                    "logp_source": "PubChem XLogP",
                    "hydrogen_bond_donors": 1,
                    "hydrogen_bond_acceptors": 1,
                    "formula": "C2H6O"
                },
                "visualization": {
                    "image_base64": "data:image/png;base64,...",
                    "width": 300,
                    "height": 300
                },
                "summary": "Ethanol (CCO) is a small alcohol molecule with molecular weight 46.069 g/mol...",
                "tool_calls": [
                    {
                        "tool_name": "search_name_to_smiles",
                        "success": True,
                        "data": {"name": "ethanol", "smiles": "CCO"}
                    }
                ]
            }
        }


class MoleculeResponseSchema(BaseModel):
    """LLM-safe response schema used in `response_format` (no free-form dict fields)."""
    compound_name: Optional[str] = Field(None, description="Common name of the compound")
    smiles: str = Field(..., description="SMILES string representation")
    properties: Optional[MolecularProperties] = Field(None, description="Calculated molecular properties")
    visualization: Optional[MoleculeVisualization] = Field(None, description="Molecule structure visualization")
    summary: str = Field(..., description="Natural language summary of the analysis")


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User's chemistry query")
    max_turns: int = Field(default=5, description="Maximum conversation turns")


class ChatResponse(BaseModel):
    """Chat response model."""
    result: MoleculeResponse = Field(..., description="Structured molecule analysis result")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Chat history")
    tokens_used: Optional[int] = Field(None, description="Total tokens used in conversation")
