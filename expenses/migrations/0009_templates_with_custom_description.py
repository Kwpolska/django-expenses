# Generated by Django 2.1.2 on 2018-10-28 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0008_field_friendly_names_change'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expensetemplate',
            name='description',
            field=models.CharField(max_length=80, verbose_name='Description'),
        ),
        migrations.AlterField(
            model_name='expensetemplate',
            name='type',
            field=models.CharField(choices=[('simple', 'Simple'), ('count', 'Multiplied by count'), ('description', 'With custom description')], default='simple', max_length=20, verbose_name='Template type'),
        ),
    ]
