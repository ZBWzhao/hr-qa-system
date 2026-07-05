# 项目清理清单 - 无用文件检查报告

## 📋 概述

本报告列出了项目中可能无用的过程文件、临时文件和测试文件。请根据实际情况决定是否删除。

**重要提醒**：生产用的Embedding模型（618MB）位于 `backend/backend/models/` 目录，**绝对不能删除**！

---

## 🗑️ 建议删除的文件

### 1. 根目录下的临时Python脚本

这些是开发过程中的临时测试脚本，功能已被其他模块覆盖：

| 文件 | 大小 | 说明 | 建议 |
|------|------|------|------|
| `read_docx.py` | 184字节 | 读取docx文档的临时脚本 | ✅ 可删除 |
| `GPTREADME.md` | 18KB | GPT相关的临时文档 | ✅ 可删除 |

### 2. backend目录下的临时测试脚本

这些是开发过程中的测试脚本，用于验证特定功能：

| 文件 | 大小 | 说明 | 建议 |
|------|------|------|------|
| `backend/test_conversation_state.py` | 9.4KB | 会话状态管理测试脚本 | ✅ 可删除 |
| `backend/test_phase2.py` | 5.9KB | 第2阶段验证脚本（年假多轮澄清） | ✅ 可删除 |
| `backend/test_attendance_slots.py` | 3.9KB | 考勤异常工单槽位提取测试 | ✅ 可删除 |
| `backend/test_ai_enhance.py` | 1.9KB | AI增强回答回归测试 | ✅ 可删除 |
| `backend/test_followup.py` | 13KB | 追问场景回归测试 | ✅ 可删除 |
| `backend/test_ticket_flow.py` | 7.5KB | 工单流程测试 | ✅ 可删除 |
| `backend/run_chat_tests.py` | 15KB | 聊天测试运行脚本 | ✅ 可删除 |
| `backend/init_db.py` | 20KB | 数据库初始化脚本（已被scripts/init_test_data.py替代） | ✅ 可删除 |

### 3. 上传的测试文件

这些是测试上传功能时生成的临时文件：

| 文件 | 大小 | 说明 | 建议 |
|------|------|------|------|
| `backend/app/uploads/20260629170440_eula.1042.txt` | 18KB | 测试上传的EULA文件 | ✅ 可删除 |
| `backend/app/uploads/20260629171941_eula.1036.txt` | 18KB | 测试上传的EULA文件 | ✅ 可删除 |
| `backend/app/uploads/20260629171948_eula.1036.txt` | 18KB | 测试上传的EULA文件 | ✅ 可删除 |
| `backend/app/uploads/20260629172106_eula.1040.txt` | 18KB | 测试上传的EULA文件 | ✅ 可删除 |
| `backend/app/uploads/20260629172853_eula.3082.txt` | 18KB | 测试上传的EULA文件 | ✅ 可删除 |

### 4. 测试模型目录

这个目录包含下载失败的测试模型文件，只有配置文件没有实际模型权重：

| 目录 | 大小 | 说明 | 建议 |
|------|------|------|------|
| `backend/test_model/` | 1.1MB | 下载失败的测试模型（damo/nlp_corom_sentence-embedding） | ✅ 可删除 |

### 5. 空目录

| 目录 | 大小 | 说明 | 建议 |
|------|------|------|------|
| `backend/app/services/rag/models/AI-ModelScope/` | 0字节 | 空目录，未被代码引用 | ✅ 可删除 |

---

## ⚠️ 绝对不能删除的目录

### 生产用Embedding模型（618MB）

| 目录 | 大小 | 说明 | 状态 |
|------|------|------|------|
| `backend/backend/models/` | 618MB | 生产用的text2vec-base-chinese模型 | ❌ **绝对不能删除** |
| `backend/backend/models/text2vec-base-chinese/model.safetensors` | 391MB | 模型权重文件 | ❌ **绝对不能删除** |

**原因**：
- 这是RAG系统的核心依赖
- 用于智能问答的文本向量化
- 删除会导致整个系统崩溃
- 配置文件中指定：`EMBEDDING_MODEL=shibing624/text2vec-base-chinese`

---

## 📄 建议保留的文件

### 1. 核心文档（必须保留）

