# 企业级RAG系统设计方案

## 📋 项目需求

设计一个企业可用的RAG（检索增强生成）系统，需要生成选型文档，设计合理的目录结构。要求如下：

1. **文档导入**：可导入PDF作为文档（未来可扩展其他格式，预留策略类）
2. **向量数据库**：使用Qdrant，连接不上时选用本地存储降级方案
3. **API服务**：提供API，用户可向机器人提问，机器人依照文档内容进行回答，并猜测用户想问的其他问题
4. **模型选型**：项目使用的模型均使用中国国内可用API或可本地部署的

---

## 🏗️ 系统架构设计

### 整体架构
```
┌─────────────┐
│   API层     │  FastAPI RESTful API
├─────────────┤
│  业务逻辑层  │  文档处理、向量化、检索、生成
├─────────────┤
│  数据存储层  │  Qdrant / FAISS (降级) + 元数据存储
├─────────────┤
│  模型服务层  │  Embedding模型 + LLM模型
└─────────────┘
```

---

## 🔧 技术选型

### 1. 文档处理
- **PDF解析**：`PyPDF2` / `pdfplumber` / `pypdf`
- **文本分割**：`langchain.text_splitter.RecursiveCharacterTextSplitter`
- **扩展策略**：使用策略模式，支持未来扩展 Word、Excel、TXT 等格式

### 2. 向量数据库
- **主选**：`Qdrant`（云服务或本地部署）
- **降级方案**：`FAISS`（本地存储）
- **元数据存储**：`SQLite` / `JSON` 文件

### 3. Embedding模型（国内可用）
- **选项1**：`text-embedding-v3` / `text-embedding-v4`（阿里云/百度云代理）
- **选项2**：`bge-large-zh-v1.5`（本地部署，智源）
- **选项3**：`m3e-base` / `m3e-large`（本地部署，Moka AI）
- **推荐**：优先使用本地部署的 `bge-large-zh-v1.5` 或 `m3e-large`

### 4. LLM模型（国内可用）
- **选项1**：`DeepSeek`（API：阿里云代理）
- **选项2**：`Qwen`（API：阿里云/通义千问）
- **选项3**：`ChatGLM3`（本地部署）
- **选项4**：`DeepSeek-R1`（本地部署，已有模型）
- **推荐**：优先使用本地部署的 `DeepSeek-R1` 或 `ChatGLM3`
- 这里采用选项4作为实现方案

### 5. API框架
- **FastAPI**：高性能、自动文档生成、类型检查

### 6. 其他依赖
- `langchain` / `langchain-community`：文本处理框架
- `numpy`：数值计算
- `pydantic`：数据验证
- `uvicorn`：ASGI服务器

---

## 📁 目录结构设计

```
china-pdf-rag/
├── README.md                 # 项目说明文档
├── requirements.txt          # Python依赖
├── .env.example              # 环境变量示例
├── config/
│   ├── __init__.py
│   ├── settings.py          # 配置管理
│   └── model_config.py      # 模型配置
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI应用入口
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── document.py  # 文档上传接口
│   │   │   ├── query.py     # 查询接口
│   │   │   └── health.py    # 健康检查
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── document.py  # 文档相关数据模型
│   │       └── query.py     # 查询相关数据模型
│   ├── core/
│   │   ├── __init__.py
│   │   ├── document_processor.py    # 文档处理核心
│   │   ├── vector_store.py          # 向量存储抽象层
│   │   ├── qdrant_store.py          # Qdrant实现
│   │   ├── faiss_store.py           # FAISS降级实现
│   │   └── llm_service.py           # LLM服务封装
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── base.py          # 处理器基类（策略模式）
│   │   ├── pdf_processor.py # PDF处理器
│   │   └── txt_processor.py # TXT处理器（预留）
│   ├── services/
│   │   ├── __init__.py
│   │   ├── embedding_service.py     # Embedding服务
│   │   ├── retrieval_service.py     # 检索服务
│   │   └── generation_service.py    # 生成服务（含问题猜测）
│   └── utils/
│       ├── __init__.py
│       ├── logger.py        # 日志工具
│       └── exceptions.py    # 自定义异常
├── data/
│   ├── documents/           # 上传的原始文档
│   ├── vectors/             # 向量数据库存储（FAISS降级）
│   └── metadata/            # 元数据存储
├── tests/                   # 测试文件
│   ├── __init__.py
│   ├── test_api.py
│   └── test_services.py
└── scripts/
    ├── init_db.py          # 初始化数据库脚本
    └── migrate.py          # 数据迁移脚本
```

---

## 🎯 核心功能模块

### 1. 文档处理模块
- **功能**：支持PDF文档解析、文本提取、分块处理
- **策略模式**：预留接口，便于扩展其他格式
- **元数据**：保存文档ID、文件名、上传时间、分块信息等

### 2. 向量存储模块
- **主选**：Qdrant连接管理、集合创建、向量插入/查询
- **降级**：自动检测Qdrant连接，失败时切换到FAISS
- **统一接口**：抽象层确保业务代码无需关心底层实现

### 3. Embedding服务
- **模型加载**：支持API调用和本地模型加载
- **批量处理**：文档分块批量向量化
- **缓存机制**：相同文本避免重复计算

### 4. 检索服务
- **相似度搜索**：基于向量相似度检索Top-K文档块
- **混合检索**：可结合关键词检索（未来扩展）
- **结果排序**：按相似度分数排序

### 5. 生成服务
- **RAG生成**：基于检索到的文档块生成答案
- **问题猜测**：基于用户问题和检索内容，生成3-5个相关问题
- **上下文管理**：合理组织检索内容和用户问题

