# Parlant Guideline 深度讲解

## Guideline 是什么？

**Guideline（指南）** 是 Parlant 中控制 AI Agent 行为的**最基本单元**。它定义了**在什么情况下（condition）做什么事（action）**。

可以把 Guideline 理解为：**给 AI 的行为规则**。

## 简单类比

想象你在训练一个客服人员：

```
没有 Guideline：
客户："你们营业到几点？"
AI：随便回答，可能答错

有 Guideline：
Condition: "客户询问营业时间"
Action: "告诉客户我们营业时间是 9:00-18:00"
→ AI 每次都会正确回答！
```

## Guideline 的结构

### 核心定义

```python
@dataclass(frozen=True)
class Guideline:
    id: GuidelineId                    # 唯一ID
    creation_utc: datetime             # 创建时间
    content: GuidelineContent          # 内容（条件+行动）
    enabled: bool                      # 是否启用
    tags: Sequence[TagId]              # 标签
    metadata: Mapping[str, JSONSerializable]  # 元数据
    criticality: Criticality           # 重要程度（LOW/MEDIUM/HIGH）
    composition_mode: Optional[CompositionMode]  # 回复生成模式
```

**代码位置**: `src/parlant/core/guidelines.py`

### GuidelineContent 结构

```python
@dataclass(frozen=True)
class GuidelineContent:
    condition: str           # 触发条件（必需）
    action: Optional[str]    # 要执行的动作（可选）
    description: Optional[str]  # 额外说明
```

### 字段说明

| 字段 | 类型 | 说明 | 例子 |
|------|------|------|------|
| `condition` | str | 什么时候触发这个 guideline | "客户询问价格" |
| `action` | Optional[str] | 触发后要做什么 | "告诉客户当前价格" |
| `description` | Optional[str] | 额外的上下文说明 | "价格可能因促销而变化" |
| `criticality` | Criticality | 重要程度 | HIGH / MEDIUM / LOW |
| `enabled` | bool | 是否启用 | True / False |
| `tags` | Sequence[TagId] | 标签，用于分类和过滤 | ["sales", "pricing"] |
| `metadata` | Mapping | 自定义键值对 | {"continuous": True} |
| `composition_mode` | CompositionMode | 回复生成方式 | FLUID / CANNED_STRICT |

## 创建 Guideline

### 基本创建

```python
# 创建一个简单的 guideline
guideline = await agent.create_guideline(
    condition="客户询问价格",
    action="告诉客户 iPhone 的价格是 ¥5999"
)
```

### 完整创建（所有参数）

```python
guideline = await agent.create_guideline(
    condition="客户询问价格",
    action="提供当前价格信息",
    description="价格可能因促销活动而变化",
    criticality=Criticality.HIGH,        # 高优先级
    enabled=True,                        # 启用
    tags=["sales", "pricing"],           # 标签
    metadata={"continuous": True},       # 可以多次应用
    composition_mode=CompositionMode.FLUID  # 自然生成回复
)
```

### 创建观察型 Guideline（没有 action）

```python
# 只观察，不执行动作
observation = await agent.create_observation(
    condition="客户看起来很沮丧"
)
# 这会影响 AI 的行为，但不会执行特定动作
```

**代码位置**: `src/parlant/core/app_modules/guidelines.py`

## Guideline 的类型

### 1. 观察型 Guideline (Observational)

**特点**：只有 `condition`，没有 `action`

```python
guideline = await agent.create_observation(
    condition="客户使用了礼貌用语"
)
```

**用途**：
- 让 AI 感知对话的氛围和语气
- 影响 AI 的整体行为，但不触发具体动作
- 例如：识别客户情绪、检测对话风格

### 2. 行动型 Guideline (Actionable)

**特点**：既有 `condition`，也有 `action`

```python
guideline = await agent.create_guideline(
    condition="客户询问退货政策",
    action="解释我们的30天无理由退货政策"
)
```

**用途**：
- 最常用的类型
- 明确定义触发条件和响应行为
- 可以关联工具调用

### 3. 消除歧义型 Guideline (Disambiguation)

