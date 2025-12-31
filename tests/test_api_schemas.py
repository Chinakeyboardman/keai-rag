"""
测试 API 数据模型
"""
import pytest
from pydantic import ValidationError
from src.api.schemas.document import DocumentUploadResponse, DocumentInfo
from src.api.schemas.query import QueryRequest, QueryResponse, SourceInfo
from src.api.schemas.health import HealthResponse


def test_query_request_valid():
    """测试有效的查询请求"""
    request = QueryRequest(
        question="什么是RAG？",
        top_k=3,
        include_suggestions=True
    )
    assert request.question == "什么是RAG？"
    assert request.top_k == 3
    assert request.include_suggestions is True


def test_query_request_defaults():
    """测试查询请求默认值"""
    request = QueryRequest(question="测试问题")
    assert request.top_k == 3
    assert request.include_suggestions is True


def test_query_request_invalid():
    """测试无效的查询请求"""
    # 空问题
    with pytest.raises(ValidationError):
        QueryRequest(question="")
    
    # 无效的 top_k
    with pytest.raises(ValidationError):
        QueryRequest(question="测试", top_k=0)


def test_query_response():
    """测试查询响应"""
    response = QueryResponse(
        question="什么是RAG？",
        answer="RAG是检索增强生成技术。",
        sources=[],
        suggested_questions=["RAG有什么优势？", "如何实现RAG？"],
        has_sources=False,
        success=True
    )
    assert response.question == "什么是RAG？"
    assert len(response.suggested_questions) == 2
    assert response.success is True


def test_source_info():
    """测试来源信息"""
    source = SourceInfo(
        id="chunk_1",
        text="这是一段来源文本",
        score=0.85,
        metadata={"document_id": "doc_123"}
    )
    assert source.metadata["document_id"] == "doc_123"
    assert source.score == 0.85
    assert source.id == "chunk_1"


def test_document_upload_response():
    """测试文档上传响应"""
    response = DocumentUploadResponse(
        document_id="doc_123",
        file_name="test.pdf",
        file_size=1024,
        chunks_count=10,
        message="上传成功",
        success=True
    )
    assert response.document_id == "doc_123"
    assert response.chunks_count == 10
    assert response.success is True


def test_document_info():
    """测试文档信息"""
    from datetime import datetime
    info = DocumentInfo(
        document_id="doc_123",
        file_name="test.pdf",
        file_size=1024,
        file_type="pdf",
        chunks_count=5,
        upload_time=datetime.now()
    )
    assert info.document_id == "doc_123"
    assert info.file_size == 1024


def test_health_response():
    """测试健康检查响应"""
    response = HealthResponse(
        status="healthy",
        version="1.0.0",
        vector_store={"status": "healthy", "count": 100},
        embedding_model={"status": "healthy", "model": "m3e-base"},
        llm_model={"status": "healthy", "model": "deepseek"}
    )
    assert response.status == "healthy"
    assert response.version == "1.0.0"
    assert response.vector_store["status"] == "healthy"

