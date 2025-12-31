#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Qdrant 向量存储实现
使用 Qdrant 作为主要的向量数据库
"""

from typing import List, Dict, Any, Optional
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)

from .vector_store import BaseVectorStore, VectorSearchResult


class QdrantStore(BaseVectorStore):
    """Qdrant 向量存储实现"""
    
    def __init__(
        self,
        collection_name: str,
        dimension: int,
        url: str = "http://localhost:6333",
        api_key: Optional[str] = None
    ):
        """
        初始化 Qdrant 存储
        
        Args:
            collection_name: 集合名称
            dimension: 向量维度
            url: Qdrant 服务地址
            api_key: API 密钥（可选）
        """
        super().__init__(collection_name, dimension)
        self.url = url
        self.api_key = api_key
        
        # 创建客户端
        try:
            self.client = QdrantClient(url=url, api_key=api_key)
            # 测试连接
            self.client.get_collections()
        except Exception as e:
            raise ConnectionError(f"无法连接到 Qdrant: {e}")
        
        # 如果集合不存在，创建它
        if not self.collection_exists():
            self.create_collection()
    
    def create_collection(self) -> bool:
        """
        创建集合
        
        Returns:
            是否创建成功
        """
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE
                )
            )
            return True
        except Exception as e:
            print(f"创建 Qdrant 集合失败: {e}")
            return False
    
    def collection_exists(self) -> bool:
        """
        检查集合是否存在
        
        Returns:
            集合是否存在
        """
        try:
            collections = self.client.get_collections()
            return any(
                col.name == self.collection_name
                for col in collections.collections
            )
        except Exception as e:
            print(f"检查集合失败: {e}")
            return False
    
    def delete_collection(self) -> bool:
        """
        删除集合
        
        Returns:
            是否删除成功
        """
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            return True
        except Exception as e:
            print(f"删除 Qdrant 集合失败: {e}")
            return False
    
    def insert_vectors(
        self,
        vectors: List[np.ndarray],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        插入向量
        
        Args:
            vectors: 向量列表
            texts: 文本列表
            metadatas: 元数据列表
            ids: ID 列表（可选）
            
        Returns:
            是否插入成功
        """
        try:
            import uuid
            from src.utils.logger import logger
            
            # 验证输入
            if not (len(vectors) == len(texts) == len(metadatas)):
                raise ValueError("向量、文本和元数据数量必须一致")
            
            # 生成 ID（如果未提供）
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
            
            # Qdrant 的点 ID 必须是纯 UUID 或整数
            # 如果传入的 ID 包含下划线（如 document_id_chunk_N），需要转换为纯 UUID
            qdrant_ids = []
            for original_id in ids:
                # 检查是否是有效的 UUID 格式
                try:
                    # 尝试解析为 UUID
                    uuid.UUID(original_id)
                    qdrant_ids.append(original_id)
                except ValueError:
                    # 如果不是有效的 UUID，生成新的 UUID
                    # 将原始 ID 存储在 payload 中
                    new_id = str(uuid.uuid4())
                    qdrant_ids.append(new_id)
                    logger.debug(f"将点 ID 从 '{original_id}' 转换为 UUID '{new_id}'")
            
            # 构建点数据
            points = []
            for qdrant_id, original_id, vector, text, metadata in zip(qdrant_ids, ids, vectors, texts, metadatas):
                payload = {
                    "text": text,
                    "original_id": original_id,  # 保存原始 ID
                    **metadata
                }
                point = PointStruct(
                    id=qdrant_id,  # 使用纯 UUID
                    vector=vector.tolist(),
                    payload=payload
                )
                points.append(point)
            
            # 批量插入
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            return True
        except Exception as e:
            print(f"插入向量失败: {e}")
            return False
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        搜索相似向量
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_dict: 过滤条件（可选）
            
        Returns:
            搜索结果列表
        """
        try:
            # 构建过滤条件
            query_filter = None
            if filter_dict:
                conditions = []
                for key, value in filter_dict.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    query_filter = Filter(must=conditions)
            
            # 搜索
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=top_k,
                query_filter=query_filter
            )
            
            # 构建结果
            results = []
            for hit in search_result:
                result = VectorSearchResult(
                    id=str(hit.id),
                    score=hit.score,
                    text=hit.payload.get("text", ""),
                    metadata={k: v for k, v in hit.payload.items() if k != "text"}
                )
                results.append(result)
            
            return results
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def delete_by_ids(self, ids: List[str]) -> bool:
        """
        根据 ID 删除向量
        
        Args:
            ids: ID 列表
            
        Returns:
            是否删除成功
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=ids
            )
            return True
        except Exception as e:
            print(f"删除向量失败: {e}")
            return False
    
    def get_chunk_ids_by_document_id(self, document_id: str) -> List[str]:
        """
        根据文档 ID 查找所有相关的块 ID
        
        Args:
            document_id: 文档 ID
            
        Returns:
            块 ID 列表（原始 ID）
        """
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            # 使用过滤器查询
            results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=10000  # 假设一个文档最多有 10000 个块
            )
            
            # 从 payload 中获取原始 ID
            chunk_ids = []
            for point in results[0]:
                # 优先使用 original_id，否则使用 Qdrant ID
                original_id = point.payload.get("original_id", str(point.id))
                chunk_ids.append(original_id)
            
            return chunk_ids
        except Exception as e:
            from src.utils.logger import logger
            logger.error(f"查找块 ID 失败: {e}")
            return []
    
    def get_vector_count(self) -> int:
        """
        获取向量数量
        
        Returns:
            向量数量
        """
        try:
            collection_info = self.client.get_collection(
                collection_name=self.collection_name
            )
            return collection_info.points_count
        except Exception as e:
            print(f"获取向量数量失败: {e}")
            return 0
    
    def close(self):
        """关闭连接"""
        # Qdrant 客户端会自动管理连接
        pass
    
    @staticmethod
    def test_connection(url: str, api_key: Optional[str] = None) -> bool:
        """
        测试 Qdrant 连接
        
        Args:
            url: Qdrant 服务地址
            api_key: API 密钥（可选）
            
        Returns:
            是否连接成功
        """
        try:
            client = QdrantClient(url=url, api_key=api_key)
            client.get_collections()
            return True
        except Exception:
            return False


