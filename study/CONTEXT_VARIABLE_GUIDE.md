# Parlant Context Variable（上下文变量）深度讲解

## Context Variable 是什么？

**Context Variable（上下文变量）** 是 Parlant 中用于存储和管理 **客户特定的动态数据** 的核心机制。

它解决了一个关键问题：**如何让 AI Agent 访问和使用个性化的、动态更新的客户数据？**

## 简单类比

想象你在银行与客服交谈：

```
没有 Context Variable：
客户："我的余额是多少？"
AI："请问您的账户号码是？"
客户："123456"
AI："请稍等，我查询一下..."
（客服每次都需要重新询问和查询）

有 Context Variable：
系统自动加载：
  - AccountBalance: ¥15,234.50
  - SubscriptionTier: "Premium"
  - LastLogin: "2024-01-15"

客户："我的余额是多少？"
AI："您好，尊敬的 Premium 客户！您的账户余额是 ¥15,234.50。"
（AI 已经知道客户信息，直接回答）
```

## 核心价值

Context Variable 使 AI Agent 能够：
- 🔄 **自动访问**客户的最新数据
- 🎯 **个性化**每一次对话
- ⚡ **动态更新**数据（通过工具调用）
- ⏰ **定时刷新**数据（基于 Cron 规则）
- 🏷️ **范围控制**（全局、Agent 专用、标签专用）

---

## Context Variable 的核心结构

### 数据模型

```python
@dataclass(frozen=True)
class ContextVariable:
    id: ContextVariableId              # 唯一ID
    name: str                          # 变量名（如 "AccountBalance"）
    description: Optional[str]         # 变量说明
    creation_utc: datetime             # 创建时间
    tool_id: Optional[ToolId]         # 关联工具（用于自动更新）
    freshness_rules: Optional[str]    # Cron 表达式（刷新规则）
    tags: Sequence[TagId]             # 标签（范围控制）
```

**代码位置**: `src/parlant/core/context_variables.py:48-60`

### 字段详解

| 字段 | 类型 | 说明 | 例子 |
|------|------|------|------|
| `id` | ContextVariableId | 唯一标识符（MD5-based） | "var_abc123" |
| `name` | str | 变量名称 | "AccountBalance" |
| `description` | Optional[str] | 变量说明 | "客户的账户余额" |
| `tool_id` | Optional[ToolId] | 关联工具，用于自动获取最新值 | ToolId("finance", "get_balance") |
| `freshness_rules` | Optional[str] | Cron 表达式，定义何时刷新 | "0 8,20 * * *"（每天 8 点和 20 点） |
| `tags` | Sequence[TagId] | 标签，控制变量的可见范围 | [Tag.for_agent_id("agent_123")] |

### ContextVariableValue（变量值）

```python
@dataclass(frozen=True)
class ContextVariableValue:
    id: ContextVariableValueId         # 唯一ID
    last_modified: datetime            # 最后修改时间
    data: JSONSerializable             # 实际数据（字典、数组等）
```

**代码位置**: `src/parlant/core/context_variables.py:63-67`

**三种存储键（Key）**：
1. `customer_id` - 客户特定值
2. `tag:{tag_id}` - 标签特定值
3. `DEFAULT` (全局默认值)

---

## 创建和管理 Context Variables

### 基本创建

```python
# 通过 Application 对象创建
variable = await app.variables.create(
    name="AccountBalance",
    description="客户的账户余额",
    tool_id=ToolId("finance_service", "get_balance"),
    freshness_rules="0 */6 * * *",  # 每 6 小时刷新一次
    tags=[Tag.for_agent_id(agent_id)]
)
```

### 完整创建（所有参数）

```python
from parlant.core.context_variables import ContextVariable
from parlant.core.tools import ToolId
from parlant.core.tags import Tag

variable = await context_variable_store.create_variable(
    name="CustomerProfile",
    description="客户的详细档案信息",
    tool_id=ToolId("customer_service", "fetch_profile"),
    freshness_rules="0 0 * * *",  # 每天午夜刷新
    tags=[
        Tag.for_agent_id("agent_bank01"),
        "vip-customers"  # 自定义标签
    ]
)
```

### CRUD 操作

```python
# 读取变量定义
variable = await context_variable_store.read_variable(variable_id)

# 更新变量定义
updated = await context_variable_store.update_variable(
    variable_id=variable_id,
    params={
        "description": "更新后的说明",
        "freshness_rules": "0 */12 * * *"  # 改为每 12 小时
    }
)

# 列出所有变量
all_variables = await context_variable_store.list_variables()

# 按标签过滤
agent_variables = await context_variable_store.list_variables(
    tags=[Tag.for_agent_id(agent_id)]
)

# 删除变量（级联删除所有值和标签）
await context_variable_store.delete_variable(variable_id)
```

**代码位置**: `src/parlant/core/context_variables.py:77-157`

### 值的管理

