# 快速开始指南

本指南将帮助您快速搭建并运行企业级 RAG 系统。

## 📋 前置要求

- **Python**: 3.8 或更高版本
- **内存**: 至少 8GB RAM（推荐 16GB）
- **磁盘**: 至少 20GB 可用空间（用于存储模型）
- **操作系统**: macOS / Linux / Windows

## 🚀 快速安装（5分钟）

### 步骤 1: 克隆或进入项目目录

```bash
cd /Users/chenjiawei/Study/ai/zhihu/13-Embeddings和向量数据库/china-pdf-rag
```

### 步骤 2: 运行自动化安装脚本

```bash
bash scripts/setup.sh
```

这个脚本会：
- ✅ 检查 Python 版本
- ✅ 创建虚拟环境（如果不存在）
- ✅ 提示您激活虚拟环境
- ✅ 创建 .env 配置文件

### 步骤 3: 激活虚拟环境

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 步骤 4: 安装依赖

```bash
pip install -r requirements.txt
```

这将安装所有必要的 Python 包，包括：
- FastAPI（Web 框架）
- LangChain（文档处理）
- FAISS（向量数据库）
- PyPDF2（PDF 处理）
- Transformers（模型加载）
- 以及其他依赖...

**注意**: 完整安装可能需要 5-10 分钟，取决于您的网络速度。

### 步骤 5: 配置环境变量

```bash
cp env.example .env
```

使用文本编辑器打开 `.env` 文件并配置：

```bash
# 最小配置（使用 FAISS 降级方案）
USE_QDRANT=false
EMBEDDING_MODEL_TYPE=local
EMBEDDING_MODEL_PATH=./models/m3e-large
LLM_MODEL_TYPE=local
LLM_MODEL_PATH=/Users/chenjiawei/Public/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
```

**重要**: 确保 `LLM_MODEL_PATH` 指向正确的 DeepSeek-R1 模型路径！

### 步骤 6: 下载 Embedding 模型（如果使用本地模型）

如果您选择使用本地 Embedding 模型（m3e-large），需要下载：

```bash
# 创建模型目录
mkdir -p models

# 使用 huggingface-cli 下载（推荐）
pip install huggingface_hub
huggingface-cli download moka-ai/m3e-large --local-dir ./models/m3e-large

# 或使用 Git LFS
cd models
git clone https://huggingface.co/moka-ai/m3e-large
cd ..
```

### 步骤 7: 初始化数据库

```bash
python scripts/init_db.py
```

这个脚本会：
- ✅ 创建必要的数据目录
- ✅ 检查环境变量配置
- ✅ 验证 FAISS 安装
- ✅ 尝试连接 Qdrant（可选）

**预期输出：**
```
====================================
🚀 企业级 RAG 系统 - 数据库初始化
====================================

🔧 初始化数据目录...
✅ 创建目录: data/documents
✅ 创建目录: data/vectors
✅ 创建目录: data/metadata
✅ 创建目录: logs
✅ 数据目录初始化完成

🔧 检查环境变量配置...
✅ 环境变量文件存在

🔧 初始化 FAISS 向量存储...
✅ FAISS 初始化成功 (维度: 1024)

====================================
📊 初始化总结
====================================
✅ 目录结构: 完成
✅ 环境变量: 已配置
✅ FAISS 存储: 正常
⚠️  Qdrant 连接: 将使用降级方案

✅ 初始化完成！可以启动服务了
   uvicorn src.api.main:app --reload
```

## ⏭️ 下一步

恭喜！阶段一（项目初始化）已完成 ✅

现在您已经完成了：
- ✅ 项目目录结构
- ✅ Python 虚拟环境
- ✅ 依赖包安装
- ✅ 环境变量配置
- ✅ 数据库初始化

**接下来的开发任务：**

### 阶段二：核心模块开发
1. 实现配置管理模块（`config/settings.py`）
2. 实现文档处理器（`src/processors/pdf_processor.py`）
3. 实现向量存储层（`src/core/vector_store.py`）
4. 实现 FAISS 存储（`src/core/faiss_store.py`）

### 阶段三：服务层开发
5. 实现 Embedding 服务
6. 实现检索服务
7. 实现 LLM 服务
8. 实现生成服务

### 阶段四：API 开发
9. 实现文档上传接口
10. 实现查询接口

查看 `checklist.md` 了解完整的开发计划。

## 🔧 常见问题

### Q: 如何验证 DeepSeek-R1 模型路径是否正确？

```bash
ls -lh /Users/chenjiawei/Public/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B
```

应该看到以下文件：
- `config.json`
- `tokenizer.json`
- `model.safetensors.index.json`
- `model-00001-of-000002.safetensors`
- `model-00002-of-000002.safetensors`

### Q: FAISS 安装失败怎么办？

如果 `pip install faiss-cpu` 失败，尝试：

```bash
# macOS
conda install -c conda-forge faiss-cpu

# 或使用预编译包
pip install faiss-cpu --no-cache-dir
```

### Q: 如何使用 Qdrant 而不是 FAISS？

1. 安装并启动 Qdrant（使用 Docker）:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

2. 修改 `.env` 文件:
```bash
USE_QDRANT=true
QDRANT_URL=http://localhost:6333
```

3. 重新运行初始化:
```bash
python scripts/init_db.py
```

### Q: 虚拟环境激活后还是提示找不到模块？

确保在虚拟环境中安装依赖：

```bash
# 确认虚拟环境已激活（命令行前应有 (venv) 标识）
which python  # 应该指向 venv/bin/python

# 重新安装依赖
pip install -r requirements.txt
```

### Q: 如何测试系统是否正常工作？

运行初始化脚本并检查输出：

```bash
python scripts/init_db.py
```

所有检查应该显示 ✅ 或 ⚠️（警告但不影响运行）。

## 📞 获取帮助

- 查看 `README.md` - 项目概述和功能说明
- 查看 `PROJECT_STRUCTURE.md` - 项目结构详解
- 查看 `checklist.md` - 完整开发计划和进度

## 🎉 完成！

您已成功完成项目初始化！系统已准备好进入下一阶段的开发。

**提示**: 建议立即提交一个 Git 提交，保存当前的初始化状态：

```bash
git add .
git commit -m "feat: 完成项目初始化（阶段一）"
```

现在可以开始开发核心模块了！🚀

