# coding: utf-8

from __future__ import absolute_import

import psycopg2
import secrets
import string


from time import sleep
import uuid

from flask import json
import requests
import sys

sys.path.append('../../../..')
from energy_manager_service.models.database.energy_manager_db import DBAvailableFlexbility
from energy_manager_service import db
from energy_manager_service.config import Config

def clean_account():
    conn = psycopg2.connect(
        database="account_manager",
        user=Config.DATABASE_USER,
        host=Config.DATABASE_IP,
        password=Config.DATABASE_PASSWORD,
        port=Config.DATABASE_PORT
    )

    with conn:
        with conn.cursor() as cur:
            cur.execute(f'TRUNCATE TABLE users CASCADE;')
            cur.execute(f'TRUNCATE TABLE confirmation_tokens CASCADE;')
            cur.execute(f'TRUNCATE TABLE events CASCADE;')

    conn.close()


# def clean_device():
#     conn = psycopg2.connect(
#         database="devicemanager",
#         user=Config.DATABASE_USER,
#         host=Config.DATABASE_IP,
#         password=Config.DATABASE_PASSWORD,
#         port=Config.DATABASE_PORT
#     )

#     with conn:
#         with conn.cursor() as cur:
#             cur.execute(f'TRUNCATE TABLE db_shiftable_machine CASCADE;')
#             cur.execute(f'TRUNCATE TABLE db_not_disturbs CASCADE;')
#             cur.execute(f'TRUNCATE TABLE db_dongles CASCADE;')
#             cur.execute(f'TRUNCATE TABLE processed_events CASCADE;')

#     conn.close()


def clean_database():
    conn = psycopg2.connect(
        database="energy_manager",
        user=Config.DATABASE_USER,
        host=Config.DATABASE_IP,
        password=Config.DATABASE_PASSWORD,
        port=Config.DATABASE_PORT
    )

    with conn:
        with conn.cursor() as cur:
            cur.execute(f'TRUNCATE TABLE flexibility_available CASCADE;')
            cur.execute(f'TRUNCATE TABLE flexibility_vectors CASCADE;')
            cur.execute(f'TRUNCATE TABLE optimized_cycles CASCADE;')

    conn.close()


def confirm_all_users():
    conn = psycopg2.connect(
        database="account_manager",
        user=Config.DATABASE_USER,
        host=Config.DATABASE_IP,
        password=Config.DATABASE_PASSWORD,
        port=Config.DATABASE_PORT
    )

    with conn:
        with conn.cursor() as cur:
            cur.execute(f'UPDATE users SET is_active = true;')
            # cur.execute(f'TRUNCATE TABLE confirmation_tokens CASCADE;')
            # cur.execute(f'TRUNCATE TABLE events CASCADE;')

    conn.close()


def id_generator(size, chars=string.ascii_lowercase + string.digits):
    return ''.join(secrets.SystemRandom().choice(chars) for _ in range(size))


METER_IDS_WITH_API_KEY = ["NLV_CLIENT_8585",
                          "NLV_CLIENT_8813", "NLV_CLIENT_8819"]
METER_IDS_WITHOUT_API_KEY = ["NLV_CLIENT_9564", "NLV_CLIENT_9953"]


def register_super_user(id="aa", meter_id=METER_IDS_WITH_API_KEY[0]):
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
        url="http://localhost:8081/api/account/register",
        data=register_data,
        headers=headers,
    )
    # new_user = requests.post(url="http://account-manager-test:8080/api/account"+ "/register", data=register_data, headers=headers)
    print(new_user.content)
    print("REGISTERING USER.... OK!")

    new_user_id = json.loads(new_user.content)["user_id"]
    print(new_user_id)

    print("Activate User Account")
    confirm_all_users()

    return new_user_id


def superuser_login(id="aa", expo_token=None, email=None, password=None):
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
    if expo_token is not None:
        headers["expo-token"] = expo_token

    user_login = requests.post(
        url="http://localhost:8081/api/account/login", data=login_data, headers=headers
    )
    print(user_login.headers)

    return user_login.headers["authorization"]


def get_user(user_id):

    query_string = {"user-ids": [user_id]}
    headers = {
        "X-Correlation-ID": "b2fdda1b-9550-4afd-9b3d-d180a6398986",
    }
    response = requests.get(
        url="http://localhost:8081/api/account/user",
        headers=headers,
        params=query_string,
    )

    return json.loads(response.content)[0]


def mock_register(user_key=None, meter_id=METER_IDS_WITH_API_KEY[0], meter_id_2=METER_IDS_WITH_API_KEY[1], meter_id_3=METER_IDS_WITH_API_KEY[2]):
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
        id=second_user_key, meter_id=meter_id_2)

    sleep(1)

    third_user_key = user_key + "c"
    third_user_id = register_super_user(
        id=third_user_key, meter_id=meter_id_3)

    sleep(1)

    return user_key, user_id, second_user_key, second_user_id, third_user_key, third_user_id


def create_available_flex(
        user_id, meter_id, request_datetime, accepted_by_grid=True,
        baseline_call_ok=False, flex_up_call_ok=False, flex_down_call_ok=False,
        baseline_zeros=True, flex_up_zeros=True
):
    avai_flex = DBAvailableFlexbility(
        user_id=user_id,
        meter_id=meter_id,
        request_datetime=request_datetime,
        accepted_by_grid=accepted_by_grid,
        baseline_call_ok=baseline_call_ok,
        flex_up_call_ok=flex_up_call_ok,
        flex_down_call_ok=flex_down_call_ok,
        baseline_zeros=baseline_zeros,
        flex_up_zeros=flex_up_zeros)
    db.session.add(avai_flex)
    db.session.commit()

    return avai_flex
