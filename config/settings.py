#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理模块
从环境变量加载配置，并提供配置访问接口
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """应用配置类"""
    
    # ==================== 项目基础配置 ====================
    PROJECT_NAME: str = Field(default="企业级RAG系统", env="PROJECT_NAME")
    PROJECT_VERSION: str = Field(default="1.0.0", env="PROJECT_VERSION")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # ==================== 向量数据库配置 ====================
    USE_QDRANT: bool = Field(default=False, env="USE_QDRANT")
    QDRANT_URL: str = Field(default="http://localhost:6333", env="QDRANT_URL")
    QDRANT_API_KEY: Optional[str] = Field(default=None, env="QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME: str = Field(default="rag_documents", env="QDRANT_COLLECTION_NAME")
    VECTOR_DIMENSION: int = Field(default=1024, env="VECTOR_DIMENSION")
    
    # ==================== Embedding 模型配置 ====================
    EMBEDDING_MODEL_TYPE: str = Field(default="local", env="EMBEDDING_MODEL_TYPE")
    EMBEDDING_MODEL_NAME: str = Field(default="moka-ai/m3e-large", env="EMBEDDING_MODEL_NAME")
    EMBEDDING_MODEL_PATH: Optional[str] = Field(default="./models/m3e-large", env="EMBEDDING_MODEL_PATH")
    EMBEDDING_API_KEY: Optional[str] = Field(default=None, env="EMBEDDING_API_KEY")
    EMBEDDING_API_BASE: str = Field(default="https://api.openai.com/v1", env="EMBEDDING_API_BASE")
    EMBEDDING_BATCH_SIZE: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")
    
    # ==================== LLM 模型配置 ====================
    LLM_MODEL_TYPE: str = Field(default="local", env="LLM_MODEL_TYPE")
    LLM_MODEL_NAME: str = Field(default="deepseek-ai/DeepSeek-R1-Distill-Qwen-7B", env="LLM_MODEL_NAME")
    LLM_MODEL_PATH: Optional[str] = Field(
        default="/Users/chenjiawei/Public/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
        env="LLM_MODEL_PATH"
    )
    LLM_API_KEY: Optional[str] = Field(default=None, env="LLM_API_KEY")
    LLM_API_BASE: str = Field(default="https://api.deepseek.com/v1", env="LLM_API_BASE")
    LLM_TEMPERATURE: float = Field(default=0.7, env="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(default=2000, env="LLM_MAX_TOKENS")
    LLM_TOP_P: float = Field(default=0.95, env="LLM_TOP_P")
    
    # ==================== 文档处理配置 ====================
    CHUNK_SIZE: int = Field(default=1000, env="CHUNK_SIZE")
    CHUNK_OVERLAP: int = Field(default=200, env="CHUNK_OVERLAP")
    RETRIEVAL_TOP_K: int = Field(default=3, env="RETRIEVAL_TOP_K")
    
    # ==================== 数据存储路径 ====================
    DATA_DIR: str = Field(default="./data", env="DATA_DIR")
    VECTOR_STORE_DIR: str = Field(default="./data/vectors", env="VECTOR_STORE_DIR")
    METADATA_DIR: str = Field(default="./data/metadata", env="METADATA_DIR")
    DOCUMENTS_DIR: str = Field(default="./data/documents", env="DOCUMENTS_DIR")
    
    # ==================== API 服务配置 ====================
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_PREFIX: str = Field(default="/api/v1", env="API_PREFIX")
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://localhost:8080", env="CORS_ORIGINS")
    
    # ==================== 日志配置 ====================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field(default="./logs/app.log", env="LOG_FILE")
    LOG_MAX_SIZE: int = Field(default=10, env="LOG_MAX_SIZE")  # MB
    LOG_BACKUP_COUNT: int = Field(default=5, env="LOG_BACKUP_COUNT")
    
    @validator("EMBEDDING_MODEL_TYPE")
    def validate_embedding_model_type(cls, v):
        """验证 Embedding 模型类型"""
        if v not in ["local", "api"]:
            raise ValueError("EMBEDDING_MODEL_TYPE 必须是 'local' 或 'api'")
        return v
    
    @validator("LLM_MODEL_TYPE")
    def validate_llm_model_type(cls, v):
        """验证 LLM 模型类型"""
        if v not in ["local", "api"]:
            raise ValueError("LLM_MODEL_TYPE 必须是 'local' 或 'api'")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """验证日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL 必须是以下之一: {', '.join(valid_levels)}")
        return v.upper()
    
    @validator("CORS_ORIGINS")
    def parse_cors_origins(cls, v):
        """解析 CORS 来源"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    def get_data_dir(self) -> Path:
        """获取数据目录路径"""
        return Path(self.DATA_DIR)
    
    def get_vector_store_dir(self) -> Path:
        """获取向量存储目录路径"""
        return Path(self.VECTOR_STORE_DIR)
    
    def get_metadata_dir(self) -> Path:
        """获取元数据目录路径"""
        return Path(self.METADATA_DIR)
    
    def get_documents_dir(self) -> Path:
        """获取文档目录路径"""
        return Path(self.DOCUMENTS_DIR)
    
    def get_log_file(self) -> Path:
        """获取日志文件路径"""
        return Path(self.LOG_FILE)
    
    def ensure_directories(self):
        """确保所有必要的目录存在"""
        directories = [
            self.get_data_dir(),
            self.get_vector_store_dir(),
            self.get_metadata_dir(),
            self.get_documents_dir(),
            self.get_log_file().parent,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def is_local_embedding(self) -> bool:
        """是否使用本地 Embedding 模型"""
        return self.EMBEDDING_MODEL_TYPE == "local"
    
    def is_local_llm(self) -> bool:
        """是否使用本地 LLM 模型"""
        return self.LLM_MODEL_TYPE == "local"
    
    def get_embedding_model_path(self) -> Optional[Path]:
        """获取 Embedding 模型路径"""
        if self.is_local_embedding() and self.EMBEDDING_MODEL_PATH:
            return Path(self.EMBEDDING_MODEL_PATH)
        return None
    
    def get_llm_model_path(self) -> Optional[Path]:
        """获取 LLM 模型路径"""
        if self.is_local_llm() and self.LLM_MODEL_PATH:
            return Path(self.LLM_MODEL_PATH)
        return None
    
    class Config:
        """Pydantic 配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例（用于依赖注入）"""
    return settings


# 初始化时确保目录存在
settings.ensure_directories()


if __name__ == "__main__":
    """测试配置加载"""
    print("=" * 60)
    print("配置加载测试")
    print("=" * 60)
    print()
    
    print("📋 项目配置:")
    print(f"  项目名称: {settings.PROJECT_NAME}")
    print(f"  版本: {settings.PROJECT_VERSION}")
    print(f"  调试模式: {settings.DEBUG}")
    print()
    
    print("📦 向量数据库配置:")
    print(f"  使用 Qdrant: {settings.USE_QDRANT}")
    print(f"  Qdrant URL: {settings.QDRANT_URL}")
    print(f"  集合名称: {settings.QDRANT_COLLECTION_NAME}")
    print(f"  向量维度: {settings.VECTOR_DIMENSION}")
    print()
    
    print("🤖 Embedding 模型配置:")
    print(f"  模型类型: {settings.EMBEDDING_MODEL_TYPE}")
    print(f"  模型名称: {settings.EMBEDDING_MODEL_NAME}")
    print(f"  模型路径: {settings.EMBEDDING_MODEL_PATH}")
    print(f"  批处理大小: {settings.EMBEDDING_BATCH_SIZE}")
    print()
    
    print("🧠 LLM 模型配置:")
    print(f"  模型类型: {settings.LLM_MODEL_TYPE}")
    print(f"  模型名称: {settings.LLM_MODEL_NAME}")
    print(f"  模型路径: {settings.LLM_MODEL_PATH}")
    print(f"  温度: {settings.LLM_TEMPERATURE}")
    print(f"  最大 Token: {settings.LLM_MAX_TOKENS}")
    print()
    
    print("📄 文档处理配置:")
    print(f"  分块大小: {settings.CHUNK_SIZE}")
    print(f"  分块重叠: {settings.CHUNK_OVERLAP}")
    print(f"  检索数量: {settings.RETRIEVAL_TOP_K}")
    print()
    
    print("📁 数据目录:")
    print(f"  数据根目录: {settings.get_data_dir()}")
    print(f"  向量存储: {settings.get_vector_store_dir()}")
    print(f"  元数据: {settings.get_metadata_dir()}")
    print(f"  文档: {settings.get_documents_dir()}")
    print()
    
    print("🌐 API 配置:")
    print(f"  主机: {settings.API_HOST}")
    print(f"  端口: {settings.API_PORT}")
    print(f"  前缀: {settings.API_PREFIX}")
    print(f"  CORS 来源: {settings.CORS_ORIGINS}")
    print()
    
    print("📝 日志配置:")
    print(f"  日志级别: {settings.LOG_LEVEL}")
    print(f"  日志文件: {settings.get_log_file()}")
    print()
    
    print("✅ 配置加载成功！")

