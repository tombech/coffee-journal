import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../config';

function FavoritesSection() {
  const [favorites, setFavorites] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchFavorites = async () => {
    try {
      setLoading(true);
      const response = await apiFetch('/stats/favorites');

      if (!response.ok) {
        throw new Error('Failed to fetch favorites');
      }

      const data = await response.json();
      setFavorites(data);
    } catch (err) {
      setError('Failed to fetch favorites: ' + err.message);
      console.error('Error fetching favorites:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFavorites();
  }, []);

  const getCategoryIcon = (type) => {
    const icons = {
      'roaster': '🏭',
      'bean_type': '☕',
      'country': '🌍',
      'region': '📍',
      'brew_method': '⚗️',
      'recipe': '📝',
      'bean_process': '🔄'
    };
    return icons[type] || '⭐';
  };

  const getCategoryTitle = (type) => {
    const titles = {
      'roaster': 'Roasters',
      'bean_type': 'Bean Types',
      'country': 'Countries',
      'region': 'Regions',
      'brew_method': 'Brew Methods',
      'recipe': 'Recipes',
      'bean_process': 'Bean Processes'
    };
    return titles[type] || type;
  };

  const getCategoryLink = (type, itemId) => {
    const links = {
      'roaster': `/roasters/${itemId}`,
      'bean_type': `/bean-types/${itemId}`,
      'country': `/countries/${itemId}`,
      'region': `/regions/${itemId}`,
      'brew_method': `/brew-methods/${itemId}`,
      'recipe': `/recipes/${itemId}`,
      'bean_process': null // No dedicated page for bean processes
    };
    return links[type];
  };

  if (loading) {
    return (
      <div style={{
        padding: '20px',
        textAlign: 'center',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        margin: '20px 0'
      }}>
        <p>Loading your favorites...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        padding: '20px',
        textAlign: 'center',
        backgroundColor: '#ffe6e6',
        borderRadius: '8px',
        margin: '20px 0',
        color: '#d63384'
      }}>
        <p>{error}</p>
      </div>
    );
  }

  // Check if we have any favorites
  const hasFavorites = Object.values(favorites).some(items => items && items.length > 0);

  if (!hasFavorites) {
    return (
      <div style={{
        padding: '20px',
        textAlign: 'center',
        backgroundColor: '#f8f9fa',
        borderRadius: '8px',
        margin: '20px 0'
      }}>
        <h3>🌟 Your Favorites</h3>
        <p style={{ color: '#666', fontStyle: 'italic' }}>
          Start brewing and rating your sessions to discover your favorites!
        </p>
      </div>
    );
  }

  return (
    <div style={{ margin: '40px 0' }}>
      <h3 style={{
        marginBottom: '20px',
        color: '#2c3e50',
        textAlign: 'left',
        fontSize: '24px',
        fontWeight: 'bold'
      }}>
        🌟 Your Favorites
      </h3>
      <p style={{
        textAlign: 'left',
        color: '#666',
        marginBottom: '30px',
        fontSize: '16px'
      }}>
        Top-rated items across your brewing journey (minimum 3 uses)
      </p>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '20px'
      }}>
        {Object.entries(favorites).map(([type, items]) => {
          if (!items || items.length === 0) return null;

          return (
            <div key={type} style={{
              backgroundColor: '#ffffff',
              border: '2px solid #e3f2fd',
              borderRadius: '12px',
              padding: '20px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
              transition: 'transform 0.2s ease, box-shadow 0.2s ease'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)';
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'translateY(0)';
              e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
            }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: '15px',
                paddingBottom: '10px',
                borderBottom: '2px solid #e3f2fd'
              }}>
                <span style={{ fontSize: '24px', marginRight: '10px' }}>
                  {getCategoryIcon(type)}
                </span>
                <h4 style={{
                  margin: 0,
                  color: '#1976d2',
                  fontSize: '18px',
                  fontWeight: 'bold'
                }}>
                  {getCategoryTitle(type)}
                </h4>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {items.map((item, index) => {
                  const link = getCategoryLink(type, item.item.id);
                  const content = (
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '12px',
                      backgroundColor: index === 0 ? '#fff3e0' : '#f8f9fa',
                      borderRadius: '8px',
                      border: index === 0 ? '2px solid #ff9800' : '1px solid #e0e0e0',
                      position: 'relative',
                      cursor: link ? 'pointer' : 'default',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseOver={(e) => {
                      if (link) {
                        e.currentTarget.style.backgroundColor = index === 0 ? '#ffe0b2' : '#e3f2fd';
                        e.currentTarget.style.transform = 'translateX(4px)';
                      }
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.backgroundColor = index === 0 ? '#fff3e0' : '#f8f9fa';
                      e.currentTarget.style.transform = 'translateX(0)';
                    }}>
                      {index === 0 && (
                        <div style={{
                          position: 'absolute',
                          top: '-8px',
                          left: '8px',
                          backgroundColor: '#ff9800',
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: '10px',
                          fontSize: '10px',
                          fontWeight: 'bold'
                        }}>
                          #1
                        </div>
                      )}

                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontWeight: index === 0 ? 'bold' : 'normal',
                          fontSize: index === 0 ? '15px' : '14px',
                          color: '#2c3e50',
                          marginBottom: '4px'
                        }}>
                          {item.item.name}
                        </div>
                        <div style={{
                          fontSize: '12px',
                          color: '#666',
                          display: 'flex',
                          gap: '12px'
                        }}>
                          <span>{item.total_uses} uses</span>
                          <span>•</span>
                          <span>{item.score_count} scores</span>
                        </div>
                      </div>

                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        <div style={{
                          backgroundColor: '#4caf50',
                          color: 'white',
                          padding: '4px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          fontWeight: 'bold',
                          minWidth: '35px',
                          textAlign: 'center'
                        }}>
                          {item.avg_score}
                        </div>
                        <span style={{ fontSize: '16px' }}>⭐</span>
                      </div>
                    </div>
                  );

                  return link ? (
                    <Link
                      key={`${type}-${item.item.id}`}
                      to={link}
                      style={{ textDecoration: 'none', color: 'inherit' }}
                    >
                      {content}
                    </Link>
                  ) : (
                    <div key={`${type}-${item.item.name}`}>
                      {content}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default FavoritesSection;