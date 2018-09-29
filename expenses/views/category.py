# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

"""Category management."""

from collections import defaultdict
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext as _

from expenses.forms import CategoryForm
from expenses.models import Category, Expense, ExpenseTemplate
from expenses.utils import cat_objs, revchron


@login_required
def category_list(request):
    paginator = Paginator(
        cat_objs(request),
        settings.EXPENSES_PAGE_SIZE)
    page = request.GET.get('page')
    categories = paginator.get_page(page)
    return render(request, 'expenses/category_list.html', {
        'htmltitle': _("Categories"),
        'pid': 'category_list',
        'categories': categories,
    })


@login_required
def category_show(request, slug):
    category = get_object_or_404(Category, slug=slug, user=request.user)
    paginator = Paginator(
        revchron(Expense.objects.filter(user=request.user, category=category)),
        settings.EXPENSES_PAGE_SIZE)
    page = request.GET.get('page')
    expenses = paginator.get_page(page)
    return render(request, 'expenses/category_show.html', {
        'expenses': expenses,
        'category': category,
        'pid': 'category_show',
    })


@login_required
def category_show_templates(request, slug):
    category = get_object_or_404(Category, slug=slug, user=request.user)
    paginator = Paginator(
        ExpenseTemplate.objects.filter(user=request.user, category=category).order_by('-date_added'),
        settings.EXPENSES_PAGE_SIZE)
    page = request.GET.get('page')
    templates = paginator.get_page(page)
    return render(request, 'expenses/category_show_templates.html', {
        'templates': templates,
        'category': category,
        'pid': 'category_show_templates',
    })


@login_required
def category_add(request):
    form = CategoryForm()
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            inst = form.save(commit=False)
            inst.user = request.user
            inst.save()
            form.save_m2m()
            return HttpResponseRedirect(reverse('expenses:category_list'))

    return render(request, 'expenses/category_add_edit.html', {
        'form': form,
        'form_mode': 'add',
        'htmltitle': _('Add a category'),
        'title': _('Add a category'),
        'pid': 'category_add',
    })


@login_required
def category_edit(request, slug):
    category = get_object_or_404(Category, slug=slug, user=request.user)
    form = CategoryForm(instance=category)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            inst = form.save()
            return HttpResponseRedirect(inst.get_absolute_url())

    return render(request, 'expenses/category_add_edit.html', {
        'form': form,
        'form_mode': 'edit',
        'htmltitle': _('Edit category %s') % category.name,
        'title': _('Edit category'),
        'pid': 'category_edit',
    })


@login_required
def category_delete(request, slug):
    category = get_object_or_404(Category, slug=slug, user=request.user)
    deletion_failed = False
    if request.method == "POST":
        if category.total_count != 0:
            dest = request.POST.get('move_destination')
            try:
                new_cat = Category.objects.get(pk=int(dest), user=request.user)
                category.expense_set.update(category=new_cat)
                category.expensetemplate_set.update(category=new_cat)
            except (Category.DoesNotExist, ValueError):
                deletion_failed = True

        if not deletion_failed:
            category.delete()
            return HttpResponseRedirect(reverse('expenses:category_list'))

    categories = cat_objs(request)
    show_del_button = True
    if categories.count == 1 and category.total_count > 0:
        show_del_button = False

    return render(request, 'expenses/category_delete.html', {
        'object': category,
        'deletion_failed': deletion_failed,
        'htmltitle': _('Delete category %s') % category.name,
        'pid': 'category_delete',
        'categories': categories,
        'show_del_button': show_del_button,
    })


@login_required
def category_bulk_edit(request):
    categories = cat_objs(request)
    if request.method == 'POST':
        added_count = 0
        changed_count = 0
        unchanged_count = 0
        failure_count = 0
        failure_list = []

        for cat in categories:
            prefix = 'cat_{}_'.format(cat.pk)
            new_name = request.POST.get(prefix + 'name')
            new_order = request.POST.get(prefix + 'order')
            if new_name and new_order and new_order.isnumeric():
                # can be changed
                new_order = int(new_order)
                if cat.name != new_name or cat.order != new_order:
                    cat.name = new_name
                    cat.order = new_order
                    cat.save()
                    changed_count += 1
                else:
                    unchanged_count += 1
            else:
                failure_count += 1
                failure_list.append(cat.name)
        
        additions = defaultdict(dict)
        print(request.POST)
        for k, v in request.POST.items():
            if k.startswith("add_"):
                print(k, v)
                _add, aid, key = k.split('_')
                additions[aid][key] = v
        
        for k, fields in additions.items():
            new_name = fields.get('name')
            new_order = fields.get('order')
            if new_name and new_order and new_order.isnumeric():
                c = Category()
                c.name = new_name
                c.order = new_order
                c.user = request.user
                c.save()
                added_count += 1
            else:
                failures_count += 1
                failures_list.append("+{}/{}".format(new_name, new_order))

        return render(request, 'expenses/category_bulk_edit_results.html', {
            'htmltitle': _('Edit categories'),
            'title': _('Edit categories'),
            'pid': 'category_bulk_edit_results',
            'added_count': added_count,
            'changed_count': changed_count,
            'unchanged_count': unchanged_count,
            'failure_count': failure_count,
            'failure_list': failure_list,
        })

    return render(request, 'expenses/category_bulk_edit.html', {
        'categories': categories,
        'htmltitle': _('Edit categories'),
        'title': _('Edit categories'),
        'pid': 'category_bulk_edit',
    })