| 文件 | 说明 | 状态 |
|------|------|------|
| `README.md` | 项目主文档 | ✅ 保留 |
| `backend/README.md` | 后端文档 | ✅ 保留 |
| `frontend/README.md` | 前端文档 | ✅ 保留 |
| `docs/api.md` | API文档 | ✅ 保留 |
| `docs/demo-data.md` | 演示数据文档 | ✅ 保留 |
| `HR_Copilot_用户故事文档.md` | 用户故事文档 | ✅ 保留 |

### 2. 开发过程文档（可选保留）

| 文件 | 说明 | 建议 |
|------|------|------|
| `backend/RAG_SETUP_GUIDE.md` | RAG设置指南 | ✅ 保留（有用） |
| `backend/TEST_CASES_CHAT.md` | 聊天测试用例清单 | ✅ 保留（有用） |
| `backend/ISSUES_FIX_PLAN.md` | 问题修复计划 | ✅ 保留（有用） |
| `backend/scripts/README_TEST_DATA.md` | 测试数据生成说明 | ✅ 保留（有用） |

### 3. 脚本文件（必须保留）

| 文件 | 说明 | 状态 |
|------|------|------|
| `backend/scripts/init_test_data.py` | 测试数据生成脚本（Python版） | ✅ 保留 |
| `backend/scripts/init_test_data.sql` | 测试数据生成脚本（SQL版） | ✅ 保留 |
| `backend/scripts/init_rag.py` | RAG初始化脚本 | ✅ 保留 |
| `backend/scripts/init_guide_data.py` | 指南数据初始化脚本 | ✅ 保留 |
| `backend/scripts/index_documents.py` | 文档索引脚本 | ✅ 保留 |

### 4. 模型文件（必须保留）

| 目录 | 说明 | 状态 |
|------|------|------|
| `backend/models/text2vec-base-chinese/` | 生产用的Embedding模型 | ✅ 保留 |

---

## 🔧 建议的清理操作

### 操作1：删除临时测试脚本

```bash
# 删除根目录下的临时脚本
rm read_docx.py
rm GPTREADME.md

# 删除backend目录下的测试脚本
rm backend/test_conversation_state.py
rm backend/test_phase2.py
rm backend/test_attendance_slots.py
rm backend/test_ai_enhance.py
rm backend/test_followup.py
rm backend/test_ticket_flow.py
rm backend/run_chat_tests.py
rm backend/init_db.py
```

### 操作2：删除上传的测试文件

```bash
# 删除uploads目录下的测试文件
rm backend/app/uploads/*.txt
```

### 操作3：删除测试模型目录

```bash
# 删除测试模型目录（只有1.1MB，不是500MB！）
rm -rf backend/test_model/
```

### 操作4：删除空目录

```bash
# 删除空目录
rm -rf backend/app/services/rag/models/AI-ModelScope/
```

### ⚠️ 重要提醒

**不要删除以下目录**：
```bash
# ❌ 绝对不能删除！这是生产用的Embedding模型（618MB）
# backend/backend/models/
# backend/backend/models/text2vec-base-chinese/
```

---

## 📊 清理统计

| 类别 | 文件数量 | 预计释放空间 |
|------|----------|--------------|
| 临时Python脚本 | 11个 | ~80KB |
| 上传的测试文件 | 5个 | ~90KB |
| 测试模型目录 | 1个目录 | 1.1MB |
| 空目录 | 1个目录 | 0字节 |
| **总计** | **~18个文件** | **~1.3MB** |

**注意**：生产用的Embedding模型（618MB）不在清理范围内！

---

## ⚠️ 注意事项

1. **备份优先**：删除前建议先备份或提交到Git
2. **测试模型**：`backend/test_model/` 目录较大（~500MB），删除后可显著减小项目体积
3. **IDE配置**：`.idea/` 目录包含个人IDE设置，通常不应提交到版本控制
4. **uploads目录**：删除后系统会自动重新创建

---

## ✅ 清理后验证

清理完成后，建议验证：

1. 后端服务是否正常启动
2. 前端服务是否正常启动
3. 测试数据生成功能是否正常
4. 聊天功能是否正常
5. 工单功能是否正常

---

**报告生成时间**: 2026-07-05
**检查人**: Claude Assistant
