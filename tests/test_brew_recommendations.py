"""
Unit tests for the brew recommendation service.

Tests the BrewRecommendationService class to ensure accurate recommendations
are generated based on historical brew session data.
"""

import pytest
from unittest.mock import Mock, patch
from coffeejournal.services.brew_recommendations import BrewRecommendationService


class TestBrewRecommendationService:
    """Test cases for the BrewRecommendationService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_session_repo = Mock()
        self.mock_method_repo = Mock()
        self.mock_factory = Mock()
        self.service = BrewRecommendationService(
            self.mock_session_repo, 
            self.mock_factory,
            self.mock_method_repo
        )
    
    def test_initialization(self):
        """Test service initialization with default parameters."""
        assert self.service.score_threshold == 3.5
        assert self.service.template_score_diff == 0.5  # Updated threshold
    
    def test_insufficient_sessions_returns_no_recommendations(self):
        """Test that insufficient good sessions returns no recommendations."""
        # Mock sessions with low scores
        self.mock_session_repo.find_all.return_value = [
            {'id': 1, 'product_id': 1, 'score': 2.0, 'brew_method_id': 1},
            {'id': 2, 'product_id': 1, 'score': None, 'sweetness': 3}  # Calculated score ~3.0
        ]
        
        result = self.service.get_recommendations(1)
        
        assert result['has_recommendations'] is False
        assert 'Need at least 2 sessions with score > 3.5' in result['message']
    
    def test_template_mode_when_best_session_significantly_better(self):
        """Test template mode when one session is 0.5+ points better."""
        # Mock sessions data
        sessions = [
            {
                'id': 1, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.5,  # Best session
                'amount_coffee_grams': 20.0,
                'amount_water_grams': 320.0,
                'brew_temperature_c': 93,  # Updated field name
                'grinder_setting': 15,     # Updated field name
                'recipe_id': 1,
                'timestamp': '2024-01-01T10:00:00'
            },
            {
                'id': 2, 'product_id': 1, 'brew_method_id': 1,
                'score': 3.9,  # Second best (diff = 0.6 > 0.5)
                'amount_coffee_grams': 18.0,
                'amount_water_grams': 300.0
            }
        ]
        
        # Mock enriched sessions (what enrich_brew_session_with_lookups returns)
        enriched_sessions = [
            {
                'id': 1, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.5,
                'amount_coffee_grams': 20.0,
                'amount_water_grams': 320.0,
                'brew_temperature_c': 93,
                'grinder_setting': 15,
                'recipe': {'id': 1, 'name': 'Perfect V60'},  # Enriched
                'timestamp': '2024-01-01T10:00:00'
            },
            {
                'id': 2, 'product_id': 1, 'brew_method_id': 1,
                'score': 3.9,
                'amount_coffee_grams': 18.0,
                'amount_water_grams': 300.0
            }
        ]
        
        self.mock_session_repo.find_all.return_value = sessions
        self.mock_method_repo.find_by_id.return_value = {'id': 1, 'name': 'V60'}
        
        # Mock the enrichment function
        with patch('coffeejournal.services.brew_recommendations.enrich_brew_session_with_lookups') as mock_enrich:
            mock_enrich.side_effect = enriched_sessions
            result = self.service.get_recommendations(1)
        
        assert result['has_recommendations'] is True
        assert 'V60' in result['recommendations']
        
        v60_rec = result['recommendations']['V60']
        assert v60_rec['type'] == 'template'
        assert v60_rec['source_score'] == 4.5
        assert v60_rec['source_date'] == '2024-01-01'
        
        # Check template parameters
        params = v60_rec['parameters']
        assert params['amount_coffee_grams']['value'] == 20.0
        assert params['amount_coffee_grams']['type'] == 'exact'
        assert params['brew_temperature_c']['value'] == 93  # Updated field name
        assert params['brew_temperature_c']['type'] == 'exact'
        assert params['grinder_setting']['value'] == 15    # Updated field name
        assert params['grinder_setting']['type'] == 'exact'
        assert params['brew_ratio']['value'] == 16.0       # NEW: 320/20 = 16.0
        assert params['brew_ratio']['type'] == 'exact'
        assert params['recipe']['value'] == {'id': 1, 'name': 'Perfect V60'}  # Enriched object
        assert params['recipe']['type'] == 'exact'
    
    def test_range_mode_when_scores_are_close(self):
        """Test range mode when session scores are close together."""
        # Mock sessions data
        sessions = [
            {
                'id': 1, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.2,
                'amount_coffee_grams': 20.0,
                'amount_water_grams': 320.0,
                'brew_temperature_c': 93,  # Updated field name
                'recipe_id': 1
            },
            {
                'id': 2, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.1,  # Diff = 0.1 < 0.5, triggers range mode
                'amount_coffee_grams': 18.0,
                'amount_water_grams': 300.0,
                'brew_temperature_c': 90,  # Updated field name
                'recipe_id': 1
            },
            {
                'id': 3, 'product_id': 1, 'brew_method_id': 1,
                'score': 3.9,
                'amount_coffee_grams': 22.0,
                'amount_water_grams': 350.0,
                'brew_temperature_c': 95,  # Updated field name
                'recipe_id': 2
            }
        ]
        
        # Mock enriched sessions
        enriched_sessions = [
            {
                'id': 1, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.2,
                'amount_coffee_grams': 20.0,
                'amount_water_grams': 320.0,
                'brew_temperature_c': 93,
                'recipe': {'id': 1, 'name': 'Standard V60'}
            },
            {
                'id': 2, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.1,
                'amount_coffee_grams': 18.0,
                'amount_water_grams': 300.0,
                'brew_temperature_c': 90,
                'recipe': {'id': 1, 'name': 'Standard V60'}
            },
            {
                'id': 3, 'product_id': 1, 'brew_method_id': 1,
                'score': 3.9,
                'amount_coffee_grams': 22.0,
                'amount_water_grams': 350.0,
                'brew_temperature_c': 95,
                'recipe': {'id': 2, 'name': 'Light V60'}
            }
        ]
        
        self.mock_session_repo.find_all.return_value = sessions
        self.mock_method_repo.find_by_id.return_value = {'id': 1, 'name': 'V60'}
        
        # Mock the enrichment function
        with patch('coffeejournal.services.brew_recommendations.enrich_brew_session_with_lookups') as mock_enrich:
            mock_enrich.side_effect = enriched_sessions
            result = self.service.get_recommendations(1)
        
        assert result['has_recommendations'] is True
        v60_rec = result['recommendations']['V60']
        assert v60_rec['type'] == 'range'
        assert v60_rec['sessions_used'] == 3
        assert v60_rec['avg_score'] == 4.1  # (4.2+4.1+3.9)/3 rounded
        
        # Check range parameters
        params = v60_rec['parameters']
        assert params['amount_coffee_grams']['min'] == 18.0
        assert params['amount_coffee_grams']['max'] == 22.0
        assert params['amount_coffee_grams']['avg'] == 20.0
        assert params['amount_coffee_grams']['type'] == 'range'
        
        # Check brew temperature (updated field name)
        assert params['brew_temperature_c']['min'] == 90
        assert params['brew_temperature_c']['max'] == 95
        assert params['brew_temperature_c']['avg'] == 92.7  # (93+90+95)/3 = 92.67 rounded to 92.7
        assert params['brew_temperature_c']['type'] == 'range'
        
        # Check brew ratio (NEW)
        # Ratios: 320/20=16.0, 300/18=16.7, 350/22=15.9
        assert params['brew_ratio']['min'] == 15.9
        assert params['brew_ratio']['max'] == 16.7
        assert params['brew_ratio']['avg'] == 16.2  # (16.0+16.7+15.9)/3 = 16.2
        assert params['brew_ratio']['type'] == 'range'
        
        # Check frequent categorical parameters
        assert params['recipe']['value'] == {'id': 1, 'name': 'Standard V60'}  # Most frequent (2 out of 3)
        assert params['recipe']['frequency'] == 2
        assert params['recipe']['total'] == 3
        assert params['recipe']['type'] == 'frequent'
    
    def test_method_filtering(self):
        """Test filtering recommendations by specific brew method."""
        sessions = [
            {
                'id': 1, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.2, 'amount_coffee_grams': 20.0
            },
            {
                'id': 2, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.0, 'amount_coffee_grams': 18.0
            },
            {
                'id': 3, 'product_id': 1, 'brew_method_id': 2,
                'score': 4.1, 'amount_coffee_grams': 25.0
            }
        ]
        
        self.mock_session_repo.find_all.return_value = sessions
        self.mock_method_repo.find_by_id.side_effect = lambda x: (
            {'id': 1, 'name': 'V60'} if x == 1 else {'id': 2, 'name': 'Chemex'}
        )
        
        # Filter for V60 only
        result = self.service.get_recommendations(1, method='V60')
        
        assert result['has_recommendations'] is True
        assert 'V60' in result['recommendations']
        assert 'Chemex' not in result['recommendations']
    
    def test_multiple_brew_methods(self):
        """Test recommendations for multiple brew methods."""
        sessions = [
            # V60 sessions
            {'id': 1, 'product_id': 1, 'brew_method_id': 1, 'score': 4.2},
            {'id': 2, 'product_id': 1, 'brew_method_id': 1, 'score': 4.0},
            # Chemex sessions
            {'id': 3, 'product_id': 1, 'brew_method_id': 2, 'score': 4.1},
            {'id': 4, 'product_id': 1, 'brew_method_id': 2, 'score': 3.9}
        ]
        
        self.mock_session_repo.find_all.return_value = sessions
        self.mock_method_repo.find_by_id.side_effect = lambda x: (
            {'id': 1, 'name': 'V60'} if x == 1 else {'id': 2, 'name': 'Chemex'}
        )
        
        result = self.service.get_recommendations(1)
        
        assert result['has_recommendations'] is True
        assert 'V60' in result['recommendations']
        assert 'Chemex' in result['recommendations']
    
    def test_calculated_score_integration(self):
        """Test integration with calculated scores from taste components."""
        sessions = [
            {
                'id': 1, 'product_id': 1, 'brew_method_id': 1,
                'score': None,  # No manual score
                'sweetness': 8, 'acidity': 7, 'body': 6, 'aroma': 8,
                'bitterness': 3, 'flavor_profile_match': 9,
                # This should calculate to (8+7+6+8+7+9)/6 = 7.5 (well above threshold)
                'amount_coffee_grams': 20.0
            },
            {
                'id': 2, 'product_id': 1, 'brew_method_id': 1,
                'score': None,  # No manual score
                'sweetness': 5, 'acidity': 6, 'body': 5, 'aroma': 6,
                'bitterness': 5, 'flavor_profile_match': 7,
                # This should calculate to (5+6+5+6+5+7)/6 = 5.7 (above threshold)
                'amount_coffee_grams': 18.0
            }
        ]
        
        self.mock_session_repo.find_all.return_value = sessions
        self.mock_method_repo.find_by_id.return_value = {'id': 1, 'name': 'V60'}
        
        result = self.service.get_recommendations(1)
        
        assert result['has_recommendations'] is True
        # Should have recommendations since both calculated scores > 3.5
    
    def test_handles_missing_brew_method_gracefully(self):
        """Test handling of sessions with missing or invalid brew method IDs."""
        sessions = [
            {
                'id': 1, 'product_id': 1, 'brew_method_id': 999,  # Invalid ID
                'score': 4.2, 'amount_coffee_grams': 20.0
            },
            {
                'id': 2, 'product_id': 1, 'brew_method_id': None,  # Missing ID
                'score': 4.0, 'amount_coffee_grams': 18.0
            }
        ]
        
        self.mock_session_repo.find_all.return_value = sessions
        self.mock_method_repo.find_by_id.return_value = None  # Method not found
        
        result = self.service.get_recommendations(1)
        
        # Should group under 'Unknown' method
        assert result['has_recommendations'] is True
        assert 'Unknown' in result['recommendations']
    
    def test_top_5_sessions_limit(self):
        """Test that only top 5 sessions per method are used for recommendations."""
        # Create 7 sessions with descending scores
        sessions = []
        for i in range(7):
            sessions.append({
                'id': i + 1, 'product_id': 1, 'brew_method_id': 1,
                'score': 5.0 - (i * 0.1),  # 5.0, 4.9, 4.8, ..., 4.4
                'amount_coffee_grams': 20.0 + i
            })
        
        self.mock_session_repo.find_all.return_value = sessions
        self.mock_method_repo.find_by_id.return_value = {'id': 1, 'name': 'V60'}
        
        result = self.service.get_recommendations(1)
        
        assert result['has_recommendations'] is True
        v60_rec = result['recommendations']['V60']
        
        # Should only use top 5 sessions for range calculation
        if v60_rec['type'] == 'range':
            assert v60_rec['sessions_used'] == 5
            # Coffee amounts should be 20.0 to 24.0 (top 5 sessions: indices 0-4)
            params = v60_rec['parameters']
            assert params['amount_coffee_grams']['min'] == 20.0
            assert params['amount_coffee_grams']['max'] == 24.0
    
    def test_empty_sessions_list(self):
        """Test behavior with no sessions at all."""
        self.mock_session_repo.find_all.return_value = []
        
        result = self.service.get_recommendations(1)
        
        assert result['has_recommendations'] is False
        assert 'Need at least 2 sessions' in result['message']
    
    def test_sessions_different_products_filtered_out(self):
        """Test that sessions for different products are filtered out."""
        sessions = [
            {'id': 1, 'product_id': 1, 'score': 4.2, 'brew_method_id': 1},  # Target product
            {'id': 2, 'product_id': 2, 'score': 4.5, 'brew_method_id': 1},  # Different product
            {'id': 3, 'product_id': 1, 'score': 4.0, 'brew_method_id': 1}   # Target product
        ]
        
        self.mock_session_repo.find_all.return_value = sessions
        self.mock_method_repo.find_by_id.return_value = {'id': 1, 'name': 'V60'}
        
        result = self.service.get_recommendations(1)  # Request for product 1
        
        assert result['has_recommendations'] is True
        # Should only consider sessions 1 and 3 (product_id = 1)
        v60_rec = result['recommendations']['V60']
        # Check total_sessions field which exists in both template and range modes
        assert v60_rec['total_sessions'] == 2  # Should be 2, not 3
    
    def test_enhanced_features_integration(self):
        """Test all enhanced features: higher threshold, brew ratio, enriched fields, correct field names."""
        # Mock sessions data with enhanced features
        sessions = [
            {
                'id': 1, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.8,  # Best session
                'amount_coffee_grams': 20.0,
                'amount_water_grams': 300.0,  # Ratio = 15.0
                'brew_temperature_c': 92,     # Correct field name
                'grinder_setting': 16,        # Correct field name
                'recipe_id': 1,
                'grinder_id': 1,
                'filter_id': 1,
                'timestamp': '2024-01-01T10:00:00'
            },
            {
                'id': 2, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.2,  # Diff = 0.6 > 0.5, should trigger template mode
                'amount_coffee_grams': 18.0,
                'amount_water_grams': 270.0,  # Ratio = 15.0
                'brew_temperature_c': 90,
                'grinder_setting': 15
            }
        ]
        
        # Mock enriched sessions with all equipment data
        enriched_sessions = [
            {
                'id': 1, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.8,
                'amount_coffee_grams': 20.0,
                'amount_water_grams': 300.0,
                'brew_temperature_c': 92,
                'grinder_setting': 16,
                'recipe': {'id': 1, 'name': 'Enhanced V60'},
                'grinder': {'id': 1, 'name': 'Baratza Encore'},
                'filter': {'id': 1, 'name': 'Hario V60 Paper'},
                'kettle': None,
                'scale': None,
                'timestamp': '2024-01-01T10:00:00'
            },
            {
                'id': 2, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.2,
                'amount_coffee_grams': 18.0,
                'amount_water_grams': 270.0,
                'brew_temperature_c': 90,
                'grinder_setting': 15
            }
        ]
        
        self.mock_session_repo.find_all.return_value = sessions
        self.mock_method_repo.find_by_id.return_value = {'id': 1, 'name': 'V60'}
        
        # Mock the enrichment function
        with patch('coffeejournal.services.brew_recommendations.enrich_brew_session_with_lookups') as mock_enrich:
            mock_enrich.side_effect = enriched_sessions
            result = self.service.get_recommendations(1)
        
        assert result['has_recommendations'] is True
        v60_rec = result['recommendations']['V60']
        
        # Should use template mode due to 0.5+ point difference
        assert v60_rec['type'] == 'template'
        assert v60_rec['source_score'] == 4.8
        
        # Check all enhanced parameters
        params = v60_rec['parameters']
        
        # Numeric fields with correct names
        assert params['amount_coffee_grams']['value'] == 20.0
        assert params['amount_water_grams']['value'] == 300.0
        assert params['brew_temperature_c']['value'] == 92  # Correct field name
        assert params['grinder_setting']['value'] == 16    # Correct field name
        
        # NEW: Brew ratio calculation
        assert params['brew_ratio']['value'] == 15.0       # 300/20 = 15.0
        assert params['brew_ratio']['type'] == 'exact'
        
        # Enriched categorical fields
        assert params['recipe']['value'] == {'id': 1, 'name': 'Enhanced V60'}
        assert params['recipe']['type'] == 'exact'
        assert params['grinder']['value'] == {'id': 1, 'name': 'Baratza Encore'}
        assert params['grinder']['type'] == 'exact'
        assert params['filter']['value'] == {'id': 1, 'name': 'Hario V60 Paper'}
        assert params['filter']['type'] == 'exact'
        
        # Equipment fields that are None should not appear in parameters
        assert 'kettle' not in params
        assert 'scale' not in params
    
    def test_brew_ratio_range_calculations(self):
        """Test brew ratio calculations in range mode."""
        # Mock sessions with different ratios
        sessions = [
            {'id': 1, 'product_id': 1, 'brew_method_id': 1, 'score': 4.2,
             'amount_coffee_grams': 20.0, 'amount_water_grams': 320.0},  # Ratio = 16.0
            {'id': 2, 'product_id': 1, 'brew_method_id': 1, 'score': 4.1,
             'amount_coffee_grams': 15.0, 'amount_water_grams': 240.0},  # Ratio = 16.0
            {'id': 3, 'product_id': 1, 'brew_method_id': 1, 'score': 4.0,
             'amount_coffee_grams': 25.0, 'amount_water_grams': 375.0}   # Ratio = 15.0
        ]
        
        enriched_sessions = sessions.copy()  # No enrichment needed for this test
        
        self.mock_session_repo.find_all.return_value = sessions
        self.mock_method_repo.find_by_id.return_value = {'id': 1, 'name': 'V60'}
        
        with patch('coffeejournal.services.brew_recommendations.enrich_brew_session_with_lookups') as mock_enrich:
            mock_enrich.side_effect = enriched_sessions
            result = self.service.get_recommendations(1)
        
        assert result['has_recommendations'] is True
        v60_rec = result['recommendations']['V60']
        assert v60_rec['type'] == 'range'  # Close scores should trigger range mode
        
        # Check brew ratio range calculation
        params = v60_rec['parameters']
        assert 'brew_ratio' in params
        assert params['brew_ratio']['min'] == 15.0
        assert params['brew_ratio']['max'] == 16.0
        assert params['brew_ratio']['avg'] == 15.7  # (16.0+16.0+15.0)/3 = 15.67 rounded to 15.7
        assert params['brew_ratio']['type'] == 'range'
    
    def test_handles_string_numeric_values_gracefully(self):
        """Test handling of string numeric values in production data."""
        # Mock sessions with string values (like production data)
        sessions = [
            {
                'id': 1, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.2,
                'amount_coffee_grams': '20.0',  # String value
                'amount_water_grams': '320.0',  # String value
                'brew_temperature_c': '93',     # String value
                'grinder_setting': '15'         # String value
            },
            {
                'id': 2, 'product_id': 1, 'brew_method_id': 1,
                'score': 4.0,
                'amount_coffee_grams': '18.5',  # String value
                'amount_water_grams': '295.0'   # String value
            },
            {
                'id': 3, 'product_id': 1, 'brew_method_id': 1,
                'score': 3.8,
                'amount_coffee_grams': 'invalid',  # Invalid string
                'amount_water_grams': '280.0'
            }
        ]
        
        enriched_sessions = sessions.copy()  # No enrichment needed for this test
        
        self.mock_session_repo.find_all.return_value = sessions
        self.mock_method_repo.find_by_id.return_value = {'id': 1, 'name': 'V60'}
        
        with patch('coffeejournal.services.brew_recommendations.enrich_brew_session_with_lookups') as mock_enrich:
            mock_enrich.side_effect = enriched_sessions
            result = self.service.get_recommendations(1)
        
        assert result['has_recommendations'] is True
        v60_rec = result['recommendations']['V60']
        
        # Should work despite string values and invalid data
        params = v60_rec['parameters']
        assert 'amount_coffee_grams' in params
        assert 'brew_ratio' in params
        
        # Should handle type conversion correctly
        if v60_rec['type'] == 'range':
            # Should use only valid numeric sessions (1 and 2)
            assert params['amount_coffee_grams']['min'] == 18.5
            assert params['amount_coffee_grams']['max'] == 20.0
        elif v60_rec['type'] == 'template':
            # Should use the best session's converted values
            assert params['amount_coffee_grams']['value'] == 20.0