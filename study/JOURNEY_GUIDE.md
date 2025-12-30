# Parlant Journey 深度讲解

## Journey 是什么？

**Journey（旅程）** 是 Parlant 中用于**管理多步骤对话流程**的核心概念。可以理解为一个**对话状态机**或**工作流引擎**。

## 简单类比

想象你去银行办理贷款：

```
传统方式（没有 Journey）：
客户："我想办贷款"
AI：随机回复，可能漏掉重要步骤

使用 Journey：
步骤1 → 询问贷款金额
步骤2 → 询问收入证明
步骤3 → 检查信用记录
步骤4 → 给出审批结果

→ 确保不会漏掉任何步骤！
```

## Journey 的结构

### 核心组成部分

```python
@dataclass(frozen=True)
class Journey:
    id: JourneyId                      # 旅程ID
    title: str                         # 名称，比如 "贷款申请流程"
    description: str                   # 详细描述
    conditions: Sequence[GuidelineId]  # 触发条件（什么情况下启动这个旅程）
    root_id: JourneyNodeId            # 起始节点
    tags: Sequence[TagId]              # 标签
```

**代码位置**: `src/parlant/core/journeys.py`

### Journey 由三部分组成

#### 1. 节点（JourneyNode）- 每个步骤

```python
@dataclass(frozen=True)
class JourneyNode:
    id: JourneyNodeId
    action: str           # 这一步要做什么，比如 "询问客户姓名"
    tools: Sequence[ToolId]  # 这一步可以用哪些工具
    description: str      # 描述
```

#### 2. 边（JourneyEdge）- 步骤之间的转换

```python
@dataclass(frozen=True)
class JourneyEdge:
    source: JourneyNodeId     # 从哪个节点
    target: JourneyNodeId     # 到哪个节点
    condition: str            # 什么条件下转换，比如 "如果客户确认"
```

#### 3. 路径（Journey Path）- 当前走到哪一步了

```python
journey_path: Sequence[str | None]  # 比如 ["1", "2", "3"]
# 表示已经完成了节点1、2，现在在节点3
```

## 具体例子：订单处理流程

### 创建 Journey

```python
# 创建一个订单处理的 Journey
journey = await agent.create_journey(
    title="订单处理流程",
    conditions=["客户说想要下单", "客户询问购买"],  # 触发条件
    description="完整的订单处理流程"
)
```

### Journey 的图结构

```
                    开始
                     ↓
        ┌────────────────────────┐
        │  节点1: 询问商品名称    │
        └────────────────────────┘
                     ↓ (客户提供了商品名)
        ┌────────────────────────┐
        │  节点2: 询问数量        │
        └────────────────────────┘
                     ↓ (客户提供了数量)
        ┌────────────────────────┐
        │  节点3: 确认订单        │
        └────────────────────────┘
              ↓              ↓
        (客户确认)      (客户取消)
              ↓              ↓
        创建订单          取消流程
              ↓
            结束
```

### 实际对话流程

```
客户："我想买东西"
→ 触发 Journey 条件，启动"订单处理流程"
→ journey_path = ["1"]

AI（节点1）："请问您想买什么商品？"
客户："我要买 iPhone"
→ 节点1完成，转到节点2
→ journey_path = ["1", "2"]

AI（节点2）："好的，您要买几个 iPhone？"
客户："2个"
→ 节点2完成，转到节点3
→ journey_path = ["1", "2", "3"]

AI（节点3）："确认订单：2个 iPhone，是否下单？"
客户："确认"
→ 调用工具 create_order(product="iPhone", quantity=2)
→ 节点3完成，Journey 结束
→ journey_path = ["1", "2", "3", None]  # None 表示已退出
```

## Journey 的核心机制

### 1. 触发机制（Conditions）

Journey 的 `conditions` 字段定义了**什么时候启动这个旅程**：

```python
journey = await agent.create_journey(
    title="客户投诉处理",
    conditions=[
        "客户表达不满",
        "客户要投诉",
        "客户说产品有问题"
    ],
    description="..."
)
```

当客户说的话匹配这些条件时，自动启动 Journey。

**代码位置**: `src/parlant/core/app_modules/journeys.py:create()`

### 2. 步骤完成判断

