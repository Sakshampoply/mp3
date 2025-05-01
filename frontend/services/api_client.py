import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BACKEND_URL")


def get_auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def handle_response(response):
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        try:
            return {"error": err.response.json().get("detail", str(err))}
        except:
            return {"error": str(err)}
    except Exception as e:
        return {"error": str(e)}


def api_get(endpoint, token=None):
    headers = get_auth_header(token) if token else {}
    response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
    return handle_response(response)


def api_post(endpoint, data=None, files=None, token=None):
    headers = get_auth_header(token) if token else {}
    try:
        if files:
            response = requests.post(
                f"{BASE_URL}{endpoint}", files=files, headers=headers
            )
        else:
            response = requests.post(
                f"{BASE_URL}{endpoint}", json=data, headers=headers
            )
        return handle_response(response)
    except Exception as e:
        return {"error": str(e)}


def api_put(endpoint, data, token=None):
    headers = get_auth_header(token) if token else {}
    response = requests.put(f"{BASE_URL}{endpoint}", json=data, headers=headers)
    return handle_response(response)


def api_delete(endpoint, token=None):
    headers = get_auth_header(token) if token else {}
    response = requests.delete(f"{BASE_URL}{endpoint}", headers=headers)
    return handle_response(response)
