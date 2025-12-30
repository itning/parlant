# Parlant Composition Mode 与 Canned Response 深度讲解

## Composition Mode 是什么？

**Composition Mode（组合模式）** 是 Parlant 中控制 AI Agent **如何生成回复**的核心机制。

它决定了在**纯 LLM 生成**和**预设模板**之间如何平衡。

## 核心问题

在企业级 AI Agent 中，我们面临一个关键矛盾：

```
灵活性 vs 可控性

┌─────────────────────────────────────┐
│  纯 LLM 生成                         │
│  ✅ 灵活、自然                       │
│  ❌ 不可控、可能不合规               │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  预设模板                            │
│  ✅ 可控、合规                       │
│  ❌ 僵硬、不自然                     │
└─────────────────────────────────────┘
```

**Composition Mode 提供了多种平衡策略。**

## 四种 Composition Mode

### 模式对比总览

| 模式 | 生成方式 | 一致性 | 灵活性 | 成本 | 合规性 |
|------|---------|--------|--------|------|--------|
| **FLUID** | 纯 LLM | 低 | 最高 | 最高 | 低 |
| **CANNED_FLUID** | LLM + 模板（可回退） | 中 | 高 | 中 | 中 |
| **CANNED_COMPOSITED** | LLM 重组为模板风格 | 高 | 中 | 中 | 高 |
| **CANNED_STRICT** | 严格模板（不可回退） | 最高 | 低 | 最低 | 最高 |

**代码位置**: `src/parlant/core/agents.py:48-52`

---

## 模式 1: FLUID（流畅模式）

### 工作原理

```
客户消息 → LLM 生成回复 → 直接返回
```

- **不使用**预设模板
- 完全由 LLM 根据 Guidelines 和上下文生成
- 最自然、最灵活的对话

### 何时使用

✅ **适合场景**：
- 开放式对话
- 需要创意回答的场景
- 客户支持（需要个性化回复）
- 首次交互（探索客户需求）

❌ **不适合**：
- 金融、医疗等需要合规的场景
- 品牌话术要求严格的场景
- 需要保证一致性的场景

### 代码示例

```python
# 创建 FLUID 模式的 agent
agent = await server.create_agent(
    name="创意助手",
    description="帮助客户解决问题",
    composition_mode=CompositionMode.FLUID  # 内部是 CANNED_FLUID
)

# 不需要创建 canned responses
# 所有回复都由 LLM 生成

guideline = await agent.create_guideline(
    condition="客户询问产品推荐",
    action="根据客户需求推荐合适的产品"
)

# 对话示例
客户："我想买一部手机"
AI："当然！为了给您推荐最合适的手机，我想了解一下：
     1. 您的预算大概是多少？
     2. 您主要用手机做什么？拍照、游戏还是日常使用？
     3. 您对品牌有偏好吗？"
（每次回复都可能不同，非常自然）
```

### 优缺点

**优点**：
- ✅ 最自然的对话体验
- ✅ 高度个性化
- ✅ 能处理各种意外情况
- ✅ 无需维护大量模板

**缺点**：
- ❌ 回复不一致
- ❌ 可能偏离品牌话术
- ❌ 成本较高（每次都调用 LLM）
- ❌ 难以保证合规性

---

## 模式 2: CANNED_FLUID（平衡模式）

### 工作原理

```
客户消息
    ↓
LLM 生成草稿（draft）
    ↓
语义搜索匹配 Canned Response
    ↓
找到匹配？
    ├─ 是（相似度 ≥ 0.4）→ 使用 Canned Response
    └─ 否 → 使用 LLM 草稿
```

- **优先使用**预设模板
- **回退到** LLM 生成（如果没有匹配）
- 最佳平衡点

### 何时使用

✅ **适合场景**：
- 大多数企业应用的**默认选择**
- 有常见问题但也有个性化需求
- 品牌一致性重要但不绝对
- 成本和灵活性都需要考虑

### 代码示例

