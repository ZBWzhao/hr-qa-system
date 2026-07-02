from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.response import success, error
from app.schemas.comment import CommentCreate, CommentOut
from app.models.comment import Comment
from app.models.user import User

router = APIRouter()


@router.get("")
def list_comments(target_type: str, target_id: int, db: Session = Depends(get_db)):
    comments = db.query(Comment).filter(Comment.target_type == target_type, Comment.target_id == target_id, Comment.parent_id == None, Comment.status == 1).order_by(Comment.created_at.desc()).all()
    result = []
    for c in comments:
        d = CommentOut.model_validate(c).model_dump()
        replies = db.query(Comment).filter(Comment.parent_id == c.id, Comment.status == 1).order_by(Comment.created_at).all()
        d["replies"] = [CommentOut.model_validate(r).model_dump() for r in replies]
        result.append(d)
    return success(result)


@router.post("")
def create_comment(data: CommentCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    comment = Comment(target_type=data.target_type, target_id=data.target_id, user_id=current_user.id, content=data.content, parent_id=data.parent_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return success(CommentOut.model_validate(comment).model_dump())


@router.put("/{comment_id}/like")
def like_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        return error("评论不存在")
    comment.like_count += 1
    db.commit()
    return success({"like_count": comment.like_count})


@router.put("/{comment_id}/adopt")
def adopt_comment(comment_id: int, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        return error("评论不存在")
    comment.is_adopted = 1
    db.commit()
    return success(None, "已采纳")


@router.delete("/{comment_id}")
def delete_comment(comment_id: int, current_user: User = Depends(require_roles("hr")), db: Session = Depends(get_db)):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        return error("评论不存在")
    comment.status = 0
    db.commit()
    return success(None, "已删除")
