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


class TestFlexibilityRecommendationsPOST(BaseTestCase):
    """FlexibilityRecommendationsController integration test stubs"""

    def test_happyflow(self):
        """Test case for flexibility_recommendations_post

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=3),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=6),
                                        True, 'up', False, False, True, '', False)

        query_string = [
            ('recommendation_id', cycle.id),
            # ('accepted', False)
        ]
        body = {
            'delay_call_ok': True
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=body
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == f"Recommendation {cycle.id} was accepted by the user"

        recommendation = query_recommendation_by_id(cycle.id)
        # print(recommendation)
        assert recommendation[8] == True
        assert recommendation[10] == True
        assert recommendation[11] == ''

    def test_no_optimized_cycle(self):
        """Test case for flexibility_recommendations_post

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        query_string = [
            ('recommendation_id', 1234),
            # ('accepted', False)
        ]
        body = {
            'delay_call_ok': True
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=body
        )
        self.assert404(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_flexibility_recommendation_post_old_timestamp(self):
        """Test case for flexibility_recommendations_post

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                        datetime.now(timezone.utc) -
                                        timedelta(hours=3),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=6),
                                        True, 'up', False, False, True, '', False)

        query_string = [
            ('recommendation_id', cycle.id),
            # ('accepted', False)
        ]
        body = {
            'delay_call_ok': True
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=body
        )
        self.assert404(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_flexibility_recommendation_post_already_accepted(self):
        """Test case for flexibility_recommendations_post

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=3),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=6),
                                        True, 'up', False, False, True, '', False)

        query_string = [
            ('recommendation_id', cycle.id),
            # ('accepted', False)
        ]
        body = {
            'delay_call_ok': True
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=body
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == f"Recommendation {cycle.id} was accepted by the user"

        recommendation = query_recommendation_by_id(cycle.id)
        # print(recommendation)
        assert recommendation[8] == True

        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=body
        )
        assert response.status_code == 202

    def test_flexibility_recommendation_post_with_delay_call_ok_false(self):
        """Test case for flexibility_recommendations_post

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=3),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=6),
                                        True, 'up', False, False, True, '', False)

        query_string = [
            ('recommendation_id', cycle.id),
            # ('accepted', False)
        ]
        body = {
            'delay_call_ok': False,
            # 'delay_call_description': "Test123"
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=body
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == f"Recommendation {cycle.id} was accepted by the user"

        recommendation = query_recommendation_by_id(cycle.id)
        # print(recommendation)
        assert recommendation[8] == True
        assert recommendation[10] == False
        assert recommendation[11] == None

    def test_flexibility_recommendation_post_with_delay_call_ok_true(self):
        """Test case for flexibility_recommendations_post

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=3),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=6),
                                        True, 'up', False, False, False, '', False)

        query_string = [
            ('recommendation_id', cycle.id),
            # ('accepted', False)
        ]
        body = {
            'delay_call_ok': True,
            # 'delay_call_description': "Test123"
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=body
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == f"Recommendation {cycle.id} was accepted by the user"

        recommendation = query_recommendation_by_id(cycle.id)
        # print(recommendation)
        assert recommendation[8] == True
        assert recommendation[10] == True
        assert recommendation[11] == ''

    def test_flexibility_recommendation_post_with_delay_call_description(self):
        """Test case for flexibility_recommendations_post

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=3),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=6),
                                        True, 'up', False, False, False, '', False)

        query_string = [
            ('recommendation_id', cycle.id),
            # ('accepted', False)
        ]
        body = {
            'delay_call_ok': False,
            'delay_call_description': "Test123"
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            # 'Authorization': 'Bearer special-key'
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=body
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == f"Recommendation {cycle.id} was accepted by the user"

        recommendation = query_recommendation_by_id(cycle.id)
        # print(recommendation)
        assert recommendation[8] == True
        assert recommendation[10] == False
        assert recommendation[11] == "Test123"

    def test_flexibility_recommendations_post_with_authorization(self):
        clear_all_db()
        clear_energy_manager()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        authorization = superuser_login(id=user_key)

        flex = create_available_flex(user_id, 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=3),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=6),
                                        True, 'up', False, False, False, '', False)

        query_string = [
            ('recommendation_id', cycle.id),
            # ('accepted', False)
        ]
        body = {
            'delay_call_ok': True
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=body
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))
        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == f"Recommendation {cycle.id} was accepted by the user"

        recommendation = query_recommendation_by_id(cycle.id)
        # print(recommendation)
        assert recommendation[8] == True
        assert recommendation[10] == True
        assert recommendation[11] == ''

    def test_flexibility_recommendations_post_with_authorization_wrong_cycle_id(self):
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=3),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=6),
                                        True, 'up', False, False, False, '', False)

        user_key, user_id, second_user_key, second_user_id = mock_register()

        authorization = superuser_login(id=user_key)

        query_string = [
            ('recommendation_id', cycle.id),
            # ('accepted', False)
        ]
        body = {
            'delay_call_ok': True
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=body
        )
        self.assert403(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_flexibility_recommendations_post_after_delete(self):
        """Test case for flexibility_recommendations_post

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=3),
                                        datetime.now(timezone.utc) +
                                        timedelta(hours=6),
                                        True, 'up', False, False, True, '', True)

        query_string = [
            ('recommendation_id', cycle.id),
        ]
        body = {
            'delay_call_ok': True
        }
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations/accept',
            method='POST',
            headers=headers,
            query_string=query_string,
            json=body
        )
        self.assert404(response, 'Response body is : ' +
                       response.data.decode('utf-8'))


if __name__ == '__main__':
    unittest.main()