```python
# 创建 agent（默认 CANNED_FLUID）
agent = await server.create_agent(
    name="客服助手",
    composition_mode=CompositionMode.CANNED_FLUID
)

# 创建常见问题的 canned responses
营业时间_canrep = await agent.create_canned_response(
    template="我们的营业时间是周一至周五 9:00-18:00。",
    signals=["营业时间", "几点", "开门", "营业"]
)

价格_canrep = await agent.create_canned_response(
    template="{{product_name}} 的价格是 ¥{{price}}。",
    signals=["价格", "多少钱", "费用"]
)

# 关联到 guideline
await agent.create_guideline(
    condition="客户询问营业时间",
    action="告知营业时间",
    canned_responses=[营业时间_canrep.id]
)

# 对话示例 1：有匹配的模板
客户："你们几点营业？"
→ LLM 生成草稿："我们的营业时间是..."
→ 语义匹配找到 营业时间_canrep（相似度 0.95）
AI："我们的营业时间是周一至周五 9:00-18:00。"
（使用预设模板）

# 对话示例 2：没有匹配的模板
客户："你们周末有人值班吗？"
→ LLM 生成草稿："非常抱歉，我们周末不营业..."
→ 语义匹配没有找到合适模板（相似度 0.2）
AI："非常抱歉，我们周末不营业。如果您有紧急问题，
     可以通过邮件联系我们，我们会在周一尽快回复。"
（使用 LLM 草稿，更个性化）
```

### 匹配质量等级

```python
class MatchQuality:
    LOW = "low"        # 相似度低，没有好的匹配
    PARTIAL = "partial"  # 部分匹配，模板覆盖了草稿的一部分
    HIGH = "high"      # 高质量匹配，模板完全符合意图
```

**匹配阈值**：相似度 ≥ 0.4（可配置）

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:1751-1768`

### 优缺点

**优点**：
- ✅ 常见问题一致性高
- ✅ 特殊情况灵活处理
- ✅ 成本适中
- ✅ 渐进式改进（逐步添加模板）

**缺点**：
- ❌ 部分回复可能不一致
- ❌ 需要维护 canned responses
- ❌ 语义匹配可能出错

---

## 模式 3: CANNED_COMPOSITED（风格一致模式）

### 工作原理

```
客户消息
    ↓
LLM 生成草稿
    ↓
语义搜索找到相关 Canned Responses
    ↓
LLM 重组草稿，使其风格与 Canned Responses 一致
    ↓
返回重组后的回复（内容相同，风格一致）
```

- **保留草稿的语义内容**
- **采用 Canned Response 的风格和语气**
- 品牌一致性最强（不牺牲灵活性）

### 何时使用

✅ **适合场景**：
- 品牌调性要求严格
- B2C 客户服务
- 市场营销对话
- 需要统一的"声音"

### 代码示例

```python
agent = await server.create_agent(
    name="品牌助手",
    composition_mode=CompositionMode.CANNED_COMPOSITED
)

# 定义品牌风格的 canned responses
友好风格 = await agent.create_canned_response(
    template="嗨！很高兴为您服务！让我来帮您解决这个问题。"
)

专业风格 = await agent.create_canned_response(
    template="感谢您的咨询。我会立即为您处理这个请求。"
)

热情风格 = await agent.create_canned_response(
    template="太棒了！我们非常期待为您提供帮助！"
)

# 对话示例
客户："我想退货"
→ LLM 草稿："好的，我可以帮您处理退货"
→ 参考 Canned Responses 的风格
→ 重组后：
AI："嗨！我很乐意帮您处理退货。让我来为您办理这个手续。"
（内容相同，但采用了友好热情的品牌调性）

客户："订单到了吗？"
→ LLM 草稿："我帮您查询一下订单状态"
→ 重组后：
AI："感谢您的咨询。我会立即为您查询订单状态。"
（更专业的表达）
```

### 重组过程

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:1981-2043`

