"""
会话状态服务
用于管理多轮对话的状态，支持槽位填充和意图追踪
"""
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from app.models.conversation_state import ConversationState


class ConversationStateService:
    """会话状态管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_state(self, user_id: int, conversation_id: Optional[str] = None) -> ConversationState:
        """
        获取或创建会话状态

        Args:
            user_id: 用户ID
            conversation_id: 会话ID，如果为空则创建新的

        Returns:
            ConversationState 对象
        """
        if conversation_id:
            state = self.db.query(ConversationState).filter(
                ConversationState.conversation_id == conversation_id,
                ConversationState.user_id == user_id
            ).first()

            if state:
                return state

        # 创建新的会话ID和状态
        new_conv_id = conversation_id or str(uuid.uuid4())[:16]
        state = ConversationState(
            conversation_id=new_conv_id,
            user_id=user_id,
            current_intent=None,
            pending_intent=None,
            required_slots="[]",
            filled_slots="{}",
            turn_count=0,
            last_answer_type=None,
            status="active"
        )
        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state

    def get_pending_state(self, user_id: int, conversation_id: str) -> Optional[ConversationState]:
        """
        获取当前会话是否存在等待补充信息的状态

        Args:
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            如果存在待处理状态则返回 ConversationState，否则返回 None
        """
        state = self.db.query(ConversationState).filter(
            ConversationState.conversation_id == conversation_id,
            ConversationState.user_id == user_id,
            ConversationState.pending_intent.isnot(None),
            ConversationState.status.in_(["waiting_for_slot", "active"])
        ).first()

        return state

    def set_pending_intent(
        self,
        user_id: int,
        conversation_id: str,
        intent: str,
        required_slots: List[str],
        current_intent: Optional[str] = None
    ) -> ConversationState:
        """
        设置当前会话进入等待补充信息状态

        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            intent: 待处理意图
            required_slots: 需要的槽位列表
            current_intent: 当前意图（可选，默认与intent相同）

        Returns:
            更新后的 ConversationState
        """
        state = self.get_or_create_state(user_id, conversation_id)

        state.current_intent = current_intent or intent
        state.pending_intent = intent
        state.required_slots = json.dumps(required_slots, ensure_ascii=False)
        state.filled_slots = "{}"
        state.status = "waiting_for_slot"
        state.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(state)
        return state

    def update_filled_slots(
        self,
        user_id: int,
        conversation_id: str,
        new_slots: Dict[str, Any]
    ) -> ConversationState:
        """
        将新提取到的槽位合并进 filled_slots

        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            new_slots: 新的槽位数据

        Returns:
            更新后的 ConversationState
        """
        state = self.get_or_create_state(user_id, conversation_id)

        # 解析已有的 filled_slots
        try:
            current_slots = json.loads(state.filled_slots) if state.filled_slots else {}
        except (json.JSONDecodeError, TypeError):
            current_slots = {}

        # 合并新槽位（不覆盖已有非空值，除非新值更明确）
        for key, value in new_slots.items():
            if value is not None and value != "" and value != 0:
                current_slots[key] = value

        state.filled_slots = json.dumps(current_slots, ensure_ascii=False)
        state.turn_count += 1
        state.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(state)
        return state

    def clear_pending_intent(self, user_id: int, conversation_id: str) -> ConversationState:
        """
        在任务完成后清空 pending_intent

        Args:
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            更新后的 ConversationState
        """
        state = self.get_or_create_state(user_id, conversation_id)

        state.pending_intent = None
        state.required_slots = "[]"
        state.filled_slots = "{}"
        state.status = "active"
        state.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(state)
        return state

    def increment_turn_count(self, user_id: int, conversation_id: str) -> ConversationState:
        """
        对话轮次 +1

        Args:
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            更新后的 ConversationState
        """
        state = self.get_or_create_state(user_id, conversation_id)

        state.turn_count += 1
        state.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(state)
        return state

    def update_last_answer_type(
        self,
        user_id: int,
        conversation_id: str,
        answer_type: str
    ) -> ConversationState:
        """
        更新最后的回答类型

        Args:
            user_id: 用户ID
            conversation_id: 会话ID
            answer_type: 回答类型

        Returns:
            更新后的 ConversationState
        """
        state = self.get_or_create_state(user_id, conversation_id)

        state.last_answer_type = answer_type
        state.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(state)
        return state

    def get_required_slots(self, user_id: int, conversation_id: str) -> List[str]:
        """
        获取当前需要的槽位列表

        Args:
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            槽位列表
        """
        state = self.db.query(ConversationState).filter(
            ConversationState.conversation_id == conversation_id,
            ConversationState.user_id == user_id
        ).first()

        if not state or not state.required_slots:
            return []

        try:
            return json.loads(state.required_slots)
        except (json.JSONDecodeError, TypeError):
            return []

    def get_filled_slots(self, user_id: int, conversation_id: str) -> Dict[str, Any]:
        """
        获取已填充的槽位

        Args:
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            已填充的槽位字典
        """
        state = self.db.query(ConversationState).filter(
            ConversationState.conversation_id == conversation_id,
            ConversationState.user_id == user_id
        ).first()

        if not state or not state.filled_slots:
            return {}

        try:
            return json.loads(state.filled_slots)
        except (json.JSONDecodeError, TypeError):
            return {}

    def check_slots_filled(self, user_id: int, conversation_id: str) -> bool:
        """
        检查所有必需的槽位是否已填充

        Args:
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            是否所有槽位都已填充
        """
        required = self.get_required_slots(user_id, conversation_id)
        filled = self.get_filled_slots(user_id, conversation_id)

        if not required:
            return True

        return all(slot in filled for slot in required)
