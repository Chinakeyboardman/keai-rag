#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF 文档处理器
支持 PDF 文件的文本提取和处理
"""

from pathlib import Path
from typing import Dict, Any, List
from PyPDF2 import PdfReader
from .base import BaseDocumentProcessor
from src.utils.logger import logger


class PDFProcessor(BaseDocumentProcessor):
    """PDF 文档处理器"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化 PDF 处理器
        
        Args:
            chunk_size: 文本分块大小
            chunk_overlap: 文本分块重叠大小
        """
        super().__init__(chunk_size, chunk_overlap)
    
    def extract_text(self, file_path: Path) -> str:
        """
        从 PDF 文件提取文本
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            提取的文本内容
        """
        try:
            logger.info(f"📄 打开 PDF 文件: {file_path}")
            reader = PdfReader(str(file_path))
            total_pages = len(reader.pages)
            logger.info(f"📄 PDF 总页数: {total_pages}")
            
            text_parts = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                if page_num % 10 == 0 or page_num == 1:
                    logger.info(f"📄 处理第 {page_num}/{total_pages} 页...")
                
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"⚠️  第 {page_num} 页提取失败: {e}")
                    continue
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"✅ PDF 文本提取完成，共 {len(text_parts)} 页有内容，总字符数: {len(full_text)}")
            return full_text
            
        except Exception as e:
            logger.error(f"❌ 提取 PDF 文本失败: {e}", exc_info=True)
            raise RuntimeError(f"提取 PDF 文本失败: {e}")
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        提取 PDF 元数据
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            PDF 元数据字典
        """
        try:
            reader = PdfReader(str(file_path))
            metadata = {
                "total_pages": len(reader.pages),
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
            }
            
            # 提取 PDF 文档信息
            if reader.metadata:
                pdf_meta = reader.metadata
                if pdf_meta.get("/Title"):
                    metadata["title"] = pdf_meta.get("/Title")
                if pdf_meta.get("/Author"):
                    metadata["author"] = pdf_meta.get("/Author")
                if pdf_meta.get("/Subject"):
                    metadata["subject"] = pdf_meta.get("/Subject")
                if pdf_meta.get("/Creator"):
                    metadata["creator"] = pdf_meta.get("/Creator")
                if pdf_meta.get("/Producer"):
                    metadata["producer"] = pdf_meta.get("/Producer")
                if pdf_meta.get("/CreationDate"):
                    metadata["creation_date"] = str(pdf_meta.get("/CreationDate"))
                if pdf_meta.get("/ModDate"):
                    metadata["modification_date"] = str(pdf_meta.get("/ModDate"))
            
            return metadata
            
        except Exception as e:
            # 如果提取元数据失败，返回基本信息
            return {
                "total_pages": 0,
                "file_name": file_path.name,
                "file_size": file_path.stat().st_size,
                "extraction_error": str(e)
            }
    
    def supported_extensions(self) -> List[str]:
        """
        获取支持的文件扩展名
        
        Returns:
            支持的扩展名列表
        """
        return ['.pdf']
    
    def extract_text_with_page_info(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        提取文本并保留页码信息
        
        Args:
            file_path: PDF 文件路径
            
        Returns:
            包含页码信息的文本列表
        """
        try:
            reader = PdfReader(str(file_path))
            pages_text = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    pages_text.append({
                        "page_number": page_num,
                        "text": page_text,
                        "char_count": len(page_text)
                    })
            
            return pages_text
            
        except Exception as e:
            raise RuntimeError(f"提取 PDF 页面文本失败: {e}")


if __name__ == "__main__":
    """测试 PDF 处理器"""
    import sys
    
    print("=" * 60)
    print("PDF 处理器测试")
    print("=" * 60)
    print()
    
    # 创建处理器
    processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
    print("✅ PDF 处理器创建成功")
    print(f"   {processor.get_processor_info()}")
    print()
    
    # 如果提供了 PDF 文件路径，进行测试
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        
        if not pdf_path.exists():
            print(f"❌ 文件不存在: {pdf_path}")
            sys.exit(1)
        
        if not processor.is_supported(pdf_path):
            print(f"❌ 不支持的文件类型: {pdf_path.suffix}")
            sys.exit(1)
        
        print(f"📄 测试文件: {pdf_path.name}")
        print()
        
        # 提取元数据
        print("📋 提取元数据...")
        metadata = processor.extract_metadata(pdf_path)
        for key, value in metadata.items():
            print(f"   {key}: {value}")
        print()
        
        # 提取文本
        print("📝 提取文本...")
        text = processor.extract_text(pdf_path)
        print(f"   文本长度: {len(text)} 字符")
        print(f"   前 200 字符: {text[:200]}...")
        print()
        
        # 分割文本
        print("✂️  分割文本...")
        chunks = processor.split_text(text)
        print(f"   分割块数: {len(chunks)}")
        if chunks:
            print(f"   第一块长度: {len(chunks[0])} 字符")
            print(f"   第一块内容: {chunks[0][:100]}...")
        print()
        
        # 处理完整文档
        print("🔄 处理完整文档...")
        document = processor.process(pdf_path, "test_doc_001")
        print(f"   文档 ID: {document.document_id}")
        print(f"   文件名: {document.file_name}")
        print(f"   文件大小: {document.file_size} 字节")
        print(f"   总块数: {document.get_total_chunks()}")
        print(f"   总文本长度: {document.get_total_text_length()} 字符")
        print()
        
        print("✅ PDF 处理器测试完成！")
    else:
        print("💡 提示: 提供 PDF 文件路径进行完整测试")
        print("   python pdf_processor.py <pdf_file_path>")
        print()
        print("✅ 基本功能测试完成！")

