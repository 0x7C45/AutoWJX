# 自动问卷星填写系统 - 设计文档

**日期：** 2026-06-09  
**状态：** 设计阶段  
**目标用户：** 人文社科等非技术专业的小白用户

---

## 1. 项目概述

### 1.1 核心价值

为急需问卷调查数据的用户提供自动化问卷填写服务，通过 AI 推理人群分布和智能数据生成，快速产出高质量、分布合理的模拟数据。

### 1.2 目标用户画像

- **典型场景：** 人文社科研究生需要在截止日期前收集 300+ 份问卷数据
- **技术水平：** 非技术背景，熟悉问卷星操作但不会编程
- **核心需求：** 操作简单、数据真实、分布合理
- **付费意愿：** 愿意为精准人群约束付费

### 1.3 核心功能

1. **一键启动：** 输入问卷 URL + 份数即可开始
2. **智能推理：** AI 自动识别目标人群约束
3. **人群分层：** 按性别、年龄、地域等维度科学分组
4. **混合生成：** 客观题概率抽样 + 主观题 LLM 生成
5. **实时监控：** WebSocket 推送执行进度
6. **增值服务：** 支持兑换码解锁 L2 隐形约束

---

## 2. 整体架构

### 2.1 技术栈

| 层次 | 技术选型 | 选型理由 |
|------|---------|---------|
| 前端 | Vue 3 + Element Plus | 渐进式框架，中文文档完善，组件库成熟 |
| 后端 | Python FastAPI | 异步高性能，AI 生态成熟，自动生成 API 文档 |
| 任务队列 | Celery + Redis | 分布式并行任务，实时进度推送 |
| 数据库 | PostgreSQL | 关系型，支持复杂查询，适合任务记录 |
| LLM | Claude API (主) / GPT API (备) | 通过统一抽象层，支持切换 |
| 部署 | Docker + Nginx | 容器化，易于扩展和迁移 |

### 2.2 系统架构图

```
浏览器 (Vue 3)
  │ HTTP/WebSocket
  ▼
FastAPI 后端
  ├── 路由层 (/parse /stratify /execute /status /result)
  ├── 业务逻辑层
  │   ├── QuestionnaireParser    问卷解析器
  │   ├── ConstraintInferencer   约束推理器 (LLM)
  │   ├── StratificationEngine   分层引擎
  │   ├── DataGenerator          数据生成器
  │   └── RedemptionManager      兑换码管理器
  └── 任务调度层 (Celery Worker Pool)
        └── SubAgent-1 ... SubAgent-N (并行执行)

数据层
  ├── PostgreSQL  任务记录 / 兑换码 / 历史数据
  ├── Redis       消息队列 / 缓存 / 会话状态
  └── LLM API     约束推理 / 主观题生成
```

---

## 3. 核心组件设计

### 3.1 问卷解析器 (QuestionnaireParser)

**职责：** 从问卷星 URL 提取结构化题目数据

**实现策略：**
- 主路径：调用 `wjx-ai-kit` TypeScript SDK（Node.js 子进程或 HTTP 微服务）
- 备用路径：基于 `autollm_wjx` 的爬虫方案
- 跳题逻辑检测：规则匹配 + LLM 辅助推理（半自动，用户可修正）

**核心数据结构：**
```python
@dataclass
class Question:
    q_id: str
    q_index: int
    q_type: QuestionType  # SINGLE / MULTIPLE / TEXT / MATRIX
    title: str
    options: List[Option]
    is_required: bool

@dataclass
class SkipRule:
    from_question: str
    from_option: str
    action: str           # "skip_to" | "end"
    target: Optional[str]
    confidence: float     # 自动检测置信度，低于阈值提示用户确认
```

### 3.2 约束推理器 (ConstraintInferencer)

**职责：** L1 AI 推理外部约束，L2 合并用户自定义约束

**三层约束模型：**
- **L1（免费）：** LLM 从问卷标题和题目中推理人群偏向（弹性约束为主）
- **L2（增值）：** 用户手动叠加约束（城市、收入、学历等），兑换码解锁
- **L3（基线）：** 中国城市人口基线分布，兜底未约束维度

**约束覆盖优先级：**
```
最终人群 = L3基线 ∪ (L1推理 ∩ L2用户指定)
L2 > L1 > L3（高优先级覆盖低优先级同一维度）
```

