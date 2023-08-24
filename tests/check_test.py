import random
import string
import datetime
from typing import List
import json
import copy

import pytest
from httpx import AsyncClient

from main import app


def generate_random_value(length: int = 10) -> str:
    characters = string.ascii_letters + string.digits
    value = ''.join(random.choice(characters) for _ in range(length))

    return value


ANSWERS = {
    "total": 18.75, "rest": 11.25, "payment": {"amount": 30.0, "type": "cash"}, "buyer_name": "FOP Pytest 1",
    "products": [
        {"name": "Phone", "price": 10.0, "quantity": 1, "total": 10.0},
        {"name": "Banana", "price": 0.5, "quantity": 10, "total": 5.0},
        {"name": "Apple", "price": 0.75, "quantity": 5, "total": 3.75}
    ]
}
EMAIL = f"test_{generate_random_value()}@example.com"
USER_NAME = f"test_{generate_random_value()}"
PASSWORD = f"test_{generate_random_value()}"

CREATE_USER_CREDS = {
    "email": EMAIL,
    "username": USER_NAME,
    "password": PASSWORD
}

CREATE_USER_CREDS_WRONG_EMAIL = {
    "email": EMAIL,
    "username": "test_user",
    "password": "test_password"
}

CREATE_USER_CREDS_WRONG_USERNAME = {
    "email": "test@example.com",
    "username": USER_NAME,
    "password": "test_password"
}

LOGIN_USER_CREDS = {
    "username": USER_NAME,
    "password": PASSWORD
}
WRONG_LOGIN_USER_CREDS = {
    "username": "test_user",
    "password": "test_password"
}


@pytest.mark.asyncio
async def test_full_user_life_circle(
        test_created_user,
        test_read_all,
        test_create_check
):
    await anext(test_created_user)
    await test_create_check
    await test_read_all
    await anext(test_created_user)


@pytest.mark.asyncio
async def test_html_check_not_found(test_client):
    client = await anext(test_client)
    response = await client.get("/checks/-1/signature/")
    response_data = response.json()
    assert response.status_code == 400
    assert response_data["detail"] == "Invalid signature"


@pytest.mark.asyncio
async def test_login_wrong_creds(test_client):
    client = await anext(test_client)
    for key in LOGIN_USER_CREDS:
        creds = {**LOGIN_USER_CREDS}
        del creds[key]
        token_response = await client.post("/login/", data=creds)
        response_data = token_response.json()
        assert token_response.status_code == 422
        assert response_data["detail"][0]["msg"] == "field required"


@pytest.mark.asyncio
async def test_create_check_bad_payload(test_client, test_access_token, test_created_user):
    await anext(test_created_user)
    token = await anext(test_access_token)
    payload, headers = prepare_create_check_request(token)
    client = await anext(test_client)
    for key1 in payload:
        if key1 == "comment":
            continue
        bad_payload = copy.deepcopy(payload)
        if key1 == "products" in ["products", "payment"]:
            for key2 in payload[key1][0]:
                bad_payload[key1][0] = copy.deepcopy(payload[key1][0])
                del bad_payload[key1][0][key2]
                await check_bad_check_creating_request(client, bad_payload, headers)
        elif key1 == "payment":
            for key2 in payload[key1]:
                bad_payload[key1] = copy.deepcopy(payload[key1])
                del bad_payload[key1][key2]
                await check_bad_check_creating_request(client, bad_payload, headers)
        else:
            del bad_payload[key1]
            await check_bad_check_creating_request(client, bad_payload, headers)
    await anext(test_created_user)


async def check_bad_check_creating_request(client, wrong_payload, headers):
    response = await client.post("/checks/", json=wrong_payload, headers=headers)
    response_data = response.json()
    assert response.status_code == 422
    assert response_data["detail"][0]["msg"] == "field required"


@pytest.mark.asyncio
async def test_create_user_bad_payload(test_client):
    client = await anext(test_client)
    for key in CREATE_USER_CREDS:
        creds = {**CREATE_USER_CREDS}
        del creds[key]
        response = await client.post("/sign-up/", json=creds)
        response_data = response.json()
        assert response.status_code == 422
        assert response_data["detail"][0]["msg"] == "field required"


@pytest.mark.asyncio
async def test_login_bad_payload(test_client):
    client = await anext(test_client)
    for key in CREATE_USER_CREDS:
        creds = {**CREATE_USER_CREDS}
        del creds[key]
        response = await client.post("/login/", json=creds)
        response_data = response.json()
        assert response.status_code == 422
        assert response_data["detail"][0]["msg"] == "field required"


