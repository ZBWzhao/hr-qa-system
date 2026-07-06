#!/usr/bin/env python3
"""
为每个部门创建专属制度文档
============================
功能:
- 为人力资源部、技术部、市场部、财务部、行政部各创建一份专属制度文档
- 文档状态设为已发布，并建立向量索引
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from app.core.config import settings
from app.models.department import Department
from app.models.user import User
from app.models.document import Document, DocumentChunk, DocumentVersion
from app.services.rag.vectorstore import add_documents, delete_document
import re

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def split_text_to_chunks(text: str, chunk_size: int = 400) -> list:
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
    final = []
    for chunk in chunks:
        if len(chunk) > chunk_size * 2:
            for i in range(0, len(chunk), chunk_size):
                final.append(chunk[i:i + chunk_size])
        else:
            final.append(chunk)
    return final


def extract_keywords(text: str) -> str:
    words = re.findall(r'[一-鿿]{2,6}', text)
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return ",".join([w for w, _ in sorted_words[:10]])


# ==================== 各部门专属制度文档内容 ====================

DEPARTMENT_DOCUMENTS = {
    "人力资源部": {
        "title": "人力资源部内部管理制度",
        "category": "other",
        "content": """
# 人力资源部内部管理制度

## 一、部门职责

人力资源部是公司人才管理的核心部门，主要负责以下工作：
1. 招聘与配置：制定招聘计划，组织面试选拔，办理入职手续
2. 培训与发展：制定培训计划，组织新员工入职培训，推进职业发展通道建设
3. 薪酬福利：制定薪酬体系，核算工资，管理五险一金和补充福利
4. 绩效管理：制定绩效考核方案，组织季度/年度考核，反馈考核结果
5. 员工关系：处理劳动纠纷，组织员工活动，维护企业文化

## 二、招聘管理规范

### 2.1 招聘流程
1. 各部门提交用人需求申请表
2. HR审核并发布招聘信息
3. 简历筛选（3个工作日内完成）
4. 初试（HR面试）→ 复试（部门负责人面试）
5. 背景调查
6. 发放offer并办理入职

### 2.2 面试评估标准
- 专业能力（40%）：岗位相关技能和经验
- 综合素质（30%）：沟通能力、团队协作、学习能力
- 文化匹配（20%）：价值观与公司文化契合度
- 发展潜力（10%）：成长空间和职业规划

## 三、培训管理制度

### 3.1 新员工培训
- 入职第1天：公司介绍、制度学习、系统账号开通
- 入职第1周：部门轮岗了解、导师分配
- 入职第1月：岗位技能培训、首次面谈

### 3.2 在职培训
- 每月至少1次部门内训
- 每季度1次跨部门交流
- 年度外部培训预算：每人3000元

## 四、考勤管理

### 4.1 工作时间
- 标准工时：周一至周五 9:00-18:00（午休12:00-13:30）
- 弹性工时：核心工作时间 10:00-16:00

### 4.2 加班管理
- 工作日加班：需提前申请，按1.5倍计算
- 周末加班：按2倍计算
- 法定节假日：按3倍计算

## 五、薪酬福利

### 5.1 工资构成
- 基本工资 + 岗位工资 + 绩效工资 + 各类补贴
- 发放时间：每月15日

### 5.2 福利体系
- 五险一金：按国家规定缴纳
- 补充商业保险：入职即享
- 年度体检：每年一次
- 节日福利：春节、中秋、端午等节日礼品
- 生日福利：生日当月礼品卡200元
"""
    },
    "技术部": {
        "title": "技术部研发管理规范",
        "category": "other",
        "content": """
# 技术部研发管理规范

## 一、部门组织架构

技术部下设三个团队：
1. 前端开发组：负责Web端和移动端界面开发
2. 后端开发组：负责服务端架构和API开发
3. 测试运维组：负责质量保障和系统运维

## 二、项目管理流程

### 2.1 需求管理
1. 产品需求文档（PRD）由产品经理提交
2. 技术评审会议（每周三下午）
3. 需求排期和任务分配
4. 开发周期：常规需求2周，紧急需求3天

### 2.2 开发流程
1. 需求理解和技术方案设计（1-2天）
2. 编码开发（主体开发时间）
3. 代码自测
4. 提交Code Review
5. 测试环境部署和验证
6. 生产环境发布

### 2.3 版本发布规范
- 常规版本：每两周发布一次（周二晚上）
- 紧急修复：随时发布，需CTO审批
- 大版本：每月一次，需全员测试

## 三、代码规范