if __name__ == "__main__":
    """测试 Qdrant 存储"""
    import sys
    
    print("=" * 60)
    print("Qdrant 存储测试")
    print("=" * 60)
    print()
    
    # 测试连接
    url = "http://localhost:6333"
    print(f"🔍 测试连接: {url}")
    if not QdrantStore.test_connection(url):
        print("❌ 无法连接到 Qdrant")
        print("   请确保 Qdrant 服务正在运行:")
        print("   docker run -p 6333:6333 qdrant/qdrant")
        sys.exit(1)
    print("✅ 连接成功")
    print()
    
    # 创建存储
    try:
        store = QdrantStore(
            collection_name="test_collection",
            dimension=128,
            url=url
        )
        print("✅ Qdrant 存储创建成功")
        print(f"   {store.get_store_info()}")
        print()
        
        # 插入测试向量
        print("📥 插入测试向量...")
        vectors = [np.random.rand(128).astype('float32') for _ in range(5)]
        texts = [f"测试文本 {i}" for i in range(5)]
        metadatas = [{"index": i, "type": "test"} for i in range(5)]
        ids = [f"test_vec_{i}" for i in range(5)]
        
        success = store.insert_vectors(vectors, texts, metadatas, ids)
        print(f"   插入{'成功' if success else '失败'}")
        print(f"   向量数量: {store.get_vector_count()}")
        print()
        
        # 搜索测试
        print("🔍 搜索测试...")
        query_vector = np.random.rand(128).astype('float32')
        results = store.search(query_vector, top_k=3)
        print(f"   找到 {len(results)} 个结果")
        for i, result in enumerate(results, 1):
            print(f"   {i}. ID: {result.id}, Score: {result.score:.4f}, Text: {result.text}")
        print()
        
        # 过滤搜索测试
        print("🔍 过滤搜索测试...")
        results = store.search(query_vector, top_k=3, filter_dict={"type": "test"})
        print(f"   找到 {len(results)} 个结果（type=test）")
        print()
        
        # 删除测试
        print("🗑️  删除测试...")
        success = store.delete_by_ids(["test_vec_0"])
        print(f"   删除{'成功' if success else '失败'}")
        print(f"   剩余向量: {store.get_vector_count()}")
        print()
        
        # 清理
        store.delete_collection()
        print("✅ 测试完成，已清理测试数据")
        
    except ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

