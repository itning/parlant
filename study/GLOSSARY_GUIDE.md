# Parlant Glossary/Term 深度讲解

## Glossary/Term 是什么？

**Glossary（词汇表）/ Term（术语）** 是 Parlant 中用于确保 **AI Agent 使用准确、一致的业务术语** 的核心机制。

它解决了一个关键的企业 AI 问题：**语义一致性和术语准确性**。

## 简单类比

想象你在训练一个区块链客服：

```
没有 Glossary：
客户："Gas 费用是什么？"
AI：Gas 是一种气体，用于... （错误！使用了通用定义）

有 Glossary：
Term: "Gas"
Description: "以太坊中衡量执行交易或智能合约所需计算工作的单位"
Synonyms: ["交易费用", "区块链燃料"]

客户："Gas 费用是什么？"
AI：Gas 是以太坊中衡量执行交易所需计算工作的单位，
    它决定了您需要支付的交易费用。（正确！使用了业务定义）
```

## Term 的核心结构

### 数据模型

```python
@dataclass(frozen=True)
class Term:
    id: TermId                    # 唯一ID
    creation_utc: datetime        # 创建时间
    name: str                     # 术语名称
    description: str              # 详细定义
    synonyms: list[str]           # 同义词列表
    tags: list[TagId]             # 标签（用于分组和过滤）

    def __repr__(self) -> str:
        term_string = f"Name: '{self.name}', Description: {self.description}"
        if self.synonyms:
            term_string += f", Synonyms: {', '.join(self.synonyms)}"
        return term_string
```

**代码位置**: `src/parlant/core/glossary.py:46-66`

### 字段说明

| 字段 | 类型 | 说明 | 例子 |
|------|------|------|------|
| `id` | TermId | 唯一标识符，自动生成或自定义 | "term_gas001" |
| `name` | str | 术语名称（1-100字符） | "Gas" |
| `description` | str | 详细的业务定义 | "以太坊中衡量计算工作的单位" |
| `synonyms` | list[str] | 同义词和变体 | ["交易费用", "区块链燃料"] |
| `tags` | list[TagId] | 范围标签（agent 专用、全局等） | ["agent-eth01"] |
| `creation_utc` | datetime | 创建时间（UTC） | "2024-01-01T00:00:00Z" |

## 为什么需要 Glossary？

### 解决的核心问题

#### 1. **术语歧义**

同一个词在不同场景下有不同含义：

```python
# 区块链 Agent
token_blockchain = await agent_crypto.create_term(
    name="Token",
    description="区块链上代表价值的数字资产",
    synonyms=["加密货币", "数字货币"]
)

# NLP Agent（完全不同的含义）
token_nlp = await agent_nlp.create_term(
    name="Token",
    description="NLP 中的单个词或字符序列",
    synonyms=["词单元", "文本片段"]
)
```

#### 2. **LLM 幻觉问题**

LLM 可能使用训练数据中的通用定义，而不是你的业务定义：

```
❌ 没有 Glossary：
客户："什么是 Premium？"
AI："Premium 通常指高级版本或优质产品..."
（使用了通用定义，可能不准确）

✅ 有 Glossary：
Term: "Premium"
Description: "我们公司的 Premium 计划包括：无限存储、
             优先客服、高级分析功能，月费 ¥299"

客户："什么是 Premium？"
AI："Premium 是我们的高级订阅计划，包括无限存储、
     优先客服和高级分析功能，月费 ¥299。"
（使用了精确的业务定义）
```

#### 3. **合规性要求**

金融、医疗等行业对术语使用有严格要求：

```python
# 金融行业
financial_term = await agent.create_term(
    name="APR",
    description="年化利率（Annual Percentage Rate）：包含利息和
                 所有费用的年化借款成本，按照监管要求计算",
    synonyms=["年利率", "综合利率"]
)
# 确保每次提到 APR 时都使用监管合规的定义
```

#### 4. **拼写错误容错**

Glossary 让 AI 能识别并纠正客户的拼写错误：

```
客户："Gass 费用多少？"（拼写错误）
AI：根据 Glossary 中的 "Gas" 术语，识别出客户可能是想问 "Gas"
AI："我理解您是在询问 Gas 费用。Gas 是以太坊中..."
```

## 创建和管理 Terms

### 基本创建

```python
# 通过 SDK 创建
agent = await server.create_agent(name="区块链专家")

term = await agent.create_term(
    name="Gas",
    description="以太坊中衡量执行交易或智能合约所需计算工作的单位",
    synonyms=["交易费用", "区块链燃料"]
)
```

### 完整创建（所有参数）

