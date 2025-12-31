#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FastAPI 应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config.settings import settings
from src.api.routes import health, document, query


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("=" * 60)
    print(f"🚀 {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    print("=" * 60)
    print()
    
    # 初始化服务
    print("📦 初始化服务...")
    from src.api.dependencies import (
        get_vector_store_manager,
        get_retrieval_service,
        get_generation_service
    )
    from src.services.embedding_service import get_embedding_service
    from src.services.llm_service import get_llm_service
    
    try:
        # 初始化向量存储
        vector_store_manager = get_vector_store_manager()
        print(f"✅ 向量存储: {vector_store_manager.get_store_type()}")
        
        # 初始化 Embedding 服务
        embedding_service = get_embedding_service()
        print(f"✅ Embedding 模型: {embedding_service.model_name}")
        
        # 初始化 LLM 服务
        llm_service = get_llm_service()
        print(f"✅ LLM 模型: {llm_service.model_name}")
        
        # 初始化检索和生成服务
        retrieval_service = get_retrieval_service()
        generation_service = get_generation_service()
        print(f"✅ 检索和生成服务已就绪")
        
        print()
        print(f"🌐 API 服务启动:")
        print(f"   地址: http://{settings.API_HOST}:{settings.API_PORT}")
        print(f"   文档: http://{settings.API_HOST}:{settings.API_PORT}/docs")
        print()
        
    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        raise
    
    yield
    
    # 关闭时清理
    print()
    print("👋 服务关闭中...")
    vector_store_manager.close()
    print("✅ 清理完成")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="企业级 RAG 系统 - 支持 PDF 文档导入、向量检索和智能问答",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(document.router, prefix=settings.API_PREFIX)
app.include_router(query.router, prefix=settings.API_PREFIX)


@app.get("/", tags=["根路径"])
async def root():
    """根路径"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "docs": f"{settings.API_PREFIX}/docs",
        "health": f"{settings.API_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

