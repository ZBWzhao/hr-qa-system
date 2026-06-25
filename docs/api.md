# HR Copilot API 文档

## 基础信息
- Base URL: `http://localhost:8000/api/v1`
- 认证方式: Bearer Token (JWT)
- 返回格式: `{ "code": 0, "message": "success", "data": {} }`

## 接口列表

### 认证模块 `/auth`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 用户登录 |
| GET | `/auth/users/me` | 获取当前用户 |
| PUT | `/auth/users/me` | 修改个人信息 |

### 用户管理 `/users`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/users` | 用户列表 (admin) |
| PUT | `/users/{id}` | 修改用户 (admin) |
| POST | `/users/{id}/reset-password` | 重置密码 (admin) |

### 部门管理 `/departments`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/departments` | 部门树 |
| GET | `/departments/flat` | 部门列表 |
| POST | `/departments` | 新增部门 (admin) |
| PUT | `/departments/{id}` | 编辑部门 (admin) |
| DELETE | `/departments/{id}` | 删除部门 (admin) |

### 文档管理 `/documents`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/documents` | 文档列表 |
| GET | `/documents/{id}` | 文档详情 |
| POST | `/documents` | 上传文档 (hr) |
| PUT | `/documents/{id}` | 编辑文档 (hr) |
| DELETE | `/documents/{id}` | 删除文档 (hr) |
| POST | `/documents/{id}/publish` | 发布文档 (hr) |
| POST | `/documents/{id}/archive` | 归档文档 (hr) |
| GET | `/documents/{id}/chunks` | 文档分块 |
| GET | `/documents/{id}/versions` | 版本记录 |

### FAQ管理 `/faqs`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/faqs` | FAQ列表 |
| GET | `/faqs/all` | 全部FAQ (hr) |
| GET | `/faqs/{id}` | FAQ详情 |
| POST | `/faqs` | 新增FAQ (hr) |
| PUT | `/faqs/{id}` | 编辑FAQ (hr) |
| DELETE | `/faqs/{id}` | 删除FAQ (hr) |

### 规则问答 `/rules`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/rules` | 规则列表 (hr) |
| GET | `/rules/{id}` | 规则详情 (hr) |
| POST | `/rules` | 新增规则 (hr) |
| PUT | `/rules/{id}` | 编辑规则 (hr) |
| DELETE | `/rules/{id}` | 删除规则 (hr) |

### 搜索 `/search`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/search` | 关键词搜索 |

### 智能问答 `/chat`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat` | 智能问答 |
| POST | `/chat/voice` | 语音问答 (Mock) |
| POST | `/chat/image` | 图片问答 (Mock) |

### 问答历史 `/chat/history`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/chat/history` | 历史列表 |
| PUT | `/chat/history/{id}/favorite` | 收藏切换 |
| DELETE | `/chat/history/{id}` | 删除历史 |

### 反馈 `/feedback`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/feedback` | 提交反馈 |
| GET | `/feedback` | 反馈列表 |
| PUT | `/feedback/{id}/handle` | 处理反馈 (hr) |
| GET | `/feedback/stats` | 反馈统计 (hr) |

### 通知公告 `/notices`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/notices` | 通知列表 |
| GET | `/notices/unread-count` | 未读数量 |
| GET | `/notices/{id}` | 通知详情 |
| POST | `/notices` | 发布通知 (hr) |
| PUT | `/notices/{id}` | 编辑通知 (hr) |
| DELETE | `/notices/{id}` | 删除通知 (hr) |

### 工单 `/tickets`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/tickets` | 工单列表 |
| POST | `/tickets` | 创建工单 |
| PUT | `/tickets/{id}` | 处理工单 (hr) |
| GET | `/tickets/stats` | 工单统计 (hr) |

### 评论 `/comments`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/comments` | 评论列表 |
| POST | `/comments` | 发表评论 |
| PUT | `/comments/{id}/like` | 点赞 |
| PUT | `/comments/{id}/adopt` | 采纳 (hr) |
| DELETE | `/comments/{id}` | 删除 (hr) |

### 推荐 `/recommendations`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/recommendations` | 猜你想问 |

### 入职引导 `/onboarding`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/onboarding` | 入职清单 |
| PUT | `/onboarding/checklist/{id}` | 标记已读 |

### 到期提醒 `/reminders`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/reminders` | 提醒列表 |
| GET | `/reminders/rules` | 规则列表 (hr) |
| POST | `/reminders/rules` | 新增规则 (hr) |
| PUT | `/reminders/rules/{id}` | 编辑规则 (hr) |

### 知识缺口 `/gaps`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/gaps` | 缺口列表 (hr) |
| GET | `/gaps/stats` | 缺口统计 (hr) |
| PUT | `/gaps/{id}/resolve` | 标记解决 (hr) |

### ROI分析 `/roi`
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/roi` | ROI报告 (hr) |

### 审批Mock `/approvals`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/approvals/initiate` | 发起审批 |
| GET | `/approvals/status` | 审批状态 |

### IM机器人Mock `/bot`
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/bot/webhook` | 机器人回调 |