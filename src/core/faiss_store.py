#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FAISS 向量存储实现
使用 FAISS 作为本地向量数据库（降级方案）
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss

from .vector_store import BaseVectorStore, VectorSearchResult


class FAISSStore(BaseVectorStore):
    """FAISS 向量存储实现"""
    
    def __init__(
        self,
        collection_name: str,
        dimension: int,
        storage_dir: str = "./data/vectors"
    ):
        """
        初始化 FAISS 存储
        
        Args:
            collection_name: 集合名称
            dimension: 向量维度
            storage_dir: 存储目录
        """
        super().__init__(collection_name, dimension)
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 文件路径
        self.index_path = self.storage_dir / f"{collection_name}.index"
        self.metadata_path = self.storage_dir / f"{collection_name}_metadata.pkl"
        self.config_path = self.storage_dir / f"{collection_name}_config.json"
        
        # 初始化索引和元数据
        self.index: Optional[faiss.Index] = None
        self.metadata_store: Dict[int, Dict[str, Any]] = {}
        self.id_to_idx: Dict[str, int] = {}
        self.idx_to_id: Dict[int, str] = {}
        self.next_idx = 0
        
        # 加载或创建索引
        if self.collection_exists():
            self._load()
        else:
            self.create_collection()
    
    def create_collection(self) -> bool:
        """
        创建集合（创建 FAISS 索引）
        
        Returns:
            是否创建成功
        """
        try:
            # 创建 L2 距离的 FAISS 索引
            self.index = faiss.IndexFlatL2(self.dimension)
            
            # 保存配置
            config = {
                "collection_name": self.collection_name,
                "dimension": self.dimension,
                "index_type": "IndexFlatL2"
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 保存空索引
            self._save()
            
            return True
        except Exception as e:
            print(f"创建 FAISS 集合失败: {e}")
            return False
    
    def collection_exists(self) -> bool:
        """
        检查集合是否存在
        
        Returns:
            集合是否存在
        """
        return (
            self.index_path.exists() and
            self.metadata_path.exists() and
            self.config_path.exists()
        )
    
    def delete_collection(self) -> bool:
        """
        删除集合
        
        Returns:
            是否删除成功
        """
        try:
            if self.index_path.exists():
                self.index_path.unlink()
            if self.metadata_path.exists():
                self.metadata_path.unlink()
            if self.config_path.exists():
                self.config_path.unlink()
            
            self.index = None
            self.metadata_store = {}
            self.id_to_idx = {}
            self.idx_to_id = {}
            self.next_idx = 0
            
            return True
        except Exception as e:
            print(f"删除 FAISS 集合失败: {e}")
            return False
    
    def insert_vectors(
        self,
        vectors: List[np.ndarray],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        插入向量
        
        Args:
            vectors: 向量列表
            texts: 文本列表
            metadatas: 元数据列表
            ids: ID 列表（可选）
            
        Returns:
            是否插入成功
        """
        try:
            if self.index is None:
                raise RuntimeError("索引未初始化")
            
            # 验证输入
            if not (len(vectors) == len(texts) == len(metadatas)):
                raise ValueError("向量、文本和元数据数量必须一致")
            
            # 生成 ID（如果未提供）
            if ids is None:
                ids = [f"vec_{self.next_idx + i}" for i in range(len(vectors))]
            
            # 转换向量为 numpy 数组
            vectors_array = np.array([v.astype('float32') for v in vectors])
            
            # 添加到 FAISS 索引
            self.index.add(vectors_array)
            
            # 保存元数据
            for i, (vec_id, text, metadata) in enumerate(zip(ids, texts, metadatas)):
                idx = self.next_idx + i
                self.metadata_store[idx] = {
                    "id": vec_id,
                    "text": text,
                    "metadata": metadata
                }
                self.id_to_idx[vec_id] = idx
                self.idx_to_id[idx] = vec_id
            
            self.next_idx += len(vectors)
            
            # 保存到磁盘
            self._save()
            
            return True
        except Exception as e:
            print(f"插入向量失败: {e}")
            return False
    
    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        搜索相似向量
        
        Args:
            query_vector: 查询向量
            top_k: 返回结果数量
            filter_dict: 过滤条件（可选，FAISS 不支持原生过滤）
            
        Returns:
            搜索结果列表
        """
        try:
            if self.index is None or self.index.ntotal == 0:
                return []
            
            # 转换查询向量
            query_vector = query_vector.astype('float32').reshape(1, -1)
            
            # 搜索
            distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
            
            # 构建结果
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:  # FAISS 返回 -1 表示无效结果
                    continue
                
                idx = int(idx)
                if idx not in self.metadata_store:
                    continue
                
                metadata_entry = self.metadata_store[idx]
                
                # 应用过滤（如果提供）
                if filter_dict:
                    skip = False
                    for key, value in filter_dict.items():
                        if metadata_entry["metadata"].get(key) != value:
                            skip = True
                            break
                    if skip:
                        continue
                
                result = VectorSearchResult(
                    id=metadata_entry["id"],
                    score=float(dist),
                    text=metadata_entry["text"],
                    metadata=metadata_entry["metadata"]
                )
                results.append(result)
            
            return results[:top_k]
        except Exception as e:
            print(f"搜索失败: {e}")
            return []
    
    def delete_by_ids(self, ids: List[str]) -> bool:
        """
        根据 ID 删除向量
        
        注意：FAISS 不支持直接删除，需要重建索引
        
        Args:
            ids: ID 列表
            
        Returns:
            是否删除成功
        """
        try:
            if self.index is None:
                return False
            
            # 找到要删除的索引
            indices_to_delete = set()
            for vec_id in ids:
                if vec_id in self.id_to_idx:
                    indices_to_delete.add(self.id_to_idx[vec_id])
            
            if not indices_to_delete:
                return True
            
            # 重建索引（排除要删除的向量）
            new_index = faiss.IndexFlatL2(self.dimension)
            new_metadata_store = {}
            new_id_to_idx = {}
            new_idx_to_id = {}
            new_idx = 0
            
            # 遍历现有向量
            for old_idx in range(self.index.ntotal):
                if old_idx in indices_to_delete:
                    continue
                
                # 获取向量
                vector = self.index.reconstruct(old_idx)
                new_index.add(vector.reshape(1, -1))
                
                # 复制元数据
                if old_idx in self.metadata_store:
                    metadata_entry = self.metadata_store[old_idx]
                    vec_id = metadata_entry["id"]
                    
                    new_metadata_store[new_idx] = metadata_entry
                    new_id_to_idx[vec_id] = new_idx
                    new_idx_to_id[new_idx] = vec_id
                    new_idx += 1
            
            # 更新索引和元数据
            self.index = new_index
            self.metadata_store = new_metadata_store
            self.id_to_idx = new_id_to_idx
            self.idx_to_id = new_idx_to_id
            self.next_idx = new_idx
            
            # 保存
            self._save()
            
            return True
        except Exception as e:
            print(f"删除向量失败: {e}")
            return False
    
    def get_chunk_ids_by_document_id(self, document_id: str) -> List[str]:
        """
        根据文档 ID 查找所有相关的块 ID
        
        Args:
            document_id: 文档 ID
            
        Returns:
            块 ID 列表
        """
        chunk_ids = []
        if self.index is None:
            return chunk_ids
        
        for old_idx in range(self.index.ntotal):
            if old_idx in self.metadata_store:
                metadata_entry = self.metadata_store[old_idx]
                # document_id 可能在 metadata 字典中，也可能在块 ID 中（格式：document_id_chunk_N）
                metadata = metadata_entry.get("metadata", {})
                vec_id = metadata_entry.get("id", "")
                
                # 方法1: 从 metadata 中查找
                if metadata.get("document_id") == document_id:
                    chunk_ids.append(vec_id)
                # 方法2: 从块 ID 中提取（格式：document_id_chunk_N）
                elif vec_id.startswith(f"{document_id}_chunk_"):
                    chunk_ids.append(vec_id)
        
        return chunk_ids
    
    def get_vector_count(self) -> int:
        """
        获取向量数量
        
        Returns:
            向量数量
        """
        if self.index is None:
            return 0
        return self.index.ntotal
    
    def close(self):
        """关闭连接（保存数据）"""
        self._save()
    
    def _save(self):
        """保存索引和元数据到磁盘"""
        try:
            if self.index is not None:
                faiss.write_index(self.index, str(self.index_path))
            
            with open(self.metadata_path, 'wb') as f:
                pickle.dump({
                    "metadata_store": self.metadata_store,
                    "id_to_idx": self.id_to_idx,
                    "idx_to_id": self.idx_to_id,
                    "next_idx": self.next_idx
                }, f)
        except Exception as e:
            print(f"保存 FAISS 数据失败: {e}")
    
    def _load(self):
        """从磁盘加载索引和元数据"""
        try:
            # 加载索引
            self.index = faiss.read_index(str(self.index_path))
            
            # 加载元数据
            with open(self.metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.metadata_store = data["metadata_store"]
                self.id_to_idx = data["id_to_idx"]
                self.idx_to_id = data["idx_to_id"]
                self.next_idx = data["next_idx"]
        except Exception as e:
            print(f"加载 FAISS 数据失败: {e}")
            raise


if __name__ == "__main__":
    """测试 FAISS 存储"""
    print("=" * 60)
    print("FAISS 存储测试")
    print("=" * 60)
    print()
    
    # 创建存储
    store = FAISSStore(
        collection_name="test_collection",
        dimension=128,
        storage_dir="./test_faiss_data"
    )
    print("✅ FAISS 存储创建成功")
    print(f"   {store.get_store_info()}")
    print()
    
    # 插入测试向量
    print("📥 插入测试向量...")
    vectors = [np.random.rand(128).astype('float32') for _ in range(5)]
    texts = [f"测试文本 {i}" for i in range(5)]
    metadatas = [{"index": i, "type": "test"} for i in range(5)]
    ids = [f"test_vec_{i}" for i in range(5)]
    
    success = store.insert_vectors(vectors, texts, metadatas, ids)
    print(f"   插入{'成功' if success else '失败'}")
    print(f"   向量数量: {store.get_vector_count()}")
    print()
    
    # 搜索测试
    print("🔍 搜索测试...")
    query_vector = np.random.rand(128).astype('float32')
    results = store.search(query_vector, top_k=3)
    print(f"   找到 {len(results)} 个结果")
    for i, result in enumerate(results, 1):
        print(f"   {i}. ID: {result.id}, Score: {result.score:.4f}, Text: {result.text}")
    print()
    
    # 删除测试
    print("🗑️  删除测试...")
    success = store.delete_by_ids(["test_vec_0"])
    print(f"   删除{'成功' if success else '失败'}")
    print(f"   剩余向量: {store.get_vector_count()}")
    print()
    
    # 清理
    store.delete_collection()
    print("✅ 测试完成，已清理测试数据")

