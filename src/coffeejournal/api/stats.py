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
        """Get top products based on average brew and shot scores with detailed analytics."""
        try:
            # Get query parameters
            limit = request.args.get('limit', 5, type=int)
            user_id = get_user_id_from_request()
            
            factory = get_repository_factory()
            brew_session_repo = factory.get_brew_session_repository(user_id)
            shot_repo = factory.get_shot_repository(user_id)
            product_repo = factory.get_product_repository(user_id)
            
            # Get all brew sessions, shots, and products
            all_sessions = brew_session_repo.find_all()
            all_shots = shot_repo.find_all()
            all_products = product_repo.find_all()
            
            # Group sessions and shots by product and calculate statistics
            product_scores = {}
            
            # Process brew sessions
            for session in all_sessions:
                score = calculate_brew_score(session)
                product_id = session.get('product_id')
                
                if score > 0 and product_id:
                    if product_id not in product_scores:
                        product_scores[product_id] = {
                            'scores': [],
                            'sessions': [],
                            'shots': [],
                            'product': next((p for p in all_products if p['id'] == product_id), None)
                        }
                    product_scores[product_id]['scores'].append(score)
                    product_scores[product_id]['sessions'].append(session)
            
            # Process shots
            for shot in all_shots:
                shot_score = shot.get('overall_score') or shot.get('calculated_score', 0)
                product_id = shot.get('product_id')
                
                if shot_score and shot_score > 0 and product_id:
                    if product_id not in product_scores:
                        product_scores[product_id] = {
                            'scores': [],
                            'sessions': [],
                            'shots': [],
                            'product': next((p for p in all_products if p['id'] == product_id), None)
                        }
                    product_scores[product_id]['scores'].append(shot_score)
                    product_scores[product_id]['shots'].append(shot)
            
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
                    'shot_count': len(data['shots']),
                    'total_count': len(data['sessions']) + len(data['shots']),
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

    @stats_bp.route('/products/<int:product_id>', methods=['GET'])
    def get_product_stats(product_id):
        """Get detailed statistics for a specific product including brew sessions and shots."""
        try:
            user_id = get_user_id_from_request()
            factory = get_repository_factory()
            
            brew_session_repo = factory.get_brew_session_repository(user_id)
            shot_repo = factory.get_shot_repository(user_id)
            batch_repo = factory.get_batch_repository(user_id)
            
            # Get all brew sessions and shots for this product
            all_sessions = brew_session_repo.find_all()
            product_sessions = [s for s in all_sessions if s.get('product_id') == product_id]
            
            all_shots = shot_repo.find_all()
            product_shots = [s for s in all_shots if s.get('product_id') == product_id]
            
            # Calculate statistics
            total_sessions = len(product_sessions)
            total_shots = len(product_shots)
            scores = []
            
            # Collect scores from brew sessions
            for session in product_sessions:
                score = calculate_brew_score(session)
                if score > 0:
                    scores.append(score)
            
            # Collect scores from shots
            for shot in product_shots:
                shot_score = shot.get('overall_score') or shot.get('calculated_score', 0)
                if shot_score and shot_score > 0:
                    scores.append(shot_score)
            
            # Get top and bottom 5 sessions by score
            sorted_sessions = sorted(product_sessions, 
                                    key=lambda s: calculate_brew_score(s), 
                                    reverse=True)
            top_5_sessions = sorted_sessions[:5]
            bottom_5_sessions = sorted_sessions[-5:] if len(sorted_sessions) > 5 else []
            
            # Get top and bottom 5 shots by score
            sorted_shots = sorted([s for s in product_shots if s.get('overall_score') or s.get('calculated_score')], 
                                key=lambda s: s.get('overall_score') or s.get('calculated_score', 0), 
                                reverse=True)
            top_5_shots = sorted_shots[:5]
            bottom_5_shots = sorted_shots[-5:] if len(sorted_shots) > 5 else []
            
            # Get batch statistics
            all_batches = batch_repo.find_all()
            product_batches = [b for b in all_batches if b.get('product_id') == product_id]
            
            return jsonify({
                'total_brew_sessions': total_sessions,
                'total_shots': total_shots,
                'total_batches': len(product_batches),
                'average_score': round(sum(scores) / len(scores), 1) if scores else 0,
                'score_range': {
                    'min': round(min(scores), 1) if scores else 0,
                    'max': round(max(scores), 1) if scores else 0
                },
                'top_5_sessions': top_5_sessions,
                'bottom_5_sessions': bottom_5_sessions,
                'top_5_shots': top_5_shots,
                'bottom_5_shots': bottom_5_shots,
                'recent_5_sessions': product_sessions[-5:] if product_sessions else [],
                'recent_5_shots': product_shots[-5:] if product_shots else []
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @stats_bp.route('/batches/<int:batch_id>', methods=['GET'])
    def get_batch_stats(batch_id):
        """Get detailed statistics for a specific batch."""
        try:
            user_id = get_user_id_from_request()
            factory = get_repository_factory()
            
            brew_session_repo = factory.get_brew_session_repository(user_id)
            shot_repo = factory.get_shot_repository(user_id)
            
            # Get all brew sessions for this batch
            all_sessions = brew_session_repo.find_all()
            batch_sessions = [s for s in all_sessions if s.get('product_batch_id') == batch_id]
            
            # Get all shots for this batch
            all_shots = shot_repo.find_all()
            batch_shots = [s for s in all_shots if s.get('product_batch_id') == batch_id]
            
            # Calculate brew session statistics
            total_sessions = len(batch_sessions)
            total_shots = len(batch_shots)
            scores = []
            
            for session in batch_sessions:
                score = calculate_brew_score(session)
                if score > 0:
                    scores.append(score)
            
            # Calculate shot scores
            for shot in batch_shots:
                shot_score = shot.get('overall_score', 0)
                if shot_score and shot_score > 0:
                    scores.append(shot_score)
            
            # Get top and bottom 5 sessions by score
            sorted_sessions = sorted(batch_sessions, 
                                    key=lambda s: calculate_brew_score(s), 
                                    reverse=True)
            top_5 = sorted_sessions[:5]
            bottom_5 = sorted_sessions[-5:] if len(sorted_sessions) > 5 else []
            
            # Calculate total coffee used
            total_coffee_grams = 0
            for session in batch_sessions:
                coffee_amount = session.get('amount_coffee_grams', 0)
                if coffee_amount:
                    total_coffee_grams += coffee_amount
            
            for shot in batch_shots:
                dose_amount = shot.get('dose_grams', 0)
                if dose_amount:
                    total_coffee_grams += dose_amount
            
            # Calculate usage statistics
            batch_repo = factory.get_batch_repository(user_id)
            batch = batch_repo.find_by_id(batch_id)
            batch_amount = batch.get('amount_grams', 0) if batch else 0

            coffee_remaining = max(0, batch_amount - total_coffee_grams)

            # Calculate sessions remaining estimate
            total_uses = total_sessions + total_shots
            sessions_remaining_estimate = 0
            average_coffee_per_use = 0

            if total_uses > 0:
                average_coffee_per_use = total_coffee_grams / total_uses
                if coffee_remaining > 0 and average_coffee_per_use > 0:
                    sessions_remaining_estimate = int(coffee_remaining / average_coffee_per_use)

            # Calculate rating breakdown from brew sessions
            rating_breakdown = {
                'overall': [],
                'aroma': [],
                'acidity': [],
                'body': [],
                'flavor': [],
                'aftertaste': []
            }

            for session in batch_sessions:
                for rating_type in rating_breakdown.keys():
                    value = session.get(f'rating_{rating_type}')
                    if value and isinstance(value, (int, float)):
                        rating_breakdown[rating_type].append(value)

            # Calculate averages for rating breakdown
            for rating_type, values in rating_breakdown.items():
                if values:
                    rating_breakdown[rating_type] = {
                        'avg': round(sum(values) / len(values), 1),
                        'count': len(values),
                        'min': min(values),
                        'max': max(values)
                    }
                else:
                    rating_breakdown[rating_type] = None

            return jsonify({
                'total_brew_sessions': total_sessions,
                'total_shots': total_shots,
                'total_coffee_used': total_coffee_grams,
                'coffee_remaining': coffee_remaining,
                'sessions_remaining_estimate': sessions_remaining_estimate,
                'average_coffee_per_use': round(average_coffee_per_use, 1) if average_coffee_per_use > 0 else 0,
                'average_score': round(sum(scores) / len(scores), 1) if scores else 0,
                'score_range': {
                    'min': round(min(scores), 1) if scores else 0,
                    'max': round(max(scores), 1) if scores else 0
                },
                'rating_breakdown': rating_breakdown
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @stats_bp.route('/roasters/<int:roaster_id>', methods=['GET'])
    def get_roaster_stats(roaster_id):
        """Get detailed statistics for a specific roaster."""
        try:
            user_id = get_user_id_from_request()
            factory = get_repository_factory()
            
            product_repo = factory.get_product_repository(user_id)
            brew_session_repo = factory.get_brew_session_repository(user_id)
            
            # Get all products from this roaster
            all_products = product_repo.find_all()
            roaster_products = [p for p in all_products if p.get('roaster_id') == roaster_id]
            product_ids = [p['id'] for p in roaster_products]
            
            # Get all brew sessions for these products
            all_sessions = brew_session_repo.find_all()
            roaster_sessions = [s for s in all_sessions if s.get('product_id') in product_ids]
            
            # Calculate statistics
            total_sessions = len(roaster_sessions)
            scores = []
            for session in roaster_sessions:
                score = calculate_brew_score(session)
                if score > 0:
                    scores.append(score)
            
            # Get top and bottom 5 sessions by score
            sorted_sessions = sorted(roaster_sessions, 
                                    key=lambda s: calculate_brew_score(s), 
                                    reverse=True)
            top_5 = sorted_sessions[:5]
            bottom_5 = sorted_sessions[-5:] if len(sorted_sessions) > 5 else []
            
            return jsonify({
                'total_products': len(roaster_products),
                'total_brew_sessions': total_sessions,
                'average_score': round(sum(scores) / len(scores), 1) if scores else 0,
                'score_range': {
                    'min': round(min(scores), 1) if scores else 0,
                    'max': round(max(scores), 1) if scores else 0
                },
                'top_5_sessions': top_5,
                'bottom_5_sessions': bottom_5
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @stats_bp.route('/brew_methods/<int:method_id>', methods=['GET'])
    def get_brew_method_stats(method_id):
        """Get detailed statistics for a specific brew method."""
        try:
            user_id = get_user_id_from_request()
            factory = get_repository_factory()
            
            brew_session_repo = factory.get_brew_session_repository(user_id)
            
            # Get all brew sessions using this method
            all_sessions = brew_session_repo.find_all()
            method_sessions = [s for s in all_sessions if s.get('brew_method_id') == method_id]
            
            # Calculate statistics
            total_sessions = len(method_sessions)
            scores = []
            for session in method_sessions:
                score = calculate_brew_score(session)
                if score > 0:
                    scores.append(score)
            
            # Get top and bottom 5 sessions by score
            sorted_sessions = sorted(method_sessions, 
                                    key=lambda s: calculate_brew_score(s), 
                                    reverse=True)
            top_5 = sorted_sessions[:5]
            bottom_5 = sorted_sessions[-5:] if len(sorted_sessions) > 5 else []
            
            return jsonify({
                'total_brew_sessions': total_sessions,
                'average_score': round(sum(scores) / len(scores), 1) if scores else 0,
                'score_range': {
                    'min': round(min(scores), 1) if scores else 0,
                    'max': round(max(scores), 1) if scores else 0
                },
                'top_5_sessions': top_5,
                'bottom_5_sessions': bottom_5
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @stats_bp.route('/filters/<int:filter_id>', methods=['GET'])
    def get_filter_stats(filter_id):
        """Get detailed statistics for a specific filter."""
        try:
            user_id = get_user_id_from_request()
            factory = get_repository_factory()
            
            brew_session_repo = factory.get_brew_session_repository(user_id)
            
            # Get all brew sessions using this filter
            all_sessions = brew_session_repo.find_all()
            filter_sessions = [s for s in all_sessions if s.get('filter_id') == filter_id]
            
            # Calculate statistics
            total_sessions = len(filter_sessions)
            scores = []
            for session in filter_sessions:
                score = calculate_brew_score(session)
                if score > 0:
                    scores.append(score)
            
            # Get top and bottom 5 sessions by score
            sorted_sessions = sorted(filter_sessions, 
                                    key=lambda s: calculate_brew_score(s), 
                                    reverse=True)
            top_5 = sorted_sessions[:5]
            bottom_5 = sorted_sessions[-5:] if len(sorted_sessions) > 5 else []
            
            return jsonify({
                'total_brew_sessions': total_sessions,
                'average_score': round(sum(scores) / len(scores), 1) if scores else 0,
                'score_range': {
                    'min': round(min(scores), 1) if scores else 0,
                    'max': round(max(scores), 1) if scores else 0
                },
                'top_5_sessions': top_5,
                'bottom_5_sessions': bottom_5
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @stats_bp.route('/grinders/<int:grinder_id>', methods=['GET'])
    def get_grinder_stats(grinder_id):
        """Get detailed statistics for a specific grinder."""
        try:
            user_id = get_user_id_from_request()
            factory = get_repository_factory()
            
            grinder_repo = factory.get_grinder_repository(user_id)
            brew_session_repo = factory.get_brew_session_repository(user_id)
            
            # Use the repository method for core statistics
            core_stats = grinder_repo.get_usage_stats(grinder_id, factory)
            
            # Get brew sessions for score calculations
            all_sessions = brew_session_repo.find_all()
            grinder_sessions = [s for s in all_sessions if s.get('grinder_id') == grinder_id]
            
            # Calculate scores for additional statistics
            scores = []
            for session in grinder_sessions:
                score = calculate_brew_score(session)
                if score > 0:
                    scores.append(score)
            
            # Get top and bottom 5 sessions by score
            sorted_sessions = sorted(grinder_sessions, 
                                    key=lambda s: calculate_brew_score(s), 
                                    reverse=True)
            top_5 = sorted_sessions[:5]
            bottom_5 = sorted_sessions[-5:] if len(sorted_sessions) > 5 else []
            
            # Combine core stats with additional scoring statistics
            result = core_stats.copy()
            result.update({
                'total_brew_sessions': core_stats['total_brews'],  # Alias for consistency with other endpoints
                'average_score': round(sum(scores) / len(scores), 1) if scores else 0,
                'score_range': {
                    'min': round(min(scores), 1) if scores else 0,
                    'max': round(max(scores), 1) if scores else 0
                },
                'top_5_sessions': top_5,
                'bottom_5_sessions': bottom_5
            })
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return stats_bp