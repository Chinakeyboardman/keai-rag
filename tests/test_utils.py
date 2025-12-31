"""
测试工具模块
"""
import pytest
from src.utils.logger import Logger, log_info, log_error, log_warning
from src.utils.exceptions import (
    RAGSystemException,
    DocumentProcessingException,
    UnsupportedFileFormatException,
    VectorStoreException,
    ModelException,
    APIException,
    handle_exception
)


def test_logger_creation():
    """测试日志记录器创建"""
    logger = Logger.get_logger("test_logger")
    assert logger is not None
    assert logger.name == "test_logger"


def test_logger_singleton():
    """测试日志记录器单例模式"""
    logger1 = Logger.get_logger("test_singleton")
    logger2 = Logger.get_logger("test_singleton")
    assert logger1 is logger2


def test_log_functions():
    """测试日志函数"""
    # 这些函数不应该抛出异常
    log_info("测试信息")
    log_warning("测试警告")
    log_error(Exception("测试错误"), "测试上下文")


def test_rag_system_exception():
    """测试基础异常"""
    exc = RAGSystemException("测试错误", "TEST_ERROR")
    assert exc.message == "测试错误"
    assert exc.code == "TEST_ERROR"
    assert str(exc) == "测试错误"


def test_document_processing_exception():
    """测试文档处理异常"""
    exc = DocumentProcessingException("文档处理失败")
    assert exc.code == "DOCUMENT_PROCESSING_ERROR"
    assert "文档处理失败" in exc.message


def test_unsupported_file_format_exception():
    """测试不支持的文件格式异常"""
    exc = UnsupportedFileFormatException("docx")
    assert "docx" in exc.message
    assert exc.code == "DOCUMENT_PROCESSING_ERROR"


def test_vector_store_exception():
    """测试向量存储异常"""
    exc = VectorStoreException("存储失败")
    assert exc.code == "VECTOR_STORE_ERROR"


def test_model_exception():
    """测试模型异常"""
    exc = ModelException("模型错误")
    assert exc.code == "MODEL_ERROR"


def test_api_exception():
    """测试API异常"""
    exc = APIException("API错误", 400)
    assert exc.status_code == 400
    assert exc.code == "API_ERROR"


def test_handle_exception_with_api_exception():
    """测试处理API异常"""
    exc = APIException("测试错误", 404)
    message, status_code = handle_exception(exc)
    assert message == "测试错误"
    assert status_code == 404


def test_handle_exception_with_rag_exception():
    """测试处理RAG系统异常"""
    exc = RAGSystemException("系统错误")
    message, status_code = handle_exception(exc)
    assert message == "系统错误"
    assert status_code == 500


def test_handle_exception_with_unknown_exception():
    """测试处理未知异常"""
    exc = ValueError("未知错误")
    message, status_code = handle_exception(exc)
    assert "未知错误" in message
    assert status_code == 500

