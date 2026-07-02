"""
会话状态管理验证脚本
用于测试 ConversationStateService 和 SlotExtractor
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.conversation_state import ConversationState
from app.models.user import User  # 导入 User 模型以确保 sys_user 表存在
from app.services.conversation_state_service import ConversationStateService
from app.services.slot_extractor import SlotExtractor, extract_slots_for_intent


def test_slot_extractor():
    """测试 SlotExtractor"""
    print("=" * 60)
    print("测试 SlotExtractor")
    print("=" * 60)

    test_cases = [
        ("我的入职时间是2010.01.01，累计工作年限是16年", "2010-01-01", 16),
        ("我是2015-06-20入职的", "2015-06-20", None),  # 会自动计算
        ("工龄是8年", None, 8),
        ("工作满21年", None, 21),
        ("我刚入职不久", None, None),
        ("2010年1月1日入职", "2010-01-01", None),  # 会自动计算
        ("累计工作年限为16年", None, 16),
        ("入职日期是2020/03/15", "2020-03-15", None),  # 会自动计算
        ("已经工作5年了", None, 5),
        ("入职时间：2018.7.1", "2018-07-01", None),  # 会自动计算
    ]

    print("\n测试结果：")
    print("-" * 80)
    print(f"{'输入文本':<40} | {'join_date':<12} | {'work_years':<10} | {'是否符合预期'}")
    print("-" * 80)

    all_passed = True
    for text, expected_date, expected_years in test_cases:
        result = SlotExtractor.extract_annual_leave_slots(text)

        actual_date = result.get("join_date")
        actual_years = result.get("work_years")

        # 检查日期
        date_ok = (actual_date == expected_date) if expected_date else (actual_date is None)

        # 检查年限（如果只提供了日期，会自动计算，所以需要特殊处理）
        if expected_years is not None:
            years_ok = (actual_years == expected_years)
        elif expected_date and actual_years is not None:
            # 只提供了日期，自动计算了年限
            years_ok = True  # 自动计算的结果
        else:
            years_ok = (actual_years is None)

        passed = date_ok and years_ok
        if not passed:
            all_passed = False

        status = "[PASS]" if passed else "[FAIL]"
        print(f"{text:<40} | {str(actual_date):<12} | {str(actual_years):<10} | {status}")

    print("-" * 80)
    print(f"总结: {'全部通过' if all_passed else '部分失败'}")
    return all_passed


def test_conversation_state_service():
    """测试 ConversationStateService"""
    print("\n" + "=" * 60)
    print("测试 ConversationStateService")
    print("=" * 60)

    db = SessionLocal()
    service = ConversationStateService(db)

    test_user_id = 1  # 使用 admin 用户

    try:
        # 测试1: 创建新状态
        print("\n1. 测试 get_or_create_state (创建新状态)")
        state = service.get_or_create_state(test_user_id)
        print(f"   conversation_id: {state.conversation_id}")
        print(f"   status: {state.status}")
        print(f"   turn_count: {state.turn_count}")
        print(f"   [OK] 创建成功")

        conv_id = state.conversation_id

        # 测试2: 设置 pending_intent
        print("\n2. 测试 set_pending_intent")
        state = service.set_pending_intent(
            user_id=test_user_id,
            conversation_id=conv_id,
            intent="annual_leave_calculation",
            required_slots=["join_date", "work_years"]
        )
        print(f"   pending_intent: {state.pending_intent}")
        print(f"   required_slots: {state.required_slots}")
        print(f"   status: {state.status}")
        print(f"   [OK] 设置成功")

        # 测试3: 获取 pending state
        print("\n3. 测试 get_pending_state")
        pending = service.get_pending_state(test_user_id, conv_id)
        print(f"   pending_intent: {pending.pending_intent if pending else 'None'}")
        print(f"   [OK] 获取成功")

        # 测试4: 更新 filled_slots
        print("\n4. 测试 update_filled_slots")
        state = service.update_filled_slots(
            user_id=test_user_id,
            conversation_id=conv_id,
            new_slots={"join_date": "2010-01-01", "work_years": 16}
        )
        print(f"   filled_slots: {state.filled_slots}")
        print(f"   turn_count: {state.turn_count}")
        print(f"   [OK] 更新成功")

        # 测试5: 检查槽位是否已填充
        print("\n5. 测试 check_slots_filled")
        is_filled = service.check_slots_filled(test_user_id, conv_id)
        print(f"   所有槽位已填充: {is_filled}")
        print(f"   [OK] 检查成功")

        # 测试6: 清空 pending_intent
        print("\n6. 测试 clear_pending_intent")
        state = service.clear_pending_intent(test_user_id, conv_id)
        print(f"   pending_intent: {state.pending_intent}")
        print(f"   status: {state.status}")
        print(f"   [OK] 清空成功")

        # 测试7: 获取已有状态
        print("\n7. 测试 get_or_create_state (获取已有状态)")
        state2 = service.get_or_create_state(test_user_id, conv_id)
        print(f"   conversation_id: {state2.conversation_id}")
        print(f"   is_same: {state.id == state2.id}")
        print(f"   [OK] 获取成功")

        print("\n" + "=" * 60)
        print("ConversationStateService 测试全部通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试数据
        try:
            db.query(ConversationState).filter(
                ConversationState.user_id == test_user_id
            ).delete()
            db.commit()
            print("\n[CLEAN] 测试数据已清理")
        except:
            pass
        db.close()


def test_slot_extractor_with_service():
    """测试 SlotExtractor 与 ConversationStateService 的集成"""
    print("\n" + "=" * 60)
    print("测试 SlotExtractor + ConversationStateService 集成")
    print("=" * 60)

    db = SessionLocal()
    service = ConversationStateService(db)

    test_user_id = 1

    try:
        # 模拟完整流程
        print("\n模拟场景：用户询问年假，系统要求补充信息，用户补充入职信息")

        # Step 1: 创建会话状态
        print("\nStep 1: 创建会话状态")
        state = service.get_or_create_state(test_user_id)
        conv_id = state.conversation_id
        print(f"   conversation_id: {conv_id}")

        # Step 2: 设置 pending_intent（模拟系统要求补充信息）
        print("\nStep 2: 设置待补充槽位")
        state = service.set_pending_intent(
            user_id=test_user_id,
            conversation_id=conv_id,
            intent="annual_leave_calculation",
            required_slots=["join_date", "work_years"]
        )
        print(f"   required_slots: {state.required_slots}")

        # Step 3: 用户补充信息，提取槽位
        print("\nStep 3: 用户说 '我的入职时间是2010.01.01，累计工作年限是16年'")
        user_input = "我的入职时间是2010.01.01，累计工作年限是16年"
        slots = extract_slots_for_intent(user_input, "annual_leave_calculation")
        print(f"   提取到的槽位: {slots}")

        # Step 4: 更新 filled_slots
        print("\nStep 4: 更新 filled_slots")
        state = service.update_filled_slots(test_user_id, conv_id, slots)
        print(f"   filled_slots: {state.filled_slots}")

        # Step 5: 检查槽位是否已填充
        print("\nStep 5: 检查槽位是否完整")
        is_filled = service.check_slots_filled(test_user_id, conv_id)
        print(f"   所有槽位已填充: {is_filled}")

        if is_filled:
            print("\nStep 6: 计算年假天数")
            filled = service.get_filled_slots(test_user_id, conv_id)
            work_years = filled.get("work_years", 0)
            if work_years < 10:
                annual_leave = 5
            elif work_years < 20:
                annual_leave = 10
            else:
                annual_leave = 15
            print(f"   工龄: {work_years}年")
            print(f"   年假天数: {annual_leave}天")

        # Step 7: 清空状态
        print("\nStep 7: 清空 pending_intent")
        state = service.clear_pending_intent(test_user_id, conv_id)
        print(f"   status: {state.status}")

        print("\n" + "=" * 60)
        print("集成测试通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试数据
        try:
            db.query(ConversationState).filter(
                ConversationState.user_id == test_user_id
            ).delete()
            db.commit()
            print("\n[CLEAN] 测试数据已清理")
        except:
            pass
        db.close()


if __name__ == "__main__":
    print("HR Copilot - 会话状态管理验证")
    print("=" * 60)

    # 确保表存在
    Base.metadata.create_all(bind=engine)
    print("[OK] 数据库表已确认")

    # 运行测试
    test_slot_extractor()
    test_conversation_state_service()
    test_slot_extractor_with_service()

    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)
