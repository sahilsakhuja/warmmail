Advanced Python Highlights
==========================

In quite some places, I have used developed some functions and classes which are the hallmarks of our learnings from this course. Sharing below a small taste of these.

Luigi
-----

*Problem statement:* Luigi checks for a task status by checking if output file exists. This creates a gap for databases. Luigi has extended support using a SqlAlchemy Target which allows inserting rows into a database. However, there is still a gap if we want to run a task by checking the value of a row/column in a database or running a filter against a database and seeing if any rows fulfill the required filter. As an example, for the Warmmail project, I needed to identify subscribers to whom an email should be sent at a certain time. To ensure scalability, I am storing a "Next Email Datetime" in the database and I want the relevant task to run if there is any such date time which has now gone into the past.

*Solution:* Custom descriptor + target which checks if there are any results for a Django filter.

Descriptor Code
^^^^^^^^^^^^^^^

This class acts inherits from the target class and overrides the exists method.

.. code-block:: Python
    :linenos:

    class RowFilterTarget(Target):
        """A target class for filters on rows
        Checks to see if any rows exist that satisfy the given filter
        If no results found, return True (i.e. task is complete), else False
        False - causes Luigi to think that task is pending and runs it + check requirements
        """

        def __init__(self, model, **kwargs):
            self.model = model
            self.kwargs = kwargs

        def exists(self):
            vals = self.model.objects.filter(**self.kwargs)
            if not vals:
                return True
            return False


Target Output Code
^^^^^^^^^^^^^^^^^^

This class operates the actual logic of running the filter on the Django database.

An additional feature implemented by this class is that it support returning the relevant fields (as requested in the arguments) to the parent task class. This ensures that these fields can be passed on to upstream tasks via the "requires" method and hence, upstream tasks do not need to check the database again.

.. code-block:: Python
    :linenos:

    class RowFilterOutput:
        """Descriptor for the output method
        Returns a "RowFilterTarget" for the Luigi task
        Additional feature: in case there are values returned from the filter,
        descriptor can accept name of fields and parameters on the parent class
        and update the parent class parameters -
        this ensures that downstream tasks do not need to call the database again
        """

        def __init__(self, model, entries_param=None, field=None, **kwargs):
            self.model = model
            entries_param = (
                entries_param if isinstance(entries_param, list) else [entries_param]
            )
            field = field if isinstance(field, list) else [field]
            self.parent_updates = dict(zip(entries_param, field))
            self.kwargs = kwargs

        def __get__(self, task, cls):
            if not task:
                return self
            return partial(self.__call__, task)

        def __call__(self, task):
            vals = self.model.objects.filter(**self.kwargs)
            if vals and self.parent_updates:
                for entry, field in self.parent_updates.items():
                    setattr(task, entry, tuple(set(getattr(v, field) for v in vals)))
            return RowFilterTarget(self.model, **self.kwargs)

Django: Models
--------------

One of the interesting features of Django Models that has been used in this project is the ENUM abstraction i.e. DJango's own way of having a restricted set of "choices" for a field in the database.

.. code-block:: Python
    :linenos:
    :emphasize-lines: 22-24

    class Subscription(models.Model):
    """
    The main subscription model with below fields.
    Constraints: Only 1 subscription allowed per email + city combination.
    """

    email = models.EmailField()
    verified = models.BooleanField(default=False)
    temp_token = models.CharField(max_length=24)
    city = models.CharField(max_length=100)
    dominentpol = models.CharField(max_length=100)
    next_email_date = models.DateTimeField(default=date.today())
    created_date = models.DateTimeField(default=date.today())
    update_date = models.DateTimeField(default=date.today())

    class Meta:
        unique_together = (
            "email",
            "city",
        )

    class Status(models.TextChoices):
        ACTIVE = "A", _("Active")
        INACTIVE = "I", _("Inactive")

    status = models.CharField(
        max_length=1, choices=Status.choices, default=Status.ACTIVE
    )

    def __str__(self):
        return self.email + " -> " + self.city



Django: Rendering
-----------------

As part of this project, there were 2 rendering challenges to be solved:

1. Template rendering for emails - For this, I have used Django’s “render_to_string” functionality
2. Render plots as images - For this, I have used the “kaleido” library from Plotly

.. code-block:: Python
    :linenos:
    :emphasize-lines: 20-28

    def run(self):
        city = urllib.parse.unquote(self.city)
        df = pd.read_parquet(self.historical.output().path)
        df = df[df["City"] == city].sort_index(ascending=False)
        df = df[df["Specie"].isin(["pm10", "pm25"])]
        df = df.pivot(index=None, columns="Specie", values="median")
        df.fillna(0, inplace=True)
        df.sort_index(inplace=True, ascending=False)
        last_7_days = df.iloc[:6]

        data = {"aqi": df.iloc[0][self.pol]}
        df["month"] = df.index.strftime("%Y-%m")

        df_month = df.groupby("month").agg("mean")

        last_7_days_bar = px.bar(last_7_days, title="Last 7 Days", barmode="group")
        month_bar = px.bar(df_month, title="Monthly", barmode="group")
        from base64 import b64encode

        data["image_last_7_days"] = b64encode(
            to_image(last_7_days_bar, format="png", engine="kaleido")
        ).decode()
        data["image_months"] = b64encode(
            to_image(month_bar, format="png", engine="kaleido")
        ).decode()
        html = render_to_string(
            "subscribe/newsletter_email_template.html", {"data": data}
        )
        with open(self.output().path, "w") as f:
            f.write(html)
