"""
@created at 2023.02.25
@author OKS in Aimdat Team
"""
from .base import *

ALLOWED_HOSTS = []

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

# 기본 송신 이메일 설정
DEFAULT_FROM_EMAIL = 'no-reply@aimdat.com'