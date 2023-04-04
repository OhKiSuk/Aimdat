"""
@created at 2023.04.02
@author OKS in Aimdat Team

@modified at 2023.04.05
@author OKS in Aimdat Team
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import DeleteView

from ..models import User

class DeleteAccountView(UserPassesTestMixin, DeleteView):
    http_method_names = ['post']
    model = User

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

        return self.request.user.is_authenticated
    
    def handle_no_permission(self):
        return HttpResponseRedirect(reverse_lazy('index'))

    def post(self, request):
        if request.user.user_classify == 'N':
            return redirect('account:naver_login_linkoff')
        elif request.user.user_classify == 'K':
            return redirect('account:kakao_login_linkoff')
        elif request.user.user_classify == 'G':
            return redirect('account:google_login_linkoff')

        return super().post(request)

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        self.request.session.flush()
        return reverse_lazy('index')