```python
term = await glossary_store.create_term(
    name="Smart Contract",
    description="存储在区块链上的自动执行代码，无需中介即可执行协议条款",
    synonyms=["智能合约", "自动化合约"],
    tags=["agent-eth01", "blockchain"],  # 范围标签
    id=TermId("term_smart_contract"),   # 自定义 ID（可选）
    creation_utc=datetime.now(timezone.utc)
)
```

### CRUD 操作

```python
# 读取 Term
term = await glossary_store.read_term(term_id)

# 更新 Term
updated_term = await glossary_store.update_term(
    term_id=term_id,
    params={
        "description": "更新后的定义",
        "synonyms": ["新同义词1", "新同义词2"]
    }
)

# 列出所有 Terms
all_terms = await glossary_store.list_terms()

# 按标签过滤
agent_terms = await glossary_store.list_terms(
    tags=[Tag.for_agent_id(agent_id)]
)

# 删除 Term
await glossary_store.delete_term(term_id)
```

**代码位置**: `src/parlant/core/glossary.py:74-133`

### 标签管理

```python
# 添加标签
await glossary_store.upsert_tag(
    term_id=term.id,
    tag_id=Tag.for_agent_id(agent_id)
)

# 移除标签
await glossary_store.remove_tag(
    term_id=term.id,
    tag_id=tag_id
)
```

## Term 的范围（Scope）

### 三种范围类型

#### 1. **全局 Terms**（所有 Agent 可用）

```python
# tags=[] 表示全局
global_term = await glossary_store.create_term(
    name="API",
    description="应用程序编程接口",
    synonyms=["Application Programming Interface"],
    tags=[]  # 空标签 = 全局
)
```

#### 2. **Agent 专用 Terms**

```python
# 只有特定 agent 可以访问
agent_specific = await agent.create_term(
    name="Gas",
    description="以太坊特定的计算费用单位",
    synonyms=["交易费用"]
    # SDK 自动添加 Tag.for_agent_id(agent.id)
)
```

#### 3. **自定义标签 Terms**

```python
# 使用自定义标签分组
regional_term = await glossary_store.create_term(
    name="GST",
    description="商品及服务税（澳大利亚）",
    tags=["region-australia", "tax"]
)
```

### 范围层次结构

```
┌─────────────────────────────────┐
│   全局 Terms (tags=[])           │  所有 Agent 可用
├─────────────────────────────────┤
│   Agent 专用 Terms               │  只有特定 Agent 可用
│   (tags=[agent-id:xyz])          │
├─────────────────────────────────┤
│   自定义标签 Terms               │  自定义分组
│   (tags=[custom-tag-1, ...])     │
└─────────────────────────────────┘
         ↓ 语义搜索 ↓
    返回最相关的 K 个 Terms
```

**代码位置**: `src/parlant/core/entity_cq.py:286-302`

## 向量嵌入与语义匹配

### 核心机制

Glossary 使用 **向量嵌入（Vector Embeddings）** 进行智能的语义匹配。

#### 1. **内容组装**

Term 的各个部分会被组装成一个字符串用于嵌入：

```python
def _assemble_term_content(
    self,
    name: str,
    description: str,
    synonyms: Optional[Sequence[str]],
) -> str:
    content = f"{name}"
    if synonyms:
        content += f", {', '.join(synonyms)}"
    content += f": {description}"
    return content

# 例子：
# "Gas, 交易费用, 区块链燃料: 以太坊中衡量执行交易所需计算工作的单位"
```

#### 2. **向量化存储**

```python
# 初始化时创建向量集合
self._collection = await self._vector_db.get_or_create_collection(
    name="glossary",
    schema=_TermDocument,
    embedder_type=embedder_type,  # 如 OpenAI, Cohere 等
    document_loader=self._document_loader,
)

# 创建 Term 时自动嵌入
await self._collection.insert_one(
    document=self._serialize(term, content, checksum)
)
```

**代码位置**: `src/parlant/core/glossary.py:169-227`

#### 3. **语义搜索流程**

```
1. 构建查询上下文
   ↓
2. 将查询文本转换为向量
   ↓
3. 在向量数据库中搜索相似向量
   ↓
4. 按相似度排序
   ↓
5. 返回前 K 个最相关的 Terms
```

### 查询上下文构建

引擎会从多个来源构建查询：

