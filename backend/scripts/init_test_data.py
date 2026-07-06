#!/usr/bin/env python3
"""
HR Copilot 测试数据生成脚本
===========================
功能:
- 为每个部门创建至少3个用户(每个部门最多1个HR)
- 为每个用户创建2-3种不同类型的工单
- 创建公告和公告已读记录
- 创建问答记录和反馈
- 确保所有数据之间的关联性

使用方法:
cd backend
python -m scripts.init_test_data
"""

import sys
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.user import User
from app.models.ticket import Ticket
from app.models.notice import Notice, NoticeRead
from app.models.qa import QARecord, QAFeedback, QAMiss
from app.models.comment import Comment

# 数据库连接
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


# ==================== 配置数据 ====================

# 部门配置
DEPARTMENTS = [
    {"name": "人力资源部", "parent_id": None, "sort_order": 1},
    {"name": "技术部", "parent_id": None, "sort_order": 2},
    {"name": "市场部", "parent_id": None, "sort_order": 3},
    {"name": "财务部", "parent_id": None, "sort_order": 4},
    {"name": "行政部", "parent_id": None, "sort_order": 5},
]

# 用户名和真实姓名池
USER_POOL = {
    "人力资源部": [
        ("zhangsan", "张三", "hr"),
        ("lisi", "李四", "employee"),
        ("wangwu", "王五", "employee"),
        ("zhaoliu", "赵六", "employee"),
        ("sunqi", "孙七", "employee"),
    ],
    "技术部": [
        ("liudehua", "刘德华", "hr"),
        ("zhangxueyou", "张学友", "employee"),
        ("guofucheng", "郭富城", "employee"),
        ("liming", "黎明", "employee"),
        ("zhoujielun", "周杰伦", "employee"),
        ("linjunjie", "林俊杰", "employee"),
    ],
    "市场部": [
        ("chenglong", "成龙", "hr"),
        ("li连杰", "李连杰", "employee"),
        ("zirui", "甄子丹", "employee"),
        ("wuyanzu", "吴彦祖", "employee"),
        ("pengyuyan", "彭于晏", "employee"),
    ],
    "财务部": [
        ("yangmi", "杨幂", "hr"),
        ("zhaoliying", "赵丽颖", "employee"),
        ("tangyan", "唐嫣", "employee"),
        ("liushishi", "刘诗诗", "employee"),
    ],
    "行政部": [
        ("huangbo", "黄渤", "hr"),
        ("xuzheng", "徐峥", "employee"),
        ("wangbaoqiang", "王宝强", "employee"),
        ("dengchao", "邓超", "employee"),
    ],
}

# 工单类型和对应的示例数据
TICKET_TEMPLATES = {
    "请假申请": [
        {
            "title": "年假申请",
            "description": "申请年假,需要回家处理个人事务",
            "slots": {
                "leave_type": "年假",
                "start_date": "2026-07-10",
                "end_date": "2026-07-12",
                "reason": "回家处理个人事务"
            }
        },
        {
            "title": "病假申请",
            "description": "身体不适,需要休息",
            "slots": {
                "leave_type": "病假",
                "start_date": "2026-07-08",
                "end_date": "2026-07-09",
                "reason": "感冒发烧,需要休息"
            }
        },
        {
            "title": "事假申请",
            "description": "家中有事需要处理",
            "slots": {
                "leave_type": "事假",
                "start_date": "2026-07-15",
                "end_date": "2026-07-15",
                "reason": "家中有急事需要处理"
            }
        },
    ],
    "证明开具": [
        {
            "title": "在职证明申请",
            "description": "需要开具在职证明用于办理签证",
            "slots": {
                "purpose": "办理签证",
                "receiver": "大使馆",
                "need_stamp": "是",
                "expected_time": "2026-07-10"
            }
        },
        {
            "title": "收入证明申请",
            "description": "需要开具收入证明用于办理贷款",
            "slots": {
                "purpose": "办理银行贷款",
                "receiver": "中国银行",
                "need_stamp": "是",
                "expected_time": "2026-07-12"
            }
        },
    ],
    "信息变更": [
        {
            "title": "手机号码变更",
            "description": "更换了新的手机号码",
            "slots": {
                "change_item": "手机号码",
                "old_value": "138****1234",
                "new_value": "139****5678",
                "reason": "原手机号已停用"
            }
        },
        {
            "title": "银行卡号变更",
            "description": "更换工资卡",
            "slots": {
                "change_item": "工资卡号",
                "old_value": "6222****1234",
                "new_value": "6228****5678",
                "reason": "原银行卡已注销"
            }
        },
    ],
    "考勤异常": [
        {
            "title": "忘打卡申请",
            "description": "早上忘记打卡",
            "slots": {
                "exception_date": "2026-07-05",
                "exception_type": "忘打卡",
                "reason": "早上急着开会忘记打卡"
            }
        },
        {
            "title": "迟到说明",
            "description": "今天迟到需要说明原因",
            "slots": {
                "exception_date": "2026-07-04",
                "exception_type": "迟到",
                "reason": "地铁故障导致迟到"
            }
        },
    ],
    "报销薪资": [
        {
            "title": "差旅费报销",
            "description": "出差期间产生的差旅费用",
            "slots": {
                "issue_type": "差旅费",
                "amount_range": "2000-5000",
                "description": "出差北京3天的交通和住宿费用"
            }
        },
        {
            "title": "办公用品报销",
            "description": "购买办公用品费用",
            "slots": {
                "issue_type": "办公用品",
                "amount_range": "500以下",
                "description": "购买键盘鼠标等办公用品"
            }
        },
    ],
    "其他": [
        {
            "title": "IT设备申请",
            "description": "申请新的笔记本电脑",
            "slots": {
                "issue_type": "设备申请",
                "description": "需要一台新的笔记本电脑用于开发工作",
                "expected_time": "2026-07-20"
            }
        },
        {
            "title": "会议室预定",
            "description": "需要预定会议室",
            "slots": {
                "issue_type": "会议室预定",
                "description": "需要预定一个可容纳10人的会议室",
                "expected_time": "2026-07-10 14:00"
            }
        },
    ],
}

