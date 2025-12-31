#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档处理器基类
使用策略模式，便于扩展不同格式的文档处理器
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DocumentChunk:
    """文档块数据类"""
    text: str
    metadata: Dict[str, Any]
    chunk_id: str
    document_id: str
    chunk_index: int
    
    def __post_init__(self):
        """验证数据"""
        if not self.text or not self.text.strip():
            raise ValueError("文本内容不能为空")
        if self.chunk_index < 0:
            raise ValueError("块索引必须大于等于 0")


@dataclass
class Document:
    """文档数据类"""
    document_id: str
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    upload_time: datetime
    chunks: List[DocumentChunk]
    metadata: Dict[str, Any]
    
    def get_total_chunks(self) -> int:
        """获取文档块总数"""
        return len(self.chunks)
    
    def get_total_text_length(self) -> int:
        """获取文档总文本长度"""
        return sum(len(chunk.text) for chunk in self.chunks)


class BaseDocumentProcessor(ABC):
    """
    文档处理器基类
    
    所有文档处理器都应继承此类并实现抽象方法
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化文档处理器
        
        Args:
            chunk_size: 文本分块大小
            chunk_overlap: 文本分块重叠大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._validate_params()
    
    def _validate_params(self):
        """验证参数"""
        if self.chunk_size <= 0:
            raise ValueError("chunk_size 必须大于 0")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap 必须大于等于 0")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size")
    
    @abstractmethod
    def extract_text(self, file_path: Path) -> str:
        """
        提取文档文本
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取的文本内容
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        提取文档元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档元数据字典
        """
        pass
    
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """
        获取支持的文件扩展名
        
        Returns:
            支持的扩展名列表，如 ['.pdf', '.txt']
        """
        pass
    
    def split_text(self, text: str) -> List[str]:
        """
        分割文本为块
        
        Args:
            text: 要分割的文本
            
        Returns:
            文本块列表
        """
        from src.utils.logger import logger
        
        if not text or not text.strip():
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        max_iterations = text_length // max(1, self.chunk_size - self.chunk_overlap) + 10  # 防止死循环
        iteration = 0
        
        logger.info(f"✂️  文本分割参数: chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}, text_length={text_length}")
        
        while start < text_length:
            iteration += 1
            if iteration > max_iterations:
                logger.error(f"❌ 文本分割可能陷入死循环，已处理 {len(chunks)} 个块，当前位置: {start}/{text_length}")
                break
            
            # 计算结束位置
            end = min(start + self.chunk_size, text_length)
            
            # 如果不是最后一块，尝试在合适的位置分割
            if end < text_length:
                # 寻找最近的句号、问号、感叹号或换行符
                split_chars = ['\n\n', '\n', '。', '！', '？', '.', '!', '?']
                best_split = end
                
                for char in split_chars:
                    pos = text.rfind(char, start, end)
                    if pos != -1:
                        best_split = pos + len(char)
                        break
                
                end = best_split
            
            # 确保 end > start，防止空块
            if end <= start:
                logger.warning(f"⚠️  检测到 end <= start ({end} <= {start})，强制推进")
                end = start + 1
            
            # 提取块
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # 更新起始位置（考虑重叠）
            # 确保 start 总是增加的，防止死循环
            new_start = end - self.chunk_overlap if end < text_length else text_length
            if new_start <= start:
                # 如果新位置没有推进，至少推进1个字符
                new_start = start + 1
                logger.warning(f"⚠️  检测到位置未推进，强制推进到 {new_start}")
            
            start = new_start
        
        logger.info(f"✅ 文本分割完成，共 {len(chunks)} 个块，迭代次数: {iteration}")
        return chunks
    
    def process(self, file_path: Path, document_id: str) -> Document:
        """
        处理文档
        
        Args:
            file_path: 文件路径
            document_id: 文档 ID
            
        Returns:
            处理后的文档对象
        """
        # 验证文件
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not self.is_supported(file_path):
            raise ValueError(f"不支持的文件类型: {file_path.suffix}")
        
        # 提取文本和元数据
        from src.utils.logger import logger
        logger.info(f"📝 开始提取文本...")
        text = self.extract_text(file_path)
        logger.info(f"✅ 文本提取完成，长度: {len(text)} 字符")
        
        logger.info(f"📋 开始提取元数据...")
        metadata = self.extract_metadata(file_path)
        logger.info(f"✅ 元数据提取完成")
        
        # 分割文本
        logger.info(f"✂️  开始分割文本，文本长度: {len(text)} 字符")
        text_chunks = self.split_text(text)
        logger.info(f"✅ 文本分割完成，共 {len(text_chunks)} 个文本块")
        
        # 创建文档块
        logger.info(f"📦 开始创建文档块...")
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk = DocumentChunk(
                text=chunk_text,
                metadata={
                    "chunk_index": i,
                    "chunk_size": len(chunk_text),
                    "source_file": str(file_path),
                    **metadata
                },
                chunk_id=f"{document_id}_chunk_{i}",
                document_id=document_id,
                chunk_index=i
            )
            chunks.append(chunk)
        logger.info(f"✅ 文档块创建完成，共 {len(chunks)} 个块")
        
        # 创建文档对象
        logger.info(f"📄 创建文档对象...")
        document = Document(
            document_id=document_id,
            file_name=file_path.name,
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            file_type=file_path.suffix,
            upload_time=datetime.now(),
            chunks=chunks,
            metadata=metadata
        )
        
        return document
    
    def is_supported(self, file_path: Path) -> bool:
        """
        检查文件是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持该文件
        """
        return file_path.suffix.lower() in self.supported_extensions()
    
    def get_processor_info(self) -> Dict[str, Any]:
        """
        获取处理器信息
        
        Returns:
            处理器信息字典
        """
        return {
            "processor_name": self.__class__.__name__,
            "supported_extensions": self.supported_extensions(),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }


class DocumentProcessorFactory:
    """文档处理器工厂类"""
    
    _processors: Dict[str, BaseDocumentProcessor] = {}
    
    @classmethod
    def register_processor(cls, processor: BaseDocumentProcessor):
        """
        注册文档处理器
        
        Args:
            processor: 处理器实例
        """
        for ext in processor.supported_extensions():
            cls._processors[ext.lower()] = processor
    
    @classmethod
    def get_processor(cls, file_path: Path) -> Optional[BaseDocumentProcessor]:
        """
        根据文件扩展名获取处理器
        
        Args:
            file_path: 文件路径
            
        Returns:
            对应的处理器，如果不支持则返回 None
        """
        ext = file_path.suffix.lower()
        return cls._processors.get(ext)
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """
        获取所有支持的扩展名
        
        Returns:
            支持的扩展名列表
        """
        return list(cls._processors.keys())
    
    @classmethod
    def is_supported(cls, file_path: Path) -> bool:
        """
        检查文件是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持该文件
        """
        return file_path.suffix.lower() in cls._processors


if __name__ == "__main__":
    """测试文档处理器基类"""
    print("=" * 60)
    print("文档处理器基类测试")
    print("=" * 60)
    print()
    
    # 创建一个简单的测试处理器
    class TestProcessor(BaseDocumentProcessor):
        def extract_text(self, file_path: Path) -> str:
            return "测试文本内容"
        
        def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
            return {"test_key": "test_value"}
        
        def supported_extensions(self) -> List[str]:
            return ['.txt']
    
    # 测试处理器
    processor = TestProcessor(chunk_size=10, chunk_overlap=2)
    print("✅ 处理器创建成功")
    print(f"   {processor.get_processor_info()}")
    print()
    
    # 测试文本分割
    text = "这是一段测试文本。" * 10
    chunks = processor.split_text(text)
    print(f"✅ 文本分割测试")
    print(f"   原文长度: {len(text)}")
    print(f"   分割块数: {len(chunks)}")
    print(f"   第一块: {chunks[0][:30]}...")
    print()
    
    print("✅ 基类测试完成！")

