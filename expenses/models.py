# Django-Expenses
# Copyright © 2018, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

import datetime
import decimal

from django.conf import settings
from django.dispatch import receiver
from django.urls import reverse
from django.utils.html import format_html
from django.utils.text import slugify, Truncator
from django.utils.translation import gettext_lazy as _, gettext_lazy
from django.db import models


class Category(models.Model):
    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")

    name = models.CharField(_("name"), max_length=20)
    slug = models.CharField(_("slug"), max_length=20)
    slugbase = models.CharField(_("slug base"), max_length=20)
    order = models.IntegerField(_("order"), default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse("expenses:category_show", args=[self.slug])

    def html_link(self):
        return format_html('<a href="{0}">{1}</a>', self.get_absolute_url(), self.name)

    def monthly_sum(self):
        return self.expense_set.aggregate(models.Sum('amount'))['amount__sum']

    def all_time_sum(self):
        today = datetime.date.today()
        return self.expense_set.filter(
            date__year=today.year, date__month=today.month).aggregate(models.Sum('amount'))['amount__sum']

    @property
    def total_count(self):
        return self.expense_set.count() + self.expensetemplate_set.count()

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<Category {0} (order {1})>".format(self.name, self.order)


class Expense(models.Model):
    date = models.DateField(_("date"), default=datetime.date.today)
    vendor = models.CharField(_("vendor"), max_length=40)
    category = models.ForeignKey(Category, verbose_name=_("category"), on_delete=models.PROTECT)
    amount = models.DecimalField(_("amount"), max_digits=10, decimal_places=2)
    description = models.CharField(_("description"), max_length=80, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    is_bill = models.BooleanField(_("this is a bill"), default=False)
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{0}: {1}'.format(self.desc_auto, self.amount)

    def __repr__(self):
        return '<Expense "{0}" on {1}: {2}>'.format(self.desc_auto, self.date, self.amount)

    def get_absolute_url(self):
        return reverse("expenses:bill_show" if self.is_bill else "expenses:expense_show", args=[self.pk])

    def calculate_bill_total(self):
        sum = 0
        for b in self.billitem_set.all():
            sum += b.amount
        return sum

    @property
    def desc_auto(self):
        if self.description:
            return self.description
        if self.billitem_set.count() == 0:
            return gettext_lazy("(empty)")
        return Truncator(", ".join(i.product for i in self.billitem_set.all())).chars(80)


class BillItem(models.Model):
    bill = models.ForeignKey(Expense, verbose_name=_("bill"), on_delete=models.CASCADE)
    product = models.CharField(_("product"), max_length=40)
    serving = models.DecimalField(_("serving [g, L]"), max_digits=10, decimal_places=3)
    count = models.DecimalField(_("count"), max_digits=10, decimal_places=3)  # weighted products
    unit_price = models.DecimalField(_("unit price"), max_digits=10, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    @property
    def amount(self):
        return (self.count * self.unit_price).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)

    def __str__(self):
        return self.product

    def __repr__(self):
        return '<BillItem "{0}" on bill {1}: {2}>'.format(self.product, self.bill_id, self.amount)


class BillItemTemplate(models.Model):
    product = models.CharField(_("product"), max_length=40)
    serving = models.DecimalField(_("serving [g, L]"), max_digits=10, decimal_places=3)
    unit_price = models.DecimalField(_("unit price"), max_digits=10, decimal_places=2)
    comment = models.TextField(_("comment"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product

    def __repr__(self):
        return '<BillItemTemplate "{0}": {1} per unit>'.format(self.product, self.unit_price)


class ExpenseTemplate(models.Model):
    vendor = models.CharField(_("vendor"), max_length=40)
    category = models.ForeignKey(Category, verbose_name=_("category"), on_delete=models.PROTECT)
    type = models.CharField(_("template type"), max_length=20, choices=(
        ('simple', _('Simple')),
        ('count', _('Multiplied by count')),
    ))
    amount = models.DecimalField(_("amount"), max_digits=10, decimal_places=2, null=True)
    description = models.CharField(_("description (!count! tag accepted)"), max_length=80)
    comment = models.TextField(_("comment"))
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '{0}: {1}'.format(self.description, self.amount)

    def __repr__(self):
        return '<ExpenseTemplate "{0}": {1}>'.format(self.description, self.amount)


# Code from the Achieve project.
@receiver(models.signals.pre_save, sender=Category)
def update_slug(sender, instance: Category, **kwargs):  # NOQA
    """Update the slug for an item."""
    # The slugbase is used to identify things with the same slug base.
    slugbase = slugify(instance.name)
    if slugbase == instance.slugbase:
        # Assuming DB consistency, the slug is fine
        return

    samebase = sender.objects.filter(user=instance.user, slugbase=slugbase)
    if not samebase:
        # New slug base.
        final_slug = slugbase
    elif len(samebase) == 1 and samebase[0] == instance:
        # (If forced) only slug like this.
        final_slug = slugbase
    else:
        # We need to find a new slug for ourselves.
        others = samebase.exclude(slug=slugbase)
        if others:
            nums = [int(i.slug.split('-')[-1]) for i in others.all()]
            final_num = max(nums) + 1
        else:
            final_num = 1
        final_slug = "{0}-{1}".format(slugbase, final_num)

    instance.slugbase = slugbase
    instance.slug = final_slug


@receiver(models.signals.post_save, sender=BillItem)
@receiver(models.signals.post_delete, sender=BillItem)
def update_bill_amount_on_billitem_change(instance: BillItem, **kwargs):
    bill = instance.bill
    bill.amount = bill.calculate_bill_total()
    bill.save()


@receiver(models.signals.pre_save, sender=Expense)
def update_bill_amount_on_bill_save(instance: Expense, **kwargs):
    if instance.is_bill:
        instance.amount = instance.calculate_bill_total()
