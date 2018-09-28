# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

from expenses.models import Expense
from expenses.utils import revchron
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


@login_required
def expense_vendor(request):
    query = request.GET['q']
    results = Expense.objects.filter(user=request.user, vendor__istartswith=query)
    return JsonResponse(
        [e.vendor for e in reversed(revchron(results)[10:])],
        safe=False
    )


@login_required
def bill_vendor(request):
    query = request.GET['q']
    results = Expense.objects.filter(user=request.user, is_bill=True, vendor__istartswith=query)
    return JsonResponse(
        [e.vendor for e in reversed(revchron(results)[10:])],
        safe=False
    )


@login_required
def expense_description(request):
    query = request.GET['q']
    vendor = request.GET.get('vendor')
    results = None
    if vendor:
        results = Expense.objects.filter(user=request.user, vendor__iexact=vendor,
                                         description__istartswith=query)
    if results is None or results.exists():
        results = Expense.objects.filter(user=request.user,
                                         description__istartswith=query)

    return JsonResponse(
        [e.vendor for e in reversed(revchron(results)[10:])],
        safe=False
    )
