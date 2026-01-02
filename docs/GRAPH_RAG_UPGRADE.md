# GraphRAG 升级方案

## 📋 概述

当前系统是基于向量相似度搜索的传统RAG系统。GraphRAG升级将引入知识图谱，实现更强大的多跳推理、实体关系查询和结构化知识管理。

---

## 🎯 GraphRAG vs 传统RAG

### 传统RAG的局限性
- ❌ 只能基于文本相似度检索，无法理解实体关系
- ❌ 难以回答需要多跳推理的问题（如"A公司的CEO是谁？" → "CEO的薪资是多少？"）
- ❌ 无法进行关系查询（如"哪些公司与X公司有合作关系？"）
- ❌ 缺乏结构化知识管理

### GraphRAG的优势
- ✅ 实体-关系-实体三元组结构，支持关系查询
- ✅ 多跳推理能力（通过图遍历）
- ✅ 结合向量搜索和图搜索的混合检索
- ✅ 结构化知识表示，便于知识管理
- ✅ 支持复杂查询（如"找出所有与X公司有合作关系的Y行业公司"）

---

## 🏗️ 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      API层                               │
│              FastAPI RESTful API                         │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                   业务逻辑层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ 文档处理服务  │  │ 知识抽取服务  │  │ 混合检索服务  │ │
│  │              │→ │              │→ │              │ │
│  │ PDF/TXT解析  │  │ 实体关系抽取  │  │ 向量+图检索   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                          │                              │
│  ┌──────────────────────────────────────────────┐      │
│  │          GraphRAG生成服务                      │      │
│  │  结合图遍历结果和向量检索结果生成答案            │      │
│  └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                   数据存储层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  向量数据库   │  │   图数据库    │  │   元数据存储   │ │
│  │              │  │              │  │              │ │
│  │ Qdrant/FAISS │  │  Neo4j/Arango│  │   SQLite/JSON │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────────┐
│                   模型服务层                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Embedding模型 │  │   NER模型     │  │   RE模型      │ │
│  │              │  │              │  │              │ │
│  │ 文本向量化    │  │  实体识别     │  │  关系抽取     │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                          │                              │
│  ┌──────────────────────────────────────────────┐      │
│  │              LLM模型（Ollama/Qwen）            │      │
│  │        用于关系抽取、答案生成、问题生成          │      │
│  └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 技术选型

### 1. 知识抽取
- **方案1（推荐）**：使用LLM进行实体关系抽取
  - 优点：准确率高，可定制化
  - 缺点：速度较慢，成本较高
  - 实现：使用Ollama本地模型（如Qwen2）进行抽取

- **方案2**：使用预训练NER/RE模型
  - 选项：`spacy` + `spacy-zh` / `HanLP` / `LTP`
  - 优点：速度快，离线可用
  - 缺点：准确率可能不如LLM

- **方案3（混合）**：LLM + 规则抽取
  - 使用规则提取简单关系，LLM处理复杂关系
  - 平衡速度和准确率

### 2. 图数据库
- **Neo4j**（推荐）
  - 优点：成熟稳定，Cypher查询语言强大，社区活跃
  - 缺点：需要Java环境，资源占用较大
  - 部署：Docker容器

- **ArangoDB**
  - 优点：支持图+文档+键值，轻量级
  - 缺点：社区相对较小

- **NebulaGraph**
  - 优点：国产，性能优秀，分布式支持
  - 缺点：学习曲线较陡

- **轻量级方案**：使用NetworkX + SQLite
  - 适合小规模数据，无需额外服务

### 3. 混合检索策略
- **向量检索**：基于文本语义相似度
- **图检索**：基于实体关系遍历
- **融合策略**：
  1. 分别检索，合并去重
  2. 向量检索 → 提取实体 → 图遍历扩展
  3. 图检索 → 获取相关文本 → 向量检索验证

---

## 📁 目录结构扩展

```
china-pdf-rag/
├── src/
│   ├── core/
│   │   ├── graph_store.py          # 图数据库抽象层（新增）
│   │   ├── neo4j_store.py          # Neo4j实现（新增）
│   │   ├── networkx_store.py       # NetworkX轻量级实现（新增）
│   │   └── hybrid_retriever.py    # 混合检索器（新增）
│   ├── processors/
│   │   ├── knowledge_extractor.py  # 知识抽取器（新增）
│   │   └── entity_linker.py       # 实体链接器（新增）
│   ├── services/
│   │   ├── ner_service.py         # 命名实体识别服务（新增）
│   │   ├── re_service.py          # 关系抽取服务（新增）
│   │   ├── graph_rag_service.py   # GraphRAG生成服务（新增）
│   │   └── generation_service.py  # 保留原有服务（兼容）
│   └── utils/
│       └── graph_utils.py         # 图工具函数（新增）
├── data/
│   ├── graphs/                    # 图数据库存储（新增）
│   └── entities/                  # 实体缓存（新增）
└── scripts/
    ├── init_graph.py              # 初始化图数据库（新增）
    └── migrate_to_graph.py       # 迁移脚本（新增）
```

