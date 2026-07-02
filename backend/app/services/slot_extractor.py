"""
槽位提取器
用于从用户输入中提取结构化信息
本阶段只处理年假相关的槽位（join_date, work_years）
"""
import re
from datetime import datetime
from typing import Dict, Optional, Any


class SlotExtractor:
    """槽位提取器"""

    @staticmethod
    def extract_annual_leave_slots(text: str) -> Dict[str, Any]:
        """
        从文本中提取年假相关的槽位

        Args:
            text: 用户输入文本

        Returns:
            提取到的槽位字典，例如 {"join_date": "2010-01-01", "work_years": 16}
        """
        result = {}

        # 提取 join_date
        join_date = SlotExtractor._extract_join_date(text)
        if join_date:
            result["join_date"] = join_date

        # 提取 work_years
        work_years = SlotExtractor._extract_work_years(text)
        if work_years is not None:
            result["work_years"] = work_years

        # 如果只有 join_date 没有 work_years，根据当前日期计算
        if "join_date" in result and "work_years" not in result:
            try:
                join_year = int(result["join_date"].split("-")[0])
                current_year = datetime.now().year
                result["work_years"] = current_year - join_year
            except (ValueError, IndexError):
                pass

        return result

    @staticmethod
    def _extract_join_date(text: str) -> Optional[str]:
        """
        从文本中提取入职日期

        支持格式：
        - 2010.01.01
        - 2010-01-01
        - 2010/01/01
        - 2010年1月1日
        - 入职时间是2010.01.01
        - 我的入职日期是2010年1月1日
        - 我是2015-06-20入职的

        Returns:
            标准化的日期字符串 YYYY-MM-DD，未匹配返回 None
        """
        # 模式1: YYYY.MM.DD 或 YYYY-MM-DD 或 YYYY/MM/DD
        pattern1 = r'(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})'
        match = re.search(pattern1, text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"

        # 模式2: YYYY年M月D日
        pattern2 = r'(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日'
        match = re.search(pattern2, text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"

        # 模式3: YYYY年M月（没有日）
        pattern3 = r'(\d{4})\s*年\s*(\d{1,2})\s*月'
        match = re.search(pattern3, text)
        if match:
            year, month = match.groups()
            return f"{year}-{int(month):02d}-01"

        return None

    @staticmethod
    def _extract_work_years(text: str) -> Optional[int]:
        """
        从文本中提取工作年限

        支持格式：
        - 16年
        - 工龄16年
        - 工龄是16年
        - 工作年限16年
        - 工作年限是16年
        - 累计工作年限是16年
        - 工作满16年
        - 已经工作16年
        - 入职16年

        Returns:
            工作年限整数，未匹配返回 None
        """
        # 模式1: 工龄/工作年限/累计工作年限 + 是/为 + 数字 + 年
        pattern1 = r'(?:工龄|工作年限|累计工作年限)\s*(?:是|为)?\s*(\d+)\s*年'
        match = re.search(pattern1, text)
        if match:
            return int(match.group(1))

        # 模式2: 工作满/已经工作/入职 + 数字 + 年
        pattern2 = r'(?:工作满|已经工作|入职|工作了)\s*(\d+)\s*年'
        match = re.search(pattern2, text)
        if match:
            return int(match.group(1))

        # 模式3: 独立的 数字 + 年（需要确保不是日期的一部分）
        # 先排除日期格式
        text_without_date = re.sub(r'\d{4}[.\-/年]\d{1,2}[.\-/月]?\d{0,2}[日]?', '', text)
        pattern3 = r'(\d+)\s*年'
        match = re.search(pattern3, text_without_date)
        if match:
            num = int(match.group(1))
            # 合理的工作年限范围：0-60年
            if 0 <= num <= 60:
                return num

        return None


def extract_slots_for_intent(text: str, intent: str) -> Dict[str, Any]:
    """
    根据意图提取对应的槽位

    Args:
        text: 用户输入文本
        intent: 意图类型

    Returns:
        提取到的槽位字典
    """
    if intent == "annual_leave_calculation":
        return SlotExtractor.extract_annual_leave_slots(text)

    # 其他意图的槽位提取可以在这里扩展
    return {}
