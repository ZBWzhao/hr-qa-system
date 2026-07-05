# HR Copilot 项目对接文档（GPT 专用）

> 本文档专为 AI（如 GPT）理解项目结构设计，按「入口 → 调用链 → 数据流」组织，便于快速定位文件和分析逻辑。

---

## 一、项目概览

| 维度 | 说明 |
|------|------|
| 项目类型 | 前后端分离的 HR 智能问答系统 |
| 前端 | Vue 3 + Vite + Element Plus + Pinia |
| 后端 | Python 3.10+ + FastAPI + SQLAlchemy |
| 数据库 | MySQL 8.0（业务）+ ChromaDB（向量） |
| AI 能力 | 小米 MiMo API（LLM）+ text2vec-base-chinese（Embedding） |

---

## 二、后端文件结构与功能映射

### 2.1 API 路由层（`backend/app/api/`）

每个文件对应一个业务模块，是 HTTP 请求的入口：

| 文件 | 路由前缀 | 核心功能 | 依赖 Service 数量 |
|------|----------|----------|-------------------|
| `chat.py` | `/api/v1/chat` | **核心枢纽**：多轮对话状态机、智能问答、工单流转、公告发布 | 11 个 |
| `documents.py` | `/api/v1/documents` | 文档 CRUD、上传解析、发布→向量索引 | 1 个 |
| `tickets.py` | `/api/v1/tickets` | 工单 CRUD、状态流转 | 0 |
| `notices.py` | `/api/v1/notices` | 通知公告 CRUD、已读追踪 | 0 |
| `feedback.py` | `/api/v1/feedback` | 反馈纠错、AI 处理建议 | 1 个 |
| `gaps.py` | `/api/v1/gaps` | 知识缺口记录、AI 汇总分析 | 1 个 |
| `search.py` | `/api/v1/search` | 文档关键词搜索 | 0 |
| `rules.py` | `/api/v1/rules` | 规则问答 CRUD | 0 |
| `users.py` | `/api/v1/users` | 用户管理、批量导入 | 0 |
| `departments.py` | `/api/v1/departments` | 部门树管理 | 0 |
| `comments.py` | `/api/v1/comments` | 评论讨论、点赞采纳 | 0 |
| `conversations.py` | `/api/v1/chat/conversations` | 对话列表、消息加载 | 0 |
| `chat_history.py` | `/api/v1/chat/history` | 问答历史、收藏 | 0 |
| `onboarding.py` | `/api/v1/onboarding` | 入职引导清单 | 0 |
| `reminders.py` | `/api/v1/reminders` | 到期提醒、提醒规则 | 0 |
| `recommendations.py` | `/api/v1/recommendations` | 首页推荐问句 | 0 |
| `roi.py` | `/api/v1/roi` | ROI 分析报表 | 0 |
| `auth.py` | `/api/v1/auth` | 登录注册、JWT | 0 |
| `approvals.py` | `/api/v1/approvals` | Mock 审批流 | 0 |
| `bot.py` | `/api/v1/bot` | Mock IM 机器人 | 0 |

### 2.2 Service 业务层（`backend/app/services/`）

按架构层次从底向上排列：

#### AI 基础层

| 文件 | 定位 | 核心函数 |
|------|------|----------|
| `llm.py` | LLM 统一调用入口 | `call_mimo_api()`（底层）、`generate_answer()`、`generate_knowledge_answer()`、`analyze_intent()`、`generate_clarification()`、`extract_ticket_slots_with_ai()`、`generate_interpretation_answer()`、`generate_feedback_handling_suggestion()`、`generate_gap_analysis_summary()`、`correct_user_question_typos()`、`sanitize_user_facing_text()` |
| `rag/embedding.py` | Embedding 模型封装 | `get_embedding_model()`、`encode_text()`、`encode_texts()` |

#### 存储层

