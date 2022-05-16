from app import db
from app.main import bp
from requests import get
from json import loads


def echo(username, api_key, resource_url):
    url = resource_url + '/rws/api/v1/echo/hello-world'
    my_response = get(url, auth=(username, api_key))
    if my_response:
        return "data", loads(my_response.content)
    else:
        return "error", my_response.status_code