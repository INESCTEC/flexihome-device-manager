# coding: utf-8

from __future__ import absolute_import
import unittest
import uuid
import json

from jsonschema import validate

from energy_manager_service.test import BaseTestCase
from energy_manager_service.test.schemas import RecommendationSchema

from energy_manager_service.test.mock.energy_manager import mock_energy_manager, clear_energy_manager, query_recommendation_by_id, query_recommendation_by_sequence_id_and_serial_number, mock_energy_manager2, create_available_flex, create_optimized_cicles

from energy_manager_service.test.helper_functions import register_super_user, superuser_login, mock_register

from datetime import datetime, timedelta, timezone

from energy_manager_service.test.helper_functions import METER_ID, METER_ID_WITHOUT_API_KEY

from energy_manager_service.test import (
    clear_all_db,
    setup_test_env
)


class TestFlexibilityRecommendationsDELETE(BaseTestCase):
    """FlexibilityRecommendationsController integration test stubs"""

    def test_happyflow(self):
        """Test case for flexibility_recommendations_delete

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
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == f"Recommendation {cycle.id} deleted."

        recommendation = query_recommendation_by_id(cycle.id)
        assert recommendation[12] == True

    def test_no_id_given(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers
        )
        self.assert400(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_only_sequence_id_given(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        query_string = [
            ('sequence_id', '123456'),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert400(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_only_serial_number_given(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        query_string = [
            ('serial_number', '123456'),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert400(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_not_found_recommendation_id_given(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        query_string = [
            ('recommendation_id', 123456),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert404(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_not_found_sequence_id_and_serial_number_given(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        query_string = [
            ('sequence_id', '123456'),
            ('serial_number', '123456'),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert404(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_delete_several_sequence_id_and_serial_number_given(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle1 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        cycle2 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        sequence_id = '1'
        serial_number = 'serial_number_example'

        query_string = [
            ('sequence_id', sequence_id),
            ('serial_number', serial_number),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == f"Recommendations of {sequence_id} for device {serial_number} deleted."

        recommendations = query_recommendation_by_sequence_id_and_serial_number(
            sequence_id, serial_number)
        assert len(recommendations) == 2
        for recommendation in recommendations:
            assert recommendation.cycle_cancelled_before_activation == True

    def test_delete_several_sequence_id_and_serial_number_given_2(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle1 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        cycle2 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        cycle3 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example_aux", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        cycle4 = create_optimized_cicles(flex.flex_id, 2, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        sequence_id = '1'
        serial_number = 'serial_number_example'

        query_string = [
            ('sequence_id', sequence_id),
            ('serial_number', serial_number),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == f"Recommendations of {sequence_id} for device {serial_number} deleted."

        recommendations = query_recommendation_by_sequence_id_and_serial_number(
            sequence_id, serial_number)
        assert len(recommendations) == 2
        for recommendation in recommendations:
            assert recommendation.cycle_cancelled_before_activation == True

        recommendations = query_recommendation_by_sequence_id_and_serial_number(
            sequence_id, "serial_number_example_aux")
        assert len(recommendations) == 1
        for recommendation in recommendations:
            assert recommendation.cycle_cancelled_before_activation == False

        recommendations = query_recommendation_by_sequence_id_and_serial_number(
            '2', serial_number)
        assert len(recommendations) == 1
        for recommendation in recommendations:
            assert recommendation.cycle_cancelled_before_activation == False

    def test_delete_recommendation_id_given_with_authorization(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
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
                                        True, 'up', False, False, True, '', False)

        query_string = [
            ('recommendation_id', cycle.id),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == f"Recommendation {cycle.id} deleted."

        recommendation = query_recommendation_by_id(cycle.id)
        assert recommendation[12] == True

    def test_delete_several_sequence_id_and_serial_number_given_with_authorization(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        authorization = superuser_login(id=user_key)

        flex = create_available_flex(user_id, 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle1 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        cycle2 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        sequence_id = '1'
        serial_number = 'serial_number_example'

        query_string = [
            ('sequence_id', sequence_id),
            ('serial_number', serial_number),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        decoded_response = json.loads(response.data.decode('utf-8'))
        print(decoded_response)
        assert isinstance(decoded_response, str)

        assert decoded_response == f"Recommendations of {sequence_id} for device {serial_number} deleted."

        recommendations = query_recommendation_by_sequence_id_and_serial_number(
            sequence_id, serial_number)
        assert len(recommendations) == 2
        for recommendation in recommendations:
            assert recommendation.cycle_cancelled_before_activation == True

    def test_delete_wrong_recommendation_id_given_with_authorization(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        authorization = superuser_login(id=user_key)

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
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert403(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_delete_several_wrong_sequence_id_and_serial_number_given_with_authorization(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        authorization = superuser_login(id=user_key)

        flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle1 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        cycle2 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        sequence_id = '1'
        serial_number = 'serial_number_example'

        query_string = [
            ('sequence_id', sequence_id),
            ('serial_number', serial_number),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert403(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_delete_several_sequence_id_and_serial_number_given_with_authorization_2(self):
        """Test case for flexibility_recommendations_delete

        Gather optimized cycle recommendations by user from today onward
        """
        clear_all_db()
        clear_energy_manager()

        user_key, user_id, second_user_key, second_user_id = mock_register()

        authorization = superuser_login(id=user_key)

        flex = create_available_flex(user_id, 'meter_id_example', datetime.now(timezone.utc),
                                     True, True, True, True, True, True)

        cycle1 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        cycle2 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        flex_aux = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
                                         True, True, True, True, True, True)

        cycle3 = create_optimized_cicles(flex_aux.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        cycle4 = create_optimized_cicles(flex_aux.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=3),
                                         datetime.now(timezone.utc) +
                                         timedelta(hours=6),
                                         True, 'up', False, False, True, '', False)

        sequence_id = '1'
        serial_number = 'serial_number_example'

        query_string = [
            ('sequence_id', sequence_id),
            ('serial_number', serial_number),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
            "Authorization": authorization,
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert200(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

        recommendations = query_recommendation_by_sequence_id_and_serial_number(
            sequence_id, serial_number)
        assert len(recommendations) == 4
        for recommendation in recommendations:
            if recommendation.flex_id == flex_aux.flex_id:
                assert recommendation.cycle_cancelled_before_activation == False
            else:
                assert recommendation.cycle_cancelled_before_activation == True

    def test_already_deleted_recommendation_id_given(self):
        """Test case for flexibility_recommendations_delete

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
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert404(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    def test_already_deleted_sequence_id_and_serial_number_given(self):
        """Test case for flexibility_recommendations_delete

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
            ('sequence_id', '1'),
            ('serial_number', 'serial_number_example'),
        ]
        headers = {
            'Accept': 'application/json',
            'X-Correlation-ID': str(uuid.uuid4()),
        }
        response = self.client.open(
            '/api/energy_manager_service/flexibility/recommendations',
            method='DELETE',
            headers=headers,
            query_string=query_string
        )
        self.assert404(response, 'Response body is : ' +
                       response.data.decode('utf-8'))

    # def test_delete_several_wrong_sequence_id_and_serial_number_given_with_authorization_2(self):
    #     """Test case for flexibility_recommendations_delete

    #     Gather optimized cycle recommendations by user from today onward
    #     """
    #     clear_all_db()
    #     clear_energy_manager()

    #     user_key, user_id, second_user_key, second_user_id = mock_register()

    #     authorization = superuser_login(id=user_key)

    #     flex = create_available_flex('1234567890', 'meter_id_example', datetime.now(timezone.utc),
    #                                  True, True, True, True, True, True)

    #     cycle1 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
    #                                      datetime.now(timezone.utc) +
    #                                      timedelta(hours=3),
    #                                      datetime.now(timezone.utc) +
    #                                      timedelta(hours=6),
    #                                      True, 'up', False, False, True, '', False)

    #     cycle2 = create_optimized_cicles(flex.flex_id, 1, "serial_number_example", datetime.now(timezone.utc)-timedelta(days=1),
    #                                      datetime.now(timezone.utc) +
    #                                      timedelta(hours=3),
    #                                      datetime.now(timezone.utc) +
    #                                      timedelta(hours=6),
    #                                      True, 'up', False, False, True, '', False)

    #     sequence_id = '1'
    #     serial_number = 'serial_number_example'

    #     query_string = [
    #         ('sequence_id', sequence_id),
    #         ('serial_number', serial_number),
    #     ]
    #     headers = {
    #         'Accept': 'application/json',
    #         'X-Correlation-ID': str(uuid.uuid4()),
    #         "Authorization": authorization,
    #     }
    #     response = self.client.open(
    #         '/api/energy_manager_service/flexibility/recommendations',
    #         method='DELETE',
    #         headers=headers,
    #         query_string=query_string
    #     )
    #     self.assert403(response, 'Response body is : ' +
    #                    response.data.decode('utf-8'))

    #     recommendations = query_recommendation_by_sequence_id_and_serial_number(
    #         sequence_id, serial_number)
    #     assert len(recommendations) == 2
    #     for recommendation in recommendations:
    #         assert recommendation.cycle_cancelled_before_activation == False


if __name__ == '__main__':
    unittest.main()
