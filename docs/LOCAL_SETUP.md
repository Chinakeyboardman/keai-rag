# 🏠 完全本地化部署指南（无需 API Key）

本指南将帮助您在**完全不需要任何 API Key** 的情况下运行 RAG 系统。

---

## 📋 方案对比

| 方案 | Embedding | LLM | 优点 | 缺点 |
|------|-----------|-----|------|------|
| **方案一（推荐）** | 本地小模型 | Ollama | 完全免费，易安装 | 需要下载模型 |
| **方案二** | 本地小模型 | 本地大模型 | 完全离线 | 需要大量内存 |
| **方案三** | 本地小模型 | 国内免费API | 快速启动 | 需要注册账号 |

---

## 🚀 方案一：使用 Ollama（最推荐）

### 优点
- ✅ 完全免费
- ✅ 安装简单
- ✅ 模型质量好
- ✅ 内存占用小（约 4-8GB）

### 步骤

#### 1. 安装 Ollama

```bash
# macOS
brew install ollama

# 或者从官网下载
# https://ollama.ai/download
```

#### 2. 启动 Ollama 服务

```bash
# 启动 Ollama（会在后台运行）
ollama serve
```

#### 3. 下载模型

```bash
# 下载中文模型 Qwen2（推荐，约 4GB）
ollama pull qwen2:7b

# 或者更小的模型（约 2GB）
ollama pull qwen2:1.5b

# 或者英文模型
ollama pull llama3.2:3b
```

#### 4. 配置项目

```bash
# 复制本地配置
cp .env.local .env

# 或手动创建 .env 文件，内容如下：
cat > .env << 'EOF'
USE_QDRANT=false
VECTOR_DIMENSION=384

# Embedding 使用小模型
EMBEDDING_MODEL_TYPE=local
EMBEDDING_MODEL_NAME=paraphrase-MiniLM-L6-v2

# LLM 使用 Ollama
LLM_MODEL_TYPE=api
LLM_MODEL_NAME=qwen2:7b
LLM_API_BASE=http://localhost:11434/v1
LLM_API_KEY=ollama
EOF
```

#### 5. 安装 Python 依赖

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装 Embedding 模型依赖
pip install sentence-transformers
```

#### 6. 启动项目

```bash
./start.sh
```

---

## 🎯 方案二：完全离线（使用本地大模型）

### 适合场景
- 完全离线环境
- 有足够的硬件资源（16GB+ RAM）

### 步骤

#### 1. 下载模型

```bash
# 下载 Embedding 模型（自动）
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-MiniLM-L6-v2')"

# 下载 LLM 模型（需要手动）
# 推荐：Qwen2-7B-Instruct 或 ChatGLM3-6B
```

#### 2. 配置 .env

```bash
USE_QDRANT=false
VECTOR_DIMENSION=384

# Embedding
EMBEDDING_MODEL_TYPE=local
EMBEDDING_MODEL_NAME=paraphrase-MiniLM-L6-v2

# LLM（需要指定模型路径）
LLM_MODEL_TYPE=local
LLM_MODEL_PATH=/path/to/your/model
```

#### 3. 启动

```bash
./start.sh
```

---

## 🌐 方案三：使用国内免费 API

### 可用的免费 API

#### 1. 阿里云通义千问（推荐）

**免费额度**: 每天 100 万 tokens

```bash
# 注册地址：https://dashscope.aliyun.com/
# 获取 API Key 后配置：

USE_QDRANT=false
VECTOR_DIMENSION=1536

# Embedding（本地）
EMBEDDING_MODEL_TYPE=local
EMBEDDING_MODEL_NAME=paraphrase-MiniLM-L6-v2

# LLM（API）
LLM_MODEL_TYPE=api
LLM_MODEL_NAME=qwen-turbo
LLM_API_KEY=your_dashscope_api_key
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
```

#### 2. DeepSeek（推荐）

**免费额度**: 每天 500 万 tokens

```bash
# 注册地址：https://platform.deepseek.com/
# 获取 API Key 后配置：

LLM_MODEL_TYPE=api
LLM_MODEL_NAME=deepseek-chat
LLM_API_KEY=your_deepseek_api_key
LLM_API_BASE=https://api.deepseek.com/v1
```

#### 3. 智谱 AI（GLM）

**免费额度**: 每月 100 万 tokens

```bash
# 注册地址：https://open.bigmodel.cn/
# 获取 API Key 后配置：

