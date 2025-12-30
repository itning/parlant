# Parlant Tag（标签）深度讲解

## Tag 是什么？

**Tag（标签）** 是 Parlant 中用于**组织、分类和关联资源**的基础机制。

它是 Parlant 架构中的"万能胶水"，将 Agents、Guidelines、Capabilities、Customers、Journeys、Context Variables、Canned Responses 等所有实体灵活地连接在一起。

## 简单类比

想象你在管理一个大型公司的文件系统：

```
没有标签系统：
每个文件只能放在一个文件夹中
- 文件夹 A：销售部文件
- 文件夹 B：VIP 客户文件
- 问题：一份"销售部 VIP 客户合同"应该放哪里？

有标签系统：
文件可以有多个标签
- 文件："VIP 客户合同.pdf"
- 标签：[销售部, VIP客户, 合同, 2024年]

查找时可以按任意标签组合：
- 找所有"VIP 客户"的文件
- 找所有"销售部"的文件
- 找所有"合同"文件
- 找"销售部 + VIP + 合同"的文件
```

在 Parlant 中：
- **Guideline** 可以有多个标签：`[agent:bank01, vip-customer, compliance]`
- **Customer** 可以有多个标签：`[vip, region-cn, language-zh]`
- 引擎加载时按标签过滤：只加载匹配的 Guidelines 给匹配的 Customers

---

## 核心价值

Tag 使 Parlant 能够：
- 🏷️ **灵活组织**资源（无层级限制）
- 🎯 **精确控制**资源的作用域
- 👥 **细分客户**群体（VIP、企业、测试组）
- 🌍 **支持多租户**（不同组织/团队）
- 🧪 **实现 A/B 测试**（实验组 vs 对照组）
- 🚩 **功能开关**（特性标志管理）

---

## Tag 的核心结构

### 数据模型

```python
@dataclass(frozen=True)
class Tag:
    id: TagId              # 唯一标识符
    creation_utc: datetime  # 创建时间
    name: str              # 标签名称
```

**代码位置**: `src/parlant/core/tags.py:36-40`

### 字段说明

| 字段 | 类型 | 说明 | 例子 |
|------|------|------|------|
| `id` | TagId | 唯一标识符（基于 MD5 自动生成） | "tag_abc123" |
| `creation_utc` | datetime | 创建时间戳（自动生成） | "2024-01-15T10:00:00Z" |
| `name` | str | 标签名称（kebab-case 格式） | "vip-customer" |

### TagId 类型

```python
TagId = NewType("TagId", str)
```

TagId 是字符串类型，使用校验和生成保证唯一性。

---

## 创建和管理 Tags

### 基本操作

```python
from parlant.core.tags import TagStore, TagId

# 1. 创建标签
tag = await tag_store.create_tag(
    name="vip-customer"
)
# 返回：
# Tag(id="tag_abc123", creation_utc="...", name="vip-customer")

# 2. 读取标签
tag = await tag_store.read_tag(tag_id="tag_abc123")

# 3. 列出所有标签
all_tags = await tag_store.list_tags()

# 4. 更新标签（只能更新名称）
updated = await tag_store.update_tag(
    tag_id="tag_abc123",
    params={"name": "premium-customer"}
)

# 5. 删除标签
await tag_store.delete_tag(tag_id="tag_abc123")
```

**代码位置**: `src/parlant/core/tags.py:95-126`

### CRUD 完整示例

```python
# 创建多个标签
vip_tag = await tag_store.create_tag("vip")
enterprise_tag = await tag_store.create_tag("enterprise")
beta_tester_tag = await tag_store.create_tag("beta-tester")
region_cn_tag = await tag_store.create_tag("region-cn")

# 列出所有标签
tags = await tag_store.list_tags()
for tag in tags:
    print(f"{tag.id}: {tag.name}")

# 输出：
# tag_abc123: vip
# tag_def456: enterprise
# tag_ghi789: beta-tester
# tag_jkl012: region-cn

# 更新标签名称
updated = await tag_store.update_tag(
    tag_id=vip_tag.id,
    params={"name": "premium-customer"}
)
# tag_abc123: premium-customer

# 删除不需要的标签
await tag_store.delete_tag(tag_id=beta_tester_tag.id)
```

---

## Tag 的类型

### 1. 系统生成的标签（Special Tags）

这些标签有特殊的语义，由系统自动生成：

```python
# Location: src/parlant/core/tags.py:42-89

# 1. Preamble 标签（对话开场白）
Tag.preamble() → "__preamble__"
# 用途：标记对话开场白的 Canned Responses

# 2. Agent 标签
Tag.for_agent_id("agent_123") → "agent:agent_123"
# 用途：将资源关联到特定 Agent

# 3. Journey 标签
Tag.for_journey_id("journey_456") → "journey:journey_456"
Tag.for_journey_node_id("node_789") → "journey_node:node_789"
# 用途：将资源关联到特定 Journey 或 Node

# 4. Guideline 标签
Tag.for_guideline_id("guideline_abc") → "guideline:guideline_abc"
# 用途：将资源关联到特定 Guideline
```

### 2. 自定义标签（Custom Tags）

用户定义的任意分类标签：

