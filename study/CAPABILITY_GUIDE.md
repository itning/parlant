# Parlant Capability 深度讲解

## Capability 是什么？

**Capability（能力）** 是 Parlant 中用于描述 **AI Agent 能够提供的服务或功能** 的核心机制。

它回答了一个关键问题：**"这个 Agent 能为客户做什么？"**

## 简单类比

想象你在银行遇到客服人员：

```
没有 Capability：
客户："我需要帮助"
客服："好的，请问具体需要什么帮助？"
（客服不主动说明能提供什么服务）

有 Capability：
客户："我需要帮助"
AI 识别到相关 Capabilities：
  - "重置密码"
  - "查询余额"
  - "挂失银行卡"
AI："我可以帮您重置密码、查询账户余额或挂失银行卡。
     请问您需要哪方面的帮助？"
（主动告知可提供的服务）
```

## Capability vs Guideline

这是两个容易混淆的概念，必须理解它们的区别：

| 方面 | Capability（能力） | Guideline（指南） |
|------|-------------------|------------------|
| **定义** | 描述 Agent **能做什么** | 规定 Agent **应该怎么做** |
| **性质** | 信息性的 | 规定性的 |
| **结构** | 标题 + 描述 + 示例信号 | 条件 + 行动 |
| **匹配** | 语义匹配（向量搜索） | 语义匹配 + 自定义策略 |
| **用途** | 主动发现和提供服务 | 强制执行行为规则 |
| **示例** | "提供贷款服务" | "当客户询问贷款时，先验证资格" |
| **控制** | Agent 可以选择是否提及 | Agent 必须遵守 |

**关键区别**：
- **Capability** = "我能帮你做这个"（能力声明）
- **Guideline** = "当遇到这种情况时必须这样做"（行为规则）

### 实际例子

```python
# Capability：告诉客户我能做什么
capability = await agent.create_capability(
    title="重置密码",
    description="帮助客户重置忘记的密码",
    signals=["忘记密码", "无法登录", "重置密码"]
)

# Guideline：规定怎么做
guideline = await agent.create_guideline(
    condition="客户要求重置密码",
    action="首先验证客户身份，然后发送重置链接到注册邮箱"
)

# 两者配合使用：
# 1. Capability 让 AI 知道可以提供密码重置服务
# 2. Guideline 规定密码重置时必须先验证身份
```

## Capability 的核心结构

### 数据模型

```python
@dataclass(frozen=True)
class Capability:
    id: CapabilityId              # 唯一ID
    creation_utc: datetime        # 创建时间
    title: str                    # 能力标题（简短名称）
    description: str              # 详细描述
    signals: Sequence[str]        # 示例信号（触发短语）
    tags: list[TagId]             # 标签（用于分组和过滤）
```

**代码位置**: `src/parlant/core/capabilities.py:50-61`

### 字段说明

| 字段 | 类型 | 说明 | 例子 |
|------|------|------|------|
| `id` | CapabilityId | 唯一标识符（从内容生成） | "cap_reset_password_001" |
| `title` | str | 能力的简短名称 | "重置密码" |
| `description` | str | 详细说明这个能力做什么 | "帮助客户重置忘记的密码" |
| `signals` | list[str] | 触发这个能力的示例短语 | ["忘记密码", "无法登录"] |
| `tags` | list[TagId] | 范围标签 | ["agent-bank01"] |
| `creation_utc` | datetime | 创建时间（UTC） | "2024-01-01T00:00:00Z" |

### Signals（信号）的重要性

**Signals 是 Capability 的核心**，它们是真实客户可能说的话：

```python
capability = await agent.create_capability(
    title="挂失银行卡",
    description="为客户挂失丢失或被盗的银行卡",
    signals=[
        "我的卡丢了",
        "银行卡被盗了",
        "需要挂失",
        "卡找不到了",
        "想挂失我的卡"
    ]
)
```

**为什么重要**：
- Signals 被嵌入成向量，用于语义搜索
- 即使客户说的话和 signals 不完全一样，也能通过语义相似度匹配
- 更多的 signals = 更好的匹配准确度

## 创建和管理 Capabilities

### 基本创建

```python
# 通过 SDK 创建
agent = await server.create_agent(name="银行客服")

capability = await agent.experimental_features.create_capability(
    title="查询余额",
    description="为客户提供账户余额信息",
    signals=[
        "我的余额是多少",
        "账户余额",
        "还有多少钱",
        "查询余额"
    ]
)
```

### 完整创建（所有参数）

```python
# 通过 CapabilityStore 创建
capability = await capability_store.create_capability(
    title="申请贷款",
    description="帮助客户申请最高 10 万元的个人贷款",
    signals=[
        "我想贷款",
        "申请贷款",
        "需要借钱",
        "能贷款吗"
    ],
    tags=[Tag.for_agent_id(agent_id), "financial-services"],
    creation_utc=datetime.now(timezone.utc)  # 可选
)
```

### CRUD 操作

