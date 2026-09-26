# Redo asciify due to broken signal definition

import builtins
from django.db import migrations, models
from expenses.utils import asciify


def populate_ascii_fields(apps, schema_editor):
    BillItem = apps.get_model('expenses', 'BillItem')

    for item in BillItem.objects.all():
        item.product_ascii = asciify(item.product)
        item.save(update_fields=['product_ascii'])


def reverse_populate(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0020_asciify_casefold'),
    ]

    operations = [
        migrations.RunPython(populate_ascii_fields, reverse_populate),
    ]
