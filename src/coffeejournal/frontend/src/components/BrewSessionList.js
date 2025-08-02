import React, { useState, useEffect } from 'react';
import BrewSessionTable from './BrewSessionTable'; // Import the table component
import BrewSessionForm from './BrewSessionForm'; // Import the form component
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';

function BrewSessionList() {
  const { addToast } = useToast();
  const [brewSessions, setBrewSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [editingSession, setEditingSession] = useState(null);

  useEffect(() => {
    fetchBrewSessions();
  }, []);


  const fetchBrewSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch('/brew_sessions');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setBrewSessions(data);
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
            fetchBrewSessions(); // Refresh list after deletion
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
        fetchBrewSessions(); // Refresh list to show the new session
        console.log("Duplicated session:", result.new_session);
    } catch (err) {
        setError("Failed to duplicate brew session: " + err.message);
        console.error("Error duplicating brew session:", err);
    }
  };

  const handleNewBrewSessionSubmitted = () => {
    setShowNewForm(false);
    fetchBrewSessions(); // Refresh list to show the new session
  };

  const handleEditBrewSession = (session) => {
    setEditingSession(session);
    setShowNewForm(false); // Close new form if open
  };

  const handleEditBrewSessionSubmitted = () => {
    setEditingSession(null);
    fetchBrewSessions(); // Refresh list to show the updated session
  };

  const handleCancelEdit = () => {
    setEditingSession(null);
  };


  if (loading) return <p className="loading-message">Loading brew sessions...</p>;
  if (error) return <p className="error-message">{error}</p>;

  return (
    <div>
      <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <h2 style={{ margin: 0, marginRight: 'auto' }}>All Brew Sessions</h2>
        
        <button 
          onClick={() => setShowNewForm(!showNewForm)}
          style={{ padding: '6px 12px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '16px' }}
          title={showNewForm ? 'Cancel' : 'Add New Brew Session'}
          aria-label={showNewForm ? 'Cancel' : 'Add New Brew Session'}
        >
          {showNewForm ? ICONS.CANCEL : ICONS.CREATE}
        </button>
        
        {editingSession && (
          <button 
            onClick={handleCancelEdit}
            style={{ padding: '6px 12px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '16px' }}
            title="Cancel Edit"
            aria-label="Cancel Edit"
          >
            {ICONS.CANCEL} Edit
          </button>
        )}
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
        <BrewSessionTable
          sessions={brewSessions}
          onDelete={handleDeleteBrewSession}
          onDuplicate={handleDuplicateBrewSession}
          onEdit={handleEditBrewSession}
          onRefresh={fetchBrewSessions}
          showNewForm={showNewForm}
          setShowNewForm={setShowNewForm}
          setEditingSession={setEditingSession}
        />
      )}
    </div>
  );
}

export default BrewSessionList;