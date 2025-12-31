#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Embedding 服务
支持本地模型和 API 调用
"""

from typing import List, Optional
import numpy as np
from pathlib import Path

from config.settings import settings
from src.utils.logger import logger


class EmbeddingService:
    """Embedding 服务类"""
    
    def __init__(self):
        """初始化 Embedding 服务"""
        self.model_type = settings.EMBEDDING_MODEL_TYPE
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.dimension = settings.VECTOR_DIMENSION
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """初始化模型"""
        if self.model_type == "local":
            self._load_local_model()
        elif self.model_type == "api":
            self._setup_api_client()
        else:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
    
    def _load_local_model(self):
        """加载本地模型"""
        from sentence_transformers import SentenceTransformer
        import os
        
        # 首先尝试使用配置的模型路径
        model_path = settings.get_embedding_model_path()
        if model_path and model_path.exists():
            logger.info(f"📦 加载本地 Embedding 模型: {model_path}")
            try:
                # 设置环境变量强制离线模式
                os.environ['HF_HUB_OFFLINE'] = '1'
                self.model = SentenceTransformer(str(model_path), local_files_only=True)
                logger.info(f"✅ Embedding 模型加载成功")
                return
            except Exception as e:
                logger.warning(f"⚠️  使用配置路径加载失败: {e}")
        
        # 尝试从 HuggingFace 缓存加载
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        model_cache_name = f"models--{self.model_name.replace('/', '--')}"
        model_cache_path = os.path.join(cache_dir, model_cache_name, "snapshots")
        
        if os.path.exists(model_cache_path):
            # 查找最新的快照
            snapshots = [d for d in os.listdir(model_cache_path) if os.path.isdir(os.path.join(model_cache_path, d))]
            if snapshots:
                latest_snapshot = os.path.join(model_cache_path, snapshots[0])
                logger.info(f"📦 从缓存加载 Embedding 模型: {latest_snapshot}")
                try:
                    os.environ['HF_HUB_OFFLINE'] = '1'
                    self.model = SentenceTransformer(latest_snapshot, local_files_only=True)
                    logger.info(f"✅ 从缓存加载模型成功")
                    return
                except Exception as e:
                    logger.warning(f"⚠️  从缓存加载失败: {e}")
        
        # 最后尝试使用模型名称加载（会尝试连接网络）
        logger.info(f"📦 尝试加载 Embedding 模型: {self.model_name}")
        try:
            # 先尝试离线模式
            os.environ['HF_HUB_OFFLINE'] = '1'
            self.model = SentenceTransformer(self.model_name, local_files_only=True)
            logger.info(f"✅ 模型加载成功（离线模式）")
            return
        except Exception as e:
            logger.warning(f"⚠️  离线加载失败: {e}")
            # 如果离线失败，尝试在线下载（可能遇到速率限制）
            try:
                os.environ.pop('HF_HUB_OFFLINE', None)  # 移除离线模式
                logger.info(f"📦 尝试在线下载模型...")
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"✅ 模型下载并加载成功")
                return
            except Exception as e:
                error_msg = (
                    f"加载 Embedding 模型失败: {e}\n"
                    f"提示: 如果遇到速率限制，请:\n"
                    f"  1. 等待一段时间后重试\n"
                    f"  2. 设置 HF_TOKEN 环境变量\n"
                    f"  3. 或手动下载模型到缓存目录"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
    
    def _setup_api_client(self):
        """设置 API 客户端"""
        try:
            from openai import OpenAI
            
            self.model = OpenAI(
                api_key=settings.EMBEDDING_API_KEY,
                base_url=settings.EMBEDDING_API_BASE
            )
            print(f"✅ Embedding API 客户端设置成功")
            
        except Exception as e:
            raise RuntimeError(f"设置 Embedding API 客户端失败: {e}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        对单个文本进行向量化
        
        Args:
            text: 输入文本
            
        Returns:
            文本向量
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")
        
        return self.embed_texts([text])[0]
    
    def embed_texts(self, texts: List[str]) -> List[np.ndarray]:
        """
        对多个文本进行批量向量化
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        if not texts:
            return []
        
        # 过滤空文本
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("没有有效的文本")
        
        if self.model_type == "local":
            return self._embed_with_local_model(valid_texts)
        else:
            return self._embed_with_api(valid_texts)
    
    def _embed_with_local_model(self, texts: List[str]) -> List[np.ndarray]:
        """使用本地模型进行向量化"""
        try:
            if self.model is None:
                raise RuntimeError("Embedding 模型未初始化")
            
            logger.info(f"🔄 开始向量化 {len(texts)} 个文本块（批量大小: {self.batch_size}）...")
            
            # 批量编码
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=True,  # 显示进度条
                convert_to_numpy=True
            )
            
            logger.info(f"✅ 向量化完成，生成 {len(embeddings)} 个向量")
            
            # 转换为列表
            return [emb.astype('float32') for emb in embeddings]
            
        except Exception as e:
            logger.error(f"❌ 本地模型向量化失败: {e}", exc_info=True)
            raise RuntimeError(f"本地模型向量化失败: {e}")
    
    def _embed_with_api(self, texts: List[str]) -> List[np.ndarray]:
        """使用 API 进行向量化"""
        try:
            embeddings = []
            
            # 分批处理
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                
                response = self.model.embeddings.create(
                    model=self.model_name,
                    input=batch,
                    dimensions=self.dimension
                )
                
                batch_embeddings = [
                    np.array(item.embedding, dtype='float32')
                    for item in response.data
                ]
                embeddings.extend(batch_embeddings)
            
            return embeddings
            
        except Exception as e:
            raise RuntimeError(f"API 向量化失败: {e}")
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.dimension
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_type": self.model_type,
            "model_name": self.model_name,
            "dimension": self.dimension,
            "batch_size": self.batch_size
        }


# 全局单例
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取 Embedding 服务单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


if __name__ == "__main__":
    """测试 Embedding 服务"""
    print("=" * 60)
    print("Embedding 服务测试")
    print("=" * 60)
    print()
    
    try:
        # 创建服务
        service = get_embedding_service()
        print(f"✅ 服务创建成功")
        print(f"   {service.get_model_info()}")
        print()
        
        # 测试单个文本
        print("📝 测试单个文本向量化...")
        text = "这是一个测试文本"
        vector = service.embed_text(text)
        print(f"   文本: {text}")
        print(f"   向量维度: {vector.shape}")
        print(f"   向量前5维: {vector[:5]}")
        print()
        
        # 测试批量文本
        print("📝 测试批量文本向量化...")
        texts = [
            "人工智能是计算机科学的一个分支",
            "机器学习是实现人工智能的一种方法",
            "深度学习是机器学习的一个子领域"
        ]
        vectors = service.embed_texts(texts)
        print(f"   文本数量: {len(texts)}")
        print(f"   向量数量: {len(vectors)}")
        print(f"   每个向量维度: {vectors[0].shape}")
        print()
        
        # 计算相似度
        print("🔍 计算文本相似度...")
        from numpy.linalg import norm
        
        def cosine_similarity(a, b):
            return np.dot(a, b) / (norm(a) * norm(b))
        
        sim_01 = cosine_similarity(vectors[0], vectors[1])
        sim_02 = cosine_similarity(vectors[0], vectors[2])
        sim_12 = cosine_similarity(vectors[1], vectors[2])
        
        print(f"   文本0 vs 文本1: {sim_01:.4f}")
        print(f"   文本0 vs 文本2: {sim_02:.4f}")
        print(f"   文本1 vs 文本2: {sim_12:.4f}")
        print()
        
        print("✅ Embedding 服务测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

