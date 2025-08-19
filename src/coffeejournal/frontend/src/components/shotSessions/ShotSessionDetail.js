import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useToast } from '../Toast';
import { apiFetch } from '../../config';
import { ICONS } from '../../config/icons';
import DeleteConfirmationModal from '../DeleteConfirmationModal';

function ShotSessionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [shotSession, setShotSession] = useState(null);
  const [shots, setShots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  useEffect(() => {
    if (id) {
      fetchShotSession();
      fetchShotSessionShots();
    }
  }, [id]);

  const fetchShotSession = async () => {
    try {
      console.log('ShotSessionDetail: Fetching shot session with ID:', id);
      const response = await apiFetch(`/shot_sessions/${id}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log('ShotSessionDetail: Received shot session data:', data);
      console.log('ShotSessionDetail: Product object:', data.product);
      console.log('ShotSessionDetail: Product batch object:', data.product_batch);
      console.log('ShotSessionDetail: Brewer object:', data.brewer);
      setShotSession(data);
    } catch (err) {
      setError("Failed to fetch shot session: " + err.message);
      console.error("Error fetching shot session:", err);
    }
  };

  const fetchShotSessionShots = async () => {
    try {
      const response = await apiFetch(`/shot_sessions/${id}/shots`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setShots(data);
    } catch (err) {
      console.error("Error fetching shots:", err);
      setShots([]); // Don't fail the whole page if shots can't be fetched
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteShotSession = async () => {
    try {
      const response = await apiFetch(`/shot_sessions/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      addToast("Shot session deleted successfully!", 'success');
      navigate('/shot-sessions');
    } catch (err) {
      setError("Failed to delete shot session: " + err.message);
      console.error("Error deleting shot session:", err);
    }
  };

  const handleDuplicateSession = async () => {
    try {
      const response = await apiFetch(`/shot_sessions/${id}/duplicate`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      addToast("Shot session duplicated successfully!", 'success');
      navigate(`/shot-sessions/${result.new_shot_session.id}`);
    } catch (err) {
      setError("Failed to duplicate shot session: " + err.message);
      console.error("Error duplicating shot session:", err);
    }
  };

  const handleAddShot = async () => {
    try {
      if (shots.length > 0) {
        // Session has shots - duplicate the newest shot
        const response = await apiFetch(`/shot_sessions/${id}/duplicate_newest_shot`, {
          method: 'POST',
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        addToast("Last shot duplicated for editing!", 'success');
        // Navigate to edit the newly created shot
        navigate(`/shots/${result.new_shot.id}/edit`);
      } else {
        // No shots in session yet - go to regular shot creation form
        navigate(`/shots/new?session_id=${id}`);
      }
    } catch (err) {
      setError("Failed to add shot: " + err.message);
      console.error("Error adding shot:", err);
    }
  };

  const handleDeleteShot = async (shotId) => {
    if (!window.confirm("Are you sure you want to delete this shot?")) {
      return;
    }
    try {
      const response = await apiFetch(`/shots/${shotId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      addToast("Shot deleted successfully!", 'success');
      // Refresh the shots data
      fetchShotSessionShots();
    } catch (err) {
      setError("Failed to delete shot: " + err.message);
      console.error("Error deleting shot:", err);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (error) {
      return dateString;
    }
  };

  const getExtractionStatusColor = (status) => {
    const colors = {
      'perfect': '#28a745',
      'under-extracted': '#ffc107',
      'over-extracted': '#fd7e14',
      'channeling': '#dc3545'
    };
    return colors[status] || '#6c757d';
  };

  // Function to detect if a field changed from the previous shot in the session
  const getFieldChangeStatus = (currentShot, fieldName) => {
    // Find current shot index in the shots array
    const currentIndex = shots.findIndex(shot => shot.id === currentShot.id);
    
    // If this is the first shot, no comparison needed
    if (currentIndex <= 0) return null;
    
    const previousShot = shots[currentIndex - 1];
    const currentValue = currentShot[fieldName];
    const previousValue = previousShot[fieldName];
    
    // Direct comparison for most fields
    return currentValue !== previousValue ? 'changed' : null;
  };

  // Function to get style for changed fields
  const getChangedFieldStyle = (baseStyle, changeStatus) => {
    if (changeStatus === 'changed') {
      return {
        ...baseStyle,
        backgroundColor: '#fff3cd',
        border: '2px solid #ffc107',
        fontWeight: 'bold'
      };
    }
    return baseStyle;
  };

  if (loading) return <p className="loading-message">Loading shot session...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!shotSession) return <p className="error-message">Shot session not found</p>;

  return (
    <div id="shot-session-detail-page">
      {/* Header */}
      <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <h2 style={{ margin: 0, marginRight: 'auto' }} id="shot-session-title">
          {shotSession.title || `Shot Session ${shotSession.id}`}
        </h2>
        <span style={{ color: '#6c757d', fontSize: '14px', marginRight: 'auto', marginLeft: '10px' }}>
          Created on {formatDate(shotSession.created_at)}
        </span>
        <Link 
          to={`/shot-sessions/${id}/edit`}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            marginRight: '5px',
            color: 'inherit',
            textDecoration: 'none'
          }}
          title="Edit Shot Session"
          aria-label="Edit Shot Session"
        >
          {ICONS.EDIT}
        </Link>
        <button 
          onClick={handleDuplicateSession}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            marginRight: '5px'
          }}
          title="Duplicate Shot Session"
          aria-label="Duplicate Shot Session"
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
          title="Delete Shot Session"
          aria-label="Delete Shot Session"
        >
          {ICONS.DELETE}
        </button>
      </div>

      {/* Session Information */}
      <div style={{ marginBottom: '30px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
        <div style={{ 
          padding: '20px', 
          backgroundColor: 'white',
          borderRadius: '12px',
          border: '1px solid #e0e0e0',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ margin: '0 0 15px 0', fontSize: '18px', fontWeight: 'bold', color: '#333' }}>📋 Session Details</h3>
          
          <div style={{ marginBottom: '10px' }}>
            <strong>Product: </strong>
            {shotSession.product ? (
              <Link to={`/products/${shotSession.product.id}`} style={{ color: '#007bff', textDecoration: 'none' }}>
                {shotSession.product.product_name}
              </Link>
            ) : '-'}
          </div>

          <div style={{ marginBottom: '10px' }}>
            <strong>Batch: </strong>
            {shotSession.product_batch ? (
              <Link to={`/batches/${shotSession.product_batch.id}`} style={{ color: '#007bff', textDecoration: 'none' }}>
                Batch #{shotSession.product_batch.id} ({shotSession.product_batch.roast_date})
              </Link>
            ) : '-'}
          </div>

          <div style={{ marginBottom: '10px' }}>
            <strong>Brewer: </strong>
            {shotSession.brewer ? (
              <span>{shotSession.brewer.name}</span>
            ) : '-'}
          </div>

          <div style={{ marginBottom: '10px' }}>
            <strong>Total Shots: </strong>
            <span style={{ 
              padding: '4px 8px', 
              backgroundColor: '#e9ecef', 
              borderRadius: '12px', 
              fontSize: '12px',
              fontWeight: 'bold'
            }}>
              {shotSession.shot_count || 0}
            </span>
          </div>
        </div>

        {/* Session Notes */}
        {shotSession.notes && (
          <div style={{ 
            padding: '20px', 
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid #e0e0e0',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ margin: '0 0 15px 0', fontSize: '18px', fontWeight: 'bold', color: '#333' }}>📝 Session Notes</h3>
            <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{shotSession.notes}</p>
          </div>
        )}
      </div>

      {/* Associated Shots */}
      <div style={{ 
        padding: '20px', 
        backgroundColor: 'white',
        borderRadius: '12px',
        border: '1px solid #e0e0e0',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h3 style={{ margin: 0, color: '#333', fontSize: '18px', fontWeight: 'bold' }}>☕ Shots in this Session</h3>
          <button
            onClick={handleAddShot}
            style={{ 
              padding: '6px 8px', 
              border: 'none', 
              background: 'none', 
              cursor: 'pointer', 
              fontSize: '16px'
            }}
            title={shots.length > 0 ? "Duplicate last shot for editing" : "Add shot to session"}
            aria-label={shots.length > 0 ? "Duplicate last shot for editing" : "Add shot to session"}
          >
            {ICONS.CREATE}
          </button>
        </div>

        {shots.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <p style={{ margin: '0 0 15px 0', color: '#666' }}>No shots in this session yet.</p>
            <Link
              to={`/shots/new?session_id=${id}`}
              style={{
                padding: '8px 16px',
                backgroundColor: '#e3f2fd',
                color: '#007bff',
                textDecoration: 'none',
                borderRadius: '4px'
              }}
            >
              ☕ Add First Shot
            </Link>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ borderCollapse: 'collapse', fontSize: '12px', whiteSpace: 'nowrap' }}>
              <thead>
                <tr style={{ backgroundColor: '#e9ecef' }}>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left', width: '90px' }}>
                    Actions
                  </th>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                    Shot #
                  </th>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                    ⚖️ Dose (g)
                  </th>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                    ☕ Yield (g)
                  </th>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                    📊 Ratio
                  </th>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                    💧 Flow Rate (g/s)
                  </th>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                    ⏱️ Extract Time (s)
                  </th>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                    🌡️ Temperature (°C)
                  </th>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                    ⚙️ Grind Setting
                  </th>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                    🎯 Extraction
                  </th>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                    ⭐ Score
                  </th>
                  <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                    🕒 Time Gap
                  </th>
                </tr>
              </thead>
              <tbody>
                {shots.map((shot) => (
                  <tr key={shot.id} style={{ '&:hover': { backgroundColor: '#f8f9fa' } }}>
                    <td style={{ padding: '2px', border: '1px solid #ddd', textAlign: 'center', fontSize: '11px', width: '90px', whiteSpace: 'nowrap' }}>
                      <Link
                        to={`/shots/${shot.id}/edit`}
                        style={{ 
                          padding: '2px 4px', 
                          margin: '0 1px', 
                          textDecoration: 'none',
                          color: 'inherit',
                          fontSize: '12px'
                        }}
                        title="Edit"
                        aria-label="Edit shot"
                      >
                        ✏️
                      </Link>
                      <Link
                        to={`/shots/${shot.id}`}
                        style={{ 
                          padding: '2px 4px', 
                          margin: '0 1px', 
                          textDecoration: 'none',
                          color: 'inherit',
                          fontSize: '12px'
                        }}
                        title="View"
                        aria-label="View shot"
                      >
                        👁️
                      </Link>
                      <button 
                        onClick={() => handleDeleteShot(shot.id)}
                        title="Delete"
                        aria-label="Delete shot"
                        style={{ 
                          padding: '2px 4px', 
                          margin: '0 1px', 
                          border: 'none', 
                          background: 'none', 
                          cursor: 'pointer', 
                          fontSize: '12px' 
                        }}
                      >
                        🗑️
                      </button>
                    </td>
                    <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top' }}>
                      <Link
                        to={`/shots/${shot.id}`}
                        style={{ 
                          textDecoration: 'none', 
                          color: 'inherit'
                        }}
                      >
                        #{shot.session_shot_number || shot.id}
                      </Link>
                    </td>
                    <td 
                      style={getChangedFieldStyle(
                        { padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' },
                        getFieldChangeStatus(shot, 'dose_grams')
                      )}
                      title={getFieldChangeStatus(shot, 'dose_grams') ? 'Dose changed from previous shot in session' : undefined}
                    >
                      {shot.dose_grams ? `${shot.dose_grams}g` : '-'}
                    </td>
                    <td 
                      style={getChangedFieldStyle(
                        { padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' },
                        getFieldChangeStatus(shot, 'yield_grams')
                      )}
                      title={getFieldChangeStatus(shot, 'yield_grams') ? 'Yield changed from previous shot in session' : undefined}
                    >
                      {shot.yield_grams ? `${shot.yield_grams}g` : '-'}
                    </td>
                    <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                      {shot.ratio || (shot.dose_yield_ratio ? `1:${shot.dose_yield_ratio}` : '-')}
                    </td>
                    <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                      {shot.flow_rate ? `${shot.flow_rate}g/s` : 
                       (shot.yield_grams && shot.extraction_time_seconds ? 
                        `${(shot.yield_grams / shot.extraction_time_seconds).toFixed(1)}g/s` : '-')}
                    </td>
                    <td 
                      style={getChangedFieldStyle(
                        { padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' },
                        getFieldChangeStatus(shot, 'extraction_time_seconds')
                      )}
                      title={getFieldChangeStatus(shot, 'extraction_time_seconds') ? 'Extraction time changed from previous shot in session' : undefined}
                    >
                      {shot.extraction_time_seconds ? `${shot.extraction_time_seconds}s` : '-'}
                    </td>
                    <td 
                      style={getChangedFieldStyle(
                        { padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' },
                        getFieldChangeStatus(shot, 'water_temperature_c')
                      )}
                      title={getFieldChangeStatus(shot, 'water_temperature_c') ? 'Temperature changed from previous shot in session' : undefined}
                    >
                      {shot.water_temperature_c ? `${shot.water_temperature_c}°C` : '-'}
                    </td>
                    <td 
                      style={getChangedFieldStyle(
                        { padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' },
                        getFieldChangeStatus(shot, 'grinder_setting')
                      )}
                      title={getFieldChangeStatus(shot, 'grinder_setting') ? 'Grinder setting changed from previous shot in session' : undefined}
                    >
                      {shot.grinder_setting || '-'}
                    </td>
                    <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                      {shot.extraction_status ? (
                        <span style={{
                          padding: '2px 4px',
                          borderRadius: '8px',
                          fontSize: '10px',
                          fontWeight: 'bold',
                          color: 'white',
                          backgroundColor: getExtractionStatusColor(shot.extraction_status),
                          textTransform: 'capitalize'
                        }}>
                          {shot.extraction_status.replace('-', ' ')}
                        </span>
                      ) : '-'}
                    </td>
                    <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap', fontWeight: 'bold' }}>
                      {shot.overall_score ? shot.overall_score.toFixed(1) : '-'}
                    </td>
                    <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap', color: '#666' }}>
                      {shot.time_since_previous || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        onConfirm={handleDeleteShotSession}
        itemName={shotSession.title || `Shot Session ${shotSession.id}`}
        itemType="shot session"
      />
    </div>
  );
}

export default ShotSessionDetail;