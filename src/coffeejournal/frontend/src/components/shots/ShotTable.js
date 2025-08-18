import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { API_BASE_URL } from '../../config';
import { ICONS } from '../../config/icons';

function ShotTable({ 
  shots, 
  onDelete, 
  onDuplicate, 
  onEdit, 
  onRefresh, 
  showNewForm, 
  setShowNewForm, 
  setEditingShot, 
  showActions = true, 
  showFilters = true, 
  showAddButton = true, 
  showProduct = true, 
  title = null, 
  preserveOrder = false, 
  initialSort = 'timestamp', 
  initialSortDirection = 'desc', 
  pagination = null, 
  pageSize = 30, 
  setPageSize = null, 
  currentPage = 1, 
  setCurrentPage = null, 
  sortColumn: externalSortColumn = null, 
  setSortColumn: externalSetSortColumn = null, 
  sortDirection: externalSortDirection = null, 
  setSortDirection: externalSetSortDirection = null,
  onFiltersChange = null,
  filterOptions = null,
  filters: externalFilters = null
}) {
  
  // Use backend calculated score instead of computing locally
  const shotsWithScore = shots.map(shot => ({
    ...shot,
    calculatedScore: shot.calculated_score || shot.score || 0
  }));

  // Function to get short name for lookup items
  const getShortName = (fullName, shortForm = null) => {
    if (!fullName) return '';
    
    if (shortForm) {
      return shortForm;
    }
    
    const shortNameMap = {
      'La Marzocco GS3': 'LM GS3',
      'Breville Barista Express': 'BBE',
      'Rancilio Silvia': 'Silvia',
      'Gaggia Classic Pro': 'Gaggia',
      'Test Espresso Machine': 'Test ESM',
      'Standard Portafilter': 'Std PF',
      'Bottomless Portafilter': 'BL PF',
      'Standard Basket': 'Std',
      'Competition Basket': 'Comp',
      'IMS Basket': 'IMS',
      'Standard Tamper': 'Std T',
      'Calibrated Tamper': 'Cal T'
    };
    
    if (shortNameMap[fullName]) {
      return shortNameMap[fullName];
    }
    
    const words = fullName.split(' ');
    if (words.length === 1) {
      return words[0].length > 6 ? words[0].substring(0, 6) : words[0];
    } else if (words.length === 2) {
      return words.map(w => w.charAt(0)).join('') + words[1].substring(1, 3);
    } else {
      return words.map(w => w.charAt(0)).join('').substring(0, 4);
    }
  };

  // Function to detect if a field changed from the previous shot in the same session
  const getFieldChangeStatus = (currentShot, fieldName) => {
    // Only highlight changes within the same session
    if (!currentShot.shot_session_id) return null;
    
    // Find all shots in the same session, sorted by session shot number
    const sessionShots = shotsWithScore
      .filter(shot => shot.shot_session_id === currentShot.shot_session_id)
      .sort((a, b) => (a.session_shot_number || 0) - (b.session_shot_number || 0));
    
    // Find current shot index in the session
    const currentIndex = sessionShots.findIndex(shot => shot.id === currentShot.id);
    
    // If this is the first shot in the session, no comparison needed
    if (currentIndex <= 0) return null;
    
    const previousShot = sessionShots[currentIndex - 1];
    const currentValue = currentShot[fieldName];
    const previousValue = previousShot[fieldName];
    
    // Handle different field types
    if (fieldName === 'brewer_name') {
      return currentShot.brewer?.name !== previousShot.brewer?.name ? 'changed' : null;
    }
    
    // For numeric values, consider them different if they differ significantly
    if (typeof currentValue === 'number' && typeof previousValue === 'number') {
      return Math.abs(currentValue - previousValue) > 0.01 ? 'changed' : null;
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

  // Use external sorting state if provided, otherwise use internal state
  const [internalSortColumn, setInternalSortColumn] = useState(initialSort);
  const [internalSortDirection, setInternalSortDirection] = useState(initialSortDirection);
  
  const sortColumn = externalSortColumn || internalSortColumn;
  const setSortColumn = externalSetSortColumn || setInternalSortColumn;
  const sortDirection = externalSortDirection || internalSortDirection;
  const setSortDirection = externalSetSortDirection || setInternalSortDirection;

  // Filter state for UI
  const [localFilters, setLocalFilters] = useState({
    brewer: '',
    extraction_status: '',
    min_score: '',
    max_score: ''
  });
  
  const filters = externalFilters || localFilters;
  const setFilters = externalFilters ? () => {} : setLocalFilters;

  // Function to check if a product is decaf
  const isDecafProduct = (shot) => {
    return shot.product_details?.decaf === true;
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

  // Use API filter options if available
  const uniqueValues = useMemo(() => {
    if (filterOptions) {
      return {
        brewers: filterOptions.brewers || [],
        extraction_statuses: filterOptions.extraction_statuses || []
      };
    }
    
    return {
      brewers: [],
      extraction_statuses: []
    };
  }, [filterOptions, shotsWithScore]);

  const getSortIcon = (column) => {
    if (sortColumn !== column) return ' ↕';
    return sortDirection === 'desc' ? ' ↓' : ' ↑';
  };

  const handleSort = (column) => {
    if (!preserveOrder) {
      if (sortColumn === column) {
        setSortDirection(sortDirection === 'desc' ? 'asc' : 'desc');
      } else {
        setSortColumn(column);
        setSortDirection('desc');
      }
    }
  };

  const handleFilterChange = (filterKey, value) => {
    const newFilters = { ...filters, [filterKey]: value };
    setFilters(newFilters);
    if (onFiltersChange) {
      onFiltersChange(newFilters);
    }
  };

  const clearAllFilters = () => {
    const clearedFilters = Object.keys(filters).reduce((acc, key) => {
      acc[key] = '';
      return acc;
    }, {});
    setFilters(clearedFilters);
    if (onFiltersChange) {
      onFiltersChange(clearedFilters);
    }
  };

  const hasActiveFilters = Object.values(filters).some(value => value && value.trim() !== '');

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

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      {title && <h3>{title}</h3>}

      {/* Filter Controls */}
      {showFilters && (
      <div className="filter-controls" style={{ marginBottom: '15px', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '5px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>          
          <select
            value={filters.brewer || ''}
            onChange={(e) => handleFilterChange('brewer', e.target.value)}
            style={{ width: '120px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
          >
            <option value="">All Brewers</option>
            {uniqueValues.brewers.map((brewer) => (
              <option key={brewer.id || brewer.name} value={brewer.id || brewer.name}>
                {brewer.name}
              </option>
            ))}
          </select>

          <select
            aria-label="Filter by extraction status"
            value={filters.extraction_status || ''}
            onChange={(e) => handleFilterChange('extraction_status', e.target.value)}
            style={{ width: '130px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
          >
            <option value="">All Extraction Status</option>
            {uniqueValues.extraction_statuses.map((status) => (
              <option key={status} value={status}>
                {formatExtractionStatus(status)}
              </option>
            ))}
          </select>

          <input
            type="number"
            placeholder="Min Score"
            value={filters.min_score || ''}
            onChange={(e) => handleFilterChange('min_score', e.target.value)}
            style={{ width: '80px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
            step="0.1"
            min="0"
            max="10"
          />

          <input
            type="number"
            placeholder="Max Score"
            value={filters.max_score || ''}
            onChange={(e) => handleFilterChange('max_score', e.target.value)}
            style={{ width: '80px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
            step="0.1"
            min="0"
            max="10"
          />
          
          <button 
            onClick={clearAllFilters} 
            style={{ padding: '6px 8px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '14px' }}
            title="Clear Filters"
            aria-label="Clear Filters"
          >
            {ICONS.DELETE}
          </button>
          
          {showAddButton && (
          <button 
            onClick={() => {
              setShowNewForm(!showNewForm);
              setEditingShot(null);
            }}
            style={{ padding: '6px 8px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '14px' }}
            title={showNewForm ? 'Cancel' : 'New Shot'}
            aria-label={showNewForm ? 'Cancel' : 'New Shot'}
          >
            {showNewForm ? ICONS.CANCEL : ICONS.CREATE}
          </button>
          )}
        </div>
      </div>
      )}

      <table style={{ borderCollapse: 'collapse', fontSize: '12px', whiteSpace: 'nowrap' }}>
        <thead>
          <tr style={{ backgroundColor: '#e9ecef' }}>
            {showActions && (
            <th style={{ padding: '4px', border: '1px solid #ddd', width: '110px', fontSize: '12px', textAlign: 'left' }}>Actions</th>
            )}
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('📅', 'Date', 'timestamp', () => handleSort('timestamp'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('🕒', 'Coffee Age', 'coffee_age', () => handleSort('coffee_age'))}
            </th>
            {showProduct && (
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('🫘', 'Product', 'product_name', () => handleSort('product_name'))}
            </th>
            )}
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('☕', 'Brewer', 'brewer_name', () => handleSort('brewer_name'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('⚖️', 'Dose (g)', 'dose_grams', () => handleSort('dose_grams'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('☕', 'Yield (g)', 'yield_grams', () => handleSort('yield_grams'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('📊', 'Ratio', 'dose_yield_ratio', () => handleSort('dose_yield_ratio'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('💧', 'Flow Rate (g/s)', 'flow_rate', () => handleSort('flow_rate'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('⏱️', 'Extract Time (s)', 'extraction_time_seconds', () => handleSort('extraction_time_seconds'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('🌡️', 'Temperature (°C)', 'water_temperature_c', () => handleSort('water_temperature_c'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }} data-testid="grinder-setting-header">
              {createIconHeader('⚙️', 'Grind Setting', 'grinder_setting', () => handleSort('grinder_setting'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('🎯', 'Extraction', 'extraction_status', () => handleSort('extraction_status'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
              {createIconHeader('⭐', 'Score', 'overall_score', () => handleSort('overall_score'))}
            </th>
            <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }} title="Notes">
              📝
            </th>
          </tr>
        </thead>
        <tbody>
          {shotsWithScore.map(shot => (
            <tr key={shot.id} style={{ '&:hover': { backgroundColor: '#f8f9fa' } }}>
              {showActions && (
              <td style={{ padding: '2px', border: '1px solid #ddd', textAlign: 'center', fontSize: '11px', width: '110px', whiteSpace: 'nowrap' }}>
                <button 
                  onClick={() => onEdit(shot)}
                  title="Edit"
                  aria-label="Edit shot"
                  data-testid={`edit-shot-${shot.id}`}
                  style={{ padding: '2px 4px', margin: '0 1px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '12px' }}
                >
                  ✏️
                </button>
                <button 
                  onClick={() => onDuplicate(shot.id)}
                  title="Duplicate"
                  aria-label="Duplicate shot"
                  data-testid={`duplicate-shot-${shot.id}`}
                  style={{ padding: '2px 4px', margin: '0 1px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '12px' }}
                >
                  {ICONS.DUPLICATE}
                </button>
                <button 
                  onClick={() => onDelete(shot.id)}
                  title="Delete"
                  aria-label="Delete shot"
                  data-testid={`delete-shot-${shot.id}`}
                  style={{ padding: '2px 4px', margin: '0 1px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '12px' }}
                >
                  🗑️
                </button>
              </td>
              )}
              <td 
                style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top' }}
                title={`Full date/time: ${new Date(shot.timestamp).toLocaleString('nb-NO')}`}
                data-testid="shot-timestamp"
              >
                <Link 
                  to={`/shots/${shot.id}`} 
                  style={{ textDecoration: 'none', color: 'inherit' }}
                  aria-label={`View details for shot from ${new Date(shot.timestamp).toLocaleDateString('nb-NO')}`}
                  data-testid={`view-shot-${shot.id}`}
                >
                  {new Date(shot.timestamp).toLocaleDateString('nb-NO')}
                </Link>
              </td>
              <td 
                style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top', whiteSpace: 'nowrap', textAlign: 'center' }}
                title={`Coffee age: ${shot.coffee_age || 'Unknown'}`}
                data-testid="shot-coffee-age"
              >
                {shot.coffee_age || '-'}
              </td>
              {showProduct && (
              <td 
                style={{ 
                  padding: '4px', 
                  border: '1px solid #ddd', 
                  fontSize: '12px', 
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: '200px',
                  verticalAlign: 'top'
                }}
                title={`${shot.product_details?.product_name || 'Unknown'}\n\nBean Type: ${Array.isArray(shot.product_details?.bean_type) ? shot.product_details?.bean_type.map(bt => bt.name).join(', ') : 'Unknown'}\nRoaster: ${shot.product_details?.roaster?.name || 'Unknown'}\nRoast Date: ${shot.product_details?.roast_date ? new Date(shot.product_details.roast_date).toLocaleDateString('nb-NO') : 'Unknown'}${isDecafProduct(shot) ? '\n\n⚠️ DECAF PRODUCT' : ''}`}
              >
                {shot.product_id ? (
                  <Link to={`/products/${shot.product_id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                    {shot.product_details?.product_name || '-'}
                  </Link>
                ) : (
                  shot.product_details?.product_name || '-'
                )}
                {isDecafProduct(shot) && <span style={{ marginLeft: '4px', color: '#ff6b35' }} title="Decaf Product">D</span>}
              </td>
              )}
              <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top', whiteSpace: 'nowrap' }} title={shot.brewer?.name || ''}>
                {shot.brewer ? (
                  <Link to={`/brewers/${shot.brewer.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                    {getShortName(shot.brewer.name, shot.brewer.short_form)}
                  </Link>
                ) : '-'}
              </td>
              <td 
                style={getChangedFieldStyle(
                  { padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' },
                  getFieldChangeStatus(shot, 'dose_grams')
                )}
                data-testid="shot-dose-grams"
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
                {shot.dose_yield_ratio ? `1:${shot.dose_yield_ratio}` : '-'}
              </td>
              <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                {shot.flow_rate ? `${shot.flow_rate}g/s` : '-'}
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
                data-testid="shot-grinder-setting"
              >
                {shot.grinder_setting || '-'}
              </td>
              <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                {shot.extraction_status ? formatExtractionStatus(shot.extraction_status) : '-'}
              </td>
              <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap', fontWeight: 'bold' }}>
                {(typeof shot.calculatedScore === 'number' && shot.calculatedScore > 0) ? shot.calculatedScore.toFixed(1) : 
                 (shot.overall_score ? shot.overall_score.toFixed(1) : '-')}
              </td>
              <td 
                style={{ 
                  padding: '4px', 
                  border: '1px solid #ddd', 
                  fontSize: '12px', 
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  maxWidth: '600px',
                  verticalAlign: 'top'
                }} 
                title={shot.notes}
              >
                {shot.notes || '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {shotsWithScore.length === 0 && (
        <p style={{ textAlign: 'center', marginTop: '20px', color: '#666' }}>
          No shots match your current filters.
        </p>
      )}
      
      {/* Bottom Controls - Info on left, Page Size + Navigation on right */}
      {pagination && pagination.total_count > 0 && (
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
            Showing {((pagination.page - 1) * pagination.page_size) + 1}-{Math.min(pagination.page * pagination.page_size, pagination.total_count)} of {pagination.total_count} shots
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
      )}
    </div>
  );
}

export default ShotTable;