# 架构优化实施指南

## 🚀 快速开始：渐进式优化

本文档提供具体的代码示例和实施步骤，帮助您逐步优化架构。

---

## 阶段一：异步化改造（最快见效）

### 1.1 安装依赖

```bash
pip install celery redis httpx aiohttp
```

### 1.2 创建异步任务队列

#### `services/celery_app.py`
```python
from celery import Celery
from config.settings import settings

celery_app = Celery(
    'rag_tasks',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0',
    backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5分钟超时
    worker_prefetch_multiplier=1,  # 防止任务堆积
)
```

#### `services/tasks/document_tasks.py`
```python
from services.celery_app import celery_app
from src.processors.pdf_processor import PDFProcessor
from src.services.embedding_service import get_embedding_service
from src.core.vector_store_manager import get_vector_store_manager
from src.utils.logger import logger

@celery_app.task(bind=True, max_retries=3)
def process_document_task(self, document_id: str, file_path: str):
    """异步处理文档上传"""
    try:
        logger.info(f"开始处理文档: {document_id}")
        
        # 1. PDF解析
        processor = PDFProcessor()
        chunks = processor.process(file_path)
        logger.info(f"文档解析完成，共 {len(chunks)} 个块")
        
        # 2. 向量化
        embedding_service = get_embedding_service()
        vectors = []
        texts = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            vector = embedding_service.embed_text(chunk.text)
            vectors.append(vector)
            texts.append(chunk.text)
            metadatas.append({
                "document_id": document_id,
                "chunk_index": i,
                **chunk.metadata
            })
        
        logger.info(f"向量化完成，共 {len(vectors)} 个向量")
        
        # 3. 存储向量
        vector_store = get_vector_store_manager().get_store()
        ids = [f"{document_id}_chunk_{i}" for i in range(len(vectors))]
        success = vector_store.insert_vectors(
            vectors=vectors,
            texts=texts,
            metadatas=metadatas,
            ids=ids
        )
        
        if success:
            logger.info(f"文档处理完成: {document_id}")
            return {"status": "success", "chunks_count": len(chunks)}
        else:
            raise Exception("向量存储失败")
            
    except Exception as e:
        logger.error(f"文档处理失败: {e}", exc_info=True)
        # 重试
        raise self.retry(exc=e, countdown=60)
```

### 1.3 修改文档上传接口

#### `src/api/routes/document.py`（修改后）
```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.tasks.document_tasks import process_document_task
from src.utils.logger import logger

router = APIRouter()

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """上传文档（异步处理）"""
    import uuid
    import os
    from pathlib import Path
    
    # 保存文件
    document_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    file_path = Path(f"data/documents/{document_id}{file_extension}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # 异步处理
    task = process_document_task.delay(document_id, str(file_path))
    
    return {
        "document_id": document_id,
        "status": "processing",
        "task_id": task.id,
        "message": "文档已上传，正在处理中"
    }

@router.get("/upload/status/{task_id}")
async def get_upload_status(task_id: str):
    """查询文档处理状态"""
    from services.celery_app import celery_app
    
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {'status': 'pending', 'progress': 0}
    elif task.state == 'PROGRESS':
        response = {
            'status': 'processing',
            'progress': task.info.get('progress', 0)
        }
    elif task.state == 'SUCCESS':
        response = {
            'status': 'completed',
            'result': task.result
        }
    else:
        response = {
            'status': 'failed',
            'error': str(task.info)
        }
    
    return response
```

### 1.4 启动Celery Worker

```bash
# 启动worker
celery -A services.celery_app worker --loglevel=info --concurrency=4

# 启动flower（监控界面）
celery -A services.celery_app flower --port=5555
```

---

## 阶段二：拆分Embedding服务

### 2.1 创建独立的Embedding服务

#### `services/embedding/main.py`
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import numpy as np
from src.services.embedding_service import get_embedding_service

