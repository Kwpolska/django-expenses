import json
import decimal

from django import template
from django.conf import settings
from django.utils import formats
from django.utils.html import mark_safe
from django.urls import reverse

from expenses.pagination import pagination
from expenses.utils import format_money, today_date

register = template.Library()
register.simple_tag(format_money, name="money")


@register.simple_tag()
def exp_config_json():
    return mark_safe(
        json.dumps(
            {
                "baseUrl": reverse("expenses:index"),
                "currencyCode": settings.EXPENSES_CURRENCY_CODE,
                "currencyLocale": settings.EXPENSES_CURRENCY_LOCALE,
            }
        )
    )


@register.simple_tag(takes_context=True)
def exp_set_page(context, page):
    get = context["request"].GET.copy()
    get["page"] = page
    return "?" + get.urlencode()


@register.inclusion_tag("expenses/extras/expense_table.html", takes_context=True)
def expense_table(context, expenses):
    show_form = context.get("show_form", False)
    ctx = {"expenses": expenses, "show_form": show_form, "pid": context["pid"]}
    if show_form:
        ctx["categories"] = context.get("categories", None)
        ctx["today"] = today_date()
    return ctx


@register.inclusion_tag("expenses/extras/template_table.html")
def template_table(templates):
    return {"templates": templates}


@register.inclusion_tag("expenses/extras/exp_paginator.html", takes_context=True)
def exp_paginator(context, page):
    page_range = pagination(page.number, page.paginator.num_pages)
    return {"page": page, "page_range": page_range, "request": context["request"]}


@register.inclusion_tag("expenses/extras/expenses_add_toolbar.html")
def expenses_add_toolbar(pid):
    return {"pid": pid}


@register.inclusion_tag("expenses/extras/exp_category_toolbar.html")
def exp_category_toolbar(category, pid):
    return {"category": category, "pid": pid}


@register.inclusion_tag("expenses/extras/exp_menu_link.html", takes_context=True)
def exp_menu_link(context, title, url_name, link_pid):
    return {"title": title, "url_name": url_name, "link_pid": link_pid, "current_pid": context.get("pid")}


@register.inclusion_tag("expenses/extras/exp_template_actions.html")
def exp_template_actions(the_template, show_title=False, show_date=False):
    return {"template": the_template, "show_title": show_title, "show_date": show_date, "today": today_date()}


# A modified version of Django’s floatformat, with locale-independent output.
# https://github.com/django/django/blob/e7fd69d051eaa67cb17f172a39b57253e9cb831a/django/template/defaultfilters.py#L94
@register.filter(is_safe=True)
def floatformatll(text, arg=-1):
    """
    Display a float to a specified number of decimal places.
    If called without an argument, display the floating point number with one
    decimal place -- but only if there's a decimal place to be displayed:
    * num1 = 34.23234
    * num2 = 34.00000
    * num3 = 34.26000
    * {{ num1|floatformat }} displays "34.2"
    * {{ num2|floatformat }} displays "34"
    * {{ num3|floatformat }} displays "34.3"
    If arg is positive, always display exactly arg number of decimal places:
    * {{ num1|floatformat:3 }} displays "34.232"
    * {{ num2|floatformat:3 }} displays "34.000"
    * {{ num3|floatformat:3 }} displays "34.260"
    If arg is negative, display arg number of decimal places -- but only if
    there are places to be displayed:
    * {{ num1|floatformat:"-3" }} displays "34.232"
    * {{ num2|floatformat:"-3" }} displays "34"
    * {{ num3|floatformat:"-3" }} displays "34.260"
    If the input float is infinity or NaN, display the string representation
    of that value.
    """
    input_val = repr(text)
    try:
        d = decimal.Decimal(input_val)
    except decimal.InvalidOperation:
        try:
            d = decimal.Decimal(str(float(text)))
        except (ValueError, decimal.InvalidOperation, TypeError):
            return ""
    try:
        p = int(arg)
    except ValueError:
        return input_val

    try:
        m = int(d) - d
    except (ValueError, OverflowError, decimal.InvalidOperation):
        return input_val

    if not m and p < 0:
        return mark_safe(formats.number_format("%d" % (int(d)), 0, use_l10n=False))

    exp = decimal.Decimal(1).scaleb(-abs(p))
    # Set the precision high enough to avoid an exception (#15789).
    tupl = d.as_tuple()
    units = len(tupl[1])
    units += -tupl[2] if m else tupl[2]
    prec = abs(p) + units + 1

    # Avoid conversion to scientific notation by accessing `sign`, `digits`,
    # and `exponent` from Decimal.as_tuple() directly.
    sign, digits, exponent = d.quantize(exp, decimal.ROUND_HALF_UP, decimal.Context(prec=prec)).as_tuple()
    digits = [str(digit) for digit in reversed(digits)]
    while len(digits) <= abs(exponent):
        digits.append("0")
    digits.insert(-exponent, ".")
    if sign:
        digits.append("-")
    number = "".join(reversed(digits))
    return mark_safe(formats.number_format(number, abs(p), use_l10n=False))
