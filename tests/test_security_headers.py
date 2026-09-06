# -*- coding: utf-8 -*-
# Unit test for security_headers helper.

import os
import sys
import unittest
from flask import Flask

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from security_headers import register_security_headers


class TestSecurityHeaders(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        register_security_headers(self.app)
        self.client = self.app.test_client()

    def test_headers_present(self):
        with self.app.test_request_context('/test'):
            # 通过after_request钩子的响应来验证
            @self.app.route('/test')
            def test_route():
                return ''

            response = self.client.get('/test')
            headers = response.headers
            self.assertEqual(headers.get('X-Content-Type-Options'), 'nosniff')
            self.assertEqual(headers.get('X-Frame-Options'), 'SAMEORIGIN')
            self.assertEqual(headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')
            self.assertEqual(headers.get('Permissions-Policy'), 'geolocation=(), microphone=(), camera=()')

    def test_does_not_override_existing(self):
        with self.app.test_request_context('/test'):
            @self.app.route('/test')
            def test_route():
                from flask import make_response
                resp = make_response('')
                resp.headers['X-Frame-Options'] = 'DENY'
                return resp

            response = self.client.get('/test')
            # 验证已存在的头部未被覆盖
            self.assertEqual(response.headers.get('X-Frame-Options'), 'DENY')
            # 其他新增头部仍应存在
            self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')


if __name__ == '__main__':
    unittest.main()
