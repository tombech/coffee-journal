"""
Test Shot and ShotSession API endpoints.
"""
import pytest
from datetime import date, datetime


class TestShotEndpoints:
    """Test Shot API endpoints."""
    
    def test_create_shot(self, client):
        """Test creating a shot via API."""
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'sweetness': 8,
            'acidity': 7,
            'body': 8,
            'aroma': 9,
            'bitterness': 2,
            'overall_score': 8,
            'notes': 'Great shot with excellent crema'
        }
        
        response = client.post('/api/shots', json=shot_data)
        assert response.status_code == 201
        
        shot = response.get_json()
        assert shot['dose_grams'] == 18.0
        assert shot['yield_grams'] == 36.0
        assert shot['dose_yield_ratio'] == 2.0
        assert shot['extraction_time_seconds'] == 25
        assert shot['water_temperature_c'] == 93
        assert shot['extraction_status'] == 'perfect'
        assert shot['overall_score'] == 8
        assert shot['notes'] == 'Great shot with excellent crema'
        assert shot['id'] is not None
        assert shot['timestamp'] is not None
    
    def test_create_shot_with_equipment(self, client):
        """Test creating a shot with all equipment fields."""
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'dose_grams': 19.0,
            'yield_grams': 38.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 27,
            'water_temperature_c': 92,
            'portafilter_id': 2,
            'basket_id': 1,
            'tamper_id': 3,
            'wdt_tool_id': 1,
            'leveling_tool_id': 2,
            'grinder_id': 5,
            'grinder_setting': 'fine',
            'extraction_status': 'under-extracted',
            'sweetness': 6,
            'acidity': 8,
            'body': 6,
            'aroma': 7,
            'bitterness': 4,
            'overall_score': 6,
            'notes': 'Slightly sour - need to grind finer'
        }
        
        response = client.post('/api/shots', json=shot_data)
        assert response.status_code == 201
        
        shot = response.get_json()
        assert shot['portafilter_id'] == 2
        assert shot['basket_id'] == 1
        assert shot['tamper_id'] == 3
        assert shot['wdt_tool_id'] == 1
        assert shot['leveling_tool_id'] == 2
        assert shot['grinder_id'] == 5
        assert shot['grinder_setting'] == 'fine'
    
    def test_create_shot_with_session(self, client):
        """Test creating a shot associated with a session."""
        # First create a session
        session_data = {
            'title': 'Test Session for Shot',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'notes': 'Testing shot creation with session'
        }
        
        session_response = client.post('/api/shot_sessions', json=session_data)
        assert session_response.status_code == 201
        session = session_response.get_json()
        session_id = session['id']
        
        # Now create a shot for this session
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'shot_session_id': session_id,
            'dose_grams': 18.5,
            'yield_grams': 37.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 26,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 9
        }
        
        response = client.post('/api/shots', json=shot_data)
        assert response.status_code == 201
        
        shot = response.get_json()
        assert shot['shot_session_id'] == session_id
    
    def test_get_shots(self, client):
        """Test getting all shots."""
        # Create some shots first
        client.post('/api/shots', json={
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 8
        })
        client.post('/api/shots', json={
            'product_id': 2,
            'product_batch_id': 2,
            'brewer_id': 2,
            'dose_grams': 19.0,
            'yield_grams': 38.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 27,
            'water_temperature_c': 92,
            'extraction_status': 'under-extracted',
            'overall_score': 6
        })
        
        response = client.get('/api/shots')
        assert response.status_code == 200
        
        shots = response.get_json()
        assert len(shots) >= 2
    
    def test_get_shot_by_id(self, client):
        """Test getting a specific shot by ID."""
        # Create a shot
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 8,
            'notes': 'Test shot for retrieval'
        }
        
        create_response = client.post('/api/shots', json=shot_data)
        created_shot = create_response.get_json()
        shot_id = created_shot['id']
        
        # Retrieve the shot
        response = client.get(f'/api/shots/{shot_id}')
        assert response.status_code == 200
        
        shot = response.get_json()
        assert shot['id'] == shot_id
        assert shot['notes'] == 'Test shot for retrieval'
        assert shot['dose_grams'] == 18.0
    
    def test_update_shot(self, client):
        """Test updating a shot."""
        # Create a shot
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 8
        }
        
        create_response = client.post('/api/shots', json=shot_data)
        created_shot = create_response.get_json()
        shot_id = created_shot['id']
        
        # Update the shot
        update_data = {
            'dose_grams': 19.0,
            'yield_grams': 38.0,
            'extraction_status': 'under-extracted',
            'overall_score': 7,
            'notes': 'Updated shot parameters'
        }
        
        response = client.put(f'/api/shots/{shot_id}', json=update_data)
        assert response.status_code == 200
        
        updated_shot = response.get_json()
        assert updated_shot['dose_grams'] == 19.0
        assert updated_shot['yield_grams'] == 38.0
        assert updated_shot['extraction_status'] == 'under-extracted'
        assert updated_shot['overall_score'] == 7
        assert updated_shot['notes'] == 'Updated shot parameters'
    
    def test_delete_shot(self, client):
        """Test deleting a shot."""
        # Create a shot
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 8
        }
        
        create_response = client.post('/api/shots', json=shot_data)
        created_shot = create_response.get_json()
        shot_id = created_shot['id']
        
        # Delete the shot
        response = client.delete(f'/api/shots/{shot_id}')
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f'/api/shots/{shot_id}')
        assert get_response.status_code == 404
    
    def test_get_shots_by_session(self, client):
        """Test getting shots filtered by session ID."""
        # Create a session
        session_data = {
            'title': 'Filter Test Session',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1
        }
        
        session_response = client.post('/api/shot_sessions', json=session_data)
        session = session_response.get_json()
        session_id = session['id']
        
        # Create shots for this session
        for i in range(3):
            shot_data = {
                'product_id': 1,
                'product_batch_id': 1,
                'brewer_id': 1,
                'shot_session_id': session_id,
                'dose_grams': 18.0 + i,
                'yield_grams': 36.0 + i * 2,
                'dose_yield_ratio': 2.0,
                'extraction_time_seconds': 25 + i,
                'water_temperature_c': 93,
                'extraction_status': 'perfect',
                'overall_score': 8 + i
            }
            client.post('/api/shots', json=shot_data)
        
        # Get shots for this session
        response = client.get(f'/api/shot_sessions/{session_id}/shots')
        assert response.status_code == 200
        
        shots = response.get_json()
        assert len(shots) == 3
        
        # Verify all shots belong to this session
        for shot in shots:
            assert shot['shot_session_id'] == session_id
    
    def test_shot_validation(self, client):
        """Test shot creation validation."""
        # Missing required fields
        response = client.post('/api/shots', json={
            'dose_grams': 18.0
        })
        assert response.status_code == 400
        
        # Invalid extraction_status
        response = client.post('/api/shots', json={
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'invalid_status',
            'overall_score': 8
        })
        assert response.status_code == 400


