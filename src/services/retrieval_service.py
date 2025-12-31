#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检索服务
负责文档检索和相关性计算
"""

from typing import List, Dict, Any, Optional
import numpy as np

from src.core.vector_store import BaseVectorStore, VectorSearchResult
from src.services.embedding_service import get_embedding_service
from config.settings import settings


class RetrievalService:
    """检索服务类"""
    
    def __init__(self, vector_store: BaseVectorStore):
        """
        初始化检索服务
        
        Args:
            vector_store: 向量存储实例
        """
        self.vector_store = vector_store
        self.embedding_service = get_embedding_service()
        self.top_k = settings.RETRIEVAL_TOP_K
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            检索结果列表
        """
        if not query or not query.strip():
            raise ValueError("查询文本不能为空")
        
        # 使用配置的默认值
        if top_k is None:
            top_k = self.top_k
        
        # 向量化查询
        query_vector = self.embedding_service.embed_text(query)
        
        # 搜索
        results = self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            filter_dict=filter_dict
        )
        
        return results
    
    def retrieve_with_scores(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        检索相关文档并返回详细信息
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            包含详细信息的结果列表
        """
        results = self.retrieve(query, top_k, filter_dict)
        
        return [
            {
                "id": result.id,
                "text": result.text,
                "score": result.score,
                "metadata": result.metadata
            }
            for result in results
        ]
    
    def get_context_text(
        self,
        query: str,
        top_k: Optional[int] = None,
        separator: str = "\n\n"
    ) -> str:
        """
        获取检索结果的上下文文本
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            separator: 文本分隔符
            
        Returns:
            合并的上下文文本
        """
        results = self.retrieve(query, top_k)
        
        if not results:
            return ""
        
        texts = [result.text for result in results]
        return separator.join(texts)


if __name__ == "__main__":
    """测试检索服务"""
    print("=" * 60)
    print("检索服务测试")
    print("=" * 60)
    print()
    print("ℹ️  检索服务需要配合向量存储使用")
    print("   请参考完整的集成测试")

