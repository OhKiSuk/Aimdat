"""
@created at 2023.04.03
@author OKS in Aimdat Team

@modified at 2023.04.05
@author OKS in Aimdat Team
"""
from account.models import User
from admin_dashboard.models import InquiryAnswer
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    TemplateView
)

from ..forms.inquiry_forms import AddInquiryForm
from ..models.inquiry import Inquiry

class InquiryView(UserPassesTestMixin, TemplateView):
    template_name = 'services/mypage/inquiry/inquiry.html'
    login_url = reverse_lazy('account:login')
    redirect_field_name=None

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

        return self.request.user.is_authenticated

    def get(self, request, *args, **kwargs):
        if Inquiry.objects.filter(user__id=request.user.id).exists():
            inquiry = Inquiry.objects.filter(user__id=request.user.id).order_by('-created_at')

            #페이징
            page = request.GET.get('page', 1)
            paginator = Paginator(inquiry, 30)
            page_obj = paginator.get_page(page)

            kwargs['inquiry'] = page_obj

        return super().get(request, *args, **kwargs)
    
class InquiryDetailView(UserPassesTestMixin, TemplateView):
    template_name = 'services/mypage/inquiry/inquiry_detail.html'
    login_url = reverse_lazy('account:login')
    redirect_field_name=None

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

        return self.request.user.is_authenticated
    
    def get(self, request, id, *args, **kwargs):
        inquiry = Inquiry.objects.get(id=id)
        kwargs['inquiry'] = inquiry

        if InquiryAnswer.objects.filter(inquiry__id=id).exists():
            inquiry_answer = InquiryAnswer.objects.get(inquiry__id=id)
            kwargs['inquiry_answer'] = inquiry_answer

        return super().get(request, *args, **kwargs)

class AddInquiryView(UserPassesTestMixin, CreateView):
    form_class = AddInquiryForm
    model = Inquiry
    template_name = 'services/mypage/inquiry/add_inquiry_form.html'
    success_url = reverse_lazy('services:mypage')
    login_url = reverse_lazy('account:login')
    redirect_field_name=None

    def test_func(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_admin:
                return False

        return self.request.user.is_authenticated

    def form_valid(self, form):
        form.instance.user = get_object_or_404(User, id=self.request.user.id)
        form.save()

        return super().form_valid(form)