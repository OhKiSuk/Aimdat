"""
@created at 2023.03.31
@author OKS in Aimdat Team
"""
from django.views.defaults import (
    bad_request, 
    page_not_found, 
    permission_denied, 
    server_error
)

def custom_400(request, exception=None, template_name='errors/400.html'):
    return bad_request(request, exception, template_name)

def custom_403(request, exception=None, template_name='errors/403.html'):
    return permission_denied(request, exception, template_name)

def custom_404(request, exception=None, template_name='errors/404.html'):
    return page_not_found(request, exception, template_name)

def custom_500(request, template_name='errors/500.html'):
    return server_error(request, template_name)