### 3.1 代码风格
- Python：遵循PEP8规范
- JavaScript/Vue：使用ESLint + Prettier
- 提交信息格式：`<type>(<scope>): <subject>`
  - type: feat/fix/docs/style/refactor/test/chore

### 3.2 代码审查要求
- 所有代码必须经过至少1人审查
- 审查重点：逻辑正确性、安全性、性能、可维护性
- 审查时间：不超过24小时

## 四、技术栈规范

### 4.1 前端技术栈
- 框架：Vue 3 + Composition API
- UI组件库：Element Plus
- 构建工具：Vite
- 状态管理：Pinia

### 4.2 后端技术栈
- 语言：Python 3.11+
- 框架：FastAPI
- 数据库：MySQL 8.0
- 缓存：Redis
- 向量数据库：ChromaDB

## 五、值班与应急

### 5.1 技术值班
- 值班周期：每人一周
- 值班职责：处理线上告警、响应紧急问题
- 值班补贴：500元/周

### 5.2 应急响应
- P0故障（系统宕机）：15分钟内响应，1小时内修复
- P1故障（功能异常）：30分钟内响应，4小时内修复
- P2故障（体验问题）：2小时内响应，24小时内修复

## 六、开发设备与环境

### 6.1 设备配置
- 开发机：MacBook Pro 或同等配置笔记本
- 显示器：27寸4K显示器
- 使用周期：3年更换

### 6.2 云服务资源
- 开发服务器：按需申请
- 测试环境：部门共享
- 生产环境：运维统一管理
"""
    },
    "市场部": {
        "title": "市场部运营管理制度",
        "category": "other",
        "content": """
# 市场部运营管理制度

## 一、部门职能

市场部是公司品牌推广和业务拓展的核心部门：
1. 品牌管理：公司品牌形象维护、品牌传播策略制定
2. 市场推广：线上线下推广活动策划与执行
3. 客户关系：客户开发、维护、满意度管理
4. 数据分析：市场调研、竞品分析、数据报告

## 二、品牌管理规范

### 2.1 品牌形象标准
- Logo使用：必须使用官方版本，不得变形、变色
- 品牌色彩：主色#D97706，辅色#059669
- 字体规范：标题使用思源黑体，正文使用苹方

### 2.2 对外宣传审核
- 所有对外物料需经部门负责人审批
- 新闻稿、PR稿件需经CEO办公室审批
- 社交媒体发布需提前1天报备

## 三、推广活动管理

### 3.1 活动策划流程
1. 活动方案撰写（目标、预算、时间、人员）
2. 方案评审（部门内评审 → 管理层审批）
3. 资源协调和供应商对接
4. 活动执行
5. 效果评估和复盘

### 3.2 预算管理
- 单次活动预算：5000元以下部门自行审批
- 单次活动预算：5000-20000元需VP审批
- 单次活动预算：20000元以上需CEO审批

## 四、客户管理

### 4.1 客户分级
- A类客户（战略客户）：年合作金额50万以上
- B类客户（重要客户）：年合作金额10-50万
- C类客户（普通客户）：年合作金额10万以下

### 4.2 客户维护频率
- A类客户：每周至少1次沟通
- B类客户：每月至少2次沟通
- C类客户：每月至少1次沟通

## 五、市场数据管理

### 5.1 数据报告周期
- 周报：每周一提交上周数据
- 月报：每月3日前提交上月数据
- 季度报告：每季度首月10日前提交

### 5.2 竞品分析
- 每月进行一次竞品动态分析
- 重点监控3-5个核心竞品
- 形成竞品分析报告并分享给产品部

## 六、媒体关系

### 6.1 媒体对接规范
- 媒体采访需提前3天报备
- 统一由市场部对外发言
- 禁止未经授权向媒体透露公司信息

### 6.2 危机公关
- 负面舆情2小时内响应
- 成立临时危机处理小组
- 统一口径，及时通报进展

## 七、物料管理

### 7.1 宣传物料清单
- 公司宣传册、产品手册
- 名片、工牌、文化衫
- 展架、海报、易拉宝

### 7.2 物料领用
- 填写物料领用申请表
- 部门负责人签字
- 行政部统一发放
"""
    },
    "财务部": {
        "title": "财务部报销与审批管理制度",
        "category": "salary",
        "content": """
# 财务部报销与审批管理制度

## 一、部门职责

财务部是公司财务管理的核心部门：
1. 会计核算：日常账务处理、凭证编制、报表编制
2. 资金管理：资金调度、银行对账、现金流管理
3. 税务管理：纳税申报、税务筹划、发票管理
4. 预算管理：年度预算编制、预算执行监控、预算分析
5. 费用报销：员工报销审核、付款处理

