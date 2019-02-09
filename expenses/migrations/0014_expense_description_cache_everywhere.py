from django.db import migrations


def generate_cached_descriptions_everywhere(apps, schema_editor):
    Expense = apps.get_model('expenses', 'Expense')
    for expense in Expense.objects.filter():
        if expense.description:
            expense.description_cache = expense.description
            expense.save()


class Migration(migrations.Migration):

    dependencies = [
        ('expenses', '0013_expense_description_cache'),
    ]

    operations = [
        migrations.RunPython(generate_cached_descriptions_everywhere),
    ]
