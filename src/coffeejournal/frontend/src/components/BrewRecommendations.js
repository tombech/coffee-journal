import React, { useState, useEffect } from 'react';
import { apiFetch } from '../config';

function BrewRecommendations({ productId, selectedMethod, onApplyRecommendation }) {
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!productId) {
      setRecommendations(null);
      return;
    }

    const fetchRecommendations = async () => {
      setLoading(true);
      setError(null);
      try {
        const params = selectedMethod ? `?method=${encodeURIComponent(selectedMethod)}` : '';
        const response = await apiFetch(`/products/${productId}/brew_recommendations${params}`);
        
        if (response.ok) {
          const data = await response.json();
          setRecommendations(data);
        } else {
          const errorData = await response.json();
          setError(errorData.error || 'Failed to fetch recommendations');
        }
      } catch (err) {
        setError('Error fetching recommendations');
        console.error('Error fetching recommendations:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchRecommendations();
  }, [productId, selectedMethod]);

  const handleApplyRecommendation = (method, parameters) => {
    const formData = {};
    
    // Apply exact values or ranges
    Object.entries(parameters).forEach(([param, data]) => {
      if (data.type === 'exact') {
        formData[param] = data.value;
      } else if (data.type === 'range') {
        // Use the average for ranges
        formData[param] = data.avg;
      } else if (data.type === 'frequent') {
        formData[param] = data.value;
      }
    });

    // Set the brew method
    formData.brew_method = method;

    onApplyRecommendation(formData);
  };

  // Helper functions for conversational text
  const getConversationalText = (method, rec) => {
    if (rec.type === 'template') {
      return `Based on your best ${method} session (scored ${rec.source_score}/5), I'd recommend replicating those exact settings. That brew was clearly exceptional!`;
    } else {
      return `Looking at your ${rec.sessions_used} successful ${method} brews (averaging ${rec.avg_score}/5), here's what typically works well for this coffee:`;
    }
  };

  const getParameterDescription = (param, data) => {
    const descriptions = {
      'amount_coffee_grams': {
        name: 'Coffee',
        unit: 'g',
        advice: {
          exact: (val) => `Use exactly ${val}g of coffee`,
          range: (min, max, avg) => `Use ${min}-${max}g of coffee (${avg}g is your sweet spot)`,
          frequent: (val, freq, total) => `Use ${val}g of coffee (worked ${freq}/${total} times)`
        }
      },
      'amount_water_grams': {
        name: 'Water',
        unit: 'g', 
        advice: {
          exact: (val) => `Add ${val}g of water`,
          range: (min, max, avg) => `Use ${min}-${max}g of water (aim for ${avg}g)`,
          frequent: (val, freq, total) => `Use ${val}g of water (your go-to amount)`
        }
      },
      'brew_ratio': {
        name: 'Brew Ratio',
        unit: ':1',
        advice: {
          exact: (val) => `Stick to a ${val}:1 water-to-coffee ratio`,
          range: (min, max, avg) => `Try a ${min}:1 to ${max}:1 ratio (${avg}:1 works well)`,
          frequent: (val, freq, total) => `Use a ${val}:1 ratio (your favorite)`
        }
      },
      'brew_temperature_c': {
        name: 'Water Temperature', 
        unit: '°C',
        advice: {
          exact: (val) => `Heat water to ${val}°C`,
          range: (min, max, avg) => `Water temperature: ${min}-${max}°C (${avg}°C is ideal)`,
          frequent: (val, freq, total) => `Use ${val}°C water (consistently good results)`
        }
      },
      'grinder_setting': {
        name: 'Grind Setting',
        unit: '',
        advice: {
          exact: (val) => `Set grinder to ${val}`,
          range: (min, max, avg) => `Grind setting: ${min}-${max} (try ${avg})`,
          frequent: (val, freq, total) => `Grind at setting ${val} (reliable choice)`
        }
      },
      'bloom_time_seconds': {
        name: 'Bloom Time',
        unit: 's',
        advice: {
          exact: (val) => `Bloom for ${val} seconds`,
          range: (min, max, avg) => `Bloom for ${min}-${max} seconds (${avg}s typically)`,
          frequent: (val, freq, total) => `Bloom for ${val} seconds (proven timing)`
        }
      },
      'brew_time_seconds': {
        name: 'Total Brew Time',
        unit: 's',
        advice: {
          exact: (val) => `Total brew time: ${Math.floor(val/60)}:${(val%60).toString().padStart(2,'0')}`,
          range: (min, max, avg) => `Brew time: ${Math.floor(min/60)}:${(min%60).toString().padStart(2,'0')}-${Math.floor(max/60)}:${(max%60).toString().padStart(2,'0')} (aim for ${Math.floor(avg/60)}:${(avg%60).toString().padStart(2,'0')})`,
          frequent: (val, freq, total) => `Brew for ${Math.floor(val/60)}:${(val%60).toString().padStart(2,'0')} (consistent results)`
        }
      },
      'recipe': {
        name: 'Recipe',
        unit: '',
        advice: {
          exact: (val) => `Follow the "${val}" recipe`,
          frequent: (val, freq, total) => `Try the "${val}" recipe (${freq}/${total} successful brews)`
        }
      },
      'grinder': {
        name: 'Grinder',
        unit: '',
        advice: {
          exact: (val) => `Use your ${val}`,
          frequent: (val, freq, total) => `Your ${val} works great (${freq}/${total} times)`
        }
      },
      'filter': {
        name: 'Filter',
        unit: '',
        advice: {
          exact: (val) => `Use ${val} filters`,
          frequent: (val, freq, total) => `${val} filters are your best bet (${freq}/${total} successes)`
        }
      }
    };

    const desc = descriptions[param];
    if (!desc) return null;

    if (data.type === 'exact') {
      return desc.advice.exact(data.value);
    } else if (data.type === 'range') {
      return desc.advice.range(data.min, data.max, data.avg);
    } else if (data.type === 'frequent') {
      return desc.advice.frequent(data.value, data.frequency, data.total);
    }
    return null;
  };

  if (!productId) return null;
  if (loading) {
    return (
      <div style={{
        backgroundColor: '#e3f2fd',
        border: '1px solid #90caf9',
        borderRadius: '4px',
        padding: '12px',
        marginBottom: '16px'
      }}>
        <div style={{ fontSize: '14px', color: '#1976d2' }}>
          🤖 Loading brew recommendations...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        backgroundColor: '#ffebee',
        border: '1px solid #f8bbd9',
        borderRadius: '4px',
        padding: '12px',
        marginBottom: '16px'
      }}>
        <div style={{ fontSize: '14px', color: '#d32f2f' }}>
          ⚠️ Error loading recommendations: {error}
        </div>
      </div>
    );
  }

  if (!recommendations || !recommendations.has_recommendations) {
    return (
      <div style={{
        backgroundColor: '#f3e5f5',
        border: '1px solid #ce93d8',
        borderRadius: '4px',
        padding: '12px',
        marginBottom: '16px'
      }}>
        <div style={{ fontSize: '14px', color: '#7b1fa2', fontWeight: 'bold', marginBottom: '4px' }}>
          🤖 Brew Assistant
        </div>
        <div style={{ fontSize: '13px', color: '#7b1fa2' }}>
          {recommendations?.message || 'Not enough information for brew recommendations yet.'}
        </div>
      </div>
    );
  }

  return (
    <div style={{
      backgroundColor: '#e8f5e8',
      border: '1px solid #81c784',
      borderRadius: '4px',
      padding: '12px',
      marginBottom: '16px'
    }}>
      <div style={{ fontSize: '14px', color: '#2e7d32', fontWeight: 'bold', marginBottom: '8px' }}>
        🤖 Brew Assistant - Recommendations
      </div>
      
      {Object.entries(recommendations.recommendations).map(([method, rec]) => (
        <div key={method} style={{ marginBottom: '16px' }}>
          <div style={{
            fontSize: '13px',
            fontWeight: 'bold',
            color: '#1a5e20',
            marginBottom: '8px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start'
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {rec.type === 'template' ? '🎯' : '📊'} {method}
            </span>
            <button
              type="button"
              onClick={() => handleApplyRecommendation(method, rec.parameters)}
              style={{
                fontSize: '11px',
                padding: '4px 8px',
                backgroundColor: '#4caf50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
              title="Apply these settings to form"
            >
              Use These Settings
            </button>
          </div>
          
          {/* Conversational introduction */}
          <div style={{ 
            fontSize: '12px', 
            color: '#2e7d32', 
            lineHeight: '1.4', 
            marginBottom: '8px',
            fontStyle: 'italic',
            backgroundColor: '#f1f8e9',
            padding: '6px 8px',
            borderRadius: '3px',
            borderLeft: '3px solid #66bb6a'
          }}>
            {getConversationalText(method, rec)}
          </div>
          
          {/* Parameter recommendations */}
          <div style={{ fontSize: '12px', color: '#2e7d32', lineHeight: '1.4' }}>
            {Object.entries(rec.parameters).map(([param, data]) => {
              const description = getParameterDescription(param, data);
              if (!description) return null;
              
              return (
                <div key={param} style={{ 
                  marginBottom: '4px',
                  padding: '2px 0',
                  display: 'flex',
                  alignItems: 'flex-start'
                }}>
                  <span style={{ 
                    color: '#558b2f', 
                    marginRight: '6px',
                    fontSize: '11px',
                    marginTop: '1px'
                  }}>
                    •
                  </span>
                  <span>{description}</span>
                </div>
              );
            })}
          </div>
        </div>
      ))}
      
      <div style={{ fontSize: '11px', color: '#558b2f', fontStyle: 'italic', marginTop: '8px' }}>
        💡 Recommendations based on previous sessions with score &gt; 3.5. 
        Click "Apply" to use these settings in your form.
      </div>
    </div>
  );
}

export default BrewRecommendations;