```python
# 客户分层
"vip"                    # VIP 客户
"enterprise"             # 企业客户
"sme"                    # 中小企业
"trial"                  # 试用用户

# 功能开关
"new-ui"                 # 新 UI
"experimental"           # 实验性功能
"ai-insights"            # AI 洞察功能

# 地区/语言
"region-cn"              # 中国区
"region-us"              # 美国区
"language-zh"            # 中文
"language-en"            # 英文

# 业务分类
"sales"                  # 销售
"support"                # 支持
"billing"                # 账单
"compliance"             # 合规

# A/B 测试
"experiment-a"           # 实验 A 组
"experiment-b"           # 实验 B 组
"control-group"          # 对照组
```

### 3. 标签命名规范

**格式**: kebab-case（小写字母 + 连字符）

✅ **好的命名**:
```python
"vip-customer"           # 清晰描述
"enterprise-user"        # 描述性强
"region-apac"            # 标准前缀
"beta-tester"            # 简洁明了
```

❌ **不好的命名**:
```python
"vipCustomer"            # 驼峰命名
"VIP_CUSTOMER"           # 大写下划线
"premium customer"       # 包含空格
"premium_customer_user"  # 过于冗长
"a"                      # 过于简洁
```

**验证规则**（来自 API）：
- 最小长度：1 个字符
- 最大长度：50 个字符
- 格式：kebab-case

---

## Tag 与其他概念的关系

### 1. Tag ↔ Agent

**关系**: Agent 可以被打上多个标签

```python
@dataclass(frozen=True)
class Agent:
    ...
    tags: Sequence[TagId]  # Agent 的标签
```

**代码位置**: `src/parlant/core/agents.py`

**示例**:
```python
# Agent 有自定义标签
agent = Agent(
    id="agent_bank01",
    name="银行客服",
    tags=["sales", "retail-banking", "region-cn"]
)

# 为 Agent 添加标签
await agent_store.upsert_tag(
    agent_id="agent_bank01",
    tag_id=TagId("premium-services")
)

# 移除标签
await agent_store.remove_tag(
    agent_id="agent_bank01",
    tag_id=TagId("trial")
)
```

**用途**:
- 组织和分类 Agents
- 让特定 Guidelines/Capabilities 只对特定 Agents 可用

---

### 2. Tag ↔ Guideline

**关系**: Guideline 可以有多个标签，控制其在哪些上下文中可用

```python
@dataclass(frozen=True)
class Guideline:
    ...
    tags: Sequence[TagId]  # Guideline 的标签
```

**代码位置**: `src/parlant/core/guidelines.py`

**示例**:
```python
# 全局 Guideline（所有 Agent 可用）
global_guideline = await guideline_store.create_guideline(
    condition="客户需要帮助",
    action="提供友好帮助",
    tags=[]  # 空标签 = 全局
)

# Agent 专用 Guideline
agent_guideline = await guideline_store.create_guideline(
    condition="VIP 客户咨询",
    action="提供优先支持",
    tags=[Tag.for_agent_id("agent_bank01")]
)

# 特定客户群的 Guideline
vip_guideline = await guideline_store.create_guideline(
    condition="客户询问费用",
    action="豁免 VIP 客户费用",
    tags=[TagId("vip-customer")]
)
```

**加载逻辑**（Entity Queries）:
```python
# 1. Agent 标签的 Guidelines
agent_guidelines = await store.list_guidelines(
    tags=[Tag.for_agent_id(agent_id)]
)

# 2. Agent 自定义标签的 Guidelines
agent = await store.read_agent(agent_id)
custom_guidelines = await store.list_guidelines(
    tags=agent.tags  # 例如 ["sales", "premium-services"]
)

# 3. 全局 Guidelines
global_guidelines = await store.list_guidelines(tags=[])

# 4. 合并去重
all_guidelines = set(chain(
    agent_guidelines,
    custom_guidelines,
    global_guidelines
))
```

**代码位置**: `src/parlant/core/entity_cq.py:68-110`

---

### 3. Tag ↔ Capability

**关系**: Capability 可以有多个标签，用于过滤和分类

```python
@dataclass(frozen=True)
class Capability:
    ...
    tags: list[TagId]  # Capability 的标签
```

**代码位置**: `src/parlant/core/capabilities.py`

**示例**:
```python
# 销售 Agent 专属能力
sales_capability = await capability_store.create_capability(
    title="产品推荐",
    description="基于客户需求推荐产品",
    tags=[TagId("sales")]  # 只有带有 "sales" 标签的 Agent 可用
)

# VIP 客户专属能力
vip_capability = await capability_store.create_capability(
    title="专属客服",
    description="VIP 客户专属客服通道",
    tags=[TagId("vip-customer")]
)

# 全局能力
global_capability = await capability_store.create_capability(
    title="查询余额",
    description="查询账户余额",
    tags=[]  # 所有 Agent 可用
)
```

**加载逻辑**:
```python
# 类似 Guideline 的加载逻辑
# 1. Agent 标签的 Capabilities
# 2. Agent 自定义标签的 Capabilities
# 3. 全局 Capabilities
# 4. 合并去重
```

---

### 4. Tag ↔ Glossary

**关系**: Term 可以有多个标签，支持多上下文术语定义

```python
@dataclass(frozen=True)
class Term:
    ...
    tags: list[TagId]  # Term 的标签
```