每个节点有不同的完成条件：

```python
class JourneyNodeKind(Enum):
    CHAT = "chat"      # 需要 AI 说话 → 客户回复后完成
    TOOL = "tool"      # 需要执行工具 → 工具执行后完成
    FORK = "fork"      # 分支节点 → 立即根据条件选择路径
```

**代码位置**: `src/parlant/core/engines/alpha/guideline_matching/generic/journey/journey_next_step_selection.py`

**例子**：
```
节点类型: CHAT
action: "询问客户的邮箱地址"

完成条件：客户回复消息后，这个节点就完成了
→ 系统会检查客户是否提供了邮箱
→ 如果提供了，转到下一步
→ 如果没提供，可能重复询问或走其他分支
```

### 3. 条件转换（Edge Conditions）

节点之间的转换可以有条件：

```python
# 从节点3到节点4的边
edge = JourneyEdge(
    source="node_3",
    target="node_4",
    condition="如果客户确认购买"
)

# 从节点3到节点5的边
edge = JourneyEdge(
    source="node_3",
    target="node_5",
    condition="如果客户取消"
)
```

**流程图**：
```
节点3: 询问是否确认
    ├─→ 客户确认 → 节点4: 创建订单
    └─→ 客户取消 → 节点5: 取消流程
```

### 4. Journey 和 Guidelines 的关系

关键点：**Journey 会被自动转换成 Guidelines**！

```python
# Journey 内部机制
class JourneyGuidelineProjection:
    async def project_journey_to_guidelines(
        self,
        journey_id: JourneyId,
    ) -> Sequence[Guideline]:
        # 将 Journey 的每个节点转换成一个 Guideline
        # 每个 Guideline 包含：
        # - action: 节点的 action 字段
        # - metadata: journey 信息（节点索引、转换条件等）
```

**代码位置**: `src/parlant/core/journey_guideline_projection.py`

**例子**：
```
Journey:
  节点1: "询问商品名称"
  节点2: "询问数量"

转换成 Guidelines:
  Guideline 1:
    action: "询问商品名称"
    metadata: {
      "journey_node": {
        "journey_id": "journey_123",
        "index": 1,
        "follow_ups": ["节点2的条件"]
      }
    }

  Guideline 2:
    action: "询问数量"
    metadata: {
      "journey_node": {
        "journey_id": "journey_123",
        "index": 2
      }
    }
```

## Journey 在引擎中的执行流程

### 完整执行流程

```
1. 客户发消息："我想办贷款"
   ↓
2. 引擎匹配所有 Guidelines（包括 Journey 的触发条件）
   ↓
3. 发现匹配到 "贷款申请流程" Journey 的条件
   ↓
4. 启动 Journey，设置 journey_path = []
   ↓
5. Journey 转换成 Guidelines
   ↓
6. 执行第一个节点的 action："询问贷款金额"
   → journey_path = ["1"]
   ↓
7. 客户回复："50万"
   ↓
8. Journey 检测到节点1完成，评估转换条件
   ↓
9. 转到节点2："询问收入证明"
   → journey_path = ["1", "2"]
   ↓
10. 继续执行，直到 Journey 结束
    → journey_path = ["1", "2", "3", None]
```

### Journey 状态管理

Journey 的当前位置（`journey_path`）存储在 **GuidelineMatch 的 metadata** 中：

```python
GuidelineMatch(
    guideline=current_guideline,
    score=10,
    metadata={
        "journey_path": ["1", "2"],  # 当前在第2个节点
        "step_selection_journey_id": "journey_123",
    }
)
```

**代码位置**: `src/parlant/core/engines/alpha/guideline_matching/guideline_match.py`

这个 metadata 会在对话的多轮之间**持久化**，确保 Journey 状态不会丢失。

## Journey 的高级特性

### 1. 回溯（Backtracking）

如果客户在 Journey 中途改变主意：

```python
class JourneyBacktrackCheck:
    async def process(self) -> GuidelineMatchingBatchResult:
        # 检测客户是否还想继续当前 Journey
        # 如果不想，可以退出或回到之前的步骤
```

**代码位置**: `src/parlant/core/engines/alpha/guideline_matching/generic/journey/journey_backtrack_check.py`

