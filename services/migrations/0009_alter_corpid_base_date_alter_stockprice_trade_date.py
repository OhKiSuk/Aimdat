# Generated by Django 4.1.5 on 2023-05-28 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0008_remove_corpid_is_crawl_corpid_base_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='corpid',
            name='base_date',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='stockprice',
            name='trade_date',
            field=models.CharField(max_length=255),
        ),
    ]
