import json

from django import template
from django.conf import settings
from django.utils.html import mark_safe

from expenses.pagination import pagination
from expenses.utils import format_money, today_date

register = template.Library()
register.simple_tag(format_money, name='money')


@register.simple_tag()
def exp_config_json():
    return mark_safe(json.dumps({
        'currencyCode': settings.EXPENSES_CURRENCY_CODE,
        'currencyLocale': settings.EXPENSES_CURRENCY_LOCALE
    }))


@register.simple_tag(takes_context=True)
def exp_set_page(context, page):
    get = context['request'].GET.copy()
    get['page'] = page
    return '?' + get.urlencode()


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


@register.inclusion_tag('expenses/extras/exp_paginator.html', takes_context=True)
def exp_paginator(context, page):
    page_range = pagination(page.number, page.paginator.num_pages)
    return {'page': page, 'page_range': page_range, 'request': context['request']}


@register.inclusion_tag('expenses/extras/expenses_add_toolbar.html')
def expenses_add_toolbar(pid):
    return {'pid': pid}


@register.inclusion_tag('expenses/extras/exp_category_toolbar.html')
def exp_category_toolbar(category, pid):
    return {'category': category, 'pid': pid}


@register.inclusion_tag('expenses/extras/exp_menu_link.html', takes_context=True)
def exp_menu_link(context, title, url_name, link_pid):
    return {'title': title, 'url_name': url_name, 'link_pid': link_pid, 'current_pid': context.get('pid')}


@register.inclusion_tag('expenses/extras/exp_template_actions.html')
def exp_template_actions(the_template, show_title=False, show_date=False):
    return {'template': the_template, 'show_title': show_title, 'show_date': show_date, 'today': today_date()}
