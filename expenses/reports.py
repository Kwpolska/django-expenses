# Django-Expenses
# Copyright © 2018-2021, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Report support framework."""
import abc
import csv
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
from django.conf import settings
from django.db import connection
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.safestring import SafeString
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _
from expenses.models import Category
from expenses.utils import format_money, format_number, get_babel_locale, peek, today_date


class Engine(enum.Enum):
    SQLITE3 = "django.db.backends.sqlite3"
    POSTGRESQL = "django.db.backends.postgresql_psycopg2"
    ANY_ENGINE = ""

    @classmethod
    def get_from_connection(cls, connection) -> "Engine":
        return cls(connection.settings_dict["ENGINE"])


@attr.s(auto_attribs=True, frozen=True)
class Option:
    name: str
    option_id: str
    type: str = attr.ib("", init=False, repr=False)


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

    default: bool = False
    type: str = "radio"


@attr.s(auto_attribs=True, frozen=True)
class TextFieldOption(Option):
    """A text field option, which can have an enabler checkbox attached."""

    required: bool = True
    enabler: typing.Optional[str] = None
    enabled_by_default: bool = True
    type: str = attr.ib("text", init=False, repr=False)


class ReportItemFormatter:
    def format_money(self, amount: typing.Union[int, float, decimal.Decimal]) -> str:
        return format_money(amount)

    def format_category(self, c: Category) -> str:
        return str(c)

    def format_vendor_link(self, vendor: str) -> str:
        return vendor


class CsvFormatter(ReportItemFormatter):
    """"Subclass for csv items formatting"""

    def format_money(self, amount: typing.Union[int, float, decimal.Decimal]) -> str:
        return format_number(amount, 2)


class HtmlFormatter(ReportItemFormatter):
    """"Subclass for html items formatting"""

    def format_category(self, c: Category) -> str:
        return c.html_link()

    def format_vendor_link(self, vendor: str) -> str:
        url = (
            reverse("expenses:search")
            + "?for=expenses&include=expenses&include=bills&category_all=true&q="
            + urllib.parse.quote_plus(vendor)
        )
        vendor_link = format_html('<a href="{}">{}</a>', url, vendor)
        return vendor_link


class Report(metaclass=abc.ABCMeta):
    name: str = None
    slug: str = None
    description: str = None
    request: django.http.HttpRequest = None
    options: typing.List[Option] = []
    settings: typing.Dict[Option, typing.Union[str, bool]] = {}

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

    def get_column_headers(self, engine: Engine, is_html=True) -> (typing.List[str], typing.List[str]):
        return self.column_headers

    def preprocess_rows(self, results: typing.Iterable, is_html=True) -> typing.Iterable:
        return results

    def tabulate(self, results: typing.Iterable, engine: Engine) -> SafeString:
        column_headers: (typing.List[str], typing.List[str]) = self.get_column_headers(engine)
        column_header_names, column_alignment = column_headers
        column_headers_with_alignment = zip(*column_headers)

        first_row, results = peek(self.preprocess_rows(results))

        if not results:
            return no_results_to_show()

        if len(column_header_names) != len(first_row):
            raise ValueError("Results do not match expected column headers")
        results_with_alignment = (zip(row, column_alignment) for row in results)

        return mark_safe(
            render_to_string(
                "expenses/reports/report_basic_table.html",
                {
                    "results_with_alignment": results_with_alignment,
                    "column_headers_with_alignment": column_headers_with_alignment,
                },
                self.request,
            )
        )

    def create_file(self, results: typing.Iterable, engine: Engine) -> HttpResponse:
        column_headers: (typing.List[str], typing.List[str]) = self.get_column_headers(engine, False)
        column_header_names = column_headers[0]

        first_row, results = peek(self.preprocess_rows(results, False))

        response = HttpResponse(content_type="text/csv")
        filename = f'{self.slug}-report-{today_date().strftime("%Y-%m-%d")}.csv'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write("\ufeff".encode("utf8"))
        writer = csv.writer(response, delimiter=settings.EXPENSES_CSV_DELIMITER)
        writer.writerow(column_header_names)

        for row in results:
            writer.writerow(row)

        if not results:
            return no_results_to_show()

        if len(column_header_names) != len(first_row):
            raise ValueError("Results do not match expected column headers")
        return response

    def run_csv(self) -> HttpResponse:
        engine: Engine = Engine.get_from_connection(connection)
        sql: str = self.get_query(self.query_type, engine)

        with connection.cursor() as cursor:
            results: typing.Iterable = self.query(cursor, sql)
        return self.create_file(results, engine)

    def run(self) -> SafeString:
        engine: Engine = Engine.get_from_connection(connection)
        sql: str = self.get_query(self.query_type, engine)

        with connection.cursor() as cursor:
            results: typing.Iterable = self.query(cursor, sql)
        return self.tabulate(results, engine)


