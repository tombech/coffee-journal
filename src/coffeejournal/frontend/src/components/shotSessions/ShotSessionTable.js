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
    if (sortColumn !== column) return ' ↕';
    return sortDirection === 'desc' ? ' ↓' : ' ↑';
  };

  // Function to create header with icon and hover text
  const createIconHeader = (icon, title, column, onClick) => (
    <span 
      style={{ cursor: 'pointer', userSelect: 'none', display: 'flex', alignItems: 'center', gap: '2px' }}
      title={title}
      onClick={onClick}
    >
      {icon}{getSortIcon(column)}
    </span>
  );

  const handleFilterChange = (filterName, value) => {
    const newFilters = {
      ...filters,
      [filterName]: value
    };
    onFiltersChange(newFilters);
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

  const formatShotCount = (shotCount) => {
    return shotCount === 1 ? '1 shot' : `${shotCount} shots`;
  };

  // Function to detect if a field changed from the previous session in the same product
  const getFieldChangeStatus = (currentSession, fieldName) => {
    // Only highlight changes within the same product
    if (!currentSession.product_id) return null;
    
    // Find all sessions for the same product, sorted by creation date
    const productSessions = shotSessions
      .filter(session => session.product_id === currentSession.product_id)
      .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    
    // Find current session index in the product sessions
    const currentIndex = productSessions.findIndex(session => session.id === currentSession.id);
    
    // If this is the first session for this product, no comparison needed
    if (currentIndex <= 0) return null;
    
    const previousSession = productSessions[currentIndex - 1];
    const currentValue = currentSession[fieldName];
    const previousValue = previousSession[fieldName];
    
    // Handle different field types
    if (fieldName === 'brewer') {
      return currentSession.brewer?.id !== previousSession.brewer?.id ? 'changed' : null;
    }
    
    // For string values, direct comparison
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

  const getPaginationInfo = () => {
    if (!pagination) return '';
    const start = (pagination.page - 1) * pagination.page_size + 1;
    const end = Math.min(pagination.page * pagination.page_size, pagination.total_count);
    return `Showing ${start}-${end} of ${pagination.total_count} shot sessions`;
  };

  const renderPaginationControls = () => {
    if (!pagination || pagination.total_count === 0) return null;

    return (
      <div style={{ 
        marginTop: '15px',
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '13px',
        color: '#6c757d',
        borderTop: '1px solid #eee',
        paddingTop: '12px'
      }}>
        {/* Left side: Showing info */}
        <span>
          {getPaginationInfo()}
        </span>

        {/* Right side: Page size selector + pagination controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Page size selector */}
          {setPageSize && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <label htmlFor="page-size-select">Show:</label>
              <select
                id="page-size-select"
                value={pageSize}
                onChange={(e) => {
                  setPageSize(Number(e.target.value));
                  if (setCurrentPage) setCurrentPage(1); // Reset to first page when changing page size
                }}
                style={{
                  padding: '3px 6px',
                  border: '1px solid #ddd',
                  borderRadius: '3px',
                  fontSize: '13px',
                  background: 'white'
                }}
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={15}>15</option>
                <option value={20}>20</option>
                <option value={30}>30</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
              <span>per page</span>
            </div>
          )}
          
          {/* Pagination controls - only show if more than one page */}
          {pagination.total_pages > 1 && setCurrentPage && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>
                Page {pagination.page} of {pagination.total_pages}
              </span>
              
              <button
                onClick={() => setCurrentPage(pagination.previous_page)}
                disabled={!pagination.has_previous}
                style={{
                  border: 'none',
                  background: 'none',
                  cursor: pagination.has_previous ? 'pointer' : 'not-allowed',
                  color: pagination.has_previous ? '#495057' : '#ccc',
                  fontSize: '16px',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  opacity: pagination.has_previous ? 1 : 0.5
                }}
                title="Previous page"
                aria-label="Previous page"
              >
                ◀
              </button>
              
              <button
                onClick={() => setCurrentPage(pagination.next_page)}
                disabled={!pagination.has_next}
                style={{
                  border: 'none',
                  background: 'none',
                  cursor: pagination.has_next ? 'pointer' : 'not-allowed',
                  color: pagination.has_next ? '#495057' : '#ccc',
                  fontSize: '16px',
                  padding: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  opacity: pagination.has_next ? 1 : 0.5
                }}
                title="Next page"
                aria-label="Next page"
              >
                ▶
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      {/* Filter Controls - Match ShotTable style */}
      <div className="filter-controls" style={{ marginBottom: '15px', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '5px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
          <label style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span style={{ fontSize: '12px', color: '#666', fontWeight: '500' }}>Session Name</span>
            <input
              type="text"
              placeholder="Session name..."
              value={filters.title}
              onChange={(e) => handleFilterChange('title', e.target.value)}
              style={{ width: '120px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
              aria-label="Filter by session name"
            />
          </label>
          
          <label style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span style={{ fontSize: '12px', color: '#666', fontWeight: '500' }}>Product</span>
            <select
              value={filters.product_id}
              onChange={(e) => handleFilterChange('product_id', e.target.value)}
              style={{ width: '130px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
              aria-label="Filter by product"
              data-testid="shot-session-product-filter"
            >
              <option value="">All Products</option>
              {filterOptions?.products?.map(product => (
                <option key={product.id} value={product.id}>{product.product_name}</option>
              ))}
            </select>
          </label>

          <label style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span style={{ fontSize: '12px', color: '#666', fontWeight: '500' }}>Brewer</span>
            <select
              value={filters.brewer_id}
              onChange={(e) => handleFilterChange('brewer_id', e.target.value)}
              style={{ width: '120px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
              aria-label="Filter by brewer"
              data-testid="shot-session-brewer-filter"
            >
              <option value="">All Brewers</option>
              {filterOptions?.brewers?.map(brewer => (
                <option key={brewer.id} value={brewer.id}>{brewer.name}</option>
              ))}
            </select>
          </label>

          <label style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span style={{ fontSize: '12px', color: '#666', fontWeight: '500' }}>Min Shots</span>
            <input
              type="number"
              placeholder="Min shots"
              value={filters.min_shots}
              onChange={(e) => handleFilterChange('min_shots', e.target.value)}
              style={{ width: '80px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
              aria-label="Filter by minimum number of shots"
            />
          </label>

          <label style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            <span style={{ fontSize: '12px', color: '#666', fontWeight: '500' }}>Max Shots</span>
            <input
              type="number"
              placeholder="Max shots"
              value={filters.max_shots}
              onChange={(e) => handleFilterChange('max_shots', e.target.value)}
              style={{ width: '80px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
              aria-label="Filter by maximum number of shots"
            />
          </label>

          <button
            onClick={() => setShowMobileSearch(true)}
            style={{ padding: '6px 8px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '14px' }}
            className="mobile-search-btn"
            title="Filter Sessions"
            aria-label="Filter Sessions"
          >
            {ICONS.FILTER}
          </button>
        </div>
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

      <table style={{ borderCollapse: 'collapse', fontSize: '12px', whiteSpace: 'nowrap' }}>
        <thead>
          <tr style={{ backgroundColor: '#e9ecef' }}>
            <th style={{ padding: '4px', border: '1px solid #ddd', width: '110px', fontSize: '12px', textAlign: 'left' }}>Actions</th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('📋', 'Session Name', 'title', () => handleSort('title'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('🫘', 'Product', 'product_name', () => handleSort('product_name'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('☕', 'Brewer', 'brewer_name', () => handleSort('brewer_name'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('#️⃣', 'Shot Count', 'shot_count', () => handleSort('shot_count'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('📅', 'Created', 'created_at', () => handleSort('created_at'))}
            </th>
          </tr>
        </thead>
        <tbody>
          {shotSessions.map((session) => (
            <tr key={session.id} style={{ '&:hover': { backgroundColor: '#f8f9fa' } }}>
              <td style={{ padding: '2px', border: '1px solid #ddd', textAlign: 'center', fontSize: '11px', width: '110px', whiteSpace: 'nowrap' }}>
                <button 
                  onClick={() => onEdit(session)}
                  title="Edit"
                  aria-label="Edit shot session"
                  data-testid={`edit-shot-session-${session.id}`}
                  style={{ padding: '2px 4px', margin: '0 1px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '12px' }}
                >
                  ✏️
                </button>
                <button 
                  onClick={() => onDuplicate(session.id)}
                  title="Duplicate"
                  aria-label="Duplicate shot session"
                  data-testid={`duplicate-shot-session-${session.id}`}
                  style={{ padding: '2px 4px', margin: '0 1px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '12px' }}
                >
                  {ICONS.DUPLICATE}
                </button>
                <button 
                  onClick={() => onDelete(session.id)}
                  title="Delete"
                  aria-label="Delete shot session"
                  data-testid={`delete-shot-session-${session.id}`}
                  style={{ padding: '2px 4px', margin: '0 1px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '12px' }}
                >
                  {ICONS.DELETE}
                </button>
              </td>
              <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top' }}>
                <Link
                  to={`/shot-sessions/${session.id}`}
                  data-testid={`view-shot-session-${session.id}`}
                  style={{ textDecoration: 'none', color: 'inherit' }}
                  aria-label={`View details for session ${session.title || session.id}`}
                >
                  {session.title || `Session ${session.id}`}
                </Link>
              </td>
              <td style={getChangedFieldStyle({ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top', whiteSpace: 'nowrap' }, getFieldChangeStatus(session, 'product_id'))}>
                {session.product ? (
                  <Link to={`/products/${session.product.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                    {session.product.product_name}
                  </Link>
                ) : (
                  '-'
                )}
              </td>
              <td style={getChangedFieldStyle({ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top', whiteSpace: 'nowrap' }, getFieldChangeStatus(session, 'brewer'))}>
                {session.brewer ? (
                  <Link to={`/brewers/${session.brewer.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                    {session.brewer.name}
                  </Link>
                ) : (
                  '-'
                )}
              </td>
              <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                <span style={{ 
                  padding: '2px 6px', 
                  backgroundColor: '#e9ecef', 
                  borderRadius: '8px', 
                  fontSize: '11px',
                  fontWeight: 'bold'
                }}>
                  {formatShotCount(session.shot_count || 0)}
                </span>
              </td>
              <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                {formatDate(session.created_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {shotSessions.length === 0 && (
        <p style={{ textAlign: 'center', marginTop: '20px', color: '#666' }}>
          No shot sessions match your current filters.
        </p>
      )}

      {renderPaginationControls()}
    </div>
  );
}

export default ShotSessionTable;