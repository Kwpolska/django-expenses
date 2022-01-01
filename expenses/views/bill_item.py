# Django-Expenses
# Copyright © 2018-2022, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Bill item views. Used only as a fallback."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import gettext as _

from expenses.forms import BillItemForm
from expenses.models import Expense, BillItem


@login_required
def bill_item_add(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if not expense.is_bill:
        return HttpResponseBadRequest("Expense is not a bill.")

    form = BillItemForm()
    if request.method == "POST":
        form = BillItemForm(request.POST)
        if form.is_valid():
            bi = form.save(commit=False)
            bi.user = request.user
            bi.bill = expense
            bi.save()
            form.save_m2m()
            return HttpResponseRedirect(expense.get_absolute_url())

    return render(
        request,
        "expenses/bill_item_add_edit.html",
        {
            "htmltitle": _("Add bill item"),
            "pid": "bill_item_add",
            "expense": expense,
            "form": form,
            "mode": "add",
        },
    )


@login_required
def bill_item_edit(request, bill_pk, item_pk):
    expense = get_object_or_404(Expense, pk=bill_pk, user=request.user)
    if not expense.is_bill:
        return HttpResponseBadRequest("Expense is not a bill.")
    bi = get_object_or_404(BillItem, pk=item_pk, bill=expense, user=request.user)

    form = BillItemForm(instance=bi)
    if request.method == "POST":
        form = BillItemForm(request.POST, instance=bi)
        if form.is_valid():
            bi = form.save(commit=False)
            bi.user = request.user
            bi.bill = expense
            bi.save()
            form.save_m2m()
            return HttpResponseRedirect(expense.get_absolute_url())

    return render(
        request,
        "expenses/bill_item_add_edit.html",
        {
            "htmltitle": _("Edit bill item"),
            "pid": "bill_item_edit",
            "expense": expense,
            "form": form,
            "mode": "edit",
        },
    )


@login_required
def bill_item_delete(request, bill_pk, item_pk):
    expense = get_object_or_404(Expense, pk=bill_pk, user=request.user)
    if not expense.is_bill:
        return HttpResponseBadRequest("Expense is not a bill.")
    bi = get_object_or_404(BillItem, pk=item_pk, bill=expense, user=request.user)
    next_url = reverse("expenses:bill_show", args=[bill_pk])

    if request.method == "POST":
        bi.delete()
        return HttpResponseRedirect(next_url)

    return render(
        request,
        "expenses/exp_confirm_delete.html",
        {"htmltitle": _("Delete %s") % bi, "pid": "bill_item_delete", "object": bi, "cancel_url": next_url},
    )
