#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自定义异常模块
定义系统中使用的各种异常类
"""


class RAGSystemException(Exception):
    """RAG系统基础异常"""
    
    def __init__(self, message: str, code: str = "SYSTEM_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# ==================== 文档处理异常 ====================

class DocumentProcessingException(RAGSystemException):
    """文档处理异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "DOCUMENT_PROCESSING_ERROR")


class UnsupportedFileFormatException(DocumentProcessingException):
    """不支持的文件格式异常"""
    
    def __init__(self, file_format: str):
        message = f"不支持的文件格式: {file_format}"
        super().__init__(message)


class FileReadException(DocumentProcessingException):
    """文件读取异常"""
    
    def __init__(self, file_path: str, reason: str):
        message = f"无法读取文件 {file_path}: {reason}"
        super().__init__(message)


class DocumentParsingException(DocumentProcessingException):
    """文档解析异常"""
    
    def __init__(self, file_path: str, reason: str):
        message = f"解析文档 {file_path} 失败: {reason}"
        super().__init__(message)


# ==================== 向量存储异常 ====================

class VectorStoreException(RAGSystemException):
    """向量存储异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "VECTOR_STORE_ERROR")


class VectorStoreConnectionException(VectorStoreException):
    """向量存储连接异常"""
    
    def __init__(self, store_type: str, reason: str):
        message = f"无法连接到向量存储 {store_type}: {reason}"
        super().__init__(message)


class VectorInsertException(VectorStoreException):
    """向量插入异常"""
    
    def __init__(self, reason: str):
        message = f"向量插入失败: {reason}"
        super().__init__(message)


class VectorSearchException(VectorStoreException):
    """向量搜索异常"""
    
    def __init__(self, reason: str):
        message = f"向量搜索失败: {reason}"
        super().__init__(message)


class VectorDeleteException(VectorStoreException):
    """向量删除异常"""
    
    def __init__(self, reason: str):
        message = f"向量删除失败: {reason}"
        super().__init__(message)


# ==================== 模型相关异常 ====================

class ModelException(RAGSystemException):
    """模型异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "MODEL_ERROR")


class ModelLoadException(ModelException):
    """模型加载异常"""
    
    def __init__(self, model_name: str, reason: str):
        message = f"加载模型 {model_name} 失败: {reason}"
        super().__init__(message)


class EmbeddingException(ModelException):
    """向量化异常"""
    
    def __init__(self, reason: str):
        message = f"文本向量化失败: {reason}"
        super().__init__(message)


class LLMGenerationException(ModelException):
    """LLM生成异常"""
    
    def __init__(self, reason: str):
        message = f"LLM生成失败: {reason}"
        super().__init__(message)


# ==================== API异常 ====================

class APIException(RAGSystemException):
    """API异常"""
    
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, "API_ERROR")
        self.status_code = status_code


class InvalidRequestException(APIException):
    """无效请求异常"""
    
    def __init__(self, message: str):
        super().__init__(message, 400)


class ResourceNotFoundException(APIException):
    """资源未找到异常"""
    
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} {resource_id} 未找到"
        super().__init__(message, 404)


class AuthenticationException(APIException):
    """认证异常"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, 401)


class AuthorizationException(APIException):
    """授权异常"""
    
    def __init__(self, message: str = "无权限访问"):
        super().__init__(message, 403)


class RateLimitException(APIException):
    """速率限制异常"""
    
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(message, 429)


# ==================== 配置异常 ====================

class ConfigurationException(RAGSystemException):
    """配置异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "CONFIGURATION_ERROR")


class MissingConfigException(ConfigurationException):
    """缺少配置异常"""
    
    def __init__(self, config_key: str):
        message = f"缺少必要配置: {config_key}"
        super().__init__(message)


class InvalidConfigException(ConfigurationException):
    """无效配置异常"""
    
    def __init__(self, config_key: str, reason: str):
        message = f"配置 {config_key} 无效: {reason}"
        super().__init__(message)


# ==================== 服务异常 ====================

class ServiceException(RAGSystemException):
    """服务异常"""
    
    def __init__(self, message: str):
        super().__init__(message, "SERVICE_ERROR")


class RetrievalException(ServiceException):
    """检索异常"""
    
    def __init__(self, reason: str):
        message = f"文档检索失败: {reason}"
        super().__init__(message)


class GenerationException(ServiceException):
    """生成异常"""
    
    def __init__(self, reason: str):
        message = f"答案生成失败: {reason}"
        super().__init__(message)


# ==================== 工具函数 ====================

def handle_exception(exception: Exception) -> tuple[str, int]:
    """
    处理异常，返回错误信息和状态码
    
    Args:
        exception: 异常对象
        
    Returns:
        (错误信息, HTTP状态码)
    """
    if isinstance(exception, APIException):
        return exception.message, exception.status_code
    elif isinstance(exception, RAGSystemException):
        return exception.message, 500
    else:
        return f"未知错误: {str(exception)}", 500

