"""
@created at 2023.03.20
@author OKS in Aimdat Team
"""
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView
from services.models.inquiry import Inquiry
from ..forms.inquery_manage_forms import InquiryAnswerForm
from ..models import InquiryAnswer

class InquiryListView(TemplateView):
    template_name = 'admin_dashboard/inquiry_manage/inquiry_list.html'

    def get(self, request):
        search_query = request.GET.get('inquiry_title', None)
        if search_query:
            inquiries = Inquiry.objects.filter(title__icontains=search_query).order_by('-created_at')
        else:
            inquiries = Inquiry.objects.all().order_by('-created_at')

        page = request.GET.get('page', 1)
        paginator = Paginator(inquiries, 20)
        page_obj = paginator.get_page(page)

        context = {
            'inquiry_list': page_obj,
            'inquiry_answer': InquiryAnswer.objects.values_list('inquiry__id', flat=True)
        }

        return render(request, 'admin_dashboard/inquiry_manage/inquiry_list.html', context=context)
    
class InquiryAddAnswerView(CreateView):
    model = InquiryAnswer
    template_name = 'admin_dashboard/inquiry_manage/add_inquiry_answer_form.html'
    form_class = InquiryAnswerForm
    success_url = reverse_lazy('admin:inquiry_manage')

    def get(self, request, pk):
        inquiry = get_object_or_404(Inquiry, id=pk)
        inquiry_answer = InquiryAnswer.objects.filter(inquiry__id=pk)

        if inquiry_answer.exists():
           inquiry_answer = inquiry_answer.get()
        else:
            inquiry_answer = None

        context = {
            'inquiry': inquiry,
            'inquiry_answer': inquiry_answer,
            'form': self.form_class
        }

        return render(request, self.template_name, context=context)

    def form_valid(self, form):
        if not self.request.user.is_admin:
            raise PermissionDenied()
        else:
            inquiry = get_object_or_404(Inquiry, id=self.kwargs['pk'])
            form.instance.inquiry = inquiry
            form.save()

        return super().form_valid(form)