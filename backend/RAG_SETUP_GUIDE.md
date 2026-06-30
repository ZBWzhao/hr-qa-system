# HR Copilot RAG系统部署指南

## 技术栈

| 组件 | 技术 | 说明 |
|-----|------|------|
| Embedding | text2vec-base-chinese | 中文语义向量模型 |
| 向量数据库 | Chroma | 轻量级嵌入式向量库 |
| LLM | DeepSeek API | 大语言模型 |
| 分词 | jieba | 中文分词 |

## 环境准备

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

首次运行会自动下载Embedding模型（约400MB）。

### 2. 配置环境变量

编辑 `backend/.env` 文件：

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=sk-351eafda1c8b4364996f02358cca40b0
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# Chroma向量数据库配置
CHROMA_PERSIST_DIR=./data/chroma_db

# Embedding模型配置
EMBEDDING_MODEL=shibing624/text2vec-base-chinese

# 数据库配置
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/hr_qa_system
```

### 3. 初始化RAG系统

```bash
cd backend
python scripts/init_rag.py
```

该脚本会：
1. 创建数据库表
2. 索引所有已发布文档到Chroma
3. 显示系统统计信息

## 使用流程

### 1. 上传文档

HR用户上传制度文档（支持txt/md/docx格式）。

### 2. 发布文档

文档发布时会自动：
- 切分成小块（500字左右）
- 提取关键词
- 向量化存储到Chroma

### 3. 智能问答

员工提问时，系统会：
1. 优先匹配FAQ标准答案
2. 未命中则匹配规则问答
3. 都未命中则通过向量检索找到相关文档
4. 调用DeepSeek生成回答
5. 返回答案和来源引用

## 问答流程图

```
用户提问
    ↓
FAQ匹配 → 命中 → 返回FAQ答案
    ↓ 未命中
规则匹配 → 命中 → 返回规则答案
    ↓ 未命中
意图分析 → 需要澄清 → 返回澄清请求
    ↓ 不需要
向量检索 → 找到相关文档 → LLM生成回答
    ↓ 未找到
返回未命中提示
```

## API接口

### 智能问答

```
POST /api/v1/chat
{
    "question": "年假怎么计算？",
    "conversation_id": "可选，对话ID"
}
```

### 重新索引文档

```
POST /api/v1/documents/reindex
```

### 获取向量库统计

```
GET /api/v1/chat/stats
```

## 文件结构

```
backend/
├── app/
│   ├── services/
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── embedding.py      # Embedding服务
│   │   │   └── vectorstore.py    # Chroma向量库服务
│   │   ├── llm.py                # DeepSeek LLM服务
│   │   └── text_splitter.py      # 文本切片工具
│   └── api/
│       ├── chat.py               # 问答API
│       └── documents.py          # 文档API
├── scripts/
│   ├── init_rag.py               # RAG初始化脚本
│   └── index_documents.py        # 文档索引脚本
├── data/
│   └── chroma_db/                # Chroma数据目录
└── .env                          # 环境变量配置
```

## 常见问题

### Q: 首次运行很慢？

A: 首次运行需要下载Embedding模型（约400MB），后续运行会使用缓存。

### Q: 如何更新文档索引？

A: 有两种方式：
1. 重新发布文档会自动更新索引
2. 调用 `/api/v1/documents/reindex` 批量重新索引

### Q: 如何提高问答质量？

A: 可以：
1. 添加更多FAQ标准答案
2. 完善规则问答
3. 上传更详细的制度文档
4. 调整Embedding模型或LLM参数

### Q: 向量数据库数据在哪里？

A: 默认存储在 `backend/data/chroma_db/` 目录。

## 下一步优化

1. **流式输出** - LLM回答支持流式显示
2. **多轮对话** - 增强上下文理解
3. **答案缓存** - 相似问题缓存答案
4. **反馈学习** - 根据用户反馈优化答案
