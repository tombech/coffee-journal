import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import DeleteConfirmationModal from './DeleteConfirmationModal';
import UsageStatistics from './UsageStatistics';

// Helper function to format field names for display
function formatFieldName(fieldName) {
  // Convert snake_case to Title Case
  return fieldName
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Helper function to format field values for display
function formatFieldValue(value, fieldName) {
  if (value === null || value === undefined) return null;

  // Handle boolean values
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }

  // Handle URLs
  if (fieldName === 'url' || fieldName === 'product_url') {
    return <a href={value} target="_blank" rel="noopener noreferrer">{value}</a>;
  }

  // Handle arrays (join with commas)
  if (Array.isArray(value)) {
    return value.join(', ');
  }

  // Handle multiline text (preserve line breaks)
  if (typeof value === 'string' && (fieldName === 'notes' || fieldName === 'instructions' || fieldName === 'description')) {
    return <span style={{ whiteSpace: 'pre-wrap' }}>{value}</span>;
  }

  // Default: return as string
  return String(value);
}

// Helper function to determine if a field should be displayed
function shouldDisplayField(fieldName, value) {
  // Skip these fields
  const skipFields = ['id', 'created_at', 'updated_at', 'is_default'];
  if (skipFields.includes(fieldName)) return false;

  // Skip empty values
  if (value === null || value === undefined || value === '') return false;

  // Skip empty arrays
  if (Array.isArray(value) && value.length === 0) return false;

  return true;
}

// Helper function to map lookup types to brew_sessions API filter parameter names
function getFilterType(lookupType) {
  const typeMap = {
    'roasters': 'roaster',
    'bean_types': 'bean_type', 
    'countries': 'country',
    'regions': 'region',
    'brew_methods': 'brew_method',
    'recipes': 'recipe',
    'decaf_methods': 'decaf_method',
    'grinders': 'grinder',
    'filters': 'filter',
    'kettles': 'kettle', 
    'scales': 'scale'
  };
  
  return typeMap[lookupType] || null;
}

