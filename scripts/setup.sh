#!/bin/bash
# 项目初始化脚本

echo "========================================"
echo "🚀 企业级 RAG 系统 - 项目初始化"
echo "========================================"
echo ""

# 检查 Python 版本
echo "🔍 检查 Python 版本..."
python3 --version || { echo "❌ Python3 未安装"; exit 1; }
echo ""

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "✅ 虚拟环境已存在"
fi
echo ""

# 激活虚拟环境提示
echo "💡 请手动激活虚拟环境:"
echo "   source venv/bin/activate  (macOS/Linux)"
echo "   venv\\Scripts\\activate    (Windows)"
echo ""

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "📝 创建环境变量文件..."
    if [ -f "env.example" ]; then
        cp env.example .env
        echo "✅ 已从 env.example 创建 .env 文件"
        echo "⚠️  请编辑 .env 文件配置必要参数"
    else
        echo "⚠️  未找到 env.example 文件"
    fi
else
    echo "✅ .env 文件已存在"
fi
echo ""

# 安装依赖提示
echo "📦 下一步: 安装依赖"
echo "   pip install -r requirements.txt"
echo ""

# 初始化数据库提示
echo "🔧 然后: 初始化数据库"
echo "   python scripts/init_db.py"
echo ""

# 启动服务提示
echo "🚀 最后: 启动服务"
echo "   uvicorn src.api.main:app --reload"
echo ""

echo "========================================"
echo "✅ 项目结构初始化完成"
echo "========================================"

