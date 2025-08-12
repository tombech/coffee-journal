import React, { useState, useEffect } from 'react';
import ShotSessionTable from './ShotSessionTable';
import ShotSessionForm from './ShotSessionForm';
import { useToast } from '../Toast';
import { apiFetch } from '../../config';
import { ICONS } from '../../config/icons';

function ShotSessionList() {
  const { addToast } = useToast();
  const [shotSessions, setShotSessions] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [editingShotSession, setEditingShotSession] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(30);
  const [sortColumn, setSortColumn] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filters, setFilters] = useState({
    title: '',
    product_id: '',
    product_batch_id: '',
    brewer_id: '',
    min_shots: '',
    max_shots: ''
  });
  const [filterOptions, setFilterOptions] = useState(null);

  useEffect(() => {
    fetchShotSessions(currentPage);
  }, [currentPage, pageSize, sortColumn, sortDirection, filters]);

  useEffect(() => {
    fetchFilterOptions();
  }, []);

  const fetchFilterOptions = async () => {
    try {
      const response = await apiFetch('/shot_sessions/filter_options');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const options = await response.json();
      setFilterOptions(options);
    } catch (err) {
      console.error("Error fetching filter options:", err);
      // Don't set error state for filter options - just log it
    }
  };

  const fetchShotSessions = async (page = 1) => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        sort: sortColumn,
        sort_direction: sortDirection
      });

      // Add filter parameters to API call
      Object.entries(filters).forEach(([key, value]) => {
        if (value && value.trim() !== '') {
          params.append(key, value);
        }
      });

      const response = await apiFetch(`/shot_sessions?${params}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setShotSessions(result.data || []);
      setPagination(result.pagination || null);
    } catch (err) {
      setError("Failed to fetch shot sessions: " + err.message);
      console.error("Error fetching shot sessions:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteShotSession = async (sessionId) => {
    if (window.confirm("Are you sure you want to delete this shot session? (Associated shots will not be deleted)")) {
      try {
        const response = await apiFetch(`/shot_sessions/${sessionId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        addToast("Shot session deleted successfully!", 'success');
        fetchShotSessions(currentPage);
      } catch (err) {
        setError("Failed to delete shot session: " + err.message);
        console.error("Error deleting shot session:", err);
      }
    }
  };

  const handleDuplicateShotSession = async (sessionId) => {
    try {
      const response = await apiFetch(`/shot_sessions/${sessionId}/duplicate`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      addToast("Shot session duplicated successfully!", 'success');
      fetchShotSessions(currentPage);
      console.log("Duplicated shot session:", result.new_shot_session);
    } catch (err) {
      setError("Failed to duplicate shot session: " + err.message);
      console.error("Error duplicating shot session:", err);
    }
  };

  const handleNewShotSessionSubmitted = () => {
    setShowNewForm(false);
    setCurrentPage(1);
    fetchShotSessions(1);
  };

  const handleEditShotSession = (shotSession) => {
    setEditingShotSession(shotSession);
    setShowNewForm(false);
  };

  const handleEditShotSessionSubmitted = () => {
    setEditingShotSession(null);
    fetchShotSessions(currentPage);
  };

  const handleCancelEdit = () => {
    setEditingShotSession(null);
  };

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  if (loading) return <p className="loading-message">Loading shot sessions...</p>;
  if (error) return <p className="error-message">{error}</p>;

  return (
    <div id="shot-session-list-page">
      <div style={{ marginBottom: '15px' }}>
        <h2 id="shot-session-list-title" style={{ margin: 0 }}>All Shot Sessions</h2>
        <p style={{ marginTop: '5px', color: '#666' }}>
          Group related shots together for dialing-in workflows
        </p>
      </div>
      
      {showNewForm && (
        <div className="new-shot-session-form" style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
          <ShotSessionForm 
            onShotSessionSubmitted={handleNewShotSessionSubmitted} 
            onCancel={() => setShowNewForm(false)}
          />
        </div>
      )}
      
      {editingShotSession && (
        <div className="edit-shot-session-form" style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#fff3cd', borderRadius: '5px', border: '1px solid #ffeaa7' }}>
          <h3>Edit Shot Session</h3>
          <ShotSessionForm 
            initialData={editingShotSession}
            onShotSessionSubmitted={handleEditShotSessionSubmitted} 
            onCancel={handleCancelEdit}
          />
        </div>
      )}
      
      {/* Always show the controls/button section */}
      <div style={{ marginBottom: '20px', display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
        <button
          onClick={() => setShowNewForm(!showNewForm)}
          style={{
            padding: '10px 20px',
            backgroundColor: showNewForm ? '#dc3545' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
          data-testid="new-shot-session-btn"
          aria-label={showNewForm ? 'Cancel new shot session' : 'Add new shot session'}
        >
          {showNewForm ? 'Cancel' : '+ New Shot Session'}
        </button>

        <button
          onClick={() => fetchShotSessions(currentPage)}
          style={{
            padding: '10px 15px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer'
          }}
        >
          Refresh
        </button>
      </div>

      {shotSessions.length === 0 ? (
        <p>No shot sessions created yet. Click "New Shot Session" to create your first one.</p>
      ) : (
        <>
          <ShotSessionTable
            shotSessions={shotSessions}
            onDelete={handleDeleteShotSession}
            onDuplicate={handleDuplicateShotSession}
            onEdit={handleEditShotSession}
            onRefresh={() => fetchShotSessions(currentPage)}
            showNewForm={showNewForm}
            setShowNewForm={setShowNewForm}
            setEditingShotSession={setEditingShotSession}
            pagination={pagination}
            pageSize={pageSize}
            setPageSize={setPageSize}
            currentPage={currentPage}
            setCurrentPage={setCurrentPage}
            sortColumn={sortColumn}
            setSortColumn={setSortColumn}
            sortDirection={sortDirection}
            setSortDirection={setSortDirection}
            onFiltersChange={handleFiltersChange}
            filterOptions={filterOptions}
            filters={filters}
          />
        </>
      )}
    </div>
  );
}

export default ShotSessionList;