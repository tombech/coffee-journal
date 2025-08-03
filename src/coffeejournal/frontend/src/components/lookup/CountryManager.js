import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiFetch } from '../../config';  
import { ICONS } from '../../config/icons';
import { useToast } from '../Toast';
import DeleteConfirmationModal from '../DeleteConfirmationModal';

function CountryManager() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  
  const [countries, setCountries] = useState([]);
  const [regionCounts, setRegionCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    short_form: '',
    description: '',
    notes: '',
    url: '',
    image_url: ''
  });
  const [submitting, setSubmitting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [countryToDelete, setCountryToDelete] = useState(null);
  const [usageInfo, setUsageInfo] = useState(null);

  useEffect(() => {
    fetchCountries();
  }, []);

  const fetchCountries = async () => {
    try {
      setLoading(true);
      const response = await apiFetch('/countries');
      if (!response.ok) throw new Error('Failed to fetch countries');
      const data = await response.json();
      setCountries(data);
      setLoading(false); // UI is ready as soon as countries are loaded
      
      // Fetch region counts asynchronously without blocking UI
      fetchRegionCounts(data);
    } catch (error) {
      setError(error.message);
      addToast('Failed to load countries: ' + error.message, 'error');
      setLoading(false);
    }
  };

  const fetchRegionCounts = async (countries) => {
    // Fetch region counts in background without blocking UI
    const counts = {};
    for (const country of countries) {
      try {
        const regionsResponse = await apiFetch(`/countries/${country.id}/regions`);
        if (regionsResponse.ok) {
          const regions = await regionsResponse.json();
          counts[country.id] = Array.isArray(regions) ? regions.length : 0;
        } else {
          counts[country.id] = 0;
        }
      } catch (err) {
        counts[country.id] = 0;
      }
    }
    setRegionCounts(counts);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      short_form: '',
      description: '',
      notes: '',
      url: '',
      image_url: ''
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      const response = await apiFetch('/countries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) throw new Error('Failed to create country');
      
      addToast('Country created successfully', 'success');
      setShowForm(false);
      resetForm();
      await fetchCountries();
    } catch (error) {
      addToast('Failed to create country: ' + error.message, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (country) => {
    try {
      // Check usage first
      const usageResponse = await apiFetch(`/countries/${country.id}/usage`);
      if (!usageResponse.ok) throw new Error('Failed to check country usage');
      
      const usage = await usageResponse.json();
      setUsageInfo(usage);
      setCountryToDelete(country);
      setShowDeleteModal(true);
    } catch (error) {
      addToast('Error checking country usage: ' + error.message, 'error');
    }
  };

  const handleDeleteConfirmed = async () => {
    try {
      const response = await apiFetch(`/countries/${countryToDelete.id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to delete country');
      
      addToast('Country deleted successfully', 'success');
      await fetchCountries();
    } catch (error) {
      addToast('Failed to delete country: ' + error.message, 'error');
    }
  };

  const cancelForm = () => {
    setShowForm(false);
    resetForm();
  };

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Loading countries...</div>;
  }

  if (error) {
    return <div style={{ padding: '20px', textAlign: 'center', color: 'red' }}>Error: {error}</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Countries</h2>
        <div>
          <button
            onClick={() => setShowForm(!showForm)}
            title={showForm ? 'Cancel' : 'Add Country'}
            aria-label={showForm ? 'Cancel' : 'Add Country'}
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
            onClick={() => navigate('/settings')}
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

      {/* Add Country Form */}
      {showForm && (
        <div style={{ 
          backgroundColor: '#f8f9fa', 
          padding: '20px', 
          borderRadius: '8px', 
          marginBottom: '30px',
          border: '2px solid #28a745'
        }}>
          <h3 style={{ marginTop: 0 }}>Add New Country</h3>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <div>
                <label htmlFor="country-name" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Name *
                </label>
                <input
                  id="country-name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  required
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}
                />
              </div>
              
              <div>
                <label htmlFor="country-short-form" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Short Form
                </label>
                <input
                  id="country-short-form"
                  type="text"
                  value={formData.short_form}
                  onChange={(e) => setFormData({...formData, short_form: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}
                />
              </div>
            </div>
            
            <div style={{ marginTop: '15px' }}>
              <label htmlFor="country-description" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Description
              </label>
              <textarea
                id="country-description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                rows="3"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  resize: 'vertical'
                }}
              />
            </div>
            
            <div style={{ marginTop: '15px' }}>
              <label htmlFor="country-notes" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Notes
              </label>
              <textarea
                id="country-notes"
                value={formData.notes}
                onChange={(e) => setFormData({...formData, notes: e.target.value})}
                rows="3"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  resize: 'vertical'
                }}
              />
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px', marginTop: '15px' }}>
              <div>
                <label htmlFor="country-url" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  URL
                </label>
                <input
                  id="country-url"
                  type="url"
                  value={formData.url}
                  onChange={(e) => setFormData({...formData, url: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}
                />
              </div>
              
              <div>
                <label htmlFor="country-image-url" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Image URL
                </label>
                <input
                  id="country-image-url"
                  type="url"
                  value={formData.image_url}
                  onChange={(e) => setFormData({...formData, image_url: e.target.value})}
                  style={{
                    width: '100%',
                    padding: '8px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}
                />
              </div>
            </div>
            
            <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
              <button
                type="submit"
                disabled={submitting}
                data-testid="create-country-btn"
                style={{
                  padding: '10px 20px',
                  background: 'none',
                  border: 'none',
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  opacity: submitting ? 0.6 : 1,
                  fontSize: '16px'
                }}
                aria-label={submitting ? 'Creating...' : 'Create Country'}
              >
                {submitting ? ICONS.LOADING : ICONS.CREATE}
              </button>
              <button
                type="button"
                onClick={cancelForm}
                style={{
                  padding: '10px 20px',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '16px'
                }}
                aria-label="Cancel"
              >
                {ICONS.CANCEL}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Countries Table */}
      <table style={{ width: '100%', borderCollapse: 'collapse' }} data-testid="countries-table" role="table">
          <thead>
            <tr style={{ backgroundColor: '#e9ecef' }}>
              <th scope="col" style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Name</th>
              <th scope="col" style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Short Form</th>
              <th scope="col" style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Description</th>
              <th scope="col" style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center' }}>Regions</th>
              <th scope="col" style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'center', width: '150px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {countries.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ 
                  padding: '40px', 
                  textAlign: 'center', 
                  color: '#6c757d', 
                  fontStyle: 'italic',
                  border: '1px solid #ddd'
                }}>
                  No countries found. Click "Add Country" to create one.
                </td>
              </tr>
            ) : (
              countries.map((country) => (
                <tr 
                  key={country.id} 
                  data-testid={`country-row-${country.id}`}
                  onClick={() => navigate(`/countries/${country.id}`)}
                  style={{ cursor: 'pointer' }}
                >
                  <td style={{ 
                    padding: '8px', 
                    border: '1px solid #ddd',
                    position: 'relative',
                    backgroundColor: country.is_default ? '#fff3cd' : 'transparent'
                  }} data-testid={`country-name-${country.id}`}>
                    {country.is_default && (
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
                    <span style={{ fontWeight: country.is_default ? 'bold' : 'normal' }}>
                      {country.name}
                    </span>
                    {country.is_default && (
                      <span 
                        style={{ marginLeft: '8px', fontSize: '11px', color: '#856404', fontStyle: 'italic' }}
                        aria-label="This is the default item"
                      >
                        Default
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                    {country.short_form || '-'}
                  </td>
                  <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                    {country.description ? (
                      <span title={country.description}>
                        {country.description.length > 50 ? 
                          country.description.substring(0, 50) + '...' : 
                          country.description
                        }
                      </span>
                    ) : '-'}
                  </td>
                  <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'center' }}>
                    {regionCounts[country.id] || 0} {(regionCounts[country.id] || 0) === 1 ? 'region' : 'regions'}
                  </td>
                  <td style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'center' }}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/countries/${country.id}`);
                      }}
                      title={`View ${country.name}`}
                      aria-label={`View ${country.name}`}
                      data-testid={`view-${country.name.toLowerCase().replace(/\s+/g, '-')}-btn`}
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
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/settings/countries/${country.id}/edit`);
                      }}
                      title={`Edit ${country.name} and manage regions`}
                      aria-label={`Edit ${country.name} and manage regions`}
                      data-testid={`edit-${country.name.toLowerCase().replace(/\s+/g, '-')}-btn`}
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
                        handleDelete(country);
                      }}
                      title={`Delete ${country.name}`}
                      aria-label={`Delete ${country.name}`}
                      data-testid={`delete-${country.name.toLowerCase().replace(/\s+/g, '-')}-btn`}
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
              ))
            )}
          </tbody>
      </table>

      {/* Delete Confirmation Modal */}
      {showDeleteModal && (
        <DeleteConfirmationModal
          item={countryToDelete}
          itemType="Country"
          usageInfo={usageInfo}
          apiEndpoint="countries"
          onClose={() => {
            setShowDeleteModal(false);
            setCountryToDelete(null);
            setUsageInfo(null);
          }}
          onDeleteConfirmed={handleDeleteConfirmed}
        />
      )}
    </div>
  );
}

export default CountryManager;