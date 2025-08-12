import React, { useState, useEffect } from 'react';
import { API_BASE_URL, apiFetch } from '../config';
import { ICONS } from '../config/icons';
import { useToast } from './Toast';
import DeleteConfirmationModal from './DeleteConfirmationModal';
import { useNavigate, useLocation } from 'react-router-dom';

function LookupManager({ 
  title, 
  apiEndpoint, 
  singularName, 
  onNavigateBack,
  fields = [], // Array of field definitions: [{name, label, type, required}]
  viewRoute = null // Optional: route pattern for view page (e.g., '/roasters' for '/roasters/:id')
}) {
  const { addToast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [formData, setFormData] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [itemToDelete, setItemToDelete] = useState(null);
  const [usageInfo, setUsageInfo] = useState(null);

  // Default fields that all lookup items have
  const defaultFields = [
    { name: 'name', label: 'Name', type: 'text', required: true },
    { name: 'short_form', label: 'Short Form', type: 'text', required: false },
    { name: 'description', label: 'Description', type: 'textarea', required: false },
    { name: 'notes', label: 'Notes', type: 'textarea', required: false },
    { name: 'url', label: 'URL', type: 'url', required: false },
    { name: 'image_url', label: 'Image URL', type: 'url', required: false },
    { name: 'icon', label: 'Icon File', type: 'file', required: false },
    { name: 'is_default', label: 'Set as Default', type: 'checkbox', required: false }
  ];

  const allFields = [...defaultFields, ...fields];

  const initializeFormData = () => {
    const initialData = {};
    allFields.forEach(field => {
      if (field.type === 'checkbox') {
        initialData[field.name] = false;
      } else if (field.type === 'number') {
        initialData[field.name] = null;
      } else {
        initialData[field.name] = '';
      }
    });
    return initialData;
  };

  useEffect(() => {
    fetchItems();
  }, [apiEndpoint]);

  useEffect(() => {
    // Check if we navigated here with an item to edit
    if (location.state?.editItem) {
      setEditingItem(location.state.editItem);
      setShowForm(true);
      // Clear the state to prevent re-editing on refresh
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  useEffect(() => {
    if (editingItem) {
      setFormData({ ...editingItem });
    } else {
      setFormData(initializeFormData());
    }
  }, [editingItem]);

  const fetchItems = async () => {
    try {
      setLoading(true);
      const response = await apiFetch(`/${apiEndpoint}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setItems(data);
    } catch (err) {
      setError(`Failed to fetch ${title.toLowerCase()}: ` + err.message);
      console.error(`Error fetching ${title}:`, err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    // Validate required fields
    for (const field of allFields) {
      if (field.required && !formData[field.name]?.trim()) {
        addToast(`${field.label} is required`, 'error');
        setSubmitting(false);
        return;
      }
    }

    // Validate number fields
    for (const field of allFields) {
      if (field.type === 'number' && formData[field.name] !== null && formData[field.name] !== undefined) {
        if (isNaN(formData[field.name])) {
          addToast(`${field.label} must be a valid number`, 'error');
          setSubmitting(false);
          return;
        }
        if (formData[field.name] < 0) {
          addToast(`${field.label} cannot be negative`, 'error');
          setSubmitting(false);
          return;
        }
      }
    }

    try {
      const method = editingItem ? 'PUT' : 'POST';
      const url = editingItem 
        ? `${API_BASE_URL}/${apiEndpoint}/${editingItem.id}`
        : `${API_BASE_URL}/${apiEndpoint}`;

      const response = await apiFetch(editingItem 
        ? `/${apiEndpoint}/${editingItem.id}`
        : `/${apiEndpoint}`, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      addToast(`${singularName} ${editingItem ? 'updated' : 'created'} successfully!`, 'success');
      setShowForm(false);
      setEditingItem(null);
      setFormData(initializeFormData());
      fetchItems();
    } catch (err) {
      addToast(`Failed to ${editingItem ? 'update' : 'create'} ${singularName.toLowerCase()}: ` + err.message, 'error');
      console.error(`Error submitting ${singularName}:`, err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (item) => {
    setItemToDelete(item);
    
    // Check if item is in use
    try {
      const usageUrl = `/${apiEndpoint}/${item.id}/usage`;
      console.log('Checking usage at:', usageUrl);
      
      const response = await apiFetch(usageUrl);
      console.log('Usage check response:', response.status, response.statusText);
      
      if (response.ok) {
        const usage = await response.json();
        console.log('Usage info received:', usage);
        setUsageInfo(usage);
      } else {
        console.warn('Usage endpoint returned error:', response.status, response.statusText);
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
      const response = await apiFetch(`/${apiEndpoint}/${itemToDelete.id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      addToast(`${singularName} deleted successfully!`, 'success');
      fetchItems();
    } catch (err) {
      addToast(`Failed to delete ${singularName.toLowerCase()}: ` + err.message, 'error');
      console.error(`Error deleting ${singularName}:`, err);
      throw err; // Re-throw to let modal handle it
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setShowForm(true);
  };

  const handleView = (item) => {
    if (viewRoute) {
      navigate(`${viewRoute}/${item.id}`);
    }
  };

  const handleCloseDeleteModal = () => {
    setShowDeleteModal(false);
    setItemToDelete(null);
    setUsageInfo(null);
  };

  const handleChange = (e) => {
    const { name, value, type, files, checked } = e.target;
    if (type === 'file') {
      // Handle file upload (we'll just store the filename for now)
      setFormData(prev => ({ ...prev, [name]: files[0]?.name || '' }));
    } else if (type === 'checkbox') {
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else if (type === 'number') {
      // Convert number inputs to actual numbers, handle empty string as null
      const numericValue = value === '' ? null : parseFloat(value);
      setFormData(prev => ({ ...prev, [name]: numericValue }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const renderField = (field) => {
    const { name, label, type, required } = field;
    const value = formData[name] === null || formData[name] === undefined ? '' : formData[name];

    switch (type) {
      case 'textarea':
        return (
          <textarea
            id={`${apiEndpoint}-${name}`}
            name={name}
            value={value}
            onChange={handleChange}
            required={required}
            rows="2"
            data-testid={`${apiEndpoint}-${name}-input`}
            style={{ 
              width: '100%', 
              padding: '8px 12px', 
              border: '1px solid #ced4da', 
              borderRadius: '4px', 
              fontSize: '14px', 
              resize: 'vertical' 
            }}
          />
        );
      case 'file':
        return (
          <input
            type="file"
            id={`${apiEndpoint}-${name}`}
            name={name}
            onChange={handleChange}
            accept="image/*"
            data-testid={`${apiEndpoint}-${name}-input`}
            style={{ 
              width: '100%', 
              padding: '8px 12px', 
              border: '1px solid #ced4da', 
              borderRadius: '4px', 
              fontSize: '14px' 
            }}
          />
        );
      case 'checkbox':
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="checkbox"
              id={`${apiEndpoint}-${name}`}
              name={name}
              checked={formData[name] || false}
              onChange={handleChange}
              data-testid={`${apiEndpoint}-${name}-input`}
              style={{ width: 'auto' }}
            />
            <span style={{ fontSize: '14px', color: '#666' }}>
              {formData[name] ? 'This will clear any existing default' : 'Make this the default for new brew sessions'}
            </span>
          </div>
        );
      default:
        return (
          <input
            type={type}
            id={`${apiEndpoint}-${name}`}
            name={name}
            value={value}
            onChange={handleChange}
            required={required}
            data-testid={`${apiEndpoint}-${name}-input`}
            style={{ 
              width: '100%', 
              padding: '8px 12px', 
              border: '1px solid #ced4da', 
              borderRadius: '4px', 
              fontSize: '14px',
              height: '32px',
              boxSizing: 'border-box'
            }}
          />
        );
    }
  };

  if (loading) return <p>Loading {title.toLowerCase()}...</p>;
  if (error) return <p className="error-message">{error}</p>;

  return (
    <div id="manager-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>{title}</h2>
        <div>
          <button 
            onClick={() => setShowForm(!showForm)}
            title={showForm ? 'Cancel' : `Add ${singularName}`}
            aria-label={showForm ? 'Cancel' : `Add ${singularName}`}
            data-testid={showForm ? 'cancel-form-btn' : 'add-item-btn'}
            style={{ 
              marginRight: '10px',
              padding: '8px 12px',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
{showForm ? ICONS.CANCEL : ICONS.CREATE}
          </button>
          <button 
            onClick={onNavigateBack}
            title="Back to Settings"
            aria-label="Back to Settings"
            data-testid="back-to-settings-btn"
            style={{ 
              padding: '8px 12px',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: '16px'
            }}
          >
{ICONS.BACK}
          </button>
        </div>
      </div>

      {showForm && (
        <div style={{ 
          marginBottom: '30px', 
          padding: '20px', 
          border: '1px solid #ddd', 
          borderRadius: '8px',
          backgroundColor: '#f9f9f9'
        }}>
          <h3 
            data-testid={editingItem ? "edit-form-heading" : "add-form-heading"}
            style={{ margin: '0 0 20px 0', fontSize: '18px', fontWeight: '600', color: '#495057' }}
          >
            {editingItem ? `Edit ${singularName}` : `Add New ${singularName}`}
          </h3>
          <form onSubmit={handleSubmit} data-testid="lookup-form">
            {/* Basic Information Section */}
            <div style={{
              backgroundColor: '#f8f9fa',
              padding: '16px',
              borderRadius: '8px',
              marginBottom: '16px',
              border: '1px solid #e9ecef'
            }}>
              <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600', color: '#495057', display: 'flex', alignItems: 'center', gap: '8px' }}>
                📝 Basic Information
              </h4>
              
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '12px'
              }}>
                {allFields.filter(field => ['name', 'short_form'].includes(field.name)).map(field => (
                  <div key={field.name}>
                    <label 
                      htmlFor={`${apiEndpoint}-${field.name}`}
                      style={{ fontSize: '12px', fontWeight: '600', display: 'block', marginBottom: '4px', color: '#495057' }}
                    >
                      {field.label}{field.required && ' *'}
                    </label>
                    {renderField(field)}
                  </div>
                ))}
              </div>
            </div>

            {/* Settings Section */}
            {allFields.some(field => ['is_default'].includes(field.name)) && (
              <div style={{
                backgroundColor: '#e8f4f8',
                padding: '16px',
                borderRadius: '8px',
                marginBottom: '16px',
                border: '1px solid #bee5eb'
              }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600', color: '#495057', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  ⚙️ Settings
                </h4>
                
                {allFields.filter(field => ['is_default'].includes(field.name)).map(field => (
                  <div key={field.name}>
                    <label 
                      htmlFor={`${apiEndpoint}-${field.name}`}
                      style={{ fontSize: '12px', fontWeight: '600', display: 'block', marginBottom: '4px', color: '#495057' }}
                    >
                      {field.label}{field.required && ' *'}
                    </label>
                    {renderField(field)}
                  </div>
                ))}
              </div>
            )}

            {/* Additional Information Section */}
            {allFields.some(field => ['description', 'notes', 'url', 'image_url', 'icon'].includes(field.name)) && (
              <div style={{
                backgroundColor: '#fff3cd',
                padding: '16px',
                borderRadius: '8px',
                marginBottom: '16px',
                border: '1px solid #ffeaa7'
              }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600', color: '#495057', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  🔗 Additional Information
                </h4>
                
                {/* Description and Notes - Side by Side */}
                {allFields.some(field => ['description', 'notes'].includes(field.name)) && (
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                    gap: '12px',
                    marginBottom: '12px'
                  }}>
                    {allFields.filter(field => ['description', 'notes'].includes(field.name)).map(field => (
                      <div key={field.name}>
                        <label 
                          htmlFor={`${apiEndpoint}-${field.name}`}
                          style={{ fontSize: '12px', fontWeight: '600', display: 'block', marginBottom: '4px', color: '#495057' }}
                        >
                          {field.label}{field.required && ' *'}
                        </label>
                        {renderField(field)}
                      </div>
                    ))}
                  </div>
                )}
                
                {/* URLs - Grid Layout */}
                {allFields.some(field => ['url', 'image_url'].includes(field.name)) && (
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                    gap: '12px',
                    marginBottom: '12px'
                  }}>
                    {allFields.filter(field => ['url', 'image_url'].includes(field.name)).map(field => (
                      <div key={field.name}>
                        <label 
                          htmlFor={`${apiEndpoint}-${field.name}`}
                          style={{ fontSize: '12px', fontWeight: '600', display: 'block', marginBottom: '4px', color: '#495057' }}
                        >
                          {field.label}{field.required && ' *'}
                        </label>
                        {renderField(field)}
                      </div>
                    ))}
                  </div>
                )}
                
                {/* Icon File - Full Width Row */}
                {allFields.filter(field => ['icon'].includes(field.name)).map(field => (
                  <div key={field.name} style={{ marginBottom: '12px' }}>
                    <label 
                      htmlFor={`${apiEndpoint}-${field.name}`}
                      style={{ fontSize: '12px', fontWeight: '600', display: 'block', marginBottom: '4px', color: '#495057' }}
                    >
                      {field.label}{field.required && ' *'}
                    </label>
                    {renderField(field)}
                  </div>
                ))}
              </div>
            )}

            {/* Custom Fields Section - Any fields not covered above */}
            {allFields.filter(field => !['name', 'short_form', 'description', 'notes', 'url', 'image_url', 'icon', 'is_default'].includes(field.name)).length > 0 && (
              <div style={{
                backgroundColor: '#e8f5e8',
                padding: '16px',
                borderRadius: '8px',
                marginBottom: '16px',
                border: '1px solid #c3e6c3'
              }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600', color: '#495057', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  🎯 Specific Information
                </h4>
                
                {allFields.filter(field => !['name', 'short_form', 'description', 'notes', 'url', 'image_url', 'icon', 'is_default'].includes(field.name)).map(field => (
                  <div key={field.name} style={{ marginBottom: '12px' }}>
                    <label 
                      htmlFor={`${apiEndpoint}-${field.name}`}
                      style={{ fontSize: '12px', fontWeight: '600', display: 'block', marginBottom: '4px', color: '#495057' }}
                    >
                      {field.label}{field.required && ' *'}
                    </label>
                    {renderField(field)}
                  </div>
                ))}
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ 
              display: 'flex', 
              gap: '10px', 
              justifyContent: 'flex-end',
              paddingTop: '16px',
              borderTop: '1px solid #e9ecef'
            }}>
              <button 
                type="button"
                onClick={handleSubmit}
                disabled={submitting}
                title={submitting ? 'Saving...' : (editingItem ? 'Update' : 'Submit new item')}
                aria-label={submitting ? 'Saving...' : (editingItem ? 'Update item' : 'Submit new item')}
                data-testid={editingItem ? 'update-item-btn' : 'create-item-btn'}
                style={{ 
                  padding: '10px 15px',
                  border: 'none',
                  background: 'none',
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  fontSize: '20px',
                  marginRight: '10px',
                  opacity: submitting ? 0.5 : 1
                }}
              >
{submitting ? ICONS.LOADING : ICONS.SAVE}
              </button>
              <button 
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingItem(null);
                  setFormData(initializeFormData());
                }}
                title="Cancel"
                aria-label="Cancel"
                data-testid="cancel-edit-btn"
                style={{ 
                  padding: '10px 15px',
                  border: 'none',
                  background: 'none',
                  cursor: 'pointer',
                  fontSize: '20px'
                }}
              >
{ICONS.CANCEL}
              </button>
            </div>
          </form>
        </div>
      )}

      <div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }} data-testid="items-table" role="table">
          <thead>
            <tr style={{ backgroundColor: '#e9ecef' }}>
              <th scope="col" style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Name</th>
              <th scope="col" style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Short Form</th>
              <th scope="col" style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Description</th>
              <th scope="col" style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center', width: viewRoute ? '150px' : '120px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr 
                key={item.id} 
                data-testid={`item-row-${item.id}`}
                onClick={() => viewRoute && handleView(item)}
                style={{ cursor: viewRoute ? 'pointer' : 'default' }}
              >
                <td style={{ 
                  padding: '8px', 
                  border: '1px solid #ddd',
                  position: 'relative',
                  backgroundColor: item.is_default ? '#fff3cd' : 'transparent'
                }}>
                  {item.is_default && (
                    <span 
                      style={{ 
                        position: 'absolute',
                        top: '2px',
                        right: '2px',
                        fontSize: '16px',
                        color: '#ff9800',
                        textShadow: '0 0 2px rgba(0,0,0,0.3)'
                      }}
                      aria-label="Default item indicator"
                      role="img"
                    >
                      {ICONS.DEFAULT}
                    </span>
                  )}
                  <span style={{ fontWeight: item.is_default ? 'bold' : 'normal' }}>
                    {item.name}
                  </span>
                  {item.is_default && (
                    <span 
                      style={{ marginLeft: '8px', fontSize: '11px', color: '#856404', fontStyle: 'italic' }}
                      aria-label="This is the default item"
                    >
                      Default
                    </span>
                  )}
                </td>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>{item.short_form || '-'}</td>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                  {item.description ? (
                    <span title={item.description}>
                      {item.description.length > 50 ? item.description.substring(0, 50) + '...' : item.description}
                    </span>
                  ) : '-'}
                </td>
                <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'center' }}>
                  {viewRoute && (
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleView(item);
                      }}
                      title={`View ${item.name}`}
                      aria-label={`View ${item.name}`}
                      data-testid={`view-${item.name.toLowerCase().replace(/\s+/g, '-')}-btn`}
                      style={{ 
                        marginRight: '5px',
                        padding: '2px 4px',
                        border: 'none',
                        background: 'none',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
{ICONS.VIEW}
                    </button>
                  )}
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEdit(item);
                    }}
                    title={`Edit ${item.name}`}
                    aria-label={`Edit ${item.name}`}
                    data-testid={`edit-${item.name.toLowerCase().replace(/\s+/g, '-')}-btn`}
                    style={{ 
                      marginRight: '5px',
                      padding: '2px 4px',
                      border: 'none',
                      background: 'none',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
{ICONS.EDIT}
                  </button>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(item);
                    }}
                    title={`Delete ${item.name}`}
                    aria-label={`Delete ${item.name}`}
                    data-testid={`delete-${item.name.toLowerCase().replace(/\s+/g, '-')}-btn`}
                    style={{ 
                      padding: '2px 4px',
                      border: 'none',
                      background: 'none',
                      cursor: 'pointer',
                      fontSize: '12px'
                    }}
                  >
{ICONS.DELETE}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {items.length === 0 && (
          <p style={{ textAlign: 'center', marginTop: '20px', color: '#666' }}>
            No {title.toLowerCase()} found. Add one to get started!
          </p>
        )}
      </div>

      <DeleteConfirmationModal
        isOpen={showDeleteModal}
        onClose={handleCloseDeleteModal}
        item={itemToDelete}
        itemType={singularName}
        apiEndpoint={apiEndpoint}
        usageInfo={usageInfo}
        onDeleteConfirmed={handleDeleteConfirmed}
        availableReplacements={items}
      />
    </div>
  );
}

export default LookupManager;