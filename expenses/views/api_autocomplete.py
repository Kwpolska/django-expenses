# Django-Expenses
# Copyright © 2018-2026, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

from expenses.models import Expense, BillItem
from expenses.utils import asciify
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def autocomplete_expense_provider(field):
    def wrap(f):
        @login_required
        def view(request):
            query = request.GET["q"]
            results = f(request, query)
            results = results.values_list(field, flat=True).distinct()
            return JsonResponse(list(reversed(results[:10])), safe=False)

        return view

    return wrap


@autocomplete_expense_provider("vendor")
def expense_vendor(request, query):
    return Expense.objects.filter(user=request.user, vendor_ascii__istartswith=asciify(query))


@autocomplete_expense_provider("description")
def expense_description(request, query):
    vendor = request.GET.get("vendor")
    results = None
    if vendor:
        results = Expense.objects.filter(user=request.user, vendor__iexact=vendor, description_ascii__istartswith=asciify(query))
    if results is None or not results.exists():
        results = Expense.objects.filter(user=request.user, description_ascii__istartswith=asciify(query))

    return results


@autocomplete_expense_provider("vendor")
def bill_vendor(request, query):
    return Expense.objects.filter(user=request.user, is_bill=True, vendor_ascii__istartswith=asciify(query))


def bill_item(request):
    query = request.GET["q"]
    vendor = request.GET["vendor"]
    results = (
        BillItem.objects.filter(user=request.user, bill__vendor__iexact=vendor, product_ascii__istartswith=asciify(query))
        .values("product", "serving", "unit_price")
        .distinct()
        .order_by("product")
    )

    return JsonResponse(list(results), safe=False)