def format_yearmonth(yearmonth: str) -> str:
    """Format a year-month pair as a locale-dependent string."""
    # Querying for yearmonth is easier (especially with sqlite3) and about the same speed,
    # even if we need to apply some more logic Python-side to make it look nice.
    year, month = map(int, yearmonth.split("-"))
    return format_skeleton("yMMMM", datetime.date(year, month, 1), locale=get_babel_locale())


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
            """,
        },
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
            """,
        },
        "category": {
            Engine.ANY_ENGINE: """
            SELECT category_id, SUM(amount)
            FROM expenses_expense, expenses_category
            WHERE expenses_expense.user_id = %s AND category_id = expenses_category.id
            GROUP BY category_id, "expenses_category"."order"
            ORDER BY "expenses_category"."order", category_id;
        """
        },
    }
    options = [
        OptionGroup(
            _("Break down expenses by:"),
            "breakdown",
            [
                CheckOption(_("Month and category"), "month_category"),
                CheckOption(_("Month"), "month"),
                CheckOption(_("Category"), "category"),
            ],
        )
    ]

    def __init__(self, request, settings: typing.Dict[CheckOption, typing.Any]):
        super().__init__(request, settings)
        # Only selected options will be in settings
        if settings:
            self.query_type = next(iter(settings)).option_id
        else:
            raise ValueError("Query type unknown")

    def get_column_headers(self, engine: Engine, is_html=True) -> (typing.List[str], typing.List[str]):
        item_formatter = HtmlFormatter() if is_html else CsvFormatter()
        if self.query_type == "month_category":
            user_categories: typing.Iterable[Category] = Category.user_objects(self.request)
            names = [_("Month")] + [item_formatter.format_category(c) for c in user_categories] + [_("Total")]
            return names, ["right"] * len(names)
        elif self.query_type == "category":
            return ([_("Category"), _("Total")], ["left", "right"])
        elif self.query_type == "month":
            return ([_("Month"), _("Total")], ["right", "right"])

    def preprocess_rows(self, results: typing.Iterable, is_html=True) -> typing.Iterable:
        item_formatter = HtmlFormatter() if is_html else CsvFormatter()
        if self.query_type == "month_category":
            user_categories: typing.Iterable[Category] = Category.user_objects(self.request)
            user_category_ids: typing.Dict[int, int] = {}
            cat_totals: typing.Dict[int, typing.Union[float, decimal.Decimal]] = {}
            for n, cat in enumerate(user_categories, 1):
                user_category_ids[cat.pk] = n
                cat_totals[cat.pk] = 0
            cat_count = len(user_category_ids)
            for yearmonth, items in itertools.groupby(results, operator.itemgetter(0)):
                row = [format_yearmonth(yearmonth)] + [item_formatter.format_money(0)] * cat_count
                row_total = 0
                for _ym, category_id, value in items:
                    row[user_category_ids[category_id]] = item_formatter.format_money(value)
                    row_total += value
                    cat_totals[category_id] += value
                row.append(item_formatter.format_money(row_total))
                yield row

            cat_totals_values = list(cat_totals.values())
            yield [_("Grand Total")] + [item_formatter.format_money(i) for i in cat_totals_values] + [
                item_formatter.format_money(sum(cat_totals_values))
            ]

        elif self.query_type == "month":
            total = 0
            for yearmonth, value in results:
                yield format_yearmonth(yearmonth), item_formatter.format_money(value)
                total += value

            yield _("Grand Total"), item_formatter.format_money(total)
        else:
            # category
            user_categories: typing.Dict[int, Category] = {c.pk: c for c in Category.user_objects(self.request)}
            total = 0
            for category, value in results:
                yield (
                    item_formatter.format_category(user_categories[category]),
                    item_formatter.format_money(value),
                )
                total += value

            yield _("Grand Total"), item_formatter.format_money(total)


