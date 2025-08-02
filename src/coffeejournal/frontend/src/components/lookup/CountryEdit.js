import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { apiFetch } from '../../config';
import { ICONS } from '../../config/icons';
import { useToast } from '../Toast';

function CountryEdit() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  
  const [country, setCountry] = useState(null);
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Country form state
  const [countryForm, setCountryForm] = useState({
    name: '',
    short_form: '',
    description: '',
    notes: '',
    url: '',
    image_url: ''
  });
  
  // Region form state
  const [showRegionForm, setShowRegionForm] = useState(false);
  const [editingRegion, setEditingRegion] = useState(null);
  const [regionForm, setRegionForm] = useState({
    name: '',
    short_form: '',
    description: '',
    notes: '',
    url: '',
    image_url: '',
    is_default: false
  });

  useEffect(() => {
    if (id) {
      fetchCountry();
      fetchRegions();
    }
  }, [id]);

  const fetchCountry = async () => {
    try {
      const response = await apiFetch(`/countries/${id}`);
      if (!response.ok) throw new Error('Failed to fetch country');
      const data = await response.json();
      setCountry(data);
      setCountryForm({
        name: data.name || '',
        short_form: data.short_form || '',
        description: data.description || '',
        notes: data.notes || '',
        url: data.url || '',
        image_url: data.image_url || ''
      });
    } catch (error) {
      addToast('Failed to load country: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchRegions = async () => {
    try {
      const response = await apiFetch(`/countries/${id}/regions`);
      if (!response.ok) throw new Error('Failed to fetch regions');
      const data = await response.json();
      setRegions(Array.isArray(data) ? data : []);
    } catch (error) {
      addToast('Failed to load regions: ' + error.message, 'error');
    }
  };

  const handleCountrySubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      const response = await apiFetch(`/countries/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(countryForm)
      });
      
      if (!response.ok) throw new Error('Failed to update country');
      
      addToast('Country updated successfully', 'success');
      fetchCountry();
    } catch (error) {
      addToast('Failed to update country: ' + error.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleRegionSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      const regionData = { ...regionForm, country_id: parseInt(id) };
      const url = editingRegion 
        ? `/regions/${editingRegion.id}`
        : `/regions`;
      const method = editingRegion ? 'PUT' : 'POST';
      
      const response = await apiFetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(regionData)
      });
      
      if (!response.ok) throw new Error(`Failed to ${editingRegion ? 'update' : 'create'} region`);
      
      addToast(`Region ${editingRegion ? 'updated' : 'created'} successfully`, 'success');
      setShowRegionForm(false);
      setEditingRegion(null);
      setRegionForm({ name: '', short_form: '', description: '', notes: '', url: '', image_url: '', is_default: false });
      fetchRegions();
    } catch (error) {
      addToast(`Failed to ${editingRegion ? 'update' : 'create'} region: ` + error.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleEditRegion = (region) => {
    setEditingRegion(region);
    setRegionForm({
      name: region.name || '',
      short_form: region.short_form || '',
      description: region.description || '',
      notes: region.notes || '',
      url: region.url || '',
      image_url: region.image_url || '',
      is_default: region.is_default || false
    });
    setShowRegionForm(true);
  };

  const handleDeleteRegion = async (region) => {
    if (!window.confirm(`Are you sure you want to delete the region "${region.name}"?`)) {
      return;
    }
    
    try {
      const response = await apiFetch(`/regions/${region.id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to delete region');
      
      addToast('Region deleted successfully', 'success');
      fetchRegions();
    } catch (error) {
      addToast('Failed to delete region: ' + error.message, 'error');
    }
  };

  const cancelRegionForm = () => {
    setShowRegionForm(false);
    setEditingRegion(null);
    setRegionForm({ name: '', short_form: '', description: '', notes: '', url: '', image_url: '', is_default: false });
  };

  if (loading) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Loading...</div>;
  }

  if (!country) {
    return <div style={{ padding: '20px', textAlign: 'center' }}>Country not found</div>;
  }

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '30px' }}>
        <button 
          onClick={() => navigate('/settings/countries')}
          style={{
            marginRight: '15px',
            padding: '8px 12px',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            fontSize: '16px'
          }}
          aria-label="Back to Countries"
        >
          {ICONS.BACK}
        </button>
        <h1 style={{ margin: 0 }}>Edit Country: {country.name}</h1>
      </div>

      {/* Country Form */}
      <div style={{ 
        backgroundColor: '#f8f9fa', 
        padding: '20px', 
        borderRadius: '8px', 
        marginBottom: '30px' 
      }}>
        <h3 style={{ marginTop: 0 }}>Country Details</h3>
        <form onSubmit={handleCountrySubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
            <div>
              <label htmlFor="country-name" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                Name *
              </label>
              <input
                id="country-name"
                type="text"
                value={countryForm.name}
                onChange={(e) => setCountryForm({...countryForm, name: e.target.value})}
                required
                data-testid="country-name-input"
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
                Country Short Form
              </label>
              <input
                id="country-short-form"
                type="text"
                value={countryForm.short_form}
                onChange={(e) => setCountryForm({...countryForm, short_form: e.target.value})}
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
              Country Description
            </label>
            <textarea
              id="country-description"
              value={countryForm.description}
              onChange={(e) => setCountryForm({...countryForm, description: e.target.value})}
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
              Country Notes
            </label>
            <textarea
              id="country-notes"
              value={countryForm.notes}
              onChange={(e) => setCountryForm({...countryForm, notes: e.target.value})}
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
                Country URL
              </label>
              <input
                id="country-url"
                type="url"
                value={countryForm.url}
                onChange={(e) => setCountryForm({...countryForm, url: e.target.value})}
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
                value={countryForm.image_url}
                onChange={(e) => setCountryForm({...countryForm, image_url: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px'
                }}
              />
            </div>
          </div>
          
          <button
            type="button"
            onClick={handleCountrySubmit}
            disabled={saving}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              background: 'none',
              border: 'none',
              cursor: saving ? 'not-allowed' : 'pointer',
              opacity: saving ? 0.6 : 1,
              fontSize: '16px'
            }}
            aria-label={saving ? 'Saving...' : 'Save Country'}
          >
            {saving ? ICONS.LOADING : ICONS.SAVE}
          </button>
        </form>
      </div>

      {/* Regions Section */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ margin: 0 }}>Regions in {country.name}</h2>
          <button
            onClick={() => setShowRegionForm(true)}
            data-testid="add-region-button"
            style={{
              padding: '8px 16px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px'
            }}
            aria-label="Add Region"
          >
            {ICONS.CREATE}
          </button>
        </div>

        {/* Region Form */}
        {showRegionForm && (
          <div style={{ 
            backgroundColor: '#f8f9fa', 
            padding: '20px', 
            borderRadius: '8px', 
            marginBottom: '20px',
            border: '2px solid #28a745'
          }}>
            <h3 style={{ marginTop: 0 }}>
              {editingRegion ? `Edit Region: ${editingRegion.name}` : 'Add New Region'}
            </h3>
            <form onSubmit={handleRegionSubmit}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                <div>
                  <label htmlFor="region-name" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                    Region Name *
                  </label>
                  <input
                    id="region-name"
                    type="text"
                    value={regionForm.name}
                    onChange={(e) => setRegionForm({...regionForm, name: e.target.value})}
                    required
                    data-testid="region-name-input"
                    style={{
                      width: '100%',
                      padding: '8px',
                      border: '1px solid #ddd',
                      borderRadius: '4px'
                    }}
                  />
                </div>
                
                <div>
                  <label htmlFor="region-short-form" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                    Region Short Form
                  </label>
                  <input
                    id="region-short-form"
                    type="text"
                    value={regionForm.short_form}
                    onChange={(e) => setRegionForm({...regionForm, short_form: e.target.value})}
                    aria-label="Region short form"
                    data-testid="region-short-form-input"
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
                <label htmlFor="region-description" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Region Description
                </label>
                <textarea
                  id="region-description"
                  value={regionForm.description}
                  onChange={(e) => setRegionForm({...regionForm, description: e.target.value})}
                  rows="2"
                  aria-label="Region description"
                  data-testid="region-description-input"
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
                <label htmlFor="region-notes" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                  Region Notes
                </label>
                <textarea
                  id="region-notes"
                  value={regionForm.notes}
                  onChange={(e) => setRegionForm({...regionForm, notes: e.target.value})}
                  rows="2"
                  aria-label="Region notes"
                  data-testid="region-notes-input"
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
                  <label htmlFor="region-url" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                    Region URL
                  </label>
                  <input
                    id="region-url"
                    type="url"
                    value={regionForm.url}
                    onChange={(e) => setRegionForm({...regionForm, url: e.target.value})}
                    aria-label="Region URL"
                    data-testid="region-url-input"
                    style={{
                      width: '100%',
                      padding: '8px',
                      border: '1px solid #ddd',
                      borderRadius: '4px'
                    }}
                  />
                </div>
                
                <div>
                  <label htmlFor="region-image-url" style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
                    Image URL
                  </label>
                  <input
                    id="region-image-url"
                    type="url"
                    value={regionForm.image_url}
                    onChange={(e) => setRegionForm({...regionForm, image_url: e.target.value})}
                    aria-label="Region image URL"
                    data-testid="region-image-url-input"
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
                <label htmlFor="region-is-default" style={{ display: 'flex', alignItems: 'center', fontWeight: 'bold' }}>
                  <input
                    id="region-is-default"
                    type="checkbox"
                    checked={regionForm.is_default}
                    onChange={(e) => setRegionForm({...regionForm, is_default: e.target.checked})}
                    style={{ marginRight: '8px' }}
                  />
                  Set as Default
                </label>
              </div>
              
              <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
                <button
                  type="button"
                  onClick={handleRegionSubmit}
                  disabled={saving}
                  data-testid="save-region-button"
                  style={{
                    padding: '8px 16px',
                    background: 'none',
                    border: 'none',
                    cursor: saving ? 'not-allowed' : 'pointer',
                    opacity: saving ? 0.6 : 1,
                    fontSize: '14px'
                  }}
                  aria-label={saving ? 'Saving...' : (editingRegion ? 'Update Region' : 'Create Region')}
                >
                  {saving ? ICONS.LOADING : (editingRegion ? ICONS.SAVE : ICONS.CREATE)}
                </button>
                <button
                  type="button"
                  onClick={cancelRegionForm}
                  data-testid="cancel-region-button"
                  style={{
                    padding: '8px 16px',
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                  aria-label="Cancel"
                >
                  {ICONS.CANCEL}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Regions List */}
        {regions.length === 0 ? (
          <p data-testid="no-regions-message" style={{ 
            textAlign: 'center', 
            color: '#6c757d', 
            fontStyle: 'italic',
            padding: '20px'
          }}>
            No regions defined for {country.name}. Click "Add Region" to create one.
          </p>
        ) : (
          <div style={{ 
            border: '1px solid #ddd', 
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#f8f9fa' }}>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>
                    Name
                  </th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #ddd' }}>
                    Description
                  </th>
                  <th style={{ padding: '12px', textAlign: 'center', borderBottom: '1px solid #ddd' }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody data-testid="region-list">
                {regions.map((region) => (
                  <tr key={region.id} data-testid="region-item">
                    <td style={{ padding: '12px', borderBottom: '1px solid #eee' }}>
                      <strong>{region.name}</strong>
                    </td>
                    <td style={{ padding: '12px', borderBottom: '1px solid #eee' }}>
                      {region.description || <em style={{ color: '#6c757d' }}>No description</em>}
                    </td>
                    <td style={{ padding: '12px', borderBottom: '1px solid #eee', textAlign: 'center' }}>
                      <button
                        onClick={() => handleEditRegion(region)}
                        aria-label={`Edit region`}
                        data-testid="edit-region-button"
                        style={{
                          marginRight: '8px',
                          padding: '4px 8px',
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}
                      >
                        {ICONS.EDIT}
                      </button>
                      <button
                        onClick={() => handleDeleteRegion(region)}
                        aria-label={`Remove region`}
                        data-testid={`delete-${region.name.toLowerCase().replace(/\\s+/g, '-')}-btn`}
                        style={{
                          padding: '4px 8px',
                          background: 'none',
                          border: 'none',
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
          </div>
        )}
      </div>
    </div>
  );
}

export default CountryEdit;