```python
async def _load_glossary_terms(self, context: EngineContext) -> Sequence[Term]:
    query = ""

    # 1. 上下文变量（客户信息、偏好等）
    if context.state.context_variables:
        query += f"\n{context_variables_to_json(context.state.context_variables)}"

    # 2. 对话历史（客户消息）
    if context.interaction.events:
        query += str([e.data for e in context.interaction.events])

    # 3. 匹配的 Guidelines（相关的行为）
    if context.state.guidelines:
        query += str([
            f"When {g.content.condition}, then {g.content.action}"
            for g in context.state.guidelines
        ])

    # 4. 工具执行结果（新出现的数据）
    if context.state.tool_events:
        query += str([e.data for e in context.state.tool_events])

    # 执行语义搜索
    if query:
        return await self._entity_queries.find_glossary_terms_for_context(
            agent_id=context.agent.id,
            query=query,
        )

    return []
```

**代码位置**: `src/parlant/core/engines/alpha/engine.py:1718-1751`

### 语义相似度搜索

```python
async def find_relevant_terms(
    self,
    query: str,
    available_terms: Sequence[Term],
    max_terms: int = 20,
) -> Sequence[Term]:
    if not available_terms:
        return []

    # 如果可用 terms 少于需要的数量，直接返回全部
    if max_terms >= len(available_terms):
        return available_terms

    # 将查询分块（适应 embedder 的 token 限制）
    queries = await query_chunks(query, self._embedder)

    # 过滤到可用的 terms
    filters: Where = {"id": {"$in": [str(t.id) for t in available_terms]}}

    # 对每个查询块执行语义搜索
    tasks = [
        self._collection.find_similar_documents(
            filters=filters,
            query=q,
            k=max_terms,
            hints={"tag": "glossary_terms"}
        )
        for q in queries
    ]

    # 合并所有结果
    all_results = chain.from_iterable(await async_utils.safe_gather(*tasks))

    # 去重并按相似度排序
    unique_results = list(set(all_results))
    top_results = sorted(unique_results, key=lambda r: r.distance)[:max_terms]

    # 反序列化并返回
    return [await self._deserialize(r.document) for r in top_results]
```

**代码位置**: `src/parlant/core/glossary.py:454-482`

### Token 分块机制

为了处理长查询，系统会自动分块：

```python
async def query_chunks(query: str, embedder: Embedder) -> list[str]:
    max_length = embedder.max_tokens // 5  # 安全边界
    total_token_count = await embedder.tokenizer.estimate_token_count(query)

    words = query.split()
    total_word_count = len(words)

    tokens_per_word = total_token_count / total_word_count
    words_per_chunk = max(int(max_length / tokens_per_word), 1)

    chunks = []
    for i in range(0, total_word_count, words_per_chunk):
        chunk_words = words[i : i + words_per_chunk]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)

    return chunks
```

**代码位置**: `src/parlant/core/persistence/vector_database_helper.py:24-41`

## Terms 在引擎中的使用

### 加载时机

Terms 在响应生成过程中的多个阶段被加载：

```
1. 初始加载（确定交互上下文后）
   ↓
2. 工具执行后重新加载（工具结果可能引用新术语）
   ↓
3. Guideline 解析后重新加载（新 guidelines 可能引用新术语）
   ↓
4. 消息生成前最终加载（最后检查术语上下文）
```

**代码位置**:
- 初始加载: `src/parlant/core/engines/alpha/engine.py:468`
- 工具执行后: `src/parlant/core/engines/alpha/engine.py:631`
- Guideline 解析后: `src/parlant/core/engines/alpha/engine.py:717`
- 消息生成前: `src/parlant/core/engines/alpha/engine.py:763`

### 在 Prompt 中的呈现

Terms 会被添加到 Agent 的 prompt 中：

```python
def add_glossary(
    self,
    terms: Sequence[Term],
) -> PromptBuilder:
    if terms:
        # 格式化术语
        terms_string = "\n".join(
            f"{i}) {repr(t)}"
            for i, t in enumerate(terms, start=1)
        )

        self.add_section(
            name=BuiltInSection.GLOSSARY,
            template="""
The following is a glossary of the business.
Understanding these terms, as they apply to the business, is critical for your task.
When encountering any of these terms, prioritize the interpretation provided here
over any definitions you may already know.
Please be tolerant of possible typos by the user with regards to these terms,
and let the user know if/when you assume they meant a term by their typo: ###
{terms_string}
###
""",
            props={"terms_string": terms_string},
            status=SectionStatus.ACTIVE,
        )

    return self
```

**代码位置**: `src/parlant/core/engines/alpha/prompt_builder.py:403-425`

### Prompt 示例

