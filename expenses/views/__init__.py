# Django-Expenses
# Copyright © 2018-2019, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Generic views."""

import pygal
import pygal.style

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.html import mark_safe
from django.utils.decorators import method_decorator
from django.views.generic.edit import DeleteView
from django.urls import reverse

from expenses.utils import format_money, today_date, revchron
from expenses.models import Expense, Category
from django.utils.translation import gettext as _


@login_required
def index(request):
    last_n_expenses = revchron(Expense.objects.filter(user=request.user).select_related('category'))[:settings.EXPENSES_INDEX_COUNT]
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT date, SUM(amount)
            FROM expenses_expense
            WHERE user_id = %s
            GROUP BY date
            ORDER BY date DESC
            LIMIT 3""", [request.user.pk])
        last_3_days = cursor.fetchall()
    last_3_days_sum = sum(r[1] for r in last_3_days)
    last_3_days = reversed(last_3_days)

    today = today_date()
    prev_month = today.month - 1
    prev_year = today.year
    while prev_month < 0:
        prev_month += 12
        prev_year -= 1

    current_months_total = Expense.objects.filter(user=request.user, date__year=today.year, date__month=today.month).aggregate(Sum('amount'))['amount__sum']
    previous_months_total = Expense.objects.filter(user=request.user, date__year=prev_year, date__month=prev_month).aggregate(Sum('amount'))['amount__sum'] or 0

    spending_per_category_qs = Expense.objects.filter(user=request.user).values('category').annotate(sum=Sum('amount')).order_by('-sum')
    categories = {cat.pk: cat for cat in Category.objects.filter(user=request.user)}
    spending_per_category = [
        (categories[i['category']], i['sum'])
        for i in spending_per_category_qs
    ]

    pie_chart = pygal.Pie(disable_xml_declaration=True, margin=0, legend_at_bottom=True,
                          print_values=True, print_labels=True,
                          style=pygal.style.DefaultStyle(plot_background='white', background='white',
                                                         font_family='var(--font-family-sans-serif)',
                                                         label_font_size=20,
                                                         value_font_size=20,
                                                         value_label_font_size=20,
                                                         tooltip_font_size=20,
                                                         legend_font_size=20))
    for c, s in spending_per_category:
        pie_chart.add(c.name, float(s), formatter=format_money)
    category_chart = mark_safe(pie_chart.render())

    return render(request, 'expenses/index.html', {
        'htmltitle': _("Expenses Dashboard"),
        'pid': 'expenses_index',
        'last_n_expenses': last_n_expenses,
        'EXPENSES_INDEX_COUNT': settings.EXPENSES_INDEX_COUNT,
        'last_3_days': last_3_days,
        'last_3_days_sum': last_3_days_sum,
        'current_months_total': current_months_total,
        'previous_months_total': previous_months_total,
        'spending_per_category': spending_per_category,
        'category_chart': category_chart,
    })


@method_decorator(login_required, name='dispatch')
class ExpDeleteView(DeleteView):
    template_name = 'expenses/exp_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.add_message(request, messages.SUCCESS,
        _("%s has been deleted.") % self.object)
        return HttpResponseRedirect(success_url)

    def get_context_data(self, **kwargs):
        obj = kwargs['object']
        return {
            'htmltitle': _("Delete %s") % obj,
            'pid': self.pid,
            'object': obj,
            'cancel_url': reverse(self.cancel_url, args=[getattr(obj, self.cancel_key)])
        }