```python
# 设置客户特定值
await context_variable_store.update_value(
    variable_id=variable.id,
    key="customer_456",  # 客户 ID
    data={
        "balance": 10000.50,
        "currency": "USD",
        "account_type": "checking",
        "status": "active"
    }
)

# 设置标签特定值
await context_variable_store.update_value(
    variable_id=variable.id,
    key="tag:premium",  # 标签键
    data={
        "balance": 50000.00,
        "currency": "USD",
        "account_type": "premium"
    }
)

# 设置全局默认值
await context_variable_store.update_value(
    variable_id=variable.id,
    key="DEFAULT",
    data={
        "balance": 0.00,
        "currency": "USD",
        "account_type": "basic"
    }
)

# 读取值
value = await context_variable_store.read_value(
    variable_id=variable.id,
    key="customer_456"
)

# 列出所有值
values = await context_variable_store.list_values(variable.id)
for key, value in values:
    print(f"{key}: {value.data}")

# 删除值
await context_variable_store.delete_value(
    variable_id=variable.id,
    key="customer_456"
)
```

---

## Context Variable 的范围（Scope）

### 三种范围类型

#### 1. **全局 Context Variables**（所有 Agent 可用）

```python
# tags=[] 表示全局
global_var = await context_variable_store.create_variable(
    name="CompanyInfo",
    description="公司的基本信息",
    tags=[]  # 空标签 = 全局
)

# 设置全局默认值
await context_variable_store.update_value(
    variable_id=global_var.id,
    key="DEFAULT",
    data={
        "company_name": "Acme Corp",
        "support_email": "support@acme.com",
        "business_hours": "9:00-18:00 Mon-Fri"
    }
)
```

#### 2. **Agent 专用 Context Variables**

```python
# 只有特定 agent 可以访问
agent_var = await app.variables.create(
    name="AgentConfig",
    description="Agent 特定配置",
    tags=[Tag.for_agent_id(agent_id)]  # SDK 自动添加
)
```

#### 3. **标签专用 Context Variables**

```python
# 使用自定义标签
regional_var = await context_variable_store.create_variable(
    name="RegionalSettings",
    description="地区特定设置",
    tags=["region-cn", "lang-zh"],
)

# VIP 客户专用
vip_var = await context_variable_store.create_variable(
    name="VIPBenefits",
    description="VIP 客户专属福利",
    tags=["customer-tier:vip"],
)
```

### 范围层次结构

```
┌─────────────────────────────────┐
│   全局 Variables (tags=[])       │  所有 Agent 可用
├─────────────────────────────────┤
│   Agent 专用 Variables           │  只有特定 Agent 可用
│   (tags=[agent-id:xyz])          │
├─────────────────────────────────┤
│   自定义标签 Variables           │  自定义分组
│   (tags=[custom-tags])           │
└─────────────────────────────────┘
         ↓ 加载时合并 ↓
    传递给 AI 的完整上下文
```

---

## 值的优先级和加载机制

### 加载顺序（优先级从高到低）

```
1. customer_id 值（客户特定）
   ↓
2. tag:{tag_id} 值（标签特定）
   ↓
3. DEFAULT 值（全局默认）
```

### 加载流程

```python
async def _load_context_variables(self, context: EngineContext):
    # 1. 查找可用变量
    available_variables = await self._entity_queries.find_context_variables_for_context(
        agent_id=context.agent.id
    )

    # 2. 为每个变量查找值（按优先级）
    context_variables: list[tuple[ContextVariable, ContextVariableValue]] = []

    for variable in available_variables:
        # 2.1 尝试客户特定值
        value = await self._load_variable_value(
            variable,
            key=context.session.customer_id
        )

        # 2.2 如果没有，尝试客户标签的值
        if not value and context.customer:
            for tag in context.customer.tags:
                value = await self._load_variable_value(
                    variable,
                    key=f"tag:{tag}"
                )
                if value:
                    break

        # 2.3 如果还没有，使用默认值
        if not value:
            value = await self._load_variable_value(
                variable,
                key="DEFAULT"
            )

        if value:
            context_variables.append((variable, value))

    return context_variables
```

**代码位置**: `src/parlant/core/engines/alpha/engine.py:1027-1056`

---

## 自动刷新机制（Freshness Rules）

### Cron 表达式

Context Variables 支持使用 Cron 表达式定义刷新规则：

```python
# 每 5 分钟刷新一次
freshness_rules="*/5 * * * *"

# 每小时刷新一次
freshness_rules="0 * * * *"

# 每天 8 点和 20 点刷新
freshness_rules="0 8,20 * * *"

# 每天午夜刷新
freshness_rules="0 0 * * *"

# 每周一早上 9 点刷新
freshness_rules="0 9 * * 1"

# 每月 1 号午夜刷新
freshness_rules="0 0 1 * *"
```

### 刷新检查逻辑

```python
async def load_fresh_context_variable_value(
    entity_queries: EntityQueries,
    entity_commands: EntityCommands,
    agent_id: AgentId,
    session: Session,
    variable: ContextVariable,
    key: str,
    current_time: datetime = datetime.now(timezone.utc),
) -> Optional[ContextVariableValue]:
    # 1. 读取现有值
    value = await entity_queries.read_context_variable_value(variable.id, key)

    # 2. 如果没有关联工具，直接返回现有值
    if not variable.tool_id:
        return value

    # 3. 检查值是否足够新鲜
    if value and variable.freshness_rules:
        from croniter import croniter

        # 计算下次应该刷新的时间
        cron_iterator = croniter(variable.freshness_rules, value.last_modified)
        next_refresh_time = cron_iterator.get_next(datetime)

        # 如果还没到刷新时间，返回现有值
        if next_refresh_time > current_time:
            return value  # 值仍然新鲜

    # 4. 需要刷新：调用工具获取新值
    tool_context = ToolContext(
        agent_id=agent_id,
        session_id=session.id,
        customer_id=session.customer_id
    )

    tool_service = await entity_queries.read_tool_service(
        variable.tool_id.service_name
    )

    tool_result = await tool_service.call_tool(
        variable.tool_id.tool_name,
        context=tool_context,
        arguments={},
    )

    # 5. 更新并返回新值
    return await entity_commands.update_context_variable_value(
        variable_id=variable.id,
        key=key,
        data=tool_result.data,
    )
```

