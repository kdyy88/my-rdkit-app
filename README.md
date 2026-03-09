# RDKit AI Platform

基于 AG2 (AutoGen) + MCP + RDKit 的智能化学分析平台

## 项目结构

```
rdkit-ai-platform/
├── backend/                # Python 空间 (由 uv 管理)
│   ├── .python-version
│   ├── .env.example        # 环境变量模板
│   ├── pyproject.toml      # 包含 rdkit, mcp, fastmcp, pubchempy
│   └── src/
│       ├── main.py         # AG2 Agent 入口，协调 MCP 与用户
│       ├── mcp_server.py   # RDKit MCP Server 核心实现
│       └── chemistry/      # 核心化学逻辑封装
│           ├── __init__.py
│           ├── draw.py     # RDKit 绘图逻辑 (SMILES -> Base64)
│           └── search.py   # 名称转 SMILES 逻辑 (PubChem)
├── frontend/               # Next.js 空间 (由 pnpm/npm 管理)
│   ├── package.json
│   ├── components.json     # Shadcn UI 配置
│   └── src/
│       ├── app/
│       │   ├── api/        # Next.js Route Handlers (连接后端)
│       │   │   └── chat/route.ts
│       │   └── page.tsx    # 主交互界面
│       ├── components/     # UI 组件
│       │   ├── ui/         # Shadcn 自动生成的组件
│       │   └── molecule/   # 自定义组件 (MoleculeViewer, SimilarityChecker)
│       └── lib/
│           ├── config.ts   # API 配置
│           ├── types.ts    # TypeScript 类型定义
│           └── utils.ts    # 工具函数
└── docker-compose.yml      # 一键编排
```

## 技术栈

### 管理工具

- **uv** - Python 包管理器和虚拟环境管理
- **pnpm** - Next.js 项目的依赖管理

### 后端核心 (Python with uv)

使用 `uv` 管理 Python 环境，确保 RDKit 运行环境的隔离与稳定。

**核心技术：**
- **ag2[openai,mcp]** - AG2 (AutoGen) Agent 框架，集成 OpenAI 和 MCP 支持
- **fastmcp** - MCP Server 高级封装，简化工具注册流程
- **rdkit** - 核心化学信息学库，提供分子操作和性质计算
- **pubchempy** - 处理自然语言到 SMILES 的模糊查询转换
- **Pydantic v2** - 数据验证和设置管理

**Web 框架：**
- **fastapi** - 现代 Web 框架
- **uvicorn** - ASGI 服务器
- **sse-starlette** - Server-Sent Events 支持，可通过 HTTP (SSE) 暴露 MCP 服务

**开发工具：**
- **mcp** - Anthropic 提供的 Model Context Protocol 官方 SDK
- **openai** - LLM API 客户端
- **python-dotenv** - 环境变量管理

所有依赖在 `backend/pyproject.toml` 中定义，使用 `uv sync` 自动安装。

### 前端核心 (Next.js with pnpm)

- **Next.js 16 (App Router)** - React 框架，使用现代化的 App Router
- **Shadcn UI** - 现代化 UI 组件库
- **Tailwind CSS** - 实用优先的 CSS 框架
- **TypeScript** - 类型安全的数据模型
- **RDKit.js** - WebAssembly 版本的 RDKit，用于前端分子预览

## 快速开始

### 1. 安装依赖

**后端：**
```bash
cd backend
uv sync
```

**前端：**
```bash
cd frontend
pnpm install
```

### 2. 配置环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY
```

### 3. 测试 MCP Server

```bash
cd backend
uv run python test_mcp.py
```

查看详细测试指南：[MCP_TESTING_GUIDE.md](backend/MCP_TESTING_GUIDE.md)

### 4. 启动服务

**后端 FastAPI 服务：**
```bash
cd backend/src
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**前端 Next.js 服务：**
```bash
cd frontend
pnpm run dev
```

访问 http://localhost:3000

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

### 开发模式

在项目根目录执行：

```bash
# 从 src 目录启动（你当前的位置）
cd /home/administrator/my-rdkit-app/backend/src
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 或从 backend 目录启动
cd /home/administrator/my-rdkit-app/backend
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 环境配置

复制 `.env.example` 为 `.env` 并配置你的 API keys：

```bash
cd ~/my-rdkit-app/backend
cp .env.example .env
# 编辑 .env 文件，填入你的 OPENAI_API_KEY
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

## 开发路线图

### 第一阶段：后端基础与 MCP 工具 (Backend & Tools)

#### 环境初始化
- [x] 执行 `uv init` 创建项目结构
- [x] 在 `pyproject.toml` 中添加核心依赖：
  - [x] `ag2[openai,mcp]` - Agent 框架
  - [x] `fastmcp` - MCP Server 封装
  - [x] `rdkit` - 化学信息学库
  - [x] `pubchempy` - PubChem API 集成

#### MCP Server 实现
- [x] 创建 `backend/src/mcp_server.py` 基础结构
- [x] 实现 `search_name_to_smiles` 工具
  - 输入：化合物名称（如 "aspirin"）
  - 输出：标准 SMILES 字符串
  - 集成 PubChem API 进行名称解析
- [x] 实现 `generate_molecule_viz` 工具
  - 输入：SMILES 字符串
  - 输出：Base64 编码的分子结构图（PNG）
  - 使用 RDKit 渲染 2D 结构

#### 测试验证
- [x] 创建测试脚本 `backend/test_mcp.py`
- [x] 验证工具功能正常
- [x] 测试边界情况（无效 SMILES、未知化合物名称）
- [ ] 使用 `mcp dev mcp_server.py` 在 MCP 控制台测试工具调用

**运行测试：**
```bash
# 运行单元测试
cd backend && uv run python test_mcp.py

# 启动 MCP 开发服务器（交互式测试）
cd backend/src && uv run mcp dev mcp_server.py
```

### 第二阶段：AG2 Agent 集成 (Coming Soon)

- [ ] 配置 AG2 Agent 连接 MCP Server
- [ ] 实现对话式化学查询接口
- [ ] 添加多轮对话支持

### 第三阶段：前端集成 (Coming Soon)

- [ ] 实现聊天界面组件
- [ ] 集成 MCP 工具调用可视化
- [ ] 添加分子结构交互式展示