```
================================
你是一个 AI 助手，名字是...

...

以下是业务词汇表。
理解这些术语在业务中的含义对于你的任务至关重要。
当遇到这些术语时，请优先使用此处提供的定义，而不是你已知的任何定义。
请容忍用户在这些术语上可能出现的拼写错误，并在你认为他们打错字时告知用户：###

1) Name: 'Gas', Description: 以太坊中衡量执行交易或智能合约所需计算工作的单位,
   Synonyms: 交易费用, 区块链燃料
2) Name: 'Token', Description: 区块链上代表价值的数字资产,
   Synonyms: 加密货币, 数字货币
3) Name: 'Smart Contract', Description: 存储在区块链上的自动执行代码...

###

...
================================
```

### 对 AI 行为的影响

1. **精确定义优先**：AI 使用 Glossary 中的定义，而不是训练数据中的通用定义
2. **拼写容错**：AI 会检测并纠正拼写错误
3. **同义词识别**：客户使用同义词时，AI 能正确理解
4. **上下文一致性**：确保整个对话中术语使用一致

## API 端点

### REST API

**文件位置**: `src/parlant/api/glossary.py`

#### 1. 创建 Term

```http
POST /terms

Request:
{
    "name": "Gas",
    "description": "以太坊中衡量计算工作的单位",
    "synonyms": ["交易费用", "区块链燃料"],
    "tags": ["agent-eth01"]
}

Response (201 Created):
{
    "id": "term_gas001",
    "name": "Gas",
    "description": "以太坊中衡量计算工作的单位",
    "synonyms": ["交易费用", "区块链燃料"],
    "tags": ["agent-eth01"]
}
```

#### 2. 读取 Term

```http
GET /terms/{term_id}

Response (200 OK):
{
    "id": "term_gas001",
    "name": "Gas",
    "description": "...",
    "synonyms": [...],
    "tags": [...]
}
```

#### 3. 列出 Terms

```http
# 列出所有 terms
GET /terms

# 按标签过滤
GET /terms?tag_id=agent-eth01

Response (200 OK):
[
    {
        "id": "term_gas001",
        "name": "Gas",
        ...
    },
    {
        "id": "term_token001",
        "name": "Token",
        ...
    }
]
```

#### 4. 更新 Term

```http
PATCH /terms/{term_id}

Request:
{
    "description": "更新后的定义",
    "synonyms": ["新同义词"],
    "tags": {
        "add": ["new-tag"],
        "remove": ["old-tag"]
    }
}

Response (200 OK):
{
    "id": "term_gas001",
    "name": "Gas",
    "description": "更新后的定义",
    ...
}
```

#### 5. 删除 Term

```http
DELETE /terms/{term_id}

Response (204 No Content)
```

## 与其他概念的关系

### Terms ↔ Guidelines

**关系**：
- Guidelines 可以在 condition 或 action 中引用术语
- Terms 为 Guidelines 提供定义上下文
- 没有显式链接，通过语义匹配关联

**例子**：
```python
# 创建术语
term = await agent.create_term(
    name="Premium",
    description="我们的高级订阅计划，包括无限存储和优先支持"
)

# 创建 guideline
guideline = await agent.create_guideline(
    condition="客户询问 Premium 计划",
    action="解释 Premium 计划的功能和价格"
)

# 当客户询问时：
客户："Premium 包括什么？"
→ Guideline 匹配
→ 加载 "Premium" 术语
→ AI 使用精确定义回复
AI："Premium 是我们的高级订阅计划，包括无限存储和优先支持..."
```

### Terms ↔ Journeys

**关系**：
- Journey 执行过程中会加载相关术语
- Journey 状态是查询上下文的一部分
- 可以为特定 Journey 创建专用术语

**例子**：
```python
# 创建 Journey 专用术语
journey_term = await glossary_store.create_term(
    name="KYC",
    description="客户身份验证流程，用于开户",
    tags=[Tag.for_journey_id(onboarding_journey.id)]
)

# Journey 执行时自动加载相关术语
```

### Terms ↔ Agents

**关系**：
- Terms 可以范围限定到特定 Agent
- Agents 可以访问全局术语和自己的专用术语
- Agent 的标签会影响可访问的术语

**作用域示例**：
```python
# Agent 专用术语
eth_agent = await server.create_agent(name="以太坊专家")
eth_term = await eth_agent.create_term(
    name="Gas",
    description="以太坊特定定义"
)  # 自动添加 Tag.for_agent_id(eth_agent.id)

# 全局术语（所有 Agent 可用）
global_term = await glossary_store.create_term(
    name="API",
    description="通用定义",
    tags=[]  # 空标签 = 全局
)
```

### Terms ↔ Canned Responses