---

## 🚀 实施计划

### 阶段一：知识抽取模块（1-2周）

#### 1.1 实体识别（NER）
- [ ] 实现基于LLM的实体识别服务
- [ ] 支持实体类型：人物、组织、地点、时间、金额、职位等
- [ ] 实体去重和规范化

#### 1.2 关系抽取（RE）
- [ ] 实现基于LLM的关系抽取服务
- [ ] 定义关系类型：雇佣、合作、投资、管理、拥有等
- [ ] 关系置信度评分

#### 1.3 实体链接
- [ ] 实体消歧（同一实体的不同表述）
- [ ] 实体规范化（统一实体名称）

**实现示例：**
```python
# src/services/ner_service.py
class NERService:
    def extract_entities(self, text: str) -> List[Entity]:
        """使用LLM提取实体"""
        prompt = f"""
        从以下文本中提取实体，返回JSON格式：
        {text}
        
        实体类型：人物、组织、地点、时间、金额、职位
        """
        # 调用LLM
        # 解析返回的实体列表
        pass

# src/services/re_service.py
class REService:
    def extract_relations(self, text: str, entities: List[Entity]) -> List[Relation]:
        """提取实体间的关系"""
        prompt = f"""
        从文本中提取实体间的关系：
        文本：{text}
        实体：{entities}
        
        关系类型：雇佣、合作、投资、管理、拥有
        """
        # 调用LLM
        # 返回三元组 (实体1, 关系, 实体2)
        pass
```

---

### 阶段二：图数据库集成（1周）

#### 2.1 图数据库抽象层
- [ ] 定义`GraphStore`接口
- [ ] 实现Neo4j存储
- [ ] 实现NetworkX轻量级存储（可选）

#### 2.2 图数据模型
- [ ] 节点（Node）：实体
  - 属性：名称、类型、描述、向量嵌入
- [ ] 边（Edge）：关系
  - 属性：关系类型、置信度、来源文档

**实现示例：**
```python
# src/core/graph_store.py
class BaseGraphStore:
    def add_entity(self, entity: Entity) -> bool:
        """添加实体节点"""
        pass
    
    def add_relation(self, relation: Relation) -> bool:
        """添加关系边"""
        pass
    
    def query_by_entity(self, entity_name: str) -> List[Dict]:
        """根据实体查询相关节点和关系"""
        pass
    
    def traverse(self, start_entity: str, relation_type: str, depth: int) -> List[Dict]:
        """图遍历查询"""
        pass

# src/core/neo4j_store.py
class Neo4jStore(BaseGraphStore):
    def __init__(self, uri: str, user: str, password: str):
        from neo4j import GraphDatabase
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def add_entity(self, entity: Entity):
        with self.driver.session() as session:
            session.run(
                "MERGE (e:Entity {name: $name}) SET e.type = $type, e.description = $desc",
                name=entity.name, type=entity.type, desc=entity.description
            )
    
    def traverse(self, start_entity: str, relation_type: str, depth: int):
        query = f"""
        MATCH path = (start:Entity {{name: $name}})-[:{relation_type}*1..{depth}]-(connected)
        RETURN path
        """
        # 执行查询并返回结果
        pass
```

---

### 阶段三：混合检索（1周）

#### 3.1 混合检索器
- [ ] 实现向量检索 + 图检索的融合
- [ ] 支持多种融合策略
- [ ] 结果排序和去重

**实现示例：**
```python
# src/core/hybrid_retriever.py
class HybridRetriever:
    def __init__(self, vector_store, graph_store):
        self.vector_store = vector_store
        self.graph_store = graph_store
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """混合检索"""
        # 1. 向量检索
        vector_results = self.vector_store.search(query, top_k=top_k)
        
        # 2. 从查询中提取实体
        entities = self.extract_entities_from_query(query)
        
        # 3. 图检索
        graph_results = []
        for entity in entities:
            related = self.graph_store.query_by_entity(entity)
            graph_results.extend(related)
        
        # 4. 融合结果
        merged = self.merge_results(vector_results, graph_results)
        
        # 5. 去重和排序
        return self.deduplicate_and_rank(merged, top_k)
```

---

### 阶段四：GraphRAG生成服务（1周）

#### 4.1 GraphRAG服务
- [ ] 实现基于图检索的答案生成
- [ ] 支持多跳推理
- [ ] 结合向量检索和图检索结果

**实现示例：**
```python
# src/services/graph_rag_service.py
class GraphRAGService:
    def generate_answer(self, query: str) -> str:
        """基于GraphRAG生成答案"""
        # 1. 混合检索
        context = self.hybrid_retriever.retrieve(query)
        
        # 2. 提取查询中的实体
        query_entities = self.ner_service.extract_entities(query)
        
        # 3. 图遍历扩展上下文
        if query_entities:
            for entity in query_entities:
                related = self.graph_store.traverse(
                    entity.name, 
                    relation_type=None,  # 所有关系类型
                    depth=2  # 2跳
                )
                context.extend(related)
        
        # 4. 构建提示词
        prompt = self.build_prompt(query, context)
        
        # 5. 调用LLM生成答案
        answer = self.llm_service.generate(prompt)
        
        return answer
```

