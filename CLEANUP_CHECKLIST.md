# 项目清理清单 - 无用文件检查报告

## 📋 概述

本报告列出了项目中可能无用的过程文件、临时文件和测试文件。请根据实际情况决定是否删除。

---

## 🗑️ 建议删除的文件

### 1. 根目录下的临时Python脚本

这些是开发过程中的临时测试脚本，功能已被其他模块覆盖：

| 文件 | 说明 | 建议 |
|------|------|------|
| `read_docx.py` | 读取docx文档的临时脚本 | ⚠️ 可删除 |
| `GPTREADME.md` | GPT相关的临时文档 | ⚠️ 可删除 |

### 2. backend目录下的临时测试脚本

这些是开发过程中的测试脚本，用于验证特定功能：

| 文件 | 说明 | 建议 |
|------|------|------|
| `backend/test_conversation_state.py` | 会话状态管理测试脚本 | ⚠️ 可删除 |
| `backend/test_phase2.py` | 第2阶段验证脚本（年假多轮澄清） | ⚠️ 可删除 |
| `backend/test_attendance_slots.py` | 考勤异常工单槽位提取测试 | ⚠️ 可删除 |
| `backend/test_ai_enhance.py` | AI增强回答回归测试 | ⚠️ 可删除 |
| `backend/test_followup.py` | 追问场景回归测试 | ⚠️ 可删除 |
| `backend/test_ticket_flow.py` | 工单流程测试 | ⚠️ 可删除 |
| `backend/run_chat_tests.py` | 聊天测试运行脚本 | ⚠️ 可删除 |
| `backend/init_db.py` | 数据库初始化脚本（已被scripts/init_test_data.py替代） | ⚠️ 可删除 |

### 3. 上传的测试文件

这些是测试上传功能时生成的临时文件：

| 文件 | 说明 | 建议 |
|------|------|------|
| `backend/app/uploads/20260629170440_eula.1042.txt` | 测试上传的EULA文件 | ⚠️ 可删除 |
| `backend/app/uploads/20260629171941_eula.1036.txt` | 测试上传的EULA文件 | ⚠️ 可删除 |
| `backend/app/uploads/20260629171948_eula.1036.txt` | 测试上传的EULA文件 | ⚠️ 可删除 |
| `backend/app/uploads/20260629172106_eula.1040.txt` | 测试上传的EULA文件 | ⚠️ 可删除 |
| `backend/app/uploads/20260629172853_eula.3082.txt` | 测试上传的EULA文件 | ⚠️ 可删除 |

### 4. 测试模型目录

这个目录包含测试用的模型文件，可能不再需要：

| 目录 | 说明 | 建议 |
|------|------|------|
| `backend/test_model/` | 测试用的NLP模型（damo/nlp_corom_sentence-embedding） | ⚠️ 可删除 |

### 5. IDE配置文件

这些是IDE的配置文件，通常不需要提交到版本控制：

| 目录/文件 | 说明 | 建议 |
|-----------|------|------|
| `.idea/` | IntelliJ IDEA配置目录 | ⚠️ 可删除（建议加入.gitignore） |

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
# 删除测试模型目录
rm -rf backend/test_model/
```

### 操作4：清理IDE配置（可选）

```bash
# 删除IDE配置目录
rm -rf .idea/

# 添加到.gitignore
echo ".idea/" >> .gitignore
```

---

## 📊 清理统计

| 类别 | 文件数量 | 预计释放空间 |
|------|----------|--------------|
| 临时Python脚本 | 8个 | ~50KB |
| 测试模型目录 | 1个目录 | ~500MB |
| 上传的测试文件 | 5个 | ~100KB |
| IDE配置文件 | 1个目录 | ~10KB |
| **总计** | **~15个文件** | **~500MB** |

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
