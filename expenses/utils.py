# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Assorted Expenses utilities."""

import babel.numbers
import decimal
import typing
from django.utils import timezone
from django.conf import settings


def format_money(amount: typing.Union[int, float, decimal.Decimal]) -> str:
    """Format an amount of money for display."""
    if amount is None:
        amount = 0
    return babel.numbers.format_currency(amount, settings.EXPENSES_CURRENCY_CODE, locale=settings.EXPENSES_CURRENCY_LOCALE)


def today_date() -> datetime.date:
    """Get today’s date."""
    return timezone.now().date()


def revchron(qs):
    """Sort expenses in reverse-chronological order."""
    return qs.order_by('-date', '-date_added')


def round_money(amount: decimal.Decimal) -> decimal.Decimal:
    """Round money in a way appropriate for money."""
    return amount.quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_HALF_UP)


def dict_overwrite(destdict: dict, destkey, srcdict: dict, srckey=None) -> None:
    """Override a dict key with one taken from another dict."""
    destdict[destkey] = srcdict.get(srckey or destkey, destdict[destkey])
