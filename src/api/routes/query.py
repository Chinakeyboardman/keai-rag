#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查询路由
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import asyncio
import json
from queue import Queue
from threading import Thread

from src.api.schemas.query import QueryRequest, QueryResponse, SourceInfo
from src.api.dependencies import get_generation_service
from src.services.generation_service import GenerationService
from src.utils.logger import logger

router = APIRouter()


@router.post("/query", response_model=QueryResponse, tags=["查询"])
async def query(
    request: QueryRequest,
    generation_service: GenerationService = Depends(get_generation_service)
):
    """
    查询接口
    
    基于文档内容回答用户问题，并推荐相关问题
    """
    try:
        logger.info(f"🔍 收到查询请求: {request.question[:50]}...")
        
        # 使用 asyncio.wait_for 添加超时保护
        try:
            if request.include_suggestions:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        generation_service.generate_with_suggestions,
                        request.question,
                        request.top_k,
                        request.num_suggestions
                    ),
                    timeout=180.0  # 180秒超时
                )
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        generation_service.generate_answer,
                        request.question,
                        request.top_k
                    ),
                    timeout=180.0  # 180秒超时
                )
                result["suggested_questions"] = None
        except asyncio.TimeoutError:
            logger.error(f"❌ 查询超时（超过180秒）")
            raise HTTPException(status_code=504, detail="查询超时，请稍后重试或简化问题")
        
        # 转换来源信息
        sources = [
            SourceInfo(**source)
            for source in result["sources"]
        ]
        
        logger.info(f"✅ 查询成功，找到 {len(sources)} 个来源")
        
        return QueryResponse(
            question=request.question,
            answer=result["answer"],
            sources=sources,
            has_sources=result["has_sources"],
            suggested_questions=result.get("suggested_questions"),
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 查询失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/query/stream", tags=["查询"])
async def query_stream(
    request: QueryRequest,
    generation_service: GenerationService = Depends(get_generation_service)
):
    """
    流式查询接口（Server-Sent Events）
    
    基于文档内容流式回答用户问题，实时返回生成的文字
    
    返回格式：
    - 首先发送 sources 信息（JSON格式）
    - 然后流式发送答案文本片段
    - 发送 done 标记（包含完整答案）
    - 如果启用推荐问题，发送 suggestions 标记（包含推荐问题列表）
    """
    async def generate():
        try:
            logger.info(f"🔍 收到流式查询请求: {request.question[:50]}...")
            
            # 使用队列在线程间传递chunks
            chunk_queue = Queue()
            error_occurred = [False]
            error_message = [None]
            full_answer_ref = [None]  # 用于存储完整答案，供推荐问题生成使用
            sources_ref = [None]  # 用于存储来源信息，判断是否需要生成推荐问题
            
            def run_stream_in_thread():
                """在线程中运行流式生成"""
                try:
                    answer_generator, sources = generation_service.generate_answer_stream(
                        request.question,
                        request.top_k
                    )
                    
                    sources_ref[0] = sources
                    
                    # 先发送sources标记
                    chunk_queue.put(("sources", sources))
                    
                    # 然后流式发送chunks
                    full_answer = ""
                    for chunk in answer_generator:
                        full_answer += chunk
                        chunk_queue.put(("chunk", chunk))
                    
                    full_answer_ref[0] = full_answer
                    
                    # 发送完成标记
                    chunk_queue.put(("done", full_answer))
                    chunk_queue.put(None)  # 结束标记
                    
                except Exception as e:
                    logger.error(f"❌ 流式生成线程失败: {e}", exc_info=True)
                    error_occurred[0] = True
                    error_message[0] = str(e)
                    chunk_queue.put(None)
            
            # 启动后台线程
            thread = Thread(target=run_stream_in_thread, daemon=True)
            thread.start()
            
            # 等待并发送sources信息
            sources = None
            full_answer = None
            
            while True:
                item = chunk_queue.get()
                if item is None:
                    break
                
                item_type, item_data = item
                
                if item_type == "sources":
                    sources = item_data
                    # 转换来源信息
                    source_infos = [
                        SourceInfo(**source)
                        for source in sources
                    ]
                    
                    # 发送来源信息
                    sources_data = {
                        "type": "sources",
                        "sources": [
                            {
                                "id": s.id,
                                "text": s.text,
                                "score": s.score,
                                "metadata": s.metadata
                            }
                            for s in source_infos
                        ],
                        "has_sources": len(source_infos) > 0
                    }
                    yield f"data: {json.dumps(sources_data, ensure_ascii=False)}\n\n"
                
                elif item_type == "chunk":
                    # 流式发送答案文本片段
                    yield f"data: {json.dumps({'type': 'chunk', 'content': item_data}, ensure_ascii=False)}\n\n"
                
                elif item_type == "done":
                    full_answer = item_data
                    # 发送完成标记
                    done_data = {
                        "type": "done",
                        "answer": item_data
                    }
                    yield f"data: {json.dumps(done_data, ensure_ascii=False)}\n\n"
                    logger.info(f"✅ 流式查询完成，答案长度: {len(item_data)} 字符")
                    break
            
            # 检查是否有错误
            if error_occurred[0]:
                error_data = {
                    "type": "error",
                    "message": error_message[0]
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                return
            
            # 如果启用推荐问题且答案生成成功，生成推荐问题
            if request.include_suggestions and full_answer and sources and len(sources) > 0:
                try:
                    logger.info(f"💡 开始生成推荐问题...")
                    # 在线程中生成推荐问题，避免阻塞
                    suggestions = await asyncio.to_thread(
                        generation_service.suggest_questions,
                        request.question,
                        full_answer,
                        None,
                        request.num_suggestions
                    )
                    logger.info(f"✅ 推荐问题生成完成，共 {len(suggestions)} 个")
                    
                    # 发送推荐问题
                    suggestions_data = {
                        "type": "suggestions",
                        "suggested_questions": suggestions
                    }
                    yield f"data: {json.dumps(suggestions_data, ensure_ascii=False)}\n\n"
                except Exception as e:
                    logger.warning(f"⚠️  生成推荐问题失败: {e}")
                    # 即使推荐问题生成失败，也不影响主流程
                    suggestions_data = {
                        "type": "suggestions",
                        "suggested_questions": []
                    }
                    yield f"data: {json.dumps(suggestions_data, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"❌ 流式查询失败: {e}", exc_info=True)
            error_data = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用Nginx缓冲
        }
    )

