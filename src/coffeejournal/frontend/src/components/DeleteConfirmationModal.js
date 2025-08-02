import React, { useState } from 'react';
import { apiFetch } from '../config';

function DeleteConfirmationModal({ 
  isOpen, 
  onClose, 
  item, 
  itemType, 
  apiEndpoint, 
  usageInfo, 
  onDeleteConfirmed,
  availableReplacements = []
}) {
  const [action, setAction] = useState('cancel');
  const [replacementId, setReplacementId] = useState('');
  const [processing, setProcessing] = useState(false);

  if (!isOpen || !item) return null;

  const getUsageDescription = () => {
    if (!usageInfo || !usageInfo.usage_type) return '';
    
    const usageType = usageInfo.usage_type;
    const count = usageInfo.usage_count;
    
    // Map usage types to user-friendly descriptions
    const typeDescriptions = {
      'products': count === 1 ? 'product' : 'products',
      'brew_sessions': count === 1 ? 'brew session' : 'brew sessions'
    };
    
    return typeDescriptions[usageType] || usageType.replace('_', ' ');
  };

  const handleConfirm = async () => {
    // If item is not in use and action is 'cancel' (default), treat it as delete
    if (action === 'cancel' && usageInfo && usageInfo.in_use) {
      onClose();
      return;
    }

    setProcessing(true);

    try {
      if (usageInfo.in_use && action !== 'force_delete') {
        // Update references first
        const updateAction = action === 'remove_references' ? 'remove' : 'replace';
        const response = await apiFetch(`/${apiEndpoint}/${item.id}/update_references`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            action: updateAction,
            replacement_id: replacementId || null
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to update references');
        }
      }

      // Now delete the item
      await onDeleteConfirmed();
      onClose();
    } catch (err) {
      console.error('Error in deletion process:', err);
      alert('Error: ' + err.message);
    } finally {
      setProcessing(false);
    }
  };

  const modalStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000
  };

  const contentStyle = {
    backgroundColor: 'white',
    padding: '30px',
    borderRadius: '8px',
    maxWidth: '500px',
    width: '90%',
    maxHeight: '80vh',
    overflow: 'auto'
  };

  return (
    <div style={modalStyle} onClick={(e) => e.target === e.currentTarget && onClose()} data-testid="delete-modal-overlay">
      <div style={contentStyle} data-testid="delete-modal-content">
        <h3>Delete {itemType}: "{item.name}"</h3>
        
        {usageInfo.in_use ? (
          <div>
            <p data-testid="usage-warning" style={{ color: '#d63384', fontWeight: 'bold' }}>
              ⚠️ This {itemType.toLowerCase()} is currently being used in {usageInfo.usage_count} {getUsageDescription()}.
            </p>
            <p>Choose how to proceed:</p>
            
            <div style={{ margin: '20px 0' }}>
              <label style={{ display: 'block', marginBottom: '10px' }}>
                <input
                  type="radio"
                  name="action"
                  value="cancel"
                  checked={action === 'cancel'}
                  onChange={(e) => setAction(e.target.value)}
                  style={{ marginRight: '8px' }}
                />
                Cancel deletion
              </label>
              
              <label style={{ display: 'block', marginBottom: '10px' }}>
                <input
                  type="radio"
                  name="action"
                  value="remove_references"
                  checked={action === 'remove_references'}
                  onChange={(e) => setAction(e.target.value)}
                  style={{ marginRight: '8px' }}
                />
                Remove all references and delete ({getUsageDescription()} will have empty {itemType.toLowerCase()})
              </label>
              
              {availableReplacements.length > 0 && (
                <div>
                  <label style={{ display: 'block', marginBottom: '10px' }}>
                    <input
                      type="radio"
                      name="action"
                      value="replace_references"
                      checked={action === 'replace_references'}
                      onChange={(e) => setAction(e.target.value)}
                      style={{ marginRight: '8px' }}
                    />
                    Replace with another {itemType.toLowerCase()} and delete
                  </label>
                  
                  {action === 'replace_references' && (
                    <select
                      value={replacementId}
                      onChange={(e) => setReplacementId(e.target.value)}
                      style={{ 
                        marginLeft: '24px', 
                        marginTop: '5px',
                        padding: '5px',
                        width: '100%',
                        maxWidth: '300px'
                      }}
                      required
                    >
                      <option value="">Select replacement...</option>
                      {availableReplacements
                        .filter(r => r.id !== item.id)
                        .map(replacement => (
                          <option key={replacement.id} value={replacement.id}>
                            {replacement.name}
                          </option>
                        ))
                      }
                    </select>
                  )}
                </div>
              )}
            </div>
          </div>
        ) : (
          <p>Are you sure you want to delete "{item.name}"? This action cannot be undone.</p>
        )}
        
        <div style={{ marginTop: '30px', textAlign: 'right' }}>
          <button
            onClick={onClose}
            disabled={processing}
            style={{
              marginRight: '10px',
              padding: '8px 16px',
              border: '1px solid #ccc',
              backgroundColor: '#f8f9fa',
              cursor: processing ? 'not-allowed' : 'pointer'
            }}
          >
            Cancel
          </button>
          
          <button
            onClick={handleConfirm}
            disabled={processing || (action === 'replace_references' && !replacementId) || (usageInfo && usageInfo.in_use && action === 'cancel')}
            style={{
              padding: '8px 16px',
              border: 'none',
              backgroundColor: (usageInfo && usageInfo.in_use && action === 'cancel') ? '#6c757d' : '#dc3545',
              color: 'white',
              cursor: (processing || (action === 'replace_references' && !replacementId) || (usageInfo && usageInfo.in_use && action === 'cancel')) ? 'not-allowed' : 'pointer'
            }}
          >
            {processing ? 'Processing...' : (
              usageInfo && usageInfo.in_use ? (
                action === 'remove_references' ? 'Remove References & Delete' :
                action === 'replace_references' ? 'Replace & Delete' :
                action === 'cancel' ? 'Choose an option above' :
                'Delete'
              ) : (
                'Delete'
              )
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default DeleteConfirmationModal;