```python
async def _recompose(
    self,
    context: CannedResponseContext,
    draft_message: str,
    reference_messages: list[str],
) -> tuple[GenerationInfo, str]:
    # 构建 prompt：
    # "你必须表达草稿的意思，但要采用参考消息的语气、风格和用词选择"

    prompt = f"""
    草稿消息：{draft_message}

    参考风格：
    {reference_messages}

    要求：
    - 保持草稿的完整意思
    - 采用参考消息的语气和风格
    - 不要添加或删除信息
    - 不要编造任何内容
    """

    # LLM 重组
    recomposed = await self._llm.generate(prompt)
    return recomposed
```

### 优缺点

**优点**：
- ✅ 品牌调性高度一致
- ✅ 内容仍然灵活和准确
- ✅ 无需为每种情况创建模板
- ✅ 适合面向消费者的场景

**缺点**：
- ❌ 需要足够多的风格示例
- ❌ 成本较高（两次 LLM 调用：草稿 + 重组）
- ❌ 如果参考模板太少效果不佳

---

## 模式 4: CANNED_STRICT（严格模式）

### 工作原理

```
客户消息
    ↓
LLM 生成草稿
    ↓
语义搜索匹配 Canned Response
    ↓
找到匹配？
    ├─ 是 → 使用 Canned Response
    └─ 否 → 返回默认"无匹配"回复
              ⚠️ 不使用 LLM 草稿
```

- **必须使用**预设模板
- **零容忍**：没有模板 = 返回默认回复
- 最严格的合规保证

### 何时使用

✅ **适合场景**：
- 金融服务（必须使用监管批准的话术）
- 医疗咨询（法律要求精确表述）
- 法律咨询（不能有任何偏差）
- 高安全性客户交互

### 代码示例

```python
agent = await server.create_agent(
    name="金融顾问",
    composition_mode=CompositionMode.CANNED_STRICT
)

# 创建所有可能的预设回复
余额查询 = await agent.create_canned_response(
    template="您的账户余额为 ¥{{std.variables.account_balance}}。此信息截至 {{std.variables.last_update_time}}。",
    signals=["余额", "账户", "多少钱", "balance"],
    metadata={"compliance": "approved", "version": "2024-01"}
)

利率查询 = await agent.create_canned_response(
    template="您的当前年利率为 {{interest_rate}}% APY。根据监管要求，此利率已包含所有相关费用。",
    signals=["利率", "interest", "APY", "年化"],
    metadata={"compliance": "approved", "version": "2024-01"}
)

# 设置默认无匹配回复
无匹配 = await agent.create_canned_response(
    template="抱歉，我无法理解您的问题。请您换一种方式表达，或联系人工客服。"
)

# 对话示例 1：有匹配
客户："我的余额是多少？"
→ 匹配到 余额查询（相似度 0.92）
AI："您的账户余额为 ¥15,234.50。此信息截至 2024-01-15 10:30。"
（使用预批准的模板）

# 对话示例 2：没有匹配
客户："能帮我炒股吗？"
→ 没有找到匹配的 Canned Response
AI："抱歉，我无法理解您的问题。请您换一种方式表达，或联系人工客服。"
（返回默认无匹配回复，不使用 LLM 生成）
```

### 默认无匹配回复

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:81`

```python
DEFAULT_NO_MATCH_CANREP = "Not sure I understand. Could you please say that another way?"
```

你可以自定义：

```python
custom_no_match = await agent.create_canned_response(
    template="非常抱歉，这个问题超出了我的服务范围。请拨打客服热线 400-123-4567。"
)
# 系统会自动使用带有特定标记的 canned response 作为 no-match 回复
```

### Follow-Up Response（后续回复）

在 STRICT 模式下，如果一个模板只覆盖了草稿的一部分，系统可以发送**第二个回复**：

```python
# 场景
客户："我的订单到哪了？客服电话多少？"

# 第一个回复（匹配到订单查询模板）
AI："您的订单已发货，预计 3 天内送达。"

