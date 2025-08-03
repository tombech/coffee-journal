from typing import Dict, List, Optional, Any
from collections import Counter
from statistics import mean
from ..api.utils import calculate_total_score, enrich_brew_session_with_lookups


class BrewRecommendationService:
    """Service for generating brew recommendations based on historical session data."""
    
    def __init__(self, brew_session_repo, factory, brew_method_repo=None):
        self.brew_session_repo = brew_session_repo
        self.factory = factory
        self.brew_method_repo = brew_method_repo
        self.score_threshold = 3.5
        self.template_score_diff = 0.5
    
    def get_recommendations(self, product_id: int, method: str = None) -> Dict[str, Any]:
        """
        Get brew recommendations for a product, optionally filtered by method.
        
        Args:
            product_id: ID of the coffee product
            method: Optional brew method to filter by
            
        Returns:
            Dictionary with recommendations grouped by brew method
        """
        # Get all brew sessions for this product
        all_sessions = self.brew_session_repo.find_all()
        product_sessions = [s for s in all_sessions if s.get('product_id') == product_id]
        
        # Enrich sessions with lookup data and filter by score threshold
        good_sessions = []
        for session in product_sessions:
            # Enrich session with lookup objects
            enriched_session = enrich_brew_session_with_lookups(session, self.factory)
            
            total_score = calculate_total_score(enriched_session)
            if total_score and total_score > self.score_threshold:
                # Add the calculated score to the session for later use
                enriched_session['total_score'] = total_score
                good_sessions.append(enriched_session)
        
        if len(good_sessions) < 2:
            return {
                'has_recommendations': False,
                'message': 'Not enough information for brew setting recommendations yet. Need at least 2 sessions with score > 3.5.'
            }
        
        # Group by brew method
        methods = {}
        for session in good_sessions:
            # Get brew method name from ID (raw repository data format)
            brew_method_id = session.get('brew_method_id')
            brew_method = 'Unknown'
            
            if brew_method_id and self.brew_method_repo:
                brew_method_obj = self.brew_method_repo.find_by_id(brew_method_id)
                if brew_method_obj:
                    brew_method = brew_method_obj.get('name', 'Unknown')
            
            if brew_method not in methods:
                methods[brew_method] = []
            methods[brew_method].append(session)
        
        # Filter by specific method if requested
        if method:
            methods = {k: v for k, v in methods.items() if k == method}
        
        # Generate recommendations for each method
        recommendations = {}
        for brew_method, sessions in methods.items():
            if len(sessions) >= 2:  # Need at least 2 sessions per method
                method_rec = self._generate_method_recommendation(sessions)
                if method_rec:
                    recommendations[brew_method] = method_rec
        
        if not recommendations:
            return {
                'has_recommendations': False,
                'message': 'Not enough information for brew setting recommendations yet. Need at least 2 sessions per brew method with score > 3.5.'
            }
        
        return {
            'has_recommendations': True,
            'recommendations': recommendations
        }
    
    def _generate_method_recommendation(self, sessions: List[Dict]) -> Dict[str, Any]:
        """Generate recommendation for a specific brew method."""
        if not sessions:
            return None
        
        # Sort by calculated score descending
        sorted_sessions = sorted(sessions, key=lambda x: x.get('total_score', 0), reverse=True)
        top_sessions = sorted_sessions[:5]  # Top 5 sessions
        
        # Check if we should use template mode
        if len(top_sessions) > 1:
            best_score = top_sessions[0].get('total_score', 0)
            second_best = top_sessions[1].get('total_score', 0)
            
            if best_score - second_best >= self.template_score_diff:
                return self._create_template_recommendation(top_sessions[0], len(sessions))
        
        # Use range mode
        return self._create_range_recommendation(top_sessions, len(sessions))
    
    def _create_template_recommendation(self, template_session: Dict, total_sessions: int) -> Dict[str, Any]:
        """Create a template-based recommendation from the best session."""
        # Calculate brew ratio with type safety
        coffee_grams = template_session.get('amount_coffee_grams')
        water_grams = template_session.get('amount_water_grams')
        brew_ratio = None
        
        try:
            # Convert to float if they're strings
            if isinstance(coffee_grams, str):
                coffee_grams = float(coffee_grams) if coffee_grams.strip() else None
            if isinstance(water_grams, str):
                water_grams = float(water_grams) if water_grams.strip() else None
            
            if coffee_grams and water_grams and coffee_grams > 0:
                brew_ratio = round(water_grams / coffee_grams, 1)
        except (ValueError, TypeError):
            brew_ratio = None
        
        # Numeric fields to copy exactly
        numeric_fields = [
            'amount_coffee_grams', 'amount_water_grams', 'brew_temperature_c',
            'bloom_time_seconds', 'brew_time_seconds', 'grinder_setting'
        ]
        
        # Non-numeric fields to copy (these come from enriched data)
        categorical_fields = [
            'recipe', 'grinder', 'filter', 'kettle', 'scale'
        ]
        
        template = {}
        
        # Add brew ratio if available
        if brew_ratio:
            template['brew_ratio'] = {'value': brew_ratio, 'type': 'exact'}
        
        for field in numeric_fields:
            raw_value = template_session.get(field)
            if raw_value is not None:
                # Convert string values to numbers for consistency
                try:
                    if isinstance(raw_value, (int, float)):
                        value = float(raw_value)
                    elif isinstance(raw_value, str) and raw_value.strip():
                        value = float(raw_value)
                    else:
                        continue  # Skip non-numeric values
                    template[field] = {'value': value, 'type': 'exact'}
                except (ValueError, TypeError):
                    continue  # Skip values that can't be converted
        
        for field in categorical_fields:
            value = template_session.get(field)
            if value and isinstance(value, dict) and value.get('name'):
                template[field] = {'value': value['name'], 'type': 'exact'}
        
        return {
            'type': 'template',
            'source_score': template_session.get('total_score'),
            'source_date': template_session.get('timestamp', '').split('T')[0] if template_session.get('timestamp') else None,
            'total_sessions': total_sessions,
            'parameters': template
        }
    
    def _create_range_recommendation(self, sessions: List[Dict], total_sessions: int) -> Dict[str, Any]:
        """Create a range-based recommendation from multiple sessions."""
        # Calculate brew ratios for all sessions with type safety
        brew_ratios = []
        for session in sessions:
            coffee_grams = session.get('amount_coffee_grams')
            water_grams = session.get('amount_water_grams')
            
            try:
                # Convert to float if they're strings
                if isinstance(coffee_grams, str):
                    coffee_grams = float(coffee_grams) if coffee_grams.strip() else None
                if isinstance(water_grams, str):
                    water_grams = float(water_grams) if water_grams.strip() else None
                
                if coffee_grams and water_grams and coffee_grams > 0:
                    brew_ratios.append(round(water_grams / coffee_grams, 1))
            except (ValueError, TypeError):
                continue  # Skip sessions with invalid numeric data
        
        # Numeric fields to calculate ranges for
        numeric_fields = [
            'amount_coffee_grams', 'amount_water_grams', 'brew_temperature_c',
            'bloom_time_seconds', 'brew_time_seconds', 'grinder_setting'
        ]
        
        # Non-numeric fields to find most frequent
        categorical_fields = [
            'recipe', 'grinder', 'filter', 'kettle', 'scale'
        ]
        
        ranges = {}
        
        # Add brew ratio range if we have data
        if brew_ratios:
            ranges['brew_ratio'] = {
                'min': min(brew_ratios),
                'max': max(brew_ratios),
                'avg': round(mean(brew_ratios), 1),
                'type': 'range'
            }
        
        # Calculate ranges for numeric fields
        for field in numeric_fields:
            raw_values = [s.get(field) for s in sessions if s.get(field) is not None]
            # Convert to numbers and filter out non-numeric values
            values = []
            for val in raw_values:
                try:
                    if isinstance(val, (int, float)):
                        values.append(float(val))
                    elif isinstance(val, str) and val.strip():
                        values.append(float(val))
                except (ValueError, TypeError):
                    continue  # Skip non-numeric values
            
            if values:
                ranges[field] = {
                    'min': min(values),
                    'max': max(values),
                    'avg': round(mean(values), 1),
                    'type': 'range'
                }
        
        # Find most frequent for categorical fields
        for field in categorical_fields:
            # Extract names from enriched objects
            names = []
            for session in sessions:
                value = session.get(field)
                if value and isinstance(value, dict) and value.get('name'):
                    names.append(value['name'])
            
            if names:
                counter = Counter(names)
                most_common = counter.most_common(1)[0]
                ranges[field] = {
                    'value': most_common[0],
                    'frequency': most_common[1],
                    'total': len(names),
                    'type': 'frequent'
                }
        
        avg_score = round(mean([s.get('total_score', 0) for s in sessions]), 1)
        
        return {
            'type': 'range',
            'sessions_used': len(sessions),
            'avg_score': avg_score,
            'total_sessions': total_sessions,
            'parameters': ranges
        }