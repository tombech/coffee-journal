import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import MobileSearchModal from '../MobileSearchModal';
import { ICONS } from '../../config/icons';

function ShotSessionTable({
  shotSessions,
  onDelete,
  onDuplicate,
  onEdit,
  onRefresh,
  showNewForm,
  setShowNewForm,
  setEditingShotSession,
  pagination,
  pageSize,
  setPageSize,
  currentPage,
  setCurrentPage,
  sortColumn,
  setSortColumn,
  sortDirection,
  setSortDirection,
  onFiltersChange,
  filterOptions,
  filters
}) {
  const [showMobileSearch, setShowMobileSearch] = useState(false);

  const handleSort = (column) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const getSortIcon = (column) => {
    if (sortColumn !== column) return '';
    return sortDirection === 'asc' ? ' ↑' : ' ↓';
  };

  const handleFilterChange = (filterName, value) => {
    const newFilters = {
      ...filters,
      [filterName]: value
    };
    onFiltersChange(newFilters);
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

  const formatShotCount = (shotCount) => {
    return shotCount === 1 ? '1 shot' : `${shotCount} shots`;
  };

  const getPaginationInfo = () => {
    if (!pagination) return '';
    const start = (pagination.page - 1) * pagination.page_size + 1;
    const end = Math.min(pagination.page * pagination.page_size, pagination.total_count);
    return `Showing ${start}-${end} of ${pagination.total_count} shot sessions`;
  };

  const renderPaginationControls = () => {
    if (!pagination) return null;

    return (
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ fontSize: '14px', color: '#666' }}>
          {getPaginationInfo()}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
          <select
            value={pageSize}
            onChange={(e) => setPageSize(Number(e.target.value))}
            style={{ padding: '5px', border: '1px solid #ddd', borderRadius: '4px' }}
          >
            <option value={15}>15 per page</option>
            <option value={30}>30 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
          </select>
          
          <button
            onClick={() => setCurrentPage(currentPage - 1)}
            disabled={!pagination.has_previous}
            style={{
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              backgroundColor: pagination.has_previous ? 'white' : '#f5f5f5',
              cursor: pagination.has_previous ? 'pointer' : 'not-allowed'
            }}
          >
            Previous
          </button>
          
          <span style={{ padding: '8px 12px', fontWeight: 'bold' }}>
            Page {pagination.page} of {pagination.total_pages}
          </span>
          
          <button
            onClick={() => setCurrentPage(currentPage + 1)}
            disabled={!pagination.has_next}
            style={{
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: '4px',
              backgroundColor: pagination.has_next ? 'white' : '#f5f5f5',
              cursor: pagination.has_next ? 'pointer' : 'not-allowed'
            }}
          >
            Next
          </button>
        </div>
      </div>
    );
  };

  return (
    <div>
      {/* Controls and filters */}
      <div style={{ marginBottom: '20px', display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
        <button
          onClick={() => setShowMobileSearch(true)}
          style={{
            padding: '10px 15px',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '5px',
            cursor: 'pointer',
            display: 'block'
          }}
          className="mobile-search-btn"
        >
          🔍 Filter Sessions
        </button>
      </div>

      {/* Filters (Desktop) */}
      <div className="desktop-filters" style={{ marginBottom: '20px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px' }}>
        <input
          type="text"
          placeholder="Session name..."
          value={filters.title}
          onChange={(e) => handleFilterChange('title', e.target.value)}
          style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
        />
        
        <select
          value={filters.product_id}
          onChange={(e) => handleFilterChange('product_id', e.target.value)}
          style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
        >
          <option value="">All Products...</option>
          {filterOptions?.products?.map(product => (
            <option key={product.id} value={product.id}>{product.product_name}</option>
          ))}
        </select>

        <select
          value={filters.brewer_id}
          onChange={(e) => handleFilterChange('brewer_id', e.target.value)}
          style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
        >
          <option value="">All Brewers...</option>
          {filterOptions?.brewers?.map(brewer => (
            <option key={brewer.id} value={brewer.id}>{brewer.name}</option>
          ))}
        </select>

        <input
          type="number"
          placeholder="Min shots..."
          value={filters.min_shots}
          onChange={(e) => handleFilterChange('min_shots', e.target.value)}
          style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
        />

        <input
          type="number"
          placeholder="Max shots..."
          value={filters.max_shots}
          onChange={(e) => handleFilterChange('max_shots', e.target.value)}
          style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
        />
      </div>

      {/* Mobile Search Modal */}
      {showMobileSearch && (
        <MobileSearchModal
          isOpen={showMobileSearch}
          onClose={() => setShowMobileSearch(false)}
          onFiltersChange={onFiltersChange}
          filters={filters}
          filterOptions={filterOptions}
        />
      )}

      {/* Table */}
      <div className="table-container" style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '800px' }} role="table">
          <thead>
            <tr style={{ backgroundColor: '#f8f9fa' }}>
              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6', cursor: 'pointer' }}
                  onClick={() => handleSort('title')}>
                Session Name{getSortIcon('title')}
              </th>
              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6', cursor: 'pointer' }}
                  onClick={() => handleSort('product_name')}>
                Product{getSortIcon('product_name')}
              </th>
              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6', cursor: 'pointer' }}
                  onClick={() => handleSort('brewer_name')}>
                Brewer{getSortIcon('brewer_name')}
              </th>
              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6', cursor: 'pointer' }}
                  onClick={() => handleSort('shot_count')}>
                Shot Count{getSortIcon('shot_count')}
              </th>
              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '2px solid #dee2e6', cursor: 'pointer' }}
                  onClick={() => handleSort('created_at')}>
                Created{getSortIcon('created_at')}
              </th>
              <th style={{ padding: '12px', textAlign: 'center', borderBottom: '2px solid #dee2e6', width: '150px' }}>
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {shotSessions.map((session) => (
              <tr key={session.id} style={{ borderBottom: '1px solid #dee2e6' }}>
                <td style={{ padding: '12px' }}>
                  <Link
                    to={`/shot-sessions/${session.id}`}
                    data-testid={`view-shot-session-${session.id}`}
                    style={{ 
                      textDecoration: 'none', 
                      color: '#007bff', 
                      fontWeight: 'bold'
                    }}
                  >
                    {session.title || `Session ${session.id}`}
                  </Link>
                </td>
                <td style={{ padding: '12px' }}>
                  {session.product?.product_name || 'N/A'}
                </td>
                <td style={{ padding: '12px' }}>
                  {session.brewer?.name || 'N/A'}
                </td>
                <td style={{ padding: '12px' }}>
                  <span style={{ 
                    padding: '4px 8px', 
                    backgroundColor: '#e9ecef', 
                    borderRadius: '12px', 
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }}>
                    {formatShotCount(session.shot_count || 0)}
                  </span>
                </td>
                <td style={{ padding: '12px', fontSize: '14px', color: '#666' }}>
                  {formatDate(session.created_at)}
                </td>
                <td style={{ padding: '12px', textAlign: 'center' }}>
                  <div style={{ display: 'flex', gap: '5px', justifyContent: 'center' }}>
                    <button
                      onClick={() => onEdit(session)}
                      data-testid={`edit-shot-session-${session.id}`}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#ffc107',
                        color: 'black',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                      title="Edit session"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => onDuplicate(session.id)}
                      data-testid={`duplicate-shot-session-${session.id}`}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#17a2b8',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                      title="Duplicate session"
                    >
                      Duplicate
                    </button>
                    <button
                      onClick={() => onDelete(session.id)}
                      data-testid={`delete-shot-session-${session.id}`}
                      style={{
                        padding: '4px 8px',
                        backgroundColor: '#dc3545',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                      title="Delete session"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {renderPaginationControls()}
    </div>
  );
}

export default ShotSessionTable;