**代码位置**: `src/parlant/core/glossary.py`

**示例**:
```python
# 同一术语在不同上下文有不同定义

# 金融 Agent 的 "Gas" 定义
gas_financial = await glossary_store.create_term(
    name="Gas",
    description="天然气期货",
    tags=[Tag.for_agent_id("agent_finance")]
)

# 加密货币 Agent 的 "Gas" 定义
gas_crypto = await glossary_store.create_term(
    name="Gas",
    description="以太坊网络费用",
    tags=[Tag.for_agent_id("agent_crypto")]
)

# 全局 "Gas" 定义
gas_general = await glossary_store.create_term(
    name="Gas",
    description="气体燃料",
    tags=[]  # 默认定义
)
```

**加载时**：
- 金融 Agent 的对话只加载 `agent:agent_finance` 的 "Gas" 定义
- 加密货币 Agent 的对话只加载 `agent:agent_crypto` 的 "Gas" 定义

---

### 5. Tag ↔ Context Variable

**关系**: Context Variable 可以有多个标签，控制其作用域

```python
@dataclass(frozen=True)
class ContextVariable:
    ...
    tags: Sequence[TagId]  # Context Variable 的标签
```

**代码位置**: `src/parlant/core/context_variables.py`

**示例**:
```python
# Agent 专用变量
agent_var = await context_variable_store.create_variable(
    name="AgentConfig",
    description="Agent 特定配置",
    tags=[Tag.for_agent_id("agent_bank01")]
)

# 特定客户群的变量
vip_var = await context_variable_store.create_variable(
    name="VIPBenefits",
    description="VIP 客户专属福利",
    tags=[TagId("vip-customer")]
)

# 地区特定变量
region_var = await context_variable_store.create_variable(
    name="RegionalSettings",
    description="地区特定设置",
    tags=[TagId("region-cn")]
)

# 全局变量
global_var = await context_variable_store.create_variable(
    name="CompanyInfo",
    description="公司信息",
    tags=[]  # 所有 Agent 可用
)
```

**值的优先级**:
```
customer_id 值
  ↓
tag:{tag_id} 值（标签特定）
  ↓
DEFAULT 值（全局默认）
```

---

### 6. Tag ↔ Journey

**关系**: Journey 可以有多个标签，用于分类和组织

```python
@dataclass(frozen=True)
class Journey:
    ...
    tags: Sequence[TagId]  # Journey 的标签
```

**代码位置**: `src/parlant/core/journeys.py`

**示例**:
```python
# VIP 客户专属 Journey
vip_journey = await journey_store.create_journey(
    title="VIP 入职流程",
    nodes=[...],
    tags=[TagId("vip-customer")]
)

# 新用户 Journey
new_user_journey = await journey_store.create_journey(
    title="新用户引导",
    nodes=[...],
    tags=[TagId("new-user")]
)

# 全局 Journey
global_journey = await journey_store.create_journey(
    title="标准入职流程",
    nodes=[...],
    tags=[]  # 所有 Agent 可用
)
```

---

### 7. Tag ↔ Customer

**关系**: Customer 可以有多个标签，用于客户分组和细分

```python
@dataclass(frozen=True)
class Customer:
    ...
    tags: Sequence[TagId]  # Customer 的标签
```

**代码位置**: `src/parlant/core/customers.py`

**示例**:
```python
# 为客户添加标签
await customer_store.upsert_tag(
    customer_id="customer_123",
    tag_id=TagId("vip")
)

await customer_store.upsert_tag(
    customer_id="customer_123",
    tag_id=TagId("region-cn")
)

await customer_store.upsert_tag(
    customer_id="customer_123",
    tag_id=TagId("beta-tester")
)

# customer_123 现在有标签：[vip, region-cn, beta-tester]

# 查询客户的标签
customer = await customer_store.read_customer("customer_123")
print(customer.tags)  # ["vip", "region-cn", "beta-tester"]

# 移除标签
await customer_store.remove_tag(
    customer_id="customer_123",
    tag_id=TagId("beta-tester")
)
```

**用途**:
- 客户分层（VIP、企业、试用等）
- 地理分区
- 实验组分配
- 个性化服务

---

### 8. Tag ↔ Canned Response

**关系**: Canned Response 可以有多个标签，包括特殊的 `__preamble__` 标签

```python
@dataclass(frozen=True)
class CannedResponse:
    ...
    tags: Sequence[TagId]  # Canned Response 的标签
```

**代码位置**: `src/parlant/core/canned_responses.py`

**示例**:
```python
# Preamble Canned Response（对话开场白）
preamble_canrep = await canned_response_store.create_canned_response(
    value="让我为您查询一下...",
    tags=[Tag.preamble()]  # 特殊的 __preamble__ 标签
)

# Agent 专用 Canned Response
agent_canrep = await canned_response_store.create_canned_response(
    value="作为我们银行的尊贵客户...",
    tags=[Tag.for_agent_id("agent_bank01")]
)

# 特定客户群的 Canned Response
vip_canrep = await canned_response_store.create_canned_response(
    value="感谢您选择我们的 VIP 服务...",
    tags=[TagId("vip-customer")]
)

# 全局 Canned Response
global_canrep = await canned_response_store.create_canned_response(
    value="感谢您的咨询...",
    tags=[]  # 所有 Agent 可用
)
```

