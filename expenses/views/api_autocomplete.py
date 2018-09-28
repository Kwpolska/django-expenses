# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

import functools

from expenses.models import Expense
from expenses.utils import revchron
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def autocomplete_expense_provider(field):
    def wrap(f):
        @login_required
        def view(request):
            query = request.GET['q']
            results = f(request, query)
            return JsonResponse(
                [getattr(e, field) for e in reversed(revchron(results)[:10])],
                safe=False
            )

        return view
    return wrap


@autocomplete_expense_provider('vendor')
def expense_vendor(request, query):
    return Expense.objects.filter(user=request.user, vendor__istartswith=query)


@autocomplete_expense_provider('vendor')
def bill_vendor(request, query):
    return Expense.objects.filter(user=request.user, is_bill=True, vendor__istartswith=query)


@autocomplete_expense_provider('description')
def expense_description(request, query):
    vendor = request.GET.get('vendor')
    results = None
    if vendor:
        results = Expense.objects.filter(user=request.user, vendor__iexact=vendor,
                                         description__istartswith=query)
    if results is None or not results.exists():
        results = Expense.objects.filter(user=request.user,
                                         description__istartswith=query)

    return results