**例子**：
```
Journey 执行中：
  节点1 → 节点2 → 节点3（当前）

客户突然说："算了，我不想买了"
→ Backtrack 检测到客户想退出
→ journey_path = ["1", "2", "3", None]  # 退出 Journey
→ 回到普通对话模式
```

### 2. 工具集成

Journey 节点可以指定可用的工具：

```python
node = JourneyNode(
    action="检查客户的信用记录",
    tools=["check_credit_score"],  # 这个节点可以调用的工具
)
```

当执行到这个节点时，AI 会自动调用 `check_credit_score` 工具。

### 3. 可视化

Parlant 可以生成 Mermaid 图来可视化 Journey：

```
GET /journeys/{journey_id}/mermaid

返回：
stateDiagram-v2
    [*] --> 询问商品
    询问商品 --> 询问数量: 客户提供商品
    询问数量 --> 确认订单: 客户提供数量
    确认订单 --> 创建订单: 客户确认
    确认订单 --> 取消: 客户取消
    创建订单 --> [*]
    取消 --> [*]
```

**代码位置**: `src/parlant/api/journeys.py`

## Journey 的批量匹配机制

当系统中有多个 Journey 时，它们的触发条件（conditions）会被**批量匹配**，就像普通的 Guidelines 一样。

### 批量大小策略

根据 Journey 数量动态调整：

```python
def _get_optimal_batch_size(self, guidelines: dict[GuidelineId, Guideline]) -> int:
    guideline_n = len(guidelines)

    if guideline_n <= 10:
        return 1      # 10个或以下：每次1个
    elif guideline_n <= 20:
        return 2      # 11-20个：每次2个
    elif guideline_n <= 30:
        return 3      # 21-30个：每次3个
    else:
        return 5      # 30个以上：每次5个
```

**代码位置**: `src/parlant/core/engines/alpha/guideline_matching/generic/guideline_actionable_batch.py:393-403`

### 并行处理

所有批次会**并行**发送给 LLM 处理：

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

**例子**：
```
你有 50 个 Journeys（每个 Journey 的 conditions 都是 Guidelines）
    ↓
分成 10 批（每批 5 个）
    ↓
┌─────────┬─────────┬─────────┬─────────┐
│  批次1  │  批次2  │  批次3  │   ...   │  ← 并行处理
│ (1-5)   │ (6-10)  │ (11-15) │  (46-50)│
└─────────┴─────────┴─────────┴─────────┘
    ↓         ↓         ↓         ↓
  结果1     结果2     结果3      结果10
    └──────────┴──────────┴──────────┘
                   ↓
          合并所有匹配结果
                   ↓
     返回匹配的 Journey 条件
                   ↓
          启动对应的 Journey
```

## Journey 的实际用途

### 企业级应用场景

#### 1. 客户入职流程

```python
journey = await agent.create_journey(
    title="客户入职流程",
    conditions=["客户说要注册", "新用户注册"],
    description="""
    1. 收集基本信息（姓名、邮箱）
    2. 验证身份（发送验证码）
    3. 创建账户
    4. 发送欢迎邮件
    """
)
```

```
节点1: 收集基本信息
  ↓
节点2: 验证身份（调用 send_verification_code 工具）
  ↓
节点3: 创建账户（调用 create_account 工具）
  ↓
节点4: 发送欢迎邮件（调用 send_email 工具）
  ↓
结束
```

#### 2. 技术支持升级路径

```python
journey = await agent.create_journey(
    title="技术支持流程",
    conditions=["客户报告问题", "客户需要帮助"],
    description="""
    1. 了解问题详情
    2. 尝试基础解决方案
    3. 如果未解决，转人工客服
    """
)
```

```
节点1: 了解问题
  ↓
节点2: 尝试基础解决方案
  ├─→ 问题解决 → 结束
  └─→ 问题未解决 → 节点3: 转人工客服
```

#### 3. 订单处理

```python
journey = await agent.create_journey(
    title="订单处理流程",
    conditions=["客户想购买", "客户下单"],
    description="""
    完整的购买流程，从选择商品到支付
    """
)
```