class TestShotSessionEndpoints:
    """Test ShotSession API endpoints."""
    
    def test_create_shot_session(self, client):
        """Test creating a shot session via API."""
        session_data = {
            'title': 'Morning Dialing Session',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'notes': 'Working on perfecting extraction timing'
        }
        
        response = client.post('/api/shot_sessions', json=session_data)
        assert response.status_code == 201
        
        session = response.get_json()
        assert session['title'] == 'Morning Dialing Session'
        assert session['product_id'] == 1
        assert session['product_batch_id'] == 1
        assert session['brewer_id'] == 1
        assert session['notes'] == 'Working on perfecting extraction timing'
        assert session['id'] is not None
        assert session['created_at'] is not None
    
    def test_create_minimal_shot_session(self, client):
        """Test creating a shot session with minimal data."""
        session_data = {
            'title': 'Minimal Session',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1
        }
        
        response = client.post('/api/shot_sessions', json=session_data)
        assert response.status_code == 201
        
        session = response.get_json()
        assert session['title'] == 'Minimal Session'
        assert session.get('notes') is None or session.get('notes') == ''
    
    def test_get_shot_sessions(self, client):
        """Test getting all shot sessions."""
        # Create some sessions first
        client.post('/api/shot_sessions', json={
            'title': 'Morning Session',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1
        })
        client.post('/api/shot_sessions', json={
            'title': 'Afternoon Session',
            'product_id': 2,
            'product_batch_id': 2,
            'brewer_id': 2
        })
        
        response = client.get('/api/shot_sessions')
        assert response.status_code == 200
        
        sessions = response.get_json()
        assert len(sessions) >= 2
    
    def test_get_shot_session_by_id(self, client):
        """Test getting a specific shot session by ID."""
        # Create a session
        session_data = {
            'title': 'Test Session for Retrieval',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'notes': 'Test session notes'
        }
        
        create_response = client.post('/api/shot_sessions', json=session_data)
        created_session = create_response.get_json()
        session_id = created_session['id']
        
        # Retrieve the session
        response = client.get(f'/api/shot_sessions/{session_id}')
        assert response.status_code == 200
        
        session = response.get_json()
        assert session['id'] == session_id
        assert session['title'] == 'Test Session for Retrieval'
        assert session['notes'] == 'Test session notes'
    
    def test_update_shot_session(self, client):
        """Test updating a shot session."""
        # Create a session
        session_data = {
            'title': 'Original Session Name',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'notes': 'Original notes'
        }
        
        create_response = client.post('/api/shot_sessions', json=session_data)
        created_session = create_response.get_json()
        session_id = created_session['id']
        
        # Update the session
        update_data = {
            'title': 'Updated Session Name',
            'notes': 'Updated notes with more details'
        }
        
        response = client.put(f'/api/shot_sessions/{session_id}', json=update_data)
        assert response.status_code == 200
        
        updated_session = response.get_json()
        assert updated_session['title'] == 'Updated Session Name'
        assert updated_session['notes'] == 'Updated notes with more details'
        assert updated_session['product_id'] == 1  # Should remain unchanged
    
    def test_delete_shot_session(self, client):
        """Test deleting a shot session."""
        # Create a session
        session_data = {
            'title': 'Session to Delete',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1
        }
        
        create_response = client.post('/api/shot_sessions', json=session_data)
        created_session = create_response.get_json()
        session_id = created_session['id']
        
        # Delete the session
        response = client.delete(f'/api/shot_sessions/{session_id}')
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f'/api/shot_sessions/{session_id}')
        assert get_response.status_code == 404
    
    def test_shot_session_validation(self, client):
        """Test shot session creation validation."""
        # Missing required fields
        response = client.post('/api/shot_sessions', json={
            'title': 'Incomplete Session'
        })
        assert response.status_code == 400
        
        # Empty title
        response = client.post('/api/shot_sessions', json={
            'title': '',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1
        })
        assert response.status_code == 400


