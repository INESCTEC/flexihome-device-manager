# coding: utf-8

from __future__ import absolute_import
import unittest
import uuid
import json

from jsonschema import validate

from energy_manager_service.test import BaseTestCase
from energy_manager_service.test.schemas import RecommendationSchema

from energy_manager_service.test.mock.energy_manager import mock_energy_manager, clear_energy_manager, query_recommendation_by_id, mock_energy_manager2, create_available_flex, create_optimized_cicles

from energy_manager_service.test.helper_functions import register_super_user, superuser_login, mock_register

from datetime import datetime, timedelta, timezone

from energy_manager_service.test.helper_functions import METER_ID, METER_ID_WITHOUT_API_KEY

from energy_manager_service.test import (
    clear_all_db,
    setup_test_env
)


class TestFlexibilityRecommendationsGET(BaseTestCase):
    """FlexibilityRecommendationsController integration test stubs"""

    def test_happyflow(self):
        """Test case for flexibility_recommendations_get

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()
        mock_energy_manager2()

        query_string = [
            ('user_id', '1234567890'),
            # ('accepted', False)
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, list)
        validate(decoded_response[0], RecommendationSchema)

        assert len(decoded_response) == 1
        assert int(decoded_response[0]['sequence_id']) == 1

        recommendation = query_recommendation_by_id(
            decoded_response[0]['recommendation_id'])
        print(recommendation)
        assert recommendation[0] == decoded_response[0]['recommendation_id']

    def test_no_optimized_cycles(self):
        """Test case for flexibility_recommendations_get

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        query_string = [
            ('user_id', '1234567890'),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        decoded_response = json.loads(response.data.decode('utf-8'))
        assert response.status_code == 202

        assert isinstance(decoded_response, str)

    def test_flexibility_recommendations_get(self):
        """Test case for flexibility_recommendations_get

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()
        mock_energy_manager2()

        query_string = [
            ('user_id', '1234567890'),
            # ('accepted', False)
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, list)
        validate(decoded_response[0], RecommendationSchema)

        assert len(decoded_response) == 1
        assert int(decoded_response[0]['sequence_id']) == 1

        recommendation = query_recommendation_by_id(
            decoded_response[0]['recommendation_id'])
        print(recommendation)
        assert recommendation[0] == decoded_response[0]['recommendation_id']

    def test_flexibility_recommendations_get_previous_day_timestamp(self):
        """Test case for flexibility_recommendations_get

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                        datetime.now(timezone.utc) -
                                        timedelta(days=1, hours=3),
                                        datetime.now(timezone.utc) +
                                        timedelta(days=1, hours=1),
                                        True, 'up', True, False, True, '', False)

        query_string = [
            ('user_id', '1234567890'),
            # ('accepted', False)
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        # self.assert202(response, 'Response body is : ' +
        #                response.data.decode('utf-8'))

        assert response.status_code == 202

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == "No optimized cycles for user 1234567890"
        # validate(decoded_response[0], RecommendationSchema)

        # assert len(decoded_response) == 0
        # assert int(decoded_response[0]['sequence_id']) == 1

        # recommendation = query_recommendation_by_id(
        #     decoded_response[0]['recommendation_id'])
        # print(recommendation)
        # assert recommendation[0] == decoded_response[0]['recommendation_id']

    def test_flexibility_recommendations_get_old_timestamp(self):
        """Test case for flexibility_recommendations_get

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)+timedelta(hours=10),
                                        datetime.now(timezone.utc) -
                                        timedelta(minutes=5),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=2),
                                        True, 'up', True, False, True, '', False)

        query_string = [
            ('user_id', '1234567890'),
            # ('accepted', False)
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        # print(decoded_response)
        assert isinstance(decoded_response, list)
        validate(decoded_response[0], RecommendationSchema)

        # assert len(decoded_response) == 0
        assert int(decoded_response[0]['sequence_id']) == 1

        recommendation = query_recommendation_by_id(
            decoded_response[0]['recommendation_id'])
        # print(recommendation)
        assert recommendation[0] == decoded_response[0]['recommendation_id']

    def test_flexibility_recommendations_get_old_timestamp_not_accepted_by_user(self):
        """Test case for flexibility_recommendations_get

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)+timedelta(hours=10),
                                        datetime.now(timezone.utc) -
                                        timedelta(minutes=5),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=2),
                                        True, 'up', False, False, True, '', False)

        query_string = [
            ('user_id', '1234567890'),
            # ('accepted', False)
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        assert response.status_code == 202

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == "No optimized cycles for user 1234567890"

    def test_flexibility_recommendations_get_good_timestamp_not_accepted_by_user(self):
        """Test case for flexibility_recommendations_get

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)+timedelta(hours=10),
                                        datetime.now(timezone.utc) +
                                        timedelta(minutes=5),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=2),
                                        True, 'up', False, False, True, '', False)

        query_string = [
            ('user_id', '1234567890'),
            # ('accepted', False)
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        # print(decoded_response)
        assert isinstance(decoded_response, list)
        validate(decoded_response[0], RecommendationSchema)

        # assert len(decoded_response) == 0
        assert int(decoded_response[0]['sequence_id']) == 1

        recommendation = query_recommendation_by_id(
            decoded_response[0]['recommendation_id'])
        # print(recommendation)
        assert recommendation[0] == decoded_response[0]['recommendation_id']

    def test_flexibility_recommendations_get_different_flex_type(self):
        """Test case for flexibility_recommendations_get

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)+timedelta(hours=10),
                                        datetime.now(timezone.utc) -
                                        timedelta(minutes=5),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=2),
                                        True, 'baseline', True, False, True, '', False)

        query_string = [
            ('user_id', '1234567890'),
            # ('accepted', False)
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        assert response.status_code == 202

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == "No optimized cycles for user 1234567890"

    def test_flexibility_recommendations_get_empty_available_flex(self):
        clear_all_db()
        clear_energy_manager()

        query_string = [
            ('user_id', '1234567890')
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        assert response.status_code == 202

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == "No available flexibility for user 1234567890"

        # assert len(decoded_response) == 0

    def test_flexibility_recommendations_get_empty_optimized_cycles(self):
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        query_string = [
            ('user_id', '1234567890')
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        assert response.status_code == 202

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)
        assert decoded_response == "No optimized cycles for user 1234567890"

        # assert len(decoded_response) == 0

    def test_flexibility_recommendations_get_with_authorization(self):
        clear_all_db()
        clear_energy_manager()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        authorization = superuser_login(id=user_key)

        flex = create_available_flex(user_id, 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)+timedelta(hours=10),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=1),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=2),
                                        True, 'up', False, False, True, '', False)

        query_string = [
            ('user_id', user_id),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_flexibility_recommendations_get_with_authorization_wrong_userid(self):
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)+timedelta(hours=10),
                                        datetime.now(timezone.utc) -
                                        timedelta(hours=1),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=2),
                                        True, 'baseline', True, False, True, '', False)

        user_key, user_id, second_user_key, second_user_id = mock_register()

        authorization = superuser_login(id=user_key)

        query_string = [
            ('user_id', '1234567890'),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert403(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_flexibility_recommendations_get_after_delete(self):
        """Test case for flexibility_recommendations_get

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)+timedelta(hours=10),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=1),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=2),
                                        True, 'up', True, False, True, '', True)

        query_string = [
            ('user_id', '1234567890'),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        assert response.status_code == 202

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == "No optimized cycles for user 1234567890"

    def test_flexibility_recommendations_get_accepted_false(self):
        """Test case for flexibility_recommendations_get

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)+timedelta(hours=10),
                                        datetime.now(timezone.utc) +
                                        timedelta(minutes=5),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=2),
                                        True, 'up', False, False, True, '', False)

        query_string = [
            ('user_id', '1234567890'),
            ('accepted', False)
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        # print(decoded_response)
        assert isinstance(decoded_response, list)
        validate(decoded_response[0], RecommendationSchema)

        # assert len(decoded_response) == 0
        assert int(decoded_response[0]['sequence_id']) == 1

        recommendation = query_recommendation_by_id(
            decoded_response[0]['recommendation_id'])
        # print(recommendation)
        assert recommendation[0] == decoded_response[0]['recommendation_id']

    def test_flexibility_recommendations_get_accepted_true(self):
        """Test case for flexibility_recommendations_get

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)+timedelta(hours=10),
                                        datetime.now(timezone.utc) +
                                        timedelta(minutes=5),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=2),
                                        True, 'up', True, False, True, '', False)

        query_string = [
            ('user_id', '1234567890'),
            ('accepted', True)
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='GET',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        # print(decoded_response)
        assert isinstance(decoded_response, list)
        validate(decoded_response[0], RecommendationSchema)

        # assert len(decoded_response) == 0
        assert int(decoded_response[0]['sequence_id']) == 1

        recommendation = query_recommendation_by_id(
            decoded_response[0]['recommendation_id'])
        # print(recommendation)
        assert recommendation[0] == decoded_response[0]['recommendation_id']


if __name__ == '__main__':
    unittest.main()