```python
# 读取 Capability
capability = await capability_store.read_capability(capability_id)

# 更新 Capability
updated = await capability_store.update_capability(
    capability_id=capability_id,
    params={
        "title": "新标题",
        "description": "更新后的描述",
        "signals": ["新信号1", "新信号2"]
    }
)

# 列出所有 Capabilities
all_capabilities = await capability_store.list_capabilities()

# 按标签过滤
agent_capabilities = await capability_store.list_capabilities(
    tags=[Tag.for_agent_id(agent_id)]
)

# 删除 Capability
await capability_store.delete_capability(capability_id)
```

**代码位置**: `src/parlant/core/capabilities.py`

### 标签管理

```python
# 添加标签
await capability_store.upsert_tag(
    capability_id=capability.id,
    tag_id=Tag.for_agent_id(agent_id)
)

# 移除标签
await capability_store.remove_tag(
    capability_id=capability.id,
    tag_id=tag_id
)
```

## Capability 的范围（Scope）

### 三种范围类型

#### 1. **全局 Capabilities**（所有 Agent 可用）

```python
# tags=[] 表示全局
global_capability = await capability_store.create_capability(
    title="提供一般信息",
    description="回答客户关于公司的一般性问题",
    signals=["你们是什么公司", "公司简介"],
    tags=[]  # 空标签 = 全局
)
```

#### 2. **Agent 专用 Capabilities**

```python
# 只有特定 agent 可以提供
agent_capability = await agent.experimental_features.create_capability(
    title="贷款服务",
    description="提供个人贷款",
    signals=["申请贷款", "贷款"]
    # SDK 自动添加 Tag.for_agent_id(agent.id)
)
```

#### 3. **自定义标签 Capabilities**

```python
# 使用自定义标签分组
regional_capability = await capability_store.create_capability(
    title="区域特定服务",
    description="仅在特定地区提供的服务",
    tags=["region-shanghai", "premium-tier"],
    signals=["上海服务", "本地服务"]
)
```

### 范围层次结构

```
┌─────────────────────────────────┐
│   全局 Capabilities (tags=[])    │  所有 Agent 可用
├─────────────────────────────────┤
│   Agent 专用 Capabilities        │  只有特定 Agent 可用
│   (tags=[agent-id:xyz])          │
├─────────────────────────────────┤
│   自定义标签 Capabilities        │  自定义分组
│   (tags=[custom-tag-1, ...])     │
└─────────────────────────────────┘
         ↓ 语义搜索 ↓
    返回最相关的 K 个 Capabilities
```

**代码位置**: `src/parlant/core/entity_cq.py:255-284`

## 向量嵌入与语义匹配

### 嵌入策略

Capability 的嵌入方式很特殊：**每个 Capability 创建多个向量**。

```python
capability = Capability(
    title="重置密码",
    description="帮助客户重置忘记的密码",
    signals=["忘记密码", "无法登录", "锁定账户"]
)

# 创建 4 个向量文档：
# 1. "重置密码: 帮助客户重置忘记的密码"
# 2. "忘记密码"
# 3. "无法登录"
# 4. "锁定账户"
```

**代码实现**：

```python
def _list_capability_contents(self, capability: Capability) -> list[str]:
    # 组合标题和描述 + 每个 signal
    return [
        f"{capability.title}: {capability.description}"
    ] + list(capability.signals)

async def _insert_capability(self, capability: Capability):
    # 为每个内容创建一个向量文档
    for content in self._list_capability_contents(capability):
        doc_id = self._id_generator.generate(md5_checksum(content))

        vec_doc = CapabilityVectorDocument(
            id=ObjectId(doc_id),
            capability_id=ObjectId(capability.id),
            content=content,  # 这个会被嵌入
            checksum=md5_checksum(content),
        )

        # 插入向量数据库（自动嵌入）
        await self._vector_collection.insert_one(document=vec_doc)
```

**代码位置**: `src/parlant/core/capabilities.py:285-302`

### 语义搜索流程

```
1. 从对话历史构建查询
   ↓
2. 将查询分块（适应 token 限制）
   ↓
3. 对每个块进行向量搜索
   ↓
4. 合并结果并去重
   ↓
5. 按相似度排序
   ↓
6. 返回前 K 个最相关的 Capabilities
```

### 语义匹配实现

```python
async def find_relevant_capabilities(
    self,
    query: str,
    available_capabilities: Sequence[Capability],
    max_count: int,
) -> Sequence[Capability]:
    # 1. 分块查询（处理长文本）
    queries = await query_chunks(query, self._embedder)

    # 2. 过滤到可用的 capabilities
    filters: Where = {
        "capability_id": {"$in": [str(c.id) for c in available_capabilities]}
    }

    # 3. 对每个查询块执行语义搜索
    tasks = [
        self._vector_collection.find_similar_documents(
            filters=filters,
            query=q,
            k=calculate_min_vectors_for_max_item_count(...)
        )
        for q in queries
    ]

    # 4. 合并所有结果
    all_sdocs = chain.from_iterable(await async_utils.safe_gather(*tasks))

    # 5. 去重（每个 capability 只保留最相似的匹配）
    unique_sdocs: dict[str, SimilarDocumentResult] = {}
    for similar_doc in all_sdocs:
        capability_id = similar_doc.document["capability_id"]
        if (capability_id not in unique_sdocs or
            unique_sdocs[capability_id].distance > similar_doc.distance):
            unique_sdocs[capability_id] = similar_doc

    # 6. 返回前 K 个，按相似度排序
    capability_ids = [
        r.document["capability_id"]
        for r in sorted(unique_sdocs.values(), key=lambda r: r.distance)[:max_count]
    ]

    return [await self._deserialize(doc) for doc in ...]
```

