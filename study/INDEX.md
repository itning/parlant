# Parlant 核心概念完整指南索引

本索引汇总了 Parlant AI Agent 框架的核心概念深度讲解文档。

## 📚 已完成的深度指南

### 1. [Journey（旅程）- 多步骤对话流程](./JOURNEY_GUIDE.md)
**核心价值**: 状态机管理复杂的多步骤对话流程

- Journey 是什么？状态机式的对话流程管理
- 核心结构：Nodes（节点）、Edges（边）、Paths（路径）
- 状态管理：会话级别的持久化状态
- 引擎集成：如何在对话中加载和执行 Journey
- 实际应用：客户入职、订单处理、技术支持等场景
- 最佳实践：设计原则和常见模式

**关键特性**:
- 声明式定义对话流程
- 自动状态管理和持久化
- 语义匹配路径选择
- 支持复杂的条件分支

---

### 2. [Guideline（指南）- AI 行为规则](./GUIDELINE_GUIDE.md)
**核心价值**: 定义 AI Agent 的行为规则和响应策略

- Guideline 是什么？条件-行动模式的行为规则
- 数据结构：Condition（条件）+ Action（行动）
- 匹配策略：语义匹配、相似度阈值、批量并行处理
- 工具关联：与工具调用的集成机制
- Composition Mode：控制回复生成策略
- 与其他概念的关系：Journey、Capability、Canned Response

**关键特性**:
- 语义匹配而非关键词匹配
- 支持工具调用集成
- 可配置的 Composition Mode
- 批量并行匹配（1-5个一批）

---

### 3. [Glossary/Term（词汇表/术语）- 术语一致性](./GLOSSARY_GUIDE.md)
**核心价值**: 确保 AI Agent 使用准确、一致的业务术语

- Term 是什么？业务专用术语定义系统
- 核心结构：Name（名称）、Description（定义）、Synonyms（同义词）
- 向量嵌入：智能的语义匹配机制
- 作用域管理：全局、Agent 专用、自定义标签
- 动态加载：根据上下文加载最相关的术语
- 拼写容错：自动识别并纠正拼写错误

**关键特性**:
- 语义搜索匹配术语
- 同义词自动识别
- 拼写错误容错
- 多上下文支持（同一术语在不同 Agent 有不同定义）

**企业价值**:
- 合规性保障（金融、医疗等行业）
- 品牌术语一致性
- 避免 LLM 幻觉（使用业务定义而非训练数据定义）

---

### 4. [Capability（能力）- 服务能力描述](./CAPABILITY_GUIDE.md)
**核心价值**: 描述 AI Agent 能够提供的服务和功能

- Capability 是什么？服务能力的声明性描述
- 核心结构：Title（标题）、Description（描述）、Signals（信号）
- **Capability vs Guideline**：
  - Capability = "我能帮你做这个"（能力声明，信息性）
  - Guideline = "当遇到这种情况时必须这样做"（行为规则，规定性）
- 多向量策略：Title+Description + 每个 Signal 各创建一个向量
- 语义发现：根据对话自动加载相关 Capabilities
- 去重机制：确保每个 Capability 只出现一次

**关键特性**:
- 主动服务发现（AI 知道自己能做什么）
- 语义匹配相关服务
- 多向量提高匹配准确度
- 动态加载（最多 3 个最相关）

**企业价值**:
- 主动服务发现，减少客户困惑
- 提升客户体验（快速提供选项）
- 服务透明度（清晰展示能力）
- 多 Agent 协调和路由

---

### 5. [Composition Mode & Canned Response（组合模式与预设回复）](./COMPOSITION_MODE_GUIDE.md)
**核心价值**: 在 LLM 灵活性和预设模板可控性之间取得平衡

#### 四种 Composition Mode

| 模式 | 生成方式 | 灵活性 | 一致性 | 合规性 | 适用场景 |
|------|---------|--------|--------|--------|----------|
| **FLUID** | 纯 LLM | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | 开放式对话、创意回答 |
| **CANNED_FLUID** | LLM + 模板（可回退） | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | **大多数企业应用（推荐默认）** |
| **CANNED_COMPOSITED** | LLM 重组为模板风格 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 品牌一致性关键场景 |
| **CANNED_STRICT** | 严格模板（不可回退） | ⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 金融、医疗等高监管行业 |

#### Canned Response 系统

- **Jinja2 模板**：强大的动态内容系统
- **四种字段提供器**：
  1. Standard (std)：自动可用的标准字段
  2. Tool-based：从工具调用结果提取
  3. Additional：自定义字段提供器
  4. Generative：LLM 动态生成
- **语义匹配**：向量嵌入搜索最相关模板
- **层次化解析**：Agent → Journey → Journey Node → Guideline（最严格优先）

**关键特性**:
- 平衡灵活性与可控性
- 支持合规要求（预批准话术）
- 品牌语气一致性
- 多层级配置

**企业价值**:
- 合规保证（金融、医疗）
- 品牌一致性（B2C）
- 成本优化（模板 vs LLM）
- 可审计性（所有回复可追溯）

---

