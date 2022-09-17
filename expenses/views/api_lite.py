# Django-Expenses
# Copyright © 2018-2022, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""The lightweight API."""

import django.contrib.auth.models
import json
import typing

from django.http import HttpRequest, HttpResponse, JsonResponse
from expenses.models import ApiKey, Category, Expense

BEARER_STRING = "bearer "
BEARER_PREFIX = len(BEARER_STRING)


def get_user(request: HttpRequest) -> typing.Optional[django.contrib.auth.models.User]:
    auth_header: typing.Optional[str] = request.headers.get("Authorization")
    if auth_header is None or not auth_header.lower().startswith(BEARER_STRING):
        return None

    key = auth_header[BEARER_PREFIX:]
    try:
        return ApiKey.objects.get(key=key).user
    except ApiKey.DoesNotExist:
        return None


def get_categories(request: HttpRequest) -> HttpResponse:
    """Get a list of categories and their IDs."""
    user = get_user(request)
    if user is None:
        return HttpResponse(status=401)

    results = Category.objects.filter(user=user).values("id", "name")
    return JsonResponse(
        {"results": list(results)},
        json_dumps_params={"ensure_ascii": False})


def quick_add_expense(request: HttpRequest) -> HttpResponse:
    """Add a new expense."""
    user = get_user(request)
    if user is None:
        return HttpResponse(status=401)

    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        body: dict = json.loads(request.body)
    except json.decoder.JSONDecodeError:
        return HttpResponse(status=400)
    try:
        category_id = body["category"]
        category = Category.objects.get(user=user, pk=category_id)

        date = body["date"]
        vendor = body["vendor"]
        amount = body["amount"]
        description = body["description"]
    except (KeyError, Category.DoesNotExist):
        return HttpResponse(status=400)

    expense = Expense(
        date=date,
        vendor=vendor,
        category=category,
        amount=amount,
        description=description,
        is_bill=False,
        user=user
    )
    expense.save()
    return HttpResponse(status=200)
