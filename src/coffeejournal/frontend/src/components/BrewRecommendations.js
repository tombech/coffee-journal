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
        <div key={method} style={{ marginBottom: '12px' }}>
          <div style={{
            fontSize: '13px',
            fontWeight: 'bold',
            color: '#1a5e20',
            marginBottom: '6px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span>
              {method} {rec.type === 'template' ? '🎯' : '📊'}
              {rec.type === 'template' && ` (Score: ${rec.source_score})`}
              {rec.type === 'range' && ` (${rec.sessions_used} sessions, avg: ${rec.avg_score})`}
            </span>
            <button
              type="button"
              onClick={() => handleApplyRecommendation(method, rec.parameters)}
              style={{
                fontSize: '11px',
                padding: '2px 6px',
                backgroundColor: '#4caf50',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer'
              }}
              title="Apply these settings to form"
            >
              Apply
            </button>
          </div>
          
          <div style={{ fontSize: '12px', color: '#2e7d32', lineHeight: '1.3' }}>
            {Object.entries(rec.parameters).map(([param, data]) => {
              const displayName = param.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').toLowerCase();
              
              if (data.type === 'exact') {
                return (
                  <div key={param} style={{ marginBottom: '2px' }}>
                    <strong>{displayName}:</strong> {data.value}
                  </div>
                );
              } else if (data.type === 'range') {
                return (
                  <div key={param} style={{ marginBottom: '2px' }}>
                    <strong>{displayName}:</strong> {data.min}-{data.max} (avg: {data.avg})
                  </div>
                );
              } else if (data.type === 'frequent') {
                return (
                  <div key={param} style={{ marginBottom: '2px' }}>
                    <strong>{displayName}:</strong> {data.value} ({data.frequency}/{data.total} times)
                  </div>
                );
              }
              return null;
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