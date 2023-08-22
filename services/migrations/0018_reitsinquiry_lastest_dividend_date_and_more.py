# Generated by Django 4.1.5 on 2023-08-22 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0017_reitsinquiry_delete_inquiry'),
    ]

    operations = [
        migrations.AddField(
            model_name='reitsinquiry',
            name='lastest_dividend_date',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='reitsinquiry',
            name='lastest_dividend_rate',
            field=models.DecimalField(decimal_places=2, max_digits=10, null=True),
        ),
    ]
