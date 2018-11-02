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

To-do
-----

* Reports


Configuration
-------------

settings.py
~~~~~~~~~~~

You should do the following changes to ``settings.py``:

* Add ``'expenses'`` and ``'oauth2_provider'`` to ``INSTALLED_APPS``
* Add ``'oauth2_provider.middleware.OAuth2TokenMiddleware'`` to ``MIDDLEWARE``
  *after* ``SessionMiddleware``
* If you’re me, add ``'expenses.middleware.ForcePolishLanguageMiddleware'``
  to ``MIDDLEWARE`` as well

and also set the following options:

* ``EXPENSES_PAGE_SIZE`` — number of items on one page
* ``EXPENSES_INDEX_COUNT`` — number of expenses to display on the dashboard
* ``EXPENSES_CURRENCY_CODE`` — currency code, eg. ``PLN``
* ``EXPENSES_CURRENCY_LOCALE`` — currency locale, eg. ``pl_PL``

urls.py
~~~~~~~

.. code:: python
    urlpatterns = [
        # ...
        path('expenses/', include(expenses.urls)),
        path('_oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    ]

If you intend to use the API, OAuth applications can be set up at
``/_oauth/applications/``. (If you don’t, the endpoints won’t do anything
without it.)
