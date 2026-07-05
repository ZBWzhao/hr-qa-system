# HR Copilot 测试数据生成指南

## 📋 概述

本目录包含用于生成测试数据的脚本，可以帮助您快速初始化数据库，以便进行系统测试。

### 数据生成规则

1. **部门用户规则**
   - 每个部门至少3个用户
   - 每个部门最多1个HR
   - 其余为普通员工

2. **工单规则**
   - 每个用户创建2-3种不同类型的工单
   - 工单类型包括：请假、证明开具、信息变更、考勤异常、报销等
   - 工单状态随机分配（pending/completed）

3. **数据关联性**
   - 员工工单自动分配给同部门HR处理
   - 公告已读记录与用户关联
   - 问答反馈与处理人关联
   - 评论与工单和用户关联

## 🚀 使用方法

### 方式一：使用Python脚本（推荐）

Python脚本使用SQLAlchemy ORM，更灵活且能自动处理密码哈希。

#### 前置条件

1. 确保已安装项目依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 确保数据库已创建：
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS hr_copilot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

3. 确保已运行数据库迁移创建表结构：
```bash
# 如果使用Alembic
alembic upgrade head

# 或者手动创建表
python -c "from app.core.database import engine, Base; from app.models import *; Base.metadata.create_all(engine)"
```

#### 执行脚本

```bash
cd backend
python -m scripts.init_test_data
```

### 方式二：使用SQL脚本

SQL脚本适合直接在MySQL中执行，但密码已预设为固定哈希值。

#### 前置条件

1. 确保数据库和表已创建

2. 确保字符集设置正确：
```bash
mysql -u root -p hr_copilot --default-character-set=utf8mb4
```

#### 执行脚本

```bash
# 方式1：命令行执行
mysql -u root -p hr_copilot < backend/scripts/init_test_data.sql

# 方式2：MySQL客户端内执行
mysql> source /path/to/init_test_data.sql
```

## 📊 测试数据统计

### 部门分布

| 部门 | 总人数 | HR人数 | 员工人数 |
|------|--------|--------|----------|
| 人力资源部 | 3 | 1 | 2 |
| 技术部 | 6 | 1 | 5 |
| 市场部 | 5 | 1 | 4 |
| 财务部 | 4 | 1 | 3 |
| 行政部 | 4 | 1 | 3 |
| **总计** | **22** | **5** | **17** |

### 工单类型分布

| 工单类型 | 说明 | 预计数量 |
|----------|------|----------|
| leave_request | 请假申请 | ~15 |
| certify | 证明开具 | ~12 |
| info_change | 信息变更 | ~10 |
| attendance_exception | 考勤异常 | ~8 |
| reimbursement | 报销/薪资 | ~8 |
| other | 人工请求 | ~8 |
| **总计** | | **~60** |

### 其他数据

- 公告：5条
- 问答记录：~30条
- 评论：~15条
- 未命中问题：7条

## 🔑 测试账号

### 默认密码
所有测试账号的密码均为：`123456`

### HR账号（每个部门1个）

| 部门 | 用户名 | 真实姓名 |
|------|--------|----------|
| 人力资源部 | zhangsan | 张三 |
| 技术部 | liudehua | 刘德华 |
| 市场部 | chenglong | 成龙 |
| 财务部 | yangmi | 杨幂 |
| 行政部 | huangbo | 黄渤 |

### 员工账号示例

| 部门 | 用户名 | 真实姓名 |
|------|--------|----------|
| 人力资源部 | lisi | 李四 |
| 人力资源部 | wangwu | 王五 |
| 技术部 | zhangxueyou | 张学友 |
| 技术部 | guofucheng | 郭富城 |
| 市场部 | lianjie | 李连杰 |
| 财务部 | zhaoliying | 赵丽颖 |
| 行政部 | xuzheng | 徐峥 |

## ⚠️ 注意事项

1. **数据清除**
   - Python脚本会检查数据是否已存在，不会重复创建
   - SQL脚本中包含注释掉的TRUNCATE语句，如需清空数据请取消注释

2. **密码安全**
   - 测试环境请勿使用生产环境密码
   - 默认密码仅用于测试目的

3. **数据库备份**
   - 执行脚本前建议备份数据库：
   ```bash
   mysqldump -u root -p hr_copilot > hr_copilot_backup.sql
   ```

4. **自定义数据**
   - 如需修改测试数据，可编辑脚本中的配置数据
   - Python脚本更易于扩展和自定义

## 🔧 故障排除

### 问题1：外键约束错误
```
ERROR 1452: Cannot add or update a child row: a foreign key constraint fails
```
**解决方案**：确保先创建部门，再创建用户；先创建用户，再创建工单。

### 问题2：重复数据错误
```
ERROR 1062: Duplicate entry 'xxx' for key 'xxx'
```
**解决方案**：脚本已使用`NOT EXISTS`检查，正常情况下不会出现此问题。如遇此问题，可先清空相关表。

### 问题3：字符编码问题
```
ERROR 1366: Incorrect string value
```
**解决方案**：确保数据库和表使用utf8mb4字符集。

## 📝 扩展建议

如需更多测试数据，可以：

1. 修改脚本中的用户池，添加更多用户
2. 增加工单模板，丰富测试场景
3. 添加更多问答记录，测试知识库功能
4. 创建更多公告，测试通知系统

## 📞 技术支持

如遇到问题，请检查：
1. 数据库连接配置是否正确
2. 表结构是否已创建
3. Python依赖是否已安装
4. 数据库用户是否有足够权限

---

**最后更新**: 2026-07-05
**维护者**: HR Copilot 开发团队