# 公告模板
NOTICE_TEMPLATES = [
    {
        "title": "关于2026年年假安排的通知",
        "content": "各位同事:\n\n根据公司规定,2026年年假安排如下:\n1. 年假有效期为2026年1月1日至2026年12月31日\n2. 请各部门合理安排员工休假计划\n3. 年假需提前3天申请\n\n特此通知.",
        "notice_type": "general",
        "is_pinned": 1,
    },
    {
        "title": "公司团建活动通知",
        "content": "各位同事:\n\n为增进同事间的交流与合作,公司定于7月20日组织团建活动.\n活动地点:XX拓展基地\n集合时间:早上8:30\n请各位同事准时参加.",
        "notice_type": "activity",
        "is_pinned": 0,
    },
    {
        "title": "关于规范考勤管理的通知",
        "content": "各位同事:\n\n为加强公司考勤管理,现将有关事项通知如下:\n1. 工作时间为上午9:00-12:00,下午13:30-18:00\n2. 迟到30分钟以内需说明原因\n3. 请务必按时打卡\n\n特此通知.",
        "notice_type": "policy",
        "is_pinned": 1,
    },
    {
        "title": "系统维护通知",
        "content": "各位同事:\n\n公司OA系统将于本周六(7月11日)22:00至次日6:00进行维护升级,届时系统将暂停服务.\n请各位同事提前做好相关工作安排.\n\n给您带来不便,敬请谅解.",
        "notice_type": "system",
        "is_pinned": 0,
    },
    {
        "title": "关于端午节放假安排的通知",
        "content": "各位同事:\n\n根据国家法定节假日安排,端午节放假时间为6月25日至6月27日,共3天.\n6月28日(周日)正常上班.\n请各部门做好工作安排.\n\n祝大家端午节快乐!",
        "notice_type": "holiday",
        "is_pinned": 1,
    },
]

