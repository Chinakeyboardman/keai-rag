# 项目结构说明

## 目录结构

```
china-pdf-rag/
├── README.md                    # 项目说明文档
├── requirements.txt             # Python 依赖列表
├── env.example                  # 环境变量配置示例
├── .gitignore                   # Git 忽略规则
│
├── docs/                        # 📚 项目文档目录
│   ├── README.md               # 文档索引
│   ├── checklist.md            # 开发计划清单
│   ├── PROJECT_STRUCTURE.md    # 本文档
│   ├── QUICKSTART.md           # 快速开始指南
│   └── STAGE1_COMPLETED.md     # 阶段一完成报告
│
├── config/                      # 配置模块
│   └── __init__.py
│   ├── settings.py             # (待创建) 全局配置管理
│   └── model_config.py         # (待创建) 模型配置
│
├── src/                         # 源代码目录
│   ├── __init__.py
│   │
│   ├── api/                     # API 接口层
│   │   ├── __init__.py
│   │   ├── main.py             # (待创建) FastAPI 应用入口
│   │   ├── routes/             # 路由模块
│   │   │   ├── __init__.py
│   │   │   ├── document.py    # (待创建) 文档管理接口
│   │   │   ├── query.py       # (待创建) 查询接口
│   │   │   └── health.py      # (待创建) 健康检查
│   │   └── schemas/            # 数据模型
│   │       ├── __init__.py
│   │       ├── document.py    # (待创建) 文档相关数据模型
│   │       └── query.py       # (待创建) 查询相关数据模型
│   │
│   ├── core/                    # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── document_processor.py    # (待创建) 文档处理核心
│   │   ├── vector_store.py          # (待创建) 向量存储抽象层
│   │   ├── qdrant_store.py          # (待创建) Qdrant 实现
│   │   ├── faiss_store.py           # (待创建) FAISS 降级实现
│   │   └── llm_service.py           # (待创建) LLM 服务封装
│   │
│   ├── processors/              # 文档处理器（策略模式）
│   │   ├── __init__.py
│   │   ├── base.py             # (待创建) 处理器基类
│   │   ├── pdf_processor.py   # (待创建) PDF 处理器
│   │   └── txt_processor.py   # (待创建) TXT 处理器（预留）
│   │
│   ├── services/                # 服务层
│   │   ├── __init__.py
│   │   ├── embedding_service.py     # (待创建) Embedding 服务
│   │   ├── retrieval_service.py     # (待创建) 检索服务
│   │   └── generation_service.py    # (待创建) 生成服务
│   │
│   └── utils/                   # 工具函数
│       ├── __init__.py
│       ├── logger.py           # (待创建) 日志工具
│       └── exceptions.py       # (待创建) 自定义异常
│
├── data/                        # 数据存储目录
│   ├── documents/              # 上传的原始文档
│   ├── vectors/                # 向量数据库存储（FAISS）
│   └── metadata/               # 元数据存储
│
├── logs/                        # 日志文件目录
│   └── .gitkeep
│
├── tests/                       # 测试文件
│   ├── __init__.py
│   ├── test_api.py            # (待创建) API 测试
│   └── test_services.py       # (待创建) 服务层测试
│
├── scripts/                     # 脚本文件
│   ├── init_db.py             # ✅ 数据库初始化脚本
│   ├── setup.sh               # ✅ 项目初始化脚本
│   └── migrate.py             # (待创建) 数据迁移脚本
│
└── venv/                        # Python 虚拟环境 (不纳入版本控制)
```

## 模块说明

### 1. API 层 (src/api/)
负责接收 HTTP 请求，处理请求参数验证，调用业务逻辑，返回响应。

**主要文件：**
- `main.py`: FastAPI 应用入口，配置 CORS、路由等
- `routes/`: 各个功能模块的路由定义
- `schemas/`: Pydantic 数据模型，用于请求/响应验证

### 2. 核心层 (src/core/)
核心业务逻辑，包括文档处理、向量存储、LLM 调用等。

**主要文件：**
- `document_processor.py`: 文档处理总控制器
- `vector_store.py`: 向量存储抽象接口
- `qdrant_store.py`: Qdrant 向量数据库实现
- `faiss_store.py`: FAISS 本地向量库实现（降级方案）
- `llm_service.py`: LLM 模型调用封装

### 3. 处理器层 (src/processors/)
使用策略模式，支持不同文档格式的处理。

**主要文件：**
- `base.py`: 文档处理器基类
- `pdf_processor.py`: PDF 文档处理器
- `txt_processor.py`: 文本文档处理器（预留）

