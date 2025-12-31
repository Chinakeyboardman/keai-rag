# 🔧 快速修复指南

根据测试结果，需要安装一些依赖并调整配置。

---

## 📦 步骤 1: 安装缺失的依赖

```bash
# 激活虚拟环境
cd /Users/chenjiawei/Study/ai/zhihu/13-Embeddings和向量数据库/china-pdf-rag
source venv/bin/activate

# 安装缺失的依赖
pip install qdrant-client sentence-transformers
```

---

## ⚙️ 步骤 2: 调整配置（使用更轻量的方案）

由于 DeepSeek-R1 模型路径不存在，建议使用 API 模式或更小的模型。

### 选项 A: 使用 API 模式（推荐用于快速测试）

编辑 `.env` 文件：

```bash
# Embedding 使用 API
EMBEDDING_MODEL_TYPE=api
EMBEDDING_API_KEY=your_api_key_here
EMBEDDING_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

# LLM 使用 API
LLM_MODEL_TYPE=api
LLM_API_KEY=your_api_key_here
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-turbo
```

### 选项 B: 使用更小的本地模型

```bash
# 下载小模型（约 400MB）
pip install -U huggingface_hub
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-MiniLM-L6-v2')"
```

然后编辑 `.env`:

```bash
# Embedding 使用小模型
EMBEDDING_MODEL_TYPE=local
EMBEDDING_MODEL_NAME=paraphrase-MiniLM-L6-v2
VECTOR_DIMENSION=384  # 注意：这个模型是 384 维

# LLM 使用 API（本地 LLM 太大）
LLM_MODEL_TYPE=api
LLM_API_KEY=your_api_key_here
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-turbo
```

---

## 🧪 步骤 3: 重新运行测试

```bash
python test_system.py
```

---

## 🚀 步骤 4: 启动服务

如果测试通过，启动服务：

```bash
python src/api/main.py
```

或

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 💡 最简单的测试方案

如果只是想快速测试系统是否工作，使用这个最小配置：

```bash
# 创建 .env 文件
cat > .env << 'EOF'
# 项目配置
PROJECT_NAME=企业级RAG系统
PROJECT_VERSION=1.0.0
DEBUG=false

# 向量数据库（使用 FAISS）
USE_QDRANT=false
VECTOR_DIMENSION=384

# Embedding（使用小模型）
EMBEDDING_MODEL_TYPE=local
EMBEDDING_MODEL_NAME=paraphrase-MiniLM-L6-v2

# LLM（使用 API）
LLM_MODEL_TYPE=api
LLM_API_KEY=sk-your-api-key
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-3.5-turbo

# 其他配置使用默认值
EOF

# 安装依赖
pip install sentence-transformers qdrant-client

# 下载模型
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-MiniLM-L6-v2')"

# 运行测试
python test_system.py
```

---

## ❓ 常见问题

### Q: 没有 API Key 怎么办？

A: 可以注册以下服务获取免费额度：
- 阿里云通义千问: https://dashscope.aliyun.com/
- DeepSeek: https://platform.deepseek.com/
- OpenAI: https://platform.openai.com/

### Q: 想使用完全本地的方案？

A: 需要下载大模型（10GB+），不推荐用于快速测试。如果确实需要：

```bash
# 下载 ChatGLM3-6B（约 12GB）
pip install transformers torch
python -c "from transformers import AutoModel; AutoModel.from_pretrained('THUDM/chatglm3-6b', trust_remote_code=True)"
```

### Q: 测试失败怎么办？

A: 查看错误信息，通常是：
1. 依赖未安装 → 运行 `pip install -r requirements.txt`
2. 模型未下载 → 使用 API 模式或下载模型
3. 配置错误 → 检查 `.env` 文件

---

## ✅ 验证安装

运行以下命令验证：

```bash
# 验证 Python 包
python -c "import qdrant_client; import sentence_transformers; print('✅ 依赖已安装')"

# 验证配置
python -c "from config.settings import settings; print(f'✅ 配置加载成功: {settings.PROJECT_NAME}')"

# 验证模型（如果使用本地）
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('paraphrase-MiniLM-L6-v2'); print('✅ 模型加载成功')"
```

---

## 🎯 推荐配置（平衡性能和易用性）

```bash
# .env 配置
USE_QDRANT=false                    # 使用 FAISS（简单）
EMBEDDING_MODEL_TYPE=local          # 本地 Embedding（快速）
EMBEDDING_MODEL_NAME=paraphrase-MiniLM-L6-v2
VECTOR_DIMENSION=384
LLM_MODEL_TYPE=api                  # API LLM（质量好）
LLM_API_KEY=your_key
LLM_MODEL_NAME=qwen-turbo
```

这个配置：
- ✅ 不需要 Qdrant 服务
- ✅ Embedding 模型小（400MB）
- ✅ LLM 使用 API（质量好）
- ✅ 启动快，占用内存少

---

**选择一个方案，然后开始测试吧！** 🚀