**代码位置**: `src/parlant/core/capabilities.py:471-523`

### 去重的重要性

由于每个 Capability 有多个向量（标题+描述 + 每个 signal），同一个 Capability 可能多次出现在搜索结果中。去重确保：
- 每个 Capability 只出现一次
- 保留最相似的匹配（最小 distance）
- 返回准确的前 K 个结果

## Capabilities 在引擎中的使用

### 加载时机

Capabilities 在响应生成过程中被加载：

```python
async def _load_capabilities(self, context: EngineContext) -> Sequence[Capability]:
    # 从最近的交互历史构建查询
    query = ""

    if context.interaction.events:
        query += str([e.data for e in context.interaction.events])

    if query:
        # 查找与对话相关的 capabilities
        return await self._entity_queries.find_capabilities_for_agent(
            agent_id=context.agent.id,
            query=query,
            max_count=3,  # 限制为前 3 个最相关的
        )

    return []
```

**代码位置**: `src/parlant/core/engines/alpha/engine.py:1700-1716`

### 查找流程

```python
async def find_capabilities_for_agent(
    self,
    agent_id: AgentId,
    query: str,
    max_count: int,
) -> Sequence[Capability]:
    # 1. 从三个来源加载 capabilities
    agent_capabilities = await self._capability_store.list_capabilities(
        tags=[Tag.for_agent_id(agent_id)],
    )

    global_capabilities = await self._capability_store.list_capabilities(
        tags=[]
    )

    agent = await self._agent_store.read_agent(agent_id)
    capabilities_for_agent_tags = await self._capability_store.list_capabilities(
        tags=[tag for tag in agent.tags]
    )

    # 2. 合并所有可用的 capabilities
    all_capabilities = set(chain(
        agent_capabilities,
        global_capabilities,
        capabilities_for_agent_tags,
    ))

    # 3. 根据查询找到语义相关的
    result = await self._capability_store.find_relevant_capabilities(
        query,
        list(all_capabilities),
        max_count=max_count,
    )

    return result
```

**代码位置**: `src/parlant/core/entity_cq.py:255-284`

### 在 Engine Context 中的位置

```python
@dataclass(frozen=False)
class ResponseState:
    """响应生成期间的状态"""

    context_variables: list[tuple[ContextVariable, ContextVariableValue]]
    glossary_terms: set[Term]
    capabilities: list[Capability]  # <-- 加载到这里
    iterations: list[IterationState]
    ordinary_guideline_matches: list[GuidelineMatch]
    tool_enabled_guideline_matches: dict[GuidelineMatch, list[ToolId]]
    journeys: list[Journey]
    # ... 更多状态 ...
```

**代码位置**: `src/parlant/core/engines/alpha/engine_context.py:144-176`

### 在 Prompt 中的呈现

#### 1. Guideline 匹配阶段

```python
def add_capabilities_for_guideline_matching(
    self,
    capabilities: Sequence[Capability]
):
    if capabilities:
        capabilities_string = self._create_capabilities_string(capabilities)

        self.add_section(
            name=BuiltInSection.CAPABILITIES,
            template="""
The following are the capabilities that you hold as an agent.
They may or may not affect your decision regarding the specified guidelines.
###
{capabilities_string}
###
""",
            props={"capabilities_string": capabilities_string},
            status=SectionStatus.ACTIVE,
        )
```

**代码位置**: `src/parlant/core/engines/alpha/prompt_builder.py:505-524`

#### 2. 消息生成阶段

```python
def add_capabilities_for_message_generation(
    self,
    capabilities: Sequence[Capability]
):
    if capabilities:
        capabilities_string = self._create_capabilities_string(capabilities)

        self.add_section(
            template="""
Below are the capabilities available to you as an agent.
You may inform the customer that you can assist them using these capabilities.
Always prefer adhering to guidelines, before offering capabilities -
only offer capabilities if you have no other instruction that's relevant.
Be proactive and offer the most relevant capabilities—but only if they are
likely to move the conversation forward.
If multiple capabilities are appropriate, aim to present them all.
If none address the current request - DO NOT MENTION THEM.

{capabilities_string}
""",
            props={"capabilities_string": capabilities_string},
        )
```

**代码位置**: `src/parlant/core/engines/alpha/prompt_builder.py:462-503`

### Prompt 示例