```
节点1: 选择商品
  ↓
节点2: 确认数量
  ↓
节点3: 填写地址
  ↓
节点4: 选择支付方式
  ↓
节点5: 创建订单（调用 create_order 工具）
  ↓
节点6: 确认订单已创建
  ↓
结束
```

#### 4. 贷款申请流程

```python
journey = await agent.create_journey(
    title="贷款申请流程",
    conditions=["客户要贷款", "申请贷款"],
    description="""
    合规的贷款申请流程，确保收集所有必要信息
    """
)
```

```
节点1: 询问贷款金额
  ↓
节点2: 询问贷款用途
  ↓
节点3: 收集收入证明
  ↓
节点4: 检查信用记录（调用 check_credit_score 工具）
  ├─→ 信用良好 → 节点5: 批准贷款
  └─→ 信用不佳 → 节点6: 拒绝贷款
  ↓
结束
```

## Process vs Utter 在 Journey 中的作用

### Process 方法与 Journey

```python
await app.sessions.process(session_id)
```

- 自动执行 Journey 的当前节点
- 根据客户消息，自动推进到下一个节点
- 会调用节点关联的工具
- 适用于正常的对话流程

**代码位置**: `src/parlant/core/engines/alpha/engine.py:177-208`

### Utter 方法与 Journey

```python
await app.sessions.utter(
    session_id,
    [UtteranceRequest(
        action="告诉客户我们正在处理",
        rationale=UtteranceRationale.BUY_TIME
    )]
)
```

- 不会自动推进 Journey
- 用于在 Journey 执行期间插入临时消息
- 适用于：争取时间、提供状态更新等

**代码位置**: `src/parlant/core/engines/alpha/engine.py:210-253`

## 核心代码架构

### Journey 相关的主要模块

```
src/parlant/core/
├── journeys.py                          # Journey 核心数据结构
├── journey_guideline_projection.py      # Journey → Guidelines 转换
├── app_modules/journeys.py              # Journey 业务逻辑模块
└── engines/alpha/
    └── guideline_matching/generic/journey/
        ├── journey_next_step_selection.py      # 选择下一步
        ├── journey_backtrack_check.py          # 回溯检查
        └── journey_backtrack_node_selection.py # 回溯节点选择
```

### API 端点

```
src/parlant/api/journeys.py

可用操作：
- POST   /journeys                    # 创建 Journey
- GET    /journeys                    # 列出所有 Journeys
- GET    /journeys/{journey_id}       # 获取特定 Journey
- GET    /journeys/{journey_id}/mermaid # 获取可视化图
- PATCH  /journeys/{journey_id}       # 更新 Journey
- DELETE /journeys/{journey_id}       # 删除 Journey
```

### 测试示例

```
tests/sdk/test_journeys.py  # SDK 层面的 Journey 测试
tests/core/unstable/engines/alpha/test_journey_*.py  # 引擎层面的测试
```

## Journey 的核心价值

| 方面 | 没有 Journey | 有 Journey |
|------|-------------|-----------|
| **对话流程** | AI 随机回复，可能漏步骤 | 严格按照预定义流程执行 |
| **一致性** | 每次对话不同 | 每次对话遵循相同流程 |
| **可控性** | 难以控制 AI 行为 | 完全控制每一步 |
| **合规性** | 难以审计 | 每一步都有记录（journey_path） |
| **复杂流程** | 难以处理多步骤流程 | 轻松管理复杂工作流 |
| **工具调用** | 需要 AI 自己决定何时调用 | 在特定步骤自动调用指定工具 |
| **状态管理** | 难以跟踪对话进度 | journey_path 清晰记录当前位置 |
| **错误恢复** | 出错后难以恢复 | 可以回溯到之前的步骤 |

## 总结

**Journey 是 Parlant 的核心特性之一，它让 AI Agent 从"随机对话机器人"变成"可控的流程自动化工具"**。

### Journey 的三个关键特点：

1. **结构化**: 通过节点和边定义清晰的对话流程
2. **可控**: 每一步都是预定义的，确保合规和一致性
3. **灵活**: 支持条件分支、工具调用、回溯等高级功能

### 适用场景：

- 需要多步骤交互的业务流程
- 需要确保合规性的金融、医疗等领域
- 需要可审计的客户服务流程
- 复杂的工作流自动化

**这对于企业级应用至关重要！**
