# -*- coding: utf-8 -*-
"""
安全响应头模块

提供统一的安全响应头设置函数，供 Flask / 其他 WSGI 应用复用。
"""


def set_security_headers(response):
    """为 HTTP 响应补充基础安全响应头"""
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault(
        'Permissions-Policy',
        'accelerometer=(), camera=(), geolocation=(), gyroscope=(), '
        'magnetometer=(), microphone=(), payment=(), usb=()'
    )
    return response
