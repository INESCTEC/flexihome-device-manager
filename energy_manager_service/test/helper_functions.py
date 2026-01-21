# coding: utf-8

from __future__ import absolute_import

from time import sleep
import uuid

from flask import json
import requests
from energy_manager_service.test.config import Config
from energy_manager_service import db

import asyncio
import string
import secrets

import psycopg2, sys


METER_ID = "NLV_CLIENT_8585"
METER_ID_WITHOUT_API_KEY = "NLV_CLIENT_9564"
API_KEY = "XXX"


def id_generator(size, chars=string.ascii_lowercase + string.digits):
    return ''.join(secrets.SystemRandom().choice(chars) for _ in range(size))


def register_super_user(id="aa", meter_id=METER_ID):
    body = {
        "first_name": "Test",
        "last_name": "Test",
        "email": f"riscas.cat1+{id}@gmail.com",
        "password": "123456",
        "password_repeat": "123456",
        "meter_id": meter_id,
        "country": "PT",
        "postal_code": "4450-001",
        "tarif_type": "simple",
        "contracted_power": "6.9 kVA",
        "schedule_type": "economic",
    }

    register_data = json.dumps(body)
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": "b2fdda1b-9550-4afd-9b3d-d180a6398986",
    }

    print("REGISTERING USER....")
    new_user = requests.post(
        url=Config.ACCOUNT_MANAGER_ENDPOINT + "/register",
        data=register_data,
        headers=headers,
    )
    # new_user = requests.post(url="http://account-manager-test:8080/api/account"+ "/register", data=register_data, headers=headers)
    print(new_user.content)
    print("REGISTERING USER.... OK!")

    new_user_id = json.loads(new_user.content)["user_id"]
    print(new_user_id)

    print("Activate User Account")
    # DBConfirmationToken.query.filter_by(user_id=new_user_id).delete()
    # user = DBUser.query.filter_by(user_id=new_user_id).first()
    # user.is_active = True
    # user.settings.permissions = "Full"

    conn_account = psycopg2.connect(
        database = "account_manager", 
        user = Config.DATABASE_USER, 
        host= Config.DATABASE_IP,
        password = Config.DATABASE_PASSWORD,
        port = Config.DATABASE_PORT
    )
    
    tries = 0
    max_tries = 3

    with conn_account:
        with conn_account.cursor() as cur:
            while tries < max_tries:
                cur = conn_account.cursor()
                cur.execute(f'SELECT token FROM confirmation_tokens WHERE user_id = \'{new_user_id}\';')
                token = cur.fetchone()
                
                if token is not None:
                    token = token[0]
                    break
                
                sleep(5)
                tries += 1

    r = requests.post(
        url=f'{Config.ACCOUNT_MANAGER_ENDPOINT}/confirm-account/{token}'
    )
    r.raise_for_status()

    print(f"User Confirmed... {r.status_code}")

    return new_user_id


def superuser_login(id="aa", email=None, password=None):
    if email is None:
        email = f"riscas.cat1+{id}@gmail.com"
    if password is None:
        password = "123456"
    login_data = json.dumps(
        {"email": email, "password": password}
    )
    headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": "b2fdda1b-9550-4afd-9b3d-d180a6398986",
    }

    user_login = requests.post(
        url=Config.ACCOUNT_MANAGER_ENDPOINT + "/login", data=login_data, headers=headers
    )
    print(user_login.headers)

    return user_login.headers["authorization"]


def mock_register(user_key=None, meter_id=METER_ID):
    # clean_account()

    # Key to create a new unique user in the db
    # user_key = "aa"  # Must have 2 leters, because of the CPE naming convention
    if user_key == None:
        user_key = id_generator(3)

    user_id = register_super_user(
        id=user_key,
        meter_id=meter_id
    )  # The randomly generated ID by the account manager

    sleep(1)

    second_user_key = user_key + "b"
    second_user_id = register_super_user(
        id=second_user_key, meter_id=METER_ID_WITHOUT_API_KEY)

    sleep(1)

    return user_key, user_id, second_user_key, second_user_id
