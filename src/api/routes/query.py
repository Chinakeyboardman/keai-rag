#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询路由
"""

from fastapi import APIRouter, HTTPException, Depends

from src.api.schemas.query import QueryRequest, QueryResponse, SourceInfo
from src.api.dependencies import get_generation_service
from src.services.generation_service import GenerationService

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
        # 生成答案
        if request.include_suggestions:
            result = generation_service.generate_with_suggestions(
                question=request.question,
                top_k=request.top_k,
                num_suggestions=request.num_suggestions
            )
        else:
            result = generation_service.generate_answer(
                question=request.question,
                top_k=request.top_k
            )
            result["suggested_questions"] = None
        
        # 转换来源信息
        sources = [
            SourceInfo(**source)
            for source in result["sources"]
        ]
        
        return QueryResponse(
            question=request.question,
            answer=result["answer"],
            sources=sources,
            has_sources=result["has_sources"],
            suggested_questions=result.get("suggested_questions"),
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

