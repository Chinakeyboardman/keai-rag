"""
pytest 配置文件
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from config.settings import settings


@pytest.fixture
def test_settings():
    """测试配置"""
    return settings


@pytest.fixture
def sample_texts():
    """示例文本"""
    return [
        "人工智能是计算机科学的一个分支。",
        "机器学习是人工智能的子领域。",
        "深度学习使用神经网络。",
        "RAG结合了检索和生成技术。"
    ]


@pytest.fixture
def sample_pdf_text():
    """示例 PDF 文本"""
    return """
    企业级 RAG 系统设计文档
    
    第一章：系统概述
    本系统是一个基于检索增强生成（RAG）的智能问答系统。
    
    第二章：技术架构
    系统采用分层架构设计，包括：
    1. 文档处理层
    2. 向量存储层
    3. 检索层
    4. 生成层
    
    第三章：核心功能
    - PDF 文档解析
    - 智能文本分块
    - 向量化存储
    - 语义检索
    - 答案生成
    """ * 10  # 重复以生成足够长的文本