**关系**：
- Canned Response 生成器在选择模板时会考虑术语
- Terms 帮助 AI 理解何时使用哪个模板
- 术语定义确保模板填充的准确性

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py`

### Terms ↔ Context Variables

**关系**：
- Context Variables 的值可能包含术语
- 术语加载时会考虑 Context Variables
- 两者共同提供完整的上下文

**例子**：
```python
# Context Variable
customer_tier = ContextVariable(
    name="customer_tier",
    value="premium"
)

# Term
premium_term = Term(
    name="Premium",
    description="..."
)

# 加载术语时，customer_tier 的值会被包含在查询中
# 如果客户是 premium，可能会优先加载 premium 相关术语
```

## 实际应用场景

### 1. 金融服务 Agent

```python
agent = await server.create_agent(name="金融顾问")

# 定义金融术语
terms = [
    await agent.create_term(
        name="APR",
        description="年化利率（Annual Percentage Rate）：包含利息和所有费用的年化借款成本",
        synonyms=["年利率", "综合利率"]
    ),
    await agent.create_term(
        name="Compound Interest",
        description="复利：在本金基础上累积的利息也计算利息",
        synonyms=["复利", "利滚利"]
    ),
    await agent.create_term(
        name="Credit Score",
        description="信用评分：700-850为优秀，640-700为良好，按照 FICO 标准",
        synonyms=["信用分", "征信分数"]
    )
]
```

**效果**：
```
客户："APR 是什么意思？"
AI："APR（年化利率）是包含利息和所有费用的年化借款成本，
     它能帮您全面了解贷款的实际成本。"
（使用精确的监管合规定义）
```

### 2. 区块链/加密货币 Agent

```python
agent = await server.create_agent(name="区块链专家")

terms = [
    await agent.create_term(
        name="Gas",
        description="以太坊中衡量执行交易或智能合约所需计算工作的单位，以 Gwei 计价",
        synonyms=["交易费用", "矿工费", "Gas Fee"]
    ),
    await agent.create_term(
        name="Smart Contract",
        description="存储在区块链上的自动执行代码，条件满足时无需中介即可执行",
        synonyms=["智能合约", "链上合约"]
    ),
    await agent.create_term(
        name="Staking",
        description="质押代币以支持网络运行并获得奖励的过程，年化收益率通常为 5-15%",
        synonyms=["质押", "Stake", "抵押"]
    )
]
```

**效果**：
```
客户："Gass 费太贵了"（拼写错误）
AI："我理解您是在说 Gas 费。Gas 是以太坊中衡量执行交易所需计算工作的单位。
     当前 Gas 价格确实较高，建议您在网络较空闲时交易以节省费用。"
（识别拼写错误并使用正确定义）
```

### 3. 电商 Agent

```python
agent = await server.create_agent(name="电商客服")

terms = [
    await agent.create_term(
        name="保修",
        description="我们提供 1 年免费保修，覆盖制造缺陷，不包括人为损坏",
        synonyms=["质保", "Warranty"]
    ),
    await agent.create_term(
        name="退货政策",
        description="30 天无理由退货，商品需保持原包装且未使用",
        synonyms=["退货", "Return Policy"]
    ),
    await agent.create_term(
        name="包邮",
        description="订单满 ¥99 包邮（偏远地区除外）",
        synonyms=["免运费", "Free Shipping"]
    )
]
```

### 4. 医疗/健康 Agent

```python
agent = await server.create_agent(name="健康助手")

terms = [
    await agent.create_term(
        name="BMI",
        description="身体质量指数（Body Mass Index）：体重(kg) / 身高(m)²，18.5-24 为正常范围",
        synonyms=["体质指数", "体重指数"]
    ),
    await agent.create_term(
        name="血压",
        description="正常血压范围：收缩压 90-120 mmHg，舒张压 60-80 mmHg",
        synonyms=["BP", "Blood Pressure"]
    ),
    await agent.create_term(
        name="处方药",
        description="需要医生处方才能购买的药品，我们不能在线销售处方药",
        synonyms=["Prescription Drug", "Rx"]
    )
]
```

### 5. SaaS 产品 Agent

```python
agent = await server.create_agent(name="SaaS 支持")

