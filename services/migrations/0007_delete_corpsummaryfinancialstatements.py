# Generated by Django 4.1.5 on 2023-05-17 13:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0006_rename_divdend_investmentindex_dividend'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CorpSummaryFinancialStatements',
        ),
    ]
