# Django-Expenses
# Copyright © 2018-2019, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Report support framework."""
import abc
import decimal
import itertools
import urllib.parse
import operator

import attr
import datetime
import enum
import typing

import django.http
from babel.dates import format_skeleton
from django.db import connection
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import SafeString
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _
from expenses.models import Category
from expenses.utils import format_money, get_babel_locale, peek


class Engine(enum.Enum):
    SQLITE3 = 'django.db.backends.sqlite3'
    POSTGRESQL = 'django.db.backends.postgresql_psycopg2'
    ANY_ENGINE = ''


@attr.s(auto_attribs=True, frozen=True)
class Option:
    name: str
    option_id: str


@attr.s(auto_attribs=True, frozen=True)
class OptionGroup:
    """A group of options."""
    name: str
    option_id: str
    options: typing.List[Option] = attr.Factory(list)
    type: str = "radio"  # radio, check, text

    def __getitem__(self, item):
        return self.options[item]

    def __iter__(self):
        return iter(self.options)


@attr.s(auto_attribs=True, frozen=True)
class CheckOption(Option):
    """A radio or checkbox option."""
    type: str = attr.ib("check", init=False, repr=False)


@attr.s(auto_attribs=True, frozen=True)
class TextFieldOption(Option):
    """A text field option, which can have an enabler checkbox attached."""
    required: bool = True
    enabler: typing.Optional[str] = None
    enabled_by_default: bool = True
    type: str = attr.ib("text", init=False, repr=False)


class Report(metaclass=abc.ABCMeta):
    name: str = None
    slug: str = None
    description: str = None
    request: django.http.HttpRequest = None
    options: typing.List[CheckOption] = []
    settings: typing.Dict[CheckOption, typing.Union[str, bool]] = {}

    @classmethod
    def meta_to_dict(cls) -> typing.Dict[str, typing.Any]:
        return {"name": cls.name, "slug": cls.slug, "description": cls.description, "options": cls.options}

    def __init__(self, request, settings):
        self.request = request
        self.settings = settings

    @abc.abstractmethod
    def run(self) -> typing.Union[str, SafeString]:
        raise NotImplementedError()


class SimpleSQLReport(Report):
    sql: typing.Dict[str, typing.Dict[Engine, str]] = {}
    column_headers: (typing.List[str], typing.List[str]) = []
    query_type: str = None

    def get_query(self, query_type: str, engine: Engine) -> str:
        sql_for_type = self.sql[query_type]
        if Engine.ANY_ENGINE in sql_for_type:
            return sql_for_type[Engine.ANY_ENGINE]
        elif engine in sql_for_type:
            return sql_for_type[engine]
        else:
            raise ValueError(f"Report does not support engine {engine}.")

    def query(self, cursor, sql: str) -> typing.Iterable:
        sql_params = [self.request.user.id]
        cursor.execute(sql, sql_params)
        return cursor.fetchall()

    def get_column_headers(self, engine: Engine) -> (typing.List[str], typing.List[str]):
        return self.column_headers

    def preprocess_rows(self, results: typing.Iterable) -> typing.Iterable:
        return results

    def tabulate(self, results: typing.Iterable, engine: Engine) -> SafeString:
        column_headers: (typing.List[str], typing.List[str]) = self.get_column_headers(engine)
        column_header_names, column_alignment = column_headers
        column_headers_with_alignment = zip(*column_headers)
        if not results:
            return no_results_to_show()
        results = self.preprocess_rows(results)

        first_row, results = peek(results)
        if len(column_header_names) != len(first_row):
            raise ValueError("Results do not match expected column headers")
        results_with_alignment = (zip(row, column_alignment) for row in results)

        return mark_safe(render_to_string("expenses/reports/report_basic_table.html", {
            'results_with_alignment': results_with_alignment,
            'column_headers_with_alignment': column_headers_with_alignment,
        }, self.request))

    def run(self) -> SafeString:
        engine: Engine = Engine(connection.settings_dict['ENGINE'])
        sql: str = self.get_query(self.query_type, engine)

        with connection.cursor() as cursor:
            results: typing.Iterable = self.query(cursor, sql)

        return self.tabulate(results, engine)