| 文件 | 定位 | 核心函数 |
|------|------|----------|
| `rag/vectorstore.py` | ChromaDB 向量库封装 | `add_documents()`、`search_similar()`、`delete_document()`、`get_collection_stats()` |

#### 检索层

| 文件 | 定位 | 核心函数 |
|------|------|----------|
| `knowledge_search_service.py` | 公告+文档统一检索 | `search_active_notices()`、`search_document_vectors()`、`search_documents_by_keyword()`、`should_prefer_dynamic_knowledge()`、`build_knowledge_context()`、`find_published_document_by_title()`、`list_published_document_titles()` |
| `text_splitter.py` | 文本分块与关键词提取 | `split_text()`、`extract_keywords()` |

#### 对话理解层

| 文件 | 定位 | 核心函数 |
|------|------|----------|
| `typo_corrector.py` | 错别字纠正 | `normalize_question_typos()` |
| `followup_service.py` | 多轮追问识别与改写 | `is_followup_question()`、`rewrite_followup_question()`、`expand_clarification_choice()`、`get_recent_context()`、`get_annual_leave_followup_answer()`、`get_seniority_welfare_followup_answer()`、`get_attendance_policy_answer()` |
| `slot_extractor.py` | 通用槽位提取 | `extract_slots_for_intent()` |

#### 工单流程层

| 文件 | 定位 | 核心函数 |
|------|------|----------|
| `ticket_intent_service.py` | 工单意图识别与配置 | `detect_ticket_intent()`、`TICKET_SLOT_CONFIG`、`build_ticket_type_selection_answer()`、`parse_ticket_type_choice()`、`is_generic_new_ticket_intent()` |
| `ticket_slot_extractor.py` | 工单槽位提取 | `extract_ticket_slots()`、`apply_single_missing_slot_fallback()` |
| `ticket_flow_service.py` | 工单多轮对话状态机 | `is_ticket_cancel_intent()`、`is_ticket_resume_intent()`、`is_ticket_modify_intent()`、`is_ticket_confirm_intent()`、`is_ticket_flow_followup()`、`is_general_question_instead_of_ticket()`、`extract_slot_field_updates()`、`build_ticket_modify_prompt()`、`build_ticket_slot_clarification()`、`answer_ticket_followup_question()`、`merge_ticket_slots()` |
| `notice_flow_service.py` | 公告发布流程 | `is_notice_publish_intent()`、`is_notice_confirm_intent()`、`is_notice_cancel_intent()`、`parse_notice_fields()`、`infer_notice_type()`、`should_pin_notice()`、`build_notice_confirm_answer()` |

#### 状态管理层

| 文件 | 定位 | 核心函数 |
|------|------|----------|
| `conversation_state_service.py` | 会话状态持久化 | `ConversationStateService` 类：`get_or_create_state()`、`set_pending_intent()`、`update_filled_slots()`、`check_slots_filled()`、`pause_ticket_for_qa()`、`resume_ticket()`、`clear_pending_intent()` |
| `auth.py` | 认证服务 | `create_user()`、`authenticate_user()`、`create_token()` |

### 2.3 数据模型层（`backend/app/models/`）

| 文件 | 表名 | 核心字段 |
|------|------|----------|
| `user.py` | `sys_user` | id, username, password_hash, role(employee/hr/admin), department_id, status |
| `document.py` | `biz_document` | id, title, content, category, status(draft/published/archived), version, keywords, file_path |
| `qa.py` | `biz_qa_record` | id, user_id, conversation_id, question, answer, source, feedback_status, source_docs |
| `ticket.py` | `biz_ticket` | id, ticket_no, user_id, type, status(pending/processing/completed/rejected), fields(JSON) |
| `notice.py` | `biz_notice` | id, title, content, type, is_pinned, valid_until, status |
| `comment.py` | `biz_comment` | id, target_type, target_id, user_id, content, parent_id, like_count, is_adopted |
| `conversation_state.py` | `biz_conversation_state` | id, user_id, conversation_id, pending_intent, required_slots(JSON), filled_slots(JSON), status |
| `department.py` | `sys_department` | id, name, parent_id, sort_order |
| `reminder.py` | `biz_reminder_rule` | id, event_type, days_before, is_active |
| `knowledge_cache.py` | `biz_knowledge_cache` | id, cache_key, cache_value(JSON), expires_at |