### 6. [Context Variable（上下文变量）- 动态数据注入](./CONTEXT_VARIABLE_GUIDE.md)
**核心价值**: 存储和管理客户特定的动态数据，实现个性化对话

- Context Variable 是什么？客户数据的动态存储和注入机制
- 核心结构：Name（变量名）、ToolId（关联工具）、Freshness Rules（刷新规则）
- 自动刷新：基于 Cron 表达式的智能数据更新
- 工具集成：无缝对接外部系统获取最新数据
- 值优先级：customer_id → tag:{tag_id} → DEFAULT
- 范围控制：全局、Agent 专用、标签专用

**关键特性**:
- 自动预加载客户数据到 Prompt
- 基于 Cron 的条件性数据刷新
- 工具调用自动更新机制
- 多级值存储（客户、标签、默认）

**企业价值**:
- 个性化客户体验（AI 了解客户）
- 提升运营效率（减少确认轮次）
- 数据实时性保证（自动刷新）
- 降低成本（智能缓存和按需更新）

---

## 🎯 核心概念关系图

```
┌─────────────────────────────────────────────────────────────┐
│                        Agent                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Journey (旅程)                                      │   │
│  │    ├─ Node 1 → Node 2 → Node 3                      │   │
│  │    └─ 管理多步骤对话流程                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Guideline (指南)                                    │   │
│  │    ├─ Condition: "客户询问价格"                      │   │
│  │    ├─ Action: "提供价格信息"                         │   │
│  │    ├─ Tools: [get_price]                            │   │
│  │    └─ Composition Mode: CANNED_STRICT               │   │
│  └─────────────────────────────────────────────────────┘   │
│         ↓ 引用                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Canned Response (预设回复)                          │   │
│  │    ├─ Template: "价格是 ¥{{price}}"                  │   │
│  │    ├─ Signals: ["价格", "多少钱"]                    │   │
│  │    └─ Fields: [price]                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Capability (能力)                                   │   │
│  │    ├─ Title: "查询余额"                              │   │
│  │    ├─ Description: "为客户提供账户余额信息"           │   │
│  │    └─ Signals: ["余额", "账户", "钱"]                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Glossary/Term (术语)                                │   │
│  │    ├─ Name: "APR"                                   │   │
│  │    ├─ Description: "年化利率..."                     │   │
│  │    └─ Synonyms: ["年利率", "综合利率"]               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Context Variable (上下文变量)                       │   │
│  │    ├─ Name: "AccountBalance"                        │   │
│  │    ├─ Value: {"balance": 5000.50, "currency": "USD"}│   │
│  │    ├─ Tool: fetch_balance (自动刷新)                │   │
│  │    └─ Freshness: "0 */6 * * *" (每 6 小时)          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  核心机制：                                                  │
│  • 语义匹配（Vector Embeddings）                            │
│  • 动态加载（根据上下文）                                     │
│  • 层次化配置（Agent → Journey → Guideline）                │
│  • 自动数据刷新（Context Variables + Tools）                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 快速对比：核心概念差异

| 概念 | 性质 | 主要作用 | 匹配方式 | 配置层级 |
|------|------|---------|---------|---------|
| **Journey** | 流程控制 | 管理多步骤对话状态 | 语义匹配 Conditions | Session 级别 |
| **Guideline** | 行为规则 | 规定"应该怎么做" | 语义匹配 Condition | Agent/Journey/Node |
| **Capability** | 能力声明 | 描述"能做什么" | 语义匹配 Signals | Agent/全局 |
| **Glossary** | 术语定义 | 确保术语一致性 | 语义匹配内容 | Agent/全局 |
| **Canned Response** | 预设模板 | 提供标准回复 | 语义匹配草稿 | Guideline 关联 |

---

## 🚀 典型企业场景应用

### 场景 1: 金融服务 Agent

```python
# 1. 定义术语（合规）
apr_term = await agent.create_term(
    name="APR",
    description="年化利率：包含利息和所有费用的年化借款成本"
)

# 2. 定义能力（服务发现）
balance_cap = await agent.create_capability(
    title="查询余额",
    description="为客户提供账户余额信息",
    signals=["余额", "账户", "钱"]
)

# 3. 定义指南（行为规则）
balance_guideline = await agent.create_guideline(
    condition="客户询问余额",
    action="提供账户余额，确保验证身份",
    composition_mode=CompositionMode.CANNED_STRICT  # 严格合规
)

# 4. 预设回复（合规话术）
balance_canrep = await agent.create_canned_response(
    template="您的账户余额为 ¥{{std.variables.balance}}。此信息截至 {{std.variables.update_time}}。",
    signals=["余额", "账户"]
)

# 协同工作：
# - Glossary 确保术语准确（APR 定义）
# - Capability 让 AI 知道可以提供余额查询
# - Guideline 规定必须先验证身份
# - Canned Response 确保使用合规话术
# - STRICT 模式确保 100% 使用预批准回复
```

### 场景 2: 电商客服 Agent

```python
# 1. 定义退货 Journey
return_journey = await agent.create_journey(
    title="退货流程",
    conditions=["客户要求退货"],
    nodes=[
        JourneyNode(name="确认订单"),
        JourneyNode(name="验证退货原因"),
        JourneyNode(name="生成退货单"),
    ]
)

