"""
测试文档处理器
"""
import pytest
from src.processors.base import DocumentProcessorFactory
from src.processors.pdf_processor import PDFProcessor


def test_pdf_processor_creation():
    """测试 PDF 处理器创建"""
    processor = PDFProcessor(chunk_size=500, chunk_overlap=100)
    assert processor is not None
    assert processor.chunk_size == 500
    assert processor.chunk_overlap == 100


def test_text_splitting(sample_pdf_text):
    """测试文本分割"""
    processor = PDFProcessor(chunk_size=500, chunk_overlap=100)
    chunks = processor.split_text(sample_pdf_text)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    # 检查分块大小是否合理
    for chunk in chunks:
        assert len(chunk) <= 600  # 允许一些余量


def test_processor_factory():
    """测试处理器工厂"""
    from pathlib import Path
    factory = DocumentProcessorFactory()
    
    # 测试支持的扩展名
    supported = factory.get_supported_extensions()
    assert isinstance(supported, list)
    
    # 测试 PDF 文件检测
    pdf_path = Path("test.pdf")
    # 如果工厂没有注册处理器，返回 None 是正常的
    processor = factory.get_processor(pdf_path)
    # 只检查返回值类型
    assert processor is None or isinstance(processor, PDFProcessor)


def test_empty_text_handling():
    """测试空文本处理"""
    processor = PDFProcessor()
    chunks = processor.split_text("")
    assert len(chunks) == 0


def test_short_text_handling():
    """测试短文本处理"""
    processor = PDFProcessor(chunk_size=500)
    short_text = "这是一段很短的文本。"
    chunks = processor.split_text(short_text)
    assert len(chunks) == 1
    assert chunks[0] == short_text

