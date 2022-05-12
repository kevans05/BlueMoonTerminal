from json import loads
from requests import get

def echo(username, api_key, resource_url):
    url = 'https://' + resource_url + '/rws/api/v1/echo/hello-world'
    my_response = get(url, auth=(username, api_key))
    if my_response:
        return "data", loads(my_response.content)
    else:
        return "error", my_response.status_code