```
================================
你是一个 AI 助手，名字是银行客服...

...

以下是你作为 Agent 拥有的能力。
你可以告知客户你可以使用这些能力帮助他们。
始终优先遵守 guidelines，只有在没有其他相关指令时才提供 capabilities。
主动提供最相关的 capabilities，但仅当它们可能推动对话进展时。
如果多个 capabilities 都合适，尽量全部展示。
如果都不适用当前请求 - 不要提及它们。

支持的能力 1: 重置密码
帮助客户重置忘记的密码

支持的能力 2: 查询余额
为客户提供账户余额信息

支持的能力 3: 挂失银行卡
为客户挂失丢失或被盗的银行卡

...
================================
```

### 对 AI 行为的影响

1. **主动服务发现**：AI 知道自己能提供哪些服务
2. **相关性判断**：只提供与当前对话相关的服务
3. **Guidelines 优先**：先遵守 guidelines，再提供 capabilities
4. **多个选项**：如果多个 capabilities 都相关，可以全部提供

## API 端点

### REST API

**文件位置**: `src/parlant/api/capabilities.py`

#### 1. 创建 Capability

```http
POST /capabilities

Request:
{
    "title": "重置密码",
    "description": "帮助客户重置忘记的密码",
    "signals": ["忘记密码", "无法登录", "重置密码"],
    "tags": ["agent-bank01"]
}

Response (201 Created):
{
    "id": "cap_reset_password_001",
    "title": "重置密码",
    "description": "帮助客户重置忘记的密码",
    "signals": ["忘记密码", "无法登录", "重置密码"],
    "tags": ["agent-bank01"],
    "creation_utc": "2024-01-01T00:00:00Z"
}
```

#### 2. 读取 Capability

```http
GET /capabilities/{capability_id}

Response (200 OK):
{
    "id": "cap_reset_password_001",
    "title": "重置密码",
    ...
}
```

#### 3. 列出 Capabilities

```http
# 列出所有 capabilities
GET /capabilities

# 按标签过滤
GET /capabilities?tag_id=agent-bank01

Response (200 OK):
[
    {
        "id": "cap_reset_password_001",
        "title": "重置密码",
        ...
    },
    {
        "id": "cap_check_balance_002",
        "title": "查询余额",
        ...
    }
]
```

#### 4. 更新 Capability

```http
PATCH /capabilities/{capability_id}

Request:
{
    "title": "账户密码重置",
    "description": "更新后的描述",
    "signals": ["新信号"],
    "tags": {
        "add": ["new-tag"],
        "remove": ["old-tag"]
    }
}

Response (200 OK):
{
    "id": "cap_reset_password_001",
    "title": "账户密码重置",
    ...
}
```

#### 5. 删除 Capability

```http
DELETE /capabilities/{capability_id}

Response (204 No Content)
```

## 与其他概念的关系

### Capabilities ↔ Guidelines

**关系**：
- **Guidelines 优先**：AI 先遵守 guidelines，再考虑提供 capabilities
- **互补关系**：Guidelines 规定"怎么做"，Capabilities 描述"能做什么"
- **共同出现**：两者可以同时出现在 prompt 中

**例子**：
```python
# Capability：告诉客户能做什么
capability = await agent.create_capability(
    title="提供贷款",
    description="提供最高 10 万元的个人贷款",
    signals=["申请贷款", "需要贷款"]
)

# Guideline：规定怎么做
guideline = await agent.create_guideline(
    condition="客户询问贷款",
    action="首先验证客户的信用评分和收入，然后提供贷款方案"
)

# 协同工作：
# 1. Capability 让 AI 知道可以提供贷款服务
# 2. Guideline 确保提供贷款前先验证资格
```

### Capabilities ↔ Tools

**关系**：
- **Tools** 是可执行的函数/API
- **Capabilities** 是对服务的描述（可能使用 Tools）
- Capability 通常依赖一个或多个 Tools 来实现

**例子**：
```python
# Tool：实际执行的函数
@tool
async def reset_password(customer_id: str) -> bool:
    # 重置密码的实际逻辑
    ...

# Capability：描述这个服务
capability = await agent.create_capability(
    title="重置密码",
    description="帮助客户重置密码",
    signals=["忘记密码", "重置密码"]
)

# Guideline：关联 Tool 和 Capability
guideline = await agent.create_guideline(
    condition="客户需要重置密码",
    action="调用 reset_password 工具"
)
await guideline.associate_tool("user_service", "reset_password")
```

### Capabilities ↔ Journeys

**关系**：
- Journey 可以包含多个 Capabilities
- Capabilities 可以标记为特定 Journey 的一部分
- Journey 执行时会加载相关的 Capabilities

**例子**：
```python
# 创建 Journey
onboarding_journey = await agent.create_journey(
    title="新客户入职",
    conditions=["新用户", "注册"],
    description="引导新客户完成入职流程"
)

# 创建 Journey 专用的 Capabilities
capability1 = await capability_store.create_capability(
    title="创建账户",
    description="为新客户创建账户",
    signals=["创建账户", "注册"],
    tags=[Tag.for_journey_id(onboarding_journey.id)]
)

capability2 = await capability_store.create_capability(
    title="验证身份",
    description="验证客户身份信息",
    signals=["身份验证", "KYC"],
    tags=[Tag.for_journey_id(onboarding_journey.id)]
)
```

