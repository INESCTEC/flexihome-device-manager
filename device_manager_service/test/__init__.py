import logging

import connexion
from flask_testing import TestCase

from flask_sqlalchemy import SQLAlchemy

from device_manager_service.encoder import JSONEncoder
from device_manager_service.config import Config
# import device_manager_service.accountEventConsumers as ec
from device_manager_service.accountEventConsumers import AccountEventConsumers
# import unittest

# Setup Flask SQLAlchemy
db = SQLAlchemy()

# db.create_all()
# db.create_all(bind=['account_manager'])

class BaseTestCase(TestCase):

    def create_app(self):
        logging.getLogger('connexion.operation').setLevel('ERROR')

        print("Connexion app")

        # Setup Flask app
        connexionApp = connexion.App(__name__,
                                        specification_dir='../openapi/',
                                        options={"swagger_ui": False})
        connexionApp.app.json_encoder = JSONEncoder

        app = connexionApp.app
        app.config.from_object(Config)

        connexionApp.add_api('openapi.yaml',
                                arguments={'title': 'Device Manager Service'},
                                pythonic_params=True,
                                validate_responses=True)

        db.init_app(app)

        return app

    def setUp(self):
        db.drop_all()
        db.drop_all(bind=['account_manager'])
        
        db.create_all()
        db.create_all(bind=['account_manager'])

    def tearDown(self):
        # db.session.remove()
        db.drop_all()
        db.drop_all(bind=['account_manager'])

    @classmethod
    def setUpClass(cls):
        print("Account event consumers")
        cls.ec = AccountEventConsumers()
        print("Account event consumers start")
        cls.ec.start()

    @classmethod
    def tearDownClass(cls):
        print("Account event consumers stop")
        cls.ec.stop()