**代码位置**: `src/parlant/core/engines/alpha/engine.py:2009-2061`

### 刷新示例

```python
# 创建关联工具的变量
balance_var = await app.variables.create(
    name="AccountBalance",
    description="账户余额（自动更新）",
    tool_id=ToolId("banking_service", "fetch_balance"),
    freshness_rules="0 */6 * * *",  # 每 6 小时刷新
)

# 初始值（由工具首次调用获取）
# 假设现在是 2024-01-15 08:00
initial_value = {
    "balance": 5000.00,
    "last_modified": "2024-01-15T08:00:00Z"
}

# 客户在 10:00 发起对话
# → 引擎检查：next_refresh = 14:00，current = 10:00
# → next_refresh > current，值仍然新鲜
# → 使用现有值 5000.00

# 客户在 15:00 发起对话
# → 引擎检查：next_refresh = 14:00，current = 15:00
# → next_refresh < current，值已过期
# → 调用工具获取新值
# → 假设新值为 4500.00
# → 更新 last_modified = "2024-01-15T15:00:00Z"
# → 使用新值 4500.00
```

---

## Context Variables 在引擎中的使用

### 加载时机

Context Variables 在响应生成的初始化阶段被加载：

```
1. Session 创建/恢复
   ↓
2. Engine.process() 被调用
   ↓
3. _initialize_response_state()
   ↓
4. _load_context_variables()
   ├─ 查找可用变量（Agent 专用 + 全局 + 标签专用）
   ├─ 为每个变量加载值（按优先级）
   ├─ 检查 freshness rules
   └─ 自动调用工具刷新过期数据
   ↓
5. 加载到 context.state.context_variables
   ↓
6. 传递给 Prompt Builder
   ↓
7. 包含在 AI Prompt 中
```

**代码位置**: `src/parlant/core/engines/alpha/engine.py:462-463`

### 在 Engine Context 中的位置

```python
@dataclass(frozen=False)
class ResponseState:
    """响应生成期间的状态"""

    context_variables: list[tuple[ContextVariable, ContextVariableValue]]  # <-- 这里
    glossary_terms: set[Term]
    capabilities: list[Capability]
    iterations: list[IterationState]
    ordinary_guideline_matches: list[GuidelineMatch]
    tool_enabled_guideline_matches: dict[GuidelineMatch, list[ToolId]]
    journeys: list[Journey]
    # ... 更多状态 ...
```

**代码位置**: `src/parlant/core/engines/alpha/engine_context.py:144-176`

### 在 Prompt 中的呈现

```python
def add_context_variables(
    self,
    variables: Sequence[tuple[ContextVariable, ContextVariableValue]],
) -> PromptBuilder:
    if variables:
        # 转换为 JSON 格式
        context_values = context_variables_to_json(variables)

        self.add_section(
            name=BuiltInSection.CONTEXT_VARIABLES,
            template="""
The following is information that you're given about the user and context of the interaction: ###
{context_values}
###
""",
            props={"context_values": context_values},
            status=SectionStatus.ACTIVE,
        )
    return self
```

**代码位置**: `src/parlant/core/engines/alpha/prompt_builder.py:383-401`

### JSON 转换

```python
def context_variables_to_json(
    context_variables: Sequence[tuple[ContextVariable, ContextVariableValue]],
) -> str:
    context_values = {
        variable.name: {
            "value": value.data,
            **({"description": variable.description} if variable.description else {}),
        }
        for variable, value in context_variables
    }
    return json.dumps(context_values, indent=2)
```

**代码位置**: `src/parlant/core/engines/alpha/utils.py:21-32`

### Prompt 示例

```
================================
你是一个 AI 助手，名字是银行客服...

...

以下是关于用户和交互上下文的信息：###
{
  "AccountBalance": {
    "value": {
      "balance": 5000.50,
      "currency": "USD",
      "account_type": "checking"
    },
    "description": "客户的账户余额"
  },
  "SubscriptionTier": {
    "value": "Premium",
    "description": "客户的订阅级别"
  },
  "LastLoginDate": {
    "value": "2024-01-15T10:30:00Z",
    "description": "客户的最后登录时间"
  }
}
###

...
================================
```

### 对 AI 行为的影响

AI 使用 Context Variables：
1. **理解客户状态** - 知道客户的当前情况
2. **个性化回复** - 根据客户信息定制响应
3. **准确回答** - 使用真实数据而非猜测
4. **主动服务** - 基于客户数据提供建议

---

## 与其他概念的关系

### Context Variable ↔ Session

**关系**：
- Session 在启动时加载 Context Variables
- 同一 Session 内使用相同的变量值
- Session 结束后，变量值仍然保留（持久化）

