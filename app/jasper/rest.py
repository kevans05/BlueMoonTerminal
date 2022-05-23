import datetime

from app import db
from app.main import bp
from requests import get
from json import loads
from urllib.parse import quote


def jasper_true_or_false(to_change):
    if to_change == 'true':
        return True
    else:
        return False


def get_rate_plan(username, apikey, url_hearer):
    url = url_hearer + "/rws/api/v1/rateplans"
    response = get(url, auth=(username, apikey))

    if response.ok:
        return "data", loads(response.content)['ratePlans']
    else:
        return "error", response.status_code


def echo(username, api_key, resource_url):
    url = resource_url + '/rws/api/v1/echo/hello-world'
    response = get(url, auth=(username, api_key))
    if response.ok:
        return "data", loads(response.content)
    else:
        return "error", response.status_code


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
            print(data)
            for zones in data['zones']:
                for devices in zones['devices']:
                    iemi_list.append({"iccid": devices['deviceId'], "dataUsage": devices['usage']['dataUsage'],
                                      "smsMOUsage": devices['usage']['smsMOUsage'],
                                      "smsMTUsage": devices['usage']['smsMTUsage'],
                                      "voiceMOUsage": devices['usage']['voiceMOUsage'],
                                      "voiceMTUsage": devices['usage']['voiceMTUsage'],
                                      "date_updated": datetime.datetime.now()})

            if data['lastPage']:
                return "data", iemi_list


def get_iccid_info(username, apikey, url_hearer, iccid):
    url = url_hearer + '/rws/api/v1/devices/' + iccid
    response = get(url, auth=(username, apikey))
    if response.ok:
        data = loads(response.content)
        return "data",  data
    else:
        return "error", response.status_code


def get_cycle_to_date(username, apikey, url_hearer, iccid):
    url_a = url_hearer + "/rws/api/v1/devices/"
    url_b = "/ctdUsages"
    url = url_a + iccid + url_b
    response = get(url, auth=(username, apikey))
    if response.ok:
        data = loads(response.content)
        return "data",  data
    else:
        return "error", response.status_code