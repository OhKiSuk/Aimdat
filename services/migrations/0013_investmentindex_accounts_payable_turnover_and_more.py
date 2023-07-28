# Generated by Django 4.1.5 on 2023-07-18 04:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0012_alter_corpinfo_corp_homepage_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='investmentindex',
            name='accounts_payable_turnover',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='accounts_receivables_turnover',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='assets_growth',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='financing_cash_flow',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='gross_profit_margin',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='interest_coverage_ratio',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='inventory_turnover',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='investing_cash_flow',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='net_profit_growth',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='net_worth_growth',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='operating_cash_flow',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='operating_profit_growth',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='revenue_growth',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='roic',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='total_assests_turnover',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='total_assets',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='total_capital',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='total_debt',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='working_capital_once',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
        migrations.AddField(
            model_name='investmentindex',
            name='working_capital_requirement',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
    ]