**例子**：
```python
# Session 1 (客户 A)
session_a = await app.sessions.create(customer_id="customer_123")
# 加载 Context Variables for customer_123
# → AccountBalance: ¥10,000

# Session 2 (客户 A，稍后)
session_a2 = await app.sessions.create(customer_id="customer_123")
# 加载相同的 Context Variables
# → AccountBalance: ¥9,500 (可能已更新)

# Session 3 (客户 B)
session_b = await app.sessions.create(customer_id="customer_456")
# 加载不同的 Context Variables
# → AccountBalance: ¥5,000
```

### Context Variable ↔ Guidelines

**关系**：
- Guidelines 定义行为规则
- Context Variables 提供数据支撑
- Guidelines 可以基于 Context Variables 的值做决策

**例子**：
```python
# Context Variable
premium_status = ContextVariable(
    name="SubscriptionTier",
    value="Premium"
)

# Guideline 使用这个信息
guideline = await agent.create_guideline(
    condition="客户需要帮助",
    action="""
    如果客户是 Premium 用户（从 SubscriptionTier 变量获取），
    提供优先支持和额外服务选项。
    否则，提供标准支持。
    """
)

# AI 使用：
客户："我需要帮助"
→ Guideline 匹配
→ AI 检查 SubscriptionTier = "Premium"
AI："您好，尊贵的 Premium 客户！我很荣幸为您提供优先支持。
     您可以享受以下服务：1) 专属客服通道 2) 24/7 支持 3) 优先处理..."
```

### Context Variable ↔ Tools

**关系**：
- Context Variables 可以关联 Tool
- Tool 被调用以获取/更新变量值
- Tool 执行结果自动存储在 Context Variable 中

**例子**：
```python
# 定义工具
@tool
async def fetch_account_balance(context: ToolContext) -> dict:
    """获取客户的账户余额"""
    customer_id = context.customer_id
    # 从数据库或外部 API 获取
    balance_data = await bank_api.get_balance(customer_id)
    return {
        "balance": balance_data.amount,
        "currency": balance_data.currency,
        "account_type": balance_data.type
    }

# 创建关联工具的变量
balance_var = await app.variables.create(
    name="AccountBalance",
    description="客户账户余额",
    tool_id=ToolId("banking_service", "fetch_account_balance"),
    freshness_rules="0 */6 * * *",  # 每 6 小时自动刷新
)

# 引擎自动流程：
# 1. 加载变量时检查 freshness
# 2. 如果需要刷新，调用 fetch_account_balance
# 3. 将结果存储到 Context Variable
# 4. 提供给 AI 使用
```

### Context Variable ↔ Canned Responses

**关系**：
- Context Variables 提供动态数据
- Canned Responses 可以在模板中引用这些数据
- 结合使用实现动态但一致的回复

**例子**：
```python
# Context Variable
account_balance = {
    "balance": 5000.50,
    "currency": "USD"
}

# Canned Response 模板（使用 std.variables）
canrep = await agent.create_canned_response(
    template="""
    您的账户余额为 {{std.variables.AccountBalance.balance}} {{std.variables.AccountBalance.currency}}。
    感谢您使用我们的服务！
    """,
    signals=["余额", "账户"]
)

# 渲染结果：
"您的账户余额为 5000.50 USD。感谢您使用我们的服务！"
```

### Context Variable ↔ Glossary

**区别**：
- **Glossary**: 存储业务术语的**静态定义**
- **Context Variable**: 存储客户的**动态数据**

**例子**：
```python
# Glossary：定义 "APR" 这个术语
term = await agent.create_term(
    name="APR",
    description="年化利率：包含利息和所有费用的年化借款成本"
)

# Context Variable：存储客户的实际 APR 值
variable = await app.variables.create(
    name="CustomerAPR",
    description="客户当前的年化利率"
)
await app.variables.update_value(
    variable_id=variable.id,
    key="customer_123",
    data={"apr": 5.5, "apr_type": "variable"}
)

# AI 使用两者：
# - Glossary 提供准确的术语定义
# - Context Variable 提供客户的具体数值
AI："您的 APR（年化利率）是 5.5%。APR 包含了利息和所有费用的年化借款成本。"
```

---

## 实际应用场景

### 场景 1: 银行客服 Agent

```python
agent = await server.create_agent(name="银行客服")

# 1. 账户余额（自动刷新）
balance_var = await app.variables.create(
    name="AccountBalance",
    description="客户的账户余额",
    tool_id=ToolId("banking_service", "fetch_balance"),
    freshness_rules="0 */6 * * *",  # 每 6 小时更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 2. 信用评分（每天更新）
credit_var = await app.variables.create(
    name="CreditScore",
    description="客户的信用评分",
    tool_id=ToolId("credit_service", "get_credit_score"),
    freshness_rules="0 0 * * *",  # 每天午夜更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 3. 最近交易（频繁更新）
transactions_var = await app.variables.create(
    name="RecentTransactions",
    description="最近的交易记录",
    tool_id=ToolId("banking_service", "fetch_recent_transactions"),
    freshness_rules="*/15 * * * *",  # 每 15 分钟更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 4. 客户等级（静态，手动更新）
tier_var = await app.variables.create(
    name="CustomerTier",
    description="客户的会员等级",
    tool_id=None,  # 无自动刷新
    tags=[Tag.for_agent_id(agent.id)]
)

# 为客户设置初始值
await app.variables.update_value(
    variable_id=tier_var.id,
    key="customer_123",
    data="Premium"
)

# 对话示例：
客户："我的余额是多少？"
→ AI 自动访问 AccountBalance 变量
→ 检查是否需要刷新（距离上次更新超过 6 小时？）
→ 如果需要，调用 fetch_balance 工具
AI："您好！您的账户余额为 ¥15,234.50。"

客户："我的信用评分怎么样？"
→ AI 访问 CreditScore 变量（每天更新）
AI："您的当前信用评分为 750 分，处于优秀范围。"
```

