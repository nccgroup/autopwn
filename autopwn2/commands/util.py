import click
import json
import requests


def get(url, data={}, debug=False):
    if debug:
        click.echo('[*] Getting URL: %s' % url)
    response = requests.get(url, data)
    return json.loads(response.text)


def post(url, data={}, debug=False):
    if debug:
        click.echo('[*] Sending data to: %s' % url)
    response = requests.post(url, json=data)
    return json.loads(response.text)


def put(url, data={}, debug=False):
    if debug:
        click.echo('[*] Sending data to: %s' % url)
    response = requests.put(url, json=data)
    return json.loads(response.text)