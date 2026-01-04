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
        检索相关文档（混合检索：向量检索 + 关键词检索）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            检索结果列表
        """
        if not query or not query.strip():
            raise ValueError("查询文本不能为空")
        
        # 使用配置的默认值，但增加检索数量以提高召回率
        if top_k is None:
            top_k = max(self.top_k, 15)  # 至少检索15个结果以提高召回率
        else:
            top_k = max(top_k, 15)  # 确保至少检索15个结果
        
        # 向量化查询
        query_vector = self.embedding_service.embed_text(query)
        
        # 向量搜索（大幅增加检索数量以确保不遗漏）
        # 检索所有可能的文档块（如果总数不多的话）
        vector_results = self.vector_store.search(
            query_vector=query_vector,
            top_k=min(top_k * 3, 50),  # 检索更多结果，最多50个
            filter_dict=filter_dict
        )
        
        # 关键词增强：如果向量检索结果较少，尝试关键词匹配
        if len(vector_results) < top_k:
            # 提取查询关键词
            keywords = self._extract_keywords(query)
            if keywords:
                # 尝试使用关键词进行二次检索
                keyword_results = self._keyword_search(keywords, top_k)
                # 合并结果，去重
                vector_results = self._merge_results(vector_results, keyword_results, top_k)
        
        # 返回top_k个结果
        return vector_results[:top_k]
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取查询关键词"""
        # 简单的关键词提取：去除停用词，保留重要词汇
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        words = query.split()
        keywords = [w for w in words if w not in stop_words and len(w) > 1]
        return keywords
    
    def _keyword_search(self, keywords: List[str], top_k: int) -> List[VectorSearchResult]:
        """基于关键词的搜索（简单实现：通过向量搜索关键词）"""
        results = []
        for keyword in keywords[:3]:  # 只使用前3个关键词
            try:
                keyword_vector = self.embedding_service.embed_text(keyword)
                keyword_results = self.vector_store.search(
                    query_vector=keyword_vector,
                    top_k=top_k,
                    filter_dict=None
                )
                results.extend(keyword_results)
            except Exception:
                continue
        return results
    
    def _merge_results(self, results1: List[VectorSearchResult], results2: List[VectorSearchResult], top_k: int) -> List[VectorSearchResult]:
        """合并检索结果，去重并按分数排序"""
        from src.utils.logger import logger
        
        # 使用字典去重（基于ID），同时记录最高分数
        seen_results = {}  # {id: result}
        
        # 先添加results1（向量检索结果，优先级更高）
        for result in results1:
            if result.id not in seen_results:
                seen_results[result.id] = result
            else:
                # 如果已存在，保留分数更高的（假设都是相似度分数，越大越好）
                if result.score > seen_results[result.id].score:
                    seen_results[result.id] = result
        
        # 再添加results2（关键词检索结果）
        for result in results2:
            if result.id not in seen_results:
                seen_results[result.id] = result
            else:
                # 如果已存在，保留分数更高的
                if result.score > seen_results[result.id].score:
                    seen_results[result.id] = result
        
        # 转换为列表并按分数排序
        # 注意：FAISS返回的是距离（越小越好），Qdrant返回的是相似度（越大越好）
        # 这里假设已经统一为相似度分数（越大越好）
        merged = list(seen_results.values())
        merged.sort(key=lambda x: x.score, reverse=True)
        
        logger.debug(f"合并检索结果: {len(results1)} + {len(results2)} -> {len(merged)} (去重后)")
        
        return merged[:top_k]
    
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

