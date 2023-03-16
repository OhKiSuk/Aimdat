"""
@created at 2023.03.15
@author OKS in Aimdat Team
"""
from admin_dashboard.forms.corp_manage_forms import CorpIdChangeForm, CorpInfoChangeForm, CorpSummaryFinancialStatementsChangeForm
from django.contrib.admin import ModelAdmin
from django.core.paginator import Paginator
from django.shortcuts import render
from django.urls import path
from services.models.corp_id import CorpId
from services.models.corp_info import CorpInfo
from services.models.corp_summary_financial_statements import CorpSummaryFinancialStatements

class CorpIdAdmin(ModelAdmin):
    model = CorpId
    list_per_page = 20
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('corp/manage', self.corp_manage, name='corp_manage'),
            path('corp/manage/id/<id>', self.corp_id_change_view, name='corp_id_change'),
            path('corp/manage/info/<id>', self.corp_info_change_view, name='corp_info_change'),
            path('corp/manage/summary/<id>', self.corp_summary_financial_statements_change_view, name='corp_summary_change'),
        ]
        return custom_urls + urls
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request):
        return False
    
    def has_delete_permission(self, request):
        return False
    
    def corp_manage(self, request):
        tab = request.GET.get('tab', 'corp_id')

        if tab == 'corp_id':
            content = CorpId.objects.all().order_by('-corp_name')
        if tab == 'corp_info':
            content = CorpInfo.objects.all().order_by('-corp_id__corp_name')
        elif tab == 'corp_summary':
            content = CorpSummaryFinancialStatements.objects.all().order_by('-corp_id__corp_name')

        page = request.GET.get('page', 1)
        paginator = Paginator(content, self.list_per_page)
        page_obj = paginator.get_page(page)
        
        context = {
            'tab': tab,
            'content': page_obj
        }

        return render(request, 'admin_dashboard/corp_manage/corp_change_list.html', context=context)
    
    def corp_id_change_view(self, request, id):
        corp_id = CorpId.objects.get(id=id)
        fields = [field.name for field in corp_id._meta.get_fields() if not field.is_relation]

        if request.method == 'POST':
            form = CorpIdChangeForm(request.POST)
            if form.is_valid():
                form.save()
        else:
            form = CorpIdChangeForm()

        content = {}
        for field in fields:
            if hasattr(corp_id, field):
                content[field] = getattr(corp_id, field)
            elif hasattr(corp_id, field + '_id'):
                content[field] = getattr(corp_id, field + '_id')

        context = {
            'form': form,
            'content': content
        }

        return render(request, 'admin_dashboard/corp_manage/corp_id_change_form.html', context=context)
    
    def corp_info_change_view(self, request, id):
        corp_info = CorpInfo.objects.get(corp_id__id=id)
        fields = [field.name for field in corp_info._meta.get_fields() if not field.is_relation]

        if request.method == 'POST':
            form = CorpInfoChangeForm(request.POST)
            if form.is_valid():
                form.save()
        else:
            form = CorpInfoChangeForm()

        content = {}
        for field in fields:
            if hasattr(corp_info, field):
                content[field] = getattr(corp_info, field)
            elif hasattr(corp_info, field + '_id'):
                content[field] = getattr(corp_info, field + '_id')

        context = {
            'form': form,
            'content': content,
            'corp_name': corp_info.corp_id.corp_name
        }

        return render(request, 'admin_dashboard/corp_manage/corp_info_change_form.html', context=context)
    
    def corp_summary_financial_statements_change_view(self, request, id):
        corp_summary = CorpSummaryFinancialStatements.objects.get(corp_id__id=id)
        fields = [field.name for field in corp_summary._meta.get_fields() if not field.is_relation]

        if request.method == 'POST':
            form = CorpSummaryFinancialStatementsChangeForm(request.POST)
            if form.is_valid():
                form.save()
        else:
            form = CorpSummaryFinancialStatementsChangeForm()

        content = {}
        for field in fields:
            if hasattr(corp_summary, field):
                content[field] = getattr(corp_summary, field)
            elif hasattr(corp_summary, field + '_id'):
                content[field] = getattr(corp_summary, field + '_id')

        context = {
            'form': form,
            'content': content,
            'corp_name': corp_summary.corp_id.corp_name
        }

        return render(request, 'admin_dashboard/corp_manage/corp_summary_financial_statements_change_form.html', context=context)