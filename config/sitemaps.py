"""
@created at 2023.06.22
@author OKS in Aimdat Team
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from services.models.corp_id import CorpId

class StaticSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5
    protocol = 'https'

    def __init__(self, app_name):
        self.app_name = app_name

    def items(self):
        if self.app_name == 'services':
            return ['search', 'analysis', 'terms_of_use', 'terms_of_privacy', 'faq']

    def location(self, item):
        return reverse(f'{self.app_name}:{item}')
    
class CorpInquriySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return CorpId.objects.all().order_by('-corp_name')

    def location(self, obj):
        return """/services/corp/inquiry/%s""" % obj.pk