**特点**：当多个 guidelines 同时匹配时，用于消除歧义

```python
# 通过关系定义优先级
await specific_guideline.prioritize_over(general_guideline)
```

### 4. Journey 节点型 Guideline

**特点**：由 Journey 自动生成，包含 journey 元数据

```python
# Journey 自动生成的 guideline 包含特殊 metadata
{
    "journey_node": {
        "journey_id": "journey_123",
        "index": "1",
        "follow_ups": ["guideline_id_2"]
    }
}
```

**代码位置**: `src/parlant/core/journey_guideline_projection.py`

## Guideline 匹配机制

### 匹配流程

```
1. 客户发送消息
   ↓
2. GuidelineMatcher 收集所有 guidelines
   ↓
3. 根据策略分组（通用 vs 自定义）
   ↓
4. 创建批次（Batches）
   ↓
5. 并行处理所有批次
   ↓
6. 合并匹配结果
   ↓
7. 返回 GuidelineMatch 列表
```

### GuidelineMatcher 核心代码

```python
class GuidelineMatcher:
    async def match_guidelines(
        self,
        context: EngineContext,
        active_journeys: Sequence[Journey],
        guidelines: Sequence[Guideline],
    ) -> GuidelineMatchingResult:
        # 1. 按策略分组
        # 2. 创建批次
        # 3. 并行执行匹配
        # 4. 返回结果
```

**代码位置**: `src/parlant/core/engines/alpha/guideline_matching/guideline_matcher.py:197`

### 匹配结果：GuidelineMatch

```python
@dataclass(frozen=True)
class GuidelineMatch:
    guideline: Guideline           # 匹配的 guideline
    score: int                     # 匹配分数 (0-10)
    rationale: str                 # 匹配原因解释
    metadata: Mapping[str, JSONSerializable]  # 额外的元数据
```

**例子**：
```python
GuidelineMatch(
    guideline=pricing_guideline,
    score=9,  # 高度匹配
    rationale="客户明确询问了产品价格",
    metadata={"journey_path": ["1", "2"]}
)
```

### 匹配上下文：GuidelineMatchingContext

匹配器会获得完整的对话上下文：

```python
@dataclass(frozen=True)
class GuidelineMatchingContext:
    agent: Agent                   # 当前 agent
    session: Session               # 会话信息
    customer: Customer             # 客户信息
    context_variables: Sequence[...]  # 上下文变量
    interaction_history: Sequence[Event]  # 对话历史
    terms: Sequence[Term]          # 术语表
    capabilities: Sequence[Capability]  # 可用能力
    staged_events: Sequence[EmittedEvent]  # 已触发的事件
    active_journeys: Sequence[Journey]  # 活跃的 journeys
    journey_paths: dict[JourneyId, list[Optional[str]]]  # Journey 路径
```

## 两种匹配策略

### 1. 通用匹配策略 (Generic Matching Strategy)

**使用 LLM 进行智能匹配**

```python
class GenericGuidelineMatchingStrategy:
    # 使用 LLM 理解 condition 和对话上下文
    # 自动判断是否匹配
```

**批次类型**：

| 批次类型 | 用途 | 代码位置 |
|---------|------|----------|
| ObservationalBatch | 处理观察型 guidelines | `observational_batch.py` |
| ActionableBatch | 处理未使用过的行动型 guidelines | `guideline_actionable_batch.py` |
| PreviouslyAppliedActionableBatch | 处理已使用过的 guidelines | `guideline_previously_applied_actionable_batch.py` |
| PreviouslyAppliedActionableCustomerDependentBatch | 处理依赖客户输入的已使用 guidelines | `guideline_previously_applied_actionable_customer_dependent_batch.py` |
| DisambiguationBatch | 消除多个匹配之间的歧义 | `disambiguation_batch.py` |
| JourneyNodeSelectionBatch | 选择 Journey 的下一步 | `journey/journey_next_step_selection.py` |

