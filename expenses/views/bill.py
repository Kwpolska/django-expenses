# Django-Expenses
# Copyright © 2018-2019, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Bill management."""

import collections

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _, ngettext

from expenses.forms import BillForm
from expenses.models import Expense, BillItem
from expenses.views import ExpDeleteView
from expenses.views.expense import expense_list as _expense_list

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
            return HttpResponseRedirect(reverse('expenses:bill_show', args=[inst.pk]))

    return render(request, 'expenses/bill_add_editmeta.html', {
        'htmltitle': _("Add a bill"),
        'pid': 'bill_add',
        'form': form,
        'mode': 'add',
    })


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

    return render(request, 'expenses/bill_add_editmeta.html', {
        'htmltitle': str(expense),
        'pid': 'bill_editmeta',
        'expense': expense,
        'form': form,
        'mode': 'editmeta',
    })


@login_required
def bill_show(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    if not expense.is_bill:
        return HttpResponseRedirect(expense.get_absolute_url())

    status_msg = None
    status_type = None
    if request.method == 'POST':
        # Bill item editor
        # 1__field → edit, a1__field → add, d__1 → delete
        add_edit = collections.defaultdict(dict)
        delete = []
        for k, v in request.POST.items():
            if '__' not in k:
                continue  # CSRF token
            mid, name = k.split('__')
            if mid == 'd':
                # deletions
                delete.append(int(name))
            else:
                add_edit[mid][name] = v

        ok = 0
        err = 0

        # Add/edit
        for pk, values in add_edit.items():
            try:
                if pk.startswith('a'):
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
            status_msgs.append(ngettext(
                'Saved changes to %(count)d item.',
                'Saved changes to %(count)d items.',
                ok) % {'count': ok})

        if err:
            status_msgs.append(ngettext(
                'Failed to change %(count)d item.',
                'Failed to change %(count)d items.',
                err) % {'count': err})

        status_msg = ' '.join(status_msgs)
        if ok and err:
            status_type = 'alert-warning'
        elif ok:
            status_type = 'alert-success'
        elif err:
            status_type = 'alert-danger'

    return render(request, 'expenses/bill_show.html', {
        'htmltitle': str(expense),
        'pid': 'bill_show',
        'expense': expense,
        'items': expense.billitem_set.order_by('date_added'),
        'status_msg': status_msg,
        'status_type': status_type,
    })


class BillDelete(ExpDeleteView):
    model = Expense
    pid = 'bill_delete'
    success_url = reverse_lazy('expenses:bill_list')
    cancel_url = 'expenses:bill_show'
    cancel_key = 'pk'
