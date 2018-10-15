"""Template views."""
import decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext as _

from expenses.forms import TemplateForm
from expenses.models import ExpenseTemplate, Expense
from expenses.utils import today_date
from expenses.views import ExpDeleteView


@login_required
def template_list(request):
    paginator = Paginator(
        ExpenseTemplate.objects.filter(user=request.user).order_by('name'),
        settings.EXPENSES_PAGE_SIZE)
    page = request.GET.get('page')
    templates = paginator.get_page(page)
    return render(request, 'expenses/template_list.html', {
        'htmltitle': _("Templates"),
        'pid': 'template_list',
        'templates': templates,
    })


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
            return HttpResponseRedirect(template.get_absolute_url())

    return render(request, 'expenses/template_add_edit.html', {
        'htmltitle': _("Add a template"),
        'pid': 'template_add',
        'form': form,
        'mode': 'add',
    })


@login_required
def template_show(request, pk):
    template = get_object_or_404(ExpenseTemplate, pk=pk, user=request.user)
    return render(request, 'expenses/template_show.html', {
        'htmltitle': _("Template %s") % template.name,
        'pid': 'template_add',
        'template': template,
    })


@login_required
def template_run(request, pk):
    template = get_object_or_404(ExpenseTemplate, pk=pk, user=request.user)
    expense = Expense(
        vendor=template.vendor,
        date=today_date(),
        category=template.category)
    if template.type == 'count':
        if 'count' not in request.GET:
            return HttpResponseBadRequest()

        try:
            count = decimal.Decimal(request.GET['count'])
        except ValueError:
            try:
                count = decimal.Decimal(request.GET['count'].replace(',', '.'))
            except ValueError:
                return HttpResponseBadRequest()

        expense.amount = template.amount * count
        expense.description = template.description.replace('!count!', str(count))
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

    return render(request, 'expenses/template_add_edit.html', {
        'htmltitle': _("Edit a template"),
        'pid': 'template_edit',
        'form': form,
        'mode': 'edit',
    })

class BillDelete(ExpDeleteView):
    model = ExpenseTemplate
    pid = 'template_delete'
    success_url = reverse_lazy('expenses:template_list')
    cancel_url = 'expenses:template_show'
    cancel_key = 'pk'