**例子**：
```python
guideline = await agent.create_guideline(
    condition="客户想要咨询产品",
    action="询问客户对哪个产品感兴趣"
)
# LLM 会理解 "客户想要咨询产品" 可以匹配：
# - "我想问一下你们的产品"
# - "能介绍一下产品吗"
# - "有什么产品推荐"
```

### 2. 自定义匹配策略 (Custom Matching Strategy)

**使用 Python 代码进行精确匹配**

```python
async def custom_matcher(
    ctx: GuidelineMatchingContext,
    guideline: Guideline
) -> GuidelineMatch:
    # 你的自定义逻辑
    if ctx.customer.name == "VIP":
        return GuidelineMatch(
            id=guideline.id,
            matched=True,
            score=10,
            rationale="VIP 客户"
        )
    else:
        return GuidelineMatch(
            id=guideline.id,
            matched=False,
            rationale="非 VIP 客户"
        )

guideline = await agent.create_guideline(
    condition="客户是 VIP",
    action="提供 VIP 专属服务",
    matcher=custom_matcher
)
```

**内置的自定义匹配器**：

```python
# 总是匹配
guideline = await agent.create_guideline(
    condition="任何情况",
    action="执行某个动作",
    matcher=Guideline.MATCH_ALWAYS
)
```

**代码位置**: `src/parlant/core/engines/alpha/guideline_matching/custom_guideline_matching_strategy.py`

## 批量匹配机制

### 批次大小策略

和 Journey 一样，Guidelines 也是**批量匹配**的：

```python
def _get_optimal_batch_size(self, guidelines: dict[GuidelineId, Guideline]) -> int:
    guideline_n = len(guidelines)

    if guideline_n <= 10:
        return 1      # 10个或以下：每次1个
    elif guideline_n <= 20:
        return 2      # 11-20个：每次2个
    elif guideline_n <= 20:
        return 3      # 21-30个：每次3个
    else:
        return 5      # 30个以上：每次5个
```

**代码位置**: `src/parlant/core/engines/alpha/guideline_matching/generic/guideline_actionable_batch.py:393-403`

### 并行处理

```python
# 创建所有批次的任务
batch_tasks = [
    self._process_guideline_matching_batch_with_retry(batch)
    for strategy_batches in batches
    for batch in strategy_batches
]

# 并行执行所有批次
batch_results = await async_utils.safe_gather(*batch_tasks)
```

**代码位置**: `src/parlant/core/engines/alpha/guideline_matching/guideline_matcher.py:249-254`

### 匹配效率示意图

```
你有 50 个 Guidelines
    ↓
按策略分组：
  - 通用策略：40 个
  - 自定义策略：10 个
    ↓
分批处理：
  通用策略 → 8 批（每批 5 个）
  自定义策略 → 2 批（每批 5 个）
    ↓
┌─────┬─────┬─────┬─────┬─────┐
│批次1│批次2│批次3│ ... │批次10│  ← 并行处理
└─────┴─────┴─────┴─────┴─────┘
    ↓     ↓     ↓     ↓     ↓
合并所有匹配结果
    ↓
返回匹配的 Guidelines（按分数排序）
```

## Guideline 的重要程度（Criticality）

### 三个级别

```python
class Criticality(Enum):
    LOW = "low"        # 低优先级
    MEDIUM = "medium"  # 中等优先级（默认）
    HIGH = "high"      # 高优先级
```

**用途**：
- 影响匹配时的优先级
- 高 criticality 的 guideline 更容易被选中
- 用于确保重要规则优先执行

**例子**：
```python
# 高优先级：安全相关
security_guideline = await agent.create_guideline(
    condition="客户要求访问敏感数据",
    action="拒绝并解释隐私政策",
    criticality=Criticality.HIGH
)

# 低优先级：闲聊
chitchat_guideline = await agent.create_guideline(
    condition="客户闲聊",
    action="友好回应",
    criticality=Criticality.LOW
)
```

## 回复生成模式（Composition Mode）

### 四种模式

```python
class CompositionMode(Enum):
    FLUID = "fluid"                      # 自然生成
    CANNED_FLUID = "canned_fluid"        # 混合模板和生成
    CANNED_COMPOSITED = "canned_composited"  # 组合多个模板
    CANNED_STRICT = "canned_strict"      # 严格使用模板
```