LLM_MODEL_TYPE=api
LLM_MODEL_NAME=glm-4-flash
LLM_API_KEY=your_zhipu_api_key
LLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
```

---

## 🔍 方案对比详细

### Embedding 模型选择

| 模型 | 大小 | 维度 | 语言 | 推荐度 | 说明 |
|------|------|------|------|--------|------|
| **paraphrase-multilingual-MiniLM-L12-v2** | 420MB | 384 | 🌍 50+语言 | ⭐⭐⭐⭐⭐ | **推荐！多语言小模型** |
| **paraphrase-multilingual-mpnet-base-v2** | 1GB | 768 | 🌍 50+语言 | ⭐⭐⭐⭐⭐ | 多语言高质量 |
| **distiluse-base-multilingual-cased-v2** | 500MB | 512 | 🌍 50+语言 | ⭐⭐⭐⭐ | 平衡性能 |
| paraphrase-MiniLM-L6-v2 | 80MB | 384 | 🇬🇧 英文 | ⭐⭐⭐⭐ | 英文专用 |
| text2vec-base-chinese | 400MB | 768 | 🇨🇳 中文 | ⭐⭐⭐⭐ | 中文专用 |
| m3e-base | 400MB | 768 | 🇨🇳 中文 | ⭐⭐⭐⭐ | 中文专用 |

### LLM 模型选择

| 方案 | 大小 | 内存需求 | 质量 | 推荐度 |
|------|------|----------|------|--------|
| Ollama (qwen2:7b) | 4GB | 8GB | 高 | ⭐⭐⭐⭐⭐ |
| Ollama (qwen2:1.5b) | 2GB | 4GB | 中 | ⭐⭐⭐⭐ |
| 通义千问 API | 0 | 0 | 高 | ⭐⭐⭐⭐ |
| DeepSeek API | 0 | 0 | 高 | ⭐⭐⭐⭐ |

---

## 📦 快速安装脚本

### 一键安装 Ollama 方案

```bash
#!/bin/bash

echo "🚀 安装 Ollama 本地方案..."

# 1. 安装 Ollama
if ! command -v ollama &> /dev/null; then
    echo "📦 安装 Ollama..."
    brew install ollama
fi

# 2. 启动 Ollama
echo "🔄 启动 Ollama 服务..."
ollama serve &
sleep 5

# 3. 下载模型
echo "📥 下载 Qwen2 模型（约 4GB）..."
ollama pull qwen2:7b

# 4. 配置项目
echo "⚙️  配置项目..."
cd /Users/chenjiawei/Study/ai/zhihu/13-Embeddings和向量数据库/china-pdf-rag
cp .env.local .env

# 5. 安装依赖
echo "📦 安装 Python 依赖..."
source venv/bin/activate
pip install sentence-transformers

echo "✅ 安装完成！"
echo ""
echo "运行以下命令启动项目："
echo "  ./start.sh"
```

保存为 `install_ollama.sh`，然后运行：

```bash
chmod +x install_ollama.sh
./install_ollama.sh
```

---

## ⚡ 性能对比

### 硬件需求

| 配置 | CPU | RAM | 磁盘 | 响应时间 |
|------|-----|-----|------|----------|
| 最小配置 | 4核 | 4GB | 5GB | 5-10秒 |
| 推荐配置 | 8核 | 8GB | 10GB | 2-5秒 |
| 高性能配置 | 16核 | 16GB | 20GB | 1-2秒 |

### 模型下载时间（参考）

| 模型 | 大小 | 下载时间（100Mbps） |
|------|------|---------------------|
| paraphrase-MiniLM-L6-v2 | 80MB | 10秒 |
| qwen2:1.5b | 2GB | 3分钟 |
| qwen2:7b | 4GB | 6分钟 |

---

## 🐛 常见问题

### Q1: Ollama 连接失败

```bash
# 检查 Ollama 是否运行
ps aux | grep ollama

# 重启 Ollama
pkill ollama
ollama serve
```

### Q2: 模型下载慢

```bash
# 使用国内镜像
export OLLAMA_HOST=https://ollama.com
ollama pull qwen2:7b
```

### Q3: 内存不足

```bash
# 使用更小的模型
ollama pull qwen2:1.5b

# 或在 .env 中设置
LLM_MODEL_NAME=qwen2:1.5b
```

### Q4: Embedding 模型下载失败

```bash
# 手动下载
python << EOF
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
print("✅ 模型下载成功")
EOF
```

---

## 🎯 推荐配置

### 个人使用（最简单）

```bash
# .env 配置
USE_QDRANT=false
EMBEDDING_MODEL_TYPE=local
EMBEDDING_MODEL_NAME=paraphrase-MiniLM-L6-v2
VECTOR_DIMENSION=384

LLM_MODEL_TYPE=api
LLM_MODEL_NAME=qwen2:7b
LLM_API_BASE=http://localhost:11434/v1
LLM_API_KEY=ollama
```

### 企业使用（高性能）

```bash
# .env 配置
USE_QDRANT=true
QDRANT_URL=http://localhost:6333

EMBEDDING_MODEL_TYPE=local
EMBEDDING_MODEL_NAME=text2vec-base-chinese
VECTOR_DIMENSION=768

LLM_MODEL_TYPE=api
LLM_MODEL_NAME=qwen2:7b
LLM_API_BASE=http://localhost:11434/v1
LLM_API_KEY=ollama
```

---

## ✅ 验证安装

```bash
# 1. 测试 Ollama
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2:7b",
  "prompt": "你好"
}'

# 2. 测试 Embedding
python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
print('✅ Embedding 模型正常')
"

# 3. 启动项目
./start.sh
```

---

**选择方案一（Ollama）是最简单且效果最好的方案！** 🎉