def format_yearmonth(yearmonth: str) -> str:
    """Format a year-month pair as a locale-dependent string."""
    # Querying for yearmonth is easier (especially with sqlite3) and about the same speed,
    # even if we need to apply some more logic Python-side to make it look nice.
    year, month = map(int, yearmonth.split("-"))
    return format_skeleton(
        'yMMMM',
        datetime.date(year, month, 1),
        locale=get_babel_locale())


class MonthCategoryBreakdown(SimpleSQLReport):
    name = _("Month/Category breakdown")
    slug = "month_category_breakdown"
    description = _("Show expenses broken down by month and category.")
    sql = {
        "month_category": {
            Engine.POSTGRESQL: """
            SELECT to_char(date, 'YYYY-MM') AS yearmonth, category_id, SUM(amount)
            FROM expenses_expense, expenses_category
            WHERE expenses_expense.user_id = %s AND category_id = expenses_category.id
            GROUP BY yearmonth, category_id, expenses_category.order
            ORDER BY yearmonth, expenses_category.order, category_id;
            """,
            Engine.SQLITE3: """
            SELECT STRFTIME('%%Y-%%m', date) AS yearmonth, category_id, SUM(amount)
            FROM expenses_expense, expenses_category
            WHERE expenses_expense.user_id = %s AND category_id = expenses_category.id
            GROUP BY yearmonth, category_id, "expenses_category"."order"
            ORDER BY yearmonth, "expenses_category"."order", category_id;
            """},
        "month": {
            Engine.POSTGRESQL: """
            SELECT to_char(date, 'YYYY-MM') AS yearmonth, SUM(amount)
            FROM expenses_expense
            WHERE expenses_expense.user_id = %s
            GROUP BY yearmonth ORDER BY yearmonth;
            """,
            Engine.SQLITE3: """
            SELECT STRFTIME('%%Y-%%m', date) AS yearmonth, SUM(amount)
            FROM expenses_expense
            WHERE expenses_expense.user_id = %s
            GROUP BY yearmonth ORDER BY yearmonth;
            """
        },
        "category": {
            Engine.ANY_ENGINE: """
            SELECT category_id, SUM(amount)
            FROM expenses_expense, expenses_category
            WHERE expenses_expense.user_id = %s AND category_id = expenses_category.id
            GROUP BY category_id, "expenses_category"."order"
            ORDER BY "expenses_category"."order", category_id;
        """}
    }
    options = [
        OptionGroup(_("Break down expenses by:"), "breakdown", [
            CheckOption(_("Month and category"), "month_category"),
            CheckOption(_("Month"), "month"),
            CheckOption(_("Category"), "category"),
        ])
    ]

    def __init__(self, request, settings: typing.Dict[CheckOption, typing.Any]):
        super().__init__(request, settings)
        # Only selected options will be in settings
        if settings:
            self.query_type = next(iter(settings)).option_id
        else:
            raise ValueError("Query type unknown")

    def get_column_headers(self, engine: Engine) -> (typing.List[str], typing.List[str]):
        if self.query_type == "month_category":
            user_categories: typing.Iterable[Category] = Category.user_objects(self.request)
            names = [_("Month")] + [c.html_link() for c in user_categories] + [_("Total")]
            return names, ["right"] * len(names)
        elif self.query_type == "category":
            return (
                [_("Category"), _("Total")],
                ["left", "right"]
            )
        elif self.query_type == "month":
            return (
                [_("Month"), _("Total")],
                ["right", "right"]
            )

    def preprocess_rows(self, results: typing.Iterable) -> typing.Iterable:
        if self.query_type == "month_category":
            user_categories: typing.Iterable[Category] = Category.user_objects(self.request)
            user_category_ids: typing.Dict[int, int] = {}
            cat_totals: typing.Dict[int, typing.Union[float, decimal.Decimal]] = {}
            for n, cat in enumerate(user_categories, 1):
                user_category_ids[cat.pk] = n
                cat_totals[cat.pk] = 0
            cat_count = len(user_category_ids)
            for yearmonth, items in itertools.groupby(results, operator.itemgetter(0)):
                row = [format_yearmonth(yearmonth)] + [format_money(0)] * cat_count
                row_total = 0
                for _ym, category_id, value in items:
                    row[user_category_ids[category_id]] = format_money(value)
                    row_total += value
                    cat_totals[category_id] += value
                row.append(format_money(row_total))
                yield row

            cat_totals_values = list(cat_totals.values())
            yield [_("Grand Total")] + [format_money(i) for i in cat_totals_values] + [format_money(sum(cat_totals_values))]

        elif self.query_type == "month":
            total = 0
            for yearmonth, value in results:
                yield format_yearmonth(yearmonth), format_money(value)
                total += value

            yield _("Grand Total"), format_money(total)
        else:
            # category
            user_categories: typing.Dict[int, Category] = {
                c.pk: c
                for c in Category.user_objects(self.request)}
            total = 0
            for category, value in results:
                yield (user_categories[category].html_link(), format_money(value))
                total += value

            yield _("Grand Total"), format_money(total)