**代码位置**: `src/parlant/core/agents.py`

### 详细说明

#### 1. FLUID（流畅模式）

AI 自由生成回复，不使用预定义模板。

```python
guideline = await agent.create_guideline(
    condition="客户询问产品推荐",
    action="根据客户需求推荐合适的产品",
    composition_mode=CompositionMode.FLUID
)
```

**效果**：
```
客户："我想买一部手机"
AI："好的！为了给您推荐最适合的手机，请问您的预算大概是多少呢？
     您主要用手机做什么？拍照、游戏还是日常使用？"
```

#### 2. CANNED_STRICT（严格模板模式）

严格使用预定义的模板，不做修改。

```python
canrep = await agent.create_canned_response(
    template="感谢您的咨询！我们的营业时间是 9:00-18:00。"
)

guideline = await agent.create_guideline(
    condition="客户询问营业时间",
    action="告知营业时间",
    canned_responses=[canrep],
    composition_mode=CompositionMode.CANNED_STRICT
)
```

**效果**：
```
客户："你们几点营业？"
AI："感谢您的咨询！我们的营业时间是 9:00-18:00。"
（每次都一模一样）
```

#### 3. CANNED_FLUID（混合模式）

结合模板和自然生成。

```python
guideline = await agent.create_guideline(
    condition="客户询问价格",
    action="提供价格信息",
    canned_responses=[price_template],
    composition_mode=CompositionMode.CANNED_FLUID
)
```

**效果**：
```
客户："iPhone 多少钱？"
AI："好的，让我为您查询 iPhone 的价格。
     我们目前的 iPhone 14 Pro 售价为 ¥7999。
     如果您需要了解其他型号或有任何问题，请随时告诉我。"
（模板 + 自然生成的补充）
```

#### 4. CANNED_COMPOSITED（组合模式）

从多个模板中选择和组合。

```python
guideline = await agent.create_guideline(
    condition="客户下单",
    action="确认订单",
    canned_responses=[template1, template2, template3],
    composition_mode=CompositionMode.CANNED_COMPOSITED
)
```

## Guideline 关系（Relationships）

Guidelines 之间可以定义关系，用于控制执行顺序和依赖。

### 五种关系类型

```python
class GuidelineRelationshipKind(Enum):
    ENTAILMENT = "entailment"        # 蕴含：A 匹配 → B 也应该匹配
    PRIORITY = "priority"            # 优先级：A 优先于 B
    DEPENDENCY = "dependency"        # 依赖：A 依赖 B（B 必须先执行）
    DISAMBIGUATION = "disambiguation"  # 消歧：在多个选项中选择 A
    REEVALUATION = "reevaluation"    # 重新评估：需要重新考虑
```

### 使用例子

#### 1. 优先级关系（PRIORITY）

```python
specific = await agent.create_guideline(
    condition="客户询问 iPhone 14 Pro 的价格",
    action="告知 iPhone 14 Pro 价格为 ¥7999"
)

general = await agent.create_guideline(
    condition="客户询问价格",
    action="询问客户想了解哪个产品的价格"
)

# specific 优先于 general
await specific.prioritize_over(general)
```

**效果**：
```
客户："iPhone 14 Pro 多少钱？"
→ 匹配到两个 guidelines
→ 因为 specific 优先级更高
→ 只执行 specific
AI："iPhone 14 Pro 的价格是 ¥7999。"
```

#### 2. 依赖关系（DEPENDENCY）

```python
create_order = await agent.create_guideline(
    condition="客户确认下单",
    action="创建订单"
)

collect_address = await agent.create_guideline(
    condition="客户提供了商品信息",
    action="收集收货地址"
)

# create_order 依赖 collect_address
await create_order.depend_on(collect_address)
```

**效果**：
```
如果没有先执行 collect_address
→ create_order 不会执行
→ 确保流程顺序正确
```

#### 3. 蕴含关系（ENTAILMENT）