# 第二个回复（follow-up，匹配到客服电话模板）
AI："如需帮助，请拨打客服热线 400-123-4567。"
```

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:2231-2306`

### 优缺点

**优点**：
- ✅ 100% 合规保证
- ✅ 完全可控
- ✅ 成本最低（只用预设）
- ✅ 可审计（所有回复都是预批准的）

**缺点**：
- ❌ 僵硬，不灵活
- ❌ 需要为所有场景创建模板
- ❌ 维护成本高
- ❌ 无法处理意外问题

---

## Canned Response（预设回复）

### 核心定义

```python
@dataclass(frozen=True)
class CannedResponse:
    id: CannedResponseId          # 唯一ID
    creation_utc: datetime        # 创建时间
    value: str                    # Jinja2 模板
    fields: Sequence[CannedResponseField]  # 模板变量定义
    signals: Sequence[str]        # 语义匹配信号
    metadata: Mapping[str, JSONSerializable]  # 自定义元数据
    tags: Sequence[TagId]         # 标签
```

**代码位置**: `src/parlant/core/canned_responses.py:63-99`

### 字段说明

| 字段 | 类型 | 说明 | 例子 |
|------|------|------|------|
| `value` | str | Jinja2 模板字符串 | `"您的余额是 {{balance}}"` |
| `fields` | Sequence | 模板变量的文档 | `[CannedResponseField(name="balance", ...)]` |
| `signals` | Sequence[str] | 用于语义匹配的关键词 | `["余额", "账户", "钱"]` |
| `metadata` | Mapping | 自定义元数据 | `{"tone": "friendly"}` |
| `tags` | Sequence[TagId] | 分类标签 | `["financial", "account"]` |

---

## Jinja2 模板系统

### 基本语法

```jinja2
# 简单变量
"您好，{{customer_name}}"

# 标准字段（std）
"您好，{{std.customer.name}}"

# 条件
"{% if premium %}VIP客户{% else %}普通客户{% endif %}"

# 循环
"{% for item in items %}{{item}}{% endfor %}"
```

### 四种字段提供器

#### 1. Standard Field Provider（std）- 标准字段

**自动可用**，无需配置。

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:196-219`

```python
{
    "std": {
        "customer": {
            "name": "张三"
        },
        "agent": {
            "name": "AI助手"
        },
        "variables": {
            "account_balance": "15234.50",
            "last_login": "2024-01-15"
        },
        "glossary": {
            "APR": "年化利率定义...",
            "Premium": "高级会员定义..."
        }
    }
}
```

**使用示例**：

```jinja2
"您好，{{std.customer.name}}！"
"您的余额是 ¥{{std.variables.account_balance}}"
"术语解释：{{std.glossary.APR}}"
```

#### 2. Tool-Based Field Provider - 工具字段

从工具调用结果中提取字段。

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:237-265`

```python
# 工具返回格式
@tool
async def get_order_status(order_id: str):
    return {
        "status": "已发货",
        "tracking_number": "SF123456789",
        "canned_response_fields": {  # 专门用于 canned response
            "order_status": "已发货",
            "tracking_number": "SF123456789",
            "delivery_date": "2024-01-20"
        }
    }

# Canned Response 模板
template = "您的订单{{order_status}}，快递单号：{{tracking_number}}，预计{{delivery_date}}送达。"
```

#### 3. Additional Field Provider - 额外字段

从 Guideline 的自定义字段提供器中获取。

```python
# 定义字段提供器函数
async def provide_custom_fields(ctx: EngineContext) -> dict[str, Any]:
    return {
        "lucky_number": 42,
        "special_offer": "九折优惠"
    }

# 创建 guideline 时关联
guideline = await agent.create_guideline(
    condition="客户询问优惠",
    action="告知优惠",
    canned_responses=[canrep_id],
    canned_response_field_provider=provide_custom_fields
)

# 模板使用
template = "您的幸运数字是 {{lucky_number}}，当前有{{special_offer}}！"
```

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:268-280`

#### 4. Generative Field Provider - 生成字段

由 LLM 动态生成字段值。

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:288-446`

