# 🚀 启动服务指南

本指南将帮助您快速启动 RAG 系统。

---

## 📋 前置检查

### 1. 确认环境配置

```bash
# 检查 .env 文件是否存在
ls -la .env

# 如果不存在，从模板创建
cp env.example .env
```

### 2. 编辑配置文件

打开 `.env` 文件，确认以下关键配置：

```bash
# 向量数据库（建议先使用 FAISS）
USE_QDRANT=false

# Embedding 模型（建议使用 API 或小模型）
EMBEDDING_MODEL_TYPE=local
EMBEDDING_MODEL_NAME=moka-ai/m3e-base

# LLM 模型
LLM_MODEL_TYPE=local
LLM_MODEL_PATH=/Users/chenjiawei/Public/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
```

### 3. 安装依赖（如果还没安装）

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

---

## 🧪 运行测试

在启动服务前，建议先运行测试确保系统正常：

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行集成测试
python test_system.py
```

**预期输出：**
```
🧪 企业级 RAG 系统 - 集成测试
============================================

1. 测试配置加载
✅ 配置加载成功

2. 测试向量存储
✅ 向量存储初始化成功

3. 测试 Embedding 服务
✅ Embedding 服务初始化成功

4. 测试 LLM 服务
✅ LLM 服务初始化成功

5. 测试文档处理
✅ 文档处理成功

6. 测试完整 RAG 流程
✅ RAG 流程测试成功

📊 测试总结
============================================
总计: 6/6 通过
🎉 所有测试通过！系统运行正常！
```

---

## 🚀 启动服务

### 方式 1: 使用 Python 直接运行

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 方式 2: 使用 main.py

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动服务
python src/api/main.py
```

### 预期输出

```
============================================
🚀 企业级RAG系统 v1.0.0
============================================

📦 初始化服务...
🔧 使用 FAISS 本地存储
✅ FAISS 存储初始化成功
   存储目录: ./data/vectors
   集合: rag_documents
   向量数量: 0

📦 加载本地 Embedding 模型: ./models/m3e-base
✅ Embedding 模型加载成功

📦 加载本地 LLM 模型: /path/to/deepseek-r1
✅ LLM 模型加载成功 (设备: cuda)

✅ 检索和生成服务已就绪

🌐 API 服务启动:
   地址: http://0.0.0.0:8000
   文档: http://0.0.0.0:8000/docs

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 📖 访问 API 文档

服务启动后，访问以下地址：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **根路径**: http://localhost:8000/

---

## 🧪 测试 API

### 1. 健康检查

```bash
curl http://localhost:8000/api/v1/health
```

### 2. 上传文档

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/document.pdf"
```

### 3. 查询问答

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "文档的主要内容是什么？",
    "top_k": 3,
    "include_suggestions": true
  }'
```

### 4. 获取文档列表

```bash
curl http://localhost:8000/api/v1/documents
```

---

## ⚠️ 常见问题

### 问题 1: 模型加载失败

**错误**: `模型路径不存在`

**解决**:
1. 检查 `.env` 中的模型路径是否正确
2. 如果使用本地模型，确保模型已下载
3. 可以临时改用 API 模式

```bash
# 在 .env 中修改
EMBEDDING_MODEL_TYPE=api
EMBEDDING_API_KEY=your_api_key
```

### 问题 2: 内存不足

**错误**: `CUDA out of memory` 或 `MemoryError`

**解决**:
1. 使用更小的模型
2. 减小批处理大小
3. 使用 CPU 而非 GPU

```bash
# 在 .env 中修改
EMBEDDING_BATCH_SIZE=8  # 减小批处理
```

### 问题 3: 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 更改端口
python -m uvicorn src.api.main:app --port 8001

# 或在 .env 中修改
API_PORT=8001
```

### 问题 4: Qdrant 连接失败

**错误**: `无法连接到 Qdrant`

**解决**:
```bash
# 在 .env 中使用 FAISS 降级
USE_QDRANT=false
```

或启动 Qdrant 服务：
```bash
docker run -p 6333:6333 qdrant/qdrant
```

---

## 📊 性能优化建议

### 1. 使用 GPU 加速

如果有 GPU，确保安装了 CUDA 版本的依赖：

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### 2. 调整批处理大小

根据可用内存调整：

```bash
# 在 .env 中
EMBEDDING_BATCH_SIZE=32  # GPU 可以更大
CHUNK_SIZE=1000          # 根据文档调整
```

### 3. 使用 Qdrant

对于大规模应用，建议使用 Qdrant：

```bash
# 启动 Qdrant
docker run -p 6333:6333 -v $(pwd)/qdrant_data:/qdrant/storage qdrant/qdrant

# 在 .env 中
USE_QDRANT=true
```

---

## 🛑 停止服务

按 `Ctrl+C` 停止服务。

服务会自动保存数据并清理资源。

---

## 📝 日志

日志文件位置：`./logs/app.log`

查看日志：
```bash
tail -f logs/app.log
```

---

## 🎉 成功！

如果看到以上输出，说明服务已成功启动！

现在可以：
1. 访问 http://localhost:8000/docs 查看 API 文档
2. 上传 PDF 文档
3. 开始提问

**祝使用愉快！** 🚀