### Capabilities ↔ Agent Discovery

**关系**：
- Capabilities 是 Agent 的"功能清单"
- 可以通过 Capabilities 发现 Agent 能做什么
- 多 Agent 系统中，可以根据 Capabilities 路由请求

**例子**：
```python
# 查询 Agent 的所有 capabilities
agent_capabilities = await capability_store.list_capabilities(
    tags=[Tag.for_agent_id(agent_id)]
)

# 展示给用户
print(f"这个 Agent 可以：")
for cap in agent_capabilities:
    print(f"- {cap.title}: {cap.description}")

# 输出：
# 这个 Agent 可以：
# - 重置密码: 帮助客户重置忘记的密码
# - 查询余额: 为客户提供账户余额信息
# - 挂失银行卡: 为客户挂失丢失或被盗的银行卡
```

## 实际应用场景

### 1. 银行客服 Agent

```python
agent = await server.create_agent(name="银行客服")

# 定义银行服务的 capabilities
capabilities = [
    await agent.experimental_features.create_capability(
        title="查询余额",
        description="为客户提供账户余额信息",
        signals=["余额", "有多少钱", "账户余额"]
    ),
    await agent.experimental_features.create_capability(
        title="转账服务",
        description="帮助客户转账到其他账户",
        signals=["转账", "汇款", "给别人打钱"]
    ),
    await agent.experimental_features.create_capability(
        title="挂失银行卡",
        description="为客户挂失丢失或被盗的银行卡",
        signals=["卡丢了", "卡被盗", "挂失"]
    ),
    await agent.experimental_features.create_capability(
        title="贷款申请",
        description="提供个人贷款申请服务，最高 10 万元",
        signals=["贷款", "借钱", "申请贷款"]
    ),
    await agent.experimental_features.create_capability(
        title="信用卡申请",
        description="帮助客户申请信用卡",
        signals=["办信用卡", "申请信用卡", "要信用卡"]
    )
]
```

**效果**：
```
客户："我需要帮助"
AI：根据对话历史，没有明确需求
→ 不加载特定 capabilities

客户："我的钱不够了"
AI：语义搜索 → 匹配到 "贷款申请" capability
AI："我看到您提到资金不足。我可以帮您申请个人贷款，
     最高额度 10 万元。您需要了解贷款详情吗？"
```

### 2. 电商客服 Agent

```python
agent = await server.create_agent(name="电商客服")

capabilities = [
    await agent.experimental_features.create_capability(
        title="订单查询",
        description="帮助客户查询订单状态",
        signals=["订单在哪", "物流", "到哪了", "订单状态"]
    ),
    await agent.experimental_features.create_capability(
        title="退货服务",
        description="处理客户的退货请求，30天无理由退货",
        signals=["退货", "不想要了", "退款", "申请退货"]
    ),
    await agent.experimental_features.create_capability(
        title="商品推荐",
        description="根据客户需求推荐合适的商品",
        signals=["推荐", "有什么好的", "买什么"]
    ),
    await agent.experimental_features.create_capability(
        title="优惠券使用",
        description="帮助客户查询和使用优惠券",
        signals=["优惠券", "折扣", "有优惠吗"]
    )
]
```

### 3. IT 支持 Agent

```python
agent = await server.create_agent(name="IT 支持")

capabilities = [
    await agent.experimental_features.create_capability(
        title="重置密码",
        description="帮助用户重置各种系统的密码",
        signals=["忘记密码", "重置密码", "无法登录"]
    ),
    await agent.experimental_features.create_capability(
        title="软件安装指导",
        description="指导用户安装和配置软件",
        signals=["怎么安装", "软件安装", "配置软件"]
    ),
    await agent.experimental_features.create_capability(
        title="网络问题排查",
        description="诊断和解决网络连接问题",
        signals=["网络断了", "连不上网", "网速慢"]
    ),
    await agent.experimental_features.create_capability(
        title="VPN 设置",
        description="帮助用户设置和连接 VPN",
        signals=["VPN", "远程访问", "无法连接公司网络"]
    )
]
```

### 4. 医疗咨询 Agent

```python
agent = await server.create_agent(name="医疗助手")

capabilities = [
    await agent.experimental_features.create_capability(
        title="预约挂号",
        description="帮助患者预约医生门诊",
        signals=["挂号", "预约", "看医生"]
    ),
    await agent.experimental_features.create_capability(
        title="检查报告解读",
        description="帮助患者理解检查报告",
        signals=["报告", "检查结果", "看不懂报告"]
    ),
    await agent.experimental_features.create_capability(
        title="药品咨询",
        description="提供药品使用方法和注意事项",
        signals=["吃什么药", "怎么吃药", "药品"]
    ),
    await agent.experimental_features.create_capability(
        title="健康建议",
        description="提供一般性的健康生活建议",
        signals=["怎么保健", "健康建议", "养生"]
    )
]
```