**Preamble 标签的用途**:
```python
# Location: src/parlant/core/engines/alpha/canned_response_generator.py:704

# 过滤出所有 preamble 标签的 Canned Responses
preamble_responses = [
    canrep
    for canrep in await store.list_canned_responses(tags=[])
    if Tag.preamble() in canrep.tags
]

# 这些回复在 AI 生成完整回复之前发送
# 给用户即时反馈："让我查询一下..."
```

---

## Tag 在引擎中的使用

### Entity Queries - 标签过滤机制

**核心概念**: Entity Queries 根据标签决定加载哪些资源

**代码位置**: `src/parlant/core/entity_cq.py`

### 加载 Guidelines 的完整流程

```python
async def find_guidelines_for_context(
    self,
    agent_id: AgentId,
    journeys: Sequence[Journey],
) -> Sequence[Guideline]:
    # 1. Agent 专用 Guidelines（agent:{agent_id} 标签）
    agent_guidelines = await self._guideline_store.list_guidelines(
        tags=[Tag.for_agent_id(agent_id)]
    )

    # 2. 全局 Guidelines（空标签）
    global_guidelines = await self._guideline_store.list_guidelines(tags=[])

    # 3. Agent 自定义标签的 Guidelines
    agent = await self._agent_store.read_agent(agent_id)
    guidelines_for_agent_tags = await self._guideline_store.list_guidelines(
        tags=[tag for tag in agent.tags]
    )

    # 4. Journey 专用 Guidelines
    guidelines_for_journeys = await self._guideline_store.list_guidelines(
        tags=[Tag.for_journey_id(journey.id) for journey in journeys]
    )

    # 5. Journey Nodes 的 Guidelines
    guidelines_for_journey_nodes = [
        await self._guideline_store.list_guidelines(
            tags=[Tag.for_journey_node_id(node.id)]
        )
        for journey in journeys
        for node in journey.nodes
    ]

    # 6. 合并所有 Guidelines（使用 set 去重）
    all_guidelines = set(chain(
        agent_guidelines,
        global_guidelines,
        guidelines_for_agent_tags,
        guidelines_for_journeys,
        *guidelines_for_journey_nodes,
    ))

    return list(all_guidelines)
```

**代码位置**: `src/parlant/core/entity_cq.py:68-110`

### 类似的加载模式

其他资源遵循相同的模式：

| 资源 | 方法 | 标签加载顺序 |
|------|------|-------------|
| **Capabilities** | `find_capabilities_for_agent()` | Agent tags + Agent's custom tags |
| **Context Variables** | `find_context_variables_for_context()` | Agent tags + Agent's custom tags |
| **Glossary Terms** | `find_glossary_terms_for_context()` | Agent tags + Agent's custom tags |
| **Canned Responses** | `find_canned_responses_for_context()` | Agent tags + Agent's custom tags + Journey tags |
| **Journeys** | `finds_journeys_for_context()` | Agent tags + Agent's custom tags |

### Context Variables 加载示例

```python
async def find_context_variables_for_context(
    self,
    agent_id: AgentId,
) -> Sequence[ContextVariable]:
    # 1. Agent 标签的 Context Variables
    agent_context_variables = await self._context_variable_store.list_variables(
        tags=[Tag.for_agent_id(agent_id)]
    )

    # 2. 全局 Context Variables
    global_context_variables = await self._context_variable_store.list_variables(tags=[])

    # 3. Agent 自定义标签的 Context Variables
    agent = await self._agent_store.read_agent(agent_id)
    context_variables_for_agent_tags = await self._context_variable_store.list_variables(
        tags=[tag for tag in agent.tags]
    )

    # 4. 合并去重
    all_context_variables = set(chain(
        agent_context_variables,
        global_context_variables,
        context_variables_for_agent_tags,
    ))

    return list(all_context_variables)
```

**代码位置**: `src/parlant/core/entity_cq.py:209-229`

---

## 实际应用场景

### 场景 1: 客户分层（Customer Segmentation）

```python
# 1. 创建客户分层标签
vip_tag = await tag_store.create_tag("vip")
enterprise_tag = await tag_store.create_tag("enterprise")
sme_tag = await tag_store.create_tag("sme")
trial_tag = await tag_store.create_tag("trial")

# 2. 为客户打标签
await customer_store.upsert_tag(customer_id="cust_001", tag_id=vip_tag.id)
await customer_store.upsert_tag(customer_id="cust_002", tag_id=enterprise_tag.id)
await customer_store.upsert_tag(customer_id="cust_003", tag_id=sme_tag.id)
await customer_store.upsert_tag(customer_id="cust_004", tag_id=trial_tag.id)

# 3. 创建针对不同客户层的 Guidelines
# VIP 专属服务
vip_guideline = await guideline_store.create_guideline(
    condition="客户需要帮助",
    action="提供优先支持，豁免等待时间",
    tags=[vip_tag.id]
)

# 企业客户专属服务
enterprise_guideline = await guideline_store.create_guideline(
    condition="客户需要帮助",
    action="提供专属客服经理联系方式",
    tags=[enterprise_tag.id]
)

# 4. 结果：
# - cust_001 (VIP) → 获得 VIP 专属服务
# - cust_002 (企业) → 获得企业专属服务
# - cust_003 (SME) → 获得标准服务
# - cust_004 (试用) → 获得试用服务
```

