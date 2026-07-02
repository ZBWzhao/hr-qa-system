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
    """AI生成关键词"""
    import os
    import json
    import subprocess
    import tempfile

    question = data.question
    answer = data.answer

    if not question and not answer:
        return error("请输入问题或回答")

    prompt = f"""请提取以下内容的5-8个关键词，只输出关键词，用逗号分隔，不要输出其他内容。

注意：
1. 只提取有实际意义的名词和专业术语
2. 不要提取通用词汇，如：如何、怎么、什么、为什么、请、帮我、告诉、一下、一些、这个、那个
3. 优先提取与业务、制度、流程相关的专业词汇

问题：{question}
回答：{answer}"""

    try:
        req_data = {
            "model": settings.MIMO_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2000
        }

        tmp_dir = tempfile.gettempdir()
        req_file = os.path.join(tmp_dir, "mimo_kw_req.json")
        resp_file = os.path.join(tmp_dir, "mimo_kw_resp.json")

        with open(req_file, "w", encoding="utf-8") as f:
            json.dump(req_data, f, ensure_ascii=False)

        subprocess.run([
            "curl", "-s", "-X", "POST",
            f"{settings.MIMO_BASE_URL}/chat/completions",
            "-H", f"Authorization: Bearer {settings.MIMO_API_KEY}",
            "-H", "Content-Type: application/json",
            "-d", f"@{req_file}",
            "-o", resp_file
        ], timeout=60)

        with open(resp_file, "rb") as f:
            raw = f.read()

        import re
        match = re.search(rb'"content":"([^"]*)"', raw)
        if match:
            keywords = match.group(1).decode("utf-8").strip()
        else:
            keywords = ""

        if not keywords:
            return error("关键词生成失败，请重试")

        return success({"keywords": keywords})
    except subprocess.TimeoutExpired:
        return error("AI服务响应超时")
    except Exception as e:
        return error(f"AI服务异常: {str(e)}")


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