```jinja2
# 模板
"根据您的情况，{{generative.personalized_recommendation}} 可能对您有帮助。"

# LLM 会根据上下文生成 personalized_recommendation 的值
# 例如："我建议您升级到高级会员"
```

**使用场景**：
- 个性化推荐
- 动态解释
- 根据上下文生成的内容

### 字段提取顺序

```
尝试 Standard → 尝试 Tool-Based → 尝试 Additional → 尝试 Generative
                                                            ↓
                                                       任何成功 → 使用该值
                                                       全部失败 → 渲染失败
```

---

## 创建 Canned Response

### 基本创建

```python
canrep = await agent.create_canned_response(
    template="您的账户余额是 ¥{{balance}}"
)
```

### 完整创建（所有参数）

```python
canrep = await agent.create_canned_response(
    template="您的账户余额是 ¥{{balance}}，上次登录时间：{{last_login}}",
    fields=[
        CannedResponseField(
            name="balance",
            description="客户的账户余额",
            examples=["9000", "15000.50", "256.30"]
        ),
        CannedResponseField(
            name="last_login",
            description="上次登录的时间",
            examples=["2024-01-15 10:30", "昨天", "3天前"]
        )
    ],
    signals=[
        "余额",
        "账户",
        "多少钱",
        "balance",
        "account"
    ],
    metadata={
        "tone": "professional",
        "department": "finance",
        "compliance_version": "2024-01"
    },
    tags=["financial", "account-info"]
)
```

### 关联到 Guideline

```python
guideline = await agent.create_guideline(
    condition="客户询问余额",
    action="提供账户余额信息",
    canned_responses=[canrep.id],
    composition_mode=CompositionMode.CANNED_STRICT
)
```

---

## 语义匹配机制

### 向量嵌入

每个 Canned Response 创建**多个向量**：

```python
canrep = CannedResponse(
    value="您的余额是 {{balance}}",
    signals=["余额", "账户", "钱"]
)

# 创建 4 个向量：
# 1. "您的余额是 {{balance}}"
# 2. "余额"
# 3. "账户"
# 4. "钱"
```

**代码位置**: `src/parlant/core/canned_responses.py:482-504`

### 匹配流程

```
1. LLM 生成草稿
   ↓
2. 将草稿转换为向量
   ↓
3. 在向量数据库中搜索相似的 Canned Responses
   ↓
4. 返回前 K 个最相似的（默认 30 个）
   ↓
5. 过滤：相似度 ≥ 阈值（默认 0.4）
   ↓
6. LLM 选择最佳匹配
   ↓
7. 渲染模板（填充字段）
   ↓
8. 返回渲染后的回复
```

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:1751-1768`

### 相似度计算

```python
# 向量搜索返回 distance（距离）
# 转换为相似度分数
similarity_score = 1 - distance

# 例如：
# distance = 0.1 → similarity = 0.9（高度相似）
# distance = 0.6 → similarity = 0.4（阈值边缘）
# distance = 0.8 → similarity = 0.2（不相似）
```

---

## Composition Mode 层次结构

### 最严格优先原则

当多个 Composition Mode 同时存在时，**最严格的获胜**。

```
严格程度（从高到低）：
CANNED_STRICT > CANNED_COMPOSITED > CANNED_FLUID > FLUID
```

### 四个层级

```
1. Agent 层级（最低优先级）
   ↓
2. Journey 层级
   ↓
3. Journey Node 层级
   ↓
4. Guideline 层级（最高优先级）
```

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:579-612`

### 解析示例

