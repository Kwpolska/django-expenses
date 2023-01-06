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
* Templates for expenses (with multiplication and custom description)
* i18n (Polish translation)
* Searching and filtering data
* A synchronization API, perfect for mobile apps (one of which is in the
  making)
* Reporting

To do
-----

* Exporting reports to spreadsheet-friendly formats (CSV? XLSX?)
* Monthly goals
* More?

Configuration
-------------

settings.py
~~~~~~~~~~~

In order to use Expenses, you need to add ``'expenses'`` to ``INSTALLED_APPS``. Also, if you’re me, add ``'django.middleware.locale.LocaleMiddleware', 'expenses.middleware.ForcePolishLanguageMiddleware'`` to ``MIDDLEWARE`` (before CommonMiddleware and after SessionMiddleware).

You should set the following options:

* ``EXPENSES_PAGE_SIZE`` — number of items on one page
* ``EXPENSES_INDEX_COUNT`` — number of expenses to display on the dashboard
* ``EXPENSES_CURRENCY_CODE`` — currency code, eg. ``PLN``
* ``EXPENSES_CURRENCY_LOCALE`` — currency locale, eg. ``pl_PL``
* ``EXPENSES_CSV_DELIMITER`` — delimiter for fields in CSV reports, eg. ``,`` or ``;`` or ``\t``
* ``EXPENSES_SYNC_API_ENABLED`` — enable the sync API? (requires extra configuration)

The following ``MESSAGE_TAGS`` is recommended for the default templates:

.. code:: python

   from django.contrib.messages import constants as messages
   MESSAGE_TAGS = {
       messages.ERROR: 'danger',
       messages.DEBUG: 'secondary'
   }

If you want to use the Expenses Sync API (it’s off by default), you should do the following changes to ``settings.py``:

* Add ``'oauth2_provider'`` to ``INSTALLED_APPS``
* Add ``'oauth2_provider.middleware.OAuth2TokenMiddleware'`` to ``MIDDLEWARE`` *after* ``SessionMiddleware``

urls.py
~~~~~~~

.. code:: python
    urlpatterns = [
        # ...
        path('expenses/', include(expenses.urls)),
        # for Sync API:
        path('__oauth__/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    ]

If you intend to use the API, OAuth applications can be set up at ``/_oauth/applications/``.

Base template
~~~~~~~~~~~~~

Expenses expects you to have a ``base.html`` template in your template root. A
sample file that should work is provided as ``base.html.sample`` in the
repository. If this doesn’t suit you, you can modify ``expbase.html`` (and
possibly make it independent).
