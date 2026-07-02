from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error, paginated
from app.core.config import settings
from app.schemas.qa import FAQCreate, FAQUpdate, FAQOut
from app.models.qa import FAQ
from app.models.user import User

router = APIRouter()


class KeywordRequest(BaseModel):
    question: str = ""
    answer: str = ""


@router.post("/generate-keywords")
def generate_keywords(data: KeywordRequest, current_user: User = Depends(require_roles("hr"))):
    """生成关键词 - 使用本地分词，不依赖AI"""
    import re

    question = data.question.strip()
    answer = data.answer.strip()

    if not question and not answer:
        return error("请输入问题或回答")

    # 合并问题和答案
    text = f"{question} {answer}"

    # 通用词列表
    stop_words = {
        # 疑问词
        '如何', '怎么', '什么', '为什么', '哪个', '哪些', '多少', '几',
        # 助动词/连词
        '可以', '能', '会', '要', '是', '的', '了', '吗', '呢', '吧', '啊',
        '但是', '可是', '然而', '而且', '并且', '或者', '如果', '因为', '所以',
        '然后', '接着', '首先', '其次', '最后', '同时', '另外', '此外',
        # 代词
        '我', '你', '他', '她', '它', '我们', '你们', '他们', '这个', '那个',
        '这些', '那些', '自己', '别人', '大家', '某', '某人', '某事',
        # 其他通用词
        '请', '帮', '告诉', '一下', '一些', '进行', '使用', '需要', '可能', '应该',
        '能够', '愿意', '必须', '不得不', '可以', '不能', '不会', '不要',
        '一个', '一种', '一次', '一个', '第一', '第二', '第三',
        '问题', '答案', '情况', '方面', '时候', '地方', '原因', '结果',
        '工作', '公司', '员工', '人员', '部门', '管理', '规定', '制度',
        '根据', '按照', '依据', '参照', '参考', '关于', '对于', '至于',
        '以及', '还有', '或者', '还是', '不是', '没有', '已经', '正在',
        '将要', '即将', '马上', '立即', '尽快', '尽快', '及时',
    }

    # 提取中文词（2-6个字）
    chinese_words = re.findall(r'[一-鿿]{2,6}', text)

    # 提取英文词（2个字母以上）
    english_words = re.findall(r'[a-zA-Z]{2,}', text)

    # 提取数字+单位
    number_units = re.findall(r'\d+[a-zA-Z%]+', text)

    # 合并所有词
    all_words = chinese_words + english_words + number_units

    # 过滤通用词，统计词频
    word_freq = {}
    for word in all_words:
        if word.lower() not in stop_words and len(word) >= 2:
            word_freq[word] = word_freq.get(word, 0) + 1

    # 按词频排序，取前5个
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, freq in sorted_words[:5]]

    if not keywords:
        return error("未能提取到有效关键词")

    return success({"keywords": ",".join(keywords)})


@router.get("")
def list_faqs(category: Optional[str] = None, keyword: Optional[str] = None, page: int = 1, page_size: int = 20, db: Session = Depends(get_db)):
    query = db.query(FAQ).filter(FAQ.status == 1)
    if category:
        query = query.filter(FAQ.category == category)
    if keyword:
        query = query.filter(FAQ.question.contains(keyword) | FAQ.keywords.contains(keyword))
    total = query.count()
    items = query.order_by(FAQ.sort_order, FAQ.view_count.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return paginated([FAQOut.model_validate(f).model_dump() for f in items], total, page, page_size)


@router.get("/all")
def list_all_faqs(page: int = 1, page_size: int = 20, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    query = db.query(FAQ)
    total = query.count()
    items = query.order_by(FAQ.sort_order.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return paginated([FAQOut.model_validate(f).model_dump() for f in items], total, page, page_size)


@router.get("/{faq_id}")
def get_faq(faq_id: int, db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        return error("FAQ不存在")
    faq.view_count += 1
    db.commit()
    return success(FAQOut.model_validate(faq).model_dump())


@router.post("")
def create_faq(data: FAQCreate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    faq = FAQ(question=data.question, answer=data.answer, category=data.category, keywords=data.keywords, sort_order=data.sort_order, created_by=current_user.id)
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return success(FAQOut.model_validate(faq).model_dump())


@router.put("/{faq_id}")
def update_faq(faq_id: int, data: FAQUpdate, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        return error("FAQ不存在")
    if data.question is not None:
        faq.question = data.question
    if data.answer is not None:
        faq.answer = data.answer
    if data.category is not None:
        faq.category = data.category
    if data.keywords is not None:
        faq.keywords = data.keywords
    if data.sort_order is not None:
        faq.sort_order = data.sort_order
    if data.status is not None:
        faq.status = data.status
    db.commit()
    db.refresh(faq)
    return success(FAQOut.model_validate(faq).model_dump())


@router.delete("/{faq_id}")
def delete_faq(faq_id: int, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    faq = db.query(FAQ).filter(FAQ.id == faq_id).first()
    if not faq:
        return error("FAQ不存在")
    db.delete(faq)
    db.commit()
    return success(None, "删除成功")
