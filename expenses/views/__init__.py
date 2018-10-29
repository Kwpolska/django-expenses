# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Generic views."""

import pygal
import pygal.style

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Sum
from django.shortcuts import render
from django.utils.html import mark_safe
from django.utils.decorators import method_decorator
from django.views.generic.edit import DeleteView
from django.urls import reverse

from expenses.utils import format_money, today_date, revchron, cat_objs, dict_overwrite
from expenses.models import Expense, Category, BillItem
from django.utils.translation import gettext as _


@login_required
def index(request):
    last_n_expenses = revchron(Expense.objects.filter(user=request.user))[:settings.EXPENSES_INDEX_COUNT]
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
    spending_per_category = [
        (Category.objects.get(pk=i['category']), i['sum'])
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


@login_required
def search(request):
    opt = {
        'q': '',
        'vendor': '',
        'search_for': 'expenses',
        'date_spec': 'any',
        'date_start': '',
        'date_end': ''
    }
    categories = cat_objs(request)
    if 'q' in request.GET or 'vendor' in request.GET:
        opt['has_query'] = True
        # Set search options (will be copied into template)
        dict_overwrite(opt, 'q', request.GET)
        dict_overwrite(opt, 'vendor', request.GET)
        dict_overwrite(opt, 'search_for', request.GET, 'for')
        dict_overwrite(opt, 'date_spec', request.GET, 'date-spec')
        dict_overwrite(opt, 'date_start', request.GET, 'date-start')
        dict_overwrite(opt, 'date_end', request.GET, 'date-end')

        includes = request.GET.getlist('include', [])
        opt['include_expenses'] = 'expenses' in includes
        opt['include_bills'] = 'bills' in includes

        cat_pks = {int(i) for i in request.GET.getlist('category', [])}
        categories_with_status = [(c, c.pk in cat_pks) for c in categories]

        # Do the search
        if opt['search_for'] == 'expenses':
            items = Expense.objects.filter(user=request.user, category__in=cat_pks)
            if opt['q']:
                items = items.filter(description__icontains=opt['q'])
            if opt['vendor']:
                items = items.filter(vendor__icontains=opt['vendor'])

            if opt['include_expenses'] and opt['include_bills']:
                pass
            elif opt['include_expenses']:
                items = items.filter(is_bill=False)
            elif opt['include_bills']:
                items = items.filter(is_bill=True)

            if opt['date_start'] and not opt['date_end']:
                items = items.filter(date__gte=opt['date_start'])
            elif opt['date_start'] and opt['date_end']:
                items = items.filter(date__gte=opt['date_start'], date__lte=opt['date_end'])

            items = revchron(items)
        elif opt['search_for'] == 'billitems':
            items = BillItem.objects.filter(user=request.user, bill__category__in=cat_pks)
            if opt['q']:
                items = items.filter(product__icontains=opt['q'])
            if opt['vendor']:
                items = items.filter(bill__vendor__icontains=opt['vendor'])

            if opt['date_start'] and not opt['date_end']:
                items = items.filter(bill__date__gte=opt['date_start'])
            elif opt['date_start'] and opt['date_end']:
                items = items.filter(bill__date__gte=opt['date_start'], bill__date__lte=opt['date_end'])

            items = items.order_by('-date_added')
        elif opt['search_for'] == 'purchases':
            cat_pks = {int(i) for i in request.GET.getlist('category', [])}

            if opt['date_start'] and not opt['date_end']:
                date_clause = 'AND d.date >= %s'
                date_args = [opt['date_start']]
            elif opt['date_start'] and opt['date_end']:
                date_clause = 'AND d.date BETWEEN %s AND %s'
                date_args = [opt['date_start'], opt['date_end']]
            else:
                date_clause = ''
                date_args = []

            ilike_word = 'LIKE' if connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3' else 'ILIKE'

            query_clause = ''
            query_args = []
            if opt['q']:
                query_clause += ' AND d.product ' + ilike_word + ' %s'
                query_args.append('%' + opt['q'] + '%')
            if opt['vendor']:
                query_clause += ' AND d.vendor ' + ilike_word + ' %s'
                query_args.append('%' + opt['vendor'] + '%')

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT d.date, d.vendor, d.product, d.unit_price FROM (
                        SELECT date, vendor, description AS product, amount AS unit_price, category_id, date_added
                        FROM expenses_expense WHERE is_bill = false AND user_id = %s
                    UNION
                        SELECT date, vendor, product, unit_price, category_id, expenses_billitem.date_added
                        FROM expenses_billitem
                        LEFT JOIN expenses_expense ON expenses_billitem.bill_id = expenses_expense.id
                        WHERE expenses_billitem.user_id = %s
                    ) AS d
                    WHERE d.category_id in ({cat_pks}) {date_clause}{query_clause}
                    ORDER BY d.date DESC, d.date_added DESC;""".format(
                    cat_pks=', '.join(str(i) for i in cat_pks), date_clause=date_clause, query_clause=query_clause),
                    [request.user.pk, request.user.pk] + date_args + query_args
                )
                items = cursor.fetchall()
                # TODO better pagination performance
        else:
            raise Exception("Unknown search type")
    else:
        opt['include_expenses'] = True
        opt['include_bills'] = True
        opt['has_query'] = False
        categories_with_status = [(c, True) for c in categories]
        items = None

    context = {
        'htmltitle': _('Search'),
        'pid': 'search',
        'categories_with_status': categories_with_status
    }
    context.update(opt)
    if items is not None:
        paginator = Paginator(items, settings.EXPENSES_PAGE_SIZE)
        page = request.GET.get('page', '1')
        context['items'] = paginator.get_page(page)
    return render(request, 'expenses/search.html', context)


@method_decorator(login_required, name='dispatch')
class ExpDeleteView(DeleteView):
    template_name = 'expenses/exp_confirm_delete.html'

    def get_context_data(self, **kwargs):
        obj = kwargs['object']
        return {
            'htmltitle': _("Delete %s") % obj,
            'pid': self.pid,
            'object': obj,
            'cancel_url': reverse(self.cancel_url, args=[getattr(obj, self.cancel_key)])
        }
