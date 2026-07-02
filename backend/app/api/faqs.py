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
    """生成关键词 - 使用jieba分词"""
    import jieba
    import jieba.posseg as pseg

    question = data.question.strip()
    answer = data.answer.strip()

    if not question and not answer:
        return error("请输入问题或回答")

    # 合并问题和答案
    text = f"{question} {answer}"

    # 通用词列表（停用词）
    stop_words = {
        # 疑问词
        '如何', '怎么', '什么', '为什么', '哪个', '哪些', '多少', '几',
        # 助动词/连词
        '可以', '能', '会', '要', '是', '的', '了', '吗', '呢', '吧', '啊',
        '但是', '可是', '然而', '而且', '并且', '或者', '如果', '因为', '所以',
        '然后', '接着', '首先', '其次', '最后', '同时', '另外', '此外',
        # 代词
        '我', '你', '他', '她', '它', '我们', '你们', '他们', '这个', '那个',
        '这些', '那些', '自己', '别人', '大家',
        # 其他通用词
        '请', '帮', '告诉', '一下', '一些', '进行', '使用', '需要', '可能', '应该',
        '能够', '愿意', '必须', '不能', '不会', '不要',
        '一个', '一种', '一次', '第一', '第二', '第三',
        '问题', '答案', '情况', '方面', '时候', '地方', '原因', '结果',
        '超过', '不', '没', '没有', '已经', '正在',
    }

    # 使用 jieba 进行词性标注分词
    words = pseg.cut(text)

    # 提取名词、动词、英文、数字
    keywords = []
    for word, flag in words:
        # 跳过停用词
        if word in stop_words:
            continue
        # 跳过单字
        if len(word) < 2:
            continue
        # 跳过纯标点
        if all(c in '，。！？、；：""''（）【】,.!?;:()[]' for c in word):
            continue

        # 只保留名词(n)、动词(v)、英文词、数字
        if flag.startswith('n') or flag.startswith('v') or flag == 'eng' or flag == 'm':
            keywords.append(word)

    # 去重并保持顺序
    seen = set()
    unique_keywords = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            unique_keywords.append(kw)

    # 取前5个
    result = unique_keywords[:5]

    if not result:
        return error("未能提取到有效关键词")

    return success({"keywords": ",".join(result)})


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