```python
vip_greeting = await agent.create_guideline(
    condition="客户是 VIP",
    action="使用 VIP 专属问候语"
)

track_vip = await agent.create_guideline(
    condition="客户是 VIP",
    action="记录 VIP 客户访问"
)

# vip_greeting 蕴含 track_vip
await vip_greeting.entail(track_vip)
```

**效果**：
```
如果 vip_greeting 匹配
→ track_vip 也会被考虑
→ 两个都会执行
```

#### 4. 消歧关系（DISAMBIGUATION）

```python
buy_phone = await agent.create_guideline(
    condition="客户想买手机",
    action="推荐手机产品"
)

buy_computer = await agent.create_guideline(
    condition="客户想买电脑",
    action="推荐电脑产品"
)

buy_something = await agent.create_guideline(
    condition="客户想购买",
    action="询问想买什么"
)

# buy_something 在 buy_phone 和 buy_computer 之间消歧
await buy_something.disambiguate([buy_phone, buy_computer])
```

**效果**：
```
客户："我想买点东西"
→ 匹配到 buy_something
→ 但不确定是手机还是电脑
→ 执行 buy_something
AI："好的！请问您想买手机还是电脑呢？"
```

**代码位置**: `src/parlant/core/guideline_relationships.py`

## Guideline 与工具（Tools）的集成

### 工具关联

Guidelines 可以关联工具，在匹配时自动调用：

```python
# 创建 guideline 并关联工具
guideline = await agent.create_guideline(
    condition="客户询问订单状态",
    action="查询并告知订单状态"
)

# 关联工具
await guideline.associate_tool(
    service_name="order_service",
    tool_name="check_order_status"
)
```

**数据结构**：
```python
@dataclass
class GuidelineToolAssociation:
    id: GuidelineToolAssociationId
    guideline_id: GuidelineId
    tool_id: ToolId  # (service_name, tool_name)
```

**执行流程**：
```
1. Guideline 匹配成功
   ↓
2. 检查是否有关联的工具
   ↓
3. 自动调用工具
   ↓
4. 获取工具结果
   ↓
5. 使用结果生成回复
```

**代码位置**: `src/parlant/core/guideline_tool_associations.py`

## Guideline 标签（Tags）

### 标签的作用

标签用于组织和过滤 guidelines：

```python
# 创建带标签的 guidelines
sales_guideline = await agent.create_guideline(
    condition="客户询问价格",
    action="提供价格信息",
    tags=["sales", "pricing"]
)

support_guideline = await agent.create_guideline(
    condition="客户报告问题",
    action="记录问题并提供支持",
    tags=["support", "troubleshooting"]
)

# 按标签查询
sales_guidelines = await agent.list_guidelines(tags=["sales"])
```

### 特殊标签

#### Journey 标签

Journey 自动为其 guidelines 添加特殊标签：

```python
# Journey 创建的 guidelines 会有这个标签
Tag.for_journey_id(journey_id)  # 格式：journey:{journey_id}
```

**代码位置**: `src/parlant/core/tags.py`

## Guideline 元数据（Metadata）

### 常用 Metadata 字段

```python
guideline = await agent.create_guideline(
    condition="客户询问问题",
    action="回答问题",
    metadata={
        "continuous": True,              # 可以多次应用
        "customer_dependent_action_data": {
            "is_customer_dependent": True  # 依赖客户输入
        },
        "agent_intention_condition": "了解客户问题",  # 意图条件
        "internal_action": "分析问题并回答",  # 内部动作
        "custom_field": "任意值"         # 自定义字段
    }
)
```

### Metadata 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `continuous` | bool | 是否可以在同一会话中多次应用 |
| `customer_dependent_action_data` | dict | 标记为依赖客户输入的动作 |
| `agent_intention_condition` | str | Agent 意图的条件（用于内部匹配） |
| `internal_action` | str | 内部执行的动作描述 |
| `journey_node` | dict | Journey 节点信息（自动添加） |

### Journey Node Metadata

```python
{
    "journey_node": {
        "journey_id": "journey_123",
        "index": "2",
        "follow_ups": ["guideline_id_3", "guideline_id_4"],
        "condition": "客户确认",
        "path": ["1", "2"]
    }
}
```

