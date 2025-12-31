#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
向量存储管理器
实现连接检测和自动降级逻辑
"""

from typing import Optional
from pathlib import Path

from .vector_store import BaseVectorStore
from .qdrant_store import QdrantStore
from .faiss_store import FAISSStore


class VectorStoreManager:
    """
    向量存储管理器
    
    负责：
    1. 检测 Qdrant 连接
    2. 自动降级到 FAISS
    3. 提供统一的向量存储接口
    """
    
    def __init__(
        self,
        collection_name: str,
        dimension: int,
        use_qdrant: bool = True,
        qdrant_url: str = "http://localhost:6333",
        qdrant_api_key: Optional[str] = None,
        faiss_storage_dir: str = "./data/vectors"
    ):
        """
        初始化向量存储管理器
        
        Args:
            collection_name: 集合名称
            dimension: 向量维度
            use_qdrant: 是否尝试使用 Qdrant
            qdrant_url: Qdrant 服务地址
            qdrant_api_key: Qdrant API 密钥
            faiss_storage_dir: FAISS 存储目录
        """
        self.collection_name = collection_name
        self.dimension = dimension
        self.use_qdrant = use_qdrant
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.faiss_storage_dir = faiss_storage_dir
        
        self.store: Optional[BaseVectorStore] = None
        self.store_type: str = ""
        
        # 初始化存储
        self._initialize_store()
    
    def _initialize_store(self):
        """初始化向量存储"""
        # 如果配置使用 Qdrant，先尝试连接
        if self.use_qdrant:
            if self._try_qdrant():
                return
            else:
                print("⚠️  Qdrant 连接失败，降级使用 FAISS")
        
        # 使用 FAISS 作为降级方案
        self._use_faiss()
    
    def _try_qdrant(self) -> bool:
        """
        尝试连接 Qdrant
        
        Returns:
            是否连接成功
        """
        try:
            print(f"🔍 尝试连接 Qdrant: {self.qdrant_url}")
            
            # 测试连接
            if not QdrantStore.test_connection(self.qdrant_url, self.qdrant_api_key):
                print("❌ Qdrant 连接测试失败")
                return False
            
            # 创建 Qdrant 存储
            self.store = QdrantStore(
                collection_name=self.collection_name,
                dimension=self.dimension,
                url=self.qdrant_url,
                api_key=self.qdrant_api_key
            )
            self.store_type = "Qdrant"
            
            print(f"✅ Qdrant 连接成功")
            print(f"   集合: {self.collection_name}")
            print(f"   向量数量: {self.store.get_vector_count()}")
            
            return True
            
        except Exception as e:
            print(f"❌ Qdrant 初始化失败: {e}")
            return False
    
    def _use_faiss(self):
        """使用 FAISS 作为存储"""
        try:
            print(f"🔧 使用 FAISS 本地存储")
            
            self.store = FAISSStore(
                collection_name=self.collection_name,
                dimension=self.dimension,
                storage_dir=self.faiss_storage_dir
            )
            self.store_type = "FAISS"
            
            print(f"✅ FAISS 存储初始化成功")
            print(f"   存储目录: {self.faiss_storage_dir}")
            print(f"   集合: {self.collection_name}")
            print(f"   向量数量: {self.store.get_vector_count()}")
            
        except Exception as e:
            raise RuntimeError(f"FAISS 初始化失败: {e}")
    
    def get_store(self) -> BaseVectorStore:
        """
        获取向量存储实例
        
        Returns:
            向量存储实例
        """
        if self.store is None:
            raise RuntimeError("向量存储未初始化")
        return self.store
    
    def get_store_type(self) -> str:
        """
        获取当前使用的存储类型
        
        Returns:
            存储类型（"Qdrant" 或 "FAISS"）
        """
        return self.store_type
    
    def is_using_qdrant(self) -> bool:
        """
        是否正在使用 Qdrant
        
        Returns:
            是否使用 Qdrant
        """
        return self.store_type == "Qdrant"
    
    def is_using_faiss(self) -> bool:
        """
        是否正在使用 FAISS
        
        Returns:
            是否使用 FAISS
        """
        return self.store_type == "FAISS"
    
    def get_store_info(self) -> dict:
        """
        获取存储信息
        
        Returns:
            存储信息字典
        """
        if self.store is None:
            return {"status": "未初始化"}
        
        info = self.store.get_store_info()
        info["store_type"] = self.store_type
        info["is_degraded"] = self.is_using_faiss() and self.use_qdrant
        
        return info
    
    def retry_qdrant(self) -> bool:
        """
        重试连接 Qdrant
        
        Returns:
            是否连接成功
        """
        if self.is_using_qdrant():
            print("ℹ️  已经在使用 Qdrant")
            return True
        
        print("🔄 尝试重新连接 Qdrant...")
        
        if self._try_qdrant():
            print("✅ 成功切换到 Qdrant")
            return True
        else:
            print("❌ Qdrant 仍然不可用，继续使用 FAISS")
            return False
    
    def close(self):
        """关闭存储连接"""
        if self.store:
            self.store.close()


def create_vector_store(
    collection_name: str,
    dimension: int,
    use_qdrant: bool = True,
    qdrant_url: str = "http://localhost:6333",
    qdrant_api_key: Optional[str] = None,
    faiss_storage_dir: str = "./data/vectors"
) -> BaseVectorStore:
    """
    创建向量存储（工厂函数）
    
    Args:
        collection_name: 集合名称
        dimension: 向量维度
        use_qdrant: 是否尝试使用 Qdrant
        qdrant_url: Qdrant 服务地址
        qdrant_api_key: Qdrant API 密钥
        faiss_storage_dir: FAISS 存储目录
        
    Returns:
        向量存储实例
    """
    manager = VectorStoreManager(
        collection_name=collection_name,
        dimension=dimension,
        use_qdrant=use_qdrant,
        qdrant_url=qdrant_url,
        qdrant_api_key=qdrant_api_key,
        faiss_storage_dir=faiss_storage_dir
    )
    return manager.get_store()


if __name__ == "__main__":
    """测试向量存储管理器"""
    print("=" * 60)
    print("向量存储管理器测试")
    print("=" * 60)
    print()
    
    # 测试 1: 尝试使用 Qdrant（可能失败）
    print("测试 1: 尝试使用 Qdrant")
    print("-" * 60)
    manager1 = VectorStoreManager(
        collection_name="test_collection_1",
        dimension=128,
        use_qdrant=True,
        qdrant_url="http://localhost:6333",
        faiss_storage_dir="./test_vectors"
    )
    print(f"存储类型: {manager1.get_store_type()}")
    print(f"存储信息: {manager1.get_store_info()}")
    print()
    
    # 测试 2: 强制使用 FAISS
    print("测试 2: 强制使用 FAISS")
    print("-" * 60)
    manager2 = VectorStoreManager(
        collection_name="test_collection_2",
        dimension=128,
        use_qdrant=False,
        faiss_storage_dir="./test_vectors"
    )
    print(f"存储类型: {manager2.get_store_type()}")
    print(f"存储信息: {manager2.get_store_info()}")
    print()
    
    # 清理
    manager1.close()
    manager2.close()
    
    # 删除测试集合
    if manager1.get_store():
        manager1.get_store().delete_collection()
    if manager2.get_store():
        manager2.get_store().delete_collection()
    
    print("✅ 测试完成")