class TestShotSessionShotRelationship:
    """Test the relationship between shot sessions and shots."""
    
    def test_session_with_multiple_shots(self, client):
        """Test creating a session and adding multiple shots to it."""
        # Create a session
        session_data = {
            'title': 'Multi-Shot Session',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'notes': 'Session for testing multiple shots'
        }
        
        session_response = client.post('/api/shot_sessions', json=session_data)
        session = session_response.get_json()
        session_id = session['id']
        
        # Create multiple shots for this session
        shot_scores = [7, 8, 9, 8]
        shot_ids = []
        
        for i, score in enumerate(shot_scores):
            shot_data = {
                'product_id': 1,
                'product_batch_id': 1,
                'brewer_id': 1,
                'shot_session_id': session_id,
                'dose_grams': 18.0 + i * 0.5,
                'yield_grams': 36.0 + i,
                'dose_yield_ratio': 2.0,
                'extraction_time_seconds': 25 + i,
                'water_temperature_c': 93,
                'extraction_status': 'perfect' if score >= 8 else 'under-extracted',
                'overall_score': score,
                'notes': f'Shot {i + 1} in session'
            }
            
            shot_response = client.post('/api/shots', json=shot_data)
            shot = shot_response.get_json()
            shot_ids.append(shot['id'])
        
        # Verify all shots are associated with the session
        session_shots_response = client.get(f'/api/shot_sessions/{session_id}/shots')
        session_shots = session_shots_response.get_json()
        
        assert len(session_shots) == 4
        returned_shot_ids = [shot['id'] for shot in session_shots]
        for shot_id in shot_ids:
            assert shot_id in returned_shot_ids
    
    def test_delete_session_with_shots(self, client):
        """Test deleting a session that has associated shots."""
        # Create a session
        session_data = {
            'title': 'Session to Delete with Shots',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1
        }
        
        session_response = client.post('/api/shot_sessions', json=session_data)
        session = session_response.get_json()
        session_id = session['id']
        
        # Create a shot for this session
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'shot_session_id': session_id,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 8
        }
        
        shot_response = client.post('/api/shots', json=shot_data)
        shot = shot_response.get_json()
        shot_id = shot['id']
        
        # Try to delete the session (this should handle the relationship appropriately)
        delete_response = client.delete(f'/api/shot_sessions/{session_id}')
        
        # Depending on implementation, this might:
        # 1. Prevent deletion (return 400/409)
        # 2. Set shot_session_id to null for associated shots
        # 3. Delete associated shots as well
        
        # For now, let's assume it sets shot_session_id to null
        if delete_response.status_code == 204:
            # Session deleted successfully
            # Check that the shot still exists but with null session_id
            shot_check = client.get(f'/api/shots/{shot_id}')
            assert shot_check.status_code == 200
            updated_shot = shot_check.get_json()
            assert updated_shot['shot_session_id'] is None
        else:
            # Session deletion prevented due to associated shots
            assert delete_response.status_code in [400, 409]
    
