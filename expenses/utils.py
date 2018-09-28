# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

import babel.numbers
from django.utils import timezone
from django.conf import settings

from expenses.models import Category

def format_money(amount):
    if amount is None:
        amount = 0
    return babel.numbers.format_currency(amount, settings.EXPENSES_CURRENCY_CODE, locale=settings.EXPENSES_CURRENCY_LOCALE)


def today_date():
    return timezone.datetime.now().date()


def revchron(obj):
    return obj.order_by('-date', '-date_added')


def cat_objs(request):
    return Category.objects.filter(user=request.user).order_by('order')
