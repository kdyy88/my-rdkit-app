# my-rdkit-app

## 前端启动

在项目根目录执行：

```bash
cd ~/my-rdkit-app/frontend
pnpm install
pnpm run dev
```

启动后访问：

- http://localhost:3000

## 后端启动

在项目根目录执行：

```bash
cd ~/my-rdkit-app/backend
uv sync
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：

- API 文档: http://127.0.0.1:8000/docs
- 示例接口: http://127.0.0.1:8000/calc?smiles=CCO