### 2.4 配置与核心（`backend/app/core/`）

| 文件 | 功能 |
|------|------|
| `config.py` | 环境变量配置（DATABASE_URL, SECRET_KEY, MIMO_*, CHROMA_*） |
| `database.py` | SQLAlchemy 引擎、SessionLocal、Base |
| `deps.py` | 依赖注入（get_db, get_current_user） |
| `security.py` | JWT 编解码、密码哈希 |
| `response.py` | 统一响应格式 `{code, message, data}` |

---

## 三、前端文件结构与功能映射

### 3.1 页面组件（`frontend/src/views/`）

| 文件 | 路径 | 功能 | 角色权限 |
|------|------|------|----------|
| `Chat.vue` | `/chat` | 智能问答主界面 | 全部 |
| `Search.vue` | `/search` | 关键词搜索 | 全部 |
| `ChatHistory.vue` | `/history` | 问答历史 | 全部 |
| `Dashboard.vue` | `/dashboard` | 首页仪表盘 | 全部 |
| `Notices.vue` | `/notices` | 通知公告 | 全部/HR发布 |
| `Tickets.vue` | `/tickets` | 工单系统 | 全部 |
| `Feedback.vue` | `/feedback` | 反馈纠错 | 全部 |
| `Comments.vue` | `/comments` | 评论讨论 | 全部 |
| `Onboarding.vue` | `/onboarding` | 入职引导 | 全部 |
| `Reminders.vue` | `/reminders` | 到期提醒 | 全部 |
| `Profile.vue` | `/profile` | 个人信息 | 全部 |
| `MyPage.vue` | `/my` | 我的页面 | 全部 |
| `Documents.vue` | `/documents` | 制度文档管理 | HR/Admin |
| `KnowledgeManage.vue` | `/knowledge` | 知识管理 | HR/Admin |
| `TodoCenter.vue` | `/todo` | 待办中心 | HR/Admin |
| `Rules.vue` | `/rules` | 规则问答管理 | HR |
| `Statistics.vue` | `/statistics` | 数据统计 | HR |
| `Gaps.vue` | `/gaps` | 知识缺口分析 | HR |
| `ROI.vue` | `/roi` | ROI 分析 | HR |
| `UserManagement.vue` | `/user-management` | 用户管理 | Admin |
| `DepartmentManagement.vue` | `/department-management` | 部门管理 | Admin |
| `Login.vue` | `/login` | 登录页 | 公开 |
| `Register.vue` | `/register` | 注册页 | 公开 |

### 3.2 API 封装层（`frontend/src/api/`）

| 文件 | 对应后端模块 | 主要接口 |
|------|--------------|----------|
| `auth.js` | auth | login, register, getUserInfo, updateProfile |
| `chat.js` | chat | sendMessage, saveRecord, voice, image, stats |
| `conversations.js` | chat/conversations | getConversations, getMessages, deleteConversation |
| `chatHistory.js` | chat/history | getHistory, toggleFavorite, deleteRecord |
| `documents.js` | documents | list, create, update, delete, publish, archive, download, chunks |
| `search.js` | search | search |
| `tickets.js` | tickets | list, detail, create, update, stats |
| `notices.js` | notices | list, detail, create, update, delete, unreadCount |
| `feedback.js` | feedback | create, list, handle, stats, suggestion |
| `comments.js` | comments | list, create, like, adopt, delete |
| `rules.js` | rules | list, detail, create, update, delete |
| `users.js` | users | list, create, batch, update, status, resetPassword, template |
| `departments.js` | departments | tree, flat, create, update, delete |
| `gaps.js` | gaps | create, list, stats, resolve, analysis |
| `roi.js` | roi | getReport |
| `onboarding.js` | onboarding | getChecklist, markRead |
| `reminders.js` | reminders | list, rules, createRule, updateRule |
| `recommendations.js` | recommendations | getRecommendations |

