"""
Unit tests for score calculation functionality.

Tests the centralized calculate_total_score function to ensure consistent
score calculation across the entire application.
"""

import pytest
from coffeejournal.api.utils import calculate_total_score


class TestScoreCalculation:
    """Test cases for the centralized score calculation function."""
    
    def test_uses_manual_score_when_available(self):
        """Test that manual score is used when provided and > 0."""
        session = {
            'score': 4.2,
            'sweetness': 8,
            'acidity': 7,
            'body': 6
        }
        
        result = calculate_total_score(session)
        assert result == 4.2
    
    def test_ignores_zero_manual_score(self):
        """Test that zero manual score triggers calculation."""
        session = {
            'score': 0,
            'sweetness': 8,
            'acidity': 7,
            'body': 6
        }
        
        result = calculate_total_score(session)
        assert result == 7.0  # (8+7+6)/3
    
    def test_ignores_null_manual_score(self):
        """Test that null manual score triggers calculation."""
        session = {
            'score': None,
            'sweetness': 8,
            'acidity': 7,
            'body': 6
        }
        
        result = calculate_total_score(session)
        assert result == 7.0  # (8+7+6)/3
    
    def test_calculates_from_taste_components(self):
        """Test calculation from all taste components."""
        session = {
            'score': None,
            'sweetness': 8,
            'acidity': 7,
            'body': 6,
            'aroma': 8,
            'bitterness': 3,  # Should become 10-3=7
            'flavor_profile_match': 9
        }
        
        result = calculate_total_score(session)
        # (8+7+6+8+7+9)/6 = 45/6 = 7.5
        assert result == 7.5
    
    def test_bitterness_inversion(self):
        """Test that bitterness is correctly inverted (10 - bitterness)."""
        session = {
            'score': None,
            'sweetness': 5,
            'bitterness': 2  # Should become 10-2=8
        }
        
        result = calculate_total_score(session)
        # (5+8)/2 = 6.5
        assert result == 6.5
    
    def test_skips_zero_and_negative_components(self):
        """Test that zero and negative taste components are ignored."""
        session = {
            'score': None,
            'sweetness': 8,
            'acidity': 0,     # Should be ignored
            'body': -1,       # Should be ignored
            'aroma': 7
        }
        
        result = calculate_total_score(session)
        # Only sweetness(8) and aroma(7): (8+7)/2 = 7.5
        assert result == 7.5
    
    def test_handles_missing_components(self):
        """Test calculation with only some components present."""
        session = {
            'score': None,
            'sweetness': 9,
            'aroma': 8
            # Missing other components
        }
        
        result = calculate_total_score(session)
        # (9+8)/2 = 8.5
        assert result == 8.5
    
    def test_returns_none_with_no_valid_components(self):
        """Test that None is returned when no valid components exist."""
        session = {
            'score': None,
            'sweetness': 0,
            'acidity': 0
        }
        
        result = calculate_total_score(session)
        assert result is None
    
    def test_handles_string_numeric_values(self):
        """Test that string representations of numbers are handled."""
        session = {
            'score': None,
            'sweetness': '8',
            'acidity': '7.5',
            'body': '6'
        }
        
        result = calculate_total_score(session)
        # (8+7.5+6)/3 = 7.2 (rounded to 1 decimal)
        assert result == 7.2
    
    def test_handles_invalid_values_gracefully(self):
        """Test that invalid values are ignored without error."""
        session = {
            'score': None,
            'sweetness': 'invalid',
            'acidity': 7,
            'body': None,
            'aroma': 8
        }
        
        result = calculate_total_score(session)
        # Only acidity(7) and aroma(8): (7+8)/2 = 7.5
        assert result == 7.5
    
    def test_rounding_to_one_decimal(self):
        """Test that results are rounded to one decimal place."""
        session = {
            'score': None,
            'sweetness': 8,
            'acidity': 7,
            'body': 6
        }
        
        result = calculate_total_score(session)
        # (8+7+6)/3 = 7.0 exactly
        assert result == 7.0
        assert isinstance(result, float)
    
    def test_edge_case_extreme_bitterness(self):
        """Test bitterness edge cases."""
        session = {
            'score': None,
            'sweetness': 5,
            'bitterness': 10  # Should become 10-10=0, ignored
        }
        
        result = calculate_total_score(session)
        # Only sweetness(5): 5.0
        assert result == 5.0
    
    def test_all_components_full_range(self):
        """Test with all components at various levels."""
        session = {
            'score': None,
            'sweetness': 10,
            'acidity': 9,
            'body': 8,
            'aroma': 7,
            'bitterness': 4,  # Becomes 6
            'flavor_profile_match': 8
        }
        
        result = calculate_total_score(session)
        # (10+9+8+7+6+8)/6 = 48/6 = 8.0
        assert result == 8.0


class TestScoreCalculationIntegration:
    """Integration tests for score calculation in API context."""
    
    def test_score_calculation_matches_frontend_logic(self):
        """Test that backend calculation matches the original frontend logic."""
        # This test case represents the exact calculation from BrewSessionTable.js
        session = {
            'score': None,
            'sweetness': 8,
            'acidity': 7,
            'body': 6,
            'aroma': 8,
            'bitterness': 3,  # Frontend: (10-3) = 7
            'flavor_profile_match': 9
        }
        
        # Frontend calculation: [8,7,6,8,7,9] -> 45/6 = 7.5
        expected = 7.5
        actual = calculate_total_score(session)
        
        assert actual == expected, f"Backend calculation {actual} doesn't match frontend expectation {expected}"
    
    def test_manual_score_precedence(self):
        """Test that manual score always takes precedence over calculated score."""
        session = {
            'score': 4.2,  # Manual score should be used
            'sweetness': 10,
            'acidity': 10,
            'body': 10,
            'aroma': 10,
            'bitterness': 1,  # Would calculate to much higher
            'flavor_profile_match': 10
        }
        
        result = calculate_total_score(session)
        assert result == 4.2  # Manual score used, not calculated ~9.8