### 场景 2: 多 Agent 环境（Multi-Agent）

```python
# 1. 创建 Agents
sales_agent = await agent_store.create_agent(name="销售 Agent")
support_agent = await agent_store.create_agent(name="支持 Agent")

# 2. 为 Agents 打标签
await agent_store.upsert_tag(sales_agent.id, TagId("sales"))
await agent_store.upsert_tag(sales_agent.id, TagId("outbound"))

await agent_store.upsert_tag(support_agent.id, TagId("support"))
await agent_store.upsert_tag(support_agent.id, TagId("inbound"))

# 3. 创建 Agent 专属 Capabilities
# 销售 Agent 专属能力
product_rec = await capability_store.create_capability(
    title="产品推荐",
    description="根据客户需求推荐产品",
    tags=[TagId("sales")]
)

discount_offer = await capability_store.create_capability(
    title="提供折扣",
    description="为客户提供折扣优惠",
    tags=[TagId("outbound")]
)

# 支持 Agent 专属能力
ticket_support = await capability_store.create_capability(
    title="工单支持",
    description="创建和处理支持工单",
    tags=[TagId("support")]
)

# 4. 结果：
# - 销售 Agent 可以：产品推荐、提供折扣
# - 支持 Agent 可以：工单支持
# - 两者不会混淆，功能边界清晰
```

### 场景 3: A/B 测试

```python
# 1. 创建实验标签
experiment_a_tag = await tag_store.create_tag("experiment-a")
experiment_b_tag = await tag_store.create_tag("experiment-b")
control_group_tag = await tag_store.create_tag("control-group")

# 2. 将客户分配到不同组
await customer_store.upsert_tag("cust_001", experiment_a_tag.id)
await customer_store.upsert_tag("cust_002", experiment_a_tag.id)
await customer_store.upsert_tag("cust_003", experiment_b_tag.id)
await customer_store.upsert_tag("cust_004", experiment_b_tag.id)
await customer_store.upsert_tag("cust_005", control_group_tag.id)

# 3. 为不同组创建不同的 Guidelines
# 实验 A 组：使用折扣话术
experiment_a_guideline = await guideline_store.create_guideline(
    condition="客户询问价格",
    action="强调折扣和优惠：现在购买可享 8 折优惠",
    tags=[experiment_a_tag.id]
)

# 实验 B 组：使用品质话术
experiment_b_guideline = await guideline_store.create_guideline(
    condition="客户询问价格",
    action="强调品质和保障：我们的产品经过严格测试，提供 3 年质保",
    tags=[experiment_b_tag.id]
)

# 对照组：使用标准话术
control_guideline = await guideline_store.create_guideline(
    condition="客户询问价格",
    action="提供标准价格信息",
    tags=[control_group_tag.id]
)

# 4. 结果：
# - cust_001、cust_002 → 收到折扣话术
# - cust_003、cust_004 → 收到品质话术
# - cust_005 → 收到标准话术
# - 可以对比转化率，找出最有效的话术
```

### 场景 4: 地区和语言本地化

```python
# 1. 创建地区和语言标签
region_cn_tag = await tag_store.create_tag("region-cn")
region_us_tag = await tag_store.create_tag("region-us")
region_eu_tag = await tag_store.create_tag("region-eu")

lang_zh_tag = await tag_store.create_tag("lang-zh")
lang_en_tag = await tag_store.create_tag("lang-en")
lang_es_tag = await tag_store.create_tag("lang-es")

# 2. 为客户打标签
await customer_store.upsert_tag("cust_cn_001", region_cn_tag.id)
await customer_store.upsert_tag("cust_cn_001", lang_zh_tag.id)

await customer_store.upsert_tag("cust_us_001", region_us_tag.id)
await customer_store.upsert_tag("cust_us_001", lang_en_tag.id)

# 3. 创建地区专属 Glossary
# 中国区的 "APR" 定义
apr_cn = await glossary_store.create_term(
    name="APR",
    description="年化收益率：投资产品的年化回报率",
    tags=[region_cn_tag.id]
)

# 美国的 "APR" 定义
apr_us = await glossary_store.create_term(
    name="APR",
    description="年化利率：贷款产品的年化借款成本",
    tags=[region_us_tag.id]
)

# 4. 创建地区专属 Guidelines
# 中国区：用人民币计价
cn_guideline = await guideline_store.create_guideline(
    condition="客户询问价格",
    action="提供人民币（CNY）价格",
    tags=[region_cn_tag.id]
)

# 美国区：用美元计价
us_guideline = await guideline_store.create_guideline(
    condition="客户询问价格",
    action="提供美元（USD）价格",
    tags=[region_us_tag.id]
)
```

### 场景 5: 功能开关（Feature Flags）