## 存储架构

### 双存储系统

```
┌──────────────────────────────────────────────────────┐
│               CapabilityVectorStore                   │
├──────────────────────────────────┬───────────────────┤
│   向量数据库 (Qdrant/Chroma)     │ 文档数据库        │
├──────────────────────────────────┼───────────────────┤
│ • CapabilityVectorDocument       │ • CapabilityDoc   │
│ • 多个向量（title+desc + signals）│ • TagAssociation  │
│ • find_similar_documents()       │ • 标签过滤        │
│ • 语义搜索                        │ • 元数据          │
└──────────────────────────────────┴───────────────────┘
```

### 存储文档格式

**文档数据库**：
```python
class CapabilityDocument(TypedDict):
    id: ObjectId
    version: Version.String       # 当前版本："0.2.0"
    creation_utc: str
    title: str
    description: str
    signals: str                  # JSON 编码的列表
```

**向量数据库**（每个 Capability 多个文档）：
```python
class CapabilityVectorDocument(TypedDict):
    id: ObjectId                  # 从内容生成
    capability_id: ObjectId       # 关联到 Capability
    version: Version.String
    content: str                  # 要嵌入的内容
    checksum: str                 # MD5 校验和
```

### 并发控制

```python
# 使用读写锁确保并发安全
async with self._lock.writer_lock:
    # 写操作（创建、更新、删除）
    await self._vector_collection.insert_one(document)

async with self._lock.reader_lock:
    # 读操作（查询、搜索）
    results = await self._vector_collection.find_similar_documents(...)
```

## 高级特性

### 1. 多信号匹配

每个 signal 都会被单独嵌入，提高匹配准确度：

```python
capability = await agent.create_capability(
    title="挂失银行卡",
    description="为客户挂失丢失或被盗的银行卡",
    signals=[
        "我的卡丢了",
        "银行卡被盗了",
        "卡找不到了",
        "需要挂失",
        "锁定我的卡",
        "卡被偷了"
    ]
)

# 创建 7 个向量：
# 1. "挂失银行卡: 为客户挂失丢失或被盗的银行卡"
# 2. "我的卡丢了"
# 3. "银行卡被盗了"
# 4. "卡找不到了"
# 5. "需要挂失"
# 6. "锁定我的卡"
# 7. "卡被偷了"

# 客户说任何相似的话都能匹配：
客户："我的卡不见了" → 语义相似 "我的卡丢了" → 匹配成功
客户："卡被人拿走了" → 语义相似 "卡被偷了" → 匹配成功
```

### 2. 去重机制

由于多个向量，同一个 Capability 可能多次匹配：

```python
# 搜索结果可能包含：
# - "我的卡丢了" (distance: 0.1)
# - "卡找不到了" (distance: 0.15)
# - "需要挂失" (distance: 0.2)

# 去重后只保留最相似的：
# - capability_id: "cap_xyz", distance: 0.1 (最小)
```

### 3. 动态相关性

只加载对话相关的 capabilities：

```python
# 限制为前 3 个最相关的
max_count=3

# 效果：
客户："我的卡丢了，而且余额不对"
→ 加载 capabilities：
  1. "挂失银行卡" (distance: 0.05)
  2. "查询余额" (distance: 0.12)
  3. "交易记录查询" (distance: 0.18)

# 只有这 3 个会出现在 prompt 中
```

### 4. 多 Agent 协调

```python
# 全局 capabilities（所有 Agent 共享）
global_cap = await capability_store.create_capability(
    title="一般咨询",
    description="回答公司的一般性问题",
    signals=["公司介绍", "营业时间"],
    tags=[]  # 全局
)

# Agent 专用 capabilities
bank_cap = await capability_store.create_capability(
    title="银行服务",
    description="提供银行专属服务",
    signals=["账户", "转账"],
    tags=[Tag.for_agent_id(bank_agent_id)]
)

# 每个 Agent 都能访问全局的，但只有特定 Agent 能访问专用的
```

### 5. Capability 分组

```python
# 按业务功能分组
await capability_store.create_capability(
    title="VIP 服务",
    description="为 VIP 客户提供专属服务",
    signals=["VIP", "专属服务"],
    tags=["vip-tier", "premium"]
)

# 按地区分组
await capability_store.create_capability(
    title="地区服务",
    description="仅在上海地区提供的服务",
    signals=["上海服务", "本地"],
    tags=["region-shanghai"]
)

# 按团队分组
await capability_store.create_capability(
    title="技术支持",
    description="技术问题支持",
    signals=["技术问题", "bug"],
    tags=["team-engineering"]
)
```

## 测试示例

### SDK 使用示例

