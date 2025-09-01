#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件费用处理模块
处理邮件发送前的费用检查和扣款
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager

class EmailCostHandler:
    """邮件费用处理器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def check_and_deduct_cost(self, user_id, email_id=None):
        """
        检查邮件费用并扣款
        返回 (success, message, cost)
        """
        if not self.db_manager.connect():
            return False, "数据库连接失败", 0
        
        try:
            # 检查并更新会员状态
            self.db_manager.check_and_update_vip_status(user_id)
            # 重置月度计数（如果需要）
            self.db_manager.reset_monthly_email_count_if_needed(user_id)
            
            # 计算邮件费用
            email_cost = self.db_manager.calculate_email_cost(user_id)
            user_stats = self.db_manager.get_user_monthly_stats(user_id)
            current_balance = user_stats.get('balance', 0) if user_stats else 0
            
            # 检查余额是否足够
            if current_balance < email_cost:
                return False, f'余额不足！当前余额：¥{current_balance:.2f}，需要：¥{email_cost:.2f}', email_cost
            
            # 扣除费用
            if email_cost > 0:
                self.db_manager.update_user_balance(user_id, -email_cost)
                self.db_manager.increment_monthly_email_count(user_id)
                
                # 记录计费
                user_type = 'vip' if user_stats.get('is_vip', False) else 'normal'
                monthly_count = user_stats.get('monthly_email_count', 0) + 1
                self.db_manager.add_email_billing(user_id, email_id, email_cost, user_type, monthly_count)
            
            return True, f'邮件发送成功！费用：¥{email_cost:.2f}', email_cost
            
        finally:
            self.db_manager.disconnect()
    
    def get_user_cost_info(self, user_id):
        """获取用户费用信息"""
        if not self.db_manager.connect():
            return None
        
        try:
            # 检查并更新会员状态
            self.db_manager.check_and_update_vip_status(user_id)
            # 重置月度计数（如果需要）
            self.db_manager.reset_monthly_email_count_if_needed(user_id)
            
            # 获取用户统计
            stats = self.db_manager.get_user_monthly_stats(user_id)
            if not stats:
                return None
            
            # 计算当前邮件费用
            current_cost = self.db_manager.calculate_email_cost(user_id)
            
            return {
                'balance': stats.get('balance', 0),
                'is_vip': stats.get('is_vip', False),
                'monthly_count': stats.get('monthly_email_count', 0),
                'vip_expire_date': stats.get('vip_expire_date'),
                'current_email_cost': current_cost
            }
            
        finally:
            self.db_manager.disconnect()

# 创建全局实例
email_cost_handler = EmailCostHandler()

def check_email_cost_and_deduct(user_id, email_id=None):
    """便捷函数"""
    return email_cost_handler.check_and_deduct_cost(user_id, email_id)

def get_user_cost_info(user_id):
    """便捷函数"""
    return email_cost_handler.get_user_cost_info(user_id)

