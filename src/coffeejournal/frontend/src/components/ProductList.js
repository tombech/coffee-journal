import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useToast } from './Toast';
import { API_BASE_URL, apiFetch } from '../config';
import { ICONS } from '../config/icons';
import StarRating from './StarRating';

function ProductList() {
  const { addToast } = useToast();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch products and their statistics in parallel
      const [productsResponse, statsResponse] = await Promise.all([
        apiFetch('/products'),
        apiFetch('/stats/top-products?limit=1000') // Get stats for all products
      ]);
      
      if (!productsResponse.ok) {
        throw new Error(`HTTP error! status: ${productsResponse.status}`);
      }
      
      const productsData = await productsResponse.json();
      
      // If stats API is available, merge the statistics
      let enrichedProducts = productsData;
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        const statsMap = new Map(statsData.map(item => [item.product.id, item]));
        
        enrichedProducts = productsData.map(product => ({
          ...product,
          average_score: statsMap.get(product.id)?.avg_score,
          brew_count: statsMap.get(product.id)?.brew_count || 0
        }));
      }
      
      setProducts(enrichedProducts);
    } catch (err) {
      setError("Failed to fetch products: " + err.message);
      console.error("Error fetching products:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm("Are you sure you want to delete this coffee product and all its associated batches and brew sessions?")) {
      try {
        const response = await apiFetch(`/products/${id}`, {
          method: 'DELETE',
        });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        setProducts(products.filter(product => product.id !== id)); // Remove from UI
        addToast("Product deleted successfully!", 'success');
      } catch (err) {
        setError("Failed to delete product: " + err.message);
        console.error("Error deleting product:", err);
      }
    }
  };

  // Group products by roaster
  const groupedProducts = useMemo(() => {
    const groups = {};
    products.forEach(product => {
      const roasterName = product.roaster?.name || 'Unknown Roaster';
      if (!groups[roasterName]) {
        groups[roasterName] = [];
      }
      groups[roasterName].push(product);
    });
    return groups;
  }, [products]);

  if (loading) return <p className="loading-message">Loading products...</p>;
  if (error) return <p className="error-message">{error}</p>;

  return (
    <div>
      <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <h2 style={{ margin: 0, marginRight: 'auto' }}>Products</h2>
        <Link 
          to="/products/new" 
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            textDecoration: 'none'
          }}
          title="New Product"
          aria-label="Add New Product"
          data-testid="add-new-product-btn"
        >
{ICONS.CREATE}
        </Link>
        <Link 
          to="/settings" 
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            textDecoration: 'none'
          }}
          title="Back to Settings"
          aria-label="Back to Settings"
        >
{ICONS.BACK}
        </Link>
      </div>

      {products.length === 0 ? (
        <p>No coffee products registered yet.</p>
      ) : (
        Object.entries(groupedProducts).map(([roaster, roasterProducts]) => (
          <div key={roaster} style={{ marginBottom: '25px' }}>
            <h3 style={{ 
              margin: '0 0 10px 0', 
              color: '#6d4c41', 
              borderBottom: '2px solid #6d4c41', 
              paddingBottom: '5px',
              fontSize: '1.2rem'
            }}>
              {roaster} ({roasterProducts.length})
            </h3>
            <div className="list-container" style={{ paddingTop: '20px' }}>
              {roasterProducts.map(product => (
                <Link 
                  key={product.id}
                  to={`/products/${product.id}`}
                  style={{ textDecoration: 'none', color: 'inherit' }}
                  aria-label={`View ${product.product_name} details`}
                  data-testid={`product-card-link-${product.id}`}
                >
                  <div className="product-card" style={{ 
                    cursor: 'pointer',
                    transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                    position: 'relative'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '3px 7px 16px rgba(0, 0, 0, 0.3)';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '3px 5px 12px rgba(0, 0, 0, 0.2)';
                  }}>
                    {product.image_url && (
                      <img 
                        src={product.image_url} 
                        alt={Array.isArray(product.bean_type) ? product.bean_type.map(bt => bt.name).join(', ') : 'Coffee'} 
                        className="product-image"
                      />
                    )}
                    {/* External link icon in upper right corner */}
                    {product.url && (
                      <a 
                        href={product.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        style={{
                          position: 'absolute',
                          top: '12px',
                          right: '12px',
                          fontSize: '16px',
                          color: '#666',
                          textDecoration: 'none',
                          padding: '4px',
                          borderRadius: '3px',
                          backgroundColor: 'rgba(255, 255, 255, 0.9)',
                          transition: 'all 0.2s ease',
                          zIndex: 2
                        }}
                        onClick={(e) => e.stopPropagation()}
                        onMouseOver={(e) => {
                          e.currentTarget.style.color = '#333';
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 1)';
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.color = '#666';
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
                        }}
                        title="View product page (opens in new window)"
                        aria-label={`View ${product.product_name} product page`}
                      >
                        🔗
                      </a>
                    )}
                    
                    {/* Green score badge - floating like Home page */}
                    {product.average_score && (
                      <div style={{ 
                        position: 'absolute',
                        top: '-18px',
                        right: product.url ? '60px' : '20px', // Offset if external link present
                        padding: '8px 12px',
                        backgroundColor: '#4caf50',
                        color: 'white',
                        borderRadius: '20px',
                        fontSize: '14px',
                        fontWeight: 'bold',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                        zIndex: 1
                      }}>
                        {typeof product.average_score === 'number' ? product.average_score.toFixed(1) : product.average_score}
                      </div>
                    )}
                    <div className="product-content">
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                        <h4 style={{ margin: '0', color: '#333', flex: 1, fontSize: '18px', fontWeight: 'bold' }}>
                          {product.product_name}
                        </h4>
                        {product.decaf && (
                          <span style={{ 
                            backgroundColor: '#e3f2fd', 
                            color: '#1976d2', 
                            padding: '2px 6px', 
                            borderRadius: '3px', 
                            fontSize: '11px', 
                            fontWeight: 'bold',
                            marginLeft: '8px'
                          }}>
                            DECAF
                          </span>
                        )}
                      </div>
                      <p style={{ margin: '0 0 6px 0', fontSize: '14px', color: '#666' }}>
                        <strong>{Array.isArray(product.bean_type) ? product.bean_type.map(bt => bt.name).join(', ') : 'Unknown'}</strong> • {product.country?.name || 'Unknown'}{Array.isArray(product.region) && product.region.length > 0 ? ` (${product.region.map(r => r.name).join(', ')})` : ''}
                      </p>
                      {product.roast_type && (
                        <div style={{ margin: '0 0 8px 0' }}>
                          {getRoastVisualization(product.roast_type)}
                        </div>
                      )}
                      {product.rating && (
                        <div style={{ margin: '0 0 8px 0' }}>
                          <StarRating rating={product.rating} readOnly={true} maxRating={5} />
                        </div>
                      )}
                      {product.brew_count && (
                        <div style={{ fontSize: '13px', color: '#777', margin: '4px 0' }}>
                          {product.brew_count} brewing sessions
                        </div>
                      )}
                      {product.description && (
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
                          {product.description}
                        </p>
                      )}
                      <div className="actions" style={{ marginTop: '8px' }}>
                        <Link 
                          to={`/products/edit/${product.id}`} 
                          style={{ 
                            padding: '4px 6px', 
                            border: 'none', 
                            background: 'none', 
                            cursor: 'pointer', 
                            fontSize: '14px',
                            textDecoration: 'none',
                            marginRight: '5px'
                          }}
                          title="Edit"
                          aria-label={`Edit ${product.product_name}`}
                          onClick={(e) => e.stopPropagation()}
                        >
{ICONS.EDIT}
                        </Link>
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(product.id);
                          }}
                          style={{ 
                            padding: '4px 6px', 
                            border: 'none', 
                            background: 'none', 
                            cursor: 'pointer', 
                            fontSize: '14px'
                          }}
                          title="Delete"
                          aria-label={`Delete ${product.product_name}`}
                        >
{ICONS.DELETE}
                        </button>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export default ProductList;