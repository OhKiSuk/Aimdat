"""
@created at 2023.04.02
@author OKS in Aimdat Team
"""
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views.generic import DeleteView

from ..models import User

class DeleteAccountView(DeleteView):
    model = User
    success_url = reverse_lazy('index')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('index')

        if request.user.user_classify == 'N':
            return redirect('account:naver_login_linkoff')
        elif request.user.user_classify == 'K':
            return redirect('account:kakao_login_linkoff')
        elif request.user.user_classify == 'G':
            return redirect('account:google_login_linkoff') 

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        return self.request.user.id

    def get_success_url(self):
        self.request.session.flush()
        return redirect(self.success_url)