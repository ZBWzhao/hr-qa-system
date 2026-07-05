import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.core.database import engine, SessionLocal, Base
from app.core.security import get_password_hash
from app.models.user import User
from app.models.department import Department
from app.models.document import Document, DocumentChunk, DocumentVersion
from app.models.qa import QARecord, Rule, QAFeedback, QAMiss
from app.models.notice import Notice, NoticeRead
from app.models.ticket import Ticket
from app.models.comment import Comment
from app.models.reminder import ReminderRule, ReminderLog
import re


def split_text_to_chunks(text, chunk_size=400):
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current = ""
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if len(current) + len(p) > chunk_size and current:
            chunks.append(current.strip())
            current = p
        else:
            current = current + "\n\n" + p if current else p
    if current.strip():
        chunks.append(current.strip())
    return chunks


def extract_keywords(text):
    words = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return ",".join([w for w, _ in sorted_words[:10]])


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Department).count() > 0:
            print("Database already initialized.")
            return

        depts = [
            Department(name="人力资源部", parent_id=None, sort_order=1),
            Department(name="技术部", parent_id=None, sort_order=2),
            Department(name="市场部", parent_id=None, sort_order=3),
            Department(name="财务部", parent_id=None, sort_order=4),
            Department(name="行政部", parent_id=None, sort_order=5),
        ]
        for d in depts:
            db.add(d)
        db.flush()

        users = [
            User(username="admin", password_hash=get_password_hash("123456"), real_name="系统管理员", email="admin@company.com", department_id=depts[0].id, role="admin", status=1, hire_date=datetime(2020, 1, 1)),
            User(username="hr001", password_hash=get_password_hash("123456"), real_name="张丽", email="hr001@company.com", department_id=depts[0].id, role="hr", status=1, hire_date=datetime(2022, 3, 15)),
            User(username="emp001", password_hash=get_password_hash("123456"), real_name="李明", email="emp001@company.com", department_id=depts[1].id, role="employee", status=1, hire_date=datetime(2025, 6, 1), contract_end_date=datetime(2028, 6, 1), probation_end_date=datetime(2025, 9, 1)),
        ]
        for u in users:
            db.add(u)
        db.flush()

        doc_contents = {
            "考勤管理制度": """第一章 总则
第一条 为规范公司考勤管理，维护正常工作秩序，根据国家相关法律法规，结合公司实际情况，制定本制度。
第二条 本制度适用于公司全体员工。

第二章 工作时间
第三条 公司实行标准工时制，每周工作五天，休息两天。
第四条 工作时间为上午9:00至12:00，下午13:30至18:00。
第五条 因工作需要，经部门负责人批准，可安排弹性工作时间，但每天工作时间不少于8小时。

第三章 打卡管理
第六条 员工每日须通过公司考勤系统进行上下班打卡。
第七条 忘记打卡的员工应在当日内通过系统提交补卡申请，经直属上级审批后生效。
第八条 每月允许补卡次数不超过3次，超过3次需HR审批。
第九条 未打卡且未补卡的视为旷工处理。

第四章 迟到早退
第十条 迟到或早退30分钟以内，每次扣减当月绩效分1分。
第十一条 迟到或早退30分钟以上1小时以内，按旷工半天处理。
第十二条 迟到或早退1小时以上，按旷工1天处理。
第十三条 每月迟到早退累计3次及以上，将给予书面警告。

第五章 加班管理
第十四条 公司提倡高效工作，原则上不鼓励加班。
第十五条 确因工作需要加班的，须提前通过系统提交加班申请，经部门负责人审批。
第十六条 工作日加班可选择调休或按1.5倍计算加班费。
第十七条 周末加班可选择调休或按2倍计算加班费。
第十八条 法定节假日加班按3倍计算加班费。
第十九条 调休须在加班后3个月内使用完毕，逾期自动作废。

第六章 请假制度
第二十条 员工请假须提前通过OA系统提交申请，审批流程如下：
1天以内：直属上级审批
1-3天：部门负责人审批
3天以上：HR审批
第二十一条 病假须提供医院证明，3天以上病假需提供二级以上医院证明。
第二十二条 事假每月累计不超过3天，超过需HR审批。""",

            "休假与年假管理办法": """第一章 总则
第一条 为保障员工休假权利，规范休假管理，根据《职工带薪年休假条例》等法规，制定本办法。

第二章 法定节假日
第二条 员工依法享受国家规定的法定节假日，包括：
元旦1天、春节3天、清明节1天、劳动节1天、端午节1天、中秋节1天、国庆节3天。

第三章 带薪年假
第三条 员工入职满一年后，享受带薪年假。年假天数按工龄计算：
工龄1年以上不满10年：5天
工龄10年以上不满20年：10天
工龄20年以上：15天
第四条 年假在一个年度内可以集中安排，也可以分段安排，一般不跨年度安排。
第五条 公司因工作需要不能安排年假的，经员工本人同意，可以不安排年假，按照日工资的300%支付年假报酬。
第六条 年假当年未使用完毕的，次年3月31日前可申请补休，逾期自动清零。
第七条 新入职员工当年度年休假天数按照入职后剩余日历天数折算，折算后不足1天的不享受年假。

第四章 婚假
第八条 员工依法登记结婚，可享受婚假3天。
第九条 婚假须在领证后6个月内使用完毕。

第五章 产假
第十条 女员工生育享受产假98天，其中产前可以休假15天。
第十一条 难产的增加产假15天，多胞胎每多生育一个增加15天。
第十二条 男员工享受陪产假15天。

第六章 丧假
第十三条 员工直系亲属去世，可享受丧假3天。
第十四条 员工岳父母或公婆去世，可享受丧假1-3天。

第七章 请假流程
第十五条 请假须提前在OA系统提交申请，注明请假类型、起止时间及事由。
第十六条 年假申请需提前3个工作日，其他假期需提前1个工作日。
第十七条 紧急情况可先电话请假，事后补办手续。""",

            "薪酬福利制度": """第一章 总则
第一条 为建立规范合理的薪酬体系，吸引和保留优秀人才，制定本制度。

第二章 薪酬结构
第二条 员工薪酬由基本工资、岗位工资、绩效工资和津贴补贴组成。
第三条 基本工资根据岗位等级确定，岗位工资根据岗位职责和任职资格确定。
第四条 绩效工资根据个人绩效考核结果发放，具体比例按照各岗位绩效方案执行。
第五条 津贴补贴包括：交通补贴、通讯补贴、餐饮补贴等。

第三章 薪资发放
第六条 公司实行月薪制，每月15日发放上月工资，遇节假日提前发放。
第七条 新入职员工薪资自报到之日起计算。
第八条 员工薪资通过银行转账方式发放至个人账户。

第四章 绩效奖金
第九条 公司根据年度经营情况和个人绩效发放年终奖金。
第十条 年终奖金一般于次年春节前发放。
第十一条 年中离职的员工不享受当年度年终奖金。

第五章 社会保险
第十二条 公司按照国家规定为员工缴纳五险一金，包括：
养老保险、医疗保险、失业保险、工伤保险、生育保险、住房公积金。
第十三条 社保缴纳基数按照员工上年度月平均工资确定。

第六章 补充福利
第十四条 公司提供以下补充福利：
1. 商业保险：公司为员工购买补充医疗保险和意外险；
2. 节日福利：春节、端午、中秋等节日发放节日礼品或礼金；
3. 生日福利：员工生日当月发放生日礼金200元；
4. 健康体检：每年组织一次免费健康体检；
5. 培训发展：提供各类培训和学习机会。

第七章 报销制度
第十五条 因公产生的费用可在规定标准内报销。
第十六条 报销流程：
1. 填写报销申请单，附上原始发票；
2. 部门负责人审批（1000元以内）；
3. 财务部审核；
4. 总经理审批（5000元以上）；
5. 财务部付款。
第十七条 报销须在费用发生后30天内提交，逾期不予报销。""",

            "绩效考核制度": """第一章 总则
第一条 为建立科学的绩效管理体系，促进员工和公司共同发展，制定本制度。

第二章 考核原则
第二条 绩效考核坚持公平、公正、公开的原则。
第三条 考核结果作为员工薪酬调整、晋升、培训的重要依据。

第三章 考核周期
第四条 绩效考核分为月度考核和年度考核。
第五条 月度考核于次月5日前完成，年度考核于次年1月31日前完成。

第四章 考核内容
第六条 绩效考核内容包括：
1. 工作业绩（60%）：完成工作任务的数量和质量；
2. 工作能力（20%）：专业技能、沟通能力、学习能力等；
3. 工作态度（20%）：责任心、主动性、团队合作等。

第五章 考核流程
第七条 绩效考核流程：
1. 员工自评（权重20%）；
2. 直属上级评价（权重50%）；
3. 跨部门评价（权重30%）；
4. HR汇总审核；
5. 绩效面谈。

第六章 考核等级
第八条 绩效考核结果分为五个等级：
优秀（A）：90分以上，占比不超过15%；
良好（B）：80-89分，占比不超过30%；
合格（C）：70-79分；
待改进（D）：60-69分；
不合格（E）：60分以下。

第七章 绩效申诉
第九条 员工对考核结果有异议的，可在结果公布后5个工作日内提出书面申诉。
第十条 申诉流程：
1. 向直属上级提出申诉；
2. 如对处理结果不满，可向HR部门提出书面申诉；
3. HR部门在收到申诉后10个工作日内完成调查并反馈结果；
4. 申诉结果为最终决定。

第八章 结果应用
第十一条 绩效考核结果应用于：
1. 绩效奖金发放；
2. 薪资调整；
3. 职位晋升；
4. 培训需求分析；
5. 劳动合同续签。""",

            "员工入职与转正管理办法": """第一章 总则
第一条 为规范员工入职和转正管理流程，帮助新员工快速融入公司，制定本办法。

第二章 入职准备
第二条 HR部门在员工入职前完成以下准备工作：
1. 发送录用通知书，明确入职时间、地点、需携带材料；
2. 准备办公设备、工位、门禁卡等；
3. 开通邮箱、OA系统等账号；
4. 通知用人部门做好接待准备。

第三条 新员工入职当天需提交以下材料：
1. 身份证原件及复印件；
2. 学历证书原件及复印件；
3. 离职证明；
4. 近期一寸照片2张；
5. 银行卡信息；
6. 体检报告。

第三章 入职流程
第四条 入职当日流程：
1. HR办理入职手续，签订劳动合同；
2. 发放员工手册和入职指引；
3. 介绍公司概况和企业文化；
4. 引导至用人部门，介绍部门同事；
5. 由导师带领熟悉工作环境。

第四章 试用期管理
第五条 试用期为3个月，自入职之日起计算。
第六条 试用期工资为转正工资的80%。
第七条 试用期内，员工需完成以下任务：
1. 熟悉公司制度和业务流程；
2. 完成部门安排的培训课程；
3. 通过试用期考核。
第八条 试用期考核内容：
1. 专业技能（40%）；
2. 工作态度（30%）；
3. 学习能力（20%）；
4. 团队融入（10%）。

第五章 转正流程
第九条 试用期满前15天，HR通知员工和用人部门启动转正评估。
第十条 转正流程：
1. 员工提交转正申请和试用期工作总结；
2. 直属上级填写转正评估表；
3. 部门负责人审批；
4. HR部门审核；
5. 总经理审批（主管级以上）。
第十一条 转正审批通过后，HR更新系统信息，次月起按转正工资发放。
第十二条 试用期考核不合格的，可延长试用期1个月或解除劳动合同。

第六章 新员工培训
第十三条 新员工入职培训包括：
1. 公司概况和企业文化；
2. 规章制度和行为规范；
3. 业务流程和产品知识；
4. 安全和保密教育。
第十四条 部门培训由导师负责，为期1个月，包含岗位技能培训和实操练习。"""
        }

        doc_list = [
            ("考勤管理制度", "attendance"),
            ("休假与年假管理办法", "leave"),
            ("薪酬福利制度", "salary"),
            ("绩效考核制度", "performance"),
            ("员工入职与转正管理办法", "other"),
        ]

        for title, category in doc_list:
            content = doc_contents[title]
            doc = Document(
                title=title,
                category=category,
                content_text=content,
                version="1.0",
                status="published",
                uploader_id=users[0].id
            )
            db.add(doc)
            db.flush()

            chunks = split_text_to_chunks(content)
            for i, chunk in enumerate(chunks):
                keywords = extract_keywords(chunk)
                doc_chunk = DocumentChunk(document_id=doc.id, chunk_index=i, content=chunk, keywords=keywords)
                db.add(doc_chunk)

            version_record = DocumentVersion(document_id=doc.id, version="1.0", content_text=content, created_by=users[0].id)
            db.add(version_record)

        rules = [
            ("HR联系方式查询", "客服电话,HR电话,联系HR,HR联系方式", "HR部门联系方式：\n- 电话：010-88888888\n- 邮箱：hr@company.com\n- 办公地点：总部大楼3层人力资源部\n- 工作时间：周一至周五 9:00-18:00\n\n如有紧急事务，可拨打HR直线：13800138000", "contact", 10),
            ("工作时间查询", "上班时间,工作时间,上下班,几点上班", "公司工作时间：\n- 上午：9:00 - 12:00\n- 午休：12:00 - 13:30\n- 下午：13:30 - 18:00\n- 周六日休息\n\n实行标准工时制，每天工作8小时。", "attendance", 9),
            ("补卡规则", "打卡,忘记打卡,补卡,漏打卡", "忘记打卡补卡规则：\n1. 当日内通过考勤系统提交补卡申请\n2. 经直属上级审批后生效\n3. 每月允许补卡次数不超过3次\n4. 超过3次需HR审批\n5. 未打卡且未补卡的视为旷工\n\n请养成按时打卡的好习惯！", "attendance", 8),
            ("迟到早退规则", "迟到,早退,迟到怎么处理,早退怎么处理,考勤异常说明", "迟到早退处理规定：\n1. 迟到或早退30分钟以内：每次扣减当月绩效分1分\n2. 30分钟以上1小时以内：按旷工半天处理\n3. 1小时以上：按旷工1天处理\n4. 每月迟到早退累计3次及以上：给予书面警告\n5. 超过30分钟或特殊情况：建议提交考勤异常说明，经直属上级审批\n\n请合理安排时间，按时到岗。", "attendance", 7),
        ]

        for name, kw, answer, cat, priority in rules:
            rule = Rule(name=name, trigger_keywords=kw, answer_template=answer, category=cat, priority=priority, created_by=users[1].id)
            db.add(rule)

        notices = [
            Notice(title="2026年端午节放假通知", content="根据国家规定，2026年端午节放假安排如下：\n\n放假时间：6月19日（星期五）至6月21日（星期日），共3天。\n6月22日（星期一）正常上班。\n\n请各部门提前做好工作安排，确保假期期间值班人员到位。\n\n祝大家端午节快乐！", notice_type="holiday", is_pinned=1, publisher_id=users[1].id),
            Notice(title="年假清零提醒", content="各位同事：\n\n根据公司《休假与年假管理办法》规定，上年度未使用完毕的年假将于2026年3月31日自动清零。\n\n请各位同事合理安排时间，在截止日期前使用剩余年假。\n\n如有疑问，请联系HR部门。", notice_type="reminder", is_pinned=0, publisher_id=users[1].id, expire_at=datetime(2026, 3, 31)),
            Notice(title="新版考勤制度发布通知", content="各位同事：\n\n为规范公司考勤管理，公司修订了《考勤管理制度》（2026年版），现予以发布。\n\n主要变化：\n1. 弹性工作时间调整为每月可申请3次\n2. 补卡次数调整为每月不超过3次\n3. 新增远程办公相关规定\n\n新制度自2026年7月1日起执行，请各部门组织学习。\n\n制度全文请查看制度文档库。", notice_type="policy", is_pinned=1, publisher_id=users[1].id),
        ]
        for n in notices:
            db.add(n)

        tickets = [
            Ticket(ticket_no="TK202606010001", type="certify", title="开具在职证明", description="因办理签证需要，请开具在职证明一份，需中英文版本。", status="pending", creator_id=users[2].id),
            Ticket(ticket_no="TK202606010002", type="info_change", title="修改个人信息", description="手机号码变更，需要更新为13800138000。", status="processing", creator_id=users[2].id, assignee_id=users[1].id),
            Ticket(ticket_no="TK202606010003", type="other", title="咨询社保缴纳", description="请问社保缴纳基数是如何确定的？需要提供什么材料？", status="completed", creator_id=users[2].id, assignee_id=users[1].id, resolve_note="社保缴纳基数按照上年度月平均工资确定，无需额外提供材料，系统自动调整。", resolved_at=datetime.now() - timedelta(days=2)),
            Ticket(ticket_no="TK202606010004", type="leave_request", title="请假申请", description="请假类型：病假\n开始日期：7月10日\n结束日期：7月12日\n请假事由：身体不适需要休息", status="pending", creator_id=users[2].id),
            Ticket(ticket_no="TK202606010005", type="resignation", title="离职申请", description="离职原因：个人发展原因\n期望离职日期：8月1日\n工作交接人：张三", status="pending", creator_id=users[2].id),
        ]
        for t in tickets:
            db.add(t)

        reminder_rules = [
            ReminderRule(name="合同到期提醒", rule_type="contract", trigger_days=30, target_role="employee", channels="site,email", template="您的劳动合同将于{date}到期，请及时与HR联系续签事宜。"),
            ReminderRule(name="试用期到期提醒", rule_type="probation", trigger_days=7, target_role="employee", channels="site", template="您的试用期将于{date}到期，请提前准备转正申请材料。"),
            ReminderRule(name="年假清零提醒", rule_type="annual_leave", trigger_days=30, target_role="employee", channels="site,email", template="您还有{days}天年假未使用，请在年底前合理安排。"),
        ]
        for r in reminder_rules:
            db.add(r)

        db.commit()
        print("Database initialized successfully!")
        print("Demo accounts:")
        print("  admin / 123456 (管理员)")
        print("  hr001 / 123456 (HR人员)")
        print("  emp001 / 123456 (普通员工)")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
