"""
@created at 2023.03.12
@author OKS in Aimdat Team
"""
from admin_dashboard.forms.inquery_manage_forms import InquiryAnswerForm
from admin_dashboard.models import InquiryAnswer
from django.contrib.admin import ModelAdmin
from django.core.paginator import Paginator
from django.shortcuts import render
from django.urls import path
from services.models.inquiry import Inquiry

class InqueryAnswerAdmin(ModelAdmin):
    model = InquiryAnswer
    change_list_template = 'admin_dashboard/inquiry_manage/inquiry_change_list.html'
    list_per_page = 20

    list_display = ('inquiry_title', 'inquiry_category', 'inquiry_created_at',)

    def inquiry_title(self, obj):
        return obj.inquiry.title

    def inquiry_category(self, obj):
        return obj.inquiry.inquiry_category

    def inquiry_created_at(self, obj):
        return obj.inquiry.created_at
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<str:id>', self.show_inquiry_view, name='inquiryanswer_show_inquiry')
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        inquiries = Inquiry.objects.all().order_by('-created_at')

        search_query = request.GET.get('inquiry_title', None)
        if search_query:
            inquiries = Inquiry.objects.filter(title__icontains=search_query).order_by('-created_at')
        else:
            inquiries = Inquiry.objects.all().order_by('-created_at')

        page = request.GET.get('page', 1)
        paginator = Paginator(inquiries, self.list_per_page)
        page_obj = paginator.get_page(page)

        inquiries_id = list(inquiry.id for inquiry in page_obj)
        inquiries_answer = list(InquiryAnswer.objects.filter(inquiry_id__in=inquiries_id).order_by('-created_at'))
        inquiries_answer_id = [answer.inquiry_id for answer in inquiries_answer]

        extra_context['cl'] = page_obj
        extra_context['answer'] = inquiries_answer_id

        return render(request, 'admin_dashboard/inquiry_manage/inquiry_change_list.html', context=extra_context)
    
    def show_inquiry_view(self, request, id):
        inquiry = Inquiry.objects.get(id=id)

        if InquiryAnswer.objects.filter(inquiry__title=inquiry.title).exists():
            inquiry_answer = InquiryAnswer.objects.get(inquiry__title=inquiry.title)
        else:
            inquiry_answer = None

        if request.method == 'POST':
            form = InquiryAnswerForm(request.POST)
            if form.is_valid():
                if request.user.has_perm('admin_dashboard.add_mymodel'):
                    answer = form.save(commit=False)
                    answer.inquiry = inquiry
                    answer.email = request.user.email
                    answer.content = form.cleaned_data.get('content')
                    self.save_model(request, answer, form, False)
                    answer.save()
                    return self.response_add(request, answer)
            else:
                form = InquiryAnswerForm(request)
        
        context = {
            'inquiry': inquiry,
            'inquiry_answer': inquiry_answer,
            'form': InquiryAnswerForm(),
        }

        return render(request, 'admin_dashboard/inquiry_manage/inquiry.html', context=context)