## 二、报销制度

### 2.1 报销时效
- 费用发生后30天内必须提交报销
- 超过30天需部门负责人特批
- 超过90天原则上不予报销

### 2.2 报销流程
1. 员工填写报销单并粘贴发票
2. 部门负责人审批
3. 财务部审核（1-3个工作日）
4. 总经理审批（单笔5000元以上）
5. 出纳付款（审批通过后5个工作日内）

### 2.3 发票要求
- 必须是正规增值税发票
- 发票抬头：公司全称
- 发票内容需与实际消费一致
- 电子发票需打印后粘贴

## 三、差旅费标准

### 3.1 交通费
- 高铁：二等座
- 飞机：经济舱（提前7天预订）
- 市内交通：出租车/网约车（需说明原因）

### 3.2 住宿费
- 一线城市：不超过500元/晚
- 二线城市：不超过400元/晚
- 其他城市：不超过300元/晚

### 3.3 餐饮补贴
- 一线城市：150元/天
- 二线城市：120元/天
- 其他城市：100元/天

## 四、付款审批权限

### 4.1 审批额度
- 单笔5000元以下：部门负责人审批
- 单笔5000-20000元：财务总监审批
- 单笔20000-100000元：总经理审批
- 单笔100000元以上：董事会审批

### 4.2 特殊付款
- 紧急付款：需总经理特批，事后补签
- 预付款：需签订合同，按合同约定执行
- 押金：需注明退还条件和时间

## 五、工资发放

### 5.1 发放时间
- 每月15日发放上月工资
- 遇节假日提前至最近工作日

### 5.2 工资构成
- 基本工资 + 岗位工资 + 绩效工资
- 各类补贴（餐补、交通、通讯）
- 代扣代缴（社保、公积金、个税）

## 六、财务报表

### 6.1 报表周期
- 月报：次月10日前完成
- 季报：季后15日前完成
- 年报：次年3月31日前完成

### 6.2 报表内容
- 资产负债表
- 利润表
- 现金流量表
- 费用明细表

## 七、税务管理

### 7.1 纳税申报
- 增值税：每月15日前
- 企业所得税：季度预缴，年度汇算清缴
- 个人所得税：每月15日前代扣代缴

### 7.2 发票管理
- 开票申请需经财务审核
- 作废发票需收回全部联次
- 发票存根保管期限：5年
"""
    },
    "行政部": {
        "title": "行政部综合管理制度",
        "category": "other",
        "content": """
# 行政部综合管理制度

## 一、部门职责

行政部是公司后勤保障的核心部门：
1. 办公环境：办公区域管理、设施维护、环境美化
2. 资产管理：固定资产登记、盘点、报废处理
3. 会议管理：会议室预定、会议支持、会议纪要
4. 车辆管理：公务用车调度、车辆维护
5. 安全管理：消防安全、门禁管理、应急预案

## 二、办公环境管理

### 2.1 办公区域划分
- 开放办公区：普通员工工位
- 独立办公室：部门负责人及以上
- 会议室：大会议室（20人）、中会议室（10人）、小会议室（4人）
- 休息区：茶水间、休息室、健身区

### 2.2 环境维护
- 保洁服务：每日早晚各一次清洁
- 绿植养护：每周一次
- 设施报修：提交行政工单，24小时内响应

## 三、固定资产管理

### 3.1 资产分类
- 电子设备：电脑、显示器、打印机等
- 办公家具：桌椅、柜子、屏风等
- 电器设备：空调、冰箱、微波炉等

### 3.2 资产管理流程
1. 采购申请：填写采购单，经审批后执行
2. 入库登记：贴资产标签，录入系统
3. 领用发放：签字确认，责任到人
4. 转移调拨：填写转移单，更新台账
5. 报废处理：使用3年以上，填写报废单

## 四、会议室管理

### 4.1 预定规则
- 提前1天在系统预定
- 单次使用不超过4小时
- 超过15分钟未到自动释放

### 4.2 使用规范
- 会后清理桌面，椅子归位
- 关闭投影仪、空调、灯光
- 如有设备故障及时报修

## 五、车辆管理

### 5.1 用车申请
- 提前1天填写用车申请
- 注明用车事由、时间、目的地
- 部门负责人审批

### 5.2 车辆使用
- 公务用车优先
- 长途用车需VP审批
- 严禁私用

### 5.3 车辆维护
- 每5000公里保养一次
- 定期检查车况
- 加油使用公司油卡

## 六、安全管理

