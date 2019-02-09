# Django-Expenses
# Copyright © 2018-2019, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

import datetime

from django.conf import settings
from django.dispatch import receiver
from django.urls import reverse
from django.utils.html import format_html
from django.utils.text import slugify, Truncator
from django.utils.translation import gettext_lazy as _
from django.db import models


from expenses.utils import round_money, serialize_dt, serialize_date, serialize_decimal, \
    parse_dt, parse_date, parse_decimal


class ExpensesModel(models.Model):
    class Meta:
        abstract = True

    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def to_json(self) -> dict:
        output = {
            "id": self.pk,
            "date_added": serialize_dt(self.date_added),
            "date_modified": serialize_dt(self.date_modified),
        }
        output.update(self.fields_to_json())
        return output

    def from_json(self, data: dict, date_modified: datetime.datetime) -> None:
        if data.get("id") is None:
            self.date_added = parse_dt(data["date_added"])
        elif data["id"] != self.pk:
            raise ValueError("Data dict does not match")
        if not self.pk or self.date_modified > date_modified:
            self.date_modified = date_modified
            self.fields_from_json(data)

    def fields_to_json(self) -> dict:
        return {}

    def fields_from_json(self, data: dict) -> None:
        pass

    def delete_at(self, date: datetime.datetime):
        dr = DeletionRecord(
            model=MODEL_TO_STR_MAP[self.__class__],
            object_pk=self.pk,
            user=self.user,
            date=date)
        dr.save()
        self.delete()


class Category(ExpensesModel):
    class Meta:
        verbose_name = _("category")
        verbose_name_plural = _("categories")
        indexes = [
            models.Index(fields=['slug', 'user'])
        ]

    name = models.CharField(_("Name"), max_length=20)
    slug = models.CharField(_("Slug"), max_length=20)
    slugbase = models.CharField(_("Slug base"), max_length=20)
    order = models.IntegerField(_("Order"), default=1)

    def get_absolute_url(self):
        return reverse("expenses:category_show", args=[self.slug])

    def html_link(self):
        return format_html('<a href="{0}">{1}</a>', self.get_absolute_url(), self.name)

    def all_time_sum(self):
        return self.expense_set.aggregate(models.Sum('amount'))['amount__sum']

    def monthly_sum(self):
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

    @classmethod
    def user_objects(cls, request):
        """Get ordered category objects for a user."""
        return cls.objects.filter(user=request.user).order_by('order')

    def prepare_deletion(self, dest, user):
        try:
            new_cat = Category.objects.get(pk=int(dest), user=user)
            self.expense_set.update(category=new_cat)
            self.expensetemplate_set.update(category=new_cat)
            return True
        except (Category.DoesNotExist, ValueError):
            return False

    def fields_to_json(self) -> dict:
        return {
            "name": self.name,
            "order": self.order,
        }

    def fields_from_json(self, data: dict) -> None:
        self.name = data["name"]
        self.order = data["order"]


class Expense(ExpensesModel):
    date = models.DateField(_("Date"), default=datetime.date.today)
    vendor = models.CharField(_("Vendor"), max_length=40)
    category = models.ForeignKey(Category, verbose_name=_("Category"), on_delete=models.PROTECT)
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2)
    description = models.CharField(_("Description"), max_length=80, blank=True)
    is_bill = models.BooleanField(_("This is a bill"), default=False)
    description_cache = models.CharField(_("Description (cache)"), max_length=300, blank=True)

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

    def generate_bill_description_full(self):
        if self.billitem_set.count() == 0:
            return _("(empty)")
        return ", ".join(i.product for i in self.billitem_set.all())

    def generate_bill_description(self):
        """Generate a bill description, truncating it to the database limit."""
        return Truncator(self.generate_bill_description_full()).chars(300)

    @property
    def desc_auto(self):
        return self.description_cache

    def fields_to_json(self):
        return {
            "date": serialize_date(self.date),
            "vendor": self.vendor,
            "category": self.category_id,
            "amount": serialize_decimal(self.amount),
            "description": self.description,
            "is_bill": self.is_bill,
        }

    def fields_from_json(self, data: dict) -> None:
        self.date = parse_date(data["date"])
        self.vendor = data["vendor"]
        self.category_id = data["category"]
        self.amount = parse_decimal(data["amount"])
        self.description = data["description"]
        self.is_bill = data["is_bill"]


class BillItem(ExpensesModel):
    bill = models.ForeignKey(Expense, verbose_name=_("Bill"), on_delete=models.CASCADE)
    product = models.CharField(_("Product"), max_length=40)
    serving = models.DecimalField(_("Serving [g, L]"), max_digits=10, decimal_places=3)
    count = models.DecimalField(_("Count"), max_digits=10, decimal_places=3)  # weighted products
    unit_price = models.DecimalField(_("Unit price"), max_digits=10, decimal_places=2)

    @property
    def amount(self):
        return round_money(self.count * self.unit_price)

    def __str__(self):
        return self.product

    def __repr__(self):
        return '<BillItem "{0}" on bill {1}: {2}>'.format(self.product, self.bill_id, self.amount)

    def fields_to_json(self) -> dict:
        return {
            "bill": self.bill_id,
            "product": self.product,
            "serving": serialize_decimal(self.serving),
            "count": serialize_decimal(self.count),
            "unit_price": serialize_decimal(self.unit_price),
        }

    def fields_from_json(self, data: dict) -> None:
        self.bill_id = data["bill"]
        self.product = data["product"]
        self.serving = parse_decimal(data["serving"])
        self.count = parse_decimal(data["count"])
        self.unit_price = parse_decimal(data["unit_price"])


