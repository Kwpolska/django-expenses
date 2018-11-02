=========
Changelog
=========

GitHub holds releases, too
==========================

More information can be found on GitHub in the `releases section
<https://github.com/Kwpolska/django-expenses/releases>`_.

Version History
===============

0.4.0
    * Add Synchronization API
    * Record all deletions in the database (for sync API)
    * Optimize search pagination

0.3.1
    * Searching for all purchases (both expenses and bills)
    * Display date in searches and sort properly

0.3.0
    * Searching and filtering data
    * Stop using admin site
    * Templates with custom descriptions and backdating
    * Pass config and locale to JS

0.2.2
    * Add Polish translation
    * Support repeating expenses
    * Fix money rounding in some places
    * Minor behavior and visual fixes

0.2.1
    * Initial implementation of expense templates

0.2.0
    * Support adding items in bulk category editor
    * Various bill editor UX improvements
    * Nuke BillItemTemplates to improve usability
    * Implement custom autocomplete thing based on ``<dataset>`` (yay for HTML5)
    * Autocomplete for bill items based on history (with same vendor)

0.1.2
    * Handle Return key in bill editor better
    * Add custom favicon
    * Streamline ``category_list.html`` table
    * Undo mixing up two functions

0.1.1
    * Fix some visual glitches
    * Refactor autocomplete handlers
    * Improve pagination display
    * Shorten descriptions

0.1.0
    Initial public release.
