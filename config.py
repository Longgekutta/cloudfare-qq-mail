# -*- coding: utf-8 -*-
"""
系统配置文件
统一管理所有系统参数，方便维护和调整
"""

class Config:
    """系统配置类"""
    
    # ========== 邮箱相关配置 ==========
    # 每个用户最大邮箱注册数量
    MAX_EMAILS_PER_USER = 50  # 允许注册更多邮箱，前5个免费，之后收费
    
    # 邮箱注册费用（元/个）
    EMAIL_REGISTRATION_COST = 1.0
    
    # ========== 邮件计费配置 ==========
    # 接收邮件费用（免费）
    EMAIL_RECEIVE_COST = 0.0
    
    # 发送邮件费用（元/条）
    EMAIL_SEND_COST_NORMAL = 0.40  # 普通用户
    EMAIL_SEND_COST_VIP_OVER = 0.20  # VIP用户超额后
    
    # ========== 会员相关配置 ==========
    # 会员费用（元/月）
    VIP_MONTHLY_COST = 10.0
    
    # 会员有效期（天）
    VIP_DURATION_DAYS = 30
    
    # 会员每月免费邮件额度
    VIP_FREE_EMAIL_QUOTA = 50
    
    # ========== 余额相关配置 ==========
    # 建议最低余额（元）
    RECOMMENDED_MIN_BALANCE = 2.0
    
    # 充值金额限制
    MIN_RECHARGE_AMOUNT = 1.0
    MAX_RECHARGE_AMOUNT = 1000.0
    
    # ========== 系统提示信息 ==========
    # 邮箱删除确认提示
    EMAIL_DELETE_WARNING = (
        "该邮箱将与您的账户进行解绑，并且立即删除该邮箱所有邮件，"
        "以保护您的隐私。删除邮箱后，您消耗的邮箱注册数不会返还。"
    )
    
    # 邮件清除确认提示
    EMAIL_CLEAR_WARNING = "确定要清除选中的邮件吗？此操作不可撤销。"
    
    # ========== 业务逻辑配置 ==========
    # 是否启用邮箱注册限制
    ENABLE_EMAIL_LIMIT = True
    
    # 是否启用付费注册
    ENABLE_PAID_REGISTRATION = True
    
    # 是否启用会员系统
    ENABLE_VIP_SYSTEM = True
    
    @classmethod
    def get_email_send_cost(cls, user):
        """
        根据用户类型和使用情况获取发送邮件费用

        Args:
            user: 用户对象（字典格式）

        Returns:
            tuple: (费用, 是否使用VIP免费额度)
        """
        if not user.get('is_vip', False):
            return cls.EMAIL_SEND_COST_NORMAL, False

        # VIP用户检查免费额度（使用VIP期间计数）
        vip_email_count = user.get('vip_email_count', 0)
        if vip_email_count < cls.VIP_FREE_EMAIL_QUOTA:
            return 0.0, True  # 免费额度内
        else:
            return cls.EMAIL_SEND_COST_VIP_OVER, False  # 超额收费
    
    @classmethod
    def get_email_cost_description(cls, user):
        """
        获取邮件费用描述文本

        Args:
            user: 用户对象（字典格式）

        Returns:
            str: 费用描述
        """
        if not user.get('is_vip', False):
            return f"接收邮件：免费，发送邮件：¥{cls.EMAIL_SEND_COST_NORMAL}/条"

        vip_email_count = user.get('vip_email_count', 0)
        if vip_email_count < cls.VIP_FREE_EMAIL_QUOTA:
            remaining = cls.VIP_FREE_EMAIL_QUOTA - vip_email_count
            return f"接收邮件：免费，发送邮件：免费（剩余{remaining}条）"
        else:
            return f"接收邮件：免费，发送邮件：¥{cls.EMAIL_SEND_COST_VIP_OVER}/条"
    
    @classmethod
    def can_register_email(cls, user, current_email_count):
        """
        检查用户是否可以注册新邮箱

        Args:
            user: 用户对象（字典格式）
            current_email_count: 当前邮箱数量

        Returns:
            tuple: (bool, str, float) 是否可以注册，错误信息，注册费用
        """
        if not cls.ENABLE_EMAIL_LIMIT:
            return True, "", 0.0

        # 检查邮箱数量限制
        if current_email_count >= cls.MAX_EMAILS_PER_USER:
            return False, f"每个用户最多只能注册{cls.MAX_EMAILS_PER_USER}个邮箱", 0.0

        # 计算注册费用（前5个免费，之后每个1元）
        registration_cost = 0.0
        if current_email_count >= 5:  # 第6个开始收费
            registration_cost = 1.0

        # 检查余额是否足够（如果需要收费）
        if registration_cost > 0:
            current_balance = float(user.get('balance', 0))
            if current_balance < registration_cost:
                return False, f"余额不足！注册第{current_email_count + 1}个邮箱需要¥{registration_cost:.2f}，当前余额：¥{current_balance:.2f}", registration_cost

        return True, "", registration_cost
