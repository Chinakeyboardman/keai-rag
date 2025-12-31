"""
测试配置模块
"""
import pytest
from config.settings import settings


def test_settings_loaded(test_settings):
    """测试配置是否正确加载"""
    assert test_settings is not None
    assert test_settings.PROJECT_NAME is not None
    assert test_settings.PROJECT_VERSION is not None


def test_vector_dimension(test_settings):
    """测试向量维度配置"""
    assert test_settings.VECTOR_DIMENSION > 0
    assert isinstance(test_settings.VECTOR_DIMENSION, int)


def test_embedding_config(test_settings):
    """测试 Embedding 配置"""
    assert test_settings.EMBEDDING_MODEL_TYPE in ['local', 'api']
    assert test_settings.EMBEDDING_MODEL_NAME is not None


def test_llm_config(test_settings):
    """测试 LLM 配置"""
    assert test_settings.LLM_MODEL_TYPE in ['local', 'api']
    if test_settings.LLM_MODEL_TYPE == 'local':
        assert test_settings.LLM_MODEL_PATH is not None


def test_chunk_config(test_settings):
    """测试文本分块配置"""
    assert test_settings.CHUNK_SIZE > 0
    assert test_settings.CHUNK_OVERLAP >= 0
    assert test_settings.CHUNK_OVERLAP < test_settings.CHUNK_SIZE


def test_api_config(test_settings):
    """测试 API 配置"""
    assert test_settings.API_PORT > 0
    assert test_settings.API_HOST is not None
    assert test_settings.API_PREFIX.startswith("/")


def test_log_config(test_settings):
    """测试日志配置"""
    assert test_settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    assert test_settings.LOG_MAX_SIZE > 0
    assert test_settings.LOG_BACKUP_COUNT >= 0