### 6.1 门禁管理
- 工作日：08:00-20:00开放
- 非工作时间：刷卡进入
- 来访登记：前台登记，被访人确认

### 6.2 消防安全
- 每季度一次消防演练
- 灭火器每月检查一次
- 安全通道保持畅通

### 6.3 应急预案
- 火灾：拨打119，有序疏散
- 停电：启动备用电源
- 设备故障：联系维修人员

## 七、办公用品管理

### 7.1 采购流程
- 每月25日前各部门提交需求
- 行政部汇总并采购
- 每月1日统一发放

### 7.2 领用标准
- 普通员工：每人每月50元额度
- 部门负责人：每人每月100元额度
- 超出额度需部门负责人特批

## 八、快递收发

### 8.1 寄件
- 填写寄件单，注明物品和费用承担部门
- 贵重物品需保价
- 公司合作快递：顺丰、京东

### 8.2 收件
- 前台统一签收
- 通知收件人领取
- 保留签收记录30天
"""
    }
}


def main():
    print("=" * 60)
    print("[START] 部门专属制度文档初始化")
    print("=" * 60)

    db = SessionLocal()

    try:
        # 获取部门映射
        departments = db.query(Department).all()
        dept_map = {d.name: d for d in departments}
        print(f"\n[DEPT] 已找到 {len(departments)} 个部门")

        # 获取HR用户（作为文档上传者）
        hr_user = db.query(User).filter(User.role == "hr").first()
        if not hr_user:
            print("[ERROR] 未找到HR用户，无法创建文档")
            return
        print(f"[USER] 文档上传者: {hr_user.real_name} (ID: {hr_user.id})")

        created_count = 0

        for dept_name, doc_data in DEPARTMENT_DOCUMENTS.items():
            dept = dept_map.get(dept_name)
            if not dept:
                print(f"\n[SKIP] 部门不存在: {dept_name}")
                continue

            # 检查是否已存在同名文档
            existing = db.query(Document).filter(
                Document.title == doc_data["title"],
                Document.department_id == dept.id
            ).first()

            if existing:
                print(f"\n[EXISTS] 文档已存在: {doc_data['title']} (ID: {existing.id})")
                # 确保已发布并索引
                if existing.status != "published":
                    existing.status = "published"
                    db.commit()
                    _index_document(db, existing)
                    print(f"  [UPDATE] 已更新为发布状态并建立索引")
                continue

            # 创建文档
            content = doc_data["content"].strip()
            doc = Document(
                title=doc_data["title"],
                category=doc_data["category"],
                content_text=content,
                version="1.0",
                status="published",
                uploader_id=hr_user.id,
                department_id=dept.id,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(doc)
            db.flush()
            print(f"\n[CREATE] 创建文档: {doc_data['title']} (ID: {doc.id})")

            # 创建文档分块
            chunks = split_text_to_chunks(content)
            for i, chunk in enumerate(chunks):
                keywords = extract_keywords(chunk)
                doc_chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=chunk,
                    keywords=keywords
                )
                db.add(doc_chunk)
            print(f"  [CHUNK] 创建 {len(chunks)} 个文档分块")

            # 创建版本记录
            version_record = DocumentVersion(
                document_id=doc.id,
                version="1.0",
                content_text=content,
                created_by=hr_user.id
            )
            db.add(version_record)

            db.commit()

            # 索引到向量数据库
            _index_document(db, doc)
            created_count += 1
            print(f"  [INDEX] 已建立向量索引")

        print("\n" + "=" * 60)
        print(f"[SUCCESS] 完成！共创建 {created_count} 个部门专属文档")
        print("=" * 60)

        # 打印文档概览
        print("\n[SUMMARY] 各部门文档概览:")
        for dept_name in DEPARTMENT_DOCUMENTS.keys():
            dept = dept_map.get(dept_name)
            if dept:
                docs = db.query(Document).filter(
                    Document.department_id == dept.id,
                    Document.status == "published"
                ).all()
                print(f"  {dept_name}: {len(docs)} 个已发布文档")
                for d in docs:
                    print(f"    - {d.title}")

    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def _index_document(db: Session, doc: Document):
    """将文档索引到向量数据库"""
    from app.services.rag.vectorstore import delete_document as delete_from_chroma

    chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).all()
    if not chunks:
        return

    delete_from_chroma(doc.id)
    chunk_dicts = [{"content": c.content, "keywords": c.keywords or ""} for c in chunks]
    add_documents(doc.id, chunk_dicts, department_id=doc.department_id)
    print(f"  [VECTOR] 已索引 {len(chunks)} 个分块到向量数据库")


if __name__ == "__main__":
    main()
