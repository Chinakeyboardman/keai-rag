#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统集成测试脚本
测试整个 RAG 系统的功能

使用方法:
    python test_system.py

详细说明请查看:
    - docs/START_SERVER.md
    - docs/QUICK_FIX.md
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_configuration():
    """测试配置加载"""
    print("=" * 60)
    print("1. 测试配置加载")
    print("=" * 60)
    
    try:
        from config.settings import settings
        
        print(f"✅ 配置加载成功")
        print(f"   项目名称: {settings.PROJECT_NAME}")
        print(f"   向量维度: {settings.VECTOR_DIMENSION}")
        print(f"   使用 Qdrant: {settings.USE_QDRANT}")
        print(f"   Embedding 类型: {settings.EMBEDDING_MODEL_TYPE}")
        print(f"   LLM 类型: {settings.LLM_MODEL_TYPE}")
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False


def test_vector_store():
    """测试向量存储"""
    print("\n" + "=" * 60)
    print("2. 测试向量存储")
    print("=" * 60)
    
    try:
        from src.core.vector_store_manager import VectorStoreManager
        from config.settings import settings
        import numpy as np
        
        # 创建管理器
        manager = VectorStoreManager(
            collection_name="test_collection",
            dimension=128,
            use_qdrant=settings.USE_QDRANT,
            qdrant_url=settings.QDRANT_URL,
            faiss_storage_dir=settings.VECTOR_STORE_DIR
        )
        
        print(f"✅ 向量存储初始化成功")
        print(f"   存储类型: {manager.get_store_type()}")
        
        # 测试插入
        store = manager.get_store()
        vectors = [np.random.rand(128).astype('float32') for _ in range(3)]
        texts = ["测试文本1", "测试文本2", "测试文本3"]
        metadatas = [{"index": i} for i in range(3)]
        ids = [f"test_{i}" for i in range(3)]
        
        success = store.insert_vectors(vectors, texts, metadatas, ids)
        print(f"✅ 向量插入: {'成功' if success else '失败'}")
        print(f"   向量数量: {store.get_vector_count()}")
        
        # 测试搜索
        query_vector = np.random.rand(128).astype('float32')
        results = store.search(query_vector, top_k=2)
        print(f"✅ 向量搜索: 找到 {len(results)} 个结果")
        
        # 清理
        store.delete_by_ids(ids)
        manager.close()
        
        return True
    except Exception as e:
        print(f"❌ 向量存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_service():
    """测试 Embedding 服务"""
    print("\n" + "=" * 60)
    print("3. 测试 Embedding 服务")
    print("=" * 60)
    
    try:
        from src.services.embedding_service import get_embedding_service
        
        service = get_embedding_service()
        print(f"✅ Embedding 服务初始化成功")
        print(f"   模型类型: {service.model_type}")
        print(f"   模型名称: {service.model_name}")
        print(f"   向量维度: {service.dimension}")
        
        # 测试单个文本
        text = "这是一个测试文本"
        vector = service.embed_text(text)
        print(f"✅ 单文本向量化成功")
        print(f"   文本: {text}")
        print(f"   向量形状: {vector.shape}")
        
        # 测试批量文本
        texts = ["人工智能", "机器学习", "深度学习"]
        vectors = service.embed_texts(texts)
        print(f"✅ 批量向量化成功")
        print(f"   文本数量: {len(texts)}")
        print(f"   向量数量: {len(vectors)}")
        
        return True
    except Exception as e:
        print(f"❌ Embedding 服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_service():
    """测试 LLM 服务"""
    print("\n" + "=" * 60)
    print("4. 测试 LLM 服务")
    print("=" * 60)
    
    try:
        from src.services.llm_service import get_llm_service
        
        service = get_llm_service()
        print(f"✅ LLM 服务初始化成功")
        print(f"   模型类型: {service.model_type}")
        print(f"   模型名称: {service.model_name}")
        
        # 测试生成
        prompt = "请用一句话解释什么是RAG。"
        print(f"📝 测试提示词: {prompt}")
        print(f"⏳ 生成中...")
        
        response = service.generate(prompt, max_tokens=100)
        print(f"✅ 文本生成成功")
        print(f"   回复: {response}")
        
        return True
    except Exception as e:
        print(f"❌ LLM 服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_processing():
    """测试文档处理"""
    print("\n" + "=" * 60)
    print("5. 测试文档处理")
    print("=" * 60)
    
    try:
        from src.processors.pdf_processor import PDFProcessor
        
        processor = PDFProcessor(chunk_size=500, chunk_overlap=100)
        print(f"✅ PDF 处理器创建成功")
        print(f"   分块大小: {processor.chunk_size}")
        print(f"   重叠大小: {processor.chunk_overlap}")
        
        # 测试文本分割
        test_text = "这是一段测试文本。" * 100
        chunks = processor.split_text(test_text)
        print(f"✅ 文本分割成功")
        print(f"   原文长度: {len(test_text)}")
        print(f"   分割块数: {len(chunks)}")
        
        return True
    except Exception as e:
        print(f"❌ 文档处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_rag_pipeline():
    """测试完整 RAG 流程"""
    print("\n" + "=" * 60)
    print("6. 测试完整 RAG 流程")
    print("=" * 60)
    
    try:
        from src.core.vector_store_manager import VectorStoreManager
        from src.services.embedding_service import get_embedding_service
        from src.services.retrieval_service import RetrievalService
        from src.services.generation_service import GenerationService
        from config.settings import settings
        
        # 1. 初始化服务
        print("📦 初始化服务...")
        manager = VectorStoreManager(
            collection_name="test_rag",
            dimension=settings.VECTOR_DIMENSION,
            use_qdrant=settings.USE_QDRANT,
            qdrant_url=settings.QDRANT_URL,
            faiss_storage_dir=settings.VECTOR_STORE_DIR
        )
        store = manager.get_store()
        embedding_service = get_embedding_service()
        retrieval_service = RetrievalService(store)
        generation_service = GenerationService(retrieval_service)
        print("✅ 服务初始化完成")
        
        # 2. 准备测试文档
        print("\n📄 准备测试文档...")
        documents = [
            "人工智能（AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
            "机器学习是人工智能的一个子领域，它使计算机能够从数据中学习而无需明确编程。",
            "深度学习是机器学习的一个分支，使用多层神经网络来学习数据的复杂模式。",
            "RAG（检索增强生成）是一种结合信息检索和文本生成的技术，用于提高AI系统的准确性。"
        ]
        
        # 3. 向量化并存储
        print("🔄 向量化文档...")
        vectors = embedding_service.embed_texts(documents)
        metadatas = [{"doc_id": f"doc_{i}", "type": "test"} for i in range(len(documents))]
        ids = [f"test_rag_{i}" for i in range(len(documents))]
        
        success = store.insert_vectors(vectors, documents, metadatas, ids)
        print(f"✅ 文档存储: {'成功' if success else '失败'}")
        print(f"   文档数量: {len(documents)}")
        
        # 4. 测试检索
        print("\n🔍 测试检索...")
        query = "什么是RAG？"
        results = retrieval_service.retrieve(query, top_k=2)
        print(f"✅ 检索完成")
        print(f"   查询: {query}")
        print(f"   结果数: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"   [{i}] 分数: {result.score:.4f}")
            print(f"       文本: {result.text[:50]}...")
        
        # 5. 测试生成
        print("\n🤖 测试 RAG 生成...")
        result = generation_service.generate_with_suggestions(
            question=query,
            top_k=2,
            num_suggestions=3
        )
        print(f"✅ 生成完成")
        print(f"   问题: {query}")
        print(f"   答案: {result['answer']}")
        print(f"   来源数: {len(result['sources'])}")
        if result.get('suggested_questions'):
            print(f"   推荐问题:")
            for i, q in enumerate(result['suggested_questions'], 1):
                print(f"     {i}. {q}")
        
        # 6. 清理
        print("\n🧹 清理测试数据...")
        store.delete_by_ids(ids)
        manager.close()
        print("✅ 清理完成")
        
        return True
    except Exception as e:
        print(f"❌ RAG 流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 企业级 RAG 系统 - 集成测试")
    print("=" * 60)
    print()
    
    tests = [
        ("配置加载", test_configuration),
        ("向量存储", test_vector_store),
        ("Embedding服务", test_embedding_service),
        ("LLM服务", test_llm_service),
        ("文档处理", test_document_processing),
        ("完整RAG流程", test_full_rag_pipeline),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 异常: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status} - {name}")
    
    print()
    print(f"总计: {passed}/{total} 通过")
    print()
    
    if passed == total:
        print("🎉 所有测试通过！系统运行正常！")
        return 0
    else:
        print("⚠️  部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())

