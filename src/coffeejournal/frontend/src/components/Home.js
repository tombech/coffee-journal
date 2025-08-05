import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch } from '../config';
import { ICONS } from '../config/icons';
import BrewSessionTable from './BrewSessionTable';
import BrewSessionForm from './BrewSessionForm';
import StarRating from './StarRating';
import { useToast } from './Toast';

function Home() {
  const { addToast } = useToast();
  const [sessions, setSessions] = useState([]);
  const [products, setProducts] = useState([]);
  const [topBrewSessions, setTopBrewSessions] = useState([]);
  const [bottomBrewSessions, setBottomBrewSessions] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [editingSession, setEditingSession] = useState(null);
  const [filterOptions, setFilterOptions] = useState(null);

  // Roast degree visualization using custom PNG images with half-filled beans
  const getRoastVisualization = (roastType) => {
    if (!roastType) {
      // Default - all white/light beans
      return (
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
          {[...Array(5)].map((_, i) => (
            <img 
              key={i}
              src="/coffee-bean-white.png" 
              alt="Light roast bean" 
              style={{ width: '16px', height: '16px' }}
            />
          ))}
        </span>
      );
    }
    
    const normalizedValue = Math.max(1, Math.min(10, roastType)); // Clamp between 1-10
    const scaledValue = normalizedValue / 2; // Convert to 0.5-5.0 scale
    
    const beans = [];
    for (let i = 0; i < 5; i++) {
      const beanValue = scaledValue - i; // How much this bean should be filled
      
      if (beanValue >= 1) {
        // Full bean - completely brown
        beans.push(
          <img 
            key={i}
            src="/coffee-bean-brown.png" 
            alt="Dark roast bean" 
            style={{ width: '16px', height: '16px' }}
          />
        );
      } else if (beanValue > 0) {
        // Partial bean - brown overlaid on white with clip-path
        const fillPercentage = Math.round(beanValue * 100);
        beans.push(
          <div 
            key={i}
            style={{ 
              position: 'relative', 
              width: '16px', 
              height: '16px',
              display: 'inline-block'
            }}
          >
            {/* White base bean */}
            <img 
              src="/coffee-bean-white.png" 
              alt={`${fillPercentage}% roasted bean`}
              style={{ 
                width: '16px', 
                height: '16px',
                position: 'absolute',
                top: 0,
                left: 0
              }}
            />
            {/* Brown overlay clipped to percentage */}
            <img 
              src="/coffee-bean-brown.png" 
              alt=""
              style={{ 
                width: '16px', 
                height: '16px',
                position: 'absolute',
                top: 0,
                left: 0,
                clipPath: `inset(0 ${100 - fillPercentage}% 0 0)`
              }}
            />
          </div>
        );
      } else {
        // Empty bean - white only
        beans.push(
          <img 
            key={i}
            src="/coffee-bean-white.png" 
            alt="Light roast bean" 
            style={{ width: '16px', height: '16px' }}
          />
        );
      }
    }
    
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
        {beans}
      </span>
    );
  };

  const fetchBrewSessions = async () => {
    try {
      setLoading(true);
      
      // Fetch all data efficiently using dedicated APIs
      const [
        sessionsResponse, 
        productsResponse,
        topBrewsResponse,
        bottomBrewsResponse,
        topProductsResponse,
        filterOptionsResponse
      ] = await Promise.all([
        apiFetch('/brew_sessions?page_size=15'), // Recent 15 sessions
        apiFetch('/products'),
        apiFetch('/brew_sessions?page_size=5&sort=score&sort_direction=desc'), // Top 5 brews
        apiFetch('/brew_sessions?page_size=5&sort=score&sort_direction=asc'), // Bottom 5 brews  
        apiFetch('/stats/top-products?limit=5'), // Top 5 products
        apiFetch('/brew_sessions/filter_options') // Filter options for dropdowns
      ]);
      
      if (!sessionsResponse.ok || !productsResponse.ok || !topBrewsResponse.ok || 
          !bottomBrewsResponse.ok || !topProductsResponse.ok || !filterOptionsResponse.ok) {
        throw new Error('Failed to fetch data from one or more endpoints');
      }
      
      const [
        sessionsResult,
        productsData,
        topBrewsResult,
        bottomBrewsResult,
        topProductsData,
        filterOptionsData
      ] = await Promise.all([
        sessionsResponse.json(),
        productsResponse.json(),
        topBrewsResponse.json(),
        bottomBrewsResponse.json(),
        topProductsResponse.json(),
        filterOptionsResponse.json()
      ]);
      
      // Set all the state
      setSessions(sessionsResult.data || []);
      setProducts(productsData);
      setTopBrewSessions(topBrewsResult.data || []);
      setBottomBrewSessions(bottomBrewsResult.data || []);
      setTopProducts(topProductsData || []);
      setFilterOptions(filterOptionsData);
      
    } catch (err) {
      setError('Failed to fetch data: ' + err.message);
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBrewSessions();
  }, []);

  const handleDelete = async (sessionId) => {
    if (!window.confirm('Are you sure you want to delete this brew session?')) {
      return;
    }

    try {
      const response = await apiFetch(`/brew_sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      addToast('Brew session deleted successfully!', 'success');
      fetchBrewSessions(); // Refresh the list
    } catch (err) {
      addToast('Failed to delete brew session: ' + err.message, 'error');
      console.error('Error deleting brew session:', err);
    }
  };

  const handleDuplicate = async (sessionId) => {
    try {
      const response = await apiFetch(`/brew_sessions/${sessionId}/duplicate`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      addToast('Brew session duplicated successfully!', 'success');
      fetchBrewSessions(); // Refresh the list
    } catch (err) {
      addToast('Failed to duplicate brew session: ' + err.message, 'error');
      console.error('Error duplicating brew session:', err);
    }
  };

  const handleEdit = (session) => {
    setEditingSession(session);
    setShowNewForm(true);
  };

  const handleSessionSubmitted = () => {
    setShowNewForm(false);
    setEditingSession(null);
    fetchBrewSessions(); // Refresh the list
  };

  if (loading) return <p>Loading recent brew sessions...</p>;
  if (error) return <p className="error-message">{error}</p>;

  // Calculate comprehensive score for brew sessions (for recent sessions display)
  const calculateBrewScore = (session) => {
    // Use overall score if available
    if (session.score && session.score > 0) {
      return session.score;
    }
    
    // Otherwise calculate from tasting notes (bitterness is negative, others positive)
    const tastingNotes = [
      session.sweetness,
      session.acidity,
      session.body,
      session.aroma,
      session.flavor_profile_match
    ].filter(score => score && score > 0);
    
    // Bitterness is subtracted (inverted)
    const bitternessScore = session.bitterness ? (10 - session.bitterness) : 0;
    if (bitternessScore > 0) tastingNotes.push(bitternessScore);
    
    return tastingNotes.length > 0 ? tastingNotes.reduce((sum, score) => sum + score, 0) / tastingNotes.length : 0;
  };


  // Norwegian date formatting
  const formatDateNorwegian = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear().toString().slice(-2);
    return `${day}.${month}.${year}`;
  };

  // Format seconds to minutes:seconds
  const formatSecondsToMinSec = (seconds) => {
    if (!seconds) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes > 0) {
      return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    return `${seconds}s`;
  };


  // Mini radar chart component for products
  const MiniRadarChart = ({ data, size = 240 }) => {
    if (!data) return null;
    
    // Debug: Log radar chart data
    console.log('DEBUG Radar Chart data:', data);
    
    const center = size / 2;
    const maxRadius = 80;
    const angles = [0, 72, 144, 216, 288]; // 5 points, 72 degrees apart
    const labels = ['Sweetness', 'Acidity', 'Body', 'Aroma', 'Bitterness'];
    const values = [data.sweetness, data.acidity, data.body, data.aroma, data.bitterness];
    
    const getPoint = (angle, radius) => {
      const radians = (angle - 90) * Math.PI / 180;
      return {
        x: center + radius * Math.cos(radians),
        y: center + radius * Math.sin(radians)
      };
    };
    
    const dataPoints = values.map((value, index) => {
      const radius = (value / 10) * maxRadius;
      return getPoint(angles[index], radius);
    });
    
    const polygonPoints = dataPoints.map(point => `${point.x},${point.y}`).join(' ');
    
    // Generate labels
    const labelElements = labels.map((label, index) => {
      const point = getPoint(angles[index], maxRadius + 20);
      return (
        <text
          key={index}
          x={point.x}
          y={point.y}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="11"
          fill="#666"
        >
          {label}
        </text>
      );
    });
    
    return (
      <svg width={size + 40} height={size + 40} viewBox={`0 0 ${size + 40} ${size + 40}`}>
        <g transform="translate(20, 20)">
          <circle cx={center} cy={center} r={maxRadius} fill="none" stroke="#e0e0e0" strokeWidth="1" />
          <circle cx={center} cy={center} r={maxRadius * 0.5} fill="none" stroke="#e0e0e0" strokeWidth="0.5" />
          {angles.map((angle, index) => {
            const point = getPoint(angle, maxRadius);
            return (
              <line
                key={index}
                x1={center}
                y1={center}
                x2={point.x}
                y2={point.y}
                stroke="#e0e0e0"
                strokeWidth="0.5"
              />
            );
          })}
          <polygon
            points={polygonPoints}
            fill="rgba(54, 162, 235, 0.2)"
            stroke="rgba(54, 162, 235, 0.8)"
            strokeWidth="1"
          />
          {labelElements}
        </g>
      </svg>
    );
  };

  return (
    <div>
      <h2>Welcome to your Coffee Journal!</h2>
      
      {showNewForm && (
        <div style={{ marginBottom: '20px', padding: '15px', border: '1px solid #ddd', borderRadius: '5px' }}>
          <BrewSessionForm
            initialData={editingSession}
            onSessionSubmitted={handleSessionSubmitted}
          />
          <button 
            onClick={() => {
              setShowNewForm(false);
              setEditingSession(null);
            }}
            style={{ marginTop: '10px' }}
          >
            Cancel
          </button>
        </div>
      )}

      <h3>Recent Brew Sessions</h3>
      <p>Your 15 most recent brew sessions:</p>
      
      <BrewSessionTable
        sessions={sessions.map(session => ({
          ...session,
          calculatedScore: calculateBrewScore(session)
        }))}
        onDelete={handleDelete}
        onDuplicate={handleDuplicate}
        onEdit={handleEdit}
        onRefresh={fetchBrewSessions}
        showNewForm={showNewForm}
        setShowNewForm={setShowNewForm}
        setEditingSession={setEditingSession}
        filterOptions={filterOptions}
      />

      {/* Analytics Section */}
      {(topBrewSessions.length > 0 || bottomBrewSessions.length > 0 || topProducts.length > 0) && (
        <div style={{ marginTop: '40px' }}>
          {/* Top 5 Brews */}
          <BrewSessionTable 
            sessions={topBrewSessions} 
            title="🏆 Top 5 Brews (Global)"
            showProduct={true}
            showActions={false}
            showFilters={false}
            showAddButton={false}
            preserveOrder={true}
            initialSort="calculatedScore"
            initialSortDirection="desc"
            onDelete={() => {}}
            onDuplicate={() => {}}
            onEdit={() => {}}
          />

          {/* Bottom 5 Brews */}
          <BrewSessionTable 
            sessions={bottomBrewSessions} 
            title="💩 Bottom 5 Brews (Global)"
            showProduct={true}
            showActions={false}
            showFilters={false}
            showAddButton={false}
            preserveOrder={true}
            initialSort="calculatedScore"
            initialSortDirection="asc"
            onDelete={() => {}}
            onDuplicate={() => {}}
            onEdit={() => {}}
          />

          {/* Top 5 Products */}
          <div style={{ marginBottom: '30px' }}>
            <h3>🥇 Top 5 Products</h3>
            {topProducts.length > 0 ? (
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fill, 600px)', 
                gap: '20px',
                justifyContent: 'start',
                paddingTop: '20px'
              }}>
                {topProducts.map((item, index) => (
                  <Link 
                    key={item.product.id} 
                    to={`/products/${item.product.id}`}
                    style={{ textDecoration: 'none', color: 'inherit' }}
                  >
                    <div style={{ 
                      border: '2px solid #ddd',
                      borderRadius: '12px',
                      padding: '15px',
                      backgroundColor: '#f9f9f9',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                      display: 'flex',
                      flexDirection: 'row',
                      alignItems: 'stretch',
                      position: 'relative',
                      cursor: 'pointer',
                      transition: 'transform 0.2s ease, box-shadow 0.2s ease'
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                    }}>
                    {/* Rank Badge */}
                    <div style={{ 
                      position: 'absolute',
                      top: '-18px',
                      left: '20px',
                      padding: '8px 12px',
                      backgroundColor: '#2196f3',
                      color: 'white',
                      borderRadius: '20px',
                      fontSize: '14px',
                      fontWeight: 'bold',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                    }}>
                      #{index + 1}
                    </div>
                    
                    {/* Score Badge */}
                    <div style={{ 
                      position: 'absolute',
                      top: '-18px',
                      right: '20px',
                      padding: '8px 12px',
                      backgroundColor: '#4caf50',
                      color: 'white',
                      borderRadius: '20px',
                      fontSize: '14px',
                      fontWeight: 'bold',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                    }}>
                      {typeof item.avg_score === 'number' ? item.avg_score.toFixed(1) : '0.0'}
                    </div>

                    {/* Left side - Product Info */}
                    <div style={{ flex: '1', paddingRight: '15px' }}>
                      <div style={{ marginTop: '5px', marginBottom: '5px' }}>
                        <h4 style={{ margin: '0 0 8px 0', fontSize: '18px', fontWeight: 'bold' }}>
                          {item.product.product_name}
                        </h4>
                        <div style={{ fontSize: '14px', lineHeight: '1.4' }}>
                          <div style={{ marginBottom: '4px', color: '#666' }}>
                            <strong>{Array.isArray(item.product.bean_type) ? item.product.bean_type.map(bt => bt.name).join(', ') : 'Unknown'}</strong> • {item.product.country?.name || 'Unknown'}{Array.isArray(item.product.region) && item.product.region.length > 0 ? ` (${item.product.region.map(r => r.name).join(', ')})` : ''}
                          </div>
                          <div style={{ marginBottom: '4px', fontSize: '13px', color: '#777' }}>
                            {item.product.roaster?.name || 'Unknown Roaster'}
                          </div>
                          {item.product.roast_type && (
                            <div style={{ margin: '4px 0' }}>
                              {getRoastVisualization(item.product.roast_type)}
                            </div>
                          )}
                          {item.product.rating && (
                            <div style={{ margin: '4px 0' }}>
                              <StarRating rating={item.product.rating} readOnly={true} maxRating={5} />
                            </div>
                          )}
                          <div style={{ fontSize: '13px', color: '#777' }}>
                            {item.brew_count} brewing sessions
                          </div>
                        </div>
                        {item.product.description && (
                          <p style={{ 
                            margin: '8px 0 0 0', 
                            fontSize: '13px', 
                            lineHeight: '1.3',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            fontStyle: 'italic',
                            color: '#777'
                          }}>
                            {item.product.description}
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Right side - Radar Chart */}
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'center',
                      justifyContent: 'center',
                      padding: '0'
                    }}>
                      <MiniRadarChart data={item.tasting_averages} />
                    </div>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p style={{ color: '#666', fontStyle: 'italic' }}>No products with scored sessions yet</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default Home;