### 4. 服务层 (src/services/)
封装可复用的业务服务。

**主要文件：**
- `embedding_service.py`: 文本向量化服务
- `retrieval_service.py`: 文档检索服务
- `generation_service.py`: 答案生成和问题推荐服务

### 5. 工具层 (src/utils/)
通用工具函数和辅助类。

**主要文件：**
- `logger.py`: 日志配置和管理
- `exceptions.py`: 自定义异常类

### 6. 配置层 (config/)
应用配置管理。

**主要文件：**
- `settings.py`: 从环境变量加载配置
- `model_config.py`: 模型相关配置

## 数据流程

```
用户上传 PDF
    ↓
API 接收请求 (src/api/routes/document.py)
    ↓
文档处理器 (src/processors/pdf_processor.py)
    ↓
文本分块 + Embedding (src/services/embedding_service.py)
    ↓
向量存储 (src/core/qdrant_store.py 或 faiss_store.py)


用户提问
    ↓
API 接收请求 (src/api/routes/query.py)
    ↓
检索服务 (src/services/retrieval_service.py)
    ↓
向量查询 (src/core/vector_store.py)
    ↓
生成服务 (src/services/generation_service.py)
    ↓
LLM 生成答案 + 推荐问题 (src/core/llm_service.py)
    ↓
返回结果给用户
```

## 设计模式

### 1. 策略模式 (Strategy Pattern)
文档处理器使用策略模式，便于扩展新的文档格式：
```python
# base.py
class BaseProcessor(ABC):
    @abstractmethod
    def process(self, file_path: str) -> List[str]:
        pass

# pdf_processor.py
class PDFProcessor(BaseProcessor):
    def process(self, file_path: str) -> List[str]:
        # PDF 处理逻辑
        pass
```

### 2. 工厂模式 (Factory Pattern)
向量存储使用工厂模式，根据配置选择实现：
```python
def create_vector_store(use_qdrant: bool):
    if use_qdrant:
        return QdrantStore()
    else:
        return FAISSStore()
```

### 3. 依赖注入 (Dependency Injection)
FastAPI 的依赖注入系统用于服务实例管理。

## 开发流程

### 阶段一：项目初始化 ✅
- [x] 创建项目目录结构
- [x] 配置 Python 虚拟环境
- [x] 编写 requirements.txt
- [x] 配置 env.example 环境变量模板
- [x] 初始化 Git 仓库

### 阶段二：核心模块开发（进行中）
- [ ] 实现配置管理模块
- [ ] 实现文档处理器
- [ ] 实现向量存储层
- [ ] 实现降级逻辑

### 阶段三：服务层开发
- [ ] Embedding 服务
- [ ] 检索服务
- [ ] LLM 服务
- [ ] 生成服务

### 阶段四：API 开发
- [ ] 设计数据模型
- [ ] 实现各个接口
- [ ] API 文档

### 阶段五：模型集成
- [ ] 集成 m3e-large
- [ ] 集成 DeepSeek-R1
- [ ] 模型配置管理

### 阶段六：测试与优化
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化

### 阶段七：文档与部署
- [ ] 完善文档
- [ ] 部署指南

## 环境变量说明

参考 `env.example` 文件，主要配置项：

| 配置项 | 说明 | 示例值 |
|--------|------|--------|
| USE_QDRANT | 是否使用 Qdrant | true/false |
| QDRANT_URL | Qdrant 服务地址 | http://localhost:6333 |
| EMBEDDING_MODEL_TYPE | Embedding 模型类型 | local/api |
| EMBEDDING_MODEL_PATH | 本地模型路径 | ./models/m3e-large |
| LLM_MODEL_TYPE | LLM 模型类型 | local/api |
| LLM_MODEL_PATH | 本地模型路径 | /path/to/deepseek-r1 |
| CHUNK_SIZE | 文本分块大小 | 1000 |
| CHUNK_OVERLAP | 文本重叠大小 | 200 |

## 快速开始

```bash
# 1. 运行初始化脚本
bash scripts/setup.sh

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp env.example .env
# 编辑 .env 文件

# 5. 初始化数据库
python scripts/init_db.py

# 6. 启动服务
uvicorn src.api.main:app --reload
```

## 注意事项

1. **虚拟环境**: 建议使用虚拟环境隔离依赖
2. **模型路径**: 确保 DeepSeek-R1 模型路径配置正确
3. **Qdrant**: 本地开发可使用 Docker 运行 Qdrant
4. **GPU**: 如有 GPU，可安装 faiss-gpu 提升性能

## 下一步

查看 `checklist.md` 了解详细的开发计划和进度。