### 场景 2: 电商客服 Agent

```python
agent = await server.create_agent(name="电商客服")

# 1. 订单状态
order_var = await app.variables.create(
    name="CurrentOrders",
    description="客户的当前订单",
    tool_id=ToolId("order_service", "fetch_orders"),
    freshness_rules="*/10 * * * *",  # 每 10 分钟更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 2. 购物车
cart_var = await app.variables.create(
    name="ShoppingCart",
    description="客户的购物车内容",
    tool_id=ToolId("cart_service", "get_cart"),
    freshness_rules="*/5 * * * *",  # 每 5 分钟更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 3. 会员积分
points_var = await app.variables.create(
    name="LoyaltyPoints",
    description="客户的会员积分",
    tool_id=ToolId("loyalty_service", "get_points"),
    freshness_rules="0 * * * *",  # 每小时更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 4. 收货地址（静态）
address_var = await app.variables.create(
    name="DefaultAddress",
    description="客户的默认收货地址",
    tool_id=None,
    tags=[Tag.for_agent_id(agent.id)]
)

# 对话示例：
客户："我的订单到哪了？"
→ AI 访问 CurrentOrders 变量
→ 检查刷新规则（10 分钟内有更新吗？）
→ 如果需要，调用 fetch_orders
AI："您好！您的订单 #12345 已发货，预计明天送达。
     快递单号：SF1234567890。"

客户："我有多少积分？"
→ AI 访问 LoyaltyPoints 变量
AI："您当前有 1,520 积分，可兑换 ¥152 的购物券。"
```

### 场景 3: SaaS 产品 Agent

```python
agent = await server.create_agent(name="SaaS 支持")

# 1. 订阅信息
subscription_var = await app.variables.create(
    name="SubscriptionDetails",
    description="用户的订阅详情",
    tool_id=ToolId("subscription_service", "get_subscription"),
    freshness_rules="0 0 * * *",  # 每天更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 2. API 使用量
usage_var = await app.variables.create(
    name="APIUsage",
    description="用户的 API 使用统计",
    tool_id=ToolId("analytics_service", "get_api_usage"),
    freshness_rules="0 * * * *",  # 每小时更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 3. 功能开关（A/B 测试）
features_var = await app.variables.create(
    name="EnabledFeatures",
    description="为用户启用的功能标志",
    tool_id=ToolId("feature_service", "get_features"),
    freshness_rules="0 */6 * * *",  # 每 6 小时更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 设置不同用户组的功能
await app.variables.update_value(
    variable_id=features_var.id,
    key="tag:beta_testers",
    data={
        "new_dashboard": True,
        "advanced_analytics": True,
        "ai_insights": True
    }
)

await app.variables.update_value(
    variable_id=features_var.id,
    key="DEFAULT",
    data={
        "new_dashboard": False,
        "advanced_analytics": False,
        "ai_insights": False
    }
)

# 对话示例：
Beta 测试用户："新仪表板在哪里？"
→ AI 访问 EnabledFeatures 变量
→ 发现 new_dashboard = True
AI："新仪表板已为您启用！您可以在设置 → 实验性功能中找到它。"

普通用户："新仪表板在哪里？"
→ AI 访问 EnabledFeatures 变量
→ 发现 new_dashboard = False
AI："新仪表板目前还在测试中，即将向所有用户开放。
     如果您想提前体验，可以申请加入 Beta 测试计划。"
```

### 场景 4: 医疗助手 Agent

```python
agent = await server.create_agent(name="医疗助手")

# 1. 患者病历摘要
medical_var = await app.variables.create(
    name="PatientMedicalRecord",
    description="患者的病历摘要",
    tool_id=ToolId("ehr_service", "fetch_patient_summary"),
    freshness_rules="0 8,20 * * *",  # 每天 8 点和 20 点更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 2. 当前药物
medication_var = await app.variables.create(
    name="CurrentMedications",
    description="患者正在服用的药物",
    tool_id=ToolId("pharmacy_service", "get_medications"),
    freshness_rules="0 0 * * *",  # 每天更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 3. 预约信息
appointment_var = await app.variables.create(
    name="UpcomingAppointments",
    description="患者的预约",
    tool_id=ToolId("appointment_service", "get_appointments"),
    freshness_rules="0 * * * *",  # 每小时更新
    tags=[Tag.for_agent_id(agent.id)]
)

# 对话示例：
患者："我下次预约是什么时候？"
→ AI 访问 UpcomingAppointments 变量
AI："您的下次预约是 2024-01-20 下午 2:00，王医生门诊。
     请提前 15 分钟到达。"

患者："我现在在吃什么药？"
→ AI 访问 CurrentMedications 变量
AI："根据您的病历，您目前在服用：
     1. 阿司匹林 100mg，每天一次
     2. 降压药 X，每天两次
     请按医嘱规律服药。"
```

