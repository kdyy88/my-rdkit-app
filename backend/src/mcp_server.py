"""RDKit MCP Server implementation using FastMCP."""

import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, Crippen, AllChem, DataStructs
try:
    from chemistry import smiles_to_base64, name_to_smiles, fetch_pubchem_xlogp
except ImportError:
    from .chemistry import smiles_to_base64, name_to_smiles, fetch_pubchem_xlogp


# Auto-load backend/.env when MCP server runs as standalone subprocess
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_BACKEND_ROOT, ".env"), override=False)


# Create MCP server instance
mcp = FastMCP("RDKit Chemistry Server")


@mcp.tool()
def calculate_properties(smiles: str) -> dict:
    """
    Calculate molecular properties for a given SMILES string.
    
    Args:
        smiles: SMILES string representation of a molecule
        
    Returns:
        Dictionary containing molecular weight, logP, HBD, HBA, and formula
    """
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return {"error": "Invalid SMILES"}

    rdkit_clogp = Crippen.MolLogP(mol)
    pubchem_xlogp = fetch_pubchem_xlogp(smiles)
    preferred_logp = pubchem_xlogp if pubchem_xlogp is not None else rdkit_clogp
    preferred_source = "PubChem XLogP" if pubchem_xlogp is not None else "RDKit Crippen.MolLogP"

    return {
        "smiles": smiles,
        "mw": round(Descriptors.MolWt(mol), 3),
        "logp": round(preferred_logp, 3),
        "logp_source": preferred_source,
        "hbd": Lipinski.NumHDonors(mol),
        "hba": Lipinski.NumHAcceptors(mol),
        "formula": Chem.rdMolDescriptors.CalcMolFormula(mol),
    }


@mcp.tool()
def calculate_similarity(smiles1: str, smiles2: str) -> dict:
    """
    Calculate Tanimoto similarity between two molecules.
    
    Args:
        smiles1: SMILES string of first molecule
        smiles2: SMILES string of second molecule
        
    Returns:
        Dictionary containing similarity score and interpretation
    """
    m1 = Chem.MolFromSmiles(smiles1)
    m2 = Chem.MolFromSmiles(smiles2)
    
    if not m1 or not m2:
        return {"error": "Invalid SMILES input"}
    
    fp1 = AllChem.GetMorganFingerprintAsBitVect(m1, 2, nBits=2048)
    fp2 = AllChem.GetMorganFingerprintAsBitVect(m2, 2, nBits=2048)
    
    score = DataStructs.TanimotoSimilarity(fp1, fp2)
    
    return {
        "score": round(score, 4),
        "percentage": f"{round(score * 100, 2)}%",
        "status": "High Similarity" if score > 0.8 else "Common" if score > 0.5 else "Low Similarity"
    }


@mcp.tool()
def search_name_to_smiles(compound_name: str) -> dict:
    """
    Search for a compound by name and convert it to SMILES.
    
    This tool searches PubChem database using common names, IUPAC names,
    or other chemical identifiers and returns the canonical SMILES representation.
    
    Args:
        compound_name: Common name, IUPAC name, or identifier (e.g., "aspirin", "caffeine", "benzene")
        
    Returns:
        Dictionary containing:
        - name: The input compound name
        - smiles: Canonical SMILES string
        - error: Error message if compound not found
        
    Example:
        >>> search_name_to_smiles("aspirin")
        {"name": "aspirin", "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"}
    """
    smiles = name_to_smiles(compound_name)
    if not smiles:
        return {"error": f"Compound '{compound_name}' not found in PubChem database"}
    
    return {"name": compound_name, "smiles": smiles}


@mcp.tool()
def search_smiles_by_name(mol_name: str) -> dict:
    """Alias tool: convert Chinese/English molecule name to SMILES."""
    return search_name_to_smiles(mol_name)


@mcp.tool()
def generate_molecule_viz(smiles: str, width: int = 300, height: int = 300) -> dict:
    """
    Generate a visual representation of a molecule from SMILES.
    
    This tool uses RDKit to render a 2D structure diagram of the molecule
    and returns it as a base64-encoded PNG image that can be displayed directly
    in web browsers or embedded in documents.
    
    Args:
        smiles: SMILES string representation of a molecule
        width: Image width in pixels (default: 300)
        height: Image height in pixels (default: 300)
        
    Returns:
        Dictionary containing:
        - image: Base64-encoded PNG image (data URL format)
        - smiles: The input SMILES string
        - error: Error message if SMILES is invalid or rendering fails
        
    Example:
        >>> generate_molecule_viz("CCO")
        {"image": "data:image/png;base64,iVBORw0KGgo...", "smiles": "CCO"}
    """
    img_data = smiles_to_base64(smiles, size=(width, height))
    if not img_data:
        return {"error": "Invalid SMILES string or molecule rendering failed"}
    
    return {
        "image": img_data,
        "smiles": smiles,
        "width": width,
        "height": height
    }


@mcp.tool()
def rdkit_2d_render(smiles: str, width: int = 300, height: int = 300) -> dict:
    """Alias tool: render SMILES to base64 PNG (2D)."""
    return generate_molecule_viz(smiles=smiles, width=width, height=height)


if __name__ == "__main__":
    mcp.run()
