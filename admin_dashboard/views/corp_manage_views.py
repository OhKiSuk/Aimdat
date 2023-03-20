"""
@created at 2023.03.19
@author OKS in Aimdat Team
"""
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import UpdateView, TemplateView
from services.models.corp_id import CorpId
from services.models.corp_info import CorpInfo
from services.models.corp_summary_financial_statements import CorpSummaryFinancialStatements
from ..forms.corp_manage_forms import CorpIdChangeForm, CorpInfoChangeForm, CorpSummaryFinancialStatementsChangeForm
    
class CorpManageView(TemplateView):
    template_name = 'admin_dashboard/corp_manage/corp_manage_view.html'

    def get(self, request):
        tab = request.GET.get('tab', 'corp_id')

        if tab == 'corp_id':
            content = CorpId.objects.all().order_by('-corp_name')
        if tab == 'corp_info':
            content = CorpInfo.objects.all().order_by('-corp_id__corp_name')
        elif tab == 'corp_summary':
            content = CorpSummaryFinancialStatements.objects.all().order_by('-corp_id__corp_name')

        page = request.GET.get('page', 1)
        paginator = Paginator(content, 20)
        page_obj = paginator.get_page(page)
        
        context = {
            'tab': tab,
            'content': page_obj
        }

        return render(self.request, self.template_name, context=context)
    
class CorpIdChangeView(UpdateView):
    model = CorpId
    template_name = 'admin_dashboard/corp_manage/corp_id_change_form.html'
    form_class = CorpIdChangeForm
    success_url = reverse_lazy('admin:corp_manage')

    def form_valid(self, form):
        if not self.request.user.is_admin:
            raise PermissionDenied()
        else:
            form.save()
            return redirect('admin:corp_manage')
    
class CorpInfoChangeView(UpdateView):
    model = CorpInfo
    template_name = 'admin_dashboard/corp_manage/corp_info_change_form.html'
    form_class = CorpInfoChangeForm
    success_url = reverse_lazy('admin:corp_manage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['corp_name'] = self.object.corp_id.corp_name
        return context

    def form_valid(self, form):
        if not self.request.user.is_admin:
            raise PermissionDenied()
        else:
            form.save()
    
class CorpSummaryFinancialStatementsChangeView(UpdateView):
    model = CorpSummaryFinancialStatements
    template_name = 'admin_dashboard/corp_manage/corp_summary_financial_statements_change_form.html'
    form_class = CorpSummaryFinancialStatementsChangeForm
    success_url = reverse_lazy('admin:corp_manage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['corp_name'] = self.object.corp_id.corp_name
        return context

    def form_valid(self, form):
        if not self.request.user.is_admin:
            raise PermissionDenied()
        else:
            form.save()

        return super().form_valid(form)