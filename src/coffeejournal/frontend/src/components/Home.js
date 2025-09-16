import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import BrewSessionTable from './BrewSessionTable';
import BrewSessionForm from './BrewSessionForm';
import { useToast } from './Toast';

function Home() {
  const { addToast } = useToast();
  const [sessions, setSessions] = useState([]);
  const [homeSummary, setHomeSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [editingSession, setEditingSession] = useState(null);
  const [filterOptions, setFilterOptions] = useState(null);

  const fetchBrewSessions = async () => {
    try {
      setLoading(true);

      // Fetch data needed for Home page
      const [
        sessionsResponse,
        filterOptionsResponse,
        homeSummaryResponse
      ] = await Promise.all([
        apiFetch('/brew_sessions?page_size=15'), // Recent 15 sessions
        apiFetch('/brew_sessions/filter_options'), // Filter options for dropdowns
        apiFetch('/stats/home-summary') // Home page summary statistics
      ]);

      if (!sessionsResponse.ok || !filterOptionsResponse.ok || !homeSummaryResponse.ok) {
        throw new Error('Failed to fetch data from one or more endpoints');
      }

      const [
        sessionsResult,
        filterOptionsData,
        homeSummaryData
      ] = await Promise.all([
        sessionsResponse.json(),
        filterOptionsResponse.json(),
        homeSummaryResponse.json()
      ]);

      // Set the state
      setSessions(sessionsResult.data || []);
      setFilterOptions(filterOptionsData);
      setHomeSummary(homeSummaryData);

    } catch (err) {
      setError('Failed to fetch data: ' + err.message);
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBrewSessions();
  }, []);

  const handleDelete = async (sessionId) => {
    if (!window.confirm('Are you sure you want to delete this brew session?')) {
      return;
    }

    try {
      const response = await apiFetch(`/brew_sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      addToast('Brew session deleted successfully!', 'success');
      fetchBrewSessions(); // Refresh the list
    } catch (err) {
      addToast('Failed to delete brew session: ' + err.message, 'error');
      console.error('Error deleting brew session:', err);
    }
  };

  const handleDuplicate = async (sessionId, batchId) => {
    try {
      // Use the correct endpoint with batch_id
      const response = await apiFetch(`/batches/${batchId}/brew_sessions/${sessionId}/duplicate`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      addToast('Brew session duplicated successfully!', 'success');
      fetchBrewSessions(); // Refresh the list
    } catch (err) {
      addToast('Failed to duplicate brew session: ' + err.message, 'error');
      console.error('Error duplicating brew session:', err);
    }
  };

  const handleEdit = (session) => {
    setEditingSession(session);
    setShowNewForm(true);
  };

  const handleSessionSubmitted = () => {
    setShowNewForm(false);
    setEditingSession(null);
    fetchBrewSessions(); // Refresh the list
  };

  if (loading) return <p>Loading recent brew sessions...</p>;
  if (error) return <p className="error-message">{error}</p>;

  // Helper function to format grams in human-readable units
  const formatGrams = (grams) => {
    if (grams >= 1000) {
      const kg = grams / 1000;
      if (kg >= 10) {
        return `${Math.round(kg)}kg`;
      } else {
        return `${kg.toFixed(1)}kg`;
      }
    } else {
      return `${Math.round(grams)}g`;
    }
  };

  return (
    <div>
      {showNewForm && (
        <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
          <BrewSessionForm
            initialData={editingSession}
            onSessionSubmitted={handleSessionSubmitted}
          />
          <button 
            onClick={() => {
              setShowNewForm(false);
              setEditingSession(null);
            }}
            style={{ marginTop: '10px' }}
          >
            Cancel
          </button>
        </div>
      )}

      {/* Home Summary Statistics */}
      {homeSummary && (
        <div style={{ marginBottom: '40px' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: '20px',
            marginBottom: '30px'
          }}>
            {/* Products Section */}
            <div style={{
              backgroundColor: '#ffffff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              padding: '24px',
              textAlign: 'center',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
              <div style={{ fontSize: '28px', marginBottom: '12px', color: '#666' }}>☕</div>
              <h4 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '16px', fontWeight: '600' }}>Products</h4>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#333', marginBottom: '8px' }}>
                {homeSummary.products_with_active_batches}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>
                Active in inventory
              </div>
              {homeSummary.products_without_active_batches > 0 && (
                <div style={{ fontSize: '12px', color: '#999', marginTop: '5px' }}>
                  +{homeSummary.products_without_active_batches} archived
                </div>
              )}
            </div>

            {/* Sessions Section */}
            <div style={{
              backgroundColor: '#ffffff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              padding: '24px',
              textAlign: 'center',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
              <div style={{ fontSize: '28px', marginBottom: '12px', color: '#666' }}>🚀</div>
              <h4 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '16px', fontWeight: '600' }}>Brewing Events</h4>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#333', marginBottom: '8px' }}>
                {homeSummary.total_brewing_events}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>
                {homeSummary.total_brew_sessions} brews • {homeSummary.total_shots} shots
              </div>
            </div>

            {/* Coffee Used Section */}
            <div style={{
              backgroundColor: '#ffffff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              padding: '24px',
              textAlign: 'center',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
              <div style={{ fontSize: '28px', marginBottom: '12px', color: '#666' }}>⚖️</div>
              <h4 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '16px', fontWeight: '600' }}>Coffee Used</h4>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#333', marginBottom: '8px' }}>
                {formatGrams(homeSummary.total_grams_used)}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>
                {homeSummary.average_coffee_per_session.toFixed(1)}g per session
              </div>
            </div>

            {/* Inventory Remaining Section */}
            <div style={{
              backgroundColor: '#ffffff',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              padding: '24px',
              textAlign: 'center',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
              <div style={{ fontSize: '28px', marginBottom: '12px', color: '#666' }}>📦</div>
              <h4 style={{ margin: '0 0 12px 0', color: '#333', fontSize: '16px', fontWeight: '600' }}>Inventory</h4>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#333', marginBottom: '8px' }}>
                {formatGrams(homeSummary.total_grams_remaining)}
              </div>
              <div style={{ fontSize: '14px', color: '#666' }}>
                {homeSummary.estimated_sessions_remaining > 0
                  ? `~${homeSummary.estimated_sessions_remaining} sessions left`
                  : 'Time to restock!'
                }
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          {homeSummary.total_grams_inventory > 0 && (
            <div style={{ marginBottom: '20px' }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '8px'
              }}>
                <span style={{ fontSize: '14px', fontWeight: 'bold', color: '#333' }}>
                  Inventory Progress
                </span>
                <span style={{ fontSize: '14px', color: '#666' }}>
                  {formatGrams(homeSummary.total_grams_remaining)} / {formatGrams(homeSummary.total_grams_inventory)}
                </span>
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                backgroundColor: '#e0e0e0',
                borderRadius: '4px',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${Math.max(0, Math.min(100, (homeSummary.total_grams_remaining / homeSummary.total_grams_inventory) * 100))}%`,
                  height: '100%',
                  backgroundColor: homeSummary.total_grams_remaining > (homeSummary.total_grams_inventory * 0.2) ? '#4caf50' : '#ff9800',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
          )}
        </div>
      )}

      <h3>Recent Brew Sessions</h3>
      <p>Your 15 most recent brew sessions:</p>
      
      <BrewSessionTable
        sessions={sessions}
        onDelete={handleDelete}
        onDuplicate={handleDuplicate}
        onEdit={handleEdit}
        onRefresh={fetchBrewSessions}
        showNewForm={showNewForm}
        setShowNewForm={setShowNewForm}
        setEditingSession={setEditingSession}
        filterOptions={filterOptions}
      />
    </div>
  );
}

export default Home;