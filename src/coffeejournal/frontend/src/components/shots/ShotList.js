import React, { useState, useEffect } from 'react';
import ShotTable from './ShotTable';
import ShotForm from './ShotForm';
import { useToast } from '../Toast';
import { apiFetch } from '../../config';
import { ICONS } from '../../config/icons';

function ShotList() {
  const { addToast } = useToast();
  const [shots, setShots] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [editingShot, setEditingShot] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(30);
  const [sortColumn, setSortColumn] = useState('timestamp');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filters, setFilters] = useState({
    product_id: '',
    product_batch_id: '',
    shot_session_id: '',
    brewer_id: '',
    extraction_status: '',
    min_score: '',
    max_score: ''
  });
  const [filterOptions, setFilterOptions] = useState(null);

  useEffect(() => {
    fetchShots(currentPage);
  }, [currentPage, pageSize, sortColumn, sortDirection, filters]);

  useEffect(() => {
    fetchFilterOptions();
  }, []);

  const fetchFilterOptions = async () => {
    try {
      const response = await apiFetch('/shots/filter_options');
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

  const fetchShots = async (page = 1) => {
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

      const response = await apiFetch(`/shots?${params}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      setShots(result.data || []);
      setPagination(result.pagination || null);
    } catch (err) {
      setError("Failed to fetch shots: " + err.message);
      console.error("Error fetching shots:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteShot = async (shotId) => {
    if (window.confirm("Are you sure you want to delete this shot?")) {
      try {
        const response = await apiFetch(`/shots/${shotId}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        addToast("Shot deleted successfully!", 'success');
        fetchShots(currentPage);
      } catch (err) {
        setError("Failed to delete shot: " + err.message);
        console.error("Error deleting shot:", err);
      }
    }
  };

  const handleDuplicateShot = async (shotId) => {
    try {
      const response = await apiFetch(`/shots/${shotId}/duplicate`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();
      addToast("Shot duplicated successfully!", 'success');
      fetchShots(currentPage);
      console.log("Duplicated shot:", result.new_shot);
    } catch (err) {
      setError("Failed to duplicate shot: " + err.message);
      console.error("Error duplicating shot:", err);
    }
  };

  const handleNewShotSubmitted = () => {
    setShowNewForm(false);
    setCurrentPage(1);
    fetchShots(1);
  };

  const handleEditShot = (shot) => {
    setEditingShot(shot);
    setShowNewForm(false);
  };

  const handleEditShotSubmitted = () => {
    setEditingShot(null);
    fetchShots(currentPage);
  };

  const handleCancelEdit = () => {
    setEditingShot(null);
  };

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
    setCurrentPage(1);
  };

  if (loading) return <p className="loading-message">Loading shots...</p>;
  if (error) return <p className="error-message">{error}</p>;

  return (
    <div id="shot-list-page">
      <div style={{ marginBottom: '15px' }}>
        <h2 id="shot-list-title" style={{ margin: 0 }}>All Shots</h2>
      </div>
      
      {showNewForm && (
        <div className="new-shot-form" style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '5px' }}>
          <ShotForm 
            onShotSubmitted={handleNewShotSubmitted} 
            onCancel={() => setShowNewForm(false)}
          />
        </div>
      )}
      
      {editingShot && (
        <div className="edit-shot-form" style={{ marginBottom: '20px', padding: '20px', backgroundColor: '#fff3cd', borderRadius: '5px', border: '1px solid #ffeaa7' }}>
          <h3>Edit Shot</h3>
          <ShotForm 
            initialData={editingShot}
            onShotSubmitted={handleEditShotSubmitted} 
            onCancel={handleCancelEdit}
          />
        </div>
      )}
      
      {/* Always show ShotTable so users can add their first shot */}
      <ShotTable
        shots={shots}
        onDelete={handleDeleteShot}
        onDuplicate={handleDuplicateShot}
        onEdit={handleEditShot}
        onRefresh={() => fetchShots(currentPage)}
        showNewForm={showNewForm}
        setShowNewForm={setShowNewForm}
        setEditingShot={setEditingShot}
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
    </div>
  );
}

export default ShotList;