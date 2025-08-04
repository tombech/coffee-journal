"""
Prose generator for brew recommendations.
Converts structured recommendation data into natural, conversational text.
"""
import random
from typing import Dict, List, Any, Optional
from math import floor


class BrewProseGenerator:
    """Generate natural language brew recommendations from structured data."""
    
    def __init__(self):
        # Define multiple template styles for variety
        self.templates = {
            'single_best': [
                "Your best brew with this coffee used {coffee}g to {water}g of water ({ratio} ratio) ground on the {grinder} at {grind_setting}. With {temp} water and the {filter} filter, you achieved a {score}/10 using the \"{recipe}\" recipe. Start with a {bloom} bloom, then complete the pour sequence for a total time of {brew_time}. Since this was your standout session, I'd stick closely to these exact parameters.",
                
                "That exceptional {score}/10 brew you had used {coffee}g coffee to {water}g water ({ratio} ratio). The {grinder} at {grind_setting} with {temp} water really hit the mark. Using the {filter} filter and \"{recipe}\" recipe, you bloomed for {bloom} and finished in {brew_time}. This combination clearly works perfectly for this coffee.",
                
                "Recreate your top-scoring session: {coffee}g coffee, {water}g water ({ratio} ratio), {grinder} grinder at {grind_setting}. Heat water to {temp} and use the {filter} filter. Follow the \"{recipe}\" recipe with a {bloom} bloom, aiming for {brew_time} total. This exact setup gave you a {score}/10 last time."
            ],
            
            'multiple_consistent': [
                "Based on your top {count} {method} brews (averaging {avg_score}/10) for this roast, I'd recommend using {coffee}g of coffee to {water}g of water ({ratio} ratio). Grind the beans using the {grinder} set to {grind_setting} and heat the water to {temp}. The \"{recipe}\" recipe has been working well with the {filter} filter. Let the coffee bloom for {bloom}, then follow the recipe aiming for a total brew time of {brew_time}.",
                
                "Looking at your {count} successful {method} sessions (averaging {avg_score}/10), I'd suggest starting with {coffee}g of coffee to {water}g of water ({ratio} ratio). The {grinder} grinder at {grind_setting} has worked well. Use {temp} water with the {filter} filter. Bloom for {bloom} before continuing with the \"{recipe}\" recipe for about {brew_time} total brew time.",
                
                "You've consistently had great results with this coffee using the {grinder} at {grind_setting} and the {filter} filter. Stick with {coffee}g coffee to {water}g water (your usual {ratio} ratio) at {temp}. The \"{recipe}\" recipe with a {bloom} bloom typically takes you {brew_time}."
            ],
            
            'multiple_variable': [
                "Your successful brews with this coffee have been quite flexible - anywhere from {coffee_range} coffee to {water_range} water ({ratio_range} ratio) has worked well. The {grinder} grinder at {grind_range} paired with the {filter} filter does the job. Water at {temp} seems to be your sweet spot. Bloom for {bloom_range}, then follow the \"{recipe}\" recipe for a total time between {brew_time_range}.",
                
                "Looking at your {count} best {method} brews (averaging {avg_score}/10), there's some room to experiment. Use {coffee_range} coffee with {water_range} water for a {ratio_range} ratio. Set your {grinder} between {grind_range} and heat water to {temp}. The {filter} filter with the \"{recipe}\" recipe has been reliable. After a {bloom_range} bloom, aim for {brew_time_range} total.",
                
                "From your successful sessions, I'd start with {coffee}g coffee to {water}g water ({ratio} ratio), though {coffee_range} to {water_range} has all worked. The {grinder} at {grind_setting} (or anywhere from {grind_range}) with {temp} water gives good results. Use the {filter} filter, bloom for {bloom}, and follow the \"{recipe}\" recipe for about {brew_time}."
            ]
        }
    
    def generate_prose(self, method: str, recommendation: Dict[str, Any], sessions: List[Dict[str, Any]]) -> str:
        """
        Generate prose recommendation based on recommendation type and data.
        
        Args:
            method: Brew method name
            recommendation: Structured recommendation data
            sessions: List of brew sessions used for the recommendation
            
        Returns:
            Natural language recommendation text
        """
        if recommendation['type'] == 'template':
            return self._generate_template_prose(method, recommendation, sessions)
        else:
            return self._generate_range_prose(method, recommendation, sessions)
    
    def _generate_template_prose(self, method: str, rec: Dict[str, Any], sessions: List[Dict[str, Any]]) -> str:
        """Generate prose for template-based (single best) recommendations."""
        template = random.choice(self.templates['single_best'])
        params = rec['parameters']
        
        # Extract values and format them
        values = {
            'method': method,
            'score': f"{rec['source_score']:.1f}" if rec.get('source_score') else "N/A",
            'coffee': self._format_number(params.get('amount_coffee_grams', {}).get('value')),
            'water': self._format_number(params.get('amount_water_grams', {}).get('value')),
            'ratio': self._format_ratio_single(params.get('brew_ratio', {}).get('value')),
            'grinder': self._get_short_name(params.get('grinder', {}).get('value', 'your grinder')),
            'grind_setting': params.get('grinder_setting', {}).get('value', 'your usual setting'),
            'temp': self._format_temperature_single(params.get('brew_temperature_c', {}).get('value')),
            'filter': self._get_short_name(params.get('filter', {}).get('value', 'your filter')),
            'recipe': self._get_short_name(params.get('recipe', {}).get('value', 'your recipe')),
            'bloom': self._format_time(params.get('bloom_time_seconds', {}).get('value')),
            'brew_time': self._format_time(params.get('brew_time_seconds', {}).get('value'))
        }
        
        return template.format(**values)
    
    def _generate_range_prose(self, method: str, rec: Dict[str, Any], sessions: List[Dict[str, Any]]) -> str:
        """Generate prose for range-based recommendations."""
        params = rec['parameters']
        
        # Determine if we have consistent or variable parameters
        has_ranges = self._has_significant_ranges(params)
        
        if has_ranges:
            template = random.choice(self.templates['multiple_variable'])
        else:
            template = random.choice(self.templates['multiple_consistent'])
        
        # Get the best session's temperature
        best_session = max(sessions, key=lambda x: x.get('total_score', 0))
        best_temp = best_session.get('brew_temperature_c')
        
        # Extract and format values
        values = {
            'method': method,
            'count': rec.get('sessions_used', len(sessions)),
            'avg_score': f"{rec.get('avg_score', 0):.1f}",
            'coffee': self._format_number(self._get_value_or_avg(params.get('amount_coffee_grams', {}))),
            'water': self._format_number(self._get_value_or_avg(params.get('amount_water_grams', {}))),
            'ratio': self._format_ratio_single(self._get_value_or_avg(params.get('brew_ratio', {}))),
            'grinder': self._get_short_name(self._get_frequent_equipment(params.get('grinder', {}))),
            'grind_setting': self._format_grind_setting(params.get('grinder_setting', {})),
            'temp': self._format_temperature_with_range(best_temp, params.get('brew_temperature_c', {})),
            'filter': self._get_short_name(self._get_frequent_equipment(params.get('filter', {}))),
            'recipe': self._get_short_name(self._get_frequent_equipment(params.get('recipe', {}))),
            'bloom': self._format_time(self._get_value_or_avg(params.get('bloom_time_seconds', {}))),
            'brew_time': self._format_time(self._get_value_or_avg(params.get('brew_time_seconds', {})))
        }
        
        # Add range values if needed
        if has_ranges:
            values.update({
                'coffee_range': self._format_range(params.get('amount_coffee_grams', {}), 'g'),
                'water_range': self._format_range(params.get('amount_water_grams', {}), 'g'),
                'ratio_range': self._format_ratio_range(params.get('brew_ratio', {})),
                'grind_range': self._format_grind_range(params.get('grinder_setting', {})),
                'bloom_range': self._format_time_range(params.get('bloom_time_seconds', {})),
                'brew_time_range': self._format_time_range(params.get('brew_time_seconds', {}))
            })
        
        return template.format(**values)
    
    def _has_significant_ranges(self, params: Dict[str, Any]) -> bool:
        """Check if parameters have significant ranges worth mentioning."""
        for param, data in params.items():
            if data.get('type') == 'range':
                min_val = data.get('min', 0)
                max_val = data.get('max', 0)
                # Consider it a range if values differ by more than 10%
                if min_val > 0 and (max_val - min_val) / min_val > 0.1:
                    return True
        return False
    
    def _format_number(self, value: Optional[float]) -> str:
        """Format a number, rounding to whole number."""
        if value is None:
            return "N/A"
        return str(int(round(value)))
    
    def _format_ratio_single(self, value: Optional[float]) -> str:
        """Format a single ratio value."""
        if value is None:
            return "N/A"
        return f"1:{int(round(value))}"
    
    def _format_ratio_range(self, data: Dict[str, Any]) -> str:
        """Format a ratio range."""
        if not data or data.get('type') != 'range':
            return "N/A"
        min_val = data.get('min')
        max_val = data.get('max')
        if min_val == max_val:
            return f"1:{int(round(min_val))}"
        return f"1:{int(round(min_val))} to 1:{int(round(max_val))}"
    
    def _format_temperature_single(self, value: Optional[float]) -> str:
        """Format a single temperature value."""
        if value is None:
            return "N/A"
        return f"{int(round(value))}°C"
    
    def _format_temperature_with_range(self, best_temp: Optional[float], temp_data: Dict[str, Any]) -> str:
        """Format temperature with the best value and range in parentheses."""
        if best_temp is None:
            return "N/A"
        
        best_rounded = int(round(best_temp))
        
        if temp_data.get('type') == 'range':
            min_temp = int(round(temp_data.get('min', best_temp)))
            max_temp = int(round(temp_data.get('max', best_temp)))
            if min_temp == max_temp:
                return f"{best_rounded}°C"
            return f"{best_rounded}°C ({min_temp}-{max_temp}°C)"
        
        return f"{best_rounded}°C"
    
    def _format_time(self, seconds: Optional[float]) -> str:
        """Format time in seconds to MM:SS or seconds format, rounded to nearest 15s."""
        if seconds is None:
            return "N/A"
        
        # Round to nearest 15 seconds
        seconds = int(round(seconds / 15) * 15)
        
        if seconds >= 60:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}:{secs:02d}"
        return f"{seconds} seconds"
    
    def _format_time_range(self, data: Dict[str, Any]) -> str:
        """Format a time range, rounded to nearest 15s."""
        if not data or data.get('type') != 'range':
            return "N/A"
        
        # Round both min and max to nearest 15 seconds
        min_sec = int(round(data.get('min', 0) / 15) * 15)
        max_sec = int(round(data.get('max', 0) / 15) * 15)
        
        if min_sec == max_sec:
            return self._format_time(min_sec)
        
        return f"{self._format_time(min_sec)} to {self._format_time(max_sec)}"
    
    def _format_range(self, data: Dict[str, Any], unit: str = '') -> str:
        """Format a numeric range with unit."""
        if not data or data.get('type') != 'range':
            return "N/A"
        
        min_val = int(round(data.get('min', 0)))
        max_val = int(round(data.get('max', 0)))
        
        if min_val == max_val:
            return f"{min_val}{unit}"
        return f"{min_val}-{max_val}{unit}"
    
    def _format_grind_setting(self, data: Dict[str, Any]) -> str:
        """Format grind setting (can be numeric or string)."""
        if data.get('type') == 'exact':
            return str(data.get('value', 'N/A'))
        elif data.get('type') == 'range':
            # For range, just return the average or most common
            return str(int(round(data.get('avg', 0))))
        elif data.get('type') == 'frequent':
            return str(data.get('value', 'N/A'))
        return 'N/A'
    
    def _format_grind_range(self, data: Dict[str, Any]) -> str:
        """Format grind setting range (handles both numeric and string settings)."""
        if not data or data.get('type') != 'range':
            return "N/A"
        
        # For string grind settings, we'd need the actual values from sessions
        # For now, assume numeric
        min_val = data.get('min', 0)
        max_val = data.get('max', 0)
        
        if min_val == max_val:
            return str(int(min_val))
        return f"{int(min_val)} to {int(max_val)}"
    
    def _get_value_or_avg(self, data: Dict[str, Any]) -> Optional[float]:
        """Get exact value or average from recommendation data."""
        if data.get('type') == 'exact':
            return data.get('value')
        elif data.get('type') == 'range':
            return data.get('avg')
        return None
    
    def _get_frequent_value(self, data: Dict[str, Any]) -> str:
        """Get the most frequent value from recommendation data."""
        if data.get('type') == 'frequent':
            return data.get('value', 'N/A')
        elif data.get('type') == 'exact':
            return data.get('value', 'N/A')
        return 'N/A'
    
    def _get_frequent_equipment(self, data: Dict[str, Any]) -> Any:
        """Get the most frequent equipment object from recommendation data."""
        if data.get('type') == 'frequent':
            return data.get('value', 'N/A')
        elif data.get('type') == 'exact':
            return data.get('value', 'N/A')
        return 'N/A'
    
    def _get_short_name(self, equipment_data: dict) -> str:
        """Get short form of equipment name from enriched data."""
        if isinstance(equipment_data, dict):
            # Equipment data is enriched with short_form field
            return equipment_data.get('short_form', equipment_data.get('name', 'N/A'))
        elif isinstance(equipment_data, str):
            # Fallback for string equipment names
            return equipment_data
        return 'N/A'