terms = [
    await agent.create_term(
        name="Webhook",
        description="我们的 Webhook 系统会在事件发生时向您的 URL 发送 HTTP POST 请求",
        synonyms=["Web Hook", "回调"]
    ),
    await agent.create_term(
        name="API Key",
        description="用于身份验证的密钥，格式：sk_live_xxx，请妥善保管",
        synonyms=["密钥", "API 令牌"]
    ),
    await agent.create_term(
        name="Rate Limit",
        description="API 速率限制：每分钟 100 请求（基础版），1000 请求（企业版）",
        synonyms=["限流", "调用限制"]
    )
]
```

## 存储架构

### 双存储系统

```
┌──────────────────────────────────────────────────────┐
│                 GlossaryVectorStore                   │
├──────────────────────────────────┬───────────────────┤
│   向量数据库 (Qdrant/Chroma)     │ 文档数据库        │
├──────────────────────────────────┼───────────────────┤
│ • _TermDocument                  │ • TagAssociation  │
│ • 向量嵌入                        │ • 标签链接        │
│ • find_similar_documents()       │ • 标签过滤        │
│ • 语义搜索                        │ • 元数据          │
└──────────────────────────────────┴───────────────────┘
```

**代码位置**: `src/parlant/core/glossary.py:136-165`

### 存储文档格式

```python
class _TermDocument(TypedDict, total=False):
    id: ObjectId                    # MongoDB ObjectId
    version: Version.String         # 当前版本："0.2.0"
    content: str                    # 组装的内容（用于嵌入）
    checksum: Required[str]         # MD5 校验和
    creation_utc: str               # ISO 格式时间戳
    name: str                       # 术语名称
    description: str                # 定义
    synonyms: Optional[str]         # 逗号分隔的同义词
```

### 并发控制

```python
# 使用读写锁确保并发安全
async with self._lock.writer_lock:
    # 写操作（创建、更新、删除）
    await self._collection.insert_one(document)

async with self._lock.reader_lock:
    # 读操作（查询、搜索）
    results = await self._collection.find_similar_documents(...)
```

### 版本迁移

当前版本：**0.2.0**

```python
async def _document_loader(
    self,
    document: VectorBaseDocument
) -> Optional[_TermDocument]:
    async def v0_1_0_to_v0_2_0(
        document: VectorBaseDocument
    ) -> Optional[VectorBaseDocument]:
        # 版本迁移逻辑
        raise Exception(
            "This code should not be reached! "
            "Please run the 'parlant-prepare-migration' script."
        )

    return await VectorDocumentMigrationHelper[_TermDocument](
        self,
        {"0.1.0": v0_1_0_to_v0_2_0},
    ).migrate(document)
```

**代码位置**: `src/parlant/core/glossary.py:194-205`

## 高级特性

### 1. 同义词处理

同义词帮助匹配客户的不同表达方式：

```python
term = await agent.create_term(
    name="Gas",
    description="以太坊计算费用单位",
    synonyms=[
        "交易费用",
        "矿工费",
        "Gas Fee",
        "Transaction Fee",
        "区块链燃料"
    ]
)

# 客户可以用任何同义词，AI 都能正确理解：
客户："交易费用太高了" → 匹配 "Gas" 术语
客户："矿工费怎么算" → 匹配 "Gas" 术语
客户："Gas Fee 是多少" → 匹配 "Gas" 术语
```

### 2. 拼写容错

AI 会识别并纠正拼写错误：

```python
# 在 Prompt 中的指令：
"""
Please be tolerant of possible typos by the user with regards to these terms,
and let the user know if/when you assume they meant a term by their typo
"""

# 效果：
客户："Gass 费用是什么？"
AI："我理解您是在询问 Gas 费用。Gas 是以太坊中..."

客户："Smart Contarct 怎么用？"
AI："我想您是在问 Smart Contract（智能合约）。Smart Contract 是..."
```

### 3. 多上下文术语

同一个词在不同 Agent 中有不同含义：

```python
# 区块链 Agent
token_crypto = await crypto_agent.create_term(
    name="Token",
    description="区块链上的数字资产",
    synonyms=["代币", "加密货币"]
)

# NLP Agent
token_nlp = await nlp_agent.create_term(
    name="Token",
    description="文本处理中的词单元",
    synonyms=["词元", "Token"]
)

# 两个 Agent 使用各自的定义，互不干扰
```

### 4. 动态术语加载

只加载相关的术语，节省 token：

```python
# 根据对话上下文动态选择最相关的 20 个术语
relevant_terms = await glossary_store.find_relevant_terms(
    query=interaction_context,  # 从对话历史、变量、工具结果构建
    available_terms=all_terms,   # 所有可用术语
    max_terms=20                 # 最多返回 20 个
)

# 只有最相关的术语会被加入 Prompt
# 不相关的术语不会浪费 token
```

### 5. 术语重新加载

在多个关键点重新加载术语：

```python
# 初始加载
terms = await load_glossary_terms(context)

# 工具执行后重新加载（工具结果可能引入新术语）
if tool_executed:
    terms = await load_glossary_terms(context)

