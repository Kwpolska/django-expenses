# Django-Expenses
# Copyright © 2018-2023, Chris Warrick.
# All rights reserved.
# See /LICENSE for licensing information.

from django import forms
from django.utils.translation import gettext_lazy

from expenses.utils import today_date
from expenses.models import Expense, Category, BillItem, ExpenseTemplate


class ExpenseForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(user=user).order_by("order")
        self.fields["date"].default = today_date().strftime("%Y-%m-%d")
        self.fields["description"].required = True

    class Meta:
        model = Expense
        fields = ["date", "vendor", "category", "amount", "description"]
        widgets = {
            "date": forms.TextInput(attrs={"class": "form-control", "placeholder": gettext_lazy("Date")}),
            "vendor": forms.TextInput(
                attrs={"class": "form-control expenses-addform-vendor", "placeholder": gettext_lazy("Vendor")}
            ),
            "amount": forms.TextInput(
                attrs={"class": "form-control form-control-lg", "type": "number", "step": "0.01", "placeholder": "0.00"}
            ),
            "description": forms.TextInput(
                attrs={"class": "form-control expenses-addform-description", "placeholder": gettext_lazy("Description")}
            ),
        }


class BillForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(user=user).order_by("order")
        self.fields["date"].default = today_date().strftime("%Y-%m-%d")
        self.fields["description"].required = False

    class Meta:
        model = Expense
        fields = ["date", "vendor", "category", "description"]
        widgets = {
            "date": forms.TextInput(attrs={"class": "form-control", "placeholder": gettext_lazy("Date")}),
            "vendor": forms.TextInput(
                attrs={"class": "form-control expenses-billaddform-vendor", "placeholder": gettext_lazy("Vendor")}
            ),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": gettext_lazy("Description")}),
        }


class BillItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["count"].default = 1

    class Meta:
        model = BillItem
        fields = ["product", "serving", "count", "unit_price"]
        widgets = {
            "product": forms.TextInput(attrs={"class": "form-control", "placeholder": gettext_lazy("Product")}),
            "serving": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "number",
                    "step": "0.001",
                    "placeholder": gettext_lazy("Serving"),
                }
            ),
            "count": forms.TextInput(
                attrs={"class": "form-control", "type": "number", "step": "0.001", "placeholder": gettext_lazy("Count")}
            ),
            "unit_price": forms.TextInput(
                attrs={"class": "form-control form-control-lg", "type": "number", "step": "0.01", "placeholder": "0.00"}
            ),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "order": forms.TextInput(attrs={"class": "form-control", "type": "number"}),
        }


class TemplateForm(forms.ModelForm):
    category = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs={"class": "form-select"}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(user=user).order_by("order")
        self.fields["description"].required = True
        self.fields["comment"].required = False
        self.fields["amount"].required = False

    class Meta:
        model = ExpenseTemplate
        fields = ["name", "vendor", "category", "amount", "description", "type", "comment"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": gettext_lazy("Name")}),
            "vendor": forms.TextInput(
                attrs={"class": "form-control expenses-tmplform-vendor", "placeholder": gettext_lazy("Vendor")}
            ),
            "amount": forms.TextInput(
                attrs={"class": "form-control form-control-lg", "type": "number", "step": "0.01", "placeholder": "0.00"}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control expenses-tmplform-description",
                    "rows": "4",
                    "placeholder": gettext_lazy("Description"),
                }
            ),
            "type": forms.RadioSelect(),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control expenses-tmplform-comment",
                    "rows": "3",
                    "placeholder": gettext_lazy("Comment (optional)"),
                }
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        template_type = cleaned_data.get("type")

        if not amount and template_type != "menu":
            self.add_error("amount", gettext_lazy("Amount is required for this template type."))
