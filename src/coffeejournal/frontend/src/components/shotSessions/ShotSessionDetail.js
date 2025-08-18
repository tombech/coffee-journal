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

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
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
            ) : 'N/A'}
          </div>

          <div style={{ marginBottom: '10px' }}>
            <strong>Batch: </strong>
            {shotSession.product_batch ? (
              <Link to={`/batches/${shotSession.product_batch.id}`} style={{ color: '#007bff', textDecoration: 'none' }}>
                Batch #{shotSession.product_batch.id} ({shotSession.product_batch.roast_date})
              </Link>
            ) : 'N/A'}
          </div>

          <div style={{ marginBottom: '10px' }}>
            <strong>Brewer: </strong>
            {shotSession.brewer ? (
              <span>{shotSession.brewer.name}</span>
            ) : 'N/A'}
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
          <Link
            to={`/shots/new?session_id=${id}`}
            style={{ 
              padding: '6px 8px', 
              border: 'none', 
              background: 'none', 
              cursor: 'pointer', 
              fontSize: '16px',
              textDecoration: 'none'
            }}
            title="Add Shot to Session"
            aria-label="Add Shot to Session"
          >
            {ICONS.CREATE}
          </Link>
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
            <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '800px' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa' }}>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Shot
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Dose → Yield
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Ratio
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Flow Rate
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Extraction Time
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Status
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Score
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6' }}>
                    Time Gap
                  </th>
                </tr>
              </thead>
              <tbody>
                {shots.map((shot) => (
                  <tr key={shot.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                    <td style={{ padding: '12px' }}>
                      <Link
                        to={`/shots/${shot.id}`}
                        style={{ 
                          color: '#007bff', 
                          textDecoration: 'none',
                          fontWeight: 'bold'
                        }}
                      >
                        #{shot.session_shot_number || shot.id}
                      </Link>
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'monospace' }}>
                      {shot.dose_grams}g → {shot.yield_grams}g
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'monospace', fontWeight: 'bold' }}>
                      1:{shot.dose_yield_ratio || 'N/A'}
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'monospace', fontWeight: 'bold' }}>
                      {shot.flow_rate ? `${shot.flow_rate}g/s` : 'N/A'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      {shot.extraction_time_seconds ? `${shot.extraction_time_seconds}s` : 'N/A'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      {shot.extraction_status && (
                        <span style={{
                          padding: '4px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: 'bold',
                          color: 'white',
                          backgroundColor: getExtractionStatusColor(shot.extraction_status),
                          textTransform: 'capitalize'
                        }}>
                          {shot.extraction_status.replace('-', ' ')}
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '12px' }}>
                      {shot.overall_score ? (
                        <span style={{ fontWeight: 'bold' }}>{shot.overall_score}/10</span>
                      ) : 'Not rated'}
                    </td>
                    <td style={{ padding: '12px', fontSize: '12px', color: '#666' }}>
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