class VendorStats(SimpleSQLReport):
    name = _("Vendor statistics")
    slug = "vendor_stats"
    description = _(
        "Get basic statistics about money spent at each vendor. Includes vendors with at least 2 separate purchases."
    )
    query_type = "vendor_stats"

    sql = {
        "vendor_stats": {
            Engine.ANY_ENGINE: """
        SELECT vendor, COUNT(*) AS count, SUM(amount) AS sum, AVG(amount) AS avg
        FROM expenses_expense
        WHERE user_id = %s GROUP BY vendor HAVING COUNT(*) > 1
        ORDER BY sum DESC, vendor;
        """
        }
    }

    def get_column_headers(self, engine: Engine, is_html=True) -> (typing.List[str], typing.List[str]):
        return [_("Vendor"), _("Count"), _("Sum"), _("Average")], ["left", "right", "right", "right"]

    def preprocess_rows(self, results: typing.Iterable, is_html=True) -> typing.Iterable:
        total_count = 0
        total_amount = 0
        item_formatter = HtmlFormatter() if is_html else CsvFormatter()

        for vendor, count, amount, avg in results:
            vendor_link = item_formatter.format_vendor_link(vendor)
            total_count += count
            total_amount += amount
            yield vendor_link, count, item_formatter.format_money(amount), item_formatter.format_money(avg)

        if total_count > 0:
            yield _("Grand Total"), total_count, item_formatter.format_money(total_amount), item_formatter.format_money(
                total_amount / total_count
            )


