#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
健康检查路由
"""

from fastapi import APIRouter, Depends, HTTPException

from src.api.schemas.health import HealthResponse
from config.settings import settings
from src.utils.logger import logger

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    try:
        from src.services.embedding_service import get_embedding_service
        from src.services.llm_service import get_llm_service
        from src.api.dependencies import get_vector_store_manager
        
        # 获取服务实例（可能失败，需要捕获）
        try:
            embedding_service = get_embedding_service()
            embedding_info = embedding_service.get_model_info()
        except Exception as e:
            logger.warning(f"Embedding 服务不可用: {e}")
            embedding_info = {"model_type": "unavailable", "model_name": "N/A"}
        
        try:
            llm_service = get_llm_service()
            llm_info = llm_service.get_model_info()
        except Exception as e:
            logger.warning(f"LLM 服务不可用: {e}")
            llm_info = {"model_type": "unavailable", "model_name": "N/A"}
        
        try:
            vector_store_manager = get_vector_store_manager()
            vector_store_info = vector_store_manager.get_store_info()
        except Exception as e:
            logger.warning(f"向量存储不可用: {e}")
            vector_store_info = {"store_type": "unavailable", "vector_count": 0}
        
        return HealthResponse(
            status="healthy",
            version=settings.PROJECT_VERSION,
            vector_store=vector_store_info,
            embedding_model=embedding_info,
            llm_model=llm_info
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"健康检查失败: {str(e)}")