### 3.3 分层引擎 (StratificationEngine)

**职责：** 执行五步分层算法，生成 subagent 分配表

**算法流程：**
1. **Step A** — 确定分层维度（只对有差异化比例的维度分层）
2. **Step B** — 确定分层粒度（连续维度离散化为 3-5 段）
3. **Step C** — 笛卡尔积生成全部分组
4. **Step D** — 精简合并（预期份数 < 5 的组合并相邻组）
5. **Step E** — 最大余数法分配份数，确保 Σquota = N

**输出：**
```python
@dataclass
class SubagentGroup:
    subagent_id: str      # "SA-1"
    quota: int
    ratio: float
    persona: Persona      # 人群画像（性别/城市/年龄/职业/收入）
    hard_constraints: Dict  # 刚性约束（题目必选项）
    answer_biases: Dict     # 答案偏好概率分布
    merged_from: Optional[List]
```

### 3.4 数据生成器 (DataGenerator)

**职责：** 混合模式生成答案

**生成策略：**
- **客观题（单选/多选）：** 概率抽样，依据 `answer_biases` 分布
- **主观题（填空/简答）：** LLM 生成，注入 persona 上下文
- **矩阵题：** 行列独立抽样

**答案一致性保障：**
- 跳题逻辑校验（生成前先检查是否应跳过）
- 刚性约束强制执行（`hard_constraints` 覆盖概率分布）
- 同一份问卷内答案语义一致性检查

### 3.5 任务执行器 (TaskExecutor)

**职责：** Celery 并行调度，安全配置，进度推送

**安全配置预设：**

| 档位 | 份间隔 | 题间隔 | 风险 |
|------|--------|--------|------|
| 保守（默认）| 3-8s | 0.5-2s | 🟢 低 |
| 标准 | 1.5-4s | 0.3-4s | 🟡 中 |
| 激进 | 0.5-1.5s | 0.1-1s | 🔴 高 |

**自动校准：**
- 凌晨 0-6 点自动降速 ×1.4
- 每 5 份插入批次休息
- 填空/矩阵题自动延长间隔

### 3.6 兑换码管理器 (RedemptionManager)

**职责：** 兑换码验证、激活、权限管理

**状态机：**
```
UNUSED → ACTIVATED → CONSUMED (一次性) / ACTIVE (订阅期内)
```

**L2 功能解锁：**
激活后解锁约束维度选择器，用户可叠加：城市/地域、收入水平、教育程度、消费行为、年龄细化、自定义维度

---

## 4. 完整数据流

### 4.1 端到端流程

```
用户输入 URL + 份数
  │
  ▼
┌─ 1. 问卷解析 (POST /api/parse)
│   → 后台异步执行，返回 task_id
│   → WebSocket 推送解析结果
│
├─ 2. L1 约束推理（自动触发）
│   → LLM 推理五大维度外部约束
│   → 微调人群模板
│   → WebSocket 推送推理结果
│
├─ 3. 前端确认点（用户交互）
│   展示：约束清单 + 分层预览 + 跳题逻辑
│   操作：[确认开始] / [L2约束] / [编辑跳题]
│
├─ 4. L2 约束（可选，POST /api/constraints）
│   → 兑换码验证
│   → 合并 L1 + L2 约束
│   → 重新分层计算
│
├─ 5. 执行分层 (POST /api/stratify)
│   → 分层算法 A-E 步骤
│   → 生成 subagent 分配表
│
├─ 6. 并行生成数据 (POST /api/execute)
│   → Celery 分发任务给 N 个 Worker
│   → 每个 Worker 执行一个 subagent 组
│   → 实时 WebSocket 推送进度
│
├─ 7. 问卷星提交
│   → wjx-ai-kit API 提交
│   → 失败重试 3 次（指数退避）
│   → 记录成功率
│
└─ 8. 结果输出 (GET /api/result/:id)
    → 统计报告（JSON）
    → 原始数据（CSV）
    → 可视化图表（前端渲染）
```

### 4.2 WebSocket 实时通信