# 问答模板
QA_TEMPLATES = [
    {
        "question": "年假有多少天?",
        "answer": "根据公司规定,员工年假天数如下:\n- 工作满1年不满10年:5天\n- 工作满10年不满20年:10天\n- 工作满20年:15天\n年假有效期为当年1月1日至12月31日,过期作废.",
        "answer_type": "rag",
    },
    {
        "question": "如何申请报销?",
        "answer": "申请报销的流程如下:\n1. 登录HR系统\n2. 选择\"报销申请\"功能\n3. 填写报销类型,金额,事由\n4. 上传发票照片\n5. 提交等待审批\n\n审批通过后,报销款项将在5个工作日内打到您的工资卡.",
        "answer_type": "rag",
    },
    {
        "question": "公司有什么福利?",
        "answer": "公司提供的福利包括:\n1. 五险一金\n2. 补充商业保险\n3. 年度体检\n4. 节日礼品\n5. 生日福利\n6. 带薪年假\n7. 员工培训\n8. 团建活动\n具体可查看员工手册.",
        "answer_type": "rag",
    },
    {
        "question": "试用期多久?",
        "answer": "公司试用期规定:\n- 劳动合同期限1年以上不满3年:试用期2个月\n- 劳动合同期限3年以上:试用期6个月\n试用期内享受正式员工80%的工资待遇.",
        "answer_type": "rag",
    },
    {
        "question": "如何请假?",
        "answer": "请假流程:\n1. 提前在HR系统提交请假申请\n2. 选择请假类型(年假/事假/病假等)\n3. 填写请假时间和原因\n4. 提交审批\n\n请假审批流程:\n- 1天以内:直属主管审批\n- 1-3天:部门经理审批\n- 3天以上:HR总监审批",
        "answer_type": "rag",
    },
    {
        "question": "工资什么时候发?",
        "answer": "公司工资发放规定:\n- 发放日期:每月15日\n- 如遇节假日则提前发放\n- 工资通过银行转账方式发放到个人工资卡\n- 工资条可在HR系统中查看",
        "answer_type": "rag",
    },
    {
        "question": "如何开具在职证明?",
        "answer": "开具在职证明的步骤:\n1. 登录HR系统\n2. 选择\"证明开具\"功能\n3. 选择证明类型(在职证明/收入证明等)\n4. 填写用途和接收单位\n5. 提交申请\n\n一般1-3个工作日内可领取.",
        "answer_type": "rag",
    },
    {
        "question": "加班如何计算?",
        "answer": "加班计算标准:\n- 工作日加班:1.5倍工资\n- 周末加班:2倍工资\n- 法定节假日:3倍工资\n\n加班需提前申请并经主管批准.加班时间可选择调休或发放加班费.",
        "answer_type": "rag",
    },
]


# ==================== 工具函数 ====================

def get_password_hash_local(password: str) -> str:
    """获取密码哈希"""
    return get_password_hash(password)


def random_date(start_days_ago: int = 90, end_days_ago: int = 0) -> datetime:
    """生成随机日期"""
    days = random.randint(end_days_ago, start_days_ago)
    return datetime.now() - timedelta(days=days)


def generate_ticket_no(index: int) -> str:
    """生成工单号"""
    return f"TK{datetime.now().strftime('%Y%m%d')}{index:04d}"


def generate_conversation_id() -> str:
    """生成会话ID"""
    import uuid
    return str(uuid.uuid4()).replace('-', '')[:32]


# ==================== 数据生成函数 ====================

def create_departments(db: Session) -> dict:
    """创建部门,返回 {部门名: 部门对象} 的映射"""
    print("\n[DEPT] 创建部门...")
    dept_map = {}

    for dept_data in DEPARTMENTS:
        # 检查部门是否已存在
        existing = db.query(Department).filter(Department.name == dept_data["name"]).first()
        if existing:
            dept_map[dept_data["name"]] = existing
            print(f"  [OK] 部门已存在: {dept_data['name']} (ID: {existing.id})")
        else:
            dept = Department(
                name=dept_data["name"],
                parent_id=dept_data["parent_id"],
                sort_order=dept_data["sort_order"],
                created_at=datetime.now()
            )
            db.add(dept)
            db.flush()
            dept_map[dept_data["name"]] = dept
            print(f"  + 创建部门: {dept_data['name']} (ID: {dept.id})")

    db.commit()
    return dept_map


