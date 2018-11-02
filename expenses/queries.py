# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Standard queries."""

from expenses.models import Category


def cat_objs(request):
    """Get ordered category objects for a user."""
    return Category.objects.filter(user=request.user).order_by('order')
