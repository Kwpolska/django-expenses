# Django-Expenses
# Copyright © 2018-2021, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Bill management."""

import time
import typing

from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseNotFound, HttpRequest
from django.shortcuts import render
from django.utils.translation import gettext as _

from expenses.reports import AVAILABLE_REPORTS, Option, OptionGroup, Report


@login_required
def report_list(request: HttpRequest):
    return render(
        request,
        "expenses/report_list.html",
        {
            "htmltitle": _("Reports"),
            "pid": "report_list",
            # work around class attributes not picked up by Django templates
            "reports": [r.meta_to_dict() for r in AVAILABLE_REPORTS.values()],
        },
    )


@login_required
def report_setup(request: HttpRequest, slug: str):
    if slug not in AVAILABLE_REPORTS:
        return HttpResponseNotFound()
    report: typing.Type[Report] = AVAILABLE_REPORTS[slug]

    return render(
        request,
        "expenses/report_setup.html",
        {
            "htmltitle": report.name,
            "pid": "report_setup",
            # work around class attributes not picked up by Django templates
            "report": report.meta_to_dict(),
        },
    )


def get_settings_from_post_data(
    request: HttpRequest, options: typing.List[Option], group: OptionGroup
) -> typing.Dict[Option, typing.Any]:
    values: typing.Dict[Option, typing.Any] = {}
    if group.type == "radio":
        option_id_value = request.POST.get(group.option_id)
        if not option_id_value:
            raise SuspiciousOperation("Invalid request (missing field value)")
        for opt in options:
            if opt.option_id == option_id_value:
                values[opt] = True
    elif group.type == "check":
        for opt in options:
            if opt.option_id in request.POST:
                values[opt] = True
    else:
        for opt in options:
            if opt.option_id in request.POST:
                values[opt] = request.POST[opt.option_id]
            elif opt.type == "text":
                values[opt] = ""
            else:
                values[opt] = False

    # TODO support for date ranges

    return values


@login_required
def report_run(request, slug):
    if slug not in AVAILABLE_REPORTS:
        return HttpResponseNotFound()

    report_class: typing.Type[Report] = AVAILABLE_REPORTS[slug]
    settings: typing.Dict[Option, typing.Any] = {}

    for opt in report_class.options:
        settings.update(get_settings_from_post_data(request, opt.options, opt))

    report: Report = report_class(request, settings)

    postfields: typing.List[(str, str)] = []
    output_format = "html"
    for k, v in request.POST.items():
        if k == "output_format":
            output_format = v
        elif k != "csrfmiddlewaretoken":
            postfields.append((k, v))

    if output_format == "print":
        template = "expenses/report_run_print.html"
    elif output_format == "csv":
        report_csv = report.run_csv()
        return report_csv
    else:
        template = "expenses/report_run.html"

    start_time = time.monotonic()
    report_html = report.run()
    end_time = time.monotonic()

    return render(
        request,
        template,
        {
            "htmltitle": report.name,
            "pid": "report_run",
            "report": report,
            "report_html": report_html,
            "time": end_time - start_time,
            "postfields": postfields,
        },
    )
