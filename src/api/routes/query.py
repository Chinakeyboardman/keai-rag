#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询路由
"""

from fastapi import APIRouter, HTTPException, Depends
import asyncio

from src.api.schemas.query import QueryRequest, QueryResponse, SourceInfo
from src.api.dependencies import get_generation_service
from src.services.generation_service import GenerationService
from src.utils.logger import logger

router = APIRouter()


@router.post("/query", response_model=QueryResponse, tags=["查询"])
async def query(
    request: QueryRequest,
    generation_service: GenerationService = Depends(get_generation_service)
):
    """
    查询接口
    
    基于文档内容回答用户问题，并推荐相关问题
    """
    try:
        logger.info(f"🔍 收到查询请求: {request.question[:50]}...")
        
        # 使用 asyncio.wait_for 添加超时保护
        try:
            if request.include_suggestions:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        generation_service.generate_with_suggestions,
                        request.question,
                        request.top_k,
                        request.num_suggestions
                    ),
                    timeout=180.0  # 180秒超时
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        generation_service.generate_answer,
                        request.question,
                        request.top_k
                    ),
                    timeout=180.0  # 180秒超时
                )
                result["suggested_questions"] = None
        except asyncio.TimeoutError:
            logger.error(f"❌ 查询超时（超过180秒）")
            raise HTTPException(status_code=504, detail="查询超时，请稍后重试或简化问题")
        
        # 转换来源信息
        sources = [
            SourceInfo(**source)
            for source in result["sources"]
        ]
        
        logger.info(f"✅ 查询成功，找到 {len(sources)} 个来源")
        
        return QueryResponse(
            question=request.question,
            answer=result["answer"],
            sources=sources,
            has_sources=result["has_sources"],
            suggested_questions=result.get("suggested_questions"),
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

