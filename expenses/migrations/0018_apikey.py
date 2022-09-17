from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('expenses', '0017_optional_billitem_serving'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deletionrecord',
            name='model',
            field=models.CharField(choices=[('category', 'category'), ('expense', 'expense'), ('billitem', 'billitem'), ('expensetemplate', 'expensetemplate'), ('apikey', 'apikey')], max_length=20),
        ),
        migrations.CreateModel(
            name='ApiKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=40, verbose_name='Name')),
                ('key', models.CharField(max_length=128, unique=True, verbose_name='Key')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