### 3.3 状态管理（`frontend/src/stores/`）

| 文件 | 功能 | 核心状态 |
|------|------|----------|
| `user.js` | 用户认证状态 | token, userInfo, isLoggedIn, role, isHR, isAdmin |
| `chat.js` | 对话状态 | groups, currentConversationId, messages, loading |

---

## 四、核心调用链路

### 4.1 智能问答完整链路（`chat.py` → 多个 Service）

```
用户输入 "7月15日考勤异常怎么处理"
    │
    ▼
[1] typo_corrector.normalize_question_typos()
    └── llm.correct_user_question_typos()  # AI纠错
    │
    ▼
[2] conversation_state_service.get_pending_state()
    └── 检查是否有待完成的工单/公告意图
    │
    ▼
[3] followup_service.is_followup_question()
    └── 判断是否为追问（标记词、短追问）
    │
    ▼ (非追问)
[4] llm.analyze_intent()
    └── AI意图分析（失败回退关键词规则）
    │
    ▼ (意图: 工单)
[5] ticket_intent_service.detect_ticket_intent()
    └── 识别工单类型（考勤异常）
    │
    ▼
[6] ticket_slot_extractor.extract_ticket_slots()
    └── llm.extract_ticket_slots_with_ai()  # AI提取槽位
    │
    ▼
[7] conversation_state_service.update_filled_slots()
    └── 持久化已填槽位
    │
    ▼
[8] ticket_flow_service.build_ticket_slot_clarification()
    └── 生成缺失槽位的澄清话术
    │
    ▼
返回响应
```

### 4.2 RAG 检索链路

```
用户问题
    │
    ▼
[1] knowledge_search_service.search_active_notices()
    └── 按关键词匹配有效公告（置顶优先）
    │
    ▼
[2] knowledge_search_service.search_document_vectors()
    └── rag/vectorstore.search_similar()
        └── rag/embedding.encode_text()  # 向量化
        └── ChromaDB 查询
    │
    ▼
[3] knowledge_search_service.should_prefer_dynamic_knowledge()
    └── 判断优先使用公告还是文档
    │
    ▼
[4] knowledge_search_service.build_knowledge_context()
    └── 组装 LLM 上下文
    │
    ▼
[5] llm.generate_answer() 或 llm.generate_knowledge_answer()
    └── 生成最终回答
    │
    ▼
[6] llm.sanitize_user_facing_text()
    └── 去除推理痕迹、截断检测
```

### 4.3 文档发布链路

```
HR 上传文档
    │
    ▼
[1] documents.py: create_document()
    └── 解析文件（txt/md/docx/pdf）
    └── text_splitter.split_text()  # 分块
    └── text_splitter.extract_keywords()  # 提取关键词
    │
    ▼
[2] HR 点击发布
    │
    ▼
[3] documents.py: publish_document()
    └── rag/vectorstore.add_documents()
        └── rag/embedding.encode_texts()  # 批量向量化
        └── ChromaDB upsert
    │
    ▼
文档可用于 RAG 检索
```

---

## 五、关键文件快速定位指南

### 5.1 按功能查找

