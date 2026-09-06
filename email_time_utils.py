from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional


def parse_email_datetime(date_str: Optional[str], default: Optional[datetime] = None) -> datetime:
    """
    解析邮件日期时间字符串，转换为本地时区并去除时区信息（MySQL兼容）。
    
    Args:
        date_str: 邮件日期字符串，可能为 None。
        default: 解析失败时的默认值，若为 None 则使用当前时间。
    
    Returns:
        去除时区信息的 datetime 对象（本地时区）。
    """
    if default is None:
        default = datetime.now()
    
    if not date_str:
        return default
    
    try:
        parsed_dt = parsedate_to_datetime(date_str)
        if parsed_dt is None:
            return default
        # 如果有时区信息，转换为本地时区后去除时区信息
        if parsed_dt.tzinfo is not None:
            return parsed_dt.astimezone().replace(tzinfo=None)
        else:
            return parsed_dt
    except Exception:
        return default