app = FastAPI(title="Embedding Service")

class EmbedRequest(BaseModel):
    text: str

class EmbedBatchRequest(BaseModel):
    texts: List[str]
    batch_size: int = 32

class EmbedResponse(BaseModel):
    vector: List[float]
    dimension: int

class EmbedBatchResponse(BaseModel):
    vectors: List[List[float]]
    count: int

@app.post("/embed", response_model=EmbedResponse)
async def embed_text(request: EmbedRequest):
    """单个文本向量化"""
    try:
        embedding_service = get_embedding_service()
        vector = embedding_service.embed_text(request.text)
        
        return EmbedResponse(
            vector=vector.tolist(),
            dimension=len(vector)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/embed/batch", response_model=EmbedBatchResponse)
async def embed_batch(request: EmbedBatchRequest):
    """批量文本向量化"""
    try:
        embedding_service = get_embedding_service()
        vectors = embedding_service.embed_batch(
            request.texts,
            batch_size=request.batch_size
        )
        
        return EmbedBatchResponse(
            vectors=[v.tolist() for v in vectors],
            count=len(vectors)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
```

### 2.2 创建Embedding服务客户端

#### `src/clients/embedding_client.py`
```python
import httpx
from typing import List
import numpy as np
from config.settings import settings
from src.utils.logger import logger

class EmbeddingClient:
    """Embedding服务客户端"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or getattr(
            settings, 'EMBEDDING_SERVICE_URL', 'http://localhost:8003'
        )
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
    
    async def embed_text(self, text: str) -> np.ndarray:
        """向量化单个文本"""
        try:
            response = await self.client.post(
                "/embed",
                json={"text": text}
            )
            response.raise_for_status()
            data = response.json()
            return np.array(data["vector"])
        except Exception as e:
            logger.error(f"Embedding服务调用失败: {e}")
            raise
    
    async def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """批量向量化"""
        try:
            response = await self.client.post(
                "/embed/batch",
                json={"texts": texts, "batch_size": batch_size}
            )
            response.raise_for_status()
            data = response.json()
            return [np.array(v) for v in data["vectors"]]
        except Exception as e:
            logger.error(f"Embedding批量服务调用失败: {e}")
            raise
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()

# 全局客户端实例
_embedding_client = None

def get_embedding_client() -> EmbeddingClient:
    """获取Embedding客户端（单例）"""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client
```

### 2.3 修改原有代码使用客户端

#### `src/services/embedding_service.py`（修改）
```python
# 添加远程调用支持
async def embed_text_remote(text: str) -> np.ndarray:
    """使用远程Embedding服务"""
    from src.clients.embedding_client import get_embedding_client
    client = get_embedding_client()
    return await client.embed_text(text)
```

---

## 阶段三：拆分LLM服务

### 3.1 创建独立的LLM服务

#### `services/llm/main.py`
```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from src.services.llm_service import get_llm_service
import json

app = FastAPI(title="LLM Service")

class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7
    stream: bool = False

class GenerateResponse(BaseModel):
    text: str
    tokens_used: int

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """生成文本"""
    try:
        llm_service = get_llm_service()
        
        if request.stream:
            # 流式输出
            async def stream_generator():
                async for chunk in llm_service.generate_stream(
                    request.prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                ):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream"
            )
        else:
            # 非流式
            result = await llm_service.generate_async(
                request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            return GenerateResponse(
                text=result["text"],
                tokens_used=result.get("tokens_used", 0)
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
```

---

## 阶段四：Docker化

### 4.1 创建Dockerfile

#### `Dockerfile.api`
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### `Dockerfile.embedding`
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8003

# 启动命令
CMD ["python", "services/embedding/main.py"]
```

### 4.2 创建docker-compose.yml

```yaml
version: '3.8'

services:
  # Redis（消息队列）
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Qdrant（向量数据库）
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  # Embedding服务（3个实例）
  embedding-service-1:
    build:
      context: .
      dockerfile: Dockerfile.embedding
    ports:
      - "8003:8003"
    environment:
      - EMBEDDING_MODEL_PATH=/models/embedding
    volumes:
      - ./models/embedding:/models/embedding

  embedding-service-2:
    build:
      context: .
      dockerfile: Dockerfile.embedding
    ports:
      - "8004:8003"
    environment:
      - EMBEDDING_MODEL_PATH=/models/embedding
    volumes:
      - ./models/embedding:/models/embedding

  embedding-service-3:
    build:
      context: .
      dockerfile: Dockerfile.embedding
    ports:
      - "8005:8003"
    environment:
      - EMBEDDING_MODEL_PATH=/models/embedding
    volumes:
      - ./models/embedding:/models/embedding

  # API服务
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
      - EMBEDDING_SERVICE_URL=http://embedding-service-1:8003
    depends_on:
      - redis
      - qdrant
      - embedding-service-1

  # Nginx（负载均衡）
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - embedding-service-1
      - embedding-service-2
      - embedding-service-3

volumes:
  redis_data:
  qdrant_data:
```

### 4.3 Nginx配置

#### `nginx.conf`
```nginx
upstream embedding_service {
    least_conn;
    server embedding-service-1:8003;
    server embedding-service-2:8003;
    server embedding-service-3:8003;
}

server {
    listen 80;
    
    location /api/v1/embedding/ {
        proxy_pass http://embedding_service;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/v1/ {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 阶段五：监控集成

### 5.1 添加Prometheus指标

#### `src/utils/metrics.py`
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# 请求计数
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# 响应时间
request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

# 活跃连接数
active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

# 向量化请求数
embedding_requests = Counter(
    'embedding_requests_total',
    'Total embedding requests',
    ['status']
)

# LLM请求数
llm_requests = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['status']
)
```

#### `src/api/main.py`（添加中间件）
```python
from src.utils.metrics import request_count, request_duration
import time

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    # 记录指标
    duration = time.time() - start_time
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response

@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    from src.utils.metrics import generate_latest
    return Response(content=generate_latest(), media_type="text/plain")
```

---

## 📊 性能测试

### 使用Locust进行压力测试

#### `tests/load_test.py`
```python
from locust import HttpUser, task, between

class RAGUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def query(self):
        """查询任务"""
        self.client.post(
            "/api/v1/query",
            json={"query": "测试问题"}
        )
    
    @task(1)
    def upload(self):
        """上传任务"""
        with open("test.pdf", "rb") as f:
            self.client.post(
                "/api/v1/documents/upload",
                files={"file": f}
            )
```

运行测试：
```bash
locust -f tests/load_test.py --host=http://localhost:8000
```

---

## 🎯 实施检查清单

### 阶段一：异步化
- [ ] 安装Celery和Redis
- [ ] 创建异步任务
- [ ] 修改上传接口
- [ ] 启动Celery Worker
- [ ] 测试异步处理

### 阶段二：服务拆分
- [ ] 创建Embedding服务
- [ ] 创建Embedding客户端
- [ ] 修改代码使用客户端
- [ ] 测试服务调用

### 阶段三：容器化
- [ ] 创建Dockerfile
- [ ] 创建docker-compose.yml
- [ ] 配置Nginx负载均衡
- [ ] 测试容器部署

### 阶段四：监控
- [ ] 集成Prometheus
- [ ] 配置Grafana
- [ ] 添加告警规则
- [ ] 测试监控系统

---

## 📚 下一步

1. **选择实施阶段**：根据实际情况选择从哪个阶段开始
2. **准备环境**：安装必要的依赖和服务
3. **逐步实施**：按照检查清单逐步完成
4. **测试验证**：每个阶段完成后进行测试
5. **监控优化**：持续监控和优化性能

---

*最后更新时间：2026-01-02*

