# HR Copilot 后端

## 技术栈
- Python 3.10+
- FastAPI
- SQLAlchemy + MySQL
- JWT 认证 + bcrypt 加密

## 启动步骤

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 创建MySQL数据库
mysql -u root -p123456 -e "CREATE DATABASE hr_copilot DEFAULT CHARACTER SET utf8mb4;"

# 3. 初始化数据库和演示数据
python init_db.py

# 4. 启动服务
uvicorn app.main:app --reload --port 8000

# 5. 智能问答自动化测试（另开终端，服务已启动后）
python run_chat_tests.py
# 详见 TEST_CASES_CHAT.md
```

## 访问地址
- API 服务: http://localhost:8000
- Swagger 文档: http://localhost:8000/docs

## 演示账号
| 账号 | 密码 | 角色 |
|------|------|------|
| admin | 123456 | 管理员 |
| hr001 | 123456 | HR人员 |
| emp001 | 123456 | 普通员工 |

## 目录结构
```
app/
├── api/          # API路由模块 (20个)
├── core/         # 核心配置 (数据库/安全/响应)
├── models/       # SQLAlchemy数据模型
├── schemas/      # Pydantic数据校验
├── services/     # 业务逻辑层
├── utils/        # 工具函数
└── main.py       # FastAPI入口
```