# Guideline 解析后重新加载（新 guidelines 可能需要新术语）
if guidelines_resolved:
    terms = await load_glossary_terms(context)

# 消息生成前最后一次加载
terms = await load_glossary_terms(context)
```

## 测试示例

### SDK 使用示例

```python
from parlant import sdk as p

# 创建 Agent
agent = await server.create_agent(name="区块链专家")

# 创建术语
gas_term = await agent.create_term(
    name="Gas",
    description="以太坊中衡量计算工作的单位",
    synonyms=["交易费用", "矿工费"]
)

# 读取术语
term = await glossary_store.read_term(gas_term.id)
print(f"术语：{term.name}")
print(f"定义：{term.description}")
print(f"同义词：{term.synonyms}")

# 更新术语
updated = await glossary_store.update_term(
    term_id=gas_term.id,
    params={
        "description": "更新后的定义",
        "synonyms": ["新同义词"]
    }
)

# 删除术语
await glossary_store.delete_term(gas_term.id)
```

### BDD 测试示例

```python
# 场景：定义术语
@given('the term "Gas" defined as "以太坊计算单位"')
def given_the_term_definition(
    context: ContextOfTest,
    term_name: str,
    term_description: str,
    agent_id: AgentId,
) -> None:
    # 创建术语
    term = context.sync_await(
        glossary_store.create_term(
            name=term_name,
            description=term_description,
        )
    )

    # 标记为 agent 专用
    context.sync_await(
        glossary_store.upsert_tag(
            term_id=term.id,
            tag_id=Tag.for_agent_id(agent_id),
        )
    )
```

**代码位置**: `tests/core/common/engines/alpha/steps/terms.py:25-46`

### API 测试示例

```python
import httpx

# 创建术语
response = await client.post(
    "/terms",
    json={
        "name": "Gas",
        "description": "以太坊计算单位",
        "synonyms": ["交易费用"]
    }
)
assert response.status_code == 201
term = response.json()

# 读取术语
response = await client.get(f"/terms/{term['id']}")
assert response.status_code == 200

# 更新术语
response = await client.patch(
    f"/terms/{term['id']}",
    json={"description": "更新后的定义"}
)
assert response.status_code == 200

# 删除术语
response = await client.delete(f"/terms/{term['id']}")
assert response.status_code == 204
```

**代码位置**: `tests/api/test_glossary.py`

## 最佳实践

### 1. 清晰的定义

❌ **不好**：
```python
term = await agent.create_term(
    name="Token",
    description="一种数字东西"  # 太模糊
)
```

✅ **好**：
```python
term = await agent.create_term(
    name="Token",
    description="区块链上代表价值的可转移数字资产，符合 ERC-20 标准，可用于交易和治理投票"
)
```

### 2. 全面的同义词

❌ **不好**：
```python
synonyms=["Gas"]  # 只有英文
```

✅ **好**：
```python
synonyms=[
    "交易费用",      # 中文常用说法
    "矿工费",        # 另一种中文说法
    "Gas Fee",       # 英文
    "Transaction Fee",  # 英文通用说法
    "区块链燃料"     # 比喻说法
]
```

### 3. 合理使用标签

```python
# 按 Agent 分组
agent_term = await agent.create_term(...)  # 自动添加 agent 标签

# 按功能分组
await glossary_store.create_term(
    name="...",
    description="...",
    tags=["blockchain", "finance"]
)

# 按地区分组
await glossary_store.create_term(
    name="GST",
    description="商品及服务税（澳大利亚）",
    tags=["region-australia", "tax"]
)
```

### 4. 保持术语简洁

```python
# 术语名称应该简短
name="Gas"  # ✅ 好
name="Gas Fee in Ethereum Blockchain"  # ❌ 太长

# 详细信息放在 description 中
description="以太坊区块链中衡量执行交易或智能合约所需计算工作的单位"
```

### 5. 避免冗余

```python
# ❌ 不要创建重复的术语
term1 = await agent.create_term(name="API", description="...")
term2 = await agent.create_term(name="API", description="...")  # 重复！

# ✅ 使用同义词
term = await agent.create_term(
    name="API",
    description="...",
    synonyms=["应用程序编程接口", "Application Programming Interface"]
)
```

### 6. 定期审查和更新

```python
# 术语定义可能会过时，定期更新
updated_term = await glossary_store.update_term(
    term_id=term_id,
    params={
        "description": "更新的定义（2024年标准）",
        "synonyms": ["新的常用说法"]
    }
)
```

## 企业价值

### 1. 合规性保障

| 行业 | 价值 |
|------|------|
| **金融** | 确保使用监管批准的术语定义，避免误导客户 |
| **医疗** | 使用标准医疗术语，符合 HIPAA 等规范 |
| **法律** | 精确使用法律术语，避免歧义 |
| **保险** | 使用保单标准术语，避免理赔纠纷 |

### 2. 品牌一致性

```
场景：多个 Agent 提供服务

