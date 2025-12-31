#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
健康检查相关数据模型
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    vector_store: Dict[str, Any] = Field(..., description="向量存储信息")
    embedding_model: Dict[str, Any] = Field(..., description="Embedding模型信息")
    llm_model: Dict[str, Any] = Field(..., description="LLM模型信息")

