# -*- coding: utf-8 -*-
"""
易支付工具类
实现MD5签名、支付请求生成等功能
"""

import hashlib
import time
import random
import requests
from urllib.parse import urlencode, quote_plus
from yipay_config import YIPAY_PID, YIPAY_KEY, YIPAY_GATEWAY, SITE_NAME, RETURN_URL, NOTIFY_URL

class YiPayUtil:
    """易支付工具类"""
    
    @staticmethod
    def generate_order_no():
        """生成商户订单号"""
        timestamp = str(int(time.time()))
        random_num = str(random.randint(1000, 9999))
        return f"YP{timestamp}{random_num}"
    
    @staticmethod
    def create_md5_sign(params, key):
        """
        创建MD5签名
        按照键名进行升序排序(a-z)，排除sign、sign_type和空值
        """
        # 过滤空值和签名相关参数
        filtered_params = {}
        for k, v in params.items():
            if k not in ['sign', 'sign_type'] and v is not None and str(v).strip() != '':
                filtered_params[k] = str(v)
        
        # 按键名升序排序
        sorted_params = sorted(filtered_params.items())
        
        # 拼接参数字符串
        param_str = '&'.join([f'{k}={v}' for k, v in sorted_params])
        
        # 加上密钥
        sign_str = param_str + key
        
        # MD5加密，转小写
        md5_hash = hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()
        
        print(f"🔐 签名调试信息:")
        print(f"   参数字符串: {param_str}")
        print(f"   签名字符串: {sign_str}")
        print(f"   MD5签名: {md5_hash}")
        
        return md5_hash
    
    @staticmethod
    def verify_sign(params, key):
        """验证签名"""
        if 'sign' not in params:
            return False
        
        received_sign = params['sign']
        calculated_sign = YiPayUtil.create_md5_sign(params, key)
        
        return received_sign.lower() == calculated_sign.lower()
    
    @staticmethod
    def create_payment_request(payment_type, amount, order_no, product_name, user_param=""):
        """
        创建支付请求
        
        Args:
            payment_type: 支付类型 (alipay, wxpay, qqpay)
            amount: 金额
            order_no: 商户订单号
            product_name: 商品名称
            user_param: 业务扩展参数
        
        Returns:
            dict: 支付请求参数
        """
        params = {
            'pid': YIPAY_PID,
            'type': payment_type,
            'out_trade_no': order_no,
            'name': product_name,
            'money': f"{amount:.2f}",
            'return_url': RETURN_URL,
            'notify_url': NOTIFY_URL,
            'sitename': SITE_NAME,
        }
        
        # 添加业务扩展参数（如果有）
        if user_param:
            params['param'] = user_param
        
        # 创建签名
        params['sign'] = YiPayUtil.create_md5_sign(params, YIPAY_KEY)
        params['sign_type'] = 'MD5'
        
        return params
    
    @staticmethod
    def get_payment_url(payment_type, amount, order_no, product_name, user_param="", direct_pay=False):
        """
        获取支付URL
        
        Args:
            direct_pay: 是否直接跳转（False返回收银台页面，True直接跳转支付）
        """
        params = YiPayUtil.create_payment_request(
            payment_type, amount, order_no, product_name, user_param
        )
        
        # 构建URL
        if direct_pay:
            # 直接支付，返回带参数的GET请求URL
            base_url = YIPAY_GATEWAY.rstrip('/') + '/submit'
            query_string = urlencode(params, quote_via=quote_plus)
            return f"{base_url}?{query_string}"
        else:
            # 收银台模式
            return YIPAY_GATEWAY.rstrip('/') + '/sytpay', params
    
    @staticmethod
    def create_payment_form_html(payment_type, amount, order_no, product_name, user_param=""):
        """
        创建自动提交的支付表单HTML
        """
        params = YiPayUtil.create_payment_request(
            payment_type, amount, order_no, product_name, user_param
        )
        
        submit_url = YIPAY_GATEWAY.rstrip('/') + '/submit'
        
        form_html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>正在跳转到支付页面...</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            text-align: center; 
            padding: 50px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .loading {{ 
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top: 3px solid white;
            animation: spin 1s ease-in-out infinite;
            margin-bottom: 20px;
        }}
        @keyframes spin {{ 
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="loading"></div>
    <h3>正在跳转到安全支付页面...</h3>
    <p>请稍候，如果没有自动跳转，请点击下方按钮</p>
    
    <form id="yipay_form" method="post" action="{submit_url}">
'''
        
        # 添加表单字段
        for key, value in params.items():
            form_html += f'        <input type="hidden" name="{key}" value="{value}">\n'
        
        form_html += '''
        <input type="submit" value="立即支付" style="
            background: #28a745; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer;
            font-size: 16px;
        ">
    </form>
    
    <script>
        // 页面加载后自动提交表单
        window.onload = function() {
            setTimeout(function() {
                document.getElementById('yipay_form').submit();
            }, 1000);
        };
    </script>
</body>
</html>
'''
        return form_html


# 测试代码
if __name__ == '__main__':
    print("🧪 易支付工具测试")
    
    # 测试订单号生成
    order_no = YiPayUtil.generate_order_no()
    print(f"📝 订单号: {order_no}")
    
    # 测试签名
    test_params = {
        'pid': '6166',
        'type': 'alipay',
        'out_trade_no': order_no,
        'name': '测试商品',
        'money': '10.00'
    }
    
    sign = YiPayUtil.create_md5_sign(test_params, YIPAY_KEY)
    print(f"🔐 签名: {sign}")
    
    # 测试支付URL生成
    payment_url, params = YiPayUtil.get_payment_url(
        'alipay', 10.00, order_no, '测试充值'
    )
    print(f"💳 支付URL: {payment_url}")
    print(f"📋 支付参数: {params}")












