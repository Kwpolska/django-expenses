# Django-Expenses
# Copyright © 2018-2023, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Expense search."""
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import connection
from django.shortcuts import render
from django.utils.translation import gettext as _

from expenses.models import Expense, BillItem, Category
from expenses.utils import dict_overwrite, revchron


class RawQueryWithSlicing:
    COUNT_QUERY = "COUNT(*)"

    def __init__(self, sql, args, selected_fields, order_clause):
        self.sql = sql
        self.args = args
        self.selected_fields = selected_fields
        self.order_clause = order_clause

    def run(self, count=False, limit=""):
        with connection.cursor() as cursor:
            if count:
                q = self.sql.format(selected_fields=self.COUNT_QUERY, limit_clause=limit, order_clause="")
                cursor.execute(q, self.args)
                return cursor.fetchone()
            else:
                q = self.sql.format(
                    selected_fields=self.selected_fields, limit_clause=limit, order_clause=self.order_clause
                )
                cursor.execute(q, self.args)
                return cursor.fetchall()

    def count(self):
        return self.run(count=True)[0]

    def __len__(self):
        return self.run(count=True)[0]

    def __getitem__(self, item):
        limit = ""
        if isinstance(item, slice):
            if item.start and item.stop:
                limit = "LIMIT {} OFFSET {}".format(item.stop - item.start, item.start)
            elif item.start:
                limit = "LIMIT {} OFFSET {}".format(self.count() - item.start, item.start)
            elif item.stop:
                limit = "LIMIT {}".format(item.stop)
        else:
            limit = "LIMIT 1 OFFSET {}".format(item)

        found = self.run(count=False, limit=limit)
        if isinstance(item, slice) and item.step:
            return found[:: item.step]
        else:
            return found


@login_required
def search(request):
    opt = {"q": "", "vendor": "", "search_for": "purchases", "date_spec": "any", "date_start": "", "date_end": ""}
    categories = Category.user_objects(request)
    if "q" in request.GET or "vendor" in request.GET:
        opt["has_query"] = True
        # Set search options (will be copied into template)
        dict_overwrite(opt, "q", request.GET)
        dict_overwrite(opt, "vendor", request.GET)
        dict_overwrite(opt, "search_for", request.GET, "for")
        dict_overwrite(opt, "date_spec", request.GET, "date-spec")
        dict_overwrite(opt, "date_start", request.GET, "date-start")
        dict_overwrite(opt, "date_end", request.GET, "date-end")

        includes = request.GET.getlist("include", [])
        opt["include_expenses"] = "expenses" in includes
        opt["include_bills"] = "bills" in includes

        if request.GET.get("category_all"):
            cat_pks = {cat.pk for cat in categories}
        else:
            cat_pks = {int(i) for i in request.GET.getlist("category", [])}
        categories_with_status = [(c, c.pk in cat_pks) for c in categories]

        # Do the search
        if opt["search_for"] == "expenses":
            items = Expense.objects.filter(user=request.user, category__in=cat_pks).select_related("category")
            if opt["q"]:
                items = items.filter(description_cache__icontains=opt["q"])
            if opt["vendor"]:
                items = items.filter(vendor__icontains=opt["vendor"])

            if opt["include_expenses"] and opt["include_bills"]:
                pass
            elif opt["include_expenses"]:
                items = items.filter(is_bill=False)
            elif opt["include_bills"]:
                items = items.filter(is_bill=True)

            if opt["date_start"] and not opt["date_end"]:
                items = items.filter(date__gte=opt["date_start"])
            elif opt["date_start"] and opt["date_end"]:
                items = items.filter(date__gte=opt["date_start"], date__lte=opt["date_end"])

            items = revchron(items)
        elif opt["search_for"] == "billitems":
            items = BillItem.objects.filter(user=request.user, bill__category__in=cat_pks).select_related("bill")
            if opt["q"]:
                items = items.filter(product__icontains=opt["q"])
            if opt["vendor"]:
                items = items.filter(bill__vendor__icontains=opt["vendor"])

            if opt["date_start"] and not opt["date_end"]:
                items = items.filter(bill__date__gte=opt["date_start"])
            elif opt["date_start"] and opt["date_end"]:
                items = items.filter(bill__date__gte=opt["date_start"], bill__date__lte=opt["date_end"])

            items = items.order_by("-date_added")
        elif opt["search_for"] == "purchases":
            cat_pks = {int(i) for i in request.GET.getlist("category", [])}

            if opt["date_start"] and not opt["date_end"]:
                date_clause = "AND d.date >= %s"
                date_args = [opt["date_start"]]
            elif opt["date_start"] and opt["date_end"]:
                date_clause = "AND d.date BETWEEN %s AND %s"
                date_args = [opt["date_start"], opt["date_end"]]
            else:
                date_clause = ""
                date_args = []

            ilike_word = "LIKE" if connection.settings_dict["ENGINE"] == "django.db.backends.sqlite3" else "ILIKE"

            query_clause = ""
            query_args = []
            if opt["q"]:
                query_clause += " AND d.product " + ilike_word + " %s"
                query_args.append("%" + opt["q"] + "%")
            if opt["vendor"]:
                query_clause += " AND d.vendor " + ilike_word + " %s"
                query_args.append("%" + opt["vendor"] + "%")

            items = RawQueryWithSlicing(
                """
                SELECT {{selected_fields}} FROM (
                    SELECT date, vendor, description AS product, amount AS unit_price, category_id, date_added
                    FROM expenses_expense WHERE is_bill = false AND user_id = %s
                UNION
                    SELECT date, vendor, product, unit_price, category_id, expenses_billitem.date_added
                    FROM expenses_billitem
                    LEFT JOIN expenses_expense ON expenses_billitem.bill_id = expenses_expense.id
                    WHERE expenses_billitem.user_id = %s
                ) AS d
                WHERE d.category_id in ({cat_pks}) {date_clause}{query_clause}
                {{order_clause}} {{limit_clause}};""".format(
                    cat_pks=", ".join(str(i) for i in cat_pks), date_clause=date_clause, query_clause=query_clause
                ),
                [request.user.pk, request.user.pk] + date_args + query_args,
                "d.date, d.vendor, d.product, d.unit_price",
                "ORDER BY d.date DESC, d.date_added DESC",
            )
        else:
            raise Exception("Unknown search type")
    else:
        opt["include_expenses"] = True
        opt["include_bills"] = True
        opt["has_query"] = False
        categories_with_status = [(c, True) for c in categories]
        items = None

    context = {"htmltitle": _("Search"), "pid": "search", "categories_with_status": categories_with_status}
    context.update(opt)
    if items is not None:
        paginator = Paginator(items, settings.EXPENSES_PAGE_SIZE)
        page = request.GET.get("page", "1")
        context["items"] = paginator.get_page(page)
    return render(request, "expenses/search.html", context)
