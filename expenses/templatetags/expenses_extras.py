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
    return {'page': page}


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