```python
# Agent 默认 FLUID
agent = await server.create_agent(
    name="助手",
    composition_mode=CompositionMode.CANNED_FLUID
)

# Guideline 1: COMPOSITED
guideline1 = await agent.create_guideline(
    condition="客户需要帮助",
    action="提供帮助",
    composition_mode=CompositionMode.CANNED_COMPOSITED
)

# Guideline 2: STRICT（更严格）
guideline2 = await agent.create_guideline(
    condition="客户询问价格",
    action="告知价格",
    composition_mode=CompositionMode.CANNED_STRICT
)

# 当两个 guidelines 同时匹配时：
客户："我需要帮助，想问问价格"
→ guideline1 匹配（COMPOSITED）
→ guideline2 匹配（STRICT）
→ 最终使用：STRICT（最严格）
```

---

## 实际应用场景

### 场景 1：金融服务（STRICT）

```python
agent = await server.create_agent(
    name="银行助手",
    composition_mode=CompositionMode.CANNED_STRICT
)

# 创建所有预批准的回复
余额查询 = await agent.create_canned_response(
    template="您的账户余额为 ¥{{std.variables.account_balance}}。此信息截至 {{std.variables.update_time}}。",
    signals=["余额", "账户", "balance"],
    metadata={"compliance": "approved_2024_v1"}
)

利率查询 = await agent.create_canned_response(
    template="您的当前利率为 {{std.variables.interest_rate}}% APY。根据监管要求，此利率已包含所有费用。",
    signals=["利率", "interest", "APR"],
    metadata={"compliance": "approved_2024_v1"}
)

转账确认 = await agent.create_canned_response(
    template="转账 ¥{{amount}} 至 {{recipient}} 需要您的确认。请输入验证码。",
    signals=["转账", "汇款", "transfer"],
    metadata={"compliance": "approved_2024_v1", "security": "high"}
)

# 好处：
# - 100% 使用预批准话术
# - 符合金融监管要求
# - 可审计
# - 零风险
```

### 场景 2：电商客服（COMPOSITED）

```python
agent = await server.create_agent(
    name="购物助手",
    composition_mode=CompositionMode.CANNED_COMPOSITED
)

# 定义品牌语气的示例
友好热情 = await agent.create_canned_response(
    template="嗨！很高兴为您服务！我会马上帮您处理这个问题。"
)

专业礼貌 = await agent.create_canned_response(
    template="感谢您的咨询。我很乐意为您提供帮助。"
)

关怀体贴 = await agent.create_canned_response(
    template="我完全理解您的感受。让我来为您解决这个问题。"
)

# 对话示例
客户："我的订单还没到"
→ LLM 草稿："我可以帮您查询订单状态"
→ 重组为品牌语气：
AI："我完全理解您的着急心情。让我马上为您查询订单状态。"
（内容准确，语气符合品牌）
```

### 场景 3：技术支持（FLUID）

```python
agent = await server.create_agent(
    name="技术支持",
    composition_mode=CompositionMode.CANNED_FLUID
)

# 创建常见问题的模板
密码重置 = await agent.create_canned_response(
    template="我已发送密码重置链接到您的邮箱 {{std.customer.email}}。请在 15 分钟内完成重置。",
    signals=["密码", "重置", "忘记"]
)

# 但对于复杂的技术问题，使用 LLM 生成
复杂问题_guideline = await agent.create_guideline(
    condition="客户遇到技术故障",
    action="提供详细的故障排查步骤"
    # 不指定 canned_responses，LLM 自由生成
)

# 效果：
# - 常见问题：快速、一致的模板回复
# - 复杂问题：个性化的详细指导
# - 最佳平衡
```

### 场景 4：医疗咨询（STRICT + 专业术语）

