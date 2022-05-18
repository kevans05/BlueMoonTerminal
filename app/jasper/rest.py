import datetime

from app import db
from app.main import bp
from requests import get
from json import loads
from urllib.parse import quote


def echo(username, api_key, resource_url):
    url = resource_url + '/rws/api/v1/echo/hello-world'
    response = get(url, auth=(username, api_key))
    if response:
        return "data", loads(response.content)
    else:
        return "error", response.status_code


def get_rate_plan(username, apikey, url_hearer):
    url = url_hearer + "/rws/api/v1/rateplans"
    response = get(url, auth=(username, apikey))

    if response.ok:
        data = loads(response.content)
        return (data['ratePlans'])
    else:
        return "error"


def get_usage_by_rate_plan(username, apikey, url_hearer, rate_plan):
    url_a = url_hearer + "/rws/api/v1/usages?ratePlanName="
    url_b = "&pageNumber="
    url_c = "&pageSize=50"
    i = 1
    iemi_list = []
    while True:
        url = url_a + quote(rate_plan) + url_b + str(i) + url_c
        i = i + 1
        response = get(url, auth=(username, apikey))
        if response.ok:
            data = loads(response.content)
            for zones in data['zones']:
                for devices in zones['devices']:
                    iemi_list.append({"imei": devices['deviceId'], "dataUsage": devices['usage']['dataUsage'],
                                      "smsMOUsage": devices['usage']['smsMOUsage'],
                                      "smsMTUsage": devices['usage']['smsMTUsage'],
                                      "voiceMOUsage": devices['usage']['voiceMOUsage'],
                                      "voiceMTUsage": devices['usage']['voiceMTUsage'],
                                      "date_updated": datetime.datetime.now()})

            if data['lastPage']:
                break
    return iemi_list
