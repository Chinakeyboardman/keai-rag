#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
日志工具模块
提供统一的日志配置和记录功能
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from config.settings import settings


class Logger:
    """日志管理器"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name: str = "rag_system") -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            配置好的日志记录器
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, settings.LOG_LEVEL))
        
        # 避免重复添加处理器
        if logger.handlers:
            return logger
        
        # 创建日志目录
        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 文件处理器（带轮转）
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=settings.LOG_MAX_SIZE * 1024 * 1024,  # MB to bytes
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        cls._loggers[name] = logger
        return logger


# 创建默认日志记录器
logger = Logger.get_logger()


def log_function_call(func):
    """
    装饰器：记录函数调用
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰后的函数
    """
    def wrapper(*args, **kwargs):
        logger.debug(f"调用函数: {func.__name__}, args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {e}", exc_info=True)
            raise
    return wrapper


def log_api_request(endpoint: str, method: str, status_code: int, duration: float):
    """
    记录API请求
    
    Args:
        endpoint: API端点
        method: HTTP方法
        status_code: 状态码
        duration: 请求耗时（秒）
    """
    logger.info(
        f"API请求 - {method} {endpoint} - "
        f"状态码: {status_code} - 耗时: {duration:.3f}s"
    )


def log_error(error: Exception, context: Optional[str] = None):
    """
    记录错误
    
    Args:
        error: 异常对象
        context: 错误上下文信息
    """
    msg = f"错误: {str(error)}"
    if context:
        msg = f"{context} - {msg}"
    logger.error(msg, exc_info=True)


def log_warning(message: str):
    """
    记录警告
    
    Args:
        message: 警告信息
    """
    logger.warning(message)


def log_info(message: str):
    """
    记录信息
    
    Args:
        message: 信息内容
    """
    logger.info(message)


def log_debug(message: str):
    """
    记录调试信息
    
    Args:
        message: 调试信息
    """
    logger.debug(message)

