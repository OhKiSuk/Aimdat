"""
@created at 2023.03.11
@author OKS in Aimdat Team

@modified at 2023.08.10
@author OKS in Aimdat Team
"""

import logging

from admin_dashboard.forms.account_manage_forms import AdminCreationForm, AdminChangeForm
from account.models import User
from django.contrib.admin import ModelAdmin
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import render

LOGGER = logging.getLogger(__name__)

class AccountManageAdmin(ModelAdmin):
    model = User
    change_list_template = 'admin_dashboard/user_manage/user_change_list.html'
    change_form_template = 'admin_dashboard/user_manage/user_change_form.html'
    add_form_template = 'admin_dashboard/user_manage/user_add_form.html'
    list_per_page = 20
    search_fields = ['user__email']

    list_display = ('email', 'user_classify', 'terms_of_use_agree', 'terms_of_privacy_agree', 'created_at', 'last_login', 'is_active', 'is_admin')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        users = User.objects.all().order_by('-created_at')

        search_query = request.GET.get('email', None)
        if search_query:
            users = User.objects.filter(email__icontains=search_query).order_by('-created_at')
        else:
            users = User.objects.all().order_by('-created_at')

        page = request.GET.get('page', 1)
        paginator = Paginator(users, self.list_per_page)
        page_obj = paginator.get_page(page)

        context = {
            'user_list': page_obj
        }

        return render(request, self.change_list_template, context=context)

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}

        if request.method == 'POST':
            form = AdminCreationForm(request.POST)
            if form.is_valid():
                # A805 로깅
                LOGGER.info('[A805] 계정을 성공적으로 추가. {}, {}'.format(str(request.user), str(form)))
                if request.user.has_perm('account.add_mymodel'):
                    user = form.save(commit=False)
                    user.is_admin = True
                    user.terms_of_use_agree = True
                    user.terms_of_privacy_agree = True
                    self.save_model(request, user, form, False)
                    user.save()
                    return self.response_add(request, user)
            else:
                # A806 로깅
                LOGGER.error('[A805] 계정 추가 실패. {}, {}'.format(str(request.user), str(form)))
                form = AdminCreationForm(request.POST).errors

            extra_context['form'] = form

        return super().add_view(request, form_url, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
    
        user = self.get_object(request, object_id)
        if user is None:
            raise Http404('Object not found.')
        
        if request.method == 'POST':
            form = AdminChangeForm(request.POST, instance=user)
            if form.is_valid():
                if request.user.has_perm('account.change_mymodel'):
                    if User.objects.filter(id=object_id, is_admin=True).exists():
                        # A803 로깅
                        LOGGER.info('[A803] 계정을 성공적으로 수정. {}, {}'.format(str(request.user), str(form)))
                        form.save()
                        return self.response_change(request, user)
                    else:
                        # A804 로깅
                        LOGGER.error('[A804] 계정 수정 실패. {}, {}'.format(str(request.user), str(form)))
                        raise Http404('관리자 계정만 변경 가능합니다.')
        else:
            form = AdminChangeForm(instance=user).errors
        
        extra_context['form'] = form
        extra_context['user_id'] = user.id
        
        return super().change_view(request, object_id, form_url, extra_context)
    
    def delete_view(self, request, object_id, extra_context=None):
        extra_context = extra_context or {}

        del_user = self.get_object(request, object_id)

        if del_user is None:
            # A802 로깅
            LOGGER.error('[A801] 계정 삭제 실패. {}, {}'.format(str(request.user), str(object_id)))
            raise Http404('Object not found.')

        if request.method == 'POST':
            if request.user.has_perm('account.delete_mymodel'):
                # A801 로깅
                LOGGER.info('[A801] 계정을 성공적으로 삭제. {}, {}'.format(str(request.user), str(object_id)))
                del_user.delete()
                return self.response_delete(request, del_user, object_id)

        return super().delete_view(request, object_id, extra_context)