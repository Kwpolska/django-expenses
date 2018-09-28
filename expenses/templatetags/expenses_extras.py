from itertools import zip_longest
from django import template

from expenses.utils import format_money, today_date

register = template.Library()
register.simple_tag(format_money, name='money')


@register.inclusion_tag('expenses/extras/expense_table.html', takes_context=True)
def expense_table(context, expenses):
    show_form = context.get('show_form', False)
    ctx = {'expenses': expenses, 'show_form': show_form, 'pid': context['pid']}
    if show_form:
        ctx['categories'] = context.get('categories', None)
        ctx['today'] = today_date()
    return ctx


@register.inclusion_tag('expenses/extras/template_table.html')
def template_table(templates):
    return {'templates': templates}


@register.inclusion_tag('expenses/extras/bill_template_table.html')
def bill_template_table(bill_templates):
    return {'bill_templates': bill_templates}


@register.inclusion_tag('expenses/extras/exp_paginator.html')
def exp_paginator(page):
    maxpage = page.paginator.num_pages
    num = page.number
    page_range = []
    if maxpage <= 5:
        page_range = list(range(num, maxpage + 1))
    else:
        if num == 1:
            around = {1, 2, 3}
        elif num == maxpage:
            around = {num - 2, num - 1, num}
        else:
            around = {num - 1, num, num + 1}
        around |= {1, maxpage}
        page_range_prop = [i for i in sorted(around) if 0 < i <= maxpage]
        for current_page, next_page in zip_longest(page_range_prop, page_range_prop[1:]):
            page_range.append(current_page)
            if next_page is None:
                continue
            diff = next_page - current_page
            if diff == 2:
                page_range.append(current_page + 1)  # ellipsis should not be one page
            elif diff > 2:
                page_range.append('...')

    return {'page': page, 'page_range': page_range}


@register.inclusion_tag('expenses/extras/expenses_add_toolbar.html')
def expenses_add_toolbar(pid):
    return {'pid': pid}


@register.inclusion_tag('expenses/extras/exp_category_toolbar.html')
def exp_category_toolbar(category, pid):
    return {'category': category, 'pid': pid}


@register.inclusion_tag('expenses/extras/exp_template_toolbar.html')
def exp_template_toolbar(pid):
    return {'pid': pid}


@register.inclusion_tag('expenses/extras/exp_menu_link.html', takes_context=True)
def exp_menu_link(context, title, url_name, link_pid):
    return {'title': title, 'url_name': url_name, 'link_pid': link_pid, 'current_pid': context.get('pid')}