没有 Glossary：
Agent A："Premium 包括高级功能..."
Agent B："Premium 是我们的付费版本..."
Agent C："Premium 提供额外服务..."
→ 客户困惑：Premium 到底是什么？

有 Glossary：
所有 Agent："Premium 是我们的高级订阅计划，
            月费 ¥299，包括无限存储、优先支持..."
→ 一致的品牌体验
```

### 3. 降低运营成本

- **减少客服培训时间**：新客服只需学习 Glossary
- **减少误解和投诉**：准确的术语使用减少纠纷
- **提高自助服务率**：客户得到清晰解释，减少转人工

### 4. 可扩展性

```
初期：10 个术语
中期：50 个术语
后期：200+ 个术语

✅ Glossary 系统自动：
- 向量化存储
- 语义搜索
- 动态加载最相关的术语
- 不影响性能
```

### 5. 多语言支持

```python
# 同一术语的不同语言版本
term_en = await agent.create_term(
    name="Gas",
    description="A unit measuring computational effort in Ethereum",
    tags=["lang-en"]
)

term_zh = await agent.create_term(
    name="Gas",
    description="以太坊中衡量计算工作的单位",
    tags=["lang-zh"]
)

# 根据客户语言偏好加载相应版本
```

### 6. 审计追踪

```python
# 所有术语都有创建时间
term.creation_utc  # "2024-01-01T00:00:00Z"

# 可以追踪术语的变更历史（如果实现了版本控制）
history = await get_term_history(term_id)
for version in history:
    print(f"{version.updated_at}: {version.description}")
```

## 核心价值总结

| 方面 | 没有 Glossary | 有 Glossary |
|------|--------------|-------------|
| **术语准确性** | 使用 LLM 训练数据中的通用定义 | 使用业务特定的精确定义 |
| **一致性** | 不同对话可能用不同定义 | 所有对话使用相同定义 |
| **合规性** | 难以确保合规 | 可以定义合规的术语 |
| **拼写容错** | 不识别拼写错误 | 自动识别并纠正 |
| **同义词处理** | 可能不理解同义词 | 智能匹配所有同义词 |
| **Token 效率** | 需要在 prompt 中硬编码所有定义 | 动态加载相关术语 |
| **可扩展性** | 难以管理大量术语 | 向量搜索，轻松处理数百术语 |
| **多上下文** | 同一词可能混淆 | 不同 Agent 可以有不同定义 |

## 技术架构总结

```
┌─────────────────────────────────────────────────────┐
│                   Glossary 系统                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. 创建 Terms                                      │
│     ├─ 组装内容（name + synonyms + description）   │
│     ├─ 生成向量嵌入                                 │
│     └─ 存储到向量数据库                             │
│                                                     │
│  2. 语义搜索                                        │
│     ├─ 构建查询上下文                               │
│     ├─ 分块处理（Token 限制）                       │
│     ├─ 并行搜索                                     │
│     └─ 按相似度排序                                 │
│                                                     │
│  3. 集成到引擎                                      │
│     ├─ 多个阶段加载术语                             │
│     ├─ 添加到 Agent Prompt                          │
│     ├─ 影响 Guideline 匹配                          │
│     └─ 指导消息生成                                 │
│                                                     │
│  4. 作用域管理                                      │
│     ├─ 全局术语（tags=[]）                          │
│     ├─ Agent 专用（tags=[agent-id:xxx]）            │
│     └─ 自定义分组（tags=[custom-tags]）             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 结论

**Glossary/Term 是 Parlant 中确保语义一致性和术语准确性的核心机制。**

### 核心特点：

1. **智能匹配**：使用向量嵌入进行语义搜索
2. **动态加载**：只加载相关术语，节省 token
3. **作用域控制**：支持全局、Agent 专用、自定义标签
4. **同义词支持**：处理多种表达方式
5. **拼写容错**：识别并纠正客户的拼写错误
6. **多上下文**：同一术语在不同场景有不同定义

### 适用场景：

- 金融、医疗等需要精确术语的行业
- 多 Agent 系统需要统一术语
- 技术产品需要解释专业术语
- 国际化应用需要多语言术语
- 品牌一致性要求高的企业

**Glossary 让 AI Agent 从"通用聊天机器人"变成"领域专家"！**
