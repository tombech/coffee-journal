import React, { useState, useEffect } from 'react';
import BrewSessionTable from './BrewSessionTable'; // Import the table component
import BrewSessionForm from './BrewSessionForm'; // Import the form component
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';

function BrewSessionList() {
  const { addToast } = useToast();
  const [brewSessions, setBrewSessions] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [editingSession, setEditingSession] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(30);
  const [sortColumn, setSortColumn] = useState('timestamp');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filters, setFilters] = useState({
    product_id: '',
    batch_id: '',
    brew_method: '',
    recipe: '',
    roaster: '',
    bean_type: '',
    country: '',
    grinder: '',
    filter: '',
    kettle: '',
    scale: '',
    min_score: '',
    max_score: ''
  });
  const [filterOptions, setFilterOptions] = useState(null);

  useEffect(() => {
    fetchBrewSessions(currentPage);
  }, [currentPage, pageSize, sortColumn, sortDirection, filters]);

  useEffect(() => {
    fetchFilterOptions(); // Fetch filter options only once on component mount
  }, []);

  const fetchFilterOptions = async () => {
    try {
      const response = await apiFetch('/brew_sessions/filter_options');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const options = await response.json();
      setFilterOptions(options);
    } catch (err) {
      console.error("Error fetching filter options:", err);
      // Don't set error state for filter options - just log it
      // The table will fall back to generating options from current sessions
    }
  };


  const fetchBrewSessions = async (page = 1) => {
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

      const response = await apiFetch(`/brew_sessions?${params}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setBrewSessions(result.data || []);
      setPagination(result.pagination || null);
    } catch (err) {
      setError("Failed to fetch brew sessions: " + err.message);
      console.error("Error fetching brew sessions:", err);
    } finally {
      setLoading(false);
    }
  };


  const handleDeleteBrewSession = async (sessionId) => {
    if (window.confirm("Are you sure you want to delete this brew session?")) {
        try {
            const response = await apiFetch(`/brew_sessions/${sessionId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            addToast("Brew session deleted successfully!", 'success');
            fetchBrewSessions(currentPage); // Refresh list after deletion
        } catch (err) {
            setError("Failed to delete brew session: " + err.message);
            console.error("Error deleting brew session:", err);
        }
    }
  };

  const handleDuplicateBrewSession = async (sessionId) => {
    try {
        // Find the session to get its batch_id
        const session = brewSessions.find(s => s.id === sessionId);
        if (!session || !session.product_batch_id) {
            throw new Error('Session not found or missing batch information');
        }
        
        const response = await apiFetch(`/batches/${session.product_batch_id}/brew_sessions/${sessionId}/duplicate`, {
            method: 'POST',
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        addToast("Brew session duplicated successfully!", 'success');
        fetchBrewSessions(currentPage); // Refresh list to show the new session
        console.log("Duplicated session:", result.new_session);
    } catch (err) {
        setError("Failed to duplicate brew session: " + err.message);
        console.error("Error duplicating brew session:", err);
    }
  };

  const handleNewBrewSessionSubmitted = () => {
    setShowNewForm(false);
    setCurrentPage(1); // Go to first page to see the newest session
    fetchBrewSessions(1); // Refresh list to show the new session
  };

  const handleEditBrewSession = (session) => {
    setEditingSession(session);
    setShowNewForm(false); // Close new form if open
  };

  const handleEditBrewSessionSubmitted = () => {
    setEditingSession(null);
    fetchBrewSessions(currentPage); // Refresh list to show the updated session
  };

  const handleCancelEdit = () => {
    setEditingSession(null);
  };

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };


  if (loading) return <p className="loading-message">Loading brew sessions...</p>;
  if (error) return <p className="error-message">{error}</p>;

  return (
    <div>
      <div style={{ marginBottom: '15px' }}>
        <h2 style={{ margin: 0 }}>All Brew Sessions</h2>
      </div>
      
      {showNewForm && (
        <div className="new-brew-session-form" style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
          <BrewSessionForm 
            onSessionSubmitted={handleNewBrewSessionSubmitted} 
            onCancel={() => setShowNewForm(false)}
          />
        </div>
      )}
      
      {editingSession && (
        <div className="edit-brew-session-form" style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#fff3cd', borderRadius: '5px', border: '1px solid #ffeaa7' }}>
          <h3>Edit Brew Session</h3>
          <BrewSessionForm 
            initialData={editingSession}
            onSessionSubmitted={handleEditBrewSessionSubmitted} 
          />
        </div>
      )}
      
      
      {brewSessions.length === 0 ? (
        <p>No brew sessions logged yet.</p>
      ) : (
        <>
          <BrewSessionTable
            sessions={brewSessions}
            onDelete={handleDeleteBrewSession}
            onDuplicate={handleDuplicateBrewSession}
            onEdit={handleEditBrewSession}
            onRefresh={() => fetchBrewSessions(currentPage)}
            showNewForm={showNewForm}
            setShowNewForm={setShowNewForm}
            setEditingSession={setEditingSession}
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

export default BrewSessionList;