# -*- coding: utf-8 -*-
# Security response headers helper.
# Adds low-risk security headers to Flask responses without changing business logic.


def register_security_headers(app):
    # Register a Flask after_request hook to append security headers.
    # setdefault avoids overriding headers already set by extensions or routes.

    @app.after_request
    def _set_security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
        return response