**事件类型：**
- `parse.progress` — 解析进度
- `parse.complete` — 解析完成
- `infer.progress` — 约束推理进度
- `infer.complete` — 推理完成，展示分层预览
- `exec.start` — 开始执行
- `exec.progress` — 执行进度（subagent 级别）
- `exec.subagent_complete` — 单组完成
- `exec.complete` — 全部完成
- `error` — 错误事件

**前端订阅示例：**
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${taskId}`)
ws.onmessage = (event) => {
  const { type, data } = JSON.parse(event.data)
  switch(type) {
    case 'exec.progress':
      updateProgressBar(data.subagent_id, data.current, data.total)
      break
    case 'exec.complete':
      showResults(data.report)
      break
  }
}
```

---

## 5. 错误处理与降级

### 5.1 分层错误处理

| 场景 | 处理策略 | 降级方案 |
|------|---------|---------|
| 问卷解析失败 | wjx-ai-kit → autollm_wjx 爬虫 → 提示用户手动导入 JSON | - |
| LLM 推理失败 | Claude API → GPT API → 使用 L3 基线模板（无 L1） | 功能降级但可用 |
| 数据生成失败 | 单份失败记录日志继续；10% 失败率暂停任务 | 人工介入 |
| 问卷星提交失败 | 429 限流退避重试；403 封禁切换 IP/UA；保存本地稍后重试 | 导出 CSV 手动上传 |

### 5.2 降级示例代码

```python
class FallbackStrategy:
    async def parse_questionnaire(url):
        try:
            return await wjx_ai_kit.parse(url)
        except APIError:
            try:
                return await autollm_wjx.crawl(url)
            except CrawlerError:
                raise UserActionRequired("请手动导入问卷 JSON")
    
    async def infer_constraints(questionnaire):
        try:
            return await claude_api.infer(questionnaire)
        except ClaudeError:
            try:
                return await openai_api.infer(questionnaire)
            except OpenAIError:
                return baseline_template  # 完全降级
```

---

## 6. 用户界面设计

### 6.1 页面结构

1. **首页（问卷配置）**
   - 输入：问卷 URL、填写份数
   - 显示：解析进度、约束推理结果
   - 操作：确认开始 / L2 约束 / 编辑跳题

2. **L2 约束配置页（增值服务）**
   - 兑换码输入框
   - 约束维度选择器（多选）
   - 人群收敛可视化（从 50 万 → 10 万）

3. **执行监控页**
   - 实时进度条（总进度 + 每组进度）
   - 成功率统计
   - 操作：暂停 / 停止 / 退出监控

4. **结果页**
   - 统计图表（分布、交叉分析）
   - 数据导出（CSV / JSON）
   - 历史任务列表

### 6.2 交互要点

**小白友好设计：**
- 默认折叠技术细节，用通俗语言展示
- 操作按钮大且明显，主路径突出（绿色）
- 错误提示清晰具体，提供解决方案
- 关键步骤有引导提示（Tooltip / 新手引导）

**专业用户支持：**
- 提供"专家模式"开关，展开技术细节
- 支持编辑跳题逻辑、调整分层粒度
- 提供 API 文档供脚本调用

---

## 7. 数据模型

### 7.1 核心数据表