```python
agent = await server.create_agent(
    name="医疗助手",
    composition_mode=CompositionMode.CANNED_STRICT
)

# 定义医疗术语
术语_BMI = await agent.create_term(
    name="BMI",
    description="身体质量指数，计算公式：体重(kg) / 身高(m)²"
)

# 创建合规的医疗回复
BMI_解释 = await agent.create_canned_response(
    template="您的 {{std.glossary.BMI}} 为 {{bmi_value}}。正常范围是 18.5-24。",
    signals=["BMI", "体重指数", "肥胖"],
    metadata={"medical_compliance": "approved", "risk_level": "low"}
)

用药指导 = await agent.create_canned_response(
    template="请按医嘱服用 {{medication}}，每日 {{dosage}}。如有不适请立即就医。",
    signals=["用药", "medication", "服药"],
    metadata={"medical_compliance": "approved", "risk_level": "high"}
)

# 严格模式确保：
# - 只使用医学审批的表述
# - 不会给出未经审查的医疗建议
# - 法律风险最小化
```

---

## 最佳实践

### 1. 选择合适的模式

**决策树**：

```
需要 100% 合规？
├─ 是 → CANNED_STRICT
└─ 否 ↓

品牌语气非常重要？
├─ 是 → CANNED_COMPOSITED
└─ 否 ↓

有常见问题但也需要灵活性？
├─ 是 → CANNED_FLUID（推荐）
└─ 否 → FLUID
```

### 2. Canned Response 设计

#### ✅ 好的模板

```jinja2
# 简洁、专注
"您的订单已发货，快递单号：{{tracking_number}}"

# 使用标准字段
"您好，{{std.customer.name}}！"

# 提供充足的 signals
signals=["订单", "发货", "物流", "快递", "tracking"]
```

#### ❌ 不好的模板

```jinja2
# 太长、太复杂
"您好，{{std.customer.name}}，感谢您的咨询，我们已经收到..."

# 缺少 signals
signals=["订单"]  # 太少

# 硬编码具体值
"您的订单已发货，快递单号：SF123456"  # 应该用变量
```

### 3. Signals 设计

```python
# ✅ 好的 signals
signals=[
    "余额",           # 主要词
    "账户余额",       # 常用短语
    "多少钱",         # 口语化
    "balance",        # 英文
    "account balance" # 英文短语
]

# ❌ 不好的 signals
signals=["余额"]  # 太少，匹配范围窄
```

### 4. 字段提供器

```python
# ✅ 好的字段提供器
async def provide_fields(ctx: EngineContext) -> dict[str, Any]:
    # 从工具结果提取
    balance = extract_balance(ctx.state.tool_events)

    # 从上下文变量获取
    customer_tier = get_variable(ctx, "customer_tier")

    return {
        "balance": balance,
        "tier": customer_tier
    }

# ❌ 不好的字段提供器
async def provide_fields(ctx: EngineContext) -> dict[str, Any]:
    return {
        "balance": "1000"  # 硬编码，没有动态获取
    }
```

### 5. 模式组合

```python
# Agent 默认 FLUID（灵活）
agent = await server.create_agent(
    composition_mode=CompositionMode.CANNED_FLUID
)

# 关键信息用 STRICT（合规）
价格_guideline = await agent.create_guideline(
    condition="客户询问价格",
    action="告知价格",
    composition_mode=CompositionMode.CANNED_STRICT,
    canned_responses=[price_canrep]
)

# 品牌信息用 COMPOSITED（语气一致）
欢迎_guideline = await agent.create_guideline(
    condition="客户打招呼",
    action="友好问候",
    composition_mode=CompositionMode.CANNED_COMPOSITED,
    canned_responses=[greeting_canrep]
)

# 技术问题用 FLUID（灵活）
技术_guideline = await agent.create_guideline(
    condition="客户遇到技术问题",
    action="提供技术支持"
    # 不指定 composition_mode，使用 agent 默认
)
```

---

## 性能优化

### 1. 向量搜索优化

```python
# 限制候选数量
max_candidates = 30  # 默认值，可调整

# 提高相似度阈值（更严格的匹配）
similarity_threshold = 0.4  # 默认值
# 更高的阈值 = 更精确的匹配，但可能找不到结果

# 更低的阈值 = 更多匹配，但可能不准确
```

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:1751-1768`

### 2. 缓存

```python
# 模板字段缓存（自动）
self._cached_response_fields: dict[CannedResponseId, set[str]] = {}

