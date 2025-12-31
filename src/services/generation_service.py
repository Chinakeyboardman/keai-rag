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
        # 检索相关文档
        logger.info(f"🔍 开始检索相关文档...")
        results = self.retrieval_service.retrieve(question, top_k)
        logger.info(f"✅ 检索完成，找到 {len(results)} 个相关文档块")
        
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
        """构建上下文"""
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[文档{i}]\n{result.text}")
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """构建提示词"""
        return f"""你是一个专业的问答助手。请根据以下文档内容回答用户的问题。

文档内容：
{context}

用户问题：{question}

请基于上述文档内容回答问题。如果文档中没有相关信息，请明确告知用户。回答要准确、简洁、专业。"""


if __name__ == "__main__":
    """测试生成服务"""
    print("=" * 60)
    print("生成服务测试")
    print("=" * 60)
    print()
    print("ℹ️  生成服务需要配合检索服务使用")
    print("   请参考完整的集成测试")