**tasks 表（任务记录）：**
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    url VARCHAR(500) NOT NULL,
    total_count INT NOT NULL,
    status VARCHAR(20),  -- parsing / inferring / stratifying / executing / completed / failed
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    result_data JSONB
);
```

**redemption_codes 表（兑换码）：**
```sql
CREATE TABLE redemption_codes (
    code VARCHAR(32) PRIMARY KEY,
    status VARCHAR(20),  -- unused / activated / consumed
    activated_at TIMESTAMP,
    user_id VARCHAR(100),
    quota INT,  -- 剩余可用次数
    expires_at TIMESTAMP
);
```

**subagent_results 表（子任务结果）：**
```sql
CREATE TABLE subagent_results (
    id UUID PRIMARY KEY,
    task_id UUID REFERENCES tasks(id),
    subagent_id VARCHAR(20),
    quota INT,
    success_count INT,
    fail_count INT,
    responses JSONB
);
```

---

## 8. 安全与性能

### 8.1 安全措施

- **兑换码防暴力破解：** 5 次失败锁定 IP 15 分钟
- **SQL 注入防护：** 使用 SQLAlchemy ORM 参数化查询
- **XSS 防护：** 前端输入转义，CSP 策略
- **敏感数据脱敏：** 日志中不记录完整兑换码

### 8.2 性能指标

| 指标 | 目标 | 备注 |
|------|------|------|
| 500 份问卷生成时间 | < 5 分钟 | 10 个并发 Worker |
| WebSocket 推送延迟 | < 100ms | 本地网络 |
| 并发任务支持 | 10 个不降级 | 单服务器 |
| 数据库查询响应 | < 50ms | 添加索引优化 |

### 8.3 扩展性设计

- **水平扩展：** Celery Worker 可独立扩展
- **数据库分片：** 按 task_id 哈希分库（未来）
- **LLM 负载均衡：** 多 API Key 轮询
- **CDN 静态资源：** 前端资源 CDN 加速

---

## 9. 测试策略

### 9.1 测试覆盖

**单元测试（pytest）：**
- 各组件独立测试，Mock 外部依赖
- 覆盖率目标：80%+

**集成测试：**
- 端到端流程测试（使用测试问卷 URL）
- 验证数据分布准确性（卡方检验）

**性能测试：**
- 压力测试（100 并发请求）
- 长时间运行测试（1000 份问卷）

**安全测试：**
- OWASP Top 10 漏洞扫描
- 兑换码暴力破解测试

### 9.2 测试数据

创建测试问卷：
- 5 题简单问卷（无跳题）
- 15 题复杂问卷（含跳题逻辑、矩阵题）
- 边界情况（100 题超长问卷）

---

## 10. 部署方案

### 10.1 Docker Compose 配置

```yaml
version: '3.8'
services:
  web:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://...
      REDIS_URL: redis://redis:6379
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
  
  worker:
    build: ./backend
    command: celery -A app.celery worker -l info
    depends_on: [redis, postgres]
  
  redis:
    image: redis:7-alpine
  
  postgres:
    image: postgres:15
    volumes: ["./data:/var/lib/postgresql/data"]
  
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes: ["./frontend/dist:/usr/share/nginx/html"]
```

### 10.2 环境变量

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost/autowjx
REDIS_URL=redis://localhost:6379/0
CLAUDE_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
WJX_API_KEY=...
SECRET_KEY=...
ALLOWED_ORIGINS=https://autowjx.example.com
```

---

## 11. 后续优化方向

### 11.1 短期优化（1-2 个月）

- 增加更多 LLM 提供商支持（Gemini、国产大模型）
- 优化 L1 推理 Prompt，提升准确率
- 增加问卷模板库（常见研究类型预设）
- 支持批量任务（上传多个 URL）

### 11.2 中期优化（3-6 个月）

- 引入答案质量评分系统
- 支持导入真实样本数据增强分布
- 提供 API 接口供第三方集成
- 开发移动端 H5 版本

### 11.3 长期优化（6+ 个月）

- 多租户 SaaS 化
- 自定义 LLM 微调（针对特定领域问卷）
- 引入答案逻辑一致性深度检查
- 支持国际化（多语言问卷）

---

## 12. 成本估算

### 12.1 单次任务成本（500 份问卷）

| 项目 | 单价 | 用量 | 小计 |
|------|------|------|------|
| Claude API（L1 推理）| $0.01/1K tokens | ~10K tokens | $0.10 |
| Claude API（主观题）| $0.01/1K tokens | ~5 题 × 500 × 50 tokens = 125K | $1.25 |
| 服务器成本 | $0.05/小时 | 0.1 小时 | $0.005 |
| **总计** | | | **$1.36** |

**定价策略建议：**
- 基础服务（L1）：¥10 / 500 份
- L2 增值服务：¥30 / 500 份（精准约束）
- 毛利率：~70%

---

## 附录：关键决策记录

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 前端框架 | Vue 3 | 小白用户友好，中文文档完善 |
| 后端框架 | FastAPI | 异步高性能，AI 生态成熟 |
| 任务队列 | Celery | 成熟稳定，支持并行 |
| 答案生成 | 混合模式 | 平衡成本和质量 |
| 付费模式 | 兑换码 | 降低支付集成复杂度 |
| 部署方式 | Web 服务 | 小白无需安装 |

---

**设计完成日期：** 2026-06-09  
**下一步：** 创建实施计划 (`/gsd-new-project`)
