# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Expense views."""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from expenses.forms import ExpenseForm
from expenses.models import Expense, BillItem
from expenses.utils import revchron, cat_objs
from expenses.views import ExpDeleteView


@login_required
def expense_list(request, bills_only=False):
    exp = revchron(Expense.objects.filter(user=request.user))
    if bills_only:
        exp = exp.filter(is_bill=True)
        htmltitle = _('Bills')
        pid = 'bill_list'
    else:
        htmltitle = _('Expenses')
        pid = 'expense_list'

    paginator = Paginator(exp.order_by('-id'), settings.EXPENSES_PAGE_SIZE)
    page = request.GET.get('page', '1')
    expenses = paginator.get_page(page)
    if page == '1' and not bills_only:
        show_form = True
        categories = cat_objs(request)
    else:
        show_form = False
        categories = None
    return render(request, 'expenses/expense_list.html', {
        'htmltitle': htmltitle,
        'pid': pid,
        'expenses': expenses,
        'bills_only': bills_only,
        'show_form': show_form,
        'categories': categories,
    })


@login_required
def expense_add(request):
    form = ExpenseForm(user=request.user)
    if request.method == "POST":
        form = ExpenseForm(request.POST, user=request.user)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.user = request.user
            inst.is_bill = False
            inst.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse('expenses:expense_list'))

    return render(request, 'expenses/expense_add_show.html', {
        'htmltitle': _("Add an expense"),
        'pid': 'expense_add',
        'form': form,
        'mode': 'add',
    })


@login_required
def expense_show(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if expense.is_bill:
        return HttpResponseRedirect(expense.get_absolute_url())
    form = ExpenseForm(instance=expense, user=request.user)
    saved = False

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.is_bill = False
            expense.save()
            form.save_m2m()
            saved = True

    return render(request, 'expenses/expense_add_show.html', {
        'htmltitle': str(expense),
        'pid': 'expense_show',
        'expense': expense,
        'form': form,
        'mode': 'show',
        'saved': saved,
    })


class ExpenseDelete(ExpDeleteView):
    model = Expense
    pid = 'expense_delete'
    success_url = reverse_lazy('expenses:expense_list')
    cancel_url = 'expenses:expense_show'
    cancel_key = 'pk'


@login_required
def expense_convert(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if request.method == "POST":
        amount = expense.amount  # the amount gets reset to 0 during the conversion
        if expense.is_bill:
            expense.description = expense.desc_auto
            expense.is_bill = False
            expense.billitem_set.all().delete()
            expense.amount = amount
            expense.save()
            return HttpResponseRedirect(reverse('expenses:expense_show', args=[expense.pk]))
        else:
            expense.is_bill = True
            expense.save()
            billitem = BillItem()
            billitem.bill = expense
            billitem.product = expense.description
            billitem.serving = 1
            billitem.count = 1
            billitem.unit_price = amount
            billitem.user = expense.user
            billitem.save()
            return HttpResponseRedirect(reverse('expenses:bill_show', args=[expense.pk]))
        # TODO

    return render(request, 'expenses/expense_convert.html', {
        'pid': 'expense_convert',
        'expense': expense,
        'htmltitle': _("Convert"),
        'cancel_url': reverse('expenses:expense_show', args=[expense.pk]),
    })
