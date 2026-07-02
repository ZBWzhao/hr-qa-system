-- HR Copilot 会话状态管理 - 数据库验证脚本
-- 第 1 阶段

-- 1. 检查 conversation_state 表是否存在
SHOW TABLES LIKE 'conversation_state';

-- 2. 查看表结构
DESC conversation_state;

-- 3. 查看最近状态（如果有数据）
SELECT
    id,
    conversation_id,
    user_id,
    current_intent,
    pending_intent,
    required_slots,
    filled_slots,
    turn_count,
    last_answer_type,
    status,
    created_at,
    updated_at
FROM conversation_state
ORDER BY updated_at DESC
LIMIT 5;

-- 4. 检查 qa_record 表结构（确认已有 conversation_id）
DESC qa_record;
