import React, { useState, useEffect } from 'react';
import { ICONS } from '../config/icons';
import BrewSessionTable from './BrewSessionTable';
import { apiFetch } from '../config';

function UsageStatistics({ 
  usageData, 
  statsData, 
  itemName, 
  customStatistics = null,
  showProduct = false,
  // New props for filtering
  filterType = null,  // 'roaster', 'bean_type', 'country', etc.
  filterId = null     // The ID to filter by
}) {
  const [topSessions, setTopSessions] = useState([]);
  const [bottomSessions, setBottomSessions] = useState([]);
  const [recentSessions, setRecentSessions] = useState([]);
  
  // Fetch top/bottom sessions using the enhanced brew_sessions API
  useEffect(() => {
    const fetchBrewSessions = async () => {
      if (!filterType || !filterId) {
        // No filtering - use existing statsData if available
        return;
      }
      
      try {
        // Construct filter parameter based on type
        const filterParam = `${filterType}=${filterId}`;
        
        const [topResponse, bottomResponse, recentResponse] = await Promise.all([
          apiFetch(`/brew_sessions?${filterParam}&page_size=5&sort=score&sort_direction=desc`),
          apiFetch(`/brew_sessions?${filterParam}&page_size=5&sort=score&sort_direction=asc`),
          apiFetch(`/brew_sessions?${filterParam}&page_size=5&sort=timestamp&sort_direction=desc`)
        ]);
        
        if (topResponse.ok && bottomResponse.ok && recentResponse.ok) {
          const topResult = await topResponse.json();
          const bottomResult = await bottomResponse.json();
          const recentResult = await recentResponse.json();
          setTopSessions(topResult.data || []);
          setBottomSessions(bottomResult.data || []);
          setRecentSessions(recentResult.data || []);
        }
      } catch (err) {
        console.error('Error fetching brew sessions:', err);
      }
    };
    
    fetchBrewSessions();
  }, [filterType, filterId]);
  
  // Determine which sessions to show - API fetched or statsData
  const displayTopSessions = filterType && filterId ? topSessions : (statsData?.top_5_sessions || []);
  const displayBottomSessions = filterType && filterId ? bottomSessions : (statsData?.bottom_5_sessions || []);
  const displayRecentSessions = filterType && filterId ? recentSessions : (statsData?.recent_5_sessions || []);
  
  if (!usageData && !statsData && !filterType) return null;

  return (
    <div style={{ 
      marginBottom: '30px',
      padding: '20px', 
      backgroundColor: 'white',
      borderRadius: '12px',
      border: '1px solid #e0e0e0',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
    }}>
      <h3 style={{ margin: '0 0 20px 0', color: '#333', fontSize: '18px', fontWeight: 'bold' }}>
        📊 Usage Statistics
      </h3>
      
      {/* Custom Statistics Grid (for complex stats like grinder) */}
      {customStatistics && (
        <div style={{ marginBottom: '20px' }}>
          {customStatistics}
        </div>
      )}
      
      {/* Simple Usage Data (for lookup items) */}
      {usageData && !customStatistics && (
        <div style={{ marginBottom: '20px' }}>
          {usageData.usage_count > 0 ? (
            <div>
              <div style={{ textAlign: 'center', marginBottom: '15px' }}>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#2e7d32' }}>{usageData.usage_count}</div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  Times Used in {usageData.usage_type === 'products' ? 'Products' : 
                                 usageData.usage_type === 'brew_sessions' ? 'Brew Sessions' : 
                                 usageData.usage_type ? usageData.usage_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 
                                 'Records'}
                </div>
              </div>
              
              {usageData.recent_usage && usageData.recent_usage.length > 0 && (
                <div>
                  <h4 style={{ margin: '15px 0 10px 0', fontSize: '14px' }}>Recent Usage:</h4>
                  <div style={{ fontSize: '12px' }}>
                    {usageData.recent_usage.slice(0, 5).map((usage, index) => (
                      <div key={index} style={{ marginBottom: '5px', color: '#666' }}>
                        • {new Date(usage.timestamp).toLocaleDateString()} - {usage.product_name || 'Unknown Product'}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p style={{ color: '#666', fontStyle: 'italic' }}>
              This {itemName?.toLowerCase()} has not been used in any {
                usageData?.usage_type === 'products' ? 'products' : 
                usageData?.usage_type === 'brew_sessions' ? 'brew sessions' : 
                usageData?.usage_type ? usageData.usage_type.replace('_', ' ') : 
                'records'
              } yet.
            </p>
          )}
        </div>
      )}
      
      {/* Top 5 Brew Sessions */}
      {displayTopSessions.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#2e7d32', fontSize: '16px' }}>🏆 Top 5 Brew Sessions</h4>
          <BrewSessionTable 
            sessions={displayTopSessions} 
            title=""
            showProduct={showProduct}
            showActions={false}
            showFilters={false}
            showAddButton={false}
            preserveOrder={true}
            onDelete={() => {}}
            onDuplicate={() => {}}
            onEdit={() => {}}
          />
        </div>
      )}
      
      {/* Bottom 5 Brew Sessions */}
      {displayBottomSessions.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#f44336', fontSize: '16px' }}>📉 Bottom 5 Brew Sessions</h4>
          <BrewSessionTable 
            sessions={displayBottomSessions} 
            title=""
            showProduct={showProduct}
            showActions={false}
            showFilters={false}
            showAddButton={false}
            preserveOrder={true}
            onDelete={() => {}}
            onDuplicate={() => {}}
            onEdit={() => {}}
          />
        </div>
      )}
      
      {/* Last 5 Brew Sessions (Most Recent) */}
      {displayRecentSessions.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#1976d2', fontSize: '16px' }}>🕐 Last 5 Brew Sessions</h4>
          <BrewSessionTable 
            sessions={displayRecentSessions} 
            title=""
            showProduct={showProduct}
            showActions={false}
            showFilters={false}
            showAddButton={false}
            preserveOrder={true}
            onDelete={() => {}}
            onDuplicate={() => {}}
            onEdit={() => {}}
          />
        </div>
      )}
    </div>
  );
}

export default UsageStatistics;