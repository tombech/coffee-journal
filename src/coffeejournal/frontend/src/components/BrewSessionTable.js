import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { API_BASE_URL } from '../config';
import { ICONS } from '../config/icons';

function BrewSessionTable({ 
  sessions, 
  onDelete, 
  onDuplicate, 
  onEdit, 
  onRefresh, 
  showNewForm, 
  setShowNewForm, 
  setEditingSession, 
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
  onFiltersChange = null,  // Callback to pass filter changes to parent
  filterOptions = null,    // Pre-computed filter options from API
  filters: externalFilters = null,  // Filters from parent component
  testId = "brew-session-table"  // Allow customizing test ID to avoid conflicts
}) {
  
  // Use backend calculated score instead of computing locally
  const sessionsWithScore = sessions.map(session => ({
    ...session,
    calculatedScore: session.calculated_score || 0
  }));

  // Function to get short name for lookup items
  const getShortName = (fullName, shortForm = null) => {
    if (!fullName) return '';
    
    // Use explicitly set short_form if available
    if (shortForm) {
      return shortForm;
    }
    
    // Predefined short names for common items
    const shortNameMap = {
      'V60': 'V60',
      'Chemex': 'Cmx',
      'French Press': 'FP',
      'AeroPress': 'AP',
      'Espresso': 'Esp',
      'Pour Over': 'PO',
      'Cold Brew': 'CB',
      'Moka Pot': 'MP',
      'Paper Filter': 'Paper',
      'Metal Filter': 'Metal',
      'Hario V60 Paper Filter': 'V60P',
      'Cafec T90': 'T90',
      'Swiss water method': 'Swiss',
      'Wilfa Uniform Evo': 'Wilfa',
      'Digital Scale': 'Dig',
      'Acaia Pearl': 'Pearl',
      'Hario V60 Scale': 'V60S'
    };
    
    // Return predefined short name if exists
    if (shortNameMap[fullName]) {
      return shortNameMap[fullName];
    }
    
    // Generate short name from full name
    const words = fullName.split(' ');
    if (words.length === 1) {
      return words[0].length > 6 ? words[0].substring(0, 6) : words[0];
    } else if (words.length === 2) {
      return words.map(w => w.charAt(0)).join('') + words[1].substring(1, 3);
    } else {
      return words.map(w => w.charAt(0)).join('').substring(0, 4);
    }
  };
  // Use external sorting state if provided, otherwise use internal state
  const [internalSortColumn, setInternalSortColumn] = useState(initialSort);
  const [internalSortDirection, setInternalSortDirection] = useState(initialSortDirection);
  
  const sortColumn = externalSortColumn || internalSortColumn;
  const setSortColumn = externalSetSortColumn || setInternalSortColumn;
  const sortDirection = externalSortDirection || internalSortDirection;
  const setSortDirection = externalSetSortDirection || setInternalSortDirection;
  // Filter state for UI - actual filtering handled server-side
  // Use external filters if provided, otherwise use local state
  const [localFilters, setLocalFilters] = useState({
    roaster: '',
    bean_type: '',
    brew_method: '',
    recipe: '',
    filter: '',
    country: '',
    grinder: '',
    kettle: '',
    scale: '',
    min_score: '',
    max_score: ''
  });
  
  const filters = externalFilters || localFilters;
  const setFilters = externalFilters ? () => {} : setLocalFilters;
  
  // Function to check if a product is decaf
  const isDecafProduct = (session) => {
    return session.product_details?.decaf === true;
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

  // Use API filter options if available, otherwise generate from current sessions
  const uniqueValues = useMemo(() => {
    if (filterOptions) {
      // Use pre-computed filter options from API (now with ID-name pairs)
      return {
        roasters: filterOptions.roasters || [],
        bean_types: filterOptions.bean_types || [],
        brew_methods: filterOptions.brew_methods || [],
        recipes: filterOptions.recipes || [],
        filters: filterOptions.filters || [],
        countries: filterOptions.countries || [],
        grinders: filterOptions.grinders || [],
        kettles: filterOptions.kettles || [],
        scales: filterOptions.scales || [],
        decaf_options: filterOptions.decaf_options || []
      };
    }
    
    // Fallback: return empty arrays (API options should always be available)
    return {
      roasters: [],
      bean_types: [],
      brew_methods: [],
      recipes: [],
      filters: [],
      countries: [],
      grinders: [],
      kettles: [],
      scales: [],
      decaf_options: []
    };
  }, [filterOptions, sessionsWithScore]);

  // Sort sessions (server-side filtering means no client-side filtering needed)
  const sortedSessions = useMemo(() => {
    // If preserveOrder is true, return sessions as-is (server controls order)
    if (preserveOrder) {
      return sessionsWithScore;
    }
    
    // Otherwise apply client-side sorting
    return [...sessionsWithScore].sort((a, b) => {
      let aVal = a[sortColumn];
      let bVal = b[sortColumn];

      // Handle special cases
      if (sortColumn === 'bean_type') {
        aVal = Array.isArray(a.product_details?.bean_type) 
          ? a.product_details?.bean_type.map(bt => bt.name).join(', ') 
          : '';
        bVal = Array.isArray(b.product_details?.bean_type) 
          ? b.product_details?.bean_type.map(bt => bt.name).join(', ') 
          : '';
      } else if (sortColumn === 'product_name') {
        aVal = a.product_details?.product_name || '';
        bVal = b.product_details?.product_name || '';
      } else if (sortColumn === 'timestamp') {
        aVal = new Date(a.timestamp);
        bVal = new Date(b.timestamp);
      } else if (sortColumn === 'calculatedScore') {
        aVal = a.calculatedScore;
        bVal = b.calculatedScore;
      }

      // Handle null/undefined values
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return sortDirection === 'asc' ? -1 : 1;
      if (bVal == null) return sortDirection === 'asc' ? 1 : -1;

      // Compare values
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }, [sessionsWithScore, sortColumn, sortDirection, preserveOrder]);

  const handleSort = (column) => {
    // Map frontend column names to backend field names
    const columnMapping = {
      'calculatedScore': 'score'  // Only mapping needed now
    };
    
    // If we have server-side sorting handlers, use them
    if (setSortColumn && setSortDirection) {
      const serverColumn = columnMapping[column] || column;
      if (sortColumn === serverColumn) {
        setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
      } else {
        setSortColumn(serverColumn);
        setSortDirection('desc'); // Default to desc for most fields
      }
    } else {
      // Fallback to client-side sorting for backwards compatibility
      if (sortColumn === column) {
        setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
      } else {
        setSortColumn(column);
        setSortDirection('asc');
      }
    }
  };

  // Old filter handlers removed - using updated server-side ones below

  // Filter change handlers - pass changes to parent for server-side filtering
  const handleFilterChange = (column, value) => {
    const newFilters = { ...filters, [column]: value };
    if (externalFilters && onFiltersChange) {
      // When filters are managed externally, just notify parent
      onFiltersChange(newFilters);
    } else {
      // When using local filters, update local state
      setFilters(newFilters);
      if (onFiltersChange) {
        onFiltersChange(newFilters);
      }
    }
  };

  const clearFilters = () => {
    const emptyFilters = {
      roaster: '',
      bean_type: '',
      brew_method: '',
      recipe: '',
      filter: '',
      country: '',
      grinder: '',
      kettle: '',
      scale: '',
      min_score: '',
      max_score: ''
    };
    if (externalFilters && onFiltersChange) {
      // When filters are managed externally, just notify parent
      onFiltersChange(emptyFilters);
    } else {
      // When using local filters, update local state
      setFilters(emptyFilters);
      if (onFiltersChange) {
        onFiltersChange(emptyFilters);
      }
    }
  };

  const getSortIcon = (column) => {
    if (sortColumn !== column) return ' ↕️';
    return sortDirection === 'asc' ? ' ↑' : ' ↓';
  };

  const formatDateNorwegian = (dateString) => {
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear().toString().slice(-2);
    return `${day}.${month}.${year}`;
  };

  const formatTimeOnly = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('nb-NO', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('nb-NO');
  };

  const formatSecondsToMinSec = (seconds) => {
    if (!seconds) return '-';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes > 0) {
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    return `${seconds}s`;
  };

  return (
    <div className="brew-session-table-container">
      {title && <h3>{title}</h3>}
      {/* Filter Controls */}
      {showFilters && (
      <div className="filter-controls" style={{ marginBottom: '15px', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '5px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
          <select 
            value={filters.roaster} 
            onChange={(e) => handleFilterChange('roaster', e.target.value)}
            style={{ width: '120px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
          >
            <option value="">All Roasters</option>
            {uniqueValues.roasters.map(roaster => (
              <option key={roaster.id} value={roaster.id}>{roaster.name}</option>
            ))}
          </select>
          
          <select 
            value={filters.bean_type} 
            onChange={(e) => handleFilterChange('bean_type', e.target.value)}
            style={{ width: '120px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
          >
            <option value="">All Bean Types</option>
            {uniqueValues.bean_types.map(type => (
              <option key={type.id} value={type.id}>{type.name}</option>
            ))}
          </select>
          
          <select 
            aria-label="Filter by brew method"
            value={filters.brew_method} 
            onChange={(e) => handleFilterChange('brew_method', e.target.value)}
            style={{ width: '120px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
          >
            <option value="">All Brew Methods</option>
            {uniqueValues.brew_methods.map(method => (
              <option key={method.id} value={method.id}>{method.name}</option>
            ))}
          </select>
          
          <select 
            value={filters.recipe} 
            onChange={(e) => handleFilterChange('recipe', e.target.value)}
            style={{ width: '110px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
          >
            <option value="">All Recipes</option>
            {uniqueValues.recipes.map(recipe => (
              <option key={recipe.id} value={recipe.id}>{recipe.name}</option>
            ))}
          </select>
          
          <select 
            value={filters.filter} 
            onChange={(e) => handleFilterChange('filter', e.target.value)}
            style={{ width: '100px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
          >
            <option value="">All Filters</option>
            {uniqueValues.filters.map(filter => (
              <option key={filter.id} value={filter.id}>{filter.name}</option>
            ))}
          </select>

          <select 
            value={filters.country} 
            onChange={(e) => handleFilterChange('country', e.target.value)}
            style={{ width: '110px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
          >
            <option value="">All Countries</option>
            {uniqueValues.countries.map(country => (
              <option key={country.id} value={country.id}>{country.name}</option>
            ))}
          </select>

          <select 
            value={filters.grinder} 
            onChange={(e) => handleFilterChange('grinder', e.target.value)}
            style={{ width: '110px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
          >
            <option value="">All Grinders</option>
            {uniqueValues.grinders.map(grinder => (
              <option key={grinder.id} value={grinder.id}>{grinder.name}</option>
            ))}
          </select>

          <input
            type="number"
            placeholder="Min Score"
            value={filters.min_score}
            onChange={(e) => handleFilterChange('min_score', e.target.value)}
            style={{ width: '80px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
            min="0"
            max="10"
            step="0.1"
          />

          <input
            type="number"
            placeholder="Max Score"
            value={filters.max_score}
            onChange={(e) => handleFilterChange('max_score', e.target.value)}
            style={{ width: '80px', padding: '4px 6px', fontSize: '14px', border: '1px solid #ccc', borderRadius: '4px' }}
            min="0"
            max="10"
            step="0.1"
          />
          
          <button 
            onClick={clearFilters} 
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
              setEditingSession(null);
            }}
            style={{ padding: '6px 8px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '14px' }}
            title={showNewForm ? 'Cancel' : 'New Brew Session'}
            aria-label={showNewForm ? 'Cancel' : 'New Brew Session'}
          >
            {showNewForm ? ICONS.CANCEL : ICONS.CREATE}
          </button>
          )}
        </div>
      </div>
      )}

      {/* Table */}
      <div>
        <table data-testid={testId} style={{ borderCollapse: 'collapse', fontSize: '12px', whiteSpace: 'nowrap' }}>
          <thead>
            <tr style={{ backgroundColor: '#e9ecef' }}>
              {showActions && (
              <th style={{ padding: '4px', border: '1px solid #ddd', width: '110px', fontSize: '12px', textAlign: 'left' }}>Actions</th>
              )}
              {showProduct && (
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('🫘', 'Product', 'product_name', () => handleSort('product_name'))}
              </th>
              )}
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('📅', 'Date', 'timestamp', () => handleSort('timestamp'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('🕒', 'Coffee Age', 'coffee_age', () => handleSort('coffee_age'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('☕', 'Method', 'brew_method', () => handleSort('brew_method'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('📋', 'Recipe', 'recipe', () => handleSort('recipe'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('📄', 'Filter', 'filter', () => handleSort('filter'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('🫘', 'Coffee (g)', 'amount_coffee_grams', () => handleSort('amount_coffee_grams'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('💧', 'Water (g)', 'amount_water_grams', () => handleSort('amount_water_grams'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('⚖️', 'Ratio', 'brew_ratio', () => handleSort('brew_ratio'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('🌡️', 'Temperature (°C)', 'brew_temperature_c', () => handleSort('brew_temperature_c'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('🌸', 'Bloom Time', 'bloom_time_seconds', () => handleSort('bloom_time_seconds'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('⏱️', 'Brew Time', 'brew_time_seconds', () => handleSort('brew_time_seconds'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('🍯', 'Sweetness', 'sweetness', () => handleSort('sweetness'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('🍋', 'Acidity', 'acidity', () => handleSort('acidity'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('☕', 'Bitterness', 'bitterness', () => handleSort('bitterness'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('💪', 'Body', 'body', () => handleSort('body'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('👃', 'Aroma', 'aroma', () => handleSort('aroma'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('⚙️', 'Grinder', 'grinder', () => handleSort('grinder'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }} title="Grinder Setting">
                🔧
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }}>
                {createIconHeader('⭐', 'Score', 'calculatedScore', () => handleSort('calculatedScore'))}
              </th>
              <th style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', whiteSpace: 'nowrap', textAlign: 'left' }} title="Notes">
                📝
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedSessions.map(session => (
              <tr key={session.id} style={{ '&:hover': { backgroundColor: '#f8f9fa' } }}>
                {showActions && (
                <td style={{ padding: '2px', border: '1px solid #ddd', textAlign: 'center', fontSize: '11px', width: '110px', whiteSpace: 'nowrap' }}>
                  <button 
                    onClick={() => onEdit(session)}
                    title="Edit"
                    aria-label="Edit brew session"
                    data-testid={`edit-brew-session-${session.id}`}
                    style={{ padding: '2px 4px', margin: '0 1px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '12px' }}
                  >
                    ✏️
                  </button>
                  <button 
                    onClick={() => onDuplicate(session.id, session.product_batch_id)}
                    title="Duplicate"
                    aria-label="Duplicate brew session"
                    style={{ padding: '2px 4px', margin: '0 1px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '12px' }}
                  >
{ICONS.DUPLICATE}
                  </button>
                  <button 
                    onClick={() => onDelete(session.id)}
                    title="Delete"
                    aria-label="Delete brew session"
                    data-testid={`delete-brew-session-${session.id}`}
                    style={{ padding: '2px 4px', margin: '0 1px', border: 'none', background: 'none', cursor: 'pointer', fontSize: '12px' }}
                  >
                    🗑️
                  </button>
                </td>
                )}
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
                  title={`${session.product_details?.product_name || 'Unknown'}\n\nBean Type: ${Array.isArray(session.product_details?.bean_type) ? session.product_details?.bean_type.map(bt => bt.name).join(', ') : 'Unknown'}\nRoaster: ${session.product_details?.roaster?.name || 'Unknown'}\nRoast Date: ${session.product_details?.roast_date ? formatDateNorwegian(session.product_details?.roast_date) : 'Unknown'}${isDecafProduct(session) ? '\n\n⚠️ DECAF PRODUCT' : ''}`}
                >
                  {session.product_id ? (
                    <Link to={`/products/${session.product_id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                      {session.product_details?.product_name || '-'}
                    </Link>
                  ) : (
                    session.product_details?.product_name || '-'
                  )}
                  {isDecafProduct(session) && <span style={{ marginLeft: '4px', color: '#ff6b35' }} title="Decaf Product">D</span>}
                </td>
                )}
                <td 
                  style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top' }}
                  title={`Full date/time: ${formatDateTime(session.timestamp)}`}
                  data-testid="session-timestamp"
                >
                  <Link 
                    to={`/brew-sessions/${session.id}`} 
                    style={{ textDecoration: 'none', color: 'inherit' }}
                    aria-label={`View details for brew session from ${formatDateNorwegian(session.timestamp)}`}
                    data-testid={`view-brew-session-${session.id}`}
                  >
                    {formatDateNorwegian(session.timestamp)}
                  </Link>
                </td>
                <td 
                  style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top', whiteSpace: 'nowrap', textAlign: 'center' }}
                  title={`Coffee age: ${session.coffee_age || 'Unknown'}`}
                  data-testid="session-coffee-age"
                >
                  {session.coffee_age || '-'}
                </td>
                <td 
                  style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top', whiteSpace: 'nowrap' }} 
                  title={session.brew_method?.name || ''}
                  data-testid="session-brew-method"
                >
                  {session.brew_method ? (
                    <Link to={`/brew-methods/${session.brew_method.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                      {getShortName(session.brew_method.name, session.brew_method.short_form)}
                    </Link>
                  ) : '-'}
                </td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top', whiteSpace: 'nowrap' }} title={session.recipe?.name || ''}>
                  {session.recipe ? (
                    <Link to={`/recipes/${session.recipe.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                      {getShortName(session.recipe.name, session.recipe.short_form)}
                    </Link>
                  ) : '-'}
                </td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top', whiteSpace: 'nowrap' }} title={session.filter?.name || ''}>
                  {session.filter ? (
                    <Link to={`/filters/${session.filter.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                      {getShortName(session.filter.name, session.filter.short_form)}
                    </Link>
                  ) : '-'}
                </td>
                <td 
                  style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}
                  data-testid="session-coffee-grams"
                >
                  {session.amount_coffee_grams ? `${session.amount_coffee_grams}g` : '-'}
                </td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                  {session.amount_water_grams ? `${session.amount_water_grams}g` : '-'}
                </td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>{session.brew_ratio || '-'}</td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                  {session.brew_temperature_c ? `${session.brew_temperature_c}°C` : '-'}
                </td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                  {formatSecondsToMinSec(session.bloom_time_seconds)}
                </td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>
                  {formatSecondsToMinSec(session.brew_time_seconds)}
                </td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>{session.sweetness || '-'}</td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>{session.acidity || '-'}</td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>{session.bitterness || '-'}</td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>{session.body || '-'}</td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap' }}>{session.aroma || '-'}</td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top', whiteSpace: 'nowrap' }} title={session.grinder?.name || ''}>
                  {session.grinder ? (
                    <Link to={`/grinders/${session.grinder.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                      {getShortName(session.grinder.name, session.grinder.short_form)}
                    </Link>
                  ) : '-'}
                </td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', verticalAlign: 'top', whiteSpace: 'nowrap' }}>{session.grinder_setting || '-'}</td>
                <td style={{ padding: '4px', border: '1px solid #ddd', fontSize: '12px', textAlign: 'center', verticalAlign: 'top', whiteSpace: 'nowrap', fontWeight: 'bold' }}>
                  {(typeof session.calculatedScore === 'number' && session.calculatedScore > 0) ? session.calculatedScore.toFixed(1) : 
                   (console.log('DEBUG Score:', session.id, 'calculatedScore:', session.calculatedScore, 'type:', typeof session.calculatedScore, 'score:', session.score, 'tasting:', {sweetness: session.sweetness, acidity: session.acidity, bitterness: session.bitterness, body: session.body, aroma: session.aroma}), '-')}
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
                  title={session.notes}
                >
                  {session.notes || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {sortedSessions.length === 0 && (
        <p style={{ textAlign: 'center', marginTop: '20px', color: '#666' }}>
          No brew sessions match your current filters.
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
            Showing {((pagination.page - 1) * pagination.page_size) + 1}-{Math.min(pagination.page * pagination.page_size, pagination.total_count)} of {pagination.total_count} sessions
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

export default BrewSessionTable;