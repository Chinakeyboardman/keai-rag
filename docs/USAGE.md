# 📖 使用指南

## 🚀 一键启动

### 方式一：使用启动脚本（推荐）

```bash
# 1. 进入项目目录
cd /Users/chenjiawei/Study/ai/zhihu/13-Embeddings和向量数据库/china-pdf-rag

# 2. 运行启动脚本
./start.sh
```

### 方式二：手动启动

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 启动服务
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🌐 访问地址

启动成功后，访问以下地址：

- **Web UI**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health

---

## 💻 Web UI 使用说明

### 1. 上传文档

1. 点击左侧"文档上传"区域
2. 选择 PDF 文件（或直接拖拽文件）
3. 点击"上传文档"按钮
4. 等待处理完成

### 2. 智能问答

1. 在右侧"智能问答"区域输入问题
2. 点击"提问"按钮（或按 Enter 键）
3. 查看 AI 生成的答案
4. 点击推荐问题可以快速提问

### 3. 查看已上传文档

在左侧底部可以看到所有已上传的文档列表。

---

## 🔧 配置说明

### 最小配置（快速测试）

编辑 `.env` 文件：

```bash
# 使用 FAISS 本地存储
USE_QDRANT=false

# 使用 API 模式（需要 API Key）
EMBEDDING_MODEL_TYPE=api
EMBEDDING_API_KEY=your_api_key_here
EMBEDDING_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

LLM_MODEL_TYPE=api
LLM_API_KEY=your_api_key_here
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-turbo
```

### 完整配置（本地模型）

```bash
# 使用本地向量存储
USE_QDRANT=false

# 使用本地 Embedding 模型
EMBEDDING_MODEL_TYPE=local
EMBEDDING_MODEL_NAME=paraphrase-MiniLM-L6-v2
VECTOR_DIMENSION=384

# 使用本地 LLM 模型
LLM_MODEL_TYPE=local
LLM_MODEL_PATH=/path/to/your/model
```

---

## 📡 API 使用示例

### 1. 上传文档

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/document.pdf"
```

### 2. 查询问答

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "文档的主要内容是什么？",
    "top_k": 3,
    "include_suggestions": true
  }'
```

### 3. 获取文档列表

```bash
curl "http://localhost:8000/api/v1/documents"
```

### 4. 健康检查

```bash
curl "http://localhost:8000/api/v1/health"
```

---

## ⚠️ 常见问题

### 问题 1: 启动失败

**错误**: `ModuleNotFoundError`

**解决**:
```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 问题 2: 找不到 .env 文件

**解决**:
```bash
# 从模板创建
cp env.example .env

# 编辑配置
nano .env  # 或使用其他编辑器
```

### 问题 3: 端口被占用

**错误**: `Address already in use`

**解决**:
```bash
# 更改端口
python -m uvicorn src.api.main:app --port 8001
```

### 问题 4: 模型加载失败

**解决**: 使用 API 模式而不是本地模型

```bash
# 在 .env 中设置
EMBEDDING_MODEL_TYPE=api
LLM_MODEL_TYPE=api
```

---

## 🛑 停止服务

在终端中按 `Ctrl+C` 停止服务。

---

## 📊 性能建议

### 小规模使用（< 100 个文档）
- 使用 FAISS 本地存储
- 使用 API 模式的模型
- 单机部署即可

### 中等规模（100-1000 个文档）
- 使用 Qdrant 向量数据库
- 考虑使用本地模型
- 增加服务器内存

### 大规模使用（> 1000 个文档）
- 使用 Qdrant 集群
- 使用本地模型 + GPU
- 考虑分布式部署

---

## 🔐 安全建议

1. **不要在生产环境暴露 8000 端口**
   - 使用 Nginx 反向代理
   - 添加 HTTPS 支持

2. **保护 API Key**
   - 不要提交 .env 文件到 Git
   - 使用环境变量管理敏感信息

3. **添加认证**
   - 实现用户认证系统
   - 添加 API Token 验证

---

## 📝 日志查看

日志文件位置：`./logs/app.log`

```bash
# 实时查看日志
tail -f logs/app.log

# 查看最近 100 行
tail -n 100 logs/app.log
```

---

## 🎯 下一步

1. 上传您的第一个文档
2. 尝试提问
3. 查看 API 文档了解更多功能
4. 根据需要调整配置

---

**祝使用愉快！** 🎉