# 2. 使用 COMPOSITED 模式保持品牌语气
guideline = await agent.create_guideline(
    condition="处理退货",
    action="按照退货流程处理",
    composition_mode=CompositionMode.CANNED_COMPOSITED  # 品牌一致性
)

# 协同工作：
# - Journey 管理退货的多步骤流程
# - COMPOSITED 模式确保语气一致
# - 内容灵活但风格统一
```

---

## 💡 设计原则和最佳实践

### 1. 选择合适的 Composition Mode

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

### 2. Guideline vs Capability

**何时使用 Guideline**:
- 需要强制执行的行为规则
- 合规要求
- 必须调用工具的场景
- 需要控制回复风格

**何时使用 Capability**:
- 主动服务发现
- 让客户知道 Agent 能做什么
- 多 Agent 路由
- 服务目录

### 3. Glossary/Term 使用建议

✅ **应该定义的术语**:
- 行业专有名词（如 "Gas", "APR"）
- 可能有歧义的词（如 "Token"）
- 需要精确定义的业务术语
- 客户常拼写错误的词

❌ **不需要定义的**:
- 通用词汇（如 "你好"）
- 不会产生歧义的日常用语

### 4. Signals 设计原则

```python
# ✅ 好的 signals（多样化、覆盖不同表达）
signals=[
    "余额",           # 主要词
    "账户余额",       # 常用短语
    "有多少钱",       # 口语化
    "balance",        # 英文
    "account balance" # 英文短语
]

# ❌ 不好的 signals（太少）
signals=["余额"]
```

---

## 🔧 技术架构核心

### 语义匹配流程（统一机制）

```
1. 用户输入/上下文
   ↓
2. 构建查询字符串
   ↓
3. 向量嵌入（Embedder）
   ↓
4. 向量数据库搜索
   ├─ Guidelines
   ├─ Capabilities
   ├─ Glossary Terms
   └─ Canned Responses
   ↓
5. 相似度排序
   ↓
6. 返回前 K 个最相关项
   ↓
7. 应用到 Prompt 或执行逻辑
```

### 向量数据库支持

- **Qdrant**（推荐）
- **Chroma**
- 其他兼容向量数据库

### 并发控制

```python
# 所有存储都使用读写锁
async with self._lock.writer_lock:
    # 写操作（创建、更新、删除）

async with self._lock.reader_lock:
    # 读操作（查询、搜索）
```

---

## 📊 代码位置速查

| 概念 | 核心定义位置 | 引擎集成位置 |
|------|------------|------------|
| **Journey** | `src/parlant/core/journeys.py:46-66` | `src/parlant/core/engines/alpha/engine.py:1642-1698` |
| **Guideline** | `src/parlant/core/guidelines.py:155-183` | `src/parlant/core/engines/alpha/guideline_resolution/` |
| **Capability** | `src/parlant/core/capabilities.py:50-61` | `src/parlant/core/engines/alpha/engine.py:1700-1716` |
| **Glossary** | `src/parlant/core/glossary.py:46-66` | `src/parlant/core/engines/alpha/engine.py:1718-1751` |
| **Canned Response** | `src/parlant/core/canned_responses.py:63-99` | `src/parlant/core/engines/alpha/canned_response_generator.py` |
| **Composition Mode** | `src/parlant/core/agents.py:48-52` | `src/parlant/core/engines/alpha/canned_response_generator.py:579-612` |

---

## 🎓 学习路径建议

### 初学者路径
1. 先理解 **Guideline**（最基础的行为控制）
2. 了解 **Composition Mode**（控制回复生成方式）
3. 学习 **Glossary**（确保术语准确）
4. 掌握 **Capability**（服务发现）
5. 最后学习 **Journey**（复杂流程管理）

### 企业应用路径
1. 根据合规需求选择 **Composition Mode**
2. 定义核心业务 **Glossary**
3. 创建 **Guidelines** 规范行为
4. 用 **Capabilities** 展示服务
5. 复杂场景使用 **Journey** 管理

---

## 📖 相关文档

- [Parlant 官网](https://parlant.io)
- [GitHub 仓库](https://github.com/emcie-co/parlant)
- API 文档位置：`src/parlant/api/`
- 测试示例：`tests/core/common/engines/alpha/`

---

## ⚠️ 重要提示

1. **所有概念都使用向量嵌入进行语义匹配**，不是关键词匹配
2. **Guideline 是规定性的**（必须遵守），**Capability 是描述性的**（可以提及）
3. **Composition Mode 有层次结构**：最严格的模式获胜
4. **动态加载**：所有内容都根据上下文动态加载，不会全部加入 Prompt
5. **批量并行处理**：Guidelines、Capabilities 等都支持批量匹配以提升性能

---

*本索引最后更新时间：2024-12-30*

*如有疑问或需要更详细的说明，请查阅各个概念的专门指南文档。*