function LookupDetail({ type, singularName, pluralName }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [item, setItem] = useState(null);
  const [usageData, setUsageData] = useState(null);
  const [statsData, setStatsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [usageInfo, setUsageInfo] = useState(null);

  useEffect(() => {
    fetchItemDetail();
  }, [id, type]);

  const fetchItemDetail = async (retryCount = 0) => {
    setLoading(true);
    try {
      // Prioritize the main item data - fetch it first
      const itemResponse = await apiFetch(`/${type}/${id}`);
      
      if (!itemResponse.ok) {
        // If server error and we haven't exhausted retries, try again
        if (itemResponse.status >= 500 && retryCount < 2) {
          console.warn(`Retrying ${singularName} detail fetch (attempt ${retryCount + 1})`);
          await new Promise(resolve => setTimeout(resolve, 1000 * (retryCount + 1)));
          return fetchItemDetail(retryCount + 1);
        }
        throw new Error(`HTTP error! status: ${itemResponse.status}`);
      }
      
      const itemData = await itemResponse.json();
      setItem(itemData);
      setError(null); // Clear any previous errors
      
      // Fetch usage data and stats separately without blocking the main render
      fetchUsageData();
      fetchStatsData();
    } catch (err) {
      setError(`Failed to fetch ${singularName.toLowerCase()} details: ` + err.message);
      console.error(`Error fetching ${singularName.toLowerCase()} details:`, err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsageData = async () => {
    try {
      const usageResponse = await apiFetch(`/${type}/${id}/usage`);
      if (usageResponse.ok) {
        const usageData = await usageResponse.json();
        setUsageData(usageData);
      }
    } catch (err) {
      // Silently fail for usage data - it's not critical for the main view
      console.warn(`Usage data fetch failed for ${singularName}: ${err.message}`);
      setUsageData(null);
    }
  };

  const fetchStatsData = async () => {
    try {
      const statsResponse = await apiFetch(`/stats/${type}/${id}`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStatsData(statsData);
      }
    } catch (err) {
      // Silently fail for stats data - it's not critical for the main view
      console.warn(`Stats data fetch failed for ${singularName}: ${err.message}`);
      setStatsData(null);
    }
  };


  const handleEdit = () => {
    // Countries have a dedicated edit page for managing regions
    if (type === 'countries') {
      navigate(`/settings/countries/${id}/edit`);
    } else {
      // Other lookups go back to the settings page with the item to edit
      navigate(`/settings/${type.replace('_', '-')}`, { 
        state: { editItem: item }
      });
    }
  };

  const handleDelete = async () => {
    // Check if item is in use first
    try {
      const usageUrl = `/${type}/${id}/usage`;
      const response = await apiFetch(usageUrl);
      
      if (response.ok) {
        const usage = await response.json();
        setUsageInfo(usage);
      } else {
        // If usage endpoint doesn't exist, assume it's not in use
        setUsageInfo({ in_use: false, usage_count: 0, usage_type: null });
      }
      setShowDeleteModal(true);
    } catch (err) {
      // If usage check fails, proceed with simple confirmation
      console.error('Usage check failed, proceeding with simple delete:', err);
      setUsageInfo({ in_use: false, usage_count: 0, usage_type: null });
      setShowDeleteModal(true);
    }
  };

  const handleDeleteConfirmed = async () => {
    try {
      const response = await apiFetch(`/${type}/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      addToast(`${singularName} deleted successfully!`, 'success');
      // Navigate back to the settings page
      navigate(`/settings/${type.replace('_', '-')}`);
    } catch (err) {
      addToast(`Failed to delete ${singularName.toLowerCase()}: ` + err.message, 'error');
      throw err; // Re-throw to let modal handle it
    }
  };

  const handleCloseDeleteModal = () => {
    setShowDeleteModal(false);
    setUsageInfo(null);
  };

  if (loading) return <p className="loading-message">Loading {singularName.toLowerCase()} details...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!item) return <p>{singularName} not found.</p>;

  return (
    <div>
      <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <h2 
          id="item-title"
          data-testid="item-title"
          style={{ 
            margin: 0, 
            marginRight: 'auto', 
            position: 'relative',
            padding: item.is_default ? '8px 12px' : '8px 0',
            backgroundColor: item.is_default ? '#fff3cd' : 'transparent',
            borderRadius: item.is_default ? '8px' : '0',
            border: item.is_default ? '2px solid #ffc107' : 'none'
          }}>
          {item.is_default && (
            <span style={{ 
              position: 'absolute',
              top: '-8px',
              right: '-8px',
              fontSize: '20px',
              color: '#ff9800',
              textShadow: '0 0 3px rgba(0,0,0,0.3)'
            }}>
              {ICONS.DEFAULT}
            </span>
          )}
          <span style={{ fontWeight: item.is_default ? 'bold' : 'normal' }}>
            {item.name}
          </span>
          {item.is_default && <span style={{ marginLeft: '8px', fontSize: '12px', color: '#856404', fontStyle: 'italic' }}>Default</span>}
        </h2>
        <button 
          onClick={handleEdit}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            marginRight: '5px'
          }}
          title={`Edit ${item.name}`}
          aria-label={`Edit ${item.name}`}
          data-testid="edit-item-btn"
        >
{ICONS.EDIT}
        </button>
        <button 
          onClick={handleDelete}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            marginRight: '5px'
          }}
          title={`Delete ${item.name}`}
          aria-label={`Delete ${item.name}`}
          data-testid="delete-item-btn"
        >
{ICONS.DELETE}
        </button>
        <Link 
          to={`/settings/${type}`}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            textDecoration: 'none',
            marginRight: '5px'
          }}
          title={`Manage ${pluralName}`}
          aria-label={`Manage ${pluralName}`}
        >
{ICONS.SETTINGS}
        </Link>
        <button 
          onClick={() => navigate(-1)}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px'
          }}
          title="Go Back"
          aria-label="Go Back"
        >
          {ICONS.BACK}
        </button>
      </div>

      {/* Default Status */}
      <div style={{
        marginBottom: '20px',
        padding: '12px 16px',
        backgroundColor: item.is_default ? '#fff3cd' : '#f8f9fa',
        borderRadius: '8px',
        border: item.is_default ? '2px solid #ffc107' : '1px solid #dee2e6',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        <span style={{ fontSize: '18px' }}>
          {item.is_default ? '⭐' : '☆'}
        </span>
        <span style={{
          fontWeight: item.is_default ? 'bold' : 'normal',
          color: item.is_default ? '#856404' : '#666'
        }}>
          {item.is_default ? 'This is the default selection' : 'Not set as default'}
        </span>
      </div>

      {/* Item Details */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 15px', alignItems: 'start' }}>
          {Object.entries(item)
            .filter(([fieldName, value]) => shouldDisplayField(fieldName, value))
            .map(([fieldName, value]) => {
              const formattedValue = formatFieldValue(value, fieldName);
              return (
                <React.Fragment key={fieldName}>
                  <strong>{formatFieldName(fieldName)}:</strong>
                  <span>{formattedValue}</span>
                </React.Fragment>
              );
            })}
        </div>
      </div>

      {/* Usage Statistics */}
      <UsageStatistics 
        usageData={usageData}
        statsData={statsData}
        itemName={singularName}
        showProduct={false}
        // New props for filtering brew sessions
        filterType={getFilterType(type)}
        filterId={parseInt(id)}
      />

      {/* Item Image */}
      {item.image_url && (
        <div style={{ marginBottom: '30px', textAlign: 'center' }}>
          <img 
            src={item.image_url} 
            alt={item.name} 
            style={{ 
              maxWidth: '300px', 
              maxHeight: '300px', 
              borderRadius: '8px',
              border: '1px solid #ddd'
            }} 
          />
        </div>
      )}

      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={handleCloseDeleteModal}
        item={item}
        itemType={singularName}
        apiEndpoint={type}
        usageInfo={usageInfo}
        onDeleteConfirmed={handleDeleteConfirmed}
        availableReplacements={[]} // Not needed for single item deletion
      />
    </div>
  );
}

export default LookupDetail;