```python
# 1. 创建功能标签
new_dashboard_tag = await tag_store.create_tag("feature-new-dashboard")
ai_insights_tag = await tag_store.create_tag("feature-ai-insights")
dark_mode_tag = await tag_store.create_tag("feature-dark-mode")

# 2. 为 Beta 测试者启用新功能
await customer_store.upsert_tag("cust_beta_001", new_dashboard_tag.id)
await customer_store.upsert_tag("cust_beta_001", ai_insights_tag.id)

# 3. 创建功能相关的 Capabilities
new_dashboard_capability = await capability_store.create_capability(
    title="新仪表板",
    description="访问全新的仪表板界面",
    tags=[new_dashboard_tag.id]
)

ai_insights_capability = await capability_store.create_capability(
    title="AI 洞察",
    description="使用 AI 分析业务数据",
    tags=[ai_insights_tag.id]
)

# 4. 创建功能相关的 Guidelines
dashboard_guideline = await guideline_store.create_guideline(
    condition="客户询问仪表板",
    action="向有标签的客户介绍新仪表板功能",
    tags=[new_dashboard_tag.id]
)

# 5. 结果：
# - Beta 测试者（cust_beta_001）可以看到新功能
# - 普通客户看不到新功能
# - 逐步推广，降低风险
```

### 场景 6: Preamble Messages（对话开场白）

```python
# 1. 创建 Preamble Canned Response
preamble_canrep = await canned_response_store.create_canned_response(
    value="让我为您查询一下，请稍等片刻...",
    signals=["查询", "等一下", "稍等"],
    tags=[Tag.preamble()]  # 特殊的 __preamble__ 标签
)

# 2. 创建常规 Canned Response
regular_canrep = await canned_response_store.create_canned_response(
    value="您的账户余额为 ¥10,000。",
    signals=["余额", "账户"]
)

# 3. 工作流程：
# 客户："我的余额是多少？"
# ↓
# 引擎检测到需要查询余额
# ↓
# 立即发送 Preamble："让我为您查询一下，请稍等片刻..."
# （用户即时收到反馈，体验更好）
# ↓
# AI 调用工具查询余额
# ↓
# 生成完整回复："您的账户余额为 ¥10,000。"
```

---

## API 端点

### REST API

**文件位置**: `src/parlant/api/tags.py`

#### 1. 创建 Tag

```http
POST /tags

Request:
{
  "name": "vip-customer"
}

Response (201 Created):
{
  "id": "tag_abc123",
  "name": "vip-customer",
  "creation_utc": "2024-01-15T10:00:00Z"
}
```

#### 2. 读取 Tag

```http
GET /tags/{tag_id}

Response (200 OK):
{
  "id": "tag_abc123",
  "name": "vip-customer",
  "creation_utc": "2024-01-15T10:00:00Z"
}
```

#### 3. 列出所有 Tags

```http
GET /tags

Response (200 OK):
[
  {
    "id": "tag_abc123",
    "name": "vip-customer",
    "creation_utc": "2024-01-15T10:00:00Z"
  },
  {
    "id": "tag_def456",
    "name": "enterprise",
    "creation_utc": "2024-01-15T11:00:00Z"
  }
]
```

#### 4. 更新 Tag

```http
PATCH /tags/{tag_id}

Request:
{
  "name": "premium-customer"
}

Response (200 OK):
{
  "id": "tag_abc123",
  "name": "premium-customer",
  "creation_utc": "2024-01-15T10:00:00Z"
}
```

#### 5. 删除 Tag

```http
DELETE /tags/{tag_id}

Response (204 No Content)
```

---

## 存储架构

### TagDocumentStore

**文件位置**: `src/parlant/core/tags.py:135-267`

**版本**: 0.1.0

**数据库集合**:
- `tags` - 存储标签文档
- 没有关联集合（关联存储在各个实体上）

**集合结构**:
```
┌─────────────────────────────────┐
│  Collection: tags               │
├─────────────────────────────────┤
│                                 │
│  {                              │
│    "_id": "tag_abc123",         │
│    "version": "0.1.0",          │
│    "name": "vip-customer",      │
│    "creation_utc": "..."        │
│  }                              │
│                                 │
│  {                              │
│    "_id": "tag_def456",         │
│    "version": "0.1.0",          │
│    "name": "enterprise",        │
│    "creation_utc": "..."        │
│  }                              │
│                                 │
└─────────────────────────────────┘
```

### 关联集合（存储在各个实体上）

```
┌──────────────────────────────────┐
│  agent_tags                      │
│  ├─ agent_id: "agent_123"       │
│  └─ tag_id: "tag_abc123"        │
├──────────────────────────────────┤
│  guideline_tag_associations      │
│  ├─ guideline_id: "guide_456"   │
│  └─ tag_id: "tag_def789"        │
├──────────────────────────────────┤
│  capability_tags                 │
│  ├─ capability_id: "cap_789"    │
│  └─ tag_id: "tag_ghi012"        │
└──────────────────────────────────┘
```

---

## 最佳实践

### 1. 标签命名规范

```python
# ✅ 好的命名（kebab-case）
"vip-customer"           # 客户分层
"enterprise-user"        # 用户类型
"region-apac"            # 地区（标准前缀）
"feature-new-ui"         # 功能（标准前缀）
"experiment-group-a"     # 实验（标准前缀）

# ❌ 不好的命名
"vipCustomer"            # 驼峰命名
"VIP_CUSTOMER"           # 大写下划线
"premium customer"       # 包含空格
"pc"                     # 过于简洁
```

