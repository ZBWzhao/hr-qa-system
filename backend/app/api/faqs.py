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
    import re

    question = data.question.strip()
    answer = data.answer.strip()

    if not question and not answer:
        return error("请输入问题或回答")

    # 精简 prompt，减少 token 消耗
    content = f"问题：{question}\n答案：{answer}" if answer else f"问题：{question}"
    prompt = f"从以下内容提取5个关键词，用逗号分隔，只输出关键词，不要输出其他内容。不要包含：如何、怎么、什么、为什么、请、帮我等通用词。\n{content}"

    try:
        req_data = {
            "model": settings.MIMO_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,  # 降低温度，提高稳定性
            "max_tokens": 100    # 降低 token 数量
        }

        tmp_dir = tempfile.gettempdir()
        req_file = os.path.join(tmp_dir, "mimo_kw_req.json")
        resp_file = os.path.join(tmp_dir, "mimo_kw_resp.json")

        with open(req_file, "w", encoding="utf-8") as f:
            json.dump(req_data, f, ensure_ascii=False)

        # 使用更短的超时时间
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            f"{settings.MIMO_BASE_URL}/chat/completions",
            "-H", f"Authorization: Bearer {settings.MIMO_API_KEY}",
            "-H", "Content-Type: application/json",
            "-d", f"@{req_file}",
            "-o", resp_file
        ], timeout=30)

        # 检查响应文件是否存在
        if not os.path.exists(resp_file):
            return error("AI服务响应异常，请重试")

        with open(resp_file, "rb") as f:
            raw = f.read()

        # 改进的响应解析
        try:
            resp = json.loads(raw.decode("utf-8"))
            content = ""
            choices = resp.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")

            # 如果 content 为空，尝试从 reasoning_content 获取
            if not content and choices:
                content = message.get("reasoning_content", "")

            if not content:
                return error("关键词生成失败，请重试")

            # 清理关键词 - 只保留逗号分隔的关键词部分
            keywords = content.strip()

            # 如果内容包含冒号或换行，只取最后一行（通常是关键词）
            if '\n' in keywords:
                lines = [l.strip() for l in keywords.split('\n') if l.strip()]
                # 找到最后一行看起来像关键词的行（包含逗号）
                for line in reversed(lines):
                    if ',' in line or '，' in line:
                        keywords = line
                        break
                else:
                    keywords = lines[-1] if lines else ""

            # 移除可能的前缀
            keywords = re.sub(r'^(关键词[：:]?\s*)', '', keywords)
            # 移除换行符
            keywords = keywords.replace('\n', ',')
            # 移除多余的空格
            keywords = re.sub(r'\s+', '', keywords)
            # 移除末尾的标点
            keywords = keywords.rstrip('。，,. ')

            # 验证关键词格式（应该包含逗号分隔）
            if not keywords or len(keywords) < 2:
                return error("关键词生成失败，请重试")

            # 如果没有逗号，可能是单个词或句子，尝试提取
            if ',' not in keywords and '，' not in keywords:
                # 如果内容太长，可能是句子而不是关键词
                if len(keywords) > 20:
                    return error("关键词生成失败，请重试")

            return success({"keywords": keywords})

        except json.JSONDecodeError:
            return error("AI服务响应格式异常，请重试")

    except subprocess.TimeoutExpired:
        return error("AI服务响应超时，请稍后重试")
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