def create_users(db: Session, dept_map: dict) -> list:
    """创建用户,返回所有用户列表"""
    print("\n[USER] 创建用户...")
    all_users = []
    default_password = get_password_hash_local("123456")

    for dept_name, user_list in USER_POOL.items():
        dept = dept_map.get(dept_name)
        if not dept:
            print(f"  [FAIL] 部门不存在: {dept_name}")
            continue

        print(f"\n  [LIST] {dept_name} (ID: {dept.id}):")

        # 确保至少3个用户
        users_to_create = user_list[:max(3, len(user_list))]

        for username, real_name, role in users_to_create:
            # 检查用户是否已存在
            existing = db.query(User).filter(User.username == username).first()
            if existing:
                all_users.append(existing)
                print(f"    [OK] 用户已存在: {real_name} ({username}) - {role}")
                continue

            # 生成入职日期(1-3年前)
            hire_date = random_date(start_days_ago=1095, end_days_ago=30)

            # 生成合同到期日(1-2年后)
            contract_end_date = datetime.now() + timedelta(days=random.randint(365, 730))

            # 生成试用期到期日(入职后3-6个月)
            probation_end_date = hire_date + timedelta(days=random.randint(90, 180))

            user = User(
                username=username,
                password_hash=default_password,
                real_name=real_name,
                email=f"{username}@company.com",
                department_id=dept.id,
                role=role,
                status=1,  # 启用状态
                hire_date=hire_date,
                contract_end_date=contract_end_date,
                probation_end_date=probation_end_date,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(user)
            db.flush()
            all_users.append(user)
            print(f"    + 创建用户: {real_name} ({username}) - {role}")

    db.commit()
    print(f"\n  [STAT] 总计创建/更新用户: {len(all_users)} 人")
    return all_users


def create_tickets(db: Session, all_users: list) -> list:
    """为每个用户创建2-3种不同类型的工单"""
    print("\n[TICK] 创建工单...")
    all_tickets = []
    ticket_types = list(TICKET_TEMPLATES.keys())
    ticket_index = 1

    for user in all_users:
        # 每人随机选择2-3种工单类型
        num_tickets = random.randint(2, 3)
        selected_types = random.sample(ticket_types, min(num_tickets, len(ticket_types)))

        print(f"\n  [PERSON] {user.real_name} ({user.username}):")

        for ticket_type in selected_types:
            templates = TICKET_TEMPLATES[ticket_type]
            template = random.choice(templates)

            # 检查是否已有相同标题的工单
            existing = db.query(Ticket).filter(
                Ticket.creator_id == user.id,
                Ticket.title == template["title"]
            ).first()

            if existing:
                all_tickets.append(existing)
                print(f"    [OK] 工单已存在: {template['title']}")
                continue

            # 随机决定工单状态
            status = random.choice(["pending", "completed"])

            # 生成创建时间(过去30天内)
            created_at = random_date(start_days_ago=30, end_days_ago=0)

            # 如果是已完成状态,生成解决时间
            resolved_at = None
            resolve_note = None
            if status == "completed":
                resolved_at = created_at + timedelta(days=random.randint(1, 5))
                resolve_note = "已处理完成"

            # 为工单分配处理人(HR或部门负责人)
            assignee = None
            if user.role == "employee":
                # 查找同部门的HR
                hr_users = [u for u in all_users
                           if u.department_id == user.department_id and u.role == "hr"]
                if hr_users:
                    assignee = random.choice(hr_users)

            ticket = Ticket(
                ticket_no=generate_ticket_no(ticket_index),
                type=ticket_type,
                title=template["title"],
                description=template["description"],
                attachments=None,
                status=status,
                creator_id=user.id,
                assignee_id=assignee.id if assignee else None,
                resolve_note=resolve_note,
                resolved_at=resolved_at,
                conversation_id=generate_conversation_id(),
                qa_record_id=None,
                created_at=created_at,
                updated_at=resolved_at if resolved_at else created_at
            )
            db.add(ticket)
            db.flush()
            all_tickets.append(ticket)
            ticket_index += 1

            print(f"    + 创建工单: {template['title']} ({ticket_type}) - {status}")

    db.commit()
    print(f"\n  [STAT] 总计创建/更新工单: {len(all_tickets)} 个")
    return all_tickets


def create_notices(db: Session, all_users: list) -> list:
    """创建公告和公告已读记录"""
    print("\n[NOTE] 创建公告...")
    all_notices = []

    # 选择HR用户作为公告发布者
    hr_users = [u for u in all_users if u.role == "hr"]
    if not hr_users:
        print("  [FAIL] 没有HR用户,跳过创建公告")
        return all_notices

    for i, notice_template in enumerate(NOTICE_TEMPLATES):
        # 检查公告是否已存在
        existing = db.query(Notice).filter(Notice.title == notice_template["title"]).first()
        if existing:
            all_notices.append(existing)
            print(f"  [OK] 公告已存在: {notice_template['title']}")
            continue

        # 随机选择发布者
        publisher = random.choice(hr_users)

        # 生成发布时间(过去14天内)
        created_at = random_date(start_days_ago=14, end_days_ago=0)

        # 生成过期时间(未来30天)
        expire_at = datetime.now() + timedelta(days=random.randint(15, 30))

        notice = Notice(
            title=notice_template["title"],
            content=notice_template["content"],
            notice_type=notice_template["notice_type"],
            is_pinned=notice_template["is_pinned"],
            publisher_id=publisher.id,
            expire_at=expire_at,
            created_at=created_at
        )
        db.add(notice)
        db.flush()
        all_notices.append(notice)
        print(f"  + 创建公告: {notice_template['title']}")

        # 为部分用户创建已读记录
        num_readers = random.randint(len(all_users) // 3, len(all_users) * 2 // 3)
        readers = random.sample(all_users, min(num_readers, len(all_users)))

        for reader in readers:
            # 检查是否已有已读记录
            existing_read = db.query(NoticeRead).filter(
                NoticeRead.notice_id == notice.id,
                NoticeRead.user_id == reader.id
            ).first()

            if not existing_read:
                notice_read = NoticeRead(
                    notice_id=notice.id,
                    user_id=reader.id,
                    read_at=created_at + timedelta(hours=random.randint(1, 48))
                )
                db.add(notice_read)

    db.commit()
    print(f"\n  [STAT] 总计创建/更新公告: {len(all_notices)} 条")
    return all_notices


def create_qa_records(db: Session, all_users: list) -> list:
    """创建问答记录和反馈"""
    print("\n[QA] 创建问答记录...")
    all_records = []

    for user in all_users:
        # 每个用户随机问2-4个问题
        num_questions = random.randint(2, 4)
        selected_qa = random.sample(QA_TEMPLATES, min(num_questions, len(QA_TEMPLATES)))

        print(f"\n  [PERSON] {user.real_name} ({user.username}):")

        for qa_template in selected_qa:
            # 生成创建时间(过去14天内)
            created_at = random_date(start_days_ago=14, end_days_ago=0)

            # 随机决定是否有反馈
            feedback = None
            if random.random() < 0.6:  # 60%的概率有反馈
                feedback = random.choice([1, -1])  # 1=满意,-1=不满意

            record = QARecord(
                user_id=user.id,
                question=qa_template["question"],
                answer=qa_template["answer"],
                answer_type=qa_template["answer_type"],
                source_docs=None,
                feedback=feedback,
                is_favorite=1 if random.random() < 0.2 else 0,  # 20%概率收藏
                conversation_id=generate_conversation_id(),
                created_at=created_at
            )
            db.add(record)
            db.flush()
            all_records.append(record)
            print(f"    + 问: {qa_template['question'][:20]}...")

            # 如果有负面反馈,创建反馈记录
            if feedback == -1 and random.random() < 0.5:
                # 查找HR用户作为处理人
                hr_users = [u for u in all_users if u.role == "hr"]
                handler = random.choice(hr_users) if hr_users else None

                qa_feedback = QAFeedback(
                    record_id=record.id,
                    user_id=user.id,
                    feedback_type="incorrect",
                    correction_text="回答不够准确,需要更新",
                    status=random.choice(["pending", "processed"]),
                    handler_id=handler.id if handler else None,
                    handle_note="已更新知识库" if handler else None,
                    ai_suggestion=None,
                    ai_suggestion_at=None,
                    created_at=created_at,
                    handled_at=created_at + timedelta(days=random.randint(1, 3)) if handler else None
                )
                db.add(qa_feedback)

    db.commit()
    print(f"\n  [STAT] 总计创建/更新问答记录: {len(all_records)} 条")
    return all_records


def create_comments(db: Session, all_users: list, all_tickets: list) -> list:
    """创建评论(针对工单的评论)"""
    print("\n[COMM] 创建评论...")
    all_comments = []

    # 评论内容模板
    comment_templates = [
        "收到,我会尽快处理.",
        "请问还有其他需要补充的吗?",
        "已经提交审批,请等待.",
        "材料已收到,正在处理中.",
        "请补充一下相关证明材料.",
        "已处理完成,请查收.",
        "感谢您的配合!",
        "如有问题请随时联系.",
    ]

    # 为部分工单创建评论
    tickets_for_comments = random.sample(
        all_tickets,
        min(len(all_tickets) // 2, 30)
    )

    for ticket in tickets_for_comments:
        # 1-3条评论
        num_comments = random.randint(1, 3)

        for i in range(num_comments):
            # 随机选择评论者(创建者或处理人)
            if ticket.assignee_id and random.random() < 0.5:
                commenter_id = ticket.assignee_id
            else:
                commenter_id = ticket.creator_id

            # 检查是否已有评论
            existing = db.query(Comment).filter(
                Comment.target_type == "ticket",
                Comment.target_id == ticket.id,
                Comment.user_id == commenter_id
            ).first()

            if existing:
                all_comments.append(existing)
                continue

            comment = Comment(
                target_type="ticket",
                target_id=ticket.id,
                user_id=commenter_id,
                content=random.choice(comment_templates),
                parent_id=None,
                like_count=random.randint(0, 5),
                is_adopted=0,
                status=1,
                created_at=ticket.created_at + timedelta(hours=random.randint(1, 24))
            )
            db.add(comment)
            db.flush()
            all_comments.append(comment)

    db.commit()
    print(f"  [STAT] 总计创建/更新评论: {len(all_comments)} 条")
    return all_comments


def create_qa_miss(db: Session, all_users: list) -> list:
    """创建未命中问题记录"""
    print("\n[QA] 创建未命中问题...")
    all_misses = []

    miss_questions = [
        "公司有没有健身房?",
        "如何申请加班餐补?",
        "年假可以跨年使用吗?",
        "公司有班车吗?",
        "如何开具无犯罪记录证明?",
        "公积金缴纳比例是多少?",
        "公司有员工宿舍吗?",
        "如何申请调岗?",
    ]

    # 随机选择一些用户创建未命中问题
    num_users = random.randint(len(all_users) // 3, len(all_users) // 2)
    selected_users = random.sample(all_users, min(num_users, len(all_users)))

    for user in selected_users:
        num_questions = random.randint(1, 2)
        selected_q = random.sample(miss_questions, min(num_questions, len(miss_questions)))

        for question in selected_q:
            # 检查是否已存在
            existing = db.query(QAMiss).filter(
                QAMiss.user_id == user.id,
                QAMiss.question == question
            ).first()

            if existing:
                all_misses.append(existing)
                continue

            miss = QAMiss(
                user_id=user.id,
                question=question,
                cluster_id=random.randint(1, 5) if random.random() < 0.5 else None,
                resolved=1 if random.random() < 0.3 else 0,
                resolved_doc_id=None,
                created_at=random_date(start_days_ago=14, end_days_ago=0)
            )
            db.add(miss)
            all_misses.append(miss)

    db.commit()
    print(f"  [STAT] 总计创建/更新未命中问题: {len(all_misses)} 条")
    return all_misses


# ==================== 主函数 ====================

def main():
    """主函数:生成所有测试数据"""
    print("=" * 60)
    print("[START] HR Copilot Test Data Generator")
    print("=" * 60)
    print(f"\n[DB] Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
    print(f"[TIME] Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    db = SessionLocal()

    try:
        # 1. 创建部门
        dept_map = create_departments(db)

        # 2. 创建用户
        all_users = create_users(db, dept_map)

        # 3. 创建工单
        all_tickets = create_tickets(db, all_users)

        # 4. 创建公告
        all_notices = create_notices(db, all_users)

        # 5. 创建问答记录
        all_records = create_qa_records(db, all_users)

        # 6. 创建评论
        all_comments = create_comments(db, all_users, all_tickets)

        # 7. 创建未命中问题
        all_misses = create_qa_miss(db, all_users)

        # 打印统计信息
        print("\n" + "=" * 60)
        print("[STAT] Data Generation Statistics")
        print("=" * 60)
        print(f"  [DEPT] Departments: {len(dept_map)}")
        print(f"  [USER] Users: {len(all_users)}")
        print(f"  [TICK] Tickets: {len(all_tickets)}")
        print(f"  [NOTE] Notices: {len(all_notices)}")
        print(f"  [QA] QA Records: {len(all_records)}")
        print(f"  [COMM] Comments: {len(all_comments)}")
        print(f"  [MISS] Missed Questions: {len(all_misses)}")

        # 打印默认账号信息
        print("\n" + "=" * 60)
        print("[ACCOUNT] Test Account Information")
        print("=" * 60)
        print("  Default Password: 123456")
        print("\n  HR Accounts (1 per department):")
        for dept_name, user_list in USER_POOL.items():
            hr_user = next((u for u in user_list if u[2] == "hr"), None)
            if hr_user:
                print(f"    - {dept_name}: {hr_user[0]} ({hr_user[1]})")

        print("\n  Employee Account Examples:")
        for dept_name, user_list in list(USER_POOL.items())[:2]:
            emp_user = next((u for u in user_list if u[2] == "employee"), None)
            if emp_user:
                print(f"    - {dept_name}: {emp_user[0]} ({emp_user[1]})")

        print("\n" + "=" * 60)
        print("[SUCCESS] Test data generation completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
