#!/bin/bash
# 一键启动脚本

echo "============================================"
echo "🚀 启动企业级 RAG 系统"
echo "============================================"
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 scripts/setup.sh"
    exit 1
fi

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source venv/bin/activate

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，从模板创建..."
    cp env.example .env
    echo "✅ 已创建 .env 文件，请编辑配置后重新运行"
    echo ""
    echo "最小配置示例："
    echo "  USE_QDRANT=false"
    echo "  EMBEDDING_MODEL_TYPE=api"
    echo "  EMBEDDING_API_KEY=your_key"
    echo "  LLM_MODEL_TYPE=api"
    echo "  LLM_API_KEY=your_key"
    exit 1
fi

# 创建必要的目录
echo "📁 创建数据目录..."
mkdir -p data/documents data/vectors data/metadata logs

# 启动服务
echo ""
echo "============================================"
echo "🌐 启动 Web 服务..."
echo "============================================"
echo ""
echo "访问地址："
echo "  - Web UI:  http://localhost:8000"
echo "  - API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 设置 HuggingFace 离线模式（避免速率限制）
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1

# 启动 uvicorn
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