---

## API 端点

### REST API

**文件位置**: `src/parlant/api/context_variables.py`

#### 1. 创建 Context Variable

```http
POST /context-variables

Request:
{
    "name": "AccountBalance",
    "description": "客户的账户余额",
    "tool_id": {
        "service_name": "banking_service",
        "tool_name": "fetch_balance"
    },
    "freshness_rules": "0 */6 * * *",
    "tags": ["agent-bank01"]
}

Response (201 Created):
{
    "id": "var_abc123",
    "name": "AccountBalance",
    "description": "客户的账户余额",
    "tool_id": {
        "service_name": "banking_service",
        "tool_name": "fetch_balance"
    },
    "freshness_rules": "0 */6 * * *",
    "tags": ["agent-bank01"],
    "creation_utc": "2024-01-15T10:00:00Z"
}
```

#### 2. 读取 Context Variable

```http
GET /context-variables/{variable_id}

Response (200 OK):
{
    "context_variable": {
        "id": "var_abc123",
        "name": "AccountBalance",
        ...
    },
    "values": [
        {
            "key": "customer_123",
            "value": {
                "id": "val_xyz",
                "last_modified": "2024-01-15T10:00:00Z",
                "data": {
                    "balance": 5000.50,
                    "currency": "USD"
                }
            }
        },
        {
            "key": "DEFAULT",
            "value": {
                "id": "val_default",
                "last_modified": "2024-01-10T00:00:00Z",
                "data": {
                    "balance": 0.00,
                    "currency": "USD"
                }
            }
        }
    ]
}
```

#### 3. 列出 Context Variables

```http
# 列出所有变量
GET /context-variables

# 按标签过滤
GET /context-variables?tag_id=agent-bank01

Response (200 OK):
[
    {
        "id": "var_abc123",
        "name": "AccountBalance",
        ...
    },
    {
        "id": "var_def456",
        "name": "CreditScore",
        ...
    }
]
```

#### 4. 更新 Context Variable 定义

```http
PATCH /context-variables/{variable_id}

Request:
{
    "description": "更新后的描述",
    "freshness_rules": "0 */12 * * *"
}

Response (200 OK):
{
    "id": "var_abc123",
    "name": "AccountBalance",
    "description": "更新后的描述",
    "freshness_rules": "0 */12 * * *",
    ...
}
```

#### 5. 删除 Context Variable

```http
DELETE /context-variables/{variable_id}

Response (204 No Content)
```

#### 6. 设置/更新变量值

```http
PUT /context-variables/{variable_id}/{key}

Request:
{
    "data": {
        "balance": 10000.50,
        "currency": "USD",
        "account_type": "premium"
    }
}

Response (200 OK):
{
    "id": "val_xyz",
    "last_modified": "2024-01-15T15:30:00Z",
    "data": {
        "balance": 10000.50,
        "currency": "USD",
        "account_type": "premium"
    }
}
```

#### 7. 获取变量值

```http
GET /context-variables/{variable_id}/{key}

Response (200 OK):
{
    "id": "val_xyz",
    "last_modified": "2024-01-15T15:30:00Z",
    "data": {
        "balance": 10000.50,
        "currency": "USD"
    }
}
```

#### 8. 删除变量值

```http
DELETE /context-variables/{variable_id}/{key}

Response (204 No Content)
```

---

## 存储架构

### 文档数据库存储

```
┌──────────────────────────────────────────────────────┐
│        ContextVariableDocumentStore                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Collection 1: variables                             │
│  ┌────────────────────────────────────────────┐     │
│  │ {                                          │     │
│  │   id: "var_abc123",                        │     │
│  │   version: "0.3.0",                        │     │
│  │   name: "AccountBalance",                  │     │
│  │   description: "...",                      │     │
│  │   tool_id: {...},                          │     │
│  │   freshness_rules: "0 */6 * * *",          │     │
│  │   creation_utc: "..."                      │     │
│  │ }                                          │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
│  Collection 2: values                                │
│  ┌────────────────────────────────────────────┐     │
│  │ {                                          │     │
│  │   id: "val_xyz",                           │     │
│  │   variable_id: "var_abc123",               │     │
│  │   key: "customer_123",                     │     │
│  │   last_modified: "...",                    │     │
│  │   data: {...}                              │     │
│  │ }                                          │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
│  Collection 3: variable_tag_associations             │
│  ┌────────────────────────────────────────────┐     │
│  │ {                                          │     │
│  │   variable_id: "var_abc123",               │     │
│  │   tag_id: "agent-bank01"                   │     │
│  │ }                                          │     │
│  └────────────────────────────────────────────┘     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**代码位置**: `src/parlant/core/context_variables.py:227-769`

### 版本管理

**当前版本**: 0.3.0

支持从以下版本自动迁移：
- 0.1.0 → 0.2.0 → 0.3.0
- 0.2.0 → 0.3.0

**迁移脚本**: `parlant-prepare-migration`

---

## 最佳实践

### 1. 变量命名规范

```python
# ✅ 好的命名（PascalCase，清晰描述）
"AccountBalance"           # 账户余额
"SubscriptionTier"         # 订阅级别
"LastPurchaseDate"         # 最后购买日期
"PreferredLanguage"        # 偏好语言
"EnabledFeatures"          # 启用的功能