@pytest.mark.asyncio
async def test_lock_endpoints_without_token(test_client):
    client = await anext(test_client)
    response = await client.delete("/unsubscribe/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    response = await client.get("/checks/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    payload, headers = prepare_create_check_request("")
    client = await anext(test_client)
    response = await client.post("/checks/", data=json.dumps(payload))
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_creads_already_exist(test_created_user, test_client):
    await anext(test_created_user)

    client = await anext(test_client)
    response = await client.post("/sign-up/", json=CREATE_USER_CREDS_WRONG_EMAIL)
    response_data = response.json()
    assert response.status_code == 400
    assert response_data["detail"] == "The email already exist"

    response = await client.post("/sign-up/", json=CREATE_USER_CREDS_WRONG_USERNAME)
    response_data = response.json()
    assert response.status_code == 400
    assert response_data["detail"] == "The username already exist"

    await anext(test_created_user)


@pytest.fixture
async def test_client():
    while True:
        async with AsyncClient(app=app, base_url="http://0.0.0.0:8000") as client:
            yield client


@pytest.fixture
async def test_created_user(test_client, test_access_token):
    client = await anext(test_client)
    response = await client.post("/sign-up/", json=CREATE_USER_CREDS)
    response_data = response.json()
    assert response.status_code == 201
    assert response_data["detail"] == "Created"
    assert isinstance(response_data["user_id"], int)

    yield None

    token = await anext(test_access_token)
    client = await anext(test_client)
    response = await client.delete("/unsubscribe/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 204

    yield None


@pytest.fixture
async def test_read_all(test_access_token, test_client):
    token = await anext(test_access_token)
    client = await anext(test_client)
    per_page, total_from = 5, 7
    payment_type, date_from = "cash", "19/08/2023"
    response = await client.get(
        "/checks/",
        params={
            "page": 1, "per_page": per_page, "date_from": date_from,
            "payment_type": payment_type, "total_from": total_from
        },
        headers={"Authorization": f"Bearer {token}"})

    response_data = response.json()
    assert response.status_code == 200
    assert isinstance(response_data["total_count"], int)
    assert isinstance(response_data["checks"], list)
    assert len(response_data["checks"]) <= per_page
    formatted_date_from = datetime.datetime.strptime(date_from, "%d/%m/%Y")
    for check in response_data["checks"]:
        check_products(check["products"])
        check_formatted_date_from = datetime.datetime.strptime(check["created_at"].split("T")[0], "%Y-%m-%d")
        assert str(check["check_id"]) in check["url"]
        assert check_formatted_date_from >= formatted_date_from
        assert ANSWERS["total"] >= total_from
        assert ANSWERS["rest"] == check["rest"]
        assert ANSWERS["buyer_name"] == check["buyer_name"]
        assert ANSWERS["payment"]["amount"] == check["payment_amount"]
        assert ANSWERS["payment"]["type"] == payment_type

        client = await anext(test_client)
        html_response = await client.get(check["url"])
        assert html_response.status_code == 200
        assert html_response.headers["Content-Type"] == "text/html; charset=utf-8"
        assert html_response.text


@pytest.fixture
async def test_access_token(test_client):
    while True:
        client = await anext(test_client)
        token_response = await client.post("/login/", data=LOGIN_USER_CREDS)
        token_response_data = token_response.json()
        assert token_response.status_code == 200
        assert token_response_data["access_token"] != "undefined"

        yield token_response_data["access_token"]


@pytest.fixture
async def test_create_check(test_access_token, test_client):
    token = await anext(test_access_token)
    payload, headers = prepare_create_check_request(token)
    client = await anext(test_client)
    response = await client.post("/checks/", headers=headers, data=json.dumps(payload))

    response_data = response.json()
    assert response.status_code == 201
    assert isinstance(response_data["products"], list)
    assert isinstance(response_data["payment"], dict)
    assert isinstance(response_data["payment"]["amount"], float)
    assert isinstance(response_data["payment"]["type"], str)
    assert isinstance(response_data["id"], int)
    assert isinstance(response_data["total"], float)
    assert isinstance(response_data["rest"], float)
    assert isinstance(response_data["created_at"], str)
    assert len(response_data["payment"]) == 2
    assert len(response_data["products"]) == 3
    assert len(response_data) == 7
    assert ANSWERS["total"] == response_data["total"]
    assert ANSWERS["rest"] == response_data["rest"]
    assert ANSWERS["buyer_name"] == response_data["buyer_name"]
    assert ANSWERS["payment"] == response_data["payment"]
    check_products(response_data["products"])


def check_products(products: List[dict]):
    for idx, product in enumerate(products):
        product_answers = ANSWERS["products"][idx]
        assert product_answers["name"] == product["name"]
        assert product_answers["price"] == product["price"]
        assert product_answers["quantity"] == product["quantity"]
        assert product_answers["total"] == product["total"]
        assert isinstance(product, dict)
        assert isinstance(product["name"], str)
        assert isinstance(product["price"], float)
        assert isinstance(product["quantity"], int)
        assert isinstance(product["total"], float)


def prepare_create_check_request(token: str):
    payload = {
        "products": [
            {
                "name": "Phone",
                "price": 10.0,
                "quantity": 1
            },
            {
                "name": "Banana",
                "price": 0.5,
                "quantity": 10
            },
            {
                "name": "Apple",
                "price": 0.75,
                "quantity": 5
            }
        ],
        "payment": {
            "type": "cash",
            "amount": 30.0
        },
        "comment": "Please, be happy!",
        "buyer_name": "FOP Pytest 1"
    }

    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    return payload, headers
