# 使用轻量级 Python 镜像
FROM python:3.10-slim

WORKDIR /app

# 安装 RDKit 运行所需的系统级 C++ 库
RUN apt-get update && apt-get install -y \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 先安装依赖，利用 Docker 缓存提高以后构建的速度
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝后端源码
COPY . .

# 启动命令 (注意 host 必须是 0.0.0.0)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]