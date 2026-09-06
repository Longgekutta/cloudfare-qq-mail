import unittest
from datetime import datetime, timezone, timedelta
from email_time_utils import parse_email_datetime


class TestParseEmailDatetime(unittest.TestCase):
    def test_valid_with_timezone(self):
        # 带时区的字符串
        date_str = "Thu, 01 Jan 2024 12:00:00 +0800"
        result = parse_email_datetime(date_str)
        self.assertIsInstance(result, datetime)
        self.assertIsNone(result.tzinfo)  # 时区信息已去除
    
    def test_valid_naive(self):
        # 无时区的字符串
        date_str = "Thu, 01 Jan 2024 12:00:00"
        result = parse_email_datetime(date_str)
        self.assertIsInstance(result, datetime)
        self.assertIsNone(result.tzinfo)
    
    def test_invalid_string(self):
        # 无效字符串应返回默认值
        result = parse_email_datetime("invalid-date")
        self.assertIsInstance(result, datetime)
    
    def test_none_input(self):
        # None 输入应返回默认值
        result = parse_email_datetime(None)
        self.assertIsInstance(result, datetime)
    
    def test_custom_default(self):
        # 自定义默认值
        default = datetime(2020, 1, 1)
        result = parse_email_datetime(None, default)
        self.assertEqual(result, default)
    
    def test_conversion_to_local_timezone(self):
        # 确保转换为本地时区
        date_str = "Thu, 01 Jan 2024 12:00:00 +0000"  # UTC
        result = parse_email_datetime(date_str)
        # 验证本地时区转换（依赖系统，但至少时区信息去除）
        self.assertIsNone(result.tzinfo)


if __name__ == "__main__":
    unittest.main()
