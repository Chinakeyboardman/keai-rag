#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FastAPI 应用入口
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
import traceback

from config.settings import settings
from src.api.routes import health, document, query
from src.utils.logger import logger
from src.utils.exceptions import handle_exception, RAGSystemException


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
    
    vector_store_manager = None
    
    try:
        # 初始化向量存储
        try:
            vector_store_manager = get_vector_store_manager()
            print(f"✅ 向量存储: {vector_store_manager.get_store_type()}")
            logger.info(f"向量存储初始化成功: {vector_store_manager.get_store_type()}")
        except Exception as e:
            logger.error(f"向量存储初始化失败: {e}", exc_info=True)
            print(f"⚠️  向量存储初始化失败: {e}")
            print(f"   系统将使用降级模式运行")
        
        # 初始化 Embedding 服务
        try:
            embedding_service = get_embedding_service()
            print(f"✅ Embedding 模型: {embedding_service.model_name}")
            logger.info(f"Embedding 模型初始化成功: {embedding_service.model_name}")
        except Exception as e:
            logger.error(f"Embedding 服务初始化失败: {e}", exc_info=True)
            print(f"❌ Embedding 服务初始化失败: {e}")
            print(f"   系统无法处理文档上传和查询功能")
            # 不 raise，让系统继续启动，但功能受限
        
        # 初始化 LLM 服务
        try:
            llm_service = get_llm_service()
            print(f"✅ LLM 模型: {llm_service.model_name}")
            logger.info(f"LLM 模型初始化成功: {llm_service.model_name}")
        except Exception as e:
            logger.error(f"LLM 服务初始化失败: {e}", exc_info=True)
            print(f"⚠️  LLM 服务初始化失败: {e}")
            print(f"   查询功能将不可用")
        
        # 初始化检索和生成服务
        try:
            retrieval_service = get_retrieval_service()
            generation_service = get_generation_service()
            print(f"✅ 检索和生成服务已就绪")
            logger.info("检索和生成服务初始化成功")
        except Exception as e:
            logger.error(f"检索和生成服务初始化失败: {e}", exc_info=True)
            print(f"⚠️  检索和生成服务初始化失败: {e}")
        
        print()
        print(f"🌐 API 服务启动:")
        print(f"   地址: http://{settings.API_HOST}:{settings.API_PORT}")
        print(f"   文档: http://{settings.API_HOST}:{settings.API_PORT}/docs")
        print()
        logger.info(f"API 服务启动成功: http://{settings.API_HOST}:{settings.API_PORT}")
        
    except Exception as e:
        logger.critical(f"服务初始化严重失败: {e}", exc_info=True)
        print(f"❌ 服务初始化严重失败: {e}")
        # 不 raise，让系统至少能启动，即使功能受限
        print(f"⚠️  系统将以降级模式启动")
    
    yield
    
    # 关闭时清理
    print()
    print("👋 服务关闭中...")
    try:
        if vector_store_manager:
            vector_store_manager.close()
        print("✅ 清理完成")
        logger.info("服务关闭完成")
    except Exception as e:
        logger.error(f"服务关闭时出错: {e}", exc_info=True)
        print(f"⚠️  清理时出错: {e}")


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

# 挂载静态文件
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 注册路由
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(document.router, prefix=settings.API_PREFIX)
app.include_router(query.router, prefix=settings.API_PREFIX)


# ==================== 全局异常处理器 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    捕获所有未处理的异常，防止应用崩溃
    """
    # 记录异常详情
    error_traceback = traceback.format_exc()
    logger.error(
        f"未处理的异常: {type(exc).__name__}: {str(exc)}\n"
        f"请求路径: {request.url.path}\n"
        f"请求方法: {request.method}\n"
        f"异常堆栈:\n{error_traceback}",
        exc_info=True
    )
    
    # 使用统一的异常处理函数
    message, status_code = handle_exception(exc)
    
    # 返回错误响应
    return JSONResponse(
        status_code=status_code,
        content={
            "error": message,
            "error_type": type(exc).__name__,
            "path": str(request.url.path),
            "method": request.method
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP 异常处理器
    处理 FastAPI 的 HTTPException
    """
    logger.warning(
        f"HTTP 异常: {exc.status_code} - {exc.detail}\n"
        f"请求路径: {request.url.path}\n"
        f"请求方法: {request.method}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_type": "HTTPException",
            "path": str(request.url.path),
            "method": request.method
        }
    )


@app.get("/", tags=["根路径"])
async def root():
    """根路径 - 返回 Web UI"""
    static_file = Path(__file__).parent / "static" / "index.html"
    if static_file.exists():
        return FileResponse(static_file)
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "docs": "/docs",
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

