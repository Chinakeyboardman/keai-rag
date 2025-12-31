#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
向量存储抽象层
定义统一的向量存储接口，支持多种向量数据库实现
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class VectorSearchResult:
    """向量搜索结果"""
    id: str
    score: float
    text: str
    metadata: Dict[str, Any]


class BaseVectorStore(ABC):
    """向量存储基类"""
    
    def __init__(self, collection_name: str, dimension: int):
        """
        初始化向量存储
        
        Args:
            collection_name: 集合名称
            dimension: 向量维度
        """
        self.collection_name = collection_name
        self.dimension = dimension
    
    @abstractmethod
    def create_collection(self) -> bool:
        """
        创建集合
        
        Returns:
            是否创建成功
        """
        pass
    
    @abstractmethod
    def collection_exists(self) -> bool:
        """
        检查集合是否存在
        
        Returns:
            集合是否存在
        """
        pass
    
    @abstractmethod
    def delete_collection(self) -> bool:
        """
        删除集合
        
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def delete_by_ids(self, ids: List[str]) -> bool:
        """
        根据 ID 删除向量
        
        Args:
            ids: ID 列表
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def get_vector_count(self) -> int:
        """
        获取向量数量
        
        Returns:
            向量数量
        """
        pass
    
    @abstractmethod
    def close(self):
        """关闭连接"""
        pass
    
    def get_store_info(self) -> Dict[str, Any]:
        """
        获取存储信息
        
        Returns:
            存储信息字典
        """
        return {
            "store_type": self.__class__.__name__,
            "collection_name": self.collection_name,
            "dimension": self.dimension,
            "vector_count": self.get_vector_count()
        }


if __name__ == "__main__":
    print("=" * 60)
    print("向量存储抽象层")
    print("=" * 60)
    print()
    print("✅ 抽象接口定义完成")
    print()
    print("📋 支持的操作:")
    print("  - create_collection(): 创建集合")
    print("  - collection_exists(): 检查集合")
    print("  - delete_collection(): 删除集合")
    print("  - insert_vectors(): 插入向量")
    print("  - search(): 搜索相似向量")
    print("  - delete_by_ids(): 删除向量")
    print("  - get_vector_count(): 获取向量数量")
    print("  - close(): 关闭连接")
    print()
    print("🔧 实现类:")
    print("  - FAISSStore: FAISS 本地存储")
    print("  - QdrantStore: Qdrant 向量数据库")