## Guideline 生命周期钩子（Hooks）

### on_match 钩子

当 guideline 匹配时触发：

```python
async def match_handler(ctx: EngineContext, match: GuidelineMatch) -> None:
    print(f"Guideline {match.guideline.id} 匹配成功！")
    print(f"匹配分数: {match.score}")
    print(f"匹配原因: {match.rationale}")
    # 可以记录日志、更新统计等

guideline = await agent.create_guideline(
    condition="客户询问价格",
    action="提供价格信息",
    on_match=match_handler
)
```

### on_message 钩子

当 AI 生成回复后触发：

```python
async def message_handler(ctx: EngineContext, match: GuidelineMatch) -> None:
    # 获取生成的消息
    messages = [
        e for e in ctx.state.message_events
        if e.source == EventSource.AI_AGENT
    ]
    print(f"AI 回复了: {messages[-1].message}")
    # 可以进行后处理、质量检查等

guideline = await agent.create_guideline(
    condition="客户询问产品",
    action="介绍产品",
    on_message=message_handler
)
```

**代码位置**: `src/parlant/core/engines/alpha/hooks.py`

## Guideline 与 Canned Responses 集成

### 创建 Canned Response

```python
# 创建模板
canrep = await agent.create_canned_response(
    template="感谢您咨询 {product_name}。它的价格是 ¥{price}。"
)

# 创建使用模板的 guideline
guideline = await agent.create_guideline(
    condition="客户询问产品价格",
    action="提供价格信息",
    canned_responses=[canrep],
    composition_mode=CompositionMode.CANNED_STRICT
)
```

### Field Provider（字段提供器）

动态填充模板中的字段：

```python
async def provide_fields(ctx: EngineContext) -> dict[str, str]:
    # 从上下文中提取信息
    product_name = extract_product_name(ctx)
    price = await get_price(product_name)

    return {
        "product_name": product_name,
        "price": price
    }

guideline = await agent.create_guideline(
    condition="客户询问产品价格",
    action="提供价格信息",
    canned_responses=[canrep],
    composition_mode=CompositionMode.CANNED_STRICT,
    canned_response_field_provider=provide_fields
)
```

**效果**：
```
客户："iPhone 多少钱？"
→ 匹配 guideline
→ 调用 provide_fields 获取字段值
→ product_name = "iPhone", price = "5999"
→ 填充模板
AI："感谢您咨询 iPhone。它的价格是 ¥5999。"
```

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py`

## Guideline API 端点

### REST API 操作

**文件位置**: `src/parlant/api/guidelines.py`

#### 1. 创建 Guideline

```http
POST /guidelines

Request Body:
{
    "condition": "客户询问价格",
    "action": "提供价格信息",
    "description": "可选的描述",
    "criticality": "high",
    "enabled": true,
    "tags": ["sales", "pricing"],
    "metadata": {"continuous": true},
    "composition_mode": "fluid"
}

Response:
{
    "id": "guideline_123",
    "condition": "客户询问价格",
    "action": "提供价格信息",
    ...
}
```

#### 2. 列出 Guidelines

```http
GET /guidelines?tag_id=sales

Response:
[
    {
        "id": "guideline_123",
        "condition": "客户询问价格",
        ...
    },
    ...
]
```

#### 3. 获取特定 Guideline

```http
GET /guidelines/{guideline_id}

Response:
{
    "id": "guideline_123",
    "condition": "客户询问价格",
    "action": "提供价格信息",
    "relationships": [...],
    "tool_associations": [...]
}
```

#### 4. 更新 Guideline

```http
PATCH /guidelines/{guideline_id}

Request Body:
{
    "condition": "新的条件",
    "action": "新的动作",
    "enabled": false
}
```

#### 5. 删除 Guideline

```http
DELETE /guidelines/{guideline_id}
```

## Guideline 实际应用场景

### 1. 客户服务场景

```python
# 基础问候
greeting = await agent.create_guideline(
    condition="客户打招呼",
    action="友好地问候客户",
    criticality=Criticality.MEDIUM
)

