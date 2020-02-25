# Django-Expenses
# Copyright © 2018-2020, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Bill management."""

import collections

from django.db import connection
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _, ngettext

from expenses.forms import BillForm
from expenses.models import Expense, BillItem
from expenses.views import ExpDeleteView
from expenses.views.expense import expense_list as _expense_list


LAST_VENDORS_QUERY = """
SELECT "vendor", "category_id", "category_name" FROM (
    SELECT "vendor", "category_id", "category_name" FROM (
        SELECT "vendor", "category_id", "expenses_category"."name" AS "category_name" FROM "expenses_expense"
        INNER JOIN "expenses_category" ON ("category_id" = "expenses_category"."id")
        WHERE "is_bill" = true AND "expenses_expense"."user_id" = %s
        ORDER BY "expenses_expense"."date_added" DESC
        LIMIT 15
    ) source
    GROUP BY "vendor", "category_id", "category_name"
    ORDER BY COUNT(*) DESC, "vendor", "category_name"
    LIMIT 3
) limited
ORDER BY "vendor", "category_name";
"""


@login_required
def bill_list(request):
    return _expense_list(request, bills_only=True)


@login_required
def bill_add(request):
    form = BillForm(user=request.user)
    if request.method == "POST":
        form = BillForm(request.POST, user=request.user)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.user = request.user
            inst.is_bill = True
            inst.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse("expenses:bill_show", args=[inst.pk]))

    with connection.cursor() as cursor:
        cursor.execute(LAST_VENDORS_QUERY, [request.user.pk])
        last_vendors = cursor.fetchall()

    return render(
        request,
        "expenses/bill_add_editmeta.html",
        {"htmltitle": _("Add a bill"), "pid": "bill_add", "form": form, "mode": "add", "last_vendors": last_vendors,},
    )


@login_required
def bill_quickadd(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    quickadd_str = request.POST.get("quickadd")
    if quickadd_str is None:
        return HttpResponseBadRequest()
    category_id, vendor = quickadd_str.split(";", 1)
    inst = Expense(user=request.user, category_id=category_id, vendor=vendor, is_bill=True)
    inst.save()
    return HttpResponseRedirect(reverse("expenses:bill_show", args=[inst.pk]))


@login_required
def bill_editmeta(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if not expense.is_bill:
        return HttpResponseRedirect(expense.get_absolute_url())
    form = BillForm(instance=expense, user=request.user)

    if request.method == "POST":
        form = BillForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.is_bill = True
            expense.save()
            form.save_m2m()
            return HttpResponseRedirect(expense.get_absolute_url())

    return render(
        request,
        "expenses/bill_add_editmeta.html",
        {"htmltitle": str(expense), "pid": "bill_editmeta", "expense": expense, "form": form, "mode": "editmeta",},
    )


@login_required
def bill_show(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if not expense.is_bill:
        return HttpResponseRedirect(expense.get_absolute_url())

    if request.method == "POST":
        # Bill item editor
        # 1__field → edit, a1__field → add, d__1 → delete
        add_edit = collections.defaultdict(dict)
        delete = []
        for k, v in request.POST.items():
            if "__" not in k:
                continue  # CSRF token
            mid, name = k.split("__")
            if mid == "d":
                # deletions
                delete.append(int(name))
            else:
                add_edit[mid][name] = v

        ok = 0
        err = 0

        # Add/edit
        for pk, values in add_edit.items():
            try:
                if pk.startswith("a"):
                    bi = BillItem()
                else:
                    bi = BillItem.objects.get(pk=int(pk), user=request.user)
                for k, v in values.items():
                    setattr(bi, k, v)
                bi.user = request.user
                bi.bill = expense
                bi.save()
                ok += 1
            except BillItem.DoesNotExist:
                err += 1

        for pk in delete:
            try:
                bi = BillItem.objects.get(pk=pk, user=request.user)
                bi.delete()
                ok += 1
            except BillItem.DoesNotExist:
                err += 1

        status_msgs = []
        if ok:
            status_msgs.append(
                ngettext("Saved changes to %(count)d item.", "Saved changes to %(count)d items.", ok) % {"count": ok}
            )

        if err:
            status_msgs.append(
                ngettext("Failed to change %(count)d item.", "Failed to change %(count)d items.", err) % {"count": err}
            )

        status_type = messages.ERROR
        if ok and err:
            status_type = messages.WARNING
        elif ok:
            status_type = messages.SUCCESS

        if status_msgs:
            messages.add_message(request, status_type, " ".join(status_msgs))

    return render(
        request,
        "expenses/bill_show.html",
        {
            "htmltitle": str(expense),
            "pid": "bill_show",
            "expense": expense,
            "items": expense.billitem_set.order_by("date_added"),
        },
    )


class BillDelete(ExpDeleteView):
    model = Expense
    pid = "bill_delete"
    success_url = reverse_lazy("expenses:bill_list")
    cancel_url = "expenses:bill_show"
    cancel_key = "pk"
