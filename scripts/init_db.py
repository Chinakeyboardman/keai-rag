#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
用于初始化向量数据库和元数据存储
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def init_directories():
    """初始化数据目录"""
    print("🔧 初始化数据目录...")
    
    directories = [
        "data/documents",
        "data/vectors",
        "data/metadata",
        "logs",
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 创建目录: {directory}")
    
    print("✅ 数据目录初始化完成\n")


def check_env_file():
    """检查环境变量文件"""
    print("🔧 检查环境变量配置...")
    
    env_file = project_root / ".env"
    env_example = project_root / "env.example"
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  未找到 .env 文件")
            print(f"📄 请复制 env.example 为 .env 并配置参数:")
            print(f"   cp env.example .env")
        else:
            print("❌ 未找到 env.example 文件")
        return False
    else:
        print("✅ 环境变量文件存在")
        return True
    
    print()


def init_faiss_storage():
    """初始化 FAISS 存储"""
    print("🔧 初始化 FAISS 向量存储...")
    
    try:
        import faiss
        import numpy as np
        
        # 创建一个简单的索引来验证 FAISS 工作正常
        dimension = 1024
        index = faiss.IndexFlatL2(dimension)
        
        print(f"✅ FAISS 初始化成功 (维度: {dimension})")
        print(f"   索引类型: {type(index).__name__}")
        return True
    except ImportError:
        print("⚠️  FAISS 未安装，请运行: pip install faiss-cpu")
        return False
    except Exception as e:
        print(f"❌ FAISS 初始化失败: {e}")
        return False
    
    print()


def check_qdrant_connection():
    """检查 Qdrant 连接（可选）"""
    print("🔧 检查 Qdrant 连接...")
    
    try:
        from qdrant_client import QdrantClient
        
        # 尝试连接本地 Qdrant
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        
        try:
            client = QdrantClient(url=qdrant_url)
            collections = client.get_collections()
            print(f"✅ Qdrant 连接成功: {qdrant_url}")
            print(f"   现有集合数: {len(collections.collections)}")
            return True
        except Exception as e:
            print(f"⚠️  无法连接到 Qdrant: {e}")
            print(f"   将使用 FAISS 作为降级方案")
            return False
            
    except ImportError:
        print("⚠️  Qdrant 客户端未安装，请运行: pip install qdrant-client")
        return False
    
    print()


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 企业级 RAG 系统 - 数据库初始化")
    print("=" * 60)
    print()
    
    # 1. 初始化目录
    init_directories()
    
    # 2. 检查环境变量
    env_exists = check_env_file()
    
    # 3. 初始化 FAISS
    faiss_ok = init_faiss_storage()
    
    # 4. 检查 Qdrant（可选）
    qdrant_ok = check_qdrant_connection()
    
    # 总结
    print("=" * 60)
    print("📊 初始化总结")
    print("=" * 60)
    print(f"✅ 目录结构: 完成")
    print(f"{'✅' if env_exists else '⚠️ '} 环境变量: {'已配置' if env_exists else '需要配置'}")
    print(f"{'✅' if faiss_ok else '❌'} FAISS 存储: {'正常' if faiss_ok else '异常'}")
    print(f"{'✅' if qdrant_ok else '⚠️ '} Qdrant 连接: {'正常' if qdrant_ok else '将使用降级方案'}")
    print()
    
    if not env_exists:
        print("⚠️  下一步: 配置环境变量")
        print("   cp env.example .env")
        print("   编辑 .env 文件")
        print()
    
    if faiss_ok or qdrant_ok:
        print("✅ 初始化完成！可以启动服务了")
        print("   uvicorn src.api.main:app --reload")
    else:
        print("❌ 初始化失败，请检查依赖安装")
        print("   pip install -r requirements.txt")
    
    print()


if __name__ == "__main__":
    main()

