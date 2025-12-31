#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询相关数据模型
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """查询请求"""
    question: str = Field(..., description="用户问题", min_length=1)
    top_k: Optional[int] = Field(default=3, description="检索文档数量", ge=1, le=10)
    include_suggestions: bool = Field(default=True, description="是否包含问题推荐")
    num_suggestions: int = Field(default=3, description="推荐问题数量", ge=1, le=5)


class SourceInfo(BaseModel):
    """来源信息"""
    id: str = Field(..., description="文档块ID")
    text: str = Field(..., description="文本片段")
    score: float = Field(..., description="相关性分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class QueryResponse(BaseModel):
    """查询响应"""
    question: str = Field(..., description="用户问题")
    answer: str = Field(..., description="生成的答案")
    sources: List[SourceInfo] = Field(..., description="来源文档")
    has_sources: bool = Field(..., description="是否有来源")
    suggested_questions: Optional[List[str]] = Field(default=None, description="推荐问题")
    success: bool = Field(..., description="是否成功")

