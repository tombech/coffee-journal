import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useToast } from './Toast';
import { apiFetch } from '../config';
import StarRating from './StarRating';
import { ICONS } from '../config/icons';

function BrewSessionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [session, setSession] = useState(null);
  const [batch, setBatch] = useState(null);
  const [product, setProduct] = useState(null);
  const [extractionDetails, setExtractionDetails] = useState(null);
  const [ratings, setRatings] = useState(null);
  const [relatedSessions, setRelatedSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBrewSessionDetail();
  }, [id]);

  const fetchBrewSessionDetail = async () => {
    setLoading(true);
    try {
      const response = await apiFetch(`/brew_sessions/${id}/detail`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSession(data.session);
      setBatch(data.batch);
      setProduct(data.product);
      setExtractionDetails(data.extraction_details);
      setRatings(data.ratings);
      setRelatedSessions(data.related_sessions || []);
    } catch (err) {
      setError("Failed to fetch brew session details: " + err.message);
      console.error("Error fetching brew session details:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatDateNorwegian = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear().toString().slice(-2);
    return `${day}.${month}.${year}`;
  };

  const formatTime = (totalSeconds) => {
    if (totalSeconds === null || totalSeconds === undefined || isNaN(totalSeconds)) return 'N/A';
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    if (hours > 0) {
      return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }
    return `${minutes}:${String(seconds).padStart(2, '0')}`;
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('nb-NO');
  };

  const handleDelete = async () => {
    if (!window.confirm('Are you sure you want to delete this brew session?')) {
      return;
    }
    
    try {
      const response = await apiFetch(`/brew_sessions/${id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      addToast('Brew session deleted successfully', 'success');
      navigate(batch ? `/batches/${batch.id}` : '/brew-sessions');
    } catch (err) {
      setError("Failed to delete brew session: " + err.message);
    }
  };

  if (loading) return <p className="loading-message">Loading brew session details...</p>;
  if (error) return <p className="error-message">{error}</p>;
  if (!session) return <p>Brew session not found.</p>;

  return (
    <div>
      <div style={{ marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <h2 style={{ margin: 0, marginRight: 'auto' }}>
          Brew Session - {formatDateTime(session.timestamp)}
        </h2>
        <Link 
          to={`/brew-sessions`}
          style={{ 
            padding: '6px 8px', 
            border: 'none', 
            background: 'none', 
            cursor: 'pointer', 
            fontSize: '16px',
            textDecoration: 'none',
            marginRight: '5px'
          }}
          title="All Brew Sessions"
          aria-label="All Brew Sessions"
        >
          📋
        </Link>
        <button
          onClick={() => navigate(`/brew-sessions/${id}/edit`)}
          title="Edit brew session"
          aria-label="Edit brew session"
          style={{
            padding: '6px 8px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '16px',
            marginRight: '5px'
          }}
        >
          {ICONS.EDIT}
        </button>
        <button
          onClick={handleDelete}
          title="Delete brew session"
          aria-label="Delete brew session"
          style={{
            padding: '6px 8px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: '16px',
            marginRight: '5px'
          }}
        >
          {ICONS.DELETE}
        </button>
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

      {/* Product and Batch Links */}
      <div style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
        {product && (
          <div style={{ padding: '10px', backgroundColor: '#e3f2fd', borderRadius: '8px', flex: 1 }}>
            <strong>Product: </strong>
            <Link to={`/products/${product.id}`} style={{ textDecoration: 'none', fontWeight: 'bold' }}>
              {product.roaster?.name} - {product.product_name}
            </Link>
          </div>
        )}
        {batch && (
          <div style={{ padding: '10px', backgroundColor: '#f3e5f5', borderRadius: '8px', flex: 1 }}>
            <strong>Batch: </strong>
            <Link to={`/batches/${batch.id}`} style={{ textDecoration: 'none', fontWeight: 'bold' }}>
              #{batch.id} (Roasted: {formatDateNorwegian(batch.roast_date)})
            </Link>
          </div>
        )}
      </div>

      {/* Brew Details */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
        <h3 style={{ margin: '0 0 15px 0' }}>☕ Brew Parameters</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 15px', alignItems: 'start' }}>
          <strong>Brew Method:</strong>
          <span>{session.brew_method?.name || 'N/A'}</span>
          
          <strong>Recipe:</strong>
          <span>{session.recipe?.name || 'N/A'}</span>
          
          <strong>Coffee Grams:</strong>
          <span>{session.amount_coffee_grams || 'N/A'}g</span>
          
          <strong>Water Grams:</strong>
          <span>{session.amount_water_grams || 'N/A'}g</span>
          
          {extractionDetails?.brew_ratio && (
            <>
              <strong>Brew Ratio:</strong>
              <span>{extractionDetails.brew_ratio}</span>
            </>
          )}
          
          <strong>Temperature:</strong>
          <span>
            {session.brew_temperature_c || 'N/A'}°C
            {extractionDetails?.water_temp_fahrenheit && ` (${extractionDetails.water_temp_fahrenheit}°F)`}
          </span>
          
          <strong>Bloom Time:</strong>
          <span>{formatTime(session.bloom_time_seconds)}</span>
          
          <strong>Brew Time:</strong>
          <span>{formatTime(session.brew_time_seconds)}</span>
        </div>
      </div>

      {/* Equipment */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#fff3e0', borderRadius: '8px' }}>
        <h3 style={{ margin: '0 0 15px 0' }}>⚙️ Equipment</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '8px 15px', alignItems: 'start' }}>
          <strong>Grinder:</strong>
          <span>
            {session.grinder?.name || 'N/A'}
            {session.grinder && (
              <Link 
                to={`/grinders/${session.grinder.id}`} 
                style={{ marginLeft: '8px', textDecoration: 'none', fontSize: '12px' }}
              >
                🔗
              </Link>
            )}
          </span>
          
          {session.grinder_setting && (
            <>
              <strong>Grinder Setting:</strong>
              <span>{session.grinder_setting}</span>
            </>
          )}
          
          <strong>Filter:</strong>
          <span>{session.filter?.name || 'N/A'}</span>
          
          <strong>Kettle:</strong>
          <span>{session.kettle?.name || 'N/A'}</span>
          
          <strong>Scale:</strong>
          <span>{session.scale?.name || 'N/A'}</span>
        </div>
      </div>

      {/* Overall Score */}
      {session && (session.score || session.sweetness || session.acidity || session.body || session.aroma || session.flavor_profile_match) && (
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#fff3cd', borderRadius: '8px', textAlign: 'center' }}>
          <h3 style={{ margin: '0 0 10px 0' }}>📊 Overall Score</h3>
          <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#856404' }}>
            {(() => {
              // Use manual score if available, otherwise calculate from tasting notes
              if (session.score && session.score > 0) {
                return session.score.toFixed(1);
              }
              
              // Use same calculation logic as BrewSessionTable
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
              
              const calculatedScore = tastingNotes.length > 0 ? tastingNotes.reduce((sum, score) => sum + score, 0) / tastingNotes.length : 0;
              return calculatedScore > 0 ? calculatedScore.toFixed(1) : '-';
            })()}/10
          </div>
        </div>
      )}

      {/* Ratings */}
      {ratings && ratings.has_ratings && (
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#e8f5e8', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 15px 0' }}>⭐ Tasting Notes</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '15px' }}>
            {ratings.overall && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>Overall Score</div>
                <StarRating rating={ratings.overall} readOnly={true} maxRating={10} />
              </div>
            )}
            {ratings.aroma && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>Aroma</div>
                <StarRating rating={ratings.aroma} readOnly={true} maxRating={10} />
              </div>
            )}
            {ratings.acidity && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>Acidity</div>
                <StarRating rating={ratings.acidity} readOnly={true} maxRating={10} />
              </div>
            )}
            {ratings.body && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>Body</div>
                <StarRating rating={ratings.body} readOnly={true} maxRating={10} />
              </div>
            )}
            {ratings.flavor && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>Flavor</div>
                <StarRating rating={ratings.flavor} readOnly={true} maxRating={10} />
              </div>
            )}
            {ratings.aftertaste && (
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '5px' }}>Aftertaste</div>
                <StarRating rating={ratings.aftertaste} readOnly={true} maxRating={10} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Notes */}
      {session.notes && (
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#fff8e1', borderRadius: '8px' }}>
          <h3 style={{ margin: '0 0 15px 0' }}>📝 Notes</h3>
          <p style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{session.notes}</p>
        </div>
      )}

      {/* Related Sessions */}
      {relatedSessions.length > 0 && (
        <div style={{ marginBottom: '30px' }}>
          <h3>🔗 Other Sessions from Same Batch</h3>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ borderCollapse: 'collapse', fontSize: '12px', whiteSpace: 'nowrap', width: '100%' }}>
              <thead>
                <tr style={{ backgroundColor: '#e9ecef' }}>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Date</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Method</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Coffee</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Water</th>
                  <th style={{ padding: '8px', border: '1px solid #ddd', textAlign: 'left' }}>Rating</th>
                </tr>
              </thead>
              <tbody>
                {relatedSessions.map(relatedSession => (
                  <tr key={relatedSession.id}>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                      <Link to={`/brew-sessions/${relatedSession.id}`} style={{ textDecoration: 'none' }}>
                        {formatDateNorwegian(relatedSession.timestamp)}
                      </Link>
                    </td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{relatedSession.brew_method?.name || '-'}</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{relatedSession.amount_coffee_grams || '-'}g</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>{relatedSession.amount_water_grams || '-'}g</td>
                    <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                      {relatedSession.score ? relatedSession.score.toFixed(1) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default BrewSessionDetail;