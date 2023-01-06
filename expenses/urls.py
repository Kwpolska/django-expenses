# Django-Expenses
# Copyright © 2018-2023, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

from django.urls import path
from django.views.decorators.cache import cache_page
from django.views.i18n import JavaScriptCatalog

import expenses.views.bill
import expenses.views.bill_item
import expenses.views.category
import expenses.views.expense
import expenses.views.reports
import expenses.views.search
import expenses.views.template
import expenses.views.api_autocomplete
import expenses.views.api_lite

from expenses import views

from django.conf import settings

app_name = "expenses"
urlpatterns = [
    path("", views.index, name="index"),
    path(
        "jsi18n/",
        cache_page(86400, key_prefix="jsi18n")(JavaScriptCatalog.as_view(packages=["expenses"])),
        name="javascript-catalog",
    ),
    path("search/", expenses.views.search.search, name="search"),
    path("expenses/", views.expense.expense_list, name="expense_list"),
    path("expenses/add/", views.expense.expense_add, name="expense_add"),
    path("expenses/<int:pk>/", views.expense.expense_show, name="expense_show"),
    path("expenses/<int:pk>/edit/", views.expense.expense_edit, name="expense_edit"),
    path("expenses/<int:pk>/convert/", views.expense.expense_convert, name="expense_convert"),
    path("expenses/<int:pk>/repeat/", views.expense.expense_repeat, name="expense_repeat"),
    path("expenses/<int:pk>/delete/", views.expense.ExpenseDelete.as_view(), name="expense_delete"),
    path("categories/", views.category.category_list, name="category_list"),
    path("categories/add/", views.category.category_add, name="category_add"),
    path("categories/bulk_edit/", views.category.category_bulk_edit, name="category_bulk_edit"),
    path("categories/<slug:slug>/", views.category.category_show, name="category_show"),
    path("categories/<slug:slug>/templates/", views.category.category_show_templates, name="category_show_templates"),
    path("categories/<slug:slug>/edit/", views.category.category_edit, name="category_edit"),
    path("categories/<slug:slug>/delete/", views.category.category_delete, name="category_delete"),
    path("templates/", views.template.template_list, name="template_list"),
    path("templates/add/", views.template.template_add, name="template_add"),
    path("templates/<int:pk>/", views.template.template_show, name="template_show"),
    path("templates/<int:pk>/run/", views.template.template_run, name="template_run"),
    path("templates/<int:pk>/edit/", views.template.template_edit, name="template_edit"),
    path("templates/<int:pk>/delete/", views.template.TemplateDelete.as_view(), name="template_delete"),
    path("bills/", views.bill.bill_list, name="bill_list"),
    path("bills/add/", views.bill.bill_add, name="bill_add"),
    path("bills/quickadd/", views.bill.bill_quickadd, name="bill_quickadd"),
    path("bills/<int:pk>/", views.bill.bill_show, name="bill_show"),
    path("bills/<int:pk>/add_item/", views.bill_item.bill_item_add, name="bill_item_add"),
    path("bills/<int:pk>/editmeta/", views.bill.bill_editmeta, name="bill_editmeta"),
    path("bills/<int:pk>/convert/", views.expense.expense_convert, name="bill_convert"),
    path("bills/<int:pk>/delete/", views.bill.BillDelete.as_view(), name="bill_delete"),
    path("bills/<int:bill_pk>/item/<int:item_pk>/", views.bill_item.bill_item_edit, name="bill_item_edit"),
    path("bills/<int:bill_pk>/item/<int:item_pk>/delete/", views.bill_item.bill_item_delete, name="bill_item_delete"),
    path("reports/", views.reports.report_list, name="report_list"),
    path("reports/<slug:slug>/", views.reports.report_setup, name="report_setup"),
    path("reports/<slug:slug>/run/", views.reports.report_run, name="report_run"),
    path(
        "api/autocomplete/expense/vendor/",
        views.api_autocomplete.expense_vendor,
        name="api_autocomplete__expense_vendor",
    ),
    path(
        "api/autocomplete/expense/description/",
        views.api_autocomplete.expense_description,
        name="api_autocomplete__expense_description",
    ),
    path("api/autocomplete/bill/vendor/", views.api_autocomplete.bill_vendor, name="api_autocomplete__bill_vendor"),
    path("api/autocomplete/bill/item/", views.api_autocomplete.bill_item, name="api_autocomplete__bill_item"),
    path("api/lite/categories/", views.api_lite.get_categories, name="api_lite__categories"),
    path("api/lite/expenses/", views.api_lite.quick_add_expense, name="api_lite__expenses"),
]

if settings.EXPENSES_SYNC_API_ENABLED:
    import expenses.views.api_sync
    urlpatterns += [
        path("api/sync/hello/", views.api_sync.hello, name="api_sync__hello"),
        path("api/sync/profile/", views.api_sync.profile, name="api_sync__profile"),
        path("api/sync/run/", views.api_sync.RunEndpoint.as_view(), name="api_sync__run"),
        path("api/sync/category/add/", views.api_sync.CategoryAddEndpoint.as_view(), name="api_sync__category_add"),
        path("api/sync/category/edit/", views.api_sync.CategoryEditEndpoint.as_view(), name="api_sync__category_edit"),
        path(
            "api/sync/category/delete/", views.api_sync.CategoryDeleteEndpoint.as_view(), name="api_sync__category_delete"
        ),
    ]