# 询问营业时间
hours = await agent.create_guideline(
    condition="客户询问营业时间",
    action="告知营业时间是 9:00-18:00",
    criticality=Criticality.HIGH
)

# 投诉处理
complaint = await agent.create_guideline(
    condition="客户表达不满或投诉",
    action="表示理解并记录问题，承诺跟进",
    criticality=Criticality.HIGH,
    tags=["support", "complaints"]
)
```

### 2. 销售场景

```python
# 产品咨询
inquiry = await agent.create_guideline(
    condition="客户咨询产品",
    action="了解客户需求并推荐合适产品",
    tags=["sales"]
)

# 价格查询
pricing = await agent.create_guideline(
    condition="客户询问价格",
    action="提供准确的价格信息",
    criticality=Criticality.HIGH,
    tags=["sales", "pricing"]
)

# 促销活动
promotion = await agent.create_guideline(
    condition="客户询问优惠",
    action="介绍当前的促销活动",
    tags=["sales", "promotions"]
)
```

### 3. 技术支持场景

```python
# 问题报告
issue_report = await agent.create_guideline(
    condition="客户报告技术问题",
    action="记录问题详情并提供初步诊断",
    tags=["support", "technical"]
)

# 故障排查
troubleshoot = await agent.create_guideline(
    condition="需要排查问题",
    action="引导客户进行基础排查步骤",
    tags=["support", "troubleshooting"]
)

# 升级到人工
escalate = await agent.create_guideline(
    condition="问题无法自动解决",
    action="将问题升级到人工客服",
    criticality=Criticality.HIGH,
    tags=["support", "escalation"]
)
```

### 4. 合规性场景

```python
# 隐私保护
privacy = await agent.create_guideline(
    condition="客户询问敏感信息",
    action="拒绝提供并解释隐私政策",
    criticality=Criticality.HIGH,
    tags=["compliance", "privacy"]
)

# 数据访问
data_access = await agent.create_guideline(
    condition="客户要求访问个人数据",
    action="引导客户通过正规流程申请",
    criticality=Criticality.HIGH,
    tags=["compliance", "data"]
)
```

## Guideline 与 Journey 的关系

### Journey 自动生成 Guidelines

```python
# 创建 Journey
journey = await agent.create_journey(
    title="订单处理流程",
    conditions=["客户想下单"],
    description="完整的订单处理流程"
)

# Journey 内部自动创建 Guidelines：
# 1. 触发条件的 guideline
# 2. 每个节点的 guideline
# 3. 每个边的条件 guideline
```

### Guidelines 可以依赖 Journey

```python
# 普通 guideline 可以依赖 journey
special_offer = await agent.create_guideline(
    condition="客户在下单流程中",
    action="提醒客户当前的优惠活动"
)

# 设置依赖关系
await special_offer.depend_on(order_journey)
```

### Guidelines 可以优先于 Journey

```python
# 紧急情况下，某个 guideline 可以打断 journey
emergency = await agent.create_guideline(
    condition="系统出现紧急故障",
    action="通知客户并暂停服务",
    criticality=Criticality.HIGH
)

# 优先级高于 journey
await emergency.prioritize_over(order_journey)
```

## 核心代码架构

### Guideline 相关的主要模块

```
src/parlant/core/
├── guidelines.py                    # Guideline 核心数据结构
├── guideline_relationships.py       # Guideline 关系管理
├── guideline_tool_associations.py   # Guideline 与工具的关联
├── app_modules/guidelines.py        # Guideline 业务逻辑模块
└── engines/alpha/
    └── guideline_matching/
        ├── guideline_matcher.py           # 核心匹配器
        ├── guideline_match.py             # 匹配结果
        ├── guideline_matching_context.py  # 匹配上下文
        ├── generic/
        │   ├── observational_batch.py
        │   ├── guideline_actionable_batch.py
        │   ├── guideline_previously_applied_actionable_batch.py
        │   ├── guideline_previously_applied_actionable_customer_dependent_batch.py
        │   ├── disambiguation_batch.py
        │   └── journey/
        │       └── journey_next_step_selection.py
        └── custom_guideline_matching_strategy.py
