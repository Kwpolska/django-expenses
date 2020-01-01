# Django-Expenses
# Copyright © 2018-2020, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Expense views."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from expenses.forms import ExpenseForm
from expenses.models import Expense, BillItem, Category
from expenses.utils import revchron, today_date
from expenses.views import ExpDeleteView


@login_required
def expense_list(request, bills_only=False):
    exp = revchron(Expense.objects.filter(user=request.user).select_related('category'))
    if bills_only:
        exp = exp.filter(is_bill=True)
        htmltitle = _('Bills')
        pid = 'bill_list'
    else:
        htmltitle = _('Expenses')
        pid = 'expense_list'

    paginator = Paginator(exp, settings.EXPENSES_PAGE_SIZE)
    page = request.GET.get('page', '1')
    expenses = paginator.get_page(page)
    if page == '1' and not bills_only:
        show_form = True
        categories = Category.user_objects(request)
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

    return render(request, 'expenses/expense_add_edit.html', {
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

    return render(request, 'expenses/expense_show.html', {
        'htmltitle': str(expense),
        'pid': 'expense_show',
        'expense': expense,
    })


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if expense.is_bill:
        return HttpResponseRedirect(expense.get_absolute_url())
    form = ExpenseForm(instance=expense, user=request.user)

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense, user=request.user)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.is_bill = False
            expense.save()
            form.save_m2m()
            return HttpResponseRedirect(expense.get_absolute_url())

    return render(request, 'expenses/expense_add_edit.html', {
        'htmltitle': str(expense),
        'pid': 'expense_edit',
        'expense': expense,
        'form': form,
        'mode': 'edit',
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

    return render(request, 'expenses/expense_convert.html', {
        'pid': 'expense_convert',
        'expense': expense,
        'htmltitle': _("Convert"),
        'cancel_url': reverse('expenses:expense_show', args=[expense.pk]),
    })


@login_required
def expense_repeat(request, pk):
    old_expense = get_object_or_404(Expense, pk=pk, user=request.user, is_bill=False)
    new_expense = Expense(
        date=today_date(),
        vendor=old_expense.vendor,
        category=old_expense.category,
        amount=old_expense.amount,
        description=old_expense.description,
        user=request.user,
        is_bill=False)
    new_expense.save()
    messages.add_message(request, messages.SUCCESS,
                         _("Expense has been repeated successfully."))
    return HttpResponseRedirect(reverse('expenses:expense_show', args=[new_expense.pk]))
