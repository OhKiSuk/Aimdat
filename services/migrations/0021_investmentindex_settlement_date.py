# Generated by Django 4.1.5 on 2023-10-18 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0020_corpid_is_financial_industry'),
    ]

    operations = [
        migrations.AddField(
            model_name='investmentindex',
            name='settlement_date',
            field=models.CharField(max_length=255, null=True),
        ),
    ]