---

### 阶段五：API扩展（3-5天）

#### 5.1 新增API端点
- [ ] `GET /api/v1/graph/entities` - 查询实体
- [ ] `GET /api/v1/graph/relations` - 查询关系
- [ ] `POST /api/v1/graph/traverse` - 图遍历查询
- [ ] `POST /api/v1/query` - 升级为支持GraphRAG

#### 5.2 文档上传流程升级
- [ ] 文档上传时自动进行知识抽取
- [ ] 将实体和关系写入图数据库
- [ ] 保留原有向量存储流程

---

### 阶段六：测试与优化（1周）

- [ ] 单元测试：知识抽取、图操作、混合检索
- [ ] 集成测试：端到端GraphRAG流程
- [ ] 性能优化：批量抽取、异步处理
- [ ] 准确性评估：对比传统RAG和GraphRAG

---

## 📊 数据流程

### 文档处理流程（升级后）

```
上传文档
  ↓
PDF解析 → 文本提取
  ↓
文本分块
  ↓
┌─────────────────┬─────────────────┐
│                 │                 │
向量化           知识抽取
  ↓                 ↓
向量存储         实体+关系
(Qdrant/FAISS)      ↓
                图存储
                (Neo4j)
```

### 查询流程（升级后）

```
用户查询
  ↓
┌─────────────────┬─────────────────┐
│                 │                 │
向量检索         实体识别
  ↓                 ↓
相似文档块        图遍历
  ↓                 ↓
┌─────────────────────────────────┐
│        混合检索结果融合            │
└─────────────────────────────────┘
  ↓
上下文构建
  ↓
LLM生成答案
  ↓
返回结果
```

---

## 🔐 环境变量配置（新增）

```bash
# 图数据库配置
GRAPH_DB_TYPE=neo4j  # neo4j, networkx
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# 知识抽取配置
USE_LLM_EXTRACTION=true  # 使用LLM进行抽取
NER_MODEL=local  # local 或 api
RE_MODEL=local

# 混合检索配置
HYBRID_RETRIEVAL=true  # 启用混合检索
VECTOR_WEIGHT=0.6  # 向量检索权重
GRAPH_WEIGHT=0.4  # 图检索权重
MAX_TRAVERSE_DEPTH=2  # 最大图遍历深度
```

---

## 📈 预期效果

### 能力提升
1. **多跳推理**：能够回答需要多步推理的问题
   - 传统RAG：❌ "A公司的CEO的薪资是多少？"
   - GraphRAG：✅ 先找到A公司，再找到CEO，最后找到薪资信息

2. **关系查询**：支持基于关系的查询
   - 传统RAG：❌ "哪些公司与X公司有合作关系？"
   - GraphRAG：✅ 直接在图数据库中查询关系

3. **结构化知识**：知识以结构化方式存储和管理
   - 便于知识更新、验证和可视化

### 性能考虑
- **抽取阶段**：增加处理时间（LLM抽取需要时间）
- **查询阶段**：可能更快（图查询通常比向量搜索快）
- **存储空间**：需要额外存储图数据

---

## 🎯 实施优先级

### 高优先级（核心功能）
1. ✅ 知识抽取模块（NER + RE）
2. ✅ 图数据库集成（Neo4j）
3. ✅ 混合检索器
4. ✅ GraphRAG生成服务

### 中优先级（优化功能）
1. 实体链接和消歧
2. 关系置信度评分
3. 图可视化接口
4. 批量抽取优化

### 低优先级（扩展功能）
1. 知识图谱自动更新
2. 多语言实体识别
3. 图数据库迁移工具
4. 知识图谱可视化界面

---

## 🚨 注意事项

1. **向后兼容**：保留原有RAG功能，GraphRAG作为增强功能
2. **性能平衡**：知识抽取会增加处理时间，需要优化
3. **数据一致性**：确保向量存储和图存储的数据一致
4. **错误处理**：图数据库连接失败时的降级方案
5. **资源占用**：Neo4j需要额外资源，考虑轻量级方案

---

## 📚 参考资料

- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [GraphRAG论文](https://arxiv.org/abs/2404.16130)
- [LangChain GraphRAG](https://python.langchain.com/docs/use_cases/graph/)
- [知识图谱构建实践](https://github.com/ownthink/KnowledgeGraph)

---

## ✅ 下一步行动

1. **评估需求**：确定是否需要GraphRAG的复杂查询能力
2. **选择方案**：确定图数据库和抽取方案
3. **原型开发**：先实现最小可行版本（MVP）
4. **逐步迭代**：按照阶段计划逐步实施

---

*最后更新时间：2026-01-01*

