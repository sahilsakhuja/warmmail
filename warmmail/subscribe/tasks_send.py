# -*- coding: utf-8 -*-

import os
import urllib.parse
from datetime import date, datetime
from functools import partial
from urllib.parse import quote_plus

import pandas as pd
import plotly.express as px
import pytz
from csci_utils.luigi.requires import Requirement, Requires
from csci_utils.luigi.target import TargetOutput
from django.template.loader import render_to_string
from luigi import (
    DateParameter,
    ExternalTask,
    ListParameter,
    LocalTarget,
    Parameter,
    Target,
    Task,
)
from plotly.io import to_image
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .models import Subscription
from .tasks_fetch import ConvertAQIFileToParquet


class UrlParameter(Parameter):
    """Descriptor to ensure that a file name is url safe i.e. quoted"""

    def normalize(self, x):
        return quote_plus(x)


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


class GenerateEmails(ExternalTask):
    """
    Task to generate the html content to be sent via email.
    Uses Django's render to string functionality.

    :param city: name of the city for which report has to be generated
    :param pol: name of the dominant pollutant for that city
    :param date: the date for which report has to be generated
    """

    city = UrlParameter(default=None)
    pol = Parameter(default="pm25")
    date = DateParameter(default=date.today())

    requires = Requires()
    historical = Requirement(ConvertAQIFileToParquet)

    output = TargetOutput(
        factory=LocalTarget,
        file_pattern="emails/{task.city}-{task.date}",
        ext=".html",
    )

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


class CheckForPendingEmails(Task):
    """
    Task to check for pending emails. This uses a "RowFilterOutput" which checks for rows in the database
    which have the "next_email_date" in the past.
    For each such row found (city + dominent pollutant fetched frm the DB), the task requires a GenerateEmails task.
    """

    cities = ListParameter(default=None)
    pols = ListParameter(default=None)
    date = DateParameter(default=date.today())

    def requires(self):
        return {
            k: GenerateEmails(city=k, pol=self.pols[i])
            for i, k in enumerate(self.cities)
        }

    output = RowFilterOutput(
        model=Subscription,
        entries_param=["cities", "pols"],
        field=["city", "dominentpol"],
        next_email_date__lte=datetime.now(tz=pytz.utc),
    )

    def run(self):
        for city in self.cities:
            vals = Subscription.objects.filter(
                next_email_date__lte=datetime.now(tz=pytz.utc), city__exact=city
            )

            emails = list(map(lambda x: x.email, vals))

            html = open(self.input()[city].path).read()

            message = Mail(
                from_email="sahilsakhuja85@gmail.com",
                to_emails=emails[0],
                subject=f"Daily AQI Update for {city} from WarmMail",
                html_content=html,
            )
            try:
                sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
                sg.send(message)
            except Exception as e:
                print(e.message)
