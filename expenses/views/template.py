"""Template views."""
import decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _

from expenses.forms import TemplateForm
from expenses.models import ExpenseTemplate, Expense
from expenses.utils import today_date, round_money, parse_amount_input
from expenses.views import ExpDeleteView


@login_required
def template_list(request):
    paginator = Paginator(
        ExpenseTemplate.objects.filter(user=request.user).order_by("name"), settings.EXPENSES_PAGE_SIZE
    )
    page = request.GET.get("page")
    templates = paginator.get_page(page)
    return render(
        request,
        "expenses/template_list.html",
        {"htmltitle": _("Templates"), "pid": "template_list", "templates": templates,},
    )


@login_required
def template_add(request):
    form = TemplateForm(user=request.user)
    if request.method == "POST":
        form = TemplateForm(request.POST, user=request.user)
        if form.is_valid():
            template = form.save(commit=False)
            template.user = request.user
            template.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse("expenses:template_list"))

    return render(
        request,
        "expenses/template_add_edit.html",
        {"htmltitle": _("Add a template"), "pid": "template_add", "form": form, "mode": "add",},
    )


@login_required
def template_show(request, pk):
    template = get_object_or_404(ExpenseTemplate, pk=pk, user=request.user)
    return render(
        request,
        "expenses/template_show.html",
        {"htmltitle": _("Template %s") % template.name, "pid": "template_add", "template": template,},
    )


@login_required
def template_run(request, pk):
    template = get_object_or_404(ExpenseTemplate, pk=pk, user=request.user)
    expense = Expense(vendor=template.vendor, category=template.category)
    if "date" in request.GET:
        expense.date = request.GET["date"]
    else:
        expense.date = today_date()

    if template.type == "count":
        if not request.GET.get("count"):
            count = decimal.Decimal(1)
        else:
            count = parse_amount_input(request.GET["count"])
            if count is None:
                return HttpResponseBadRequest()

        expense.amount = round_money(template.amount * count)
        desc_lines = template.description.strip().split("\n")
        desc_possibilities = len(desc_lines)
        desc = desc_lines[0]
        if count % 1 != 0:
            # Is decimal, use last possibility
            desc = desc_lines[desc_possibilities - 1]
        elif desc_possibilities == 2:
            # 0 → 1, 1 → anything else (English)
            desc = desc_lines[int(count != 1)]
        elif desc_possibilities in {3, 4}:
            # Polish scheme
            if count == 1:
                desc = desc_lines[0]
            else:
                # Expression from gettext, simplified
                desc = desc_lines[1 if (2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20)) else 2]

        expense.description = desc.replace("!count!", str(count))
    elif template.type == "description":
        expense.amount = template.amount
        expense.description = template.description.replace("!description!", request.GET["description"])
    elif template.type == "desc_select":
        main_desc, *desc_options = template.description.strip().split("\n")
        desc_id = int(request.GET["desc_id"])
        expense.amount = template.amount
        expense.description = main_desc.strip().replace("!description!", desc_options[desc_id].strip())
    elif template.type == "menu":
        desc_id = int(request.GET["desc_id"])
        desc_options = template.description.strip().split("\n")
        amount_str, desc = desc_options[desc_id].strip().split(" ", 1)
        expense.amount = parse_amount_input(amount_str.strip())
        if expense.amount is None:
            return HttpResponseBadRequest()
        expense.description = desc.strip()
    else:
        expense.amount = template.amount
        expense.description = template.description

    expense.user = request.user
    expense.save()
    return HttpResponseRedirect(expense.get_absolute_url())


@login_required
def template_edit(request, pk):
    template = get_object_or_404(ExpenseTemplate, pk=pk, user=request.user)
    form = TemplateForm(instance=template, user=request.user)
    if request.method == "POST":
        form = TemplateForm(request.POST, instance=template, user=request.user)
        if form.is_valid():
            template = form.save(commit=False)
            template.user = request.user
            template.save()
            form.save_m2m()
            return HttpResponseRedirect(template.get_absolute_url())

    return render(
        request,
        "expenses/template_add_edit.html",
        {"htmltitle": _("Edit a template"), "pid": "template_edit", "form": form, "mode": "edit",},
    )


class TemplateDelete(ExpDeleteView):
    model = ExpenseTemplate
    pid = "template_delete"
    success_url = reverse_lazy("expenses:template_list")
    cancel_url = "expenses:template_show"
    cancel_key = "pk"