# 避免重复解析 Jinja2 模板
```

**代码位置**: `src/parlant/core/engines/alpha/canned_response_generator.py:526`

### 3. 批量操作

```python
# 并行渲染多个 canned responses
rendered_canreps = await self._render_responses(
    context=context,
    responses=relevant_canreps,  # 批量渲染
)
```

---

## API 端点

### REST API

**文件位置**: `src/parlant/api/canned_responses.py`

```http
# 创建
POST /canned_responses
{
  "value": "您的余额是 {{balance}}",
  "fields": [...],
  "signals": ["余额", "账户"],
  "tags": ["financial"],
  "metadata": {"tone": "professional"}
}

# 读取
GET /canned_responses/{id}

# 更新
PUT /canned_responses/{id}

# 删除
DELETE /canned_responses/{id}

# 列出
GET /canned_responses

# 标签管理
POST /canned_responses/{id}/tags
DELETE /canned_responses/{id}/tags/{tag_id}
```

---

## 核心价值总结

| 方面 | FLUID | CANNED_FLUID | CANNED_COMPOSITED | CANNED_STRICT |
|------|-------|-------------|-------------------|--------------|
| **灵活性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| **一致性** | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **合规性** | ⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **成本** | 高 | 中 | 中 | 低 |
| **维护成本** | 低 | 中 | 中 | 高 |
| **适用场景** | 开放对话 | 大多数企业应用 | 品牌一致性 | 高度监管 |

## 技术架构总结

```
┌─────────────────────────────────────────────────────┐
│            Composition Mode 系统                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. 生成草稿（LLM）                                  │
│     - 考虑 Guidelines                               │
│     - 考虑上下文和历史                               │
│     - 生成初步回复                                   │
│                                                     │
│  2. 解析 Composition Mode                           │
│     - 检查 Agent、Guideline、Journey 级别            │
│     - 选择最严格的模式                               │
│                                                     │
│  3. 根据模式处理                                     │
│     ┌─────────────────────────────────────────┐    │
│     │ FLUID:                                  │    │
│     │   → 直接使用草稿                        │    │
│     ├─────────────────────────────────────────┤    │
│     │ CANNED_FLUID:                           │    │
│     │   → 语义搜索匹配 Canned Response        │    │
│     │   → 找到 → 使用模板                     │    │
│     │   → 未找到 → 使用草稿                   │    │
│     ├─────────────────────────────────────────┤    │
│     │ CANNED_COMPOSITED:                      │    │
│     │   → 找到相关 Canned Responses           │    │
│     │   → 重组草稿以匹配其风格                │    │
│     ├─────────────────────────────────────────┤    │
│     │ CANNED_STRICT:                          │    │
│     │   → 语义搜索匹配 Canned Response        │    │
│     │   → 找到 → 使用模板                     │    │
│     │   → 未找到 → 使用默认无匹配回复         │    │
│     └─────────────────────────────────────────┘    │
│                                                     │
│  4. 渲染模板                                        │
│     - 提取字段（std, tool, additional, generative）│
│     - 填充 Jinja2 模板                              │
│     - 返回最终回复                                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 结论

**Composition Mode 和 Canned Response 是 Parlant 平衡灵活性和可控性的核心机制。**

### 核心特点：

1. **四种模式**：从完全灵活到完全控制
2. **智能匹配**：基于向量嵌入的语义搜索
3. **Jinja2 模板**：强大的动态内容系统
4. **多级字段提供器**：灵活的数据源
5. **层次化解析**：最严格优先原则

### 选择建议：

- **FLUID**：原型开发、创意对话
- **CANNED_FLUID**：大多数企业应用（**推荐默认**）
- **CANNED_COMPOSITED**：品牌一致性关键
- **CANNED_STRICT**：金融、医疗、法律等高监管行业

**Composition Mode 让 AI Agent 既能自然对话，又能合规可控！**
