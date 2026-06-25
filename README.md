# HR Copilot - 公司HR制度智能问答系统

## 项目介绍
HR Copilot 是一个基于 Vue 3 + FastAPI 的公司HR制度智能问答系统，采用前后端分离架构，支持 RAG 智能问答、文档管理、FAQ管理、工单系统等完整功能。

## 技术栈

### 前端
- Vue 3 + Vite + Element Plus
- Pinia + Vue Router + Axios
- ECharts 数据可视化

### 后端
- Python 3.10+ + FastAPI
- SQLAlchemy + MySQL 8.0
- JWT 认证 + bcrypt 加密

## 功能模块

| 模块 | 说明 |
|------|------|
| 智能问答 | FAQ优先 → 规则匹配 → RAG检索 → MockLLM |
| 文档管理 | 上传/发布/归档 + 自动分chunk + 版本记录 |
| 关键词搜索 | 文档内容搜索 + 分类过滤 + 高亮显示 |
| FAQ管理 | CRUD + 分类 + 浏览计数 |
| 规则问答 | 关键词触发 + 优先级排序 |
| 通知公告 | 发布/置顶/已读标记 |
| 工单系统 | 创建/受理/完成/驳回 |
| 反馈纠错 | 有用无用评价 + HR处理 |
| 评论讨论 | 回复/点赞/采纳 |
| 统计看板 | ECharts图表 |
| 知识缺口 | 未命中问题记录 |
| ROI分析 | 节省工时/等效全职HR |
| 入职引导 | 新员工学习清单 |
| 到期提醒 | 试用期/合同/年假提醒 |
| Mock扩展 | 语音/图片问答/审批/IM机器人 |

## 启动步骤

### 1. 后端
```bash
cd backend
pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --reload --port 8000
```

### 2. 前端
```bash
cd frontend
npm install
npm run dev
```

### 3. 访问
- 前端: http://localhost:3000
- 后端API: http://localhost:8000/docs

## 演示账号
| 账号 | 密码 | 角色 |
|------|------|------|
| admin | 123456 | 管理员 |
| hr001 | 123456 | HR人员 |
| emp001 | 123456 | 普通员工 |

## 项目亮点
1. 完整的 RAG 智能问答链路 (FAQ→规则→RAG→MockLLM)
2. 角色权限控制 (employee/hr/admin)
3. 20个后端API模块 + 21个前端页面
4. 统一的接口返回格式和错误处理
5. ECharts 数据可视化看板
6. 可替换的 AI 能力接口设计

## 后续可扩展方向
- 接入真实 LLM API (OpenAI/文心一言)
- 部署 Milvus 向量数据库
- 集成企业微信/钉钉/飞书
- 添加 ASR/OCR/TTS 能力
- 部署 Elasticsearch 全文搜索
- 添加 Redis 缓存和 Celery 异步任务