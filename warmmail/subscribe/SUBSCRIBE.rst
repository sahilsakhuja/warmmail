Subscribe App
=============

Welcome to the documentation for the Subscribe App. The subscribe app is the central app for this Django project.

The subscribe app handles the following:

* Frontend: The subscribe app has the logic for all the Views that are used to render the complete frontend website
* Models: The subscribe app also defines the main model - Subscribe - that manages the newsletter subscriptions
* Tasks: In the backend, Warmmail uses Luigi tasks to update data every day as well as to send emails to subscribed users

There are complete details available about these functionalities below.

Frontend: Views
---------------

.. autofunction:: warmmail.subscribe.views.index

|

.. autofunction:: warmmail.subscribe.views.findplace

|

.. autofunction:: warmmail.subscribe.views.selectplace

|

.. autofunction:: warmmail.subscribe.views.subscribeplace

|

.. autofunction:: warmmail.subscribe.views.confirmsubscription

|

.. autofunction:: warmmail.subscribe.views.verifyemail

|

Models
------

.. autofunction:: warmmail.subscribe.models.Subscription

|

Tasks
-----

.. autofunction:: warmmail.subscribe.tasks_fetch.DownloadAQI

|

.. autofunction:: warmmail.subscribe.tasks_fetch.ConvertAQIFileToParquet

|

.. autofunction:: warmmail.subscribe.tasks_send.GenerateEmails

|

.. autofunction:: warmmail.subscribe.tasks_send.CheckForPendingEmails

|

Helper Functions for Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: warmmail.subscribe.tasks_send.UrlParameter

|

.. autofunction:: warmmail.subscribe.tasks_send.RowFilterTarget

|

.. autofunction:: warmmail.subscribe.tasks_send.RowFilterOutput

|
