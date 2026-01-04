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
from src.utils.logger import logger
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
        logger.info(f"📤 开始上传文档: {file.filename}")
        
        # 验证文件类型
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持 PDF 文件")
        
        # 生成文档 ID
        document_id = str(uuid.uuid4())
        logger.info(f"📝 文档 ID: {document_id}")
        
        # 保存文件
        documents_dir = settings.get_documents_dir()
        file_path = documents_dir / f"{document_id}_{file.filename}"
        
        logger.info(f"💾 保存文件到: {file_path}")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"✅ 文件保存成功")
        
        # 处理文档
        logger.info(f"📄 开始处理 PDF 文档...")
        try:
            processor = PDFProcessor(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            logger.info(f"📄 PDF 处理器已创建，开始处理...")
            document = processor.process(file_path, document_id)
            logger.info(f"✅ PDF 处理完成，共 {document.get_total_chunks()} 个文本块")
        except Exception as e:
            logger.error(f"❌ PDF 处理失败: {e}", exc_info=True)
            # 删除已保存的文件
            if file_path.exists():
                file_path.unlink()
                logger.info(f"🗑️  已删除失败的文件: {file_path}")
            raise HTTPException(status_code=500, detail=f"PDF 处理失败: {str(e)}")
        
        # 向量化并存储
        logger.info(f"🔢 开始向量化文本...")
        try:
            logger.info(f"📞 正在获取 Embedding 服务...")
            embedding_service = get_embedding_service()
            if embedding_service.model is None:
                raise RuntimeError("Embedding 模型未初始化")
            logger.info(f"✅ Embedding 服务已获取，模型: {embedding_service.model_name}")
        except Exception as e:
            logger.error(f"❌ 获取 Embedding 服务失败: {e}", exc_info=True)
            # 删除已保存的文件
            if file_path.exists():
                file_path.unlink()
                logger.info(f"🗑️  已删除失败的文件: {file_path}")
            raise HTTPException(status_code=500, detail=f"Embedding 服务不可用: {str(e)}")
        
        try:
            vector_store_manager = get_vector_store_manager()
            store = vector_store_manager.get_store()
            logger.info(f"✅ 向量存储已获取")
        except Exception as e:
            logger.error(f"❌ 获取向量存储失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"向量存储不可用: {str(e)}")
        
        # 提取文本和元数据
        logger.info(f"📋 提取文本和元数据...")
        texts = [chunk.text for chunk in document.chunks]
        # 确保 document_id 在 metadata 中
        metadatas = [
            {**chunk.metadata, "document_id": chunk.document_id}
            for chunk in document.chunks
        ]
        ids = [chunk.chunk_id for chunk in document.chunks]
        logger.info(f"✅ 已提取 {len(texts)} 个文本块")
        
        # 记录每个块的信息用于验证
        logger.info(f"📋 块信息预览（前3个和后3个）:")
        for i, chunk in enumerate(document.chunks[:3]):
            logger.info(f"   块{i}: chunk_index={chunk.chunk_index}, chunk_id={chunk.chunk_id[:30]}..., "
                      f"text_length={len(chunk.text)}, text_preview={chunk.text[:50]}...")
        if len(document.chunks) > 3:
            for i, chunk in enumerate(document.chunks[-3:], len(document.chunks)-3):
                logger.info(f"   块{i}: chunk_index={chunk.chunk_index}, chunk_id={chunk.chunk_id[:30]}..., "
                          f"text_length={len(chunk.text)}, text_preview={chunk.text[:50]}...")
        
        # 检查是否有包含目标文本的块
        target_keywords = ["每年一月份", "申报时间", "第十一条"]
        for i, chunk in enumerate(document.chunks):
            if any(keyword in chunk.text for keyword in target_keywords):
                logger.info(f"✅ 找到包含目标关键词的块: chunk_index={chunk.chunk_index}, "
                          f"text_preview={chunk.text[:100]}...")
        
        # 批量向量化
        logger.info(f"⏳ 正在向量化 {len(texts)} 个文本块...")
        try:
            import time
            start_time = time.time()
            vectors = embedding_service.embed_texts(texts)
            elapsed_time = time.time() - start_time
            logger.info(f"✅ 向量化完成，耗时 {elapsed_time:.2f} 秒")
        except Exception as e:
            logger.error(f"❌ 向量化失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"向量化失败: {str(e)}")
        
        # 插入向量存储
        logger.info(f"💾 插入向量存储...")
        logger.info(f"   准备插入 {len(vectors)} 个向量")
        logger.info(f"   向量维度: {len(vectors[0]) if vectors else 0}")
        logger.info(f"   文本数量: {len(texts)}")
        logger.info(f"   元数据数量: {len(metadatas)}")
        logger.info(f"   ID数量: {len(ids)}")
        
        # 验证数据一致性
        if not (len(vectors) == len(texts) == len(metadatas) == len(ids)):
            error_msg = f"数据不一致: 向量({len(vectors)})、文本({len(texts)})、元数据({len(metadatas)})、ID({len(ids)})"
            logger.error(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        try:
            start_time = time.time()
            success = store.insert_vectors(vectors, texts, metadatas, ids)
            elapsed_time = time.time() - start_time
            
            if success:
                logger.info(f"✅ 向量存储完成，耗时 {elapsed_time:.2f} 秒")
                
                # 验证存储结果
                try:
                    stored_count = store.get_vector_count()
                    logger.info(f"📊 向量存储验证: 集合中现有 {stored_count} 个向量")
                    if stored_count < len(vectors):
                        logger.warning(f"⚠️  存储的向量数量({stored_count})少于预期({len(vectors)})")
                except Exception as verify_error:
                    logger.warning(f"⚠️  无法验证存储结果: {verify_error}")
            else:
                logger.error(f"❌ 向量存储失败（返回False）")
                raise HTTPException(status_code=500, detail="向量存储失败")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ 向量存储异常: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"向量存储失败: {str(e)}")
        
        logger.info(f"✅ 文档上传完成: {file.filename}")
        
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
        
        # 获取向量存储，用于查询块数量
        try:
            vector_store_manager = get_vector_store_manager()
            store = vector_store_manager.get_store()
        except Exception as e:
            logger.warning(f"⚠️  无法获取向量存储，块数量将显示为0: {e}")
            store = None
        
        for file_path in documents_dir.glob("*.pdf"):
            # 解析文件名获取文档 ID
            parts = file_path.stem.split("_", 1)
            if len(parts) == 2:
                document_id, original_name = parts
                
                # 从向量存储查询该文档的块数量
                chunks_count = 0
                if store:
                    try:
                        chunk_ids = store.get_chunk_ids_by_document_id(document_id)
                        chunks_count = len(chunk_ids)
                    except Exception as e:
                        logger.warning(f"⚠️  查询文档 {document_id} 的块数量失败: {e}")
                
                documents.append(
                    DocumentInfo(
                        document_id=document_id,
                        file_name=original_name + ".pdf",
                        file_size=file_path.stat().st_size,
                        file_type=".pdf",
                        chunks_count=chunks_count,
                        upload_time=file_path.stat().st_mtime,
                        metadata={}
                    )
                )
        
        return DocumentListResponse(
            documents=documents,
            total=len(documents)
        )
        
    except Exception as e:
        logger.error(f"❌ 获取文档列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文档列表失败: {str(e)}")


@router.delete("/documents/{document_id}", response_model=DocumentDeleteResponse, tags=["文档管理"])
async def delete_document(document_id: str):
    """
    删除文档接口
    
    删除指定文档及其向量数据
    """
    try:
        logger.info(f"🗑️  开始删除文档: {document_id}")
        
        # 删除向量数据（先删除向量，再删除文件）
        vector_store_manager = get_vector_store_manager()
        store = vector_store_manager.get_store()
        
        # 查找所有相关的块 ID
        chunk_ids = store.get_chunk_ids_by_document_id(document_id)
        logger.info(f"📋 找到 {len(chunk_ids)} 个相关向量块")
        
        if chunk_ids:
            # 删除向量数据
            success = store.delete_by_ids(chunk_ids)
            if success:
                logger.info(f"✅ 已删除 {len(chunk_ids)} 个向量块")
            else:
                logger.warning(f"⚠️  删除向量块失败，但继续删除文件")
        else:
            logger.info(f"ℹ️  未找到相关向量数据（可能是上传失败的文档）")
        
        # 删除文件
        documents_dir = settings.get_documents_dir()
        deleted = False
        
        for file_path in documents_dir.glob(f"{document_id}_*.pdf"):
            logger.info(f"🗑️  删除文件: {file_path}")
            file_path.unlink()
            deleted = True
        
        if not deleted:
            # 如果没有找到文件，但找到了向量数据，说明向量数据已删除
            if chunk_ids:
                logger.info(f"✅ 文档文件不存在，但已删除向量数据")
                return DocumentDeleteResponse(
                    document_id=document_id,
                    message="向量数据已删除（文件不存在）",
                    success=True
                )
            raise HTTPException(status_code=404, detail="文档不存在")
        
        logger.info(f"✅ 文档删除成功: {document_id}")
        
        return DocumentDeleteResponse(
            document_id=document_id,
            message=f"文档删除成功（已删除 {len(chunk_ids)} 个向量块）",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 文档删除失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文档删除失败: {str(e)}")


@router.delete("/documents", response_model=DocumentDeleteResponse, tags=["文档管理"])
async def delete_failed_documents():
    """
    删除失败的文档接口
    
    删除所有只有文件但没有向量数据的文档（上传失败的文档）
    """
    try:
        logger.info(f"🗑️  开始清理失败的文档...")
        
        documents_dir = settings.get_documents_dir()
        vector_store_manager = get_vector_store_manager()
        store = vector_store_manager.get_store()
        
        deleted_count = 0
        deleted_files = []
        
        # 遍历所有 PDF 文件
        for file_path in documents_dir.glob("*.pdf"):
            # 解析文档 ID
            parts = file_path.stem.split("_", 1)
            if len(parts) != 2:
                continue
            
            document_id = parts[0]
            
            # 检查是否有对应的向量数据
            chunk_ids = store.get_chunk_ids_by_document_id(document_id)
            
            # 如果没有向量数据，说明上传失败，删除文件
            if not chunk_ids:
                logger.info(f"🗑️  删除失败文档: {file_path.name}")
                file_path.unlink()
                deleted_count += 1
                deleted_files.append(file_path.name)
        
        logger.info(f"✅ 清理完成，删除了 {deleted_count} 个失败文档")
        
        return DocumentDeleteResponse(
            document_id="batch",
            message=f"已删除 {deleted_count} 个失败文档",
            success=True
        )
        
    except Exception as e:
        logger.error(f"❌ 清理失败文档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清理失败文档失败: {str(e)}")