```python
from parlant import sdk as p

# 创建 Agent
agent = await server.create_agent(name="客服助手")

# 创建 Capability
capability = await agent.experimental_features.create_capability(
    title="重置密码",
    description="帮助客户重置密码",
    signals=["忘记密码", "无法登录", "重置密码"]
)

# 读取 Capability
stored_cap = await capability_store.read_capability(capability.id)
print(f"能力：{stored_cap.title}")
print(f"描述：{stored_cap.description}")
print(f"信号：{stored_cap.signals}")

# 更新 Capability
updated = await capability_store.update_capability(
    capability_id=capability.id,
    params={
        "description": "更新后的描述",
        "signals": ["新信号1", "新信号2"]
    }
)

# 删除 Capability
await capability_store.delete_capability(capability.id)
```

### BDD 测试示例

```python
# 测试预定义的 capabilities
CAPABILITIES = {
    "offer_loan": {
        "title": "offer_loan",
        "description": "You can offer a loan of up to 10,000$ to the customer.",
        "signals": ["offering loan", "low balance", "need more money"],
    },
    "replace_card": {
        "title": "replace_card",
        "description": "Issue and send a replacement for the customer's card.",
        "signals": ["my card was stolen", "I lost my card", "need a new card"],
    },
    "reset_password": {
        "title": "reset_password",
        "description": "Assist customer in resetting password if forgotten.",
        "signals": ["forgot my password", "can't log in", "reset my password"],
    },
}

# 在测试中使用
@given("the capability 'reset_password'")
def setup_capability(context):
    cap_data = CAPABILITIES["reset_password"]
    capability = context.sync_await(
        capability_store.create_capability(**cap_data)
    )
```

**代码位置**: `tests/core/common/engines/alpha/steps/capabilities.py`

### API 测试示例

```python
import httpx

# 创建 capability
response = await client.post(
    "/capabilities",
    json={
        "title": "重置密码",
        "description": "帮助客户重置密码",
        "signals": ["忘记密码", "无法登录"]
    }
)
assert response.status_code == 201
capability = response.json()

# 读取 capability
response = await client.get(f"/capabilities/{capability['id']}")
assert response.status_code == 200

# 更新 capability
response = await client.patch(
    f"/capabilities/{capability['id']}",
    json={"description": "更新后的描述"}
)
assert response.status_code == 200

# 删除 capability
response = await client.delete(f"/capabilities/{capability['id']}")
assert response.status_code == 204
```

## 最佳实践

### 1. 清晰的标题

❌ **不好**：
```python
title="做事情"  # 太模糊
```

✅ **好**：
```python
title="重置账户密码"  # 清晰具体
```

### 2. 详细的描述

❌ **不好**：
```python
description="帮助客户"  # 不够具体
```

✅ **好**：
```python
description="帮助客户重置忘记的账户密码，发送验证码到注册邮箱"
```

### 3. 丰富的信号

❌ **不好**：
```python
signals=["密码"]  # 太少，太简单
```

✅ **好**：
```python
signals=[
    "忘记密码",
    "密码忘了",
    "无法登录",
    "登不进去",
    "重置密码",
    "修改密码",
    "密码错误"
]  # 多样化，覆盖不同表达方式
```

### 4. 合理使用标签

```python
# 按 Agent 分组
await agent.create_capability(...)  # 自动添加 agent 标签

# 按功能分组
tags=["password-management", "security"]

# 按业务分组
tags=["retail-banking", "customer-service"]

# 按地区分组
tags=["region-cn", "region-us"]
```

### 5. 避免重复

```python
# ❌ 不要创建重复的 capabilities
cap1 = await agent.create_capability(
    title="重置密码",
    description="...",
    signals=[...]
)
cap2 = await agent.create_capability(
    title="密码重置",  # 重复！
    description="...",
    signals=[...]
)

# ✅ 使用更多的 signals
cap = await agent.create_capability(
    title="重置密码",
    description="...",
    signals=[
        "忘记密码",
        "重置密码",
        "修改密码",
        "密码重置",
        "更改密码"
    ]
)
```

### 6. 定期审查和更新

```python
# 定期检查和更新 capabilities
capabilities = await capability_store.list_capabilities(
    tags=[Tag.for_agent_id(agent_id)]
)

for cap in capabilities:
    # 检查是否还相关
    # 更新 signals 以反映客户的实际用语
    if needs_update(cap):
        await capability_store.update_capability(
            cap.id,
            {"signals": updated_signals}
        )
```

## 企业价值

### 1. 主动服务发现

| 场景 | 没有 Capabilities | 有 Capabilities |
|------|------------------|-----------------|
| **客户求助** | "请问需要什么帮助？" | "我可以帮您重置密码、查询余额或挂失银行卡" |
| **模糊需求** | 等待客户说清楚 | 主动提供相关服务选项 |
| **服务范围** | 客户不知道能做什么 | 清晰展示可用服务 |

### 2. 提升客户体验

```
场景：客户遇到问题

传统方式：
客户："我遇到问题了"
AI："请具体说明您的问题"
客户："就是有点问题"
AI："能详细说明吗？"
→ 反复确认，体验差

使用 Capabilities：
客户："我遇到问题了"
AI：语义搜索 → 发现常见问题相关的 capabilities
AI："我可以帮您：
     1. 重置密码
     2. 查询订单状态
     3. 处理退货
     请问是哪方面的问题？"
→ 主动提供选项，快速解决
```

