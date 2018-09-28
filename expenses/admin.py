# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

from django.contrib import admin
from django.contrib.admin import ModelAdmin

from expenses import models

# Register your models here.

admin.site.register([models.Category, models.BillItem, models.Expense,
                     models.ExpenseTemplate, models.BillItemTemplate], ModelAdmin)

