from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rdkit import Chem
from rdkit.Chem import Descriptors
from rdkit.Chem import AllChem, DataStructs

app = FastAPI()
# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在开发环境下允许所有源，生产环境再缩小范围
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/calc")
def calculate_molecule(smiles: str = "CCO"):
    mol = Chem.MolFromSmiles(smiles)
    if not mol:
        return {"error": "SMILES 解析失败"}
    
    return {
        "smiles": smiles,
        "mw": Descriptors.MolWt(mol),
        "logp": Descriptors.MolLogP(mol),
        "formula": Chem.rdMolDescriptors.CalcMolFormula(mol)
    }
    
@app.get("/similarity")
def get_similarity(smi1: str, smi2: str):
    m1 = Chem.MolFromSmiles(smi1)
    m2 = Chem.MolFromSmiles(smi2)
    
    if not m1 or not m2:
        return {"error": "输入的 SMILES 无效"}
    
    # 1. 生成 Morgan 指纹 (半径为2，这是药物化学的标准配置)
    fp1 = AllChem.GetMorganFingerprintAsBitVect(m1, 2, nBits=2048)
    fp2 = AllChem.GetMorganFingerprintAsBitVect(m2, 2, nBits=2048)
    
    # 2. 计算 Tanimoto 相似度 (结果在 0 到 1 之间)
    score = DataStructs.TanimotoSimilarity(fp1, fp2)
    
    return {
        "score": round(score, 4),
        "percentage": f"{round(score * 100, 2)}%",
        "status": "High Similarity" if score > 0.8 else "Common" if score > 0.5 else "Low Similarity"
    }