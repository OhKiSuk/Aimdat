"""
@modified at 2023.08.10
@author OKS in Aimdat Team
"""
from django.contrib.auth.models import (
    AbstractBaseUser, 
    BaseUserManager
)
from django.db import models
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, is_not_teen=False, terms_of_use_agree=False, terms_of_privacy_agree=False, password=None):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            is_not_teen=is_not_teen,
            terms_of_use_agree=terms_of_use_agree,
            terms_of_privacy_agree=terms_of_privacy_agree
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(
            email,
            password=password,
            is_not_teen=True,
            terms_of_use_agree=True,
            terms_of_privacy_agree=True,
        )
        user.is_admin = True
        user.is_active = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    user_classify = models.CharField(
        max_length=255,
        default='U' # G: 구글 소셜 로그인, K: 카카오 소셜 로그인, N: 네이버 소셜 로그인, U: 일반 사용자
    )
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )
    refresh_token = models.TextField(null=True, blank=True) #소셜로그인 사용자의 토큰 갱신을 위한 field
    created_at = models.DateTimeField(auto_now_add=True) #계정 생성일
    terms_of_use_agree = models.BooleanField(default=False)
    terms_of_privacy_agree = models.BooleanField(default=False)
    is_not_teen = models.BooleanField(default=False) #만 14세 이하인지 확인(만 14세 이하의 경우 서비스 이용 불가)
    is_active = models.BooleanField(default=True) #계정 활성화 여부
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin