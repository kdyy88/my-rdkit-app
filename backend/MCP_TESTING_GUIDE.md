# MCP Server 快速测试指南

## 方法一：使用 Python 测试脚本

最简单的方式，运行预制的测试套件：

```bash
cd /home/administrator/my-rdkit-app/backend
uv run python test_mcp.py
```

**输出示例：**
```
🧪 MCP Server Tool Tests
============================================================
Testing: search_name_to_smiles
✅ aspirin              → CC(=O)OC1=CC=CC=C1C(=O)O
✅ caffeine             → CN1C=NC2=C1C(=O)N(C(=O)N2C)C
...
```

## 方法二：使用 MCP 开发模式（推荐）

启动交互式 MCP 控制台，可以手动调用工具：

```bash
cd /home/administrator/my-rdkit-app/backend/src
uv run mcp dev mcp_server.py
```

这将启动一个 MCP Inspector，你可以在浏览器中：
- 查看所有可用工具
- 测试工具调用
- 查看工具返回值
- 调试工具行为

## 方法三：Python 脚本直接调用

创建自己的测试脚本：

```python
import sys
sys.path.insert(0, 'src')

from mcp_server import search_name_to_smiles, generate_molecule_viz

# 测试 1: 搜索化合物
result = search_name_to_smiles("aspirin")
print(f"SMILES: {result['smiles']}")

# 测试 2: 生成分子图
viz = generate_molecule_viz("CCO", width=400, height=400)
print(f"Image data length: {len(viz['image'])} chars")
```

## 可用的 MCP 工具

### 1. search_name_to_smiles
将化合物名称转换为 SMILES

**示例调用：**
```python
search_name_to_smiles("aspirin")
# 返回: {"name": "aspirin", "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"}
```

### 2. generate_molecule_viz
生成分子结构图（Base64 PNG）

**示例调用：**
```python
generate_molecule_viz("CCO", width=300, height=300)
# 返回: {"image": "data:image/png;base64,...", "smiles": "CCO", ...}
```

### 3. calculate_properties
计算分子性质

**示例调用：**
```python
calculate_properties("CCO")
# 返回: {"mw": 46.069, "logp": -0.1, "hbd": 1, "hba": 1, ...}
```

### 4. calculate_similarity
计算两个分子的相似度

**示例调用：**
```python
calculate_similarity("CCO", "CCCO")
# 返回: {"score": 0.75, "percentage": "75.0%", ...}
```

## 故障排查

### 导入错误
如果遇到 `ModuleNotFoundError: No module named 'chemistry'`：

```bash
# 确保从正确的目录运行
cd backend/src
uv run python ../test_mcp.py

# 或者使用绝对导入
cd backend
PYTHONPATH=src uv run python test_mcp.py
```

### PubChem 查询失败
如果化合物名称查询失败：
- 检查网络连接
- 尝试使用 IUPAC 名称或 CAS 号
- 化合物可能不存在于 PubChem 数据库

### RDKit 渲染错误
如果分子图生成失败：
- 检查 SMILES 语法是否正确
- 使用 RDKit 验证：`Chem.MolFromSmiles("your_smiles")`
