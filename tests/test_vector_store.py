"""
测试向量存储
"""
import pytest
import numpy as np
from src.core.faiss_store import FAISSStore
from config.settings import settings


@pytest.fixture
def faiss_store(tmp_path):
    """创建临时 FAISS 存储"""
    store = FAISSStore(
        dimension=128,
        collection_name="test_collection",
        storage_dir=str(tmp_path)
    )
    yield store
    # 清理
    store.clear()


def test_faiss_store_creation(faiss_store):
    """测试 FAISS 存储创建"""
    assert faiss_store is not None
    assert faiss_store.dimension == 128
    assert faiss_store.collection_name == "test_collection"


def test_vector_insertion(faiss_store):
    """测试向量插入"""
    vectors = [np.random.rand(128).astype('float32') for _ in range(5)]
    texts = [f"文本 {i}" for i in range(5)]
    metadatas = [{"index": i} for i in range(5)]
    ids = [f"id_{i}" for i in range(5)]
    
    success = faiss_store.insert_vectors(vectors, texts, metadatas, ids)
    assert success is True
    assert faiss_store.get_vector_count() == 5


def test_vector_search(faiss_store):
    """测试向量搜索"""
    # 插入测试数据
    vectors = [np.random.rand(128).astype('float32') for _ in range(10)]
    texts = [f"文本 {i}" for i in range(10)]
    metadatas = [{"index": i} for i in range(10)]
    ids = [f"id_{i}" for i in range(10)]
    
    faiss_store.insert_vectors(vectors, texts, metadatas, ids)
    
    # 搜索
    query_vector = np.random.rand(128).astype('float32')
    results = faiss_store.search(query_vector, top_k=3)
    
    assert len(results) <= 3
    assert all(hasattr(r, 'id') for r in results)
    assert all(hasattr(r, 'score') for r in results)
    assert all(hasattr(r, 'text') for r in results)


def test_vector_deletion(faiss_store):
    """测试向量删除"""
    # 插入测试数据
    vectors = [np.random.rand(128).astype('float32') for _ in range(5)]
    texts = [f"文本 {i}" for i in range(5)]
    metadatas = [{"index": i} for i in range(5)]
    ids = [f"id_{i}" for i in range(5)]
    
    faiss_store.insert_vectors(vectors, texts, metadatas, ids)
    assert faiss_store.get_vector_count() == 5
    
    # 删除部分向量
    success = faiss_store.delete_by_ids(["id_0", "id_1"])
    assert success is True
    assert faiss_store.get_vector_count() == 3


def test_store_persistence(tmp_path):
    """测试存储持久化"""
    # 创建存储并插入数据
    store1 = FAISSStore(
        dimension=128,
        collection_name="test_persist",
        storage_dir=str(tmp_path)
    )
    
    vectors = [np.random.rand(128).astype('float32') for _ in range(3)]
    texts = ["文本1", "文本2", "文本3"]
    metadatas = [{"i": i} for i in range(3)]
    ids = ["id_1", "id_2", "id_3"]
    
    store1.insert_vectors(vectors, texts, metadatas, ids)
    store1.save()
    
    # 创建新存储并加载
    store2 = FAISSStore(
        dimension=128,
        collection_name="test_persist",
        storage_dir=str(tmp_path)
    )
    store2.load()
    
    assert store2.get_vector_count() == 3


def test_empty_search(faiss_store):
    """测试空索引搜索"""
    query_vector = np.random.rand(128).astype('float32')
    results = faiss_store.search(query_vector, top_k=5)
    assert len(results) == 0


def test_health_check(faiss_store):
    """测试健康检查"""
    health = faiss_store.health_check()
    assert health is True