class VendorStats(SimpleSQLReport):
    name = _("Vendor statistics")
    slug = "vendor_stats"
    description = _("Get basic statistics about money spent at each vendor. Includes vendors with at least 2 separate purchases.")
    query_type = "vendor_stats"

    sql = {
        "vendor_stats": {Engine.ANY_ENGINE: """
        SELECT vendor, COUNT(*) AS count, SUM(amount) AS sum, AVG(amount) AS avg
        FROM expenses_expense
        WHERE user_id = %s GROUP BY vendor HAVING COUNT(*) > 1
        ORDER BY sum DESC, vendor;
        """}
    }

    def get_column_headers(self, engine: Engine) -> (typing.List[str], typing.List[str]):
        return [_("Vendor"), _("Count"), _("Sum"), _("Average")], ["left", "right", "right", "right"]

    def preprocess_rows(self, results: typing.Iterable) -> typing.Iterable:
        total_count = 0
        total_amount = 0
        for vendor, count, amount, avg in results:
            url = reverse('expenses:search') + "?for=expenses&include=expenses&include=bills&category_all=true&q=" + urllib.parse.quote_plus(vendor)
            vendor_link = format_html('<a href="{}">{}</a>', url, vendor)
            total_count += count
            total_amount += amount
            yield vendor_link, count, format_money(amount), format_money(avg)

        if total_count > 0:
            yield _("Grand Total"), total_count, format_money(total_amount), format_money(total_amount/total_count)