### 2. 何时使用 Tags

✅ **应该使用**:
- 客户分层（VIP、企业、试用）
- 功能开关（实验性功能）
- 多租户（不同组织/团队）
- 地区/语言本地化
- A/B 测试
- Agent 分类和组织

❌ **不应该使用**:
- 层级关系（使用实体关系代替）
- 基于时间的数据（使用时间戳）
- 高基数数据（如个别用户 ID）
- 临时状态（使用 Session 或内存）

### 3. 标签层级设计

Tags 是扁平的，不是层级结构。要模拟层级：

```python
# ❌ 错误方式（试图创建层级）
parent_tag = await tag_store.create_tag("region")
child_tag = await tag_store.create_tag("emea")
# 没有父子关系！

# ✅ 正确方式（使用命名约定模拟层级）
region_emea_tag = await tag_store.create_tag("region-emea")
region_emea_france_tag = await tag_store.create_tag("region-emea-france")
region_apac_tag = await tag_store.create_tag("region-apac")
region_apac_china_tag = await tag_store.create_tag("region-apac-china")

# 过滤时：
# - 所有 EMEA：匹配 "region-emea*"
# - 所有 APAC：匹配 "region-apac*"
```

### 4. 标签命名约定（前缀）

使用一致的前缀便于管理和过滤：

```python
# 客户分层
"tier-vip"
"tier-enterprise"
"tier-sme"
"tier-trial"

# 功能开关
"feature-new-dashboard"
"feature-ai-insights"
"feature-dark-mode"

# 地区
"region-cn"
"region-us"
"region-eu"
"region-apac"

# 语言
"lang-zh"
"lang-en"
"lang-es"

# 实验
"exp-a-discount-messaging"
"exp-b-quality-messaging"
"exp-control-standard"

# 业务单元
"bu-sales"
"bu-support"
"bu-billing"
```

### 5. 性能优化

```python
# ✅ 好的做法
# 1. 使用标签预过滤
agent_guidelines = await store.list_guidelines(
    tags=[Tag.for_agent_id(agent_id)]
)

# 2. 合理使用全局资源（tags=[]）
global_guideline = await store.create_guideline(
    condition="通用规则",
    action="标准行动",
    tags=[]  # 所有 Agent 共享
)

# 3. 使用 set 去重（EntityQueries 自动处理）
all_guidelines = set(chain(
    agent_guidelines,
    global_guidelines,
    custom_guidelines
))

# ❌ 不好的做法
# 1. 加载所有资源后在内存中过滤
all_guidelines = await store.list_guidelines()  # 慢！
filtered = [g for g in all_guidelines if check_tags(g)]

# 2. 过度细分标签
tags = ["region-cn", "region-cn-beijing", "region-cn-beijing-haidian", ...]
# 标签太多，查询变慢
```

### 6. 标签与权限控制

```python
# 1. 创建权限标签
compliance_tag = await tag_store.create_tag("compliance-access")
hr_tag = await tag_store.create_tag("hr-access")

# 2. 创建敏感资源的 Guidelines
compliance_guideline = await guideline_store.create_guideline(
    condition="客户询问合规信息",
    action="提供合规相关内容",
    tags=[compliance_tag.id]
)

# 3. 只有特定 Agent 才有权限标签
await agent_store.upsert_tag(
    agent_id="agent_compliance",
    tag_id=compliance_tag.id
)

# 4. 其他 Agent（如销售 Agent）没有该标签，无法访问敏感内容
```

---

## 企业价值

### 1. 多租户支持

| 场景 | 实现 |
|------|------|
| **组织隔离** | 每个组织有独立的标签 |
| **资源隔离** | 通过标签控制资源可见性 |
| **配置隔离** | 同一资源在不同标签下有不同配置 |

```python
# 组织 A
org_a_tag = await tag_store.create_tag("org-acme")

# 组织 B
org_b_tag = await tag_store.create_tag("org-globex")

# 相同的资源，不同的配置
balance_guideline_a = await guideline_store.create_guideline(
    condition="查询余额",
    action="显示 ACME 格式的余额",
    tags=[org_a_tag.id]
)

balance_guideline_b = await guideline_store.create_guideline(
    condition="查询余额",
    action="显示 Globex 格式的余额",
    tags=[org_b_tag.id]
)
```

### 2. 客户细分

```
无标签系统：
- 所有客户收到相同的服务
- 无法个性化体验

有标签系统：
- VIP 客户 → 优先支持、专属客服
- 企业客户 → 专属经理、定制方案
- 试用客户 → 引导购买、功能限制
```

### 3. A/B 测试和实验

```
场景：测试新的销售话术

实验组 A（折扣话术）：
- 1000 客户
- 转化率：15%

实验组 B（品质话术）：
- 1000 客户
- 转化率：18%

对照组（标准话术）：
- 1000 客户
- 转化率：12%

结论：品质话术最有效，全面推广！
```

### 4. 功能渐进式发布

```
Week 1: 10% Beta 测试者
Week 2: 25% Beta 测试者
Week 3: 50% 所有用户
Week 4: 100% 所有用户

每个阶段添加标签，逐步扩大功能可用范围
```

### 5. 运营效率