# ❌ 不好的命名
"bal"                      # 太简洁
"account_balance_usd"      # 使用下划线
"customer_primary_account_balance_in_default_currency"  # 太冗长
```

### 2. 何时使用 Context Variable

✅ **应该使用**：
- 客户特定的数据（余额、订单、偏好等）
- 需要频繁更新的动态数据
- 需要个性化 AI 响应的数据
- 与外部工具集成获取的数据
- 需要跨多个 Session 保持的数据

❌ **不应该使用**：
- 静态的业务规则 → 使用 **Guidelines**
- 术语定义 → 使用 **Glossary**
- 临时状态 → 使用 Session 或引擎内存
- 大量数据 → 考虑按需查询而非预加载

### 3. 合理设置 Freshness Rules

```python
# 高频更新的数据（订单状态、库存）
freshness_rules="*/5 * * * *"     # 每 5 分钟

# 中频更新的数据（账户余额、积分）
freshness_rules="0 * * * *"       # 每小时

# 低频更新的数据（会员等级、配置）
freshness_rules="0 0 * * *"       # 每天

# 静态数据（地址、偏好设置）
freshness_rules=None              # 手动更新
```

### 4. 使用标签控制范围

```python
# ✅ 好的范围控制
# Agent 专用
tags=[Tag.for_agent_id(agent_id)]

# 特定客户群
tags=["customer-tier:premium", "region:cn"]

# 多个 Agent 共享
tags=["agent-finance", "agent-support"]

# 全局（所有 Agent）
tags=[]

# ❌ 不好的范围控制
# 所有变量都是全局的（污染命名空间）
tags=[]  # 对所有变量都这样设置

# 过度细分（管理复杂）
tags=["agent1", "agent2", "agent3", "customer_type_a", "region_1", ...]
```

### 5. 性能优化

```python
# ✅ 好的做法
# 1. 按标签过滤，只加载需要的变量
variables = await store.list_variables(
    tags=[Tag.for_agent_id(agent_id)]
)

# 2. 合理设置刷新规则，避免频繁调用工具
freshness_rules="0 */6 * * *"  # 根据实际需求设置

# 3. 批量操作
variable = await store.create_variable(...)
await store.add_variable_tag(variable.id, tag1)
await store.add_variable_tag(variable.id, tag2)

# ❌ 不好的做法
# 1. 加载所有变量后过滤
all_variables = await store.list_variables()
relevant = [v for v in all_variables if check_condition(v)]

# 2. 过于频繁的刷新
freshness_rules="*/1 * * * *"  # 每分钟刷新

# 3. 在循环中单独操作
for tag in tags:
    variable = await store.create_variable(...)
    await store.add_variable_tag(variable.id, tag)
```

### 6. 数据结构设计

```python
# ✅ 好的数据结构（结构化、类型明确）
data={
    "balance": 5000.50,          # 数值
    "currency": "USD",            # 字符串
    "account_type": "checking",   # 枚举值
    "is_active": True,            # 布尔值
    "last_transaction": "2024-01-15T10:30:00Z",  # ISO 时间戳
    "transactions": [             # 数组
        {"id": "tx1", "amount": 100.00},
        {"id": "tx2", "amount": -50.00}
    ]
}

# ❌ 不好的数据结构
data={
    "info": "balance:5000.50,currency:USD"  # 字符串拼接
}

data={
    "val": 5000.50  # 缺少上下文
}
```

### 7. 错误处理

```python
# ✅ 好的错误处理
try:
    value = await store.read_value(variable_id, customer_id)
    if value is None:
        # 使用默认值
        value = await store.read_value(variable_id, "DEFAULT")
except Exception as e:
    logger.error(f"Failed to load variable {variable_id}: {e}")
    # 提供降级方案

# ❌ 不好的错误处理
value = await store.read_value(variable_id, customer_id)
# 不检查 None，直接使用
balance = value.data["balance"]  # 可能抛出异常
```

---

## 企业价值

### 1. 个性化客户体验

| 场景 | 没有 Context Variables | 有 Context Variables |
|------|----------------------|---------------------|
| **客户咨询** | "您的账户号是？" → 反复确认 | 自动识别客户，直接提供信息 |
| **推荐服务** | 通用推荐，不精准 | 基于客户数据的精准推荐 |
| **问题解决** | 需要客户提供大量信息 | AI 已知客户状态，快速定位问题 |

### 2. 提升运营效率

```
场景：客户询问订单状态

传统方式（无 Context Variables）：
1. 客户："我的订单到哪了？"
2. AI："请提供订单号"
3. 客户："#12345"
4. AI："请稍等，我查询一下..."
5. AI 调用工具查询
6. AI："您的订单已发货..."
→ 4-5 轮对话

使用 Context Variables：
1. 客户："我的订单到哪了？"
   （系统已预加载 CurrentOrders 变量）
2. AI："您的订单 #12345 已发货，预计明天送达。快递单号：SF1234567890。"
→ 1 轮对话

