# Generated by Django 2.1.2 on 2018-10-15 21:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0006_expensetemplate_comment_blank'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expensetemplate',
            name='type',
            field=models.CharField(choices=[('simple', 'Simple'), ('count', 'Multiplied by count')], default='simple', max_length=20, verbose_name='template type'),
        ),
    ]
