#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成服务
实现 RAG 生成和问题推荐
"""

from typing import List, Dict, Any, Optional

from src.services.llm_service import get_llm_service
from src.services.retrieval_service import RetrievalService
from src.utils.logger import logger


class GenerationService:
    """生成服务类"""
    
    def __init__(self, retrieval_service: RetrievalService):
        """
        初始化生成服务
        
        Args:
            retrieval_service: 检索服务实例
        """
        self.retrieval_service = retrieval_service
        self.llm_service = get_llm_service()
    
    def generate_answer(
        self,
        question: str,
        top_k: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        基于 RAG 生成答案
        
        Args:
            question: 用户问题
            top_k: 检索文档数量
            
        Returns:
            包含答案和相关信息的字典
        """
        # 检索相关文档（增加检索数量以提高召回率）
        logger.info(f"🔍 开始检索相关文档...")
        # 如果top_k未指定，使用更大的默认值以提高召回率（至少10个）
        effective_top_k = top_k if top_k is not None else max(10, self.retrieval_service.top_k)
        results = self.retrieval_service.retrieve(question, effective_top_k)
        logger.info(f"✅ 检索完成，找到 {len(results)} 个相关文档块")
        
        # 记录检索结果的相似度分数
        if results:
            scores = [r.score for r in results]
            logger.info(f"📊 相似度分数范围: {min(scores):.4f} - {max(scores):.4f}, 平均: {sum(scores)/len(scores):.4f}")
        
        if not results:
            logger.warning(f"⚠️  未找到相关文档")
            return {
                "answer": "抱歉，我没有找到相关的文档来回答这个问题。",
                "sources": [],
                "has_sources": False
            }
        
        # 构建上下文
        logger.info(f"📝 构建上下文...")
        context = self._build_context(results)
        logger.info(f"✅ 上下文构建完成，长度: {len(context)} 字符")
        
        # 构建提示词
        logger.info(f"📝 构建提示词...")
        prompt = self._build_prompt(question, context)
        logger.info(f"✅ 提示词构建完成，长度: {len(prompt)} 字符")
        # 打印提示词前100字
        logger.info(f"📝 提示词前100字: {prompt[:100]}")
        
        # 生成答案
        logger.info(f"🤖 开始调用 LLM 生成答案...")
        try:
            import time
            start_time = time.time()
            answer = self.llm_service.generate(prompt)
            elapsed_time = time.time() - start_time
            logger.info(f"✅ LLM 生成完成，耗时 {elapsed_time:.2f} 秒，答案长度: {len(answer)} 字符")
        except Exception as e:
            logger.error(f"❌ LLM 生成失败: {e}", exc_info=True)
            raise
        
        # 构建来源信息
        sources = [
            {
                "id": result.id,
                "text": result.text[:200] + "..." if len(result.text) > 200 else result.text,
                "score": result.score,
                "metadata": result.metadata
            }
            for result in results
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "has_sources": True
        }
    
    def suggest_questions(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None,
        num_questions: int = 3
    ) -> List[str]:
        """
        基于问题和答案生成相关问题推荐
        
        Args:
            question: 原始问题
            answer: 生成的答案
            context: 上下文（可选）
            num_questions: 推荐问题数量
            
        Returns:
            推荐问题列表
        """
        prompt = f"""基于以下对话，生成{num_questions}个用户可能想问的相关问题。

用户问题：{question}

回答：{answer}

请直接列出{num_questions}个相关问题，每个问题一行，不要编号，不要额外解释。"""
        
        # 生成推荐问题
        logger.info(f"🤖 调用 LLM 生成推荐问题...")
        try:
            response = self.llm_service.generate(prompt, temperature=0.8)
            logger.info(f"✅ LLM 推荐问题生成完成")
        except Exception as e:
            logger.error(f"❌ LLM 生成推荐问题失败: {e}", exc_info=True)
            raise
        
        # 解析问题
        questions = [
            q.strip().lstrip("0123456789.-、").strip()
            for q in response.strip().split("\n")
            if q.strip()
        ]
        
        return questions[:num_questions]
    
    def generate_with_suggestions(
        self,
        question: str,
        top_k: Optional[int] = None,
        num_suggestions: int = 3
    ) -> Dict[str, Any]:
        """
        生成答案并推荐相关问题
        
        Args:
            question: 用户问题
            top_k: 检索文档数量
            num_suggestions: 推荐问题数量
            
        Returns:
            包含答案、来源和推荐问题的字典
        """
        # 生成答案
        result = self.generate_answer(question, top_k)
        
        # 生成推荐问题
        if result["has_sources"]:
            try:
                logger.info(f"💡 开始生成推荐问题...")
                suggestions = self.suggest_questions(
                    question,
                    result["answer"],
                    num_questions=num_suggestions
                )
                logger.info(f"✅ 推荐问题生成完成，共 {len(suggestions)} 个")
            except Exception as e:
                logger.warning(f"⚠️  生成推荐问题失败: {e}")
                suggestions = []
        else:
            suggestions = []
        
        result["suggested_questions"] = suggestions
        
        return result
    
    def _build_context(self, results: List[Any]) -> str:
        """
        构建上下文，整合多个文档块
        - 智能选择1-5个最相关的块
        
        Args:
            results: 检索结果列表
            
        Returns:
            格式化的上下文字符串
        """
        if not results:
            return ""
        
        # 按相似度分数排序（分数越高越相关）
        sorted_results = sorted(results, key=lambda x: x.score, reverse=True)
        
        # 去重：如果多个块有相同的文本，只保留相似度最高的
        seen_texts = set()
        unique_results = []
        for result in sorted_results:
            # 使用文本的前100字符作为唯一标识（避免完全重复）
            text_key = result.text[:100].strip()
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_results.append(result)
        
        logger.info(f"📋 构建上下文: 原始{len(results)}个块，去重后{len(unique_results)}个块")
        
        # 智能选择1-5个最相关的块
        selected_results = self._select_relevant_blocks_simple(unique_results, min_blocks=1, max_blocks=5)
        logger.info(f"📋 最终选择: {len(selected_results)}个块用于生成答案")
        
        # 详细记录选中的块信息
        logger.info(f"📌 选用的块详情：")
        for i, result in enumerate(selected_results, 1):
            chunk_idx = result.metadata.get('chunk_index', -1) if result.metadata else -1
            doc_id = result.metadata.get('document_id', '') if result.metadata else 'unknown'
            doc_id_short = doc_id[:8] + '...' if doc_id and len(doc_id) > 8 else (doc_id if doc_id else 'unknown')
            block_id = result.id[:30] + '...' if len(result.id) > 30 else result.id
            text_preview = result.text[:50] + '...' if len(result.text) > 50 else result.text
            logger.info(f"   ✅ 块{i}: 文档ID={doc_id_short}, chunk_index={chunk_idx}, "
                      f"块ID={block_id}, 相似度={result.score:.4f}, 文本预览={text_preview}")
        
        # 构建上下文
        context_parts = []
        for i, result in enumerate(selected_results, 1):
            context_parts.append(
                f"[文档 {i}]\n{result.text}"
            )
        
        return "\n\n".join(context_parts)
    
    def _select_relevant_blocks_simple(self, results: List[Any], min_blocks: int = 1, max_blocks: int = 5) -> List[Any]:
        """
        智能选择最相关的块（1-5个）
        
        Args:
            results: 检索结果列表（已按相似度排序）
            min_blocks: 最少块数
            max_blocks: 最多块数
            
        Returns:
            选中的块列表
        """
        if not results:
            return []
        
        # 如果块数少于等于max_blocks，全部使用
        if len(results) <= max_blocks:
            return results[:max_blocks]
        
        # 智能选择策略：
        # 1. 优先选择相似度最高的块
        # 2. 如果前几个块相似度都很高（差距小），多选几个
        # 3. 如果相似度差距大，少选几个
        
        selected = [results[0]]  # 至少选择最相关的块
        
        if len(results) == 1:
            return selected
        
        # 计算相似度分数差距
        scores = [r.score for r in results]
        max_score = scores[0]
        
        # 如果前几个块相似度都很高（差距小于0.1），多选几个
        threshold = max_score - 0.1
        
        for i in range(1, min(len(results), max_blocks)):
            if scores[i] >= threshold:
                selected.append(results[i])
            else:
                # 相似度差距较大，如果已经有2个以上块，可以停止
                if len(selected) >= 2:
                    break
                # 否则至少再选一个
                selected.append(results[i])
                break
        
        # 确保至少选择min_blocks个
        while len(selected) < min_blocks and len(selected) < len(results):
            next_idx = len(selected)
            if next_idx < len(results):
                selected.append(results[next_idx])
            else:
                break
        
        return selected
    
    def _build_prompt(self, question: str, context: str) -> str:
        """
        构建提示词，优化多块整合
        
        Args:
            question: 用户问题
            context: 上下文（包含多个文档块）
            
        Returns:
            格式化的提示词
        """
        return f"""你是一个专业的问答助手。请仔细阅读以下文档内容，并基于这些文档内容准确、全面地回答用户的问题。

文档内容：
{context}

用户问题：{question}

重要提示：
1. **仔细阅读**：请仔细阅读所有提供的文档内容，整合其中的信息来回答问题。

2. **信息整合**：
   - 如果文档中明确提到了相关信息，请直接引用文档内容回答
   - 如果文档中提到了相关概念但信息不完整，请基于文档内容进行合理推断
   - 如果文档中提供了不同角度的信息，请整合这些信息给出全面的答案
   - 只有在文档中完全没有相关信息时，才告知用户文档中没有相关信息

3. **回答要求**：
   - 回答要准确、简洁、专业
   - 优先使用文档中的原话或关键信息
   - 回答要自然流畅，不要暴露技术细节（如"文档块"、"相似度"等术语）
   - 直接回答问题，就像在阅读完整文档后回答一样

4. **回答格式**：
   - 如果文档中有明确答案，直接给出答案
   - 如果需要进行推断，可以说明"根据文档内容"或"基于文档信息"
   - 回答要符合自然对话的风格，让用户感觉像是在与熟悉文档的助手对话

请开始回答："""


if __name__ == "__main__":
    """测试生成服务"""
    print("=" * 60)
    print("生成服务测试")
    print("=" * 60)
    print()
    print("ℹ️  生成服务需要配合检索服务使用")
    print("   请参考完整的集成测试")

