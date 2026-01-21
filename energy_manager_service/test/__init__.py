import logging

import connexion
from flask_testing import TestCase

from flask_sqlalchemy import SQLAlchemy

from energy_manager_service.encoder import JSONEncoder

from energy_manager_service import Config

from energy_manager_service.test.clear_database import clear_all_db, clear_energy_prices_db
from energy_manager_service.test.setup_test_env import (
    setup_test_env,
    user_register_and_login,
    mock_forecast,
    mock_energy_prices,
    add_device,
    schedule_cycle,
    set_automatic_management_of_device
)

import string


alphabet = string.ascii_lowercase + string.digits


def random_choice():
    random.seed()
    return ''.join(random.choices(alphabet, k=8))


# conn_prices = psycopg2.connect(
#     database = "energyprices",
#     user = Config.DATABASE_USER,
#     host= Config.DATABASE_IP,
#     password = Config.DATABASE_PASSWORD,
#     port = Config.DATABASE_PORT
# )


class BaseTestCase(TestCase):

    def create_app(self):
        logging.getLogger('connexion.operation').setLevel('ERROR')

        connexionApp = connexion.App(__name__, specification_dir='../openapi/',
                                     options={"swagger_ui": False})
        connexionApp.app.json_encoder = JSONEncoder

        app = connexionApp.app
        app.config.from_object(Config)

        connexionApp.add_api('openapi.yaml',
                             arguments={'title': 'Energy Manager Service'},
                             pythonic_params=True,
                             validate_responses=True)

        # Setup Flask SQLAlchemy
        db = SQLAlchemy(app)

        db.create_all()

        return app