| 想了解的功能 | 优先查看文件 |
|--------------|--------------|
| 智能问答主流程 | `backend/app/api/chat.py`（约2700行，最复杂） |
| LLM 调用方式 | `backend/app/services/llm.py` |
| 向量检索逻辑 | `backend/app/services/rag/vectorstore.py` |
| 工单多轮对话 | `backend/app/services/ticket_flow_service.py` |
| 追问识别与改写 | `backend/app/services/followup_service.py` |
| 对话状态管理 | `backend/app/services/conversation_state_service.py` |
| 知识搜索排序 | `backend/app/services/knowledge_search_service.py` |
| 前端问答页面 | `frontend/src/views/Chat.vue` |
| 前端路由配置 | `frontend/src/router/index.js` |
| 前端 API 调用 | `frontend/src/api/chat.js` |
| 数据库模型 | `backend/app/models/` 目录 |
| 环境配置 | `backend/app/core/config.py` |

### 5.2 按调用关系查找

| 如果你在分析... | 需要同时查看 |
|-----------------|--------------|
| `chat.py` | `llm.py`, `knowledge_search_service.py`, `followup_service.py`, `ticket_flow_service.py`, `conversation_state_service.py`, `typo_corrector.py` |
| `documents.py` | `rag/vectorstore.py`, `rag/embedding.py` |
| `feedback.py` | `llm.py`（generate_feedback_handling_suggestion） |
| `gaps.py` | `llm.py`（generate_gap_analysis_summary） |
| `ticket_flow_service.py` | `ticket_intent_service.py`, `ticket_slot_extractor.py`, `llm.py` |
| `knowledge_search_service.py` | `rag/vectorstore.py`, `text_splitter.py` |

---

## 六、Service 依赖关系图

```
                         app.core.config.settings
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
         llm.py            embedding.py     conversation_state_service.py
           │                    │                     │
           │               vectorstore.py      (ConversationState ORM)
           │                    │
     ┌─────┴────┬──────────┐   │
     │          │          │   │
     ▼          ▼          ▼   ▼
typo_corrector  │   ticket_flow_service.py
     │          │          │           │
     │          │          ▼           ▼
     │          │  ticket_intent_service  ticket_slot_extractor
     │          │          │
     │          │          └── llm.py (extract_ticket_slots_with_ai)
     │          │
     │     knowledge_search_service.py
     │          │
     │          ├── vectorstore.py (search_similar)
     │          ├── text_splitter.py (extract_keywords)
     │          ├── Document (ORM)
     │          └── Notice (ORM)
     │
     ▼
followup_service.py
     │
     ├── QARecord (ORM)
     └── ticket_flow_service.py (is_ticket_flow_followup)
```

---

## 七、数据库表关系

```
sys_user (用户)
    │
    ├──< biz_qa_record (问答记录)
    ├──< biz_ticket (工单)
    ├──< biz_comment (评论)
    ├──< biz_conversation_state (对话状态)
    └──< biz_notice_read (已读公告)

sys_department (部门)
    │
    └──< sys_user

biz_document (文档)
    │
    ├──< biz_qa_record (source_docs)
    └──< biz_knowledge_gap (resolved_doc_id)

biz_notice (公告)
    │
    └──< biz_notice_read

biz_ticket (工单)
    │
    └── user_id → sys_user
```

---

## 八、环境配置要点

`backend/.env` 关键配置项：

```env
DATABASE_URL=mysql+pymysql://root:密码@localhost:3306/hr_copilot
SECRET_KEY=jwt-secret-key
MIMO_API_KEY=小米MiMo API密钥
MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5
CHROMA_PERSIST_DIR=./data/chroma_db
EMBEDDING_MODEL=shibing624/text2vec-base-chinese
```

---

## 九、给 GPT 的分析建议

1. **分析智能问答**：先读 `chat.py`，重点关注 `chat()` 函数中的 `if/elif` 分支结构
2. **分析工单流程**：读 `ticket_flow_service.py` + `conversation_state_service.py`
3. **分析 RAG 检索**：读 `knowledge_search_service.py` → `vectorstore.py` → `embedding.py`
4. **分析前端交互**：读 `views/Chat.vue` → `api/chat.js` → 对应后端 API
5. **分析数据模型**：读 `models/` 目录下各文件的 SQLAlchemy 模型定义
