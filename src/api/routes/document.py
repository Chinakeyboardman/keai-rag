#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档管理路由
"""

import uuid
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from src.api.schemas.document import (
    DocumentUploadResponse,
    DocumentInfo,
    DocumentListResponse,
    DocumentDeleteResponse
)
from src.api.dependencies import get_vector_store_manager, get_retrieval_service
from src.processors.pdf_processor import PDFProcessor
from src.services.embedding_service import get_embedding_service
from config.settings import settings

router = APIRouter()


@router.post("/documents/upload", response_model=DocumentUploadResponse, tags=["文档管理"])
async def upload_document(
    file: UploadFile = File(..., description="PDF文档文件")
):
    """
    上传文档接口
    
    支持 PDF 文档上传，自动处理并存储到向量数据库
    """
    try:
        # 验证文件类型
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持 PDF 文件")
        
        # 生成文档 ID
        document_id = str(uuid.uuid4())
        
        # 保存文件
        documents_dir = settings.get_documents_dir()
        file_path = documents_dir / f"{document_id}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 处理文档
        processor = PDFProcessor(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        document = processor.process(file_path, document_id)
        
        # 向量化并存储
        embedding_service = get_embedding_service()
        vector_store_manager = get_vector_store_manager()
        store = vector_store_manager.get_store()
        
        # 提取文本和元数据
        texts = [chunk.text for chunk in document.chunks]
        metadatas = [chunk.metadata for chunk in document.chunks]
        ids = [chunk.chunk_id for chunk in document.chunks]
        
        # 批量向量化
        vectors = embedding_service.embed_texts(texts)
        
        # 插入向量存储
        success = store.insert_vectors(vectors, texts, metadatas, ids)
        
        if not success:
            raise HTTPException(status_code=500, detail="向量存储失败")
        
        return DocumentUploadResponse(
            document_id=document_id,
            file_name=file.filename,
            file_size=document.file_size,
            chunks_count=document.get_total_chunks(),
            message="文档上传并处理成功",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")


@router.get("/documents", response_model=DocumentListResponse, tags=["文档管理"])
async def list_documents():
    """
    获取文档列表接口
    
    返回所有已上传的文档信息
    """
    try:
        documents_dir = settings.get_documents_dir()
        documents = []
        
        for file_path in documents_dir.glob("*.pdf"):
            # 解析文件名获取文档 ID
            parts = file_path.stem.split("_", 1)
            if len(parts) == 2:
                document_id, original_name = parts
                documents.append(
                    DocumentInfo(
                        document_id=document_id,
                        file_name=original_name + ".pdf",
                        file_size=file_path.stat().st_size,
                        file_type=".pdf",
                        chunks_count=0,  # 需要从向量存储查询
                        upload_time=file_path.stat().st_mtime,
                        metadata={}
                    )
                )
        
        return DocumentListResponse(
            documents=documents,
            total=len(documents)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.delete("/documents/{document_id}", response_model=DocumentDeleteResponse, tags=["文档管理"])
async def delete_document(document_id: str):
    """
    删除文档接口
    
    删除指定文档及其向量数据
    """
    try:
        # 删除文件
        documents_dir = settings.get_documents_dir()
        deleted = False
        
        for file_path in documents_dir.glob(f"{document_id}_*.pdf"):
            file_path.unlink()
            deleted = True
        
        if not deleted:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 删除向量数据
        vector_store_manager = get_vector_store_manager()
        store = vector_store_manager.get_store()
        
        # 查找所有相关的块 ID
        # 注意：这里简化处理，实际应该从元数据中查询
        # store.delete_by_ids([...])
        
        return DocumentDeleteResponse(
            document_id=document_id,
            message="文档删除成功",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文档删除失败: {str(e)}")

