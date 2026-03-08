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

## 拉取更新后强制重建部署（Docker）

如果从 GitHub 拉取更新后页面或接口没有变化，执行以下命令：

```bash
cd ~/my-rdkit-app

# 1) 停止并删除旧容器
docker compose down

# 2) 无缓存重建镜像
docker compose build --no-cache

# 3) 强制重建并启动容器
docker compose up -d --force-recreate
```

可选：查看服务状态

```bash
docker compose ps
```
