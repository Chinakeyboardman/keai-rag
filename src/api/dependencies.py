#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API 依赖项
"""

from typing import Optional
from functools import lru_cache

from src.core.vector_store_manager import VectorStoreManager
from src.services.retrieval_service import RetrievalService
from src.services.generation_service import GenerationService
from config.settings import settings


# 全局实例
_vector_store_manager: Optional[VectorStoreManager] = None
_retrieval_service: Optional[RetrievalService] = None
_generation_service: Optional[GenerationService] = None


def get_vector_store_manager() -> VectorStoreManager:
    """获取向量存储管理器"""
    global _vector_store_manager
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            dimension=settings.VECTOR_DIMENSION,
            use_qdrant=settings.USE_QDRANT,
            qdrant_url=settings.QDRANT_URL,
            qdrant_api_key=settings.QDRANT_API_KEY,
            faiss_storage_dir=settings.VECTOR_STORE_DIR
        )
    return _vector_store_manager


def get_retrieval_service() -> RetrievalService:
    """获取检索服务"""
    global _retrieval_service
    if _retrieval_service is None:
        manager = get_vector_store_manager()
        _retrieval_service = RetrievalService(manager.get_store())
    return _retrieval_service


def get_generation_service() -> GenerationService:
    """获取生成服务"""
    global _generation_service
    if _generation_service is None:
        retrieval_service = get_retrieval_service()
        _generation_service = GenerationService(retrieval_service)
    return _generation_service