| 操作 | 无标签 | 有标签 |
|------|--------|--------|
| **部署新功能** | 需要修改代码 | 添加标签即可 |
| **隔离问题客户** | 手动过滤 | 打标签自动过滤 |
| **定向推广** | 手动筛选 | 标签精准投放 |
| **权限控制** | 硬编码 | 标签动态管理 |

---

## 核心价值总结

| 方面 | 没有 Tags | 有 Tags |
|------|----------|---------|
| **资源组织** | 僵化的层级结构 | 灵活的多维度分类 |
| **作用域控制** | 全局或 Agent 级别 | 细粒度标签级别 |
| **客户细分** | 一刀切 | 个性化服务 |
| **实验和测试** | 需要修改代码 | 标签隔离，无需改代码 |
| **多租户** | 难以实现 | 标签天然支持 |
| **权限控制** | 硬编码 | 标签动态管理 |

## 技术架构总结

```
┌──────────────────────────────────────────────────────┐
│              Tag 系统架构                            │
├──────────────────────────────────────────────────────┤
│                                                      │
│  1. Tag 定义                                         │
│     ├─ ID（唯一标识）                                │
│     ├─ Name（标签名称）                              │
│     └─ Creation UTC（创建时间）                      │
│                                                      │
│  2. Tag 类型                                         │
│     ├─ 系统标签                                      │
│     │   ├─ __preamble__                             │
│     │   ├─ agent:{id}                               │
│     │   ├─ journey:{id}                             │
│     │   └─ guideline:{id}                           │
│     └─ 自定义标签                                    │
│         ├─ 客户分层（vip, enterprise）              │
│         ├─ 功能开关（feature-new-ui）                │
│         ├─ 地区（region-cn, region-us）              │
│         └─ 实验（exp-a, exp-b）                      │
│                                                      │
│  3. Tag 关联                                         │
│     ├─ Agent → Tags                                  │
│     ├─ Guideline → Tags                             │
│     ├─ Capability → Tags                            │
│     ├─ Glossary → Tags                              │
│     ├─ Context Variable → Tags                      │
│     ├─ Journey → Tags                               │
│     ├─ Customer → Tags                              │
│     └─ Canned Response → Tags                       │
│                                                      │
│  4. Entity Queries                                  │
│     ├─ 查找 Agent 标签的资源                         │
│     ├─ 查找 Agent 自定义标签的资源                   │
│     ├─ 查找全局资源（tags=[]）                       │
│     ├─ 查找 Journey 标签的资源                       │
│     └─ 合并去重（set operations）                   │
│                                                      │
│  5. 引擎使用                                         │
│     ├─ 加载时按标签过滤                              │
│     ├─ 只加载匹配的资源                              │
│     ├─ 动态组合资源集合                              │
│     └─ 提供给 AI 使用                                │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## 代码位置速查

| 功能 | 代码位置 |
|------|---------|
| **Tag 数据模型** | `src/parlant/core/tags.py:36-94` |
| **TagStore 接口** | `src/parlant/core/tags.py:95-126` |
| **TagDocumentStore 实现** | `src/parlant/core/tags.py:135-267` |
| **Entity Queries** | `src/parlant/core/entity_cq.py` |
| **REST API** | `src/parlant/api/tags.py` |
| **Agent Tags** | `src/parlant/core/agents.py` |
| **Guideline Tags** | `src/parlant/core/guidelines.py` |
| **Capability Tags** | `src/parlant/core/capabilities.py` |
| **Glossary Tags** | `src/parlant/core/glossary.py` |
| **Context Variable Tags** | `src/parlant/core/context_variables.py` |
| **Journey Tags** | `src/parlant/core/journeys.py` |
| **Customer Tags** | `src/parlant/core/customers.py` |
| **Canned Response Tags** | `src/parlant/core/canned_responses.py` |
| **Preamble Tag 使用** | `src/parlant/core/engines/alpha/canned_response_generator.py:704` |
| **SDK** | `src/parlant/sdk.py:783-793` |
| **测试用例** | `tests/api/test_tags.py` |
| **集成测试** | `tests/core/stable/test_entity_cq.py` |

---

## 结论

**Tag 是 Parlant 框架中的核心组织机制，实现了灵活的资源分类和作用域控制。**

### 核心特点：

1. **简单但强大**: 简单的标签实体 + 强大的过滤能力
2. **跨实体使用**: 所有主要实体都支持标签
3. **扁平结构**: 无层级，通过命名约定模拟层级
4. **系统标签**: 特殊标签支持系统级行为（preamble, agent 作用域等）
5. **动态组合**: Entity Queries 在运行时动态组合资源
6. **多维度分类**: 同一资源可以有多个标签

### 适用场景：

- 客户细分（VIP、企业、试用）
- 功能开关和渐进式发布
- 多租户和权限控制
- A/B 测试和实验
- 地区和语言本地化
- Agent 组织和管理

### 与其他概念的配合：

```
Tags: 提供分类和组织
    ↓
Entity Queries: 按标签加载资源
    ↓
Engine: 使用加载的资源
    ↓
AI: 在正确的上下文中使用正确的资源
    ↓
高度个性化、精准控制的 AI 体验
```

**Tag 让 Parlant 从"一刀切"变成"精准定制"！**
