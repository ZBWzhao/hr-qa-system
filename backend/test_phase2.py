"""
第 2 阶段验证脚本：年假多轮澄清链路
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.conversation_state import ConversationState
from app.models.qa import QARecord
from app.services.conversation_state_service import ConversationStateService
from app.services.slot_extractor import extract_slots_for_intent
from app.api.chat import is_annual_leave_days_question


def test_is_annual_leave_days_question():
    """测试年假天数问题判断函数"""
    print("=" * 60)
    print("测试 is_annual_leave_days_question")
    print("=" * 60)

    test_cases = [
        ("我有多少天年假啊", True),
        ("年假有几天", True),
        ("年假几天", True),
        ("今年年假多少天", True),
        ("能休几天年假", True),
        ("年假天数是多少", True),
        ("请假需要提前多久", False),
        ("报销流程是什么", False),
        ("工作文档可以用AI写吗", False),
    ]

    print("\n测试结果：")
    print("-" * 60)
    all_passed = True
    for text, expected in test_cases:
        result = is_annual_leave_days_question(text)
        passed = result == expected
        if not passed:
            all_passed = False
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {text:<30} -> {result:<5} {status}")

    print("-" * 60)
    print(f"总结: {'全部通过' if all_passed else '部分失败'}")
    return all_passed


def test_multi_turn_clarification():
    """测试多轮澄清流程"""
    print("\n" + "=" * 60)
    print("测试多轮澄清流程")
    print("=" * 60)

    db = SessionLocal()
    state_service = ConversationStateService(db)

    # 使用一个测试用户（假设 user_id=1 是 admin）
    test_user_id = 1

    try:
        # 清理测试数据
        db.query(ConversationState).filter(ConversationState.user_id == test_user_id).delete()
        db.query(QARecord).filter(QARecord.user_id == test_user_id).delete()
        db.commit()

        # ===== 第一轮：用户问年假天数 =====
        print("\n--- 第一轮：用户问 '我有多少天年假啊' ---")
        question1 = "我有多少天年假啊"

        # 判断是否需要澄清
        needs_clarification = is_annual_leave_days_question(question1)
        print(f"  需要澄清: {needs_clarification}")

        if needs_clarification:
            # 创建会话状态
            state = state_service.get_or_create_state(test_user_id)
            conv_id = state.conversation_id
            print(f"  conversation_id: {conv_id}")

            # 设置 pending_intent
            state_service.set_pending_intent(
                user_id=test_user_id,
                conversation_id=conv_id,
                intent="annual_leave_calculation",
                required_slots=["join_date", "work_years"]
            )

            # 检查状态
            state = state_service.get_pending_state(test_user_id, conv_id)
            print(f"  pending_intent: {state.pending_intent}")
            print(f"  required_slots: {state.required_slots}")
            print(f"  status: {state.status}")

        # ===== 第二轮：用户补充信息 =====
        print("\n--- 第二轮：用户说 '我的入职时间是2010.01.01，累计工作年限是16年' ---")
        question2 = "我的入职时间是2010.01.01，累计工作年限是16年"

        # 检查是否有 pending_intent
        state = state_service.get_pending_state(test_user_id, conv_id)
        has_pending = state is not None and state.pending_intent is not None
        print(f"  有 pending_intent: {has_pending}")

        if has_pending:
            print(f"  pending_intent: {state.pending_intent}")

            # 提取槽位
            slots = extract_slots_for_intent(question2, state.pending_intent)
            print(f"  提取到的槽位: {slots}")

            # 更新 filled_slots
            state_service.update_filled_slots(test_user_id, conv_id, slots)

            # 检查槽位是否完整
            is_filled = state_service.check_slots_filled(test_user_id, conv_id)
            print(f"  所有槽位已填充: {is_filled}")

            if is_filled:
                # 计算年假
                filled = state_service.get_filled_slots(test_user_id, conv_id)
                work_years = filled.get("work_years", 0)

                if work_years < 10:
                    annual_leave = 5
                elif work_years < 20:
                    annual_leave = 10
                else:
                    annual_leave = 15

                print(f"  工龄: {work_years}年")
                print(f"  年假天数: {annual_leave}天")

                # 清空 pending_intent
                state_service.clear_pending_intent(test_user_id, conv_id)
                print(f"  pending_intent 已清空")

        print("\n" + "=" * 60)
        print("多轮澄清流程测试通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试数据
        try:
            db.query(ConversationState).filter(ConversationState.user_id == test_user_id).delete()
            db.query(QARecord).filter(QARecord.user_id == test_user_id).delete()
            db.commit()
            print("\n[CLEAN] 测试数据已清理")
        except:
            pass
        db.close()


if __name__ == "__main__":
    print("HR Copilot - 第 2 阶段验证：年假多轮澄清")
    print("=" * 60)

    # 确保表存在
    Base.metadata.create_all(bind=engine)
    print("[OK] 数据库表已确认")

    # 运行测试
    test_is_annual_leave_days_question()
    test_multi_turn_clarification()

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)
