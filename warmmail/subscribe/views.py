import json
import random
import string
from datetime import date, datetime, timedelta
from functools import reduce
from pathlib import Path

import environ
import pandas as pd
import plotly.express as px
import pytz
import requests

# from django.http import HttpResponse
from django.shortcuts import Http404, get_object_or_404, render
from django.template.loader import render_to_string
from plotly.offline import plot
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .models import Subscription

# Create your views here.

ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
# warmmail/
APPS_DIR = ROOT_DIR / "warmmail"
env = environ.Env()

env.read_env(str(ROOT_DIR / ".env"))


def index(request):
    return render(request, "subscribe/index.html")
    # return HttpResponse("Hello, world. You're at the polls index.")


def findplace(request):
    srch = request.POST["search_term"]
    response = requests.get(
        f"http://api.geonames.org/searchJSON?formatted=true&q={srch}&maxRows=10&lang=es&"
        f"username=sahilsakhuja&style=full"
    )
    if response:
        items = response.json()
        places = []
        for item in items["geonames"]:
            city = {
                "name": item["asciiName"],
                "country": item["countryCode"],
                "lat": item["lat"],
                "long": item["lng"],
            }
            places.append(city)
        return render(request, "subscribe/list_places.html", {"places": places})
    else:
        # redirect to index with error
        return render(request, "subscribe/list_places.html")


aqi_desc = {
    50: {
        "level": "Good",
        "text": "Air quality is considered satisfactory, and air pollution poses little or no risk.",
        "class": "text-success",
    },
    100: {
        "level": "Moderate",
        "text": "Air quality is acceptable; however, for some pollutants there may be a moderate health concern "
        "for a very small number of people who are unusually sensitive to air pollution.",
        "class": "text-warning",
    },
    150: {
        "level": "Unhealthy for Sensitive Groups",
        "text": "Members of sensitive groups may experience health effects. "
        "The general public is not likely to be affected.",
        "class": "text-warning",
    },
    200: {
        "level": "Unhealthy",
        "text": "Everyone may begin to experience health effects; "
        "members of sensitive groups may experience more serious health effects.",
        "class": "text-danger",
    },
    250: {
        "level": "Very Unhealthy",
        "text": "Health warnings of emergency conditions. The entire population is more likely to be affected.",
        "class": "text-danger",
    },
    300: {
        "level": "Hazardous",
        "text": "Health alert: everyone may experience more serious health effects.",
        "class": "text-danger",
    },
}


def selectplace(request, lat, long):
    # get the real time aqi data for this lat long
    aqi = f"https://api.waqi.info/feed/geo:{lat};{long}/?token=d3b715b3649e188d8531e4ce0ae79a0fd130ba46"
    response = requests.get(aqi, verify=False, timeout=2)
    if response:
        response = response.json()
        data = {
            "aqi": response["data"]["aqi"],
            "station": response["data"]["city"]["name"],
        }

        data["dominentpol"] = (
            response["data"]["dominentpol"]
            if response["data"]["dominentpol"]
            else "pm25"
        )

        # get aqi description
        for k, v in aqi_desc.items():
            if k > int(data["aqi"]):
                data["aqi_desc"] = v
                break

        # find the name of the city from the station name
        with open("data/airquality-covid19-cities.json", "r") as f:
            cities = json.loads(f.read())

        # readjust cities to make stations the keys
        cities = reduce(
            lambda x, y: {**x, **y},
            list(
                map(
                    lambda x: {
                        k["Name"]: {
                            "city": x["Place"]["name"],
                            "country": x["Place"]["country"],
                        }
                        for k in x["Stations"]
                    },
                    cities["data"],
                )
            ),
        )

        # our city of focus...
        city = cities[data["station"]]
        data["city"] = city["city"]

        # get parquet file
        df = pd.read_parquet(f"data/AQI_Data-{date.today()}.parquet")
        df = df[df["City"] == city["city"]].sort_index(ascending=False)
        df = df[df["Specie"].isin(["pm10", "pm25"])]
        df = df.pivot(index=None, columns="Specie", values="median")
        df.fillna(0, inplace=True)
        df.sort_index(inplace=True, ascending=False)
        last_7_days = df.iloc[:6]

        df["month"] = df.index.strftime("%Y-%m")

        df_month = df.groupby("month").agg("mean")

        last_7_days_bar = px.bar(last_7_days, title="Last 7 Days", barmode="group")
        month_bar = px.bar(df_month, title="Monthly", barmode="group")
        data["last_7_days_bar"] = plot(last_7_days_bar, output_type="div")
        data["month_bar"] = plot(month_bar, output_type="div")

        # check that the response
    return render(request, "subscribe/select_place.html", {"data": data})


def subscribeplace(request, city, dominentpol):
    data = {
        "city": city,
        "dominentpol": dominentpol,
    }
    data["tz"] = pytz.all_timezones
    return render(request, "subscribe/subscribe_place.html", {"data": data})


time_of_day = {
    "M": 8,
    "A": 12,
    "E": 16,
}


def confirmsubscription(request):
    subscription = Subscription()
    subscription.email = request.POST["email"]
    temp_token = "".join(random.choices(string.ascii_letters + string.digits, k=24))
    subscription.temp_token = temp_token
    subscription.city = request.POST["city"]
    subscription.dominentpol = request.POST["dominentpol"]

    today = datetime.now(tz=pytz.utc)
    tz = pytz.timezone(request.POST["timezone"])
    loc_time = datetime(
        today.year, today.month, today.day, time_of_day[request.POST["timeofday"]], 0, 0
    )
    loc_time = tz.localize(loc_time)
    utc_time = loc_time.astimezone(pytz.utc)
    if utc_time <= today:
        utc_time = utc_time + timedelta(days=1)

    subscription.next_email_date = utc_time

    try:
        subscription.save()
    except:  # noqa: E722
        raise Http404("Sorry! This request is invalid!")

    data = {"subscription_id": subscription.pk, "token": temp_token}
    data["host"] = request.META["HTTP_ORIGIN"]
    # send an email to verify this

    html = render_to_string("subscribe/confirm_email_template.html", {"data": data})
    message = Mail(
        from_email="sahilsakhuja85@gmail.com",
        to_emails=request.POST["email"],
        subject="Confirm your subscription from WarmMail",
        html_content=html,
    )
    try:
        sg = SendGridAPIClient(env.str("SENDGRID_API_KEY"))
        sg.send(message)
    except Exception as e:
        print(e.message)
    return render(request, "subscribe/confirm_subscription.html", {"data": data})


def verifyemail(request, subscription_id, token):
    subscription = get_object_or_404(Subscription, pk=subscription_id)
    if subscription.temp_token == token:
        # alles gut!
        subscription.verified = True
        subscription.update_date = date.today()
        subscription.save()
        data = {
            "message": f"Great! Your email address has been verified. "
            f"You will start receiving AQI updates for {subscription.city} in 24 hours!",
        }
        return render(request, "subscribe/email_confirmed.html", {"data": data})
    elif subscription.verified:
        data = {
            "message": "This subscription is already verified!",
        }
        return render(request, "subscribe/email_confirmed.html", {"data": data})
    else:
        raise Http404("Sorry! This request is invalid!")