```

### API 层

```
src/parlant/api/
└── guidelines.py  # REST API 端点
```

### 测试

```
tests/
├── sdk/test_guidelines.py           # SDK 层面的测试
└── core/unstable/engines/alpha/
    └── test_guideline_matcher.py    # 匹配器测试
```

## Guideline 最佳实践

### 1. 明确的条件

❌ **不好**：
```python
condition="客户有问题"  # 太模糊
```

✅ **好**：
```python
condition="客户询问产品价格或促销信息"  # 明确具体
```

### 2. 可操作的动作

❌ **不好**：
```python
action="帮助客户"  # 不够具体
```

✅ **好**：
```python
action="询问客户具体需要哪方面的帮助，并提供相关选项"  # 具体可执行
```

### 3. 合理使用优先级

```python
# 高优先级：安全、合规、紧急
high_priority = await agent.create_guideline(
    condition="检测到欺诈行为",
    action="立即终止交互并记录",
    criticality=Criticality.HIGH
)

# 中等优先级：常规业务
medium_priority = await agent.create_guideline(
    condition="客户询问产品",
    action="介绍产品信息",
    criticality=Criticality.MEDIUM
)

# 低优先级：闲聊、补充信息
low_priority = await agent.create_guideline(
    condition="客户闲聊天气",
    action="简短友好回应",
    criticality=Criticality.LOW
)
```

### 4. 使用标签组织

```python
# 按功能分类
sales_guideline = await agent.create_guideline(..., tags=["sales"])
support_guideline = await agent.create_guideline(..., tags=["support"])

# 按优先级分类
critical_guideline = await agent.create_guideline(..., tags=["critical"])

# 按场景分类
onboarding_guideline = await agent.create_guideline(..., tags=["onboarding"])
```

### 5. 避免冲突

```python
# 使用关系避免冲突
specific = await agent.create_guideline(
    condition="客户询问 iPhone 14 Pro 价格",
    action="告知 ¥7999"
)

general = await agent.create_guideline(
    condition="客户询问价格",
    action="询问是哪个产品"
)

# 明确优先级
await specific.prioritize_over(general)
```

## Guideline 的核心价值

| 方面 | 没有 Guideline | 有 Guideline |
|------|---------------|-------------|
| **行为控制** | AI 随机回复，不可预测 | 严格按照规则行为，可控 |
| **一致性** | 每次回复不同 | 相同情况回复一致 |
| **合规性** | 难以确保合规 | 可以定义合规规则 |
| **优先级** | 无法控制重要性 | 通过 criticality 控制 |
| **关系管理** | 规则之间独立 | 支持依赖、优先级等关系 |
| **工具集成** | 需要 AI 自己决定 | 自动关联和调用工具 |
| **定制化** | 只能用自然语言 | 支持自定义匹配逻辑 |
| **组织管理** | 难以管理大量规则 | 标签、关系、批量处理 |

## 总结

**Guideline 是 Parlant 的核心基础，它定义了 AI Agent 的所有行为规则**。

### Guideline 的三个关键特点：

1. **灵活性**: 支持通用匹配（LLM）和自定义匹配（代码）
2. **可控性**: 通过优先级、关系、元数据精确控制行为
3. **扩展性**: 可以关联工具、使用模板、定义钩子

### 核心概念回顾：

- **Condition**: 什么时候触发
- **Action**: 触发后做什么
- **Matching**: 如何判断是否触发（通用 vs 自定义）
- **Relationships**: Guidelines 之间的关系
- **Criticality**: 重要程度
- **Composition Mode**: 如何生成回复
- **Tags**: 组织和过滤
- **Metadata**: 扩展信息
- **Hooks**: 生命周期回调

### 适用场景：

- 客户服务的标准回复
- 销售流程的引导
- 技术支持的故障排查
- 合规性要求的强制规则
- 复杂业务逻辑的精确控制

**Guidelines 让 AI Agent 从"不可预测的聊天机器人"变成"可控的业务自动化工具"！**