### 6. API服务
- **文档上传**：POST `/api/v1/documents/upload`
- **文档列表**：GET `/api/v1/documents`
- **文档删除**：DELETE `/api/v1/documents/{doc_id}`
- **查询接口**：POST `/api/v1/query`
- **健康检查**：GET `/api/v1/health`

---

## 🔄 降级方案设计

### Qdrant连接检测
1. 启动时检测Qdrant连接
2. 连接失败时自动切换到FAISS
3. 定期重试连接Qdrant（可选）

### 数据一致性
- FAISS降级时，元数据存储在SQLite/JSON
- 支持从FAISS迁移到Qdrant（未来功能）

---

## 📝 实施Checklist

### 阶段一：项目初始化 ✅
- [x] 创建项目目录结构
- [x] 配置Python虚拟环境
- [x] 编写 `requirements.txt`
- [x] 配置 `env.example` 环境变量模板
- [x] 初始化Git仓库
- [x] 创建 README.md 项目说明文档
- [x] 创建 PROJECT_STRUCTURE.md 结构说明文档
- [x] 创建初始化脚本 `scripts/init_db.py`
- [x] 创建安装脚本 `scripts/setup.sh`

### 阶段二：核心模块开发 ✅
- [x] 实现配置管理模块（`config/settings.py`）
- [x] 实现文档处理器基类（策略模式）
- [x] 实现PDF处理器（`processors/pdf_processor.py`）
- [x] 实现向量存储抽象层（`core/vector_store.py`）
- [x] 实现Qdrant存储（`core/qdrant_store.py`）
- [x] 实现FAISS降级存储（`core/faiss_store.py`）
- [x] 实现连接检测和自动降级逻辑（`core/vector_store_manager.py`）

### 阶段三：服务层开发 ✅
- [x] 实现Embedding服务（支持API和本地模型）
- [x] 实现检索服务（相似度搜索）
- [x] 实现LLM服务封装（支持API和本地模型）
- [x] 实现生成服务（RAG + 问题猜测）

### 阶段四：API开发 ✅
- [x] 设计API数据模型（Pydantic Schemas）
- [x] 实现文档上传接口
- [x] 实现文档列表/删除接口
- [x] 实现查询接口（含问题猜测）
- [x] 实现健康检查接口
- [x] 添加API文档（FastAPI自动生成）

### 阶段五：模型集成 ✅
- [x] 集成Embedding模型（支持本地和API）
- [x] 集成LLM模型（支持本地和API）
- [x] 实现模型加载和调用封装
- [x] 添加模型配置管理

### 阶段六：测试与优化
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 测试PDF文档处理流程
- [ ] 测试Qdrant连接和降级
- [ ] 测试API接口
- [ ] 性能优化（批量处理、缓存等）
- [ ] 错误处理和日志记录

### 阶段七：文档与部署
- [ ] 编写README文档
- [ ] 编写API使用文档
- [ ] 编写部署指南
- [ ] 准备Docker配置（可选）
- [ ] 准备启动脚本

### 阶段八：扩展功能（可选）
- [ ] 支持Word文档处理
- [ ] 支持Excel文档处理
- [ ] 支持TXT文档处理
- [ ] 实现文档版本管理
- [ ] 实现用户权限管理
- [ ] 实现查询历史记录
- [ ] 添加Web UI界面（可选）

---

## 🔐 环境变量配置

```bash
# 向量数据库配置
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=rag_documents
USE_QDRANT=true  # false时使用FAISS

# Embedding模型配置
EMBEDDING_MODEL_TYPE=local  # api 或 local
EMBEDDING_MODEL_NAME=bge-large-zh-v1.5
EMBEDDING_API_KEY=
EMBEDDING_API_BASE=

# LLM模型配置
LLM_MODEL_TYPE=local  # api 或 local
LLM_MODEL_NAME=deepseek-r1-distill-qwen-7b
LLM_API_KEY=
LLM_API_BASE=

# 数据存储路径
DATA_DIR=./data
VECTOR_STORE_DIR=./data/vectors
METADATA_DIR=./data/metadata
DOCUMENTS_DIR=./data/documents

# 服务配置
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

---

## 📊 技术难点与解决方案

### 1. 向量数据库降级
- **问题**：Qdrant连接失败时的无缝切换
- **方案**：使用工厂模式和策略模式，统一接口，运行时切换实现

### 2. 问题猜测功能
- **问题**：如何基于用户问题和检索内容生成相关问题
- **方案**：使用LLM的few-shot提示，基于检索到的文档块和用户问题生成相关问题

### 3. 大文档处理
- **问题**：PDF文档过大时的内存和性能问题
- **方案**：流式处理、分批向量化、异步处理

### 4. 模型本地部署
- **问题**：本地模型加载和推理性能
- **方案**：模型量化、GPU加速、批量推理

---

## 🚀 快速开始（待实现）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 3. 初始化数据库
python scripts/init_db.py

# 4. 启动服务
uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# 5. 访问API文档
# http://localhost:8000/docs
```

---

## 📌 注意事项

1. **模型选择**：优先使用本地部署模型，避免API调用限制和成本
2. **数据安全**：企业文档敏感，注意数据加密和访问控制
3. **性能优化**：大规模文档时考虑分布式处理和缓存
4. **可扩展性**：使用策略模式，便于未来扩展其他文档格式
5. **错误处理**：完善的异常处理和日志记录

---

## ✅ 下一步行动

1. **审查本方案**：检查技术选型、目录结构、功能设计是否符合需求
2. **确认模型**：确定最终使用的Embedding和LLM模型
3. **开始实施**：按照Checklist逐步开发
4. **迭代优化**：根据实际使用情况调整和优化

---

*最后更新时间：2025-01-XX*
