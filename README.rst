===============
Django-Expenses
===============

A comprehensive system for managing expenses.

License: 3-clause BSD. (But please don’t use ``expbase.html`` as-is, it contains
copyrighted chriswarrick.com CSS assets.)

Features
--------

* Management of expenses
* Management of bills — expenses with multiple items, complete with an advanced interactive editor
* Reasonable appearance on Desktop and Mobile
* Autocomplete for expenses and bill items

To-do
-----

* Templates for expenses
* Autocomplete for expense templates?
* i18n (Polish translation)
* Pushing config (URLs, locale) to JS
* searching and filtering

Configuration
-------------

* ``EXPENSES_PAGE_SIZE`` — number of items on one page
* ``EXPENSES_INDEX_COUNT`` — number of expenses to display on the dashboard
* ``EXPENSES_CURRENCY_CODE`` — currency code, eg. ``PLN``
* ``EXPENSES_CURRENCY_LOCALE`` — currency locale, eg. ``pl_PL``
