#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
健康检查路由
"""

from fastapi import APIRouter, Depends

from src.api.schemas.health import HealthResponse
from config.settings import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    from src.services.embedding_service import get_embedding_service
    from src.services.llm_service import get_llm_service
    from src.api.dependencies import get_vector_store_manager
    
    # 获取服务实例
    embedding_service = get_embedding_service()
    llm_service = get_llm_service()
    vector_store_manager = get_vector_store_manager()
    
    return HealthResponse(
        status="healthy",
        version=settings.PROJECT_VERSION,
        vector_store=vector_store_manager.get_store_info(),
        embedding_model=embedding_service.get_model_info(),
        llm_model=llm_service.get_model_info()
    )

