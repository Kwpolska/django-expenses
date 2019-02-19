# Django-Expenses
# Copyright © 2018-2019, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Assorted Expenses utilities."""

import babel.numbers
import datetime
import decimal
import iso8601
import itertools
import typing
from django.utils import timezone
from django.conf import settings
from django.utils.translation import get_language


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


def serialize_date(date: datetime.date) -> str:
    """Serialize a datetime."""
    return date.isoformat()


def serialize_dt(dt: datetime.datetime) -> str:
    """Serialize a datetime."""
    return dt.isoformat()


def serialize_decimal(amount: decimal.Decimal) -> str:
    """Serialize a decimal value."""
    return str(amount)


def parse_date(date_str: str) -> datetime.date:
    """Parse an ISO 8601 date."""
    return iso8601.parse_date(date_str).date()


def parse_dt(dt_str: str) -> datetime.datetime:
    """Parse an ISO 8601 datetime."""
    return iso8601.parse_date(dt_str)


def parse_decimal(amount_str: str) -> decimal.Decimal:
    """Parse a decimal object."""
    return decimal.Decimal(amount_str)


def get_babel_locale() -> str:
    """Get a babel-friendly locale name."""
    lang, region = get_language().split('-')
    return f"{lang}_{region.upper()}"


T = typing.TypeVar('T')


def peek(iterable: typing.Iterable[T]) -> (T, typing.Iterable[T]):
    """Peek at the first row of an iterable.

    Returns (first row, iterable with first row)."""
    iterator = iter(iterable)
    first_row = next(iterator)
    return first_row, itertools.chain([first_row], iterator)
