#!/usr/bin/env python3
"""
Test script for MCP Server tools.

Usage:
    cd backend/src && uv run python ../test_mcp.py
    
Or to run the MCP server in development mode:
    cd backend/src && uv run mcp dev mcp_server.py
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_server import search_name_to_smiles, generate_molecule_viz


def test_search_name_to_smiles():
    """Test compound name to SMILES conversion."""
    print("\n" + "="*60)
    print("Testing: search_name_to_smiles")
    print("="*60)
    
    test_cases = [
        "aspirin",
        "caffeine",
        "ethanol",
        "benzene",
        "invalid_compound_xyz123",  # Should fail
    ]
    
    for name in test_cases:
        result = search_name_to_smiles(name)
        if "error" in result:
            print(f"❌ {name:20} → Error: {result['error']}")
        else:
            print(f"✅ {name:20} → {result['smiles']}")


def test_generate_molecule_viz():
    """Test molecule visualization generation."""
    print("\n" + "="*60)
    print("Testing: generate_molecule_viz")
    print("="*60)
    
    test_cases = [
        ("CCO", "ethanol"),
        ("c1ccccc1", "benzene"),
        ("CC(=O)OC1=CC=CC=C1C(=O)O", "aspirin"),
        ("INVALID", "should fail"),
    ]
    
    for smiles, description in test_cases:
        result = generate_molecule_viz(smiles, width=200, height=200)
        if "error" in result:
            print(f"❌ {description:15} → Error: {result['error']}")
        else:
            img_size = len(result['image'])
            print(f"✅ {description:15} → Image generated ({img_size} chars, {result['width']}x{result['height']})")


def main():
    """Run all tests."""
    print("🧪 MCP Server Tool Tests")
    print("=" * 60)
    
    test_search_name_to_smiles()
    test_generate_molecule_viz()
    
    print("\n" + "="*60)
    print("✨ All tests completed!")
    print("="*60)
    print("\nTo run the MCP server in development mode:")
    print("  cd backend/src && uv run mcp dev mcp_server.py")


if __name__ == "__main__":
    main()
