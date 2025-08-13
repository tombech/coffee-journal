"""
Test coffee age calculation functionality.
"""

import pytest
from datetime import datetime, timezone
from coffeejournal.api.utils import calculate_coffee_age


class TestCoffeeAgeCalculation:
    """Test the coffee age calculation utility function."""
    
    def test_same_day_brewing(self):
        """Test coffee brewed on the same day as roasting."""
        roast_date = "2025-01-20"
        brew_date = "2025-01-20T14:30:00"
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result == "same day"
    
    def test_one_day_age(self):
        """Test coffee brewed one day after roasting."""
        roast_date = "2025-01-20"
        brew_date = "2025-01-21T10:00:00"
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result == "1 day"
    
    def test_multiple_days_less_than_week(self):
        """Test coffee brewed multiple days but less than a week after roasting."""
        roast_date = "2025-01-20"
        brew_date = "2025-01-25T10:00:00"  # 5 days later
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result == "5 days"
    
    def test_exactly_one_week(self):
        """Test coffee brewed exactly one week after roasting."""
        roast_date = "2025-01-20"
        brew_date = "2025-01-27T10:00:00"  # 7 days later
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result == "1 week"
    
    def test_multiple_weeks(self):
        """Test coffee brewed multiple weeks after roasting."""
        roast_date = "2025-01-01"
        brew_date = "2025-01-15T10:00:00"  # 14 days = 2 weeks
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result == "2 weeks"
    
    def test_many_weeks(self):
        """Test coffee brewed many weeks after roasting."""
        roast_date = "2024-12-15"
        brew_date = "2025-08-13T10:00:00"  # About 35 weeks
        
        result = calculate_coffee_age(roast_date, brew_date)
        # Should be around 35 weeks, allowing for slight variation in rounding
        assert "weeks" in result
        weeks = int(result.split()[0])
        assert 34 <= weeks <= 36
    
    def test_timezone_aware_datetime(self):
        """Test with timezone-aware datetime strings."""
        roast_date = "2025-01-20"
        brew_date = "2025-01-27T10:00:00+00:00"  # UTC timezone
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result == "1 week"
    
    def test_timezone_z_suffix(self):
        """Test with Z suffix for UTC timezone."""
        roast_date = "2025-01-20"
        brew_date = "2025-01-27T10:00:00Z"  # Z suffix for UTC
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result == "1 week"
    
    def test_complex_timezone_string(self):
        """Test with complex timezone string from real data."""
        roast_date = "2024-12-15"
        brew_date = "2025-08-13T06:17:17.625629+00:00"
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert "weeks" in result
        weeks = int(result.split()[0])
        assert weeks > 30  # Should be many weeks
    
    def test_invalid_roast_date(self):
        """Test with invalid roast date."""
        roast_date = "invalid-date"
        brew_date = "2025-01-27T10:00:00"
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result is None
    
    def test_invalid_brew_date(self):
        """Test with invalid brew date."""
        roast_date = "2025-01-20"
        brew_date = "invalid-datetime"
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result is None
    
    def test_missing_roast_date(self):
        """Test with missing roast date."""
        roast_date = None
        brew_date = "2025-01-27T10:00:00"
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result is None
    
    def test_missing_brew_date(self):
        """Test with missing brew date."""
        roast_date = "2025-01-20"
        brew_date = None
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result is None
    
    def test_empty_string_dates(self):
        """Test with empty string dates."""
        roast_date = ""
        brew_date = ""
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result is None
    
    def test_brew_before_roast(self):
        """Test invalid case where brew date is before roast date."""
        roast_date = "2025-01-27"
        brew_date = "2025-01-20T10:00:00"  # Before roast date
        
        result = calculate_coffee_age(roast_date, brew_date)
        assert result is None
    
    def test_datetime_objects(self):
        """Test with actual datetime objects instead of strings."""
        roast_dt = datetime(2025, 1, 20)
        brew_dt = datetime(2025, 1, 27, 10, 0, 0)
        
        result = calculate_coffee_age(roast_dt, brew_dt)
        assert result == "1 week"
    
    def test_rounding_to_nearest_week(self):
        """Test that days are properly rounded to nearest week."""
        roast_date = "2025-01-01"
        
        # 10 days = 1.43 weeks, should round to 1 week
        brew_date_10_days = "2025-01-11T10:00:00"
        result = calculate_coffee_age(roast_date, brew_date_10_days)
        assert result == "1 week"
        
        # 11 days = 1.57 weeks, should round to 2 weeks
        brew_date_11_days = "2025-01-12T10:00:00"
        result = calculate_coffee_age(roast_date, brew_date_11_days)
        assert result == "2 weeks"