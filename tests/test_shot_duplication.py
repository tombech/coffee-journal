"""
Tests for shot duplication functionality in shot sessions.
"""

import pytest
from datetime import datetime, timezone


class TestShotDuplication:
    """Test shot duplication from session context."""

    @pytest.fixture
    def test_user_id(self):
        return 'test_shot_duplication_user'

    @pytest.fixture
    def sample_data(self, client, test_user_id):
        """Create test data for duplication tests."""
        # Create product
        product_data = {
            'product_name': 'Test Coffee for Duplication',
            'roaster': 'Test Roaster',
            'bean_type': ['Arabica'],
            'country': 'Colombia'
        }
        product_response = client.post(f'/api/products?user_id={test_user_id}', json=product_data)
        assert product_response.status_code == 201
        product = product_response.get_json()

        # Create batch
        batch_data = {
            'roast_date': '2024-01-15',
            'amount_grams': 250,
            'price': 15.99
        }
        batch_response = client.post(f'/api/products/{product["id"]}/batches?user_id={test_user_id}', json=batch_data)
        assert batch_response.status_code == 201
        batch = batch_response.get_json()

        # Create brewer
        brewer_data = {'name': 'Test Brewer for Duplication'}
        brewer_response = client.post(f'/api/brewers?user_id={test_user_id}', json=brewer_data)
        assert brewer_response.status_code == 201
        brewer = brewer_response.get_json()

        # Create shot session
        session_data = {
            'title': 'Test Session for Duplication',
            'product_id': product['id'],
            'product_batch_id': batch['id'],
            'brewer_id': brewer['id'],
            'notes': 'Test session for shot duplication'
        }
        session_response = client.post(f'/api/shot_sessions?user_id={test_user_id}', json=session_data)
        assert session_response.status_code == 201
        session = session_response.get_json()

        yield {
            'product': product,
            'batch': batch,
            'brewer': brewer,
            'session': session,
            'user_id': test_user_id
        }

        # Cleanup
        client.delete(f'/api/test/cleanup/{test_user_id}')

    def test_duplicate_shot_in_empty_session(self, client, sample_data):
        """Test duplicating shot in session with no existing shots returns 404."""
        session = sample_data['session']
        user_id = sample_data['user_id']

        response = client.post(f'/api/shot_sessions/{session["id"]}/duplicate_newest_shot?user_id={user_id}')
        
        # Should fail because there are no shots in the session
        assert response.status_code == 404
        assert 'No shots found' in response.get_json()['error']

    def test_duplicate_newest_shot_success(self, client, sample_data):
        """Test successful duplication of the newest shot in session."""
        session = sample_data['session']
        batch = sample_data['batch']
        brewer = sample_data['brewer']
        user_id = sample_data['user_id']

        # Create first shot
        shot1_data = {
            'product_batch_id': batch['id'],
            'shot_session_id': session['id'],
            'brewer_id': brewer['id'],
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93.0,
            'grinder_setting': '15',
            'sweetness': 8,
            'acidity': 7,
            'body': 6,
            'aroma': 8,
            'bitterness': 3,
            'overall_score': 7.5,
            'notes': 'First shot - baseline'
        }
        shot1_response = client.post(f'/api/shots?user_id={user_id}', json=shot1_data)
        assert shot1_response.status_code == 201
        shot1 = shot1_response.get_json()

        # Create second shot (newer)
        shot2_data = {
            'product_batch_id': batch['id'],
            'shot_session_id': session['id'],
            'brewer_id': brewer['id'],
            'dose_grams': 19.0,
            'yield_grams': 38.0,
            'extraction_time_seconds': 27,
            'water_temperature_c': 94.0,
            'grinder_setting': '14',
            'sweetness': 9,
            'acidity': 6,
            'body': 8,
            'aroma': 9,
            'bitterness': 2,
            'overall_score': 8.5,
            'notes': 'Second shot - improved'
        }
        shot2_response = client.post(f'/api/shots?user_id={user_id}', json=shot2_data)
        assert shot2_response.status_code == 201
        shot2 = shot2_response.get_json()

        # Duplicate the newest shot
        duplicate_response = client.post(f'/api/shot_sessions/{session["id"]}/duplicate_newest_shot?user_id={user_id}')
        assert duplicate_response.status_code == 201
        duplicate_result = duplicate_response.get_json()

        # Verify response structure
        assert 'new_shot' in duplicate_result
        assert 'original_shot' in duplicate_result
        new_shot = duplicate_result['new_shot']
        original_shot = duplicate_result['original_shot']

        # Verify the original shot is the newest one (shot2)
        assert original_shot['id'] == shot2['id']

        # Verify the new shot has copied the settings from shot2
        assert new_shot['product_batch_id'] == shot2['product_batch_id']
        assert new_shot['shot_session_id'] == shot2['shot_session_id']
        assert new_shot['brewer_id'] == shot2['brewer_id']
        assert new_shot['dose_grams'] == shot2['dose_grams']
        assert new_shot['yield_grams'] == shot2['yield_grams']
        assert new_shot['extraction_time_seconds'] == shot2['extraction_time_seconds']
        assert new_shot['water_temperature_c'] == shot2['water_temperature_c']
        assert new_shot['grinder_setting'] == shot2['grinder_setting']

        # Verify tasting scores are cleared
        assert new_shot.get('sweetness') is None
        assert new_shot.get('acidity') is None
        assert new_shot.get('body') is None
        assert new_shot.get('aroma') is None
        assert new_shot.get('bitterness') is None
        assert new_shot.get('overall_score') is None

        # Verify notes are cleared
        assert new_shot.get('notes') is None or new_shot.get('notes') == ''

        # Verify new shot has different ID and timestamp
        assert new_shot['id'] != shot2['id']
        assert new_shot['timestamp'] != shot2['timestamp']

    def test_duplicate_shot_tasting_scores_cleared(self, client, sample_data):
        """Test that tasting scores are cleared in duplicated shot."""
        session = sample_data['session']
        batch = sample_data['batch']
        brewer = sample_data['brewer']
        user_id = sample_data['user_id']

        # Create shot with all tasting scores
        shot_data = {
            'product_batch_id': batch['id'],
            'shot_session_id': session['id'],
            'brewer_id': brewer['id'],
            'dose_grams': 18.5,
            'yield_grams': 37.0,
            'extraction_time_seconds': 26,
            'sweetness': 9,
            'acidity': 8,
            'body': 7,
            'aroma': 8,
            'bitterness': 2,
            'crema': 8,
            'flavor_profile_match': 9,
            'overall_score': 8.2,
            'notes': 'Excellent shot with detailed tasting notes'
        }
        shot_response = client.post(f'/api/shots?user_id={user_id}', json=shot_data)
        assert shot_response.status_code == 201

        # Duplicate the shot
        duplicate_response = client.post(f'/api/shot_sessions/{session["id"]}/duplicate_newest_shot?user_id={user_id}')
        assert duplicate_response.status_code == 201
        new_shot = duplicate_response.get_json()['new_shot']

        # Verify all tasting scores are cleared
        tasting_fields = ['sweetness', 'acidity', 'body', 'aroma', 'bitterness', 'crema', 'flavor_profile_match', 'overall_score']
        for field in tasting_fields:
            assert new_shot.get(field) is None, f"Tasting field {field} should be cleared"

        # Verify notes are cleared
        assert new_shot.get('notes') is None or new_shot.get('notes') == ''

    def test_duplicate_shot_equipment_preserved(self, client, sample_data):
        """Test that equipment settings are preserved in duplicated shot."""
        session = sample_data['session']
        batch = sample_data['batch']
        brewer = sample_data['brewer']
        user_id = sample_data['user_id']

        # Create additional equipment
        grinder_data = {'name': 'Test Grinder'}
        grinder_response = client.post(f'/api/grinders?user_id={user_id}', json=grinder_data)
        assert grinder_response.status_code == 201
        grinder = grinder_response.get_json()

        portafilter_data = {'name': 'Test Portafilter'}
        portafilter_response = client.post(f'/api/portafilters?user_id={user_id}', json=portafilter_data)
        assert portafilter_response.status_code == 201
        portafilter = portafilter_response.get_json()

        # Create shot with equipment
        shot_data = {
            'product_batch_id': batch['id'],
            'shot_session_id': session['id'],
            'brewer_id': brewer['id'],
            'grinder_id': grinder['id'],
            'portafilter_id': portafilter['id'],
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93.0,
            'grinder_setting': '15',
            'preinfusion_seconds': 3,
            'pressure_bars': 9.0
        }
        shot_response = client.post(f'/api/shots?user_id={user_id}', json=shot_data)
        assert shot_response.status_code == 201

        # Duplicate the shot
        duplicate_response = client.post(f'/api/shot_sessions/{session["id"]}/duplicate_newest_shot?user_id={user_id}')
        assert duplicate_response.status_code == 201
        new_shot = duplicate_response.get_json()['new_shot']

        # Verify equipment is preserved
        assert new_shot['brewer_id'] == brewer['id']
        assert new_shot['grinder_id'] == grinder['id']
        assert new_shot['portafilter_id'] == portafilter['id']

        # Verify brewing parameters are preserved
        assert new_shot['dose_grams'] == 18.0
        assert new_shot['yield_grams'] == 36.0
        assert new_shot['extraction_time_seconds'] == 25
        assert new_shot['water_temperature_c'] == 93.0
        assert new_shot['grinder_setting'] == '15'
        assert new_shot['preinfusion_seconds'] == 3
        assert new_shot['pressure_bars'] == 9.0

    def test_duplicate_shot_invalid_session(self, client, sample_data):
        """Test duplication with invalid session ID returns 404."""
        user_id = sample_data['user_id']
        
        response = client.post(f'/api/shot_sessions/99999/duplicate_newest_shot?user_id={user_id}')
        assert response.status_code == 404
        assert 'not found' in response.get_json()['error']

    def test_duplicate_newest_shot_selection(self, client, sample_data):
        """Test that the newest shot is correctly selected for duplication."""
        session = sample_data['session']
        batch = sample_data['batch']
        brewer = sample_data['brewer']
        user_id = sample_data['user_id']

        # Create multiple shots with specific timestamps
        shots_created = []
        base_timestamp = datetime(2024, 1, 20, 10, 0, 0, tzinfo=timezone.utc)
        
        for i in range(3):
            # Create shots with increasing timestamps
            timestamp = base_timestamp.replace(hour=10 + i)
            shot_data = {
                'product_batch_id': batch['id'],
                'shot_session_id': session['id'],
                'brewer_id': brewer['id'],
                'dose_grams': 18.0 + i,  # Different doses to identify shots
                'yield_grams': 36.0,
                'timestamp': timestamp.isoformat(),
                'notes': f'Shot {i + 1}'
            }
            shot_response = client.post(f'/api/shots?user_id={user_id}', json=shot_data)
            assert shot_response.status_code == 201
            shots_created.append(shot_response.get_json())

        # Duplicate the newest shot
        duplicate_response = client.post(f'/api/shot_sessions/{session["id"]}/duplicate_newest_shot?user_id={user_id}')
        assert duplicate_response.status_code == 201
        duplicate_result = duplicate_response.get_json()

        # Verify the newest shot (last created) was selected
        original_shot = duplicate_result['original_shot']
        new_shot = duplicate_result['new_shot']
        
        # The newest shot should have dose_grams = 20.0 (18.0 + 2)
        assert original_shot['dose_grams'] == 20.0
        assert new_shot['dose_grams'] == 20.0

    def test_session_shot_count_after_duplication(self, client, sample_data):
        """Test that shot count increases after duplication."""
        session = sample_data['session']
        batch = sample_data['batch']
        brewer = sample_data['brewer']
        user_id = sample_data['user_id']

        # Get initial session state
        initial_response = client.get(f'/api/shot_sessions/{session["id"]}?user_id={user_id}')
        assert initial_response.status_code == 200
        initial_session = initial_response.get_json()
        initial_count = initial_session.get('shot_count', 0)

        # Create first shot
        shot_data = {
            'product_batch_id': batch['id'],
            'shot_session_id': session['id'],
            'brewer_id': brewer['id'],
            'dose_grams': 18.0,
            'yield_grams': 36.0
        }
        shot_response = client.post(f'/api/shots?user_id={user_id}', json=shot_data)
        assert shot_response.status_code == 201

        # Verify count increased by 1
        after_first_response = client.get(f'/api/shot_sessions/{session["id"]}?user_id={user_id}')
        assert after_first_response.status_code == 200
        after_first_session = after_first_response.get_json()
        assert after_first_session['shot_count'] == initial_count + 1

        # Duplicate the shot
        duplicate_response = client.post(f'/api/shot_sessions/{session["id"]}/duplicate_newest_shot?user_id={user_id}')
        assert duplicate_response.status_code == 201

        # Verify count increased by 1 more
        final_response = client.get(f'/api/shot_sessions/{session["id"]}?user_id={user_id}')
        assert final_response.status_code == 200
        final_session = final_response.get_json()
        assert final_session['shot_count'] == initial_count + 2

    def test_duplicate_preserves_session_context(self, client, sample_data):
        """Test that duplicated shot maintains session context."""
        session = sample_data['session']
        batch = sample_data['batch']
        brewer = sample_data['brewer']
        user_id = sample_data['user_id']

        # Create shot
        shot_data = {
            'product_batch_id': batch['id'],
            'shot_session_id': session['id'],
            'brewer_id': brewer['id'],
            'dose_grams': 18.0,
            'yield_grams': 36.0
        }
        shot_response = client.post(f'/api/shots?user_id={user_id}', json=shot_data)
        assert shot_response.status_code == 201

        # Duplicate the shot
        duplicate_response = client.post(f'/api/shot_sessions/{session["id"]}/duplicate_newest_shot?user_id={user_id}')
        assert duplicate_response.status_code == 201
        new_shot = duplicate_response.get_json()['new_shot']

        # Verify session context is preserved
        assert new_shot['shot_session_id'] == session['id']
        assert new_shot['product_batch_id'] == batch['id']

        # Verify the new shot appears in session shots
        session_shots_response = client.get(f'/api/shot_sessions/{session["id"]}/shots?user_id={user_id}')
        assert session_shots_response.status_code == 200
        session_shots = session_shots_response.get_json()
        
        # Should have 2 shots now (original + duplicate)
        assert len(session_shots) == 2
        
        # Verify the new shot is in the session
        new_shot_in_session = any(shot['id'] == new_shot['id'] for shot in session_shots)
        assert new_shot_in_session, "Duplicated shot should appear in session shots"