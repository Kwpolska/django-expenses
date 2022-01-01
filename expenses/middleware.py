# Django-Expenses
# Copyright © 2018-2022, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

from django.utils import translation


class ForcePolishLanguageMiddleware:
    """Force Expenses language to be Polish, independently of the site-wide language."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.resolver_match.app_name == "expenses":
            translation.activate("pl")
            request.LANGUAGE_CODE = translation.get_language()
        return view_func(request, *view_args, **view_kwargs)
