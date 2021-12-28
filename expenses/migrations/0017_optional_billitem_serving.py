from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0016_menu_templates'),
    ]

    operations = [
        migrations.AlterField(
            model_name='billitem',
            name='serving',
            field=models.DecimalField(decimal_places=3, max_digits=10, null=True, verbose_name='Serving'),
        ),
    ]