### 3. 降低运营成本

- **减少客户培训成本**：客户自己发现能用的服务
- **减少误解**：清晰的能力描述减少沟通成本
- **提高自助率**：客户知道能做什么，更倾向自助

### 4. 可扩展性

```
初期：5 个 capabilities
中期：20 个 capabilities
后期：50+ capabilities

✅ Capabilities 系统自动：
- 向量化存储
- 语义搜索
- 去重
- 相关性排序
- 只展示最相关的前 K 个
```

### 5. 多 Agent 协调

```python
# 场景：多个专业 Agent

# 通用 Agent
general_agent = await server.create_agent(name="通用助手")
await general_agent.create_capability(
    title="一般咨询",
    description="回答公司的一般性问题",
    signals=["公司介绍", "营业时间"]
)

# 技术 Agent
tech_agent = await server.create_agent(name="技术支持")
await tech_agent.create_capability(
    title="技术支持",
    description="解决技术问题",
    signals=["技术问题", "bug", "系统错误"]
)

# 根据 capabilities 自动路由：
# 客户："公司在哪里？" → 路由到 general_agent
# 客户："系统崩溃了" → 路由到 tech_agent
```

### 6. 服务透明度

```python
# 可以向客户展示 Agent 的所有能力
capabilities = await capability_store.list_capabilities(
    tags=[Tag.for_agent_id(agent_id)]
)

print("我们的 AI 助手可以帮您：")
for cap in capabilities:
    print(f"• {cap.title}: {cap.description}")

# 输出：
# 我们的 AI 助手可以帮您：
# • 重置密码: 帮助您重置忘记的密码
# • 查询余额: 为您提供账户余额信息
# • 挂失银行卡: 为您挂失丢失或被盗的银行卡
# • 转账服务: 帮助您转账到其他账户
# • 贷款申请: 提供个人贷款申请服务
```

## 核心价值总结

| 方面 | 没有 Capabilities | 有 Capabilities |
|------|------------------|-----------------|
| **服务发现** | 客户需要主动询问 | AI 主动提供相关服务 |
| **相关性** | 无法判断什么服务相关 | 语义搜索自动匹配 |
| **可扩展性** | 添加服务需要修改代码 | 直接创建新 Capability |
| **透明度** | 客户不知道能做什么 | 清晰展示可用服务 |
| **多 Agent** | 难以协调 | 根据 capabilities 路由 |
| **客户体验** | 反复确认需求 | 快速提供选项 |

## 技术架构总结

```
┌─────────────────────────────────────────────────────┐
│                  Capability 系统                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. 创建 Capabilities                               │
│     ├─ 定义 title + description + signals          │
│     ├─ 为每个内容创建向量文档                        │
│     └─ 存储到向量数据库                              │
│                                                     │
│  2. 语义搜索                                        │
│     ├─ 从对话构建查询                                │
│     ├─ 分块处理（Token 限制）                        │
│     ├─ 并行搜索多个向量                              │
│     ├─ 去重（每个 capability 只保留最相似的）        │
│     └─ 按相似度排序，返回前 K 个                     │
│                                                     │
│  3. 集成到引擎                                      │
│     ├─ 加载相关 capabilities                        │
│     ├─ 添加到 Agent Prompt                          │
│     ├─ Guidelines 优先，Capabilities 补充           │
│     └─ 指导 AI 主动提供服务                         │
│                                                     │
│  4. 作用域管理                                      │
│     ├─ 全局 capabilities（tags=[]）                │
│     ├─ Agent 专用（tags=[agent-id:xxx]）            │
│     └─ 自定义分组（tags=[custom-tags]）             │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 结论

**Capability 是 Parlant 中描述 AI Agent 服务能力的核心机制。**

### 核心特点：

1. **语义发现**：通过向量搜索自动匹配相关服务
2. **多向量策略**：每个 capability 创建多个向量（title+desc + 每个 signal）
3. **去重机制**：确保每个 capability 只出现一次
4. **动态加载**：只加载对话相关的 capabilities
5. **作用域控制**：支持全局、Agent 专用、自定义标签
6. **与 Guidelines 互补**：Guidelines 规定怎么做，Capabilities 描述能做什么

### 适用场景：

- 需要主动发现和提供服务的场景
- 多服务 Agent（如银行、电商客服）
- 多 Agent 系统的服务路由
- 需要向客户透明展示能力的场景
- 服务目录和发现机制

### 与 Guideline 的配合：

```
Guideline：定义规则和行为
    ↓
Capability：描述可用服务
    ↓
协同工作：
  - Guidelines 确保合规和正确的行为
  - Capabilities 帮助主动发现和提供服务
  - Guidelines 优先级更高
  - Capabilities 作为补充选项
```

**Capabilities 让 AI Agent 从"被动响应"变成"主动服务提供者"！**
