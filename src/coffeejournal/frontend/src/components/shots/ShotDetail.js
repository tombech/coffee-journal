import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useToast } from '../Toast';
import { apiFetch } from '../../config';
import { ICONS } from '../../config/icons';
import StarRating from '../StarRating';
import DeleteConfirmationModal from '../DeleteConfirmationModal';

// Mini Radar Chart Component for Tasting Notes
const ShotTasteRadarChart = ({ data }) => {
  if (!data) return null;
  
  const viewBoxSize = 200;
  const padding = 30; // Space for labels
  const center = viewBoxSize / 2;
  const maxRadius = center - padding;
  const angles = [0, 72, 144, 216, 288]; // 5 points, 72 degrees apart
  const labels = ['Sweet', 'Acid', 'Body', 'Aroma', 'Bitter'];
  const values = [
    data.sweetness || 0,
    data.acidity || 0,
    data.body || 0,
    data.aroma || 0,
    data.bitterness || 0
  ];
  
  // Convert polar coordinates to cartesian
  const getPoint = (angle, radius) => {
    const radians = (angle - 90) * Math.PI / 180; // -90 to start at top
    return {
      x: center + radius * Math.cos(radians),
      y: center + radius * Math.sin(radians)
    };
  };
  
  // Generate grid circles
  const gridCircles = [2, 4, 6, 8, 10].map(level => (
    <circle
      key={level}
      cx={center}
      cy={center}
      r={(level / 10) * maxRadius}
      fill="none"
      stroke="#e0e0e0"
      strokeWidth="1"
    />
  ));
  
  // Generate axis lines
  const axisLines = angles.map((angle, index) => {
    const point = getPoint(angle, maxRadius);
    return (
      <line
        key={index}
        x1={center}
        y1={center}
        x2={point.x}
        y2={point.y}
        stroke="#e0e0e0"
        strokeWidth="1"
      />
    );
  });
  
  // Generate data polygon
  const dataPoints = values.map((value, index) => {
    const radius = (value / 10) * maxRadius;
    return getPoint(angles[index], radius);
  });
  
  const polygonPoints = dataPoints.map(point => `${point.x},${point.y}`).join(' ');
  
  // Generate labels
  const labelElements = labels.map((label, index) => {
    const point = getPoint(angles[index], maxRadius + 20);
    return (
      <text
        key={index}
        x={point.x}
        y={point.y}
        textAnchor="middle"
        dominantBaseline="middle"
        fontSize="14"
        fill="#666"
        fontWeight="600"
      >
        {label}
      </text>
    );
  });
  
  return (
    <svg 
      width="100%" 
      height="100%" 
      viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
      style={{ 
        display: 'block',
        minHeight: '140px',
        maxHeight: '180px',
        verticalAlign: 'top'
      }}
    >
      {gridCircles}
      {axisLines}
      <polygon
        points={polygonPoints}
        fill="rgba(54, 162, 235, 0.2)"
        stroke="rgba(54, 162, 235, 0.8)"
        strokeWidth="2"
      />
      {dataPoints.map((point, index) => (
        <circle
          key={index}
          cx={point.x}
          cy={point.y}
          r="3"
          fill="rgba(54, 162, 235, 0.8)"
        />
      ))}
      {labelElements}
    </svg>
  );
};

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
      <div style={{ 
        marginBottom: '15px', 
        padding: '12px 15px',
        backgroundColor: 'white',
        borderRadius: '8px',
        border: '1px solid #e0e0e0',
        display: 'flex', 
        alignItems: 'center', 
        gap: '10px' 
      }}>
        <h2 style={{ margin: 0 }} id="shot-title">
          Shot #{shot.id}
        </h2>
        <span style={{ color: '#6c757d', fontSize: '14px', marginLeft: '10px' }}>
          {date} at {time}
        </span>

        {/* Coffee and Batch Info - Compact */}
        <div style={{ marginLeft: '20px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px' }}>
          <span>☕</span>
          {shot.product_id ? (
            <Link 
              to={`/products/${shot.product_id}`} 
              style={{ color: '#28a745', textDecoration: 'none', fontWeight: 'bold' }}
            >
              {shot.product_name}
            </Link>
          ) : (
            <span style={{ fontWeight: 'bold' }}>{shot.product_name}</span>
          )}
          {shot.product_batch_id && (
            <span style={{ color: '#6c757d' }}>
              (
              <Link 
                to={`/batches/${shot.product_batch_id}`}
                style={{ color: '#6c757d', textDecoration: 'none' }}
              >
                #{shot.product_batch_id}
              </Link>
              )
            </span>
          )}
        </div>
        
        {/* Keep just coffee info in header, move score/status to assessment column */}
        <div style={{ marginLeft: 'auto' }}>
        </div>
        
        {/* Quick Link Icons */}
        <div style={{ display: 'flex', gap: '5px' }}>
          <Link 
            to="/shots"
            style={{ 
              padding: '6px 8px', 
              border: 'none', 
              background: 'none', 
              cursor: 'pointer', 
              fontSize: '16px',
              textDecoration: 'none'
            }}
            title="All Shots"
            aria-label="All Shots"
          >
            📋
          </Link>
          {shot.shot_session_id && (
            <Link 
              to={`/shot_sessions/${shot.shot_session_id}`}
              style={{ 
                padding: '6px 8px', 
                border: 'none', 
                background: 'none', 
                cursor: 'pointer', 
                fontSize: '16px',
                textDecoration: 'none'
              }}
              title={`View Shot Session #${shot.shot_session_id}`}
              aria-label={`View Shot Session #${shot.shot_session_id}`}
            >
              📊
            </Link>
          )}
        </div>
        
        {/* Action buttons */}
        <div style={{ display: 'flex', gap: '5px' }}>
          <Link 
            to={`/shots/${id}/edit`}
            style={{ 
              padding: '6px 8px', 
              border: 'none', 
              background: 'none', 
              cursor: 'pointer', 
              fontSize: '16px',
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
              fontSize: '16px'
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
      </div>

      {/* Three Column Layout: Shot Parameters + Assessment + Equipment/Tasting Notes */}
      <div style={{ display: 'flex', gap: '20px', marginBottom: '15px' }}>
        
        {/* Left Column: Shot Parameters */}
        <div style={{ 
          flex: '2',
          padding: '20px', 
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #e0e0e0'
        }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>📊 Shot Parameters</h3>
          
          {/* Primary Parameters - Wrapper for centering secondary parameters */}
          <div>
            {/* Primary Parameters - All equally important - Bigger */}
            <div style={{ display: 'flex', gap: '30px', alignItems: 'center', marginBottom: '20px', justifyContent: 'flex-start' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#007bff' }}>
                  {shot.dose_grams}g
                </div>
                <div style={{ fontSize: '14px', color: '#6c757d', fontWeight: '500' }}>Dose</div>
              </div>
              <div style={{ fontSize: '32px', color: '#ccc' }}>→</div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#28a745' }}>
                  {shot.yield_grams}g
                </div>
                <div style={{ fontSize: '14px', color: '#6c757d', fontWeight: '500' }}>Yield</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#6f42c1' }}>
                  {shot.ratio}
                </div>
                <div style={{ fontSize: '14px', color: '#6c757d', fontWeight: '500' }}>Ratio</div>
              </div>
              {shot.extraction_time_seconds && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#17a2b8' }}>
                    {shot.extraction_time_seconds}s
                  </div>
                  <div style={{ fontSize: '14px', color: '#6c757d', fontWeight: '500' }}>Time</div>
                </div>
              )}
              {shot.grinder_setting && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#fd7e14' }}>
                    {shot.grinder_setting}
                  </div>
                  <div style={{ fontSize: '14px', color: '#6c757d', fontWeight: '500' }}>Grind</div>
                </div>
              )}
            </div>
            
            {/* Secondary Parameters - Centered relative to primary parameters */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', justifyContent: 'flex-start', fontSize: '16px', color: '#6c757d', marginTop: '10px', marginLeft: '30px' }}>
              {shot.water_temperature_c && (
                <div>
                  <strong>🌡️</strong> {shot.water_temperature_c}°C
                </div>
              )}
              {shot.pressure_bars && (
                <div>
                  <strong>📊</strong> {shot.pressure_bars} bar
                </div>
              )}
              {shot.preinfusion_seconds && (
                <div>
                  <strong>💧</strong> {shot.preinfusion_seconds}s preinfusion
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Middle Column: Shot Assessment */}
        <div style={{ 
          flex: '1',
          padding: '20px', 
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #e0e0e0'
        }}>
          <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>🎯 Shot Assessment</h3>
          
          {/* Overall Score - Large and prominent */}
          {shot.overall_score ? (
            <div style={{ textAlign: 'center', marginBottom: '25px' }}>
              <div style={{ fontSize: '48px', fontWeight: 'bold', margin: '0 0 8px 0', color: shot.overall_score >= 7 ? '#28a745' : shot.overall_score >= 5 ? '#ffc107' : '#dc3545' }}>
                {shot.overall_score}
              </div>
              <div style={{ fontSize: '14px', color: '#6c757d', fontWeight: '500' }}>Overall Score</div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', marginBottom: '25px' }}>
              <div style={{ fontSize: '24px', color: '#6c757d', fontStyle: 'italic' }}>No Score</div>
            </div>
          )}
          
          {/* Extraction Status */}
          {shot.extraction_status && (
            <div style={{ textAlign: 'center', marginBottom: '20px' }}>
              <div style={{
                display: 'inline-block',
                fontSize: '16px',
                fontWeight: 'bold',
                color: getExtractionStatusColor(shot.extraction_status),
                padding: '8px 16px',
                backgroundColor: getExtractionStatusColor(shot.extraction_status) + '20',
                borderRadius: '8px',
                border: `2px solid ${getExtractionStatusColor(shot.extraction_status)}`
              }}>
                {formatExtractionStatus(shot.extraction_status)}
              </div>
            </div>
          )}
          
        </div>

        {/* Right Column: Equipment + Tasting Notes */}
        <div style={{ flex: '1', display: 'flex', flexDirection: 'column', gap: '15px' }}>
          
          {/* Equipment - Compact with Labels */}
          <div style={{ 
            padding: '12px', 
            backgroundColor: 'white',
            borderRadius: '8px',
            border: '1px solid #e0e0e0'
          }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#333', fontSize: '16px', fontWeight: 'bold' }}>⚙️ Equipment</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
              {shot.brewer && (
                <div>
                  <strong>Brewer:</strong> {shot.brewer.name}
                  {shot.brewer.type && <span style={{ color: '#6c757d' }}> ({shot.brewer.type})</span>}
                </div>
              )}
              {shot.grinder && (
                <div>
                  <strong>Grinder:</strong> {shot.grinder.name}
                </div>
              )}
              {shot.portafilter && (
                <div>
                  <strong>Portafilter:</strong> {shot.portafilter.name}
                </div>
              )}
              {shot.basket && (
                <div>
                  <strong>Basket:</strong> {shot.basket.name}
                </div>
              )}
              {shot.tamper && (
                <div>
                  <strong>Tamper:</strong> {shot.tamper.name}
                  {shot.tamper.size && <span style={{ color: '#6c757d' }}> ({shot.tamper.size})</span>}
                </div>
              )}
              {shot.scale && (
                <div>
                  <strong>Scale:</strong> {shot.scale.name}
                </div>
              )}
              {shot.recipe && (
                <div>
                  <strong>Recipe:</strong> {shot.recipe.name}
                </div>
              )}
            </div>
          </div>

          {/* Tasting Notes with Spider Web Chart */}
          <div style={{ 
            padding: '12px', 
            backgroundColor: 'white',
            borderRadius: '8px',
            border: '1px solid #e0e0e0'
          }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#333', fontSize: '16px', fontWeight: 'bold' }}>👃 Tasting Notes</h3>
            
            {/* Check if we have tasting data */}
            {(shot.sweetness || shot.acidity || shot.body || shot.aroma || shot.bitterness) ? (
              <div style={{ display: 'flex', gap: '15px', alignItems: 'stretch' }}>
                
                {/* Left side: Numerical scores */}
                <div style={{ flex: '1', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '13px' }}>
                  {[
                    { field: 'sweetness', label: 'Sweetness', icon: '🍯' },
                    { field: 'acidity', label: 'Acidity', icon: '🍋' },
                    { field: 'body', label: 'Body', icon: '🥛' },
                    { field: 'aroma', label: 'Aroma', icon: '👃' },
                    { field: 'bitterness', label: 'Bitterness', icon: '🥀' },
                    { field: 'crema', label: 'Crema', icon: '☁️' }
                  ].map(({ field, label, icon }) => 
                    shot[field] ? (
                      <div key={field} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span>{icon}</span>
                        <span>{label}:</span>
                        <span style={{ fontWeight: 'bold', color: '#007bff' }}>
                          {shot[field]}/10
                        </span>
                      </div>
                    ) : null
                  )}
                  {shot.flavor_profile_match && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span>🎯</span>
                      <span>Profile Match:</span>
                      <span style={{ fontWeight: 'bold', color: '#007bff' }}>
                        {shot.flavor_profile_match}/10
                      </span>
                    </div>
                  )}
                </div>
                
                {/* Right side: Spider web chart */}
                <div style={{ flex: '1', display: 'flex', justifyContent: 'center', alignItems: 'flex-start' }}>
                  <ShotTasteRadarChart data={{
                    sweetness: shot.sweetness || 0,
                    acidity: shot.acidity || 0,
                    body: shot.body || 0,
                    aroma: shot.aroma || 0,
                    bitterness: shot.bitterness || 0
                  }} size={120} />
                </div>
                
              </div>
            ) : (
              <div style={{ fontSize: '13px', color: '#6c757d', fontStyle: 'italic' }}>
                No tasting notes recorded
              </div>
            )}
          </div>
          
        </div>
      </div>

      {/* Notes - Full Width Below */}
      {shot.notes && (
        <div style={{ 
          padding: '12px', 
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #e0e0e0',
          marginBottom: '15px' 
        }}>
          <h3 style={{ margin: '0 0 8px 0', color: '#333', fontSize: '16px', fontWeight: 'bold' }}>📝 Notes</h3>
          <p style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: '1.4', fontSize: '14px' }}>{shot.notes}</p>
        </div>
      )}

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