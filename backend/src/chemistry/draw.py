"""RDKit drawing utilities for molecular structures."""

import base64
from io import BytesIO
from rdkit import Chem
from rdkit.Chem import Draw


def smiles_to_base64(smiles: str, size: tuple[int, int] = (300, 300)) -> str | None:
    """
    Convert SMILES to base64-encoded PNG image.
    
    Args:
        smiles: SMILES string representation of a molecule
        size: Tuple of (width, height) for the output image
        
    Returns:
        Base64-encoded PNG image string or None if SMILES is invalid
    """
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return None
    
    img = Draw.MolToImage(mol, size=size)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"
