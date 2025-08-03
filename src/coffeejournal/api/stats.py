"""
Statistics API endpoints for Coffee Journal application.

This module provides aggregated statistics and analytics endpoints
that require complex calculations across multiple entities.
"""

from flask import Blueprint, jsonify, request
from ..repositories.factory import get_repository_factory
from .utils import enrich_product_with_lookups, get_user_id_from_request


def create_stats_blueprint():
    """Create the statistics API blueprint."""
    stats_bp = Blueprint('stats', __name__)

    def calculate_brew_score(session):
        """Calculate comprehensive score for a brew session."""
        # Use overall score if available
        if session.get('score') and session['score'] > 0:
            return session['score']
        
        # Otherwise calculate from tasting notes (bitterness is negative, others positive)
        tasting_notes = [
            session.get('sweetness'),
            session.get('acidity'),
            session.get('body'),
            session.get('aroma'),
            session.get('flavor_profile_match')
        ]
        tasting_notes = [score for score in tasting_notes if score and score > 0]
        
        # Bitterness is subtracted (inverted)
        bitterness_score = session.get('bitterness')
        if bitterness_score and bitterness_score > 0:
            inverted_bitterness = 10 - bitterness_score
            if inverted_bitterness > 0:
                tasting_notes.append(inverted_bitterness)
        
        return sum(tasting_notes) / len(tasting_notes) if tasting_notes else 0

    @stats_bp.route('/top-products', methods=['GET'])
    def get_top_products():
        """Get top products based on average brew scores with detailed analytics."""
        try:
            # Get query parameters
            limit = request.args.get('limit', 5, type=int)
            user_id = get_user_id_from_request()
            
            factory = get_repository_factory()
            brew_session_repo = factory.get_brew_session_repository(user_id)
            product_repo = factory.get_product_repository(user_id)
            
            # Get all brew sessions and products
            all_sessions = brew_session_repo.find_all()
            all_products = product_repo.find_all()
            
            # Group sessions by product and calculate statistics
            product_scores = {}
            
            for session in all_sessions:
                score = calculate_brew_score(session)
                product_id = session.get('product_id')
                
                if score > 0 and product_id:
                    if product_id not in product_scores:
                        product_scores[product_id] = {
                            'scores': [],
                            'sessions': [],
                            'product': next((p for p in all_products if p['id'] == product_id), None)
                        }
                    product_scores[product_id]['scores'].append(score)
                    product_scores[product_id]['sessions'].append(session)
            
            # Calculate averages and detailed analytics for each product
            result = []
            for product_id, data in product_scores.items():
                if not data['product'] or len(data['sessions']) == 0:
                    continue
                
                # Calculate tasting averages for radar chart
                valid_sessions = [s for s in data['sessions'] if any([
                    s.get('sweetness'), s.get('acidity'), s.get('bitterness'), 
                    s.get('body'), s.get('aroma')
                ])]
                
                averages = None
                if valid_sessions:
                    totals = {'sweetness': 0, 'acidity': 0, 'bitterness': 0, 'body': 0, 'aroma': 0}
                    counts = {'sweetness': 0, 'acidity': 0, 'bitterness': 0, 'body': 0, 'aroma': 0}
                    
                    for session in valid_sessions:
                        for attribute in ['sweetness', 'acidity', 'bitterness', 'body', 'aroma']:
                            value = session.get(attribute)
                            if value and value > 0:
                                totals[attribute] += value
                                counts[attribute] += 1
                    
                    averages = {
                        attr: totals[attr] / counts[attr] if counts[attr] > 0 else 0
                        for attr in ['sweetness', 'acidity', 'bitterness', 'body', 'aroma']
                    }
                
                # Calculate scores statistics
                scores = data['scores']
                avg_score = sum(scores) / len(scores)
                
                # Enrich the product with lookup data before returning
                enriched_product = enrich_product_with_lookups(data['product'].copy(), factory, user_id)
                
                result.append({
                    'product': enriched_product,
                    'avg_score': round(avg_score, 1),
                    'brew_count': len(data['sessions']),
                    'score_range': {
                        'min': round(min(scores), 1),
                        'max': round(max(scores), 1)
                    },
                    'tasting_averages': averages
                })
            
            # Sort by average score descending and limit
            result.sort(key=lambda x: x['avg_score'], reverse=True)
            
            return jsonify(result[:limit])
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return stats_bp