"""初始化新员工速查指引数据"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, SessionLocal, Base
from app.models.guide import GuideCategory, GuideItem

# 确保表存在
Base.metadata.create_all(bind=engine)

# 原始数据
INITIAL_DATA = [
    {
        "title": "日常办公",
        "items": [
            {
                "question": "办公用品如何选购？",
                "answer": (
                    "1. 登录公司 OA →「行政服务」→「办公用品申领」\n"
                    "2. 选择常用耗材（笔、纸、文件夹等）并填写数量\n"
                    "3. 部门负责人审批后，行政部每周二、四统一配送至工位\n"
                    "4. 紧急需求可联系行政前台（内线 8001）说明用途\n\n"
                    "提示：单价超过 200 元的物品需提前 1 个工作日申请。"
                ),
            },
            {
                "question": "如何预约会议室？",
                "answer": (
                    "在企业日历中搜索「会议室预订」，选择楼层与时段提交即可。\n"
                    "超过 20 人的会议请提前 1 天预订，并注明是否需要投影/视频会议设备。"
                ),
            },
            {
                "question": "电脑/网络问题找谁？",
                "answer": (
                    "IT 服务台：内线 8090 或企业微信「IT 小助手」。\n"
                    "常见问题（VPN、邮箱、打印机）可先查看 IT 知识库自助解决。"
                ),
            },
        ],
    },
    {
        "title": "考勤与请假",
        "items": [
            {
                "question": "如何请假？",
                "answer": (
                    "1. OA →「考勤管理」→「请假申请」\n"
                    "2. 选择假别（事假/病假/年假等），填写起止时间与事由\n"
                    "3. 直属上级审批；3 天以上假期需部门负责人 + HR 备案\n\n"
                    "病假超过 1 天需上传医院证明；年假需确保余额充足。"
                ),
            },
            {
                "question": "年假有多少天？",
                "answer": (
                    "按《休假与年假管理办法》：\n"
                    "- 工龄 1–10 年：5 天/年\n"
                    "- 工龄 10–20 年：10 天/年\n"
                    "- 工龄 20 年以上：15 天/年\n\n"
                    "具体天数可在 OA 考勤模块查看「年假余额」。"
                ),
            },
            {
                "question": "迟到/忘打卡怎么办？",
                "answer": (
                    "1. 忘记打卡：OA 提交「考勤异常说明」，选择日期与原因\n"
                    "2. 或在智能问答「办事项」中发起考勤异常工单\n"
                    "3. 每月补卡机会有限，频繁异常将影响绩效\n\n"
                    "也可在智能问答中问「迟到怎么处理」了解制度规定。"
                ),
            },
        ],
    },
    {
        "title": "人事与福利",
        "items": [
            {
                "question": "如何开具在职/收入证明？",
                "answer": (
                    "智能问答 → 选择「办事项」→ 说明「我要开在职证明」。\n"
                    "按提示填写用途、接收单位、是否需要盖章等信息，提交后 HR 会在 1–3 个工作日处理。"
                ),
            },
            {
                "question": "手机号/邮箱变更怎么办理？",
                "answer": (
                    "智能问答「办事项」→「个人信息变更」，填写原信息与新信息。\n"
                    "也可携带有效证件到 HR 窗口办理，变更后请同步更新 OA 个人信息。"
                ),
            },
            {
                "question": "报销流程是什么？",
                "answer": (
                    "1. 费用发生后 30 天内，OA →「财务报销」上传发票与明细\n"
                    "2. 选择费用类型（差旅/交通/餐饮等），关联项目或部门\n"
                    "3. 审批通过后财务打款，一般 5–10 个工作日到账"
                ),
            },
        ],
    },
    {
        "title": "系统使用",
        "items": [
            {
                "question": "智能问答「查制度」能做什么？",
                "answer": (
                    "用于查询公司制度：年假、请假、考勤、薪酬、绩效、入职转正等。\n"
                    "示例：「年假有几天？」「婚假多少天？」「试用期多久？」"
                ),
            },
            {
                "question": "智能问答「办事项」能做什么？",
                "answer": (
                    "用于发起 HR 工单：在职证明、信息变更、考勤异常说明等。\n"
                    "选择「办事项」模式后，用自然语言说明需求，系统会引导您补全信息。"
                ),
            },
            {
                "question": "在哪里看公司通知？",
                "answer": "左侧菜单「通知公告」可查看全部、未读、置顶通知；重要政策变更会以置顶公告发布。",
            },
        ],
    },
]


def init_guide_data():
    """初始化指引数据"""
    db = SessionLocal()
    try:
        # 检查是否已有数据
        existing_count = db.query(GuideCategory).count()
        if existing_count > 0:
            print(f"数据库中已有 {existing_count} 个分类，跳过初始化")
            return

        # 插入数据
        for i, cat_data in enumerate(INITIAL_DATA):
            category = GuideCategory(
                title=cat_data["title"],
                sort_order=i
            )
            db.add(category)
            db.flush()  # 获取ID

            for j, item_data in enumerate(cat_data["items"]):
                item = GuideItem(
                    category_id=category.id,
                    question=item_data["question"],
                    answer=item_data["answer"],
                    sort_order=j
                )
                db.add(item)

        db.commit()
        print(f"成功初始化 {len(INITIAL_DATA)} 个分类的指引数据")
    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_guide_data()