class DailySpending(SimpleSQLReport):
    name = _("Daily spending")
    slug = "daily_spending"
    description = _("Get daily, weekly, monthly average spending.")
    sql = {
        "data": {
            Engine.ANY_ENGINE: """
        SELECT category_id, COUNT(amount), SUM(amount)
        FROM expenses_expense, expenses_category
        WHERE expenses_expense.user_id = %s AND category_id = expenses_category.id
        GROUP BY category_id, "expenses_category"."order"
        ORDER BY "expenses_category"."order", category_id;
        """
        },
        "day_counts": {
            Engine.SQLITE3: "SELECT COUNT(DISTINCT date), MAX(julianday(date)) - MIN(julianday(date)) FROM expenses_expense WHERE user_id=%s;",
            Engine.POSTGRESQL: "SELECT COUNT(DISTINCT date), MAX(date) - MIN(date) FROM expenses_expense WHERE user_id=%s;",
        },
    }

    def preprocess(self, is_html=True):
        engine: Engine = Engine.get_from_connection(connection)

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
            365: _("Per year (365 days)"),
        }

        all_time_count = all_time_sum = 0
        for _cat, at_cat_count, at_cat_sum in cat_data:
            all_time_count += at_cat_count
            all_time_sum += at_cat_sum

        daily_data = self.compute_daily_data(
            all_time_count, all_time_sum, days, days_names, timescales, timescale_names
        )
        cat_tables = self.compute_category_data(
            cat_data, user_categories, days, days_names, timescales, timescale_names, is_html
        )

        return days, daily_data, user_categories, cat_tables

    def run(self):
        days, daily_data, user_categories, cat_tables = self.preprocess()

        return mark_safe(
            render_to_string(
                "expenses/reports/report_daily_spending.html",
                {
                    "days": days,
                    "daily_data": daily_data,
                    "cat_links": [cat.html_link() for cat in user_categories],
                    "cat_tables": cat_tables,
                },
                self.request,
            )
        )

    def run_csv(self):

        days, daily_data, user_categories, cat_tables = self.preprocess(False)

        response = HttpResponse(content_type="text/csv")
        filename = f'{self.slug}-report-{today_date().strftime("%Y-%m-%d")}.csv'
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write("\ufeff".encode("utf8"))
        writer = csv.writer(response)

        property_row = []
        timescale_row = []
        timescale_headers: typing.Iterable[str] = [
            f"Na dE = {days['expense_days']} dni",
            f"Na dA = {days['all_days']} dzień",
        ]
        for timescale in timescale_headers:
            timescale_row.append(timescale)
            property_row.append(_("Count"))
            timescale_row.append(timescale)
            property_row.append(_("Amount"))
        timescale_row.insert(0, _("Time scale"))
        property_row.insert(0, _("Property"))

        writer.writerow(timescale_row)
        writer.writerow(property_row)

        for row in daily_data:
            writer.writerow(row)

        for title, results in cat_tables:
            writer.writerow([])
            writer.writerow([title])
            cat_links = []
            property_row = []
            for cat in user_categories:
                cat_links.append(cat.__str__())
                property_row.append(_("Count"))
                cat_links.append(cat.__str__())
                property_row.append(_("Amount"))
            property_row.insert(0, _("Property"))
            cat_links.insert(0, _("Category"))
            writer.writerow(cat_links)
            writer.writerow(property_row)

            for row in results:
                writer.writerow(row)

        return response

    def compute_daily_data(
        self,
        all_time_count,
        all_time_sum,
        days,
        days_names,
        timescales,
        timescale_names,
    ):
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
        daily_data.append([_("All time")] + all_time_row + all_time_row)

        return daily_data

    def compute_category_data(
        self, cat_data, user_categories, days, days_names, timescales, timescale_names, is_html=True
    ):
        cat_totals: typing.Dict[int, typing.Union[float, decimal.Decimal]] = {}

        if is_html:
            cat_tables_headings = [
                format_html(
                    _("Category spending per expense-day (<var>d<sub>E</sub></var> = {})"), days["expense_days"]
                ),
                format_html(_("Category spending per day (<var>d<sub>A</sub></var> = {})"), days["all_days"]),
            ]
        else:
            cat_tables_headings = [
                f"{_('Category spending per expense-day dE =')} {days['expense_days']}",
                f"{_('Category spending per day dA =')} {days['all_days']}",
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


class ProductPriceHistory(SimpleSQLReport):
    name = _("Product price history")
    slug = "product_price_history"
    description = _("Get price history for a product.")
    column_headers = (
        [
            _("Vendor"),
            _("Product"),
            _("Date"),
            _("Serving"),
            _("Serving Unit"),
            _("Count"),
            _("Unit Price"),
            _("Price per Serving Unit"),
            _("Difference"),
        ],
        ["left", "left", "left", "right", "right", "right", "right", "right", "right"],
    )
    column_names = [
        "vendor",
        "product",
        "date",
        "serving",
        "pricing_unit",
        "count",
        "unit_price",
        "price_per_unit",
        "diff",
    ]
    options = [
        OptionGroup(
            _("Customize data included in report"),
            "product_box",
            [
                TextFieldOption(_("Product name"), "product", False),
                TextFieldOption(_("Vendor"), "vendor", False),
                CheckOption(_("Separate history for each product name"), "partition_product", True, type="check"),
                CheckOption(_("Separate history for each vendor"), "partition_vendor", True, type="check"),
                CheckOption(_("Fuzzy search"), "fuzzy_search", False, type="check"),
                # TODO more filtering options
            ],
            type="text",
        )
    ]
    query_type = "product_price_history"
    sql = {
        "product_price_history": {
            Engine.SQLITE3: """
        SELECT vendor, product, date, serving, pricing_unit, count, unit_price, price_per_unit, price_per_unit - lag(price_per_unit) OVER ({partition_clause}) AS diff
        FROM (
            SELECT vendor, product, date, expenses_billitem.date_added, serving, count, unit_price,
            CASE WHEN serving = 0 THEN unit_price
                 WHEN serving < 20 THEN round(unit_price / serving, 4)
                 ELSE round(unit_price * 100 / serving, 4)
            END AS price_per_unit,
            CASE WHEN serving = 0 THEN NULL
                 WHEN serving < 20 THEN 1
                 ELSE 100
            END AS pricing_unit
            FROM expenses_billitem
            JOIN expenses_expense ON expenses_expense.id = expenses_billitem.bill_id
            WHERE expenses_billitem.user_id = %s {filter_options}
        ) sq
        ORDER BY {order_clause};
        """,
            Engine.POSTGRESQL: """
            SELECT vendor, product, date, serving, pricing_unit, count, unit_price, price_per_unit, price_per_unit - lag(price_per_unit) OVER ({partition_clause}) AS diff
            FROM (
                SELECT vendor, product, date, expenses_billitem.date_added, serving, count, unit_price,
                CASE WHEN serving = 0 THEN unit_price
                     WHEN serving < 20 THEN (unit_price / serving)::numeric(10, 4)
                     ELSE (unit_price * 100 / serving)::numeric(10, 4)
                END AS price_per_unit,
                CASE WHEN serving = 0 THEN NULL
                     WHEN serving < 20 THEN 1
                     ELSE 100
                END AS pricing_unit
                FROM expenses_billitem
                JOIN expenses_expense ON expenses_expense.id = expenses_billitem.bill_id
                WHERE expenses_billitem.user_id = %s {filter_options}
            ) sq
            ORDER BY {order_clause};
            """,
        }
    }

    def query(self, cursor, sql: str) -> typing.Iterable:
        filter_options = ""
        sql_params = [self.request.user.id]

        product = self.settings.get(self.options[0][0], "")
        vendor = self.settings.get(self.options[0][1], "")
        partition_product = self.settings.get(self.options[0][2], False)
        partition_vendor = self.settings.get(self.options[0][3], False)
        fuzzy_search = self.settings.get(self.options[0][4], False)

        if Engine.get_from_connection(connection) == Engine.POSTGRESQL:
            # We always use ILIKE for case insensitvity, but not always provide %% for fuzzy search
            product_fs = "%" + product + "%" if fuzzy_search else product
            vendor_fs = "%" + vendor + "%" if fuzzy_search else vendor

            if product:
                filter_options += " AND product ILIKE %s"
                sql_params.append(product_fs)
            if vendor:
                filter_options += " AND vendor ILIKE %s"
                sql_params.append(vendor_fs)
        else:
            product_fs = "%" + product.lower() + "%" if fuzzy_search else product.lower()
            vendor_fs = "%" + vendor.lower() + "%" if fuzzy_search else vendor.lower()

            if product:
                filter_options += " AND LOWER(product) {} %s".format("LIKE" if fuzzy_search else "=")
                sql_params.append(product_fs)
            if vendor:
                filter_options += " AND LOWER(vendor) {} %s".format("LIKE" if fuzzy_search else "=")
                sql_params.append(vendor_fs)

        if partition_vendor and partition_product:
            order_clause = "vendor, product, date"
            partition_clause = "PARTITION BY vendor, product ORDER BY date, date_added"
        elif partition_vendor:
            order_clause = "vendor, product, date"
            partition_clause = "PARTITION BY vendor ORDER BY date, date_added, product"
        elif partition_product:
            order_clause = "product, date, vendor"
            partition_clause = "PARTITION BY product ORDER BY date, date_added, vendor"
        else:
            order_clause = "date, vendor, product"
            partition_clause = "ORDER BY date, date_added, vendor, product"
        sql_full = sql.format(
            filter_options=filter_options, order_clause=order_clause, partition_clause=partition_clause
        )
        cursor.execute(sql_full, sql_params)
        return cursor.fetchall()

    def tabulate(self, results: typing.Iterable, engine: Engine) -> SafeString:
        column_headers: (typing.List[str], typing.List[str]) = self.get_column_headers(engine)
        column_header_names, column_alignment = column_headers
        column_headers_with_alignment = list(zip(*column_headers))

        if not results:
            return no_results_to_show()

        main_groups = {(row[0], row[1]) for row in results}
        vendor_groups = {row[0] for row in main_groups}
        product_groups = {row[1] for row in main_groups}

        partition_product = self.settings.get(self.options[0][2], False)
        partition_vendor = self.settings.get(self.options[0][3], False)

        if partition_vendor and partition_product and len(vendor_groups) > 1 and len(product_groups) > 1:
            group_title = _("{1} — {0}")
        elif partition_vendor and len(vendor_groups) > 1:
            group_title = _("{0}")
        elif partition_product and len(product_groups) > 1:
            group_title = _("{1}")
        else:
            group_title = ""

        if partition_vendor and partition_product:
            grouper = lambda row: (row[0], row[1])
        elif partition_vendor:
            grouper = lambda row: row[0]
        elif partition_product:
            grouper = lambda row: row[1]
        else:
            grouper = lambda row: True

        first_row, results = peek(results)
        if len(column_header_names) != len(first_row):
            raise ValueError("Results do not match expected column headers")

        current_group = None
        results_grouped = []

        for row in results:
            group = grouper(row)
            row = list(row)
            if group != current_group:
                results_grouped.append({"title": group_title.format(*row), "rows": []})
                current_group = group

            results_grouped[-1]["rows"].append({k: v for k, v in zip(self.column_names, row)})

        return mark_safe(
            render_to_string(
                "expenses/reports/report_product_price_history.html",
                {
                    "results_grouped": results_grouped,
                    "column_headers_with_alignment": column_headers_with_alignment,
                    "show_group_title": bool(group_title),
                },
                self.request,
            )
        )


def no_results_to_show():
    """Produce an error message when there are no results to show."""
    return format_html('<p class="expenses-empty">{}</p>', _("No results to show."))


AVAILABLE_REPORTS: typing.Dict[str, typing.Type[Report]] = {
    r.slug: r for r in [MonthCategoryBreakdown, VendorStats, DailySpending, ProductPriceHistory]
}
