# HR Copilot — 公司 HR 制度智能问答系统

面向企业人力资源场景的一体化 Copilot：员工用自然语言**查制度、办事项**，HR 用同一平台**维护知识、处理待办、分析效果**。前后端分离，内置 RAG 检索、多轮对话、工单引导、公告检索与 AI 运营辅助能力。

---

## 目录

- [系统概览](#系统概览)
- [技术架构](#技术架构)
- [智能问答链路](#智能问答链路)
- [功能模块](#功能模块)
- [项目结构](#项目结构)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [演示账号](#演示账号)
- [API 模块](#api-模块)
- [前端页面与权限](#前端页面与权限)
- [在线部署](#在线部署)
- [测试与文档](#测试与文档)
- [设计要点](#设计要点)
- [已知限制与后续方向](#已知限制与后续方向)

---

## 系统概览

| 维度 | 说明 |
|------|------|
| 目标用户 | 普通员工、HR、系统管理员 |
| 核心能力 | 制度问答（RAG + 规则 + 公告）、对话式工单、知识管理、运营分析 |
| 知识来源 | **制度文档**（向量化）+ **通知公告**（关键词/时效）+ **规则库**（关键词触发） |
| AI 能力 | 小米 MiMo 大模型（问答润色、通俗解读、纠错理解、运营建议） |
| 向量检索 | Chroma + `text2vec-base-chinese` 中文 Embedding |
| 数据存储 | MySQL 8.0（业务数据）+ Chroma 本地持久化（向量） |

> **说明**：标准答案库（FAQ）已下线，知识统一维护在「制度文档」与「通知公告」中。

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                     前端 (Vue 3 + Vite)                      │
│  Chat / 知识管理 / 待办中心 / 数据看板 / ROI / 我的 …        │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST + JWT
┌───────────────────────────▼─────────────────────────────────┐
│                   后端 (FastAPI + SQLAlchemy)                  │
│  chat · documents · tickets · feedback · gaps · roi …       │
├──────────────┬──────────────────────┬─────────────────────────┤
│   MySQL      │   Chroma 向量库       │   MiMo LLM API          │
│  用户/文档/   │  文档 chunk 语义检索   │  回答生成/解读/纠错/建议  │
│  工单/问答记录 │                      │                         │
└──────────────┴──────────────────────┴─────────────────────────┘
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3、Vite、Element Plus、Pinia、Vue Router、Axios、ECharts |
| 后端 | Python 3.10+、FastAPI、SQLAlchemy、Pydantic v2 |
| 数据库 | MySQL 8.0 |
| 认证 | JWT + bcrypt |
| RAG | Chroma、sentence-transformers、`shibing624/text2vec-base-chinese` |
| 分词 | jieba |
| LLM | 小米 MiMo API（`mimo-v2.5`，可通过 `.env` 配置） |

---

## 智能问答链路

用户每条消息进入 `/api/v1/chat` 后，按优先级依次处理（简化流程）：

```mermaid
flowchart TD
    A[用户输入] --> B[AI 静默错别字纠正]
    B --> C{有待完成意图?}
    C -->|是| D[工单/公告/年假等槽位补充]
    C -->|否| E[多轮追问改写]
    E --> F{通俗解读 / 按文档名解读?}
    F -->|是| G[加载目标文档全文解读]
    F -->|否| H{入职准备等专项?}
    H -->|是| I[角色区分 / 意图澄清]
    H -->|否| J{工单意图?}
    J -->|是| K[对话式工单引导]
    J -->|否| L[公告 + 最新文档优先检索]
    L --> M[规则关键词匹配]
    M --> N[RAG 向量检索 + LLM 生成]
    N --> O{命中?}
    O -->|否| P[记录知识缺口 / 澄清]
    O -->|是| Q[返回答案 + 引用来源]
```

**关键特性：**

- **公告与新文档优先**：含日期、考勤、最新制度类问题优先动态知识，避免被旧规则覆盖
- **多轮追问**：支持「7月6日呢？」「HR准备」等上下文继承与澄清选项
- **通俗解读（FR-11）**：如「通俗解读《员工入职与转正管理办法》」，按文档名加载原文解读
- **个人权益说明**：结合员工入职日期、试用期等信息个性化解读
- **AI 静默纠错**：输入经 MiMo 理解后纠正同音字/拼音混输，不打扰用户
- **输出净化**：过滤模型思考过程泄露，截断时回退到制度原文

---

## 功能模块

### 员工端

| 模块 | 说明 |
|------|------|
| 智能问答 | 查制度 + 对话式办事项（在职证明、信息变更、考勤异常等） |
| 通知公告 | 查看、已读标记 |
| 我的 | 个人问答历史、收藏、工单摘要 |
| 反馈纠错 | 对回答标记有用/无用并提交纠错 |
| 入职引导 | 新员工清单与常见问题 |
| 到期提醒 | 试用期、合同等到期提醒 |

### HR 端

| 模块 | 说明 |
|------|------|
| 待办中心 | 工单受理、反馈处理（**按需生成** AI 处理建议，可重新生成）、知识缺口 |
| 知识管理 | 制度文档上传/发布/归档/下架，发布时自动重建向量索引 |
| 通知发布 | 公告 CRUD、置顶、有效期 |
| 规则问答 | 关键词触发式规则维护 |
| 知识缺口 | 未命中问题列表 + **AI 汇总分析面板**（按需生成、结果缓存） |
| 数据看板 | 问答趋势、类别分布、**高频提问排行**、工单状态 |
| ROI 分析 | 节省工时与等效全职 HR 估算 |

### 管理员

| 模块 | 说明 |
|------|------|
| 用户与角色 | 用户 CRUD |
| 系统配置 | 部门管理 |
| 数据维护 | 文档底层维护入口 |

### Mock / 扩展（演示）

| 模块 | 说明 |
|------|------|
| 语音/图片问答 | Mock 接口，预留 ASR/OCR 接入点 |
| 审批流 / IM 机器人 | Mock 接口 |

---

## 项目结构

```
hr-qa-system/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/                # REST 路由（chat、documents、tickets…）
│   │   ├── core/               # 配置、数据库、JWT、统一响应
│   │   ├── models/             # SQLAlchemy 模型
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   └── services/           # 业务逻辑
│   │       ├── llm.py          # MiMo 调用、回答生成、解读、建议
│   │       ├── followup_service.py    # 多轮追问
│   │       ├── ticket_flow_service.py # 工单对话流
│   │       ├── knowledge_search_service.py # 公告+文档检索
│   │       ├── typo_corrector.py      # AI 静默纠错
│   │       └── rag/            # Embedding + Chroma 向量库
│   ├── data/chroma_db/         # 向量库持久化目录（运行时生成）
│   ├── uploads/                # 上传文件目录
│   ├── init_db.py              # 数据库初始化与种子数据
│   ├── requirements.txt
│   ├── RAG_SETUP_GUIDE.md      # RAG 部署补充说明
│   ├── TEST_CASES_CHAT.md      # 问答测试用例说明
│   └── test_*.py                 # 回归测试脚本
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   ├── api/                # 接口封装
│   │   ├── stores/             # Pinia 状态
│   │   ├── components/         # 布局等公共组件
│   │   └── utils/              # markdown 渲染等工具
│   └── vite.config.js
├── docs/                       # 数据库脚本、API 文档、演示数据说明
└── README.md
```

---

## 环境要求

- **Python** 3.10+
- **Node.js** 18+（推荐 LTS）
- **MySQL** 8.0
- **curl**（后端通过 curl 调用 MiMo API，Windows/Linux 均需可用）
- 首次启动会下载 Embedding 模型（约 400MB，需网络）

---

## 快速开始

### 1. 创建数据库

```sql
CREATE DATABASE hr_copilot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 后端

```bash
cd backend
pip install -r requirements.txt
```

在 `backend/` 下创建 `.env`（见[配置说明](#配置说明)），然后：

```bash
# 初始化表结构 + 种子数据（仅首次空库执行）
python init_db.py

# 启动 API（默认 8000 端口）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动时会自动：建表、迁移增量字段、索引所有**已发布**文档到 Chroma。

可选：单独重建向量索引

```bash
python scripts/init_rag.py
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

默认访问：**http://localhost:3000**

> 注意：`frontend/vite.config.js` 中 API 代理目标为 `http://localhost:8001`。若后端运行在 **8000**，请将 `vite.config.js` 的 `proxy.target` 改为 `http://localhost:8000`，或把后端改到 8001，保持前后端一致。

### 4. 接口文档

- Swagger UI：**http://localhost:8000/docs**
- 健康检查：**http://localhost:8000/api/v1/health**

---

## 在线部署

本项目已部署到 Railway 云平台，可直接访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端** | https://fortunate-youthfulness-production-7cec.up.railway.app | Vue 3 前端应用 |
| **后端 API** | https://hr-qa-system-production.up.railway.app/api/v1 | FastAPI 后端服务 |
| **API 文档** | https://hr-qa-system-production.up.railway.app/docs | Swagger UI |

### 部署架构

- **平台**: Railway (https://railway.app)
- **前端**: 自动从 GitHub `main` 分支部署，Vite 构建
- **后端**: 自动从 GitHub `main` 分支部署，uvicorn 运行
- **数据库**: Railway 内置 MySQL 插件
- **环境变量**: 在 Railway 控制台配置（DATABASE_URL, SECRET_KEY, MIMO_* 等）

### 部署更新

推送到 GitHub `master` 分支后，Railway 会自动触发重新部署：

```bash
git push github master
```

---

## 配置说明

在 `backend/.env` 中配置（示例）：

```env
# 数据库
DATABASE_URL=mysql+pymysql://root:你的密码@localhost:3306/hr_copilot

# JWT
SECRET_KEY=your-secret-key

# 小米 MiMo（智能问答、解读、纠错、运营建议）
MIMO_API_KEY=your-mimo-api-key
MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5

# Chroma 向量库路径
CHROMA_PERSIST_DIR=./data/chroma_db

# Embedding 模型
EMBEDDING_MODEL=shibing624/text2vec-base-chinese

# 上传目录
UPLOAD_DIR=uploads
```

未配置 `MIMO_API_KEY` 时，部分 AI 能力会降级或返回占位提示。

---

## 演示账号

| 账号 | 密码 | 角色 | 典型用途 |
|------|------|------|----------|
| `emp001` | `123456` | 员工 | 智能问答、查公告、提交工单 |
| `hr001` | `123456` | HR | 知识管理、待办中心、数据看板 |
| `admin` | `123456` | 管理员 | 用户/部门/数据维护 |

种子数据包含 5 份制度文档（考勤、休假、薪酬、绩效、入职转正）、规则库条目及示例公告。

---

## API 模块

| 前缀 | 模块 | 说明 |
|------|------|------|
| `/api/v1/auth` | 认证 | 登录、注册、Token |
| `/api/v1/chat` | 智能问答 | 主对话、统计、高频问题 |
| `/api/v1/chat/conversations` | 对话管理 | 会话列表、删除 |
| `/api/v1/chat/history` | 问答历史 | 记录查询、收藏 |
| `/api/v1/documents` | 制度文档 | 上传、发布、归档、下载、分类 |
| `/api/v1/notices` | 通知公告 | 发布、已读、置顶 |
| `/api/v1/rules` | 规则问答 | CRUD |
| `/api/v1/tickets` | 工单 | 创建、受理、完成、驳回 |
| `/api/v1/feedback` | 反馈纠错 | 提交、处理、AI 建议 |
| `/api/v1/gaps` | 知识缺口 | 列表、AI 汇总分析 |
| `/api/v1/roi` | ROI 分析 | 效能报表 |
| `/api/v1/search` | 关键词搜索 | 文档全文检索 |
| `/api/v1/comments` | 评论 | 文档讨论 |
| `/api/v1/onboarding` | 入职引导 | 新员工清单 |
| `/api/v1/reminders` | 到期提醒 | 规则与日志 |
| `/api/v1/recommendations` | 推荐问句 | 首页推荐 |
| `/api/v1/users` · `/departments` | 组织管理 | 用户、部门 |
| `/api/v1/approvals` · `/bot` | Mock | 审批、IM 机器人 |

统一响应格式：`{ "code": 0, "message": "ok", "data": ... }`

---

## 前端页面与权限

| 路径 | 页面 | 角色 |
|------|------|------|
| `/chat` | 智能问答 | 全部 |
| `/dashboard` | 首页 | 全部 |
| `/search` | 关键词搜索 | 全部 |
| `/notices` | 通知公告 / 发布 | 全部 / HR |
| `/my` | 我的 | 员工 |
| `/todo` | 待办中心 | HR、Admin |
| `/knowledge` | 知识管理 | HR、Admin |
| `/documents` | 制度文档（底层维护） | HR、Admin |
| `/rules` | 规则问答 | HR |
| `/statistics` | 数据看板 | HR |
| `/roi` | ROI 分析 | HR |
| `/gaps` | 知识缺口 | HR |
| `/history` | 问答历史 | 全部 |
| `/tickets` | 工单 | 全部 |
| `/feedback` | 反馈 | 全部 |
| `/comments` | 评论讨论 | 全部 |
| `/onboarding` | 入职引导 | 全部 |
| `/reminders` | 到期提醒 | 全部 |
| `/profile` | 个人信息 | 全部 |
| `/user-management` | 用户管理 | Admin |
| `/department-management` | 部门管理 | Admin |
| `/faqs` | — | 已重定向至 `/knowledge` |

> **Admin 限制**：管理员仅可访问白名单页面（用户/部门/知识/待办/统计等），不可进入智能问答主界面。

智能问答欢迎页提供「**不知道HR智能助手可以干什么？**」入口，实时拉取**已发布**制度文档列表与能力说明。

---

## 测试与文档

| 文件 | 内容 |
|------|------|
| [backend/TEST_CASES_CHAT.md](backend/TEST_CASES_CHAT.md) | 问答场景测试用例 |
| [backend/test_cases_chat.json](backend/test_cases_chat.json) | 结构化测试数据 |
| [backend/run_chat_tests.py](backend/run_chat_tests.py) | 批量问答测试脚本 |
| [backend/RAG_SETUP_GUIDE.md](backend/RAG_SETUP_GUIDE.md) | RAG 与向量库说明 |
| [backend/ISSUES_FIX_PLAN.md](backend/ISSUES_FIX_PLAN.md) | 全模块测试修复记录 |
| [docs/api.md](docs/api.md) | 接口文档（部分） |
| [docs/database.sql](docs/database.sql) | 数据库参考脚本 |
| [HR_Copilot_用户故事文档.md](HR_Copilot_用户故事文档.md) | 需求与用户故事 |

运行问答回归（需后端已启动且配置 LLM）：

```bash
cd backend
python run_chat_tests.py
```

---

## 设计要点

1. **知识单一来源**：文档 + 公告 + 规则，废弃独立 FAQ 表，降低维护成本
2. **发布即索引**：文档发布/更新/下架时同步维护 Chroma 向量，保证 RAG 时效性
3. **对话状态机**：`conversation_state` 持久化工单/公告/年假等 pending 意图，支持多轮槽位填充
4. **AI 按需调用**：反馈建议、缺口分析、纠错等均**点击后生成**并缓存，避免浪费
5. **角色化体验**：HR 问「入职准备」直接给 HR 侧答案；员工则澄清「HR准备 / 新员工准备」
6. **Markdown 渲染**：问答、AI 建议、缺口分析等支持基础 MD 展示
7. **三端权限**：employee / hr / admin 路由与菜单隔离

---

## 已知限制与后续方向

| 项 | 说明 |
|----|------|
| LLM 依赖 curl | MiMo 通过 subprocess 调用 curl，部署环境需可用 |
| 向量库单机 | Chroma 本地持久化，未做分布式 |
| Mock 能力 | 语音、图片、审批、IM 为演示接口 |
| 响应式部署 | 生产环境 Nginx、HTTPS、多实例等待完善 |
| 搜索增强 | 可接入 Elasticsearch 做全文检索增强 |
| 企业集成 | 企业微信 / 钉钉 / 飞书消息通道 |

---

## 许可证

本项目为课程设计 / 内部演示用途，请勿将 `.env` 中的 API Key 提交至公开仓库。
