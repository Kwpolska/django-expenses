# Generated by Django 2.1.2 on 2019-02-09 19:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0014_expense_description_cache_everywhere'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expensetemplate',
            name='type',
            field=models.CharField(choices=[('simple', 'Simple'), ('count', 'Multiplied by count'), ('description', 'With custom description'), ('desc_select', 'With description selected from list')], default='simple', max_length=20, verbose_name='Template type'),
        ),
    ]