class DailySpending(SimpleSQLReport):
    name = _("Daily spending")
    slug = "daily_spending"
    description = _("Get daily, weekly, monthly average spending.")
    sql = {
        "data": {Engine.ANY_ENGINE: """
        SELECT category_id, COUNT(amount), SUM(amount)
        FROM expenses_expense, expenses_category
        WHERE expenses_expense.user_id = %s AND category_id = expenses_category.id
        GROUP BY category_id, "expenses_category"."order"
        ORDER BY "expenses_category"."order", category_id;
        """},
        "day_counts": {
            Engine.SQLITE3: "SELECT COUNT(DISTINCT date), MAX(julianday(date)) - MIN(julianday(date)) FROM expenses_expense WHERE user_id=%s;",
            Engine.POSTGRESQL: "SELECT COUNT(DISTINCT date), MAX(date) - MIN(date) FROM expenses_expense WHERE user_id=%s;"
        }
    }

    def run(self):
        engine: Engine = Engine(connection.settings_dict['ENGINE'])

        days: typing.Dict[str, int] = {}
        days_names = ("expense_days", "all_days")
        with connection.cursor() as cursor:
            sql: str = self.get_query("day_counts", engine)
            cursor.execute(sql, [self.request.user.id])
            expense_days, all_days = cursor.fetchone()
            days["expense_days"] = int(expense_days)
            days["all_days"] = int(all_days)

            sql: str = self.get_query("data", engine)
            cursor.execute(sql, [self.request.user.id])
            cat_data: typing.List[tuple] = cursor.fetchall()

        if days["all_days"] == 0:
            return no_results_to_show()

        user_categories: typing.Iterable[Category] = Category.user_objects(self.request)
        timescales = [1, 7, 30, 365]
        timescale_names = {
            1: _("Per 1 day"),
            7: _("Per week (7 days)"),
            30: _("Per month (30 days)"),
            365: _("Per year (365 days)")
        }

        all_time_count = all_time_sum = 0
        for _cat, at_cat_count, at_cat_sum in cat_data:
            all_time_count += at_cat_count
            all_time_sum += at_cat_sum

        daily_data = self.compute_daily_data(all_time_count, all_time_sum, days, days_names, timescales, timescale_names)
        cat_tables = self.compute_category_data(cat_data, user_categories, days, days_names, timescales, timescale_names)

        return mark_safe(render_to_string("expenses/reports/report_daily_spending.html", {
            'days': days,
            'daily_data': daily_data,
            'cat_links': [cat.html_link() for cat in user_categories],
            'cat_tables': cat_tables
        }, self.request))

    def compute_daily_data(self, all_time_count, all_time_sum, days, days_names, timescales, timescale_names):
        """Compute the “daily data” table."""
        timescale_rows = {num: [name] for num, name in timescale_names.items()}

        for day_count_name in days_names:
            day_count: int = days[day_count_name]
            for num, row in timescale_rows.items():
                current_count = all_time_count * num / day_count
                current_sum = all_time_sum * num / day_count
                row.extend([round(current_count, 2), format_money(current_sum)])

        daily_data = [timescale_rows[timescale] for timescale in timescales]
        all_time_row = [int(all_time_count), format_money(all_time_sum)]
        daily_data.append(
            [_("All time")] + all_time_row + all_time_row
        )

        return daily_data

    def compute_category_data(self, cat_data, user_categories, days, days_names, timescales, timescale_names):
        cat_totals: typing.Dict[int, typing.Union[float, decimal.Decimal]] = {}

        cat_tables_headings = [
            format_html(_("Category spending per expense-day (<var>d<sub>E</sub></var> = {})"), days["expense_days"]),
            format_html(_("Category spending per day (<var>d<sub>A</sub></var> = {})"), days["all_days"]),
        ]
        cat_tables_contents = []

        # Just in case not all categories have expenses
        cat_data_per_id = {cat_id: (cat_count, cat_sum) for cat_id, cat_count, cat_sum in cat_data}
        user_category_ids = [cat.pk for cat in user_categories]

        for day_count_name in days_names:
            day_count: int = days[day_count_name]
            rows = []
            for timescale in timescales:
                row = [timescale_names[timescale]]
                for category in user_category_ids:
                    cat_count, cat_sum = cat_data_per_id.get(category, (0, 0))
                    current_count = cat_count * timescale / day_count
                    current_sum = cat_sum * timescale / day_count
                    row.extend([round(current_count, 2), format_money(current_sum)])
                rows.append(row)
            all_time_row = [_("All time")]
            for category in user_category_ids:
                cat_count, cat_sum = cat_data_per_id.get(category, (0, 0))
                all_time_row.extend([cat_count, format_money(cat_sum)])
            rows.append(all_time_row)
            cat_tables_contents.append(rows)

        cat_tables = zip(cat_tables_headings, cat_tables_contents)

        return cat_tables


def no_results_to_show():
    """Produce an error message when there are no results to show."""
    return format_html('<p class="expenses-empty">{}</p>', _("No results to show."))


AVAILABLE_REPORTS: typing.Dict[str, typing.Type[Report]] = {r.slug: r for r in [
    MonthCategoryBreakdown, VendorStats, DailySpending
]}