TEMPLATE_TYPE_CHOICES = (
    ('simple', _('Simple')),
    ('count', _('Multiplied by count')),
    ('description', _('With custom description')),
    ('desc_select', _('With description selected from list'))
)
TEMPLATE_TYPE_CHOICES_LOOKUP = {k: v for k, v in TEMPLATE_TYPE_CHOICES}


class ExpenseTemplate(ExpensesModel):
    name = models.CharField(_("Name"), max_length=40)
    vendor = models.CharField(_("Vendor"), max_length=40)
    category = models.ForeignKey(Category, verbose_name=_("Category"), on_delete=models.PROTECT)
    type = models.CharField(_("Template type"), max_length=20, choices=TEMPLATE_TYPE_CHOICES, default='simple')
    amount = models.DecimalField(_("Amount"), max_digits=10, decimal_places=2, null=True)
    description = models.CharField(_("Description"), max_length=400)
    comment = models.TextField(_("Comment"), blank=True)

    def get_absolute_url(self):
        return reverse("expenses:template_show", args=[self.pk])

    def type_text(self):
        return TEMPLATE_TYPE_CHOICES_LOOKUP[self.type]

    def html_link(self):
        return format_html('<a href="{0}">{1}</a>', self.get_absolute_url(), self.name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<ExpenseTemplate "{0}">'.format(self.name)

    def description_choices(self):
        return self.description.split('\n')[1:]

    def fields_to_json(self) -> dict:
        return {
            "name": self.name,
            "vendor": self.vendor,
            "category": self.category_id,
            "type": self.type,
            "amount": serialize_decimal(self.amount),
            "description": self.description,
            "comment": self.comment,
        }

    def fields_from_json(self, data: dict) -> None:
        self.name = data["name"]
        self.vendor = data["vendor"]
        self.category_id = data["category_id"]
        self.type = data["type"]
        self.amount = parse_decimal(data["amount"])
        self.description = data["description"]
        self.comment = data["comment"]


DR_MODEL_CHOICES = (
    ('category', 'category'),
    ('expense', 'expense'),
    ('billitem', 'billitem'),
    ('expensetemplate', 'expensetemplate'),
)


class DeletionRecord(models.Model):
    model = models.CharField(max_length=20, choices=DR_MODEL_CHOICES)
    object_pk = models.IntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "<DeletionRecord {} #{}>".format(self.model, self.object_pk)

    def to_json_dict(self):
        return {
            "model": self.model,
            "object": self.object_pk,
            "date": self.date
        }


STR_TO_MODEL_MAP = {
    'category': Category,
    'expense': Expense,
    'billitem': BillItem,
    'expensetemplate': ExpenseTemplate,
    'deletionrecord': DeletionRecord
}
MODEL_TO_STR_MAP = {v: k for k, v in STR_TO_MODEL_MAP.items()}

DATA_MODELS = (
    (Category, 'category'),
    (Expense, 'expense'),
    (BillItem, 'billitem'),
    (ExpenseTemplate, 'expensetemplate')
)

DATA_MODELS_STR = ['category', 'expense', 'billitem', 'expensetemplate']
STR_TO_DATA_MODEL_MAP = {k: v for k, v in STR_TO_MODEL_MAP.items() if k != 'deletionrecord'}


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
def update_bill_info_on_billitem_change(instance: BillItem, **kwargs):
    bill = instance.bill
    bill.amount = bill.calculate_bill_total()
    if not bill.description:
        bill.description_cache = bill.generate_bill_description()
    else:
        bill.description_cache = bill.description
    bill.save()


@receiver(models.signals.pre_save, sender=Expense)
def update_bill_info_on_bill_save(instance: Expense, **kwargs):
    instance.description_cache = instance.description
    if instance.is_bill:
        instance.amount = instance.calculate_bill_total()
        instance.description_cache = instance.generate_bill_description()
        if not instance.description:
            instance.description = instance.description_cache


@receiver(models.signals.pre_delete, sender=Category)
@receiver(models.signals.pre_delete, sender=Expense)
@receiver(models.signals.pre_delete, sender=BillItem)
@receiver(models.signals.pre_delete, sender=ExpenseTemplate)
def create_deletion_record(instance, sender, **kwargs):
    DeletionRecord.objects.get_or_create(
        model=MODEL_TO_STR_MAP[sender],
        object_pk=instance.pk,
        user=instance.user)

