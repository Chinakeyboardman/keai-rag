#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档相关数据模型
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    document_id: str = Field(..., description="文档ID")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    chunks_count: int = Field(..., description="分块数量")
    message: str = Field(..., description="处理消息")
    success: bool = Field(..., description="是否成功")


class DocumentInfo(BaseModel):
    """文档信息"""
    document_id: str = Field(..., description="文档ID")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    file_type: str = Field(..., description="文件类型")
    chunks_count: int = Field(..., description="分块数量")
    upload_time: datetime = Field(..., description="上传时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[DocumentInfo] = Field(..., description="文档列表")
    total: int = Field(..., description="文档总数")


class DocumentDeleteResponse(BaseModel):
    """文档删除响应"""
    document_id: str = Field(..., description="文档ID")
    message: str = Field(..., description="删除消息")
    success: bool = Field(..., description="是否成功")

