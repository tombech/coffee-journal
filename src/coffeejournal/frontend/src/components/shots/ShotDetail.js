import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useToast } from '../Toast';
import { apiFetch } from '../../config';
import { ICONS } from '../../config/icons';
import StarRating from '../StarRating';
import DeleteConfirmationModal from '../DeleteConfirmationModal';

function ShotDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [shot, setShot] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    fetchShot();
  }, [id]);

  const fetchShot = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch(`/shots/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const shotData = await response.json();
      setShot(shotData);
    } catch (err) {
      setError("Failed to fetch shot details: " + err.message);
      console.error("Error fetching shot:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      const response = await apiFetch(`/shots/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      addToast("Shot deleted successfully!", 'success');
      navigate('/shots');
    } catch (err) {
      setError("Failed to delete shot: " + err.message);
      console.error("Error deleting shot:", err);
    }
  };

  const handleDuplicate = async () => {
    try {
      const response = await apiFetch(`/shots/${id}/duplicate`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      addToast("Shot duplicated successfully!", 'success');
      navigate(`/shots/${result.new_shot.id}`);
    } catch (err) {
      setError("Failed to duplicate shot: " + err.message);
      console.error("Error duplicating shot:", err);
    }
  };

  const formatExtractionStatus = (status) => {
    if (!status) return '';
    return status.split('-').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const getExtractionStatusColor = (status) => {
    switch(status) {
      case 'perfect': return '#28a745';
      case 'channeling': return '#dc3545';
      case 'over-extracted': return '#fd7e14';
      case 'under-extracted': return '#ffc107';
      default: return '#6c757d';
    }
  };

  const formatDateTime = (timestamp) => {
    const date = new Date(timestamp);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
    };
  };

  if (loading) return <p className="loading-message">Loading shot details...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!shot) return <p className="error-message">Shot not found</p>;

  const { date, time } = formatDateTime(shot.timestamp);

  return (
    <div id="shot-detail-page">
      {/* Header */}
      <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <h2 style={{ margin: 0, marginRight: 'auto' }} id="shot-title">
          Shot #{shot.id}
        </h2>
        <span style={{ color: '#6c757d', fontSize: '14px', marginRight: 'auto', marginLeft: '10px' }}>
          {date} at {time}
        </span>
        <Link 
          to={`/shots/${id}/edit`}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            marginRight: '5px',
            textDecoration: 'none'
          }}
          title="Edit Shot"
          aria-label="✏️ Edit"
        >
          {ICONS.EDIT}
        </Link>
        <button 
          onClick={handleDuplicate}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            marginRight: '5px'
          }}
          title="Duplicate Shot"
          aria-label="Duplicate Shot"
        >
          {ICONS.DUPLICATE}
        </button>
        <button 
          onClick={() => setShowDeleteModal(true)}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px'
          }}
          title="Delete Shot"
          aria-label="Delete Shot"
        >
          {ICONS.DELETE}
        </button>
      </div>

      {/* Top Section: Shot Overview */}
      <div style={{ marginBottom: '30px', display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        <div>
          {/* Product and Batch Info */}
          <div style={{ 
            padding: '20px', 
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid #e0e0e0',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: '20px' 
          }}>
            <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>☕ Coffee & Batch</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <div>
                <strong>{ICONS.COFFEE} Product:</strong><br/>
                <Link 
                  to={`/products/${shot.product_id}`}
                  style={{ color: '#28a745', textDecoration: 'none', fontWeight: 'bold' }}
                >
                  {shot.product_name}
                </Link>
                {shot.roaster_name && (
                  <>
                    <br/>
                    <small style={{ color: '#6c757d' }}>by {shot.roaster_name}</small>
                  </>
                )}
                {shot.product_details?.decaf && (
                  <span style={{
                    marginLeft: '10px',
                    fontSize: '10px',
                    background: '#ff6b35',
                    color: 'white',
                    padding: '2px 6px',
                    borderRadius: '3px',
                    fontWeight: 'bold'
                  }}>
                    DECAF
                  </span>
                )}
              </div>
              <div>
                <strong>📦 Batch:</strong><br/>
                <Link 
                  to={`/batches/${shot.product_batch_id}`}
                  style={{ color: '#007bff', textDecoration: 'none' }}
                >
                  Batch #{shot.product_batch_id}
                </Link>
                {shot.batch_details?.roast_date && (
                  <>
                    <br/>
                    <small style={{ color: '#6c757d' }}>
                      Roasted: {new Date(shot.batch_details.roast_date).toLocaleDateString()}
                    </small>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Shot Parameters */}
          <div style={{ 
            padding: '20px', 
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid #e0e0e0',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: '20px' 
          }}>
            <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>📊 Shot Parameters</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
              <div style={{ textAlign: 'center', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#007bff' }}>
                  {shot.dose_grams}g
                </div>
                <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '5px' }}>
                  ⚖️ Dose
                </div>
              </div>
              <div style={{ textAlign: 'center', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#28a745' }}>
                  {shot.yield_grams}g
                </div>
                <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '5px' }}>
                  ☕ Yield
                </div>
              </div>
              <div style={{ textAlign: 'center', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '6px' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#6f42c1' }}>
                  {shot.ratio}
                </div>
                <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '5px' }}>
                  📊 Ratio
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px', marginTop: '20px' }}>
              {shot.brew_time_seconds && (
                <div>
                  <strong>⏱️ Brew Time:</strong><br/>
                  {shot.brew_time_seconds}s
                </div>
              )}
              {shot.temperature_c && (
                <div>
                  <strong>🌡️ Temperature:</strong><br/>
                  {shot.temperature_c}°C
                </div>
              )}
              {shot.pressure_bars && (
                <div>
                  <strong>📊 Pressure:</strong><br/>
                  {shot.pressure_bars} bars
                </div>
              )}
              {shot.preinfusion_seconds && (
                <div>
                  <strong>💧 Preinfusion:</strong><br/>
                  {shot.preinfusion_seconds}s
                </div>
              )}
              {shot.grinder_setting && (
                <div>
                  <strong>🎛️ Grind Setting:</strong><br/>
                  {shot.grinder_setting}
                </div>
              )}
            </div>
          </div>

          {/* Equipment */}
          <div style={{ 
            padding: '20px', 
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid #e0e0e0',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: '20px' 
          }}>
            <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>⚙️ Equipment</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              {shot.brewer && (
                <div>
                  <strong>☕ Brewer:</strong><br/>
                  {shot.brewer.name}
                  {shot.brewer.type && (
                    <small style={{ color: '#6c757d', marginLeft: '5px' }}>
                      ({shot.brewer.type})
                    </small>
                  )}
                </div>
              )}
              {shot.grinder && (
                <div>
                  <strong>⚙️ Grinder:</strong><br/>
                  {shot.grinder.name}
                </div>
              )}
              {shot.portafilter && (
                <div>
                  <strong>🔧 Portafilter:</strong><br/>
                  {shot.portafilter.name}
                </div>
              )}
              {shot.basket && (
                <div>
                  <strong>🗂️ Basket:</strong><br/>
                  {shot.basket.name}
                </div>
              )}
              {shot.tamper && (
                <div>
                  <strong>🔨 Tamper:</strong><br/>
                  {shot.tamper.name}
                  {shot.tamper.size && (
                    <small style={{ color: '#6c757d', marginLeft: '5px' }}>
                      ({shot.tamper.size})
                    </small>
                  )}
                </div>
              )}
              {shot.scale && (
                <div>
                  <strong>⚖️ Scale:</strong><br/>
                  {shot.scale.name}
                </div>
              )}
              {shot.recipe && (
                <div>
                  <strong>📖 Recipe:</strong><br/>
                  {shot.recipe.name}
                </div>
              )}
            </div>
          </div>

          {/* Tasting Notes */}
          <div style={{ 
            padding: '20px', 
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid #e0e0e0',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: '20px' 
          }}>
            <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>👃 Tasting Notes</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px' }}>
              {[
                { field: 'sweetness', label: 'Sweetness', icon: '🍯' },
                { field: 'acidity', label: 'Acidity', icon: '🍋' },
                { field: 'body', label: 'Body', icon: '🥛' },
                { field: 'aroma', label: 'Aroma', icon: '👃' },
                { field: 'bitterness', label: 'Bitterness', icon: '🥀' },
                { field: 'crema', label: 'Crema', icon: '☁️' }
              ].map(({ field, label, icon }) => 
                shot[field] ? (
                  <div key={field} style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '5px' }}>
                      {icon} {label}
                    </div>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#007bff' }}>
                      {shot[field]}/10
                    </div>
                  </div>
                ) : null
              )}
            </div>
            {shot.flavor_profile_match && (
              <div style={{ marginTop: '20px', textAlign: 'center' }}>
                <div style={{ fontSize: '14px', color: '#6c757d', marginBottom: '5px' }}>
                  🎯 Flavor Profile Match
                </div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#007bff' }}>
                  {shot.flavor_profile_match}/10
                </div>
              </div>
            )}
          </div>

          {/* Notes */}
          {shot.notes && (
            <div style={{ 
              padding: '20px', 
              backgroundColor: 'white',
              borderRadius: '12px',
              border: '1px solid #e0e0e0',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              marginBottom: '20px' 
            }}>
              <h3 style={{ margin: '0 0 15px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>📝 Notes</h3>
              <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: '1.5' }}>{shot.notes}</p>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div>
          {/* Overall Score */}
          <div style={{ 
            padding: '20px', 
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid #e0e0e0',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            marginBottom: '20px',
            textAlign: 'center'
          }}>
            <h3 style={{ margin: '0 0 15px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>⭐ Overall Score</h3>
            {shot.score ? (
              <div>
                <div style={{ 
                  fontSize: '48px', 
                  fontWeight: 'bold', 
                  color: shot.score >= 7 ? '#28a745' : shot.score >= 5 ? '#ffc107' : '#dc3545',
                  marginBottom: '10px'
                }}>
                  {shot.score}
                </div>
                <StarRating rating={shot.score} maxRating={10} size="medium" />
              </div>
            ) : (
              <div style={{ color: '#6c757d', fontStyle: 'italic' }}>
                No score provided
              </div>
            )}
          </div>

          {/* Extraction Status */}
          {shot.extraction_status && (
            <div style={{ 
              padding: '20px', 
              backgroundColor: 'white',
              borderRadius: '12px',
              border: '1px solid #e0e0e0',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              marginBottom: '20px',
              textAlign: 'center'
            }}>
              <h3 style={{ margin: '0 0 15px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>🎯 Extraction Status</h3>
              <div style={{
                fontSize: '18px',
                fontWeight: 'bold',
                color: getExtractionStatusColor(shot.extraction_status),
                padding: '10px',
                backgroundColor: getExtractionStatusColor(shot.extraction_status) + '20',
                borderRadius: '6px',
                border: `2px solid ${getExtractionStatusColor(shot.extraction_status)}`
              }}>
                🎯 {formatExtractionStatus(shot.extraction_status)}
              </div>
            </div>
          )}

          {/* Shot Session Link */}
          {shot.shot_session_id && (
            <div style={{ 
              padding: '20px', 
              backgroundColor: 'white',
              borderRadius: '12px',
              border: '1px solid #e0e0e0',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              marginBottom: '20px'
            }}>
              <h4 style={{ margin: '0 0 15px 0', color: '#333', fontSize: '16px', fontWeight: 'bold' }}>📋 Part of Session</h4>
              <Link 
                to={`/shot_sessions/${shot.shot_session_id}`}
                style={{ 
                  color: '#007bff', 
                  textDecoration: 'none', 
                  fontWeight: 'bold' 
                }}
              >
                📋 View Shot Session #{shot.shot_session_id}
              </Link>
            </div>
          )}

          {/* Quick Actions */}
          <div style={{ 
            padding: '20px', 
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid #e0e0e0',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h4 style={{ margin: '0 0 15px 0', color: '#333', fontSize: '16px', fontWeight: 'bold' }}>🔗 Quick Actions</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <Link 
                to="/shots" 
                style={{ 
                  color: '#007bff', 
                  textDecoration: 'none', 
                  padding: '8px', 
                  backgroundColor: '#e3f2fd', 
                  borderRadius: '4px',
                  textAlign: 'center'
                }}
              >
                📋 All Shots
              </Link>
              {shot.product_id && (
                <Link 
                  to={`/products/${shot.product_id}`}
                  style={{ 
                    color: '#28a745', 
                    textDecoration: 'none', 
                    padding: '8px', 
                    backgroundColor: '#e8f5e8', 
                    borderRadius: '4px',
                    textAlign: 'center'
                  }}
                >
                  ☕ View Product
                </Link>
              )}
              {shot.product_batch_id && (
                <Link 
                  to={`/batches/${shot.product_batch_id}`}
                  style={{ 
                    color: '#6f42c1', 
                    textDecoration: 'none', 
                    padding: '8px', 
                    backgroundColor: '#f3e5f5', 
                    borderRadius: '4px',
                    textAlign: 'center'
                  }}
                >
                  📦 View Batch
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDelete}
        itemName={`Shot #${shot.id}`}
        itemType="shot"
      />
    </div>
  );
}

export default ShotDetail;