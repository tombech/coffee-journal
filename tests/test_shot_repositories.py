"""
Unit tests for Shot and ShotSession repositories.
Tests CRUD operations and relationships for espresso shot tracking.
"""
import pytest
from datetime import date, datetime


class TestShotRepository:
    """Tests for the Shot repository."""
    
    def test_create_shot(self, repo_factory):
        """Test creating a shot."""
        shot_repo = repo_factory.get_shot_repository()
        
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
        
        shot = shot_repo.create(shot_data)
        
        assert shot['id'] is not None
        assert shot['dose_grams'] == 18.0
        assert shot['yield_grams'] == 36.0
        assert shot['dose_yield_ratio'] == 2.0
        assert shot['extraction_time_seconds'] == 25
        assert shot['extraction_status'] == 'perfect'
        assert shot['timestamp'] is not None
        
        # Verify it's persisted
        found_shot = shot_repo.find_by_id(shot['id'])
        assert found_shot is not None
        assert found_shot['dose_grams'] == 18.0
    
    def test_create_shot_with_optional_equipment(self, repo_factory):
        """Test creating a shot with optional equipment fields."""
        shot_repo = repo_factory.get_shot_repository()
        
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'dose_grams': 19.5,
            'yield_grams': 38.0,
            'dose_yield_ratio': 1.9,
            'extraction_time_seconds': 28,
            'water_temperature_c': 92,
            'portafilter_id': 2,
            'basket_id': 1,
            'tamper_id': 3,
            'wdt_tool_id': 1,
            'leveling_tool_id': 2,
            'grinder_id': 5,
            'grinder_setting': 'fine',
            'extraction_status': 'under-extracted',
            'sweetness': 7,
            'acidity': 8,
            'body': 6,
            'aroma': 7,
            'bitterness': 4,
            'overall_score': 6,
            'notes': 'Slightly sour - adjust grind finer'
        }
        
        shot = shot_repo.create(shot_data)
        
        assert shot['portafilter_id'] == 2
        assert shot['basket_id'] == 1
        assert shot['tamper_id'] == 3
        assert shot['wdt_tool_id'] == 1
        assert shot['leveling_tool_id'] == 2
        assert shot['grinder_id'] == 5
        assert shot['grinder_setting'] == 'fine'
        assert shot['sweetness'] == 7
        assert shot['notes'] == 'Slightly sour - adjust grind finer'
    
    def test_create_shot_with_session(self, repo_factory):
        """Test creating a shot associated with a session."""
        shot_repo = repo_factory.get_shot_repository()
        
        shot_data = {
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'shot_session_id': 1,
            'dose_grams': 18.5,
            'yield_grams': 37.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 26,
            'water_temperature_c': 94,
            'extraction_status': 'perfect',
            'overall_score': 9
        }
        
        shot = shot_repo.create(shot_data)
        assert shot['shot_session_id'] == 1
    
    def test_update_shot(self, repo_factory):
        """Test updating a shot."""
        shot_repo = repo_factory.get_shot_repository()
        
        # Create initial shot
        shot = shot_repo.create({
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
        shot_id = shot['id']
        
        # Update the shot
        updated_shot = shot_repo.update(shot_id, {
            'dose_grams': 19.0,
            'yield_grams': 38.0,
            'dose_yield_ratio': 2.0,
            'extraction_status': 'under-extracted',
            'overall_score': 7,
            'notes': 'Updated shot parameters'
        })
        
        assert updated_shot['dose_grams'] == 19.0
        assert updated_shot['yield_grams'] == 38.0
        assert updated_shot['extraction_status'] == 'under-extracted'
        assert updated_shot['overall_score'] == 7
        assert updated_shot['notes'] == 'Updated shot parameters'
        assert updated_shot['id'] == shot_id
        
        # Verify persistence
        fetched_shot = shot_repo.find_by_id(shot_id)
        assert fetched_shot['dose_grams'] == 19.0
        assert fetched_shot['notes'] == 'Updated shot parameters'
    
    def test_delete_shot(self, repo_factory):
        """Test deleting a shot."""
        shot_repo = repo_factory.get_shot_repository()
        
        shot = shot_repo.create({
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
        shot_id = shot['id']
        
        # Verify it exists
        assert shot_repo.find_by_id(shot_id) is not None
        
        # Delete the shot
        shot_repo.delete(shot_id)
        
        # Verify it's gone
        assert shot_repo.find_by_id(shot_id) is None
    
    def test_find_all_shots(self, repo_factory):
        """Test finding all shots."""
        shot_repo = repo_factory.get_shot_repository()
        
        # Create multiple shots
        shot1 = shot_repo.create({
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
        
        shot2 = shot_repo.create({
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
        
        shots = shot_repo.find_all()
        assert len(shots) >= 2
        
        # Check that our shots are in the results
        shot_ids = [shot['id'] for shot in shots]
        assert shot1['id'] in shot_ids
        assert shot2['id'] in shot_ids
    
    def test_find_shots_by_session(self, repo_factory):
        """Test finding shots by session ID."""
        shot_repo = repo_factory.get_shot_repository()
        
        # Create shots with different session IDs
        session1_shot = shot_repo.create({
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'shot_session_id': 1,
            'dose_grams': 18.0,
            'yield_grams': 36.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 25,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 8
        })
        
        session1_shot2 = shot_repo.create({
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'shot_session_id': 1,
            'dose_grams': 18.5,
            'yield_grams': 37.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 26,
            'water_temperature_c': 93,
            'extraction_status': 'perfect',
            'overall_score': 9
        })
        
        session2_shot = shot_repo.create({
            'product_id': 2,
            'product_batch_id': 2,
            'brewer_id': 2,
            'shot_session_id': 2,
            'dose_grams': 19.0,
            'yield_grams': 38.0,
            'dose_yield_ratio': 2.0,
            'extraction_time_seconds': 27,
            'water_temperature_c': 92,
            'extraction_status': 'under-extracted',
            'overall_score': 6
        })
        
        # Test finding by session
        session1_shots = [shot for shot in shot_repo.find_all() if shot.get('shot_session_id') == 1]
        assert len(session1_shots) >= 2
        
        session2_shots = [shot for shot in shot_repo.find_all() if shot.get('shot_session_id') == 2]
        assert len(session2_shots) >= 1


class TestShotSessionRepository:
    """Tests for the ShotSession repository."""
    
    def test_create_shot_session(self, repo_factory):
        """Test creating a shot session."""
        shot_session_repo = repo_factory.get_shot_session_repository()
        
        session_data = {
            'session_name': 'Morning Dialing Session',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'notes': 'Working on perfecting extraction timing'
        }
        
        session = shot_session_repo.create(session_data)
        
        assert session['id'] is not None
        assert session['session_name'] == 'Morning Dialing Session'
        assert session['product_id'] == 1
        assert session['product_batch_id'] == 1
        assert session['brewer_id'] == 1
        assert session['notes'] == 'Working on perfecting extraction timing'
        assert session['created_at'] is not None
        
        # Verify it's persisted
        found_session = shot_session_repo.find_by_id(session['id'])
        assert found_session is not None
        assert found_session['session_name'] == 'Morning Dialing Session'
    
    def test_create_minimal_shot_session(self, repo_factory):
        """Test creating a shot session with minimal data."""
        shot_session_repo = repo_factory.get_shot_session_repository()
        
        session_data = {
            'session_name': 'Quick Session',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1
        }
        
        session = shot_session_repo.create(session_data)
        
        assert session['session_name'] == 'Quick Session'
        assert session.get('notes') is None or session.get('notes') == ''
    
    def test_update_shot_session(self, repo_factory):
        """Test updating a shot session."""
        shot_session_repo = repo_factory.get_shot_session_repository()
        
        # Create initial session
        session = shot_session_repo.create({
            'session_name': 'Test Session',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'notes': 'Initial notes'
        })
        session_id = session['id']
        
        # Update the session
        updated_session = shot_session_repo.update(session_id, {
            'session_name': 'Updated Test Session',
            'notes': 'Updated notes with more details'
        })
        
        assert updated_session['session_name'] == 'Updated Test Session'
        assert updated_session['notes'] == 'Updated notes with more details'
        assert updated_session['id'] == session_id
        
        # Verify persistence
        fetched_session = shot_session_repo.find_by_id(session_id)
        assert fetched_session['session_name'] == 'Updated Test Session'
        assert fetched_session['notes'] == 'Updated notes with more details'
    
    def test_delete_shot_session(self, repo_factory):
        """Test deleting a shot session."""
        shot_session_repo = repo_factory.get_shot_session_repository()
        
        session = shot_session_repo.create({
            'session_name': 'Delete Test Session',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1
        })
        session_id = session['id']
        
        # Verify it exists
        assert shot_session_repo.find_by_id(session_id) is not None
        
        # Delete the session
        shot_session_repo.delete(session_id)
        
        # Verify it's gone
        assert shot_session_repo.find_by_id(session_id) is None
    
    def test_find_all_shot_sessions(self, repo_factory):
        """Test finding all shot sessions."""
        shot_session_repo = repo_factory.get_shot_session_repository()
        
        # Create multiple sessions
        session1 = shot_session_repo.create({
            'session_name': 'Morning Session',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1
        })
        
        session2 = shot_session_repo.create({
            'session_name': 'Afternoon Session',
            'product_id': 2,
            'product_batch_id': 2,
            'brewer_id': 2
        })
        
        sessions = shot_session_repo.find_all()
        assert len(sessions) >= 2
        
        # Check that our sessions are in the results
        session_ids = [session['id'] for session in sessions]
        assert session1['id'] in session_ids
        assert session2['id'] in session_ids
    
    def test_shot_session_relationship_with_shots(self, repo_factory):
        """Test the relationship between shot sessions and shots."""
        shot_session_repo = repo_factory.get_shot_session_repository()
        shot_repo = repo_factory.get_shot_repository()
        
        # Create a shot session
        session = shot_session_repo.create({
            'session_name': 'Relationship Test Session',
            'product_id': 1,
            'product_batch_id': 1,
            'brewer_id': 1,
            'notes': 'Testing relationship'
        })
        session_id = session['id']
        
        # Create shots associated with this session
        shot1 = shot_repo.create({
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
        })
        
        shot2 = shot_repo.create({
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
        })
        
        # Verify the shots are associated with the session
        assert shot1['shot_session_id'] == session_id
        assert shot2['shot_session_id'] == session_id
        
        # Find all shots for this session
        session_shots = [shot for shot in shot_repo.find_all() if shot.get('shot_session_id') == session_id]
        assert len(session_shots) >= 2
        
        shot_ids = [shot['id'] for shot in session_shots]
        assert shot1['id'] in shot_ids
        assert shot2['id'] in shot_ids