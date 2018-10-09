# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

from django.urls import path

import expenses.views.bill
import expenses.views.bill_item
import expenses.views.category
import expenses.views.expense
from expenses import views
from expenses.views import api_autocomplete

app_name = 'expenses'
urlpatterns = [
    path('', views.index, name='index'),

    path('expenses/', expenses.views.expense.expense_list, name='expense_list'),
    path('expenses/add/', expenses.views.expense.expense_add, name='expense_add'),
    path('expenses/<int:pk>/', expenses.views.expense.expense_show, name='expense_show'),
    path('expenses/<int:pk>/edit/', expenses.views.expense.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/convert/', expenses.views.expense.expense_convert, name='expense_convert'),
    path('expenses/<int:pk>/delete/', expenses.views.expense.ExpenseDelete.as_view(), name='expense_delete'),

    path('categories/', expenses.views.category.category_list, name='category_list'),
    path('categories/add/', expenses.views.category.category_add, name='category_add'),
    path('categories/bulk_edit/', expenses.views.category.category_bulk_edit, name='category_bulk_edit'),
    path('categories/<slug:slug>/', expenses.views.category.category_show, name='category_show'),
    path('categories/<slug:slug>/templates', expenses.views.category.category_show_templates, name='category_show_templates'),
    path('categories/<slug:slug>/edit/', expenses.views.category.category_edit, name='category_edit'),
    path('categories/<slug:slug>/delete/', expenses.views.category.category_delete, name='category_delete'),

    path('templates/', views.template_list, name='template_list'),
    path('templates/add/', views.vni, name='template_add'),
    path('templates/<int:pk>/', views.vni, name='template_run'),
    path('templates/<int:pk>/edit/', views.vni, name='template_edit'),
    path('templates/<int:pk>/delete/', views.vni, name='template_delete'),

    path('bills/', expenses.views.bill.bill_list, name='bill_list'),
    path('bills/add/', expenses.views.bill.bill_add, name='bill_add'),
    path('bills/<int:pk>/', expenses.views.bill.bill_show, name='bill_show'),
    path('bills/<int:pk>/add_item/', expenses.views.bill_item.bill_item_add, name='bill_item_add'),
    path('bills/<int:pk>/editmeta/', expenses.views.bill.bill_editmeta, name='bill_editmeta'),
    path('bills/<int:pk>/convert/', expenses.views.expense.expense_convert, name='bill_convert'),
    path('bills/<int:pk>/delete/', expenses.views.bill.BillDelete.as_view(), name='bill_delete'),
    path('bills/<int:bill_pk>/item/<int:item_pk>/', expenses.views.bill_item.bill_item_edit, name='bill_item_edit'),
    path('bills/<int:bill_pk>/item/<int:item_pk>/delete/', expenses.views.bill_item.bill_item_delete, name='bill_item_delete'),

    path('api/autocomplete/expense/vendor/', api_autocomplete.expense_vendor, name='api_autocomplete__expense_vendor'),
    path('api/autocomplete/expense/description/', api_autocomplete.expense_description, name='api_autocomplete__expense_description'),
    path('api/autocomplete/bill/vendor/', api_autocomplete.bill_vendor, name='api_autocomplete__bill_vendor'),
    path('api/autocomplete/bill/item/', api_autocomplete.bill_item, name='api_autocomplete__bill_item'),
]