效率提升：75%
```

### 3. 数据实时性

- **自动刷新**: 基于 Cron 规则自动更新数据
- **按需更新**: freshness_rules 确保数据在需要时才刷新
- **工具集成**: 无缝对接外部系统获取最新数据

### 4. 合规性和安全性

```python
# 敏感数据控制
sensitive_var = await app.variables.create(
    name="SensitiveInfo",
    description="客户敏感信息",
    tags=[Tag.for_agent_id("compliance_agent")],  # 只有特定 Agent 可访问
)

# 审计追踪
# last_modified 字段记录每次更新时间
# 可追溯数据变更历史
```

### 5. A/B 测试和实验

```python
# 为不同用户组设置不同配置
experiment_var = await app.variables.create(
    name="ExperimentConfig",
    description="实验配置"
)

# 控制组
await app.variables.update_value(
    variable_id=experiment_var.id,
    key="tag:control_group",
    data={"feature_enabled": False}
)

# 测试组
await app.variables.update_value(
    variable_id=experiment_var.id,
    key="tag:test_group",
    data={"feature_enabled": True}
)

# AI 根据用户所属组提供不同体验
```

### 6. 降低成本

- **减少 LLM 调用**: 预加载数据，AI 直接使用，无需多轮询问
- **缓存机制**: freshness_rules 避免不必要的工具调用
- **智能刷新**: 只在数据过期时才更新

---

## 核心价值总结

| 方面 | 没有 Context Variables | 有 Context Variables |
|------|----------------------|---------------------|
| **数据访问** | 每次对话都需要询问/查询 | 自动预加载，直接使用 |
| **个性化** | 通用回复，千篇一律 | 基于客户数据的个性化回复 |
| **效率** | 多轮对话确认信息 | 一轮对话解决问题 |
| **实时性** | 手动查询，可能过时 | 自动刷新，数据最新 |
| **可扩展性** | 硬编码客户数据 | 动态配置，易于扩展 |
| **成本** | 频繁工具调用，成本高 | 智能缓存，成本优化 |

## 技术架构总结

```
┌─────────────────────────────────────────────────────┐
│           Context Variable 系统                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. 定义变量                                        │
│     ├─ 名称、描述                                   │
│     ├─ 关联工具（可选）                             │
│     ├─ 刷新规则（Cron）                             │
│     └─ 标签（范围控制）                             │
│                                                     │
│  2. 存储值                                          │
│     ├─ customer_id: 客户特定值                      │
│     ├─ tag:{tag_id}: 标签特定值                     │
│     └─ DEFAULT: 全局默认值                          │
│                                                     │
│  3. 引擎加载                                        │
│     ├─ 查找可用变量（Agent + 全局 + 标签）          │
│     ├─ 按优先级加载值                               │
│     ├─ 检查 freshness rules                         │
│     ├─ 自动调用工具刷新（如需要）                   │
│     └─ 转换为 JSON 格式                             │
│                                                     │
│  4. 集成到 Prompt                                   │
│     ├─ 添加到 Context Variables 部分                │
│     ├─ 包含变量名、值、描述                         │
│     └─ 提供给 AI 模型使用                           │
│                                                     │
│  5. AI 使用                                         │
│     ├─ 理解客户状态                                 │
│     ├─ 个性化回复                                   │
│     ├─ 准确回答                                     │
│     └─ 主动服务                                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 代码位置速查

| 功能 | 代码位置 |
|------|---------|
| **数据模型** | `src/parlant/core/context_variables.py:48-74` |
| **Store 接口** | `src/parlant/core/context_variables.py:77-157` |
| **Store 实现** | `src/parlant/core/context_variables.py:227-769` |
| **引擎加载** | `src/parlant/core/engines/alpha/engine.py:1027-1056` |
| **自动刷新** | `src/parlant/core/engines/alpha/engine.py:2009-2061` |
| **Prompt 集成** | `src/parlant/core/engines/alpha/prompt_builder.py:383-401` |
| **JSON 转换** | `src/parlant/core/engines/alpha/utils.py:21-32` |
| **REST API** | `src/parlant/api/context_variables.py` |
| **SDK 模块** | `src/parlant/core/app_modules/context_variables.py` |
| **测试用例** | `tests/api/test_context_variables.py` |
| **引擎测试** | `tests/core/stable/engines/alpha/test_context_variable_loading.py` |

---

## 结论

**Context Variable 是 Parlant 框架中实现个性化 AI 对话的核心机制。**

### 核心特点：

1. **动态数据注入** - 自动将客户数据注入 AI Prompt
2. **智能刷新** - 基于 Cron 规则的条件性数据更新
3. **工具集成** - 无缝对接外部系统获取最新数据
4. **范围控制** - 支持全局、Agent 专用、标签专用
5. **值优先级** - customer → tag → DEFAULT 的层级加载
6. **性能优化** - 智能缓存和按需刷新

### 适用场景：

- 需要访问客户特定数据的 AI Agent
- 需要实时或定期更新数据的场景
- 需要个性化对话体验的应用
- 需要与外部系统集成的 Agent
- 需要 A/B 测试或实验的场景

### 与其他概念的配合：

```
Context Variables: 提供动态数据
    ↓
Guidelines: 基于数据执行规则
    ↓
Canned Responses: 使用数据填充模板
    ↓
Tools: 更新和刷新数据
    ↓
完整的个性化 AI 体验
```

**Context Variable 让 AI Agent 从"通用助手"变成"了解你的私人顾问"！**
