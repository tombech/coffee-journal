import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Dot } from 'recharts';
import { apiFetch } from '../config';

function ScoresOverTimeChart({ grinderId }) {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [grinderName, setGrinderName] = useState('');

  useEffect(() => {
    fetchScoresData();
  }, [grinderId]);

  const fetchScoresData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch(`/grinders/${grinderId}/scores-over-time`);

      if (!response.ok) {
        throw new Error(`Failed to fetch scores data: ${response.status}`);
      }

      const data = await response.json();
      setGrinderName(data.grinder_name);

      // Process data for the chart - calculate rolling average
      const processedData = [];
      const windowSize = 3; // Rolling average window

      data.data.forEach((point, index) => {
        // Calculate rolling average
        let avgScore = point.score;
        if (data.data.length >= windowSize) {
          const start = Math.max(0, index - Math.floor(windowSize / 2));
          const end = Math.min(data.data.length, index + Math.floor(windowSize / 2) + 1);
          const window = data.data.slice(start, end);
          avgScore = window.reduce((sum, p) => sum + p.score, 0) / window.length;
        }

        processedData.push({
          date: point.date,
          score: point.score,
          averageScore: parseFloat(avgScore.toFixed(2)),
          product: point.product_name,
          method: point.brew_method,
          index: index + 1,
          // Format date for display
          dateDisplay: new Date(point.date).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
          })
        });
      });

      setChartData(processedData);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching scores data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={{ padding: '20px', textAlign: 'center' }}>Loading chart data...</div>;
  if (error) return <div style={{ padding: '20px', color: '#d32f2f' }}>Error loading chart: {error}</div>;
  if (chartData.length === 0) return <div style={{ padding: '20px', textAlign: 'center' }}>No scored brew sessions found for this grinder.</div>;

  // Custom tooltip to show more information
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload[0]) {
      const data = payload[0].payload;
      return (
        <div style={{
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          padding: '10px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>
            {new Date(data.date).toLocaleDateString('en-US', {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
              year: 'numeric'
            })}
          </p>
          <p style={{ margin: '2px 0', color: '#2e7d32' }}>Score: {data.score}</p>
          <p style={{ margin: '2px 0', color: '#1976d2' }}>Avg: {data.averageScore}</p>
          <p style={{ margin: '2px 0', fontSize: '0.9em' }}>{data.product}</p>
          <p style={{ margin: '2px 0', fontSize: '0.9em' }}>{data.method}</p>
        </div>
      );
    }
    return null;
  };

  // Custom dot to highlight specific scores
  const CustomDot = (props) => {
    const { cx, cy, payload } = props;
    // Highlight perfect scores
    if (payload.score === 10) {
      return (
        <Dot
          cx={cx}
          cy={cy}
          r={6}
          fill="#4caf50"
          stroke="#2e7d32"
          strokeWidth={2}
        />
      );
    }
    // Highlight low scores
    if (payload.score <= 5) {
      return (
        <Dot
          cx={cx}
          cy={cy}
          r={5}
          fill="#f44336"
          stroke="#d32f2f"
          strokeWidth={1}
        />
      );
    }
    // Default dot
    return (
      <Dot
        cx={cx}
        cy={cy}
        r={4}
        fill="#1976d2"
      />
    );
  };

  return (
    <div style={{
      marginTop: '30px',
      padding: '20px',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
    }}>
      <h3 style={{ marginBottom: '20px', color: '#333' }}>
        Brew Session Scores Over Time
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
          <XAxis
            dataKey="dateDisplay"
            label={{ value: 'Date', position: 'insideBottom', offset: -5 }}
            tick={{ fontSize: 11, angle: -45 }}
            height={60}
            interval={chartData.length > 10 ? Math.floor(chartData.length / 8) : 0}
          />
          <YAxis
            domain={[0, 10]}
            ticks={[0, 2, 4, 6, 8, 10]}
            label={{ value: 'Score', angle: -90, position: 'insideLeft' }}
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          {/* Individual scores */}
          <Line
            type="monotone"
            dataKey="score"
            stroke="#1976d2"
            strokeWidth={1}
            dot={<CustomDot />}
            name="Session Score"
            connectNulls
          />

          {/* Rolling average line */}
          <Line
            type="monotone"
            dataKey="averageScore"
            stroke="#ff9800"
            strokeWidth={2}
            dot={false}
            name="3-Session Average"
            strokeDasharray="5 5"
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>

      <div style={{
        marginTop: '15px',
        display: 'flex',
        gap: '20px',
        fontSize: '12px',
        color: '#666',
        justifyContent: 'center'
      }}>
        <span>
          <span style={{
            display: 'inline-block',
            width: '12px',
            height: '12px',
            backgroundColor: '#4caf50',
            borderRadius: '50%',
            marginRight: '5px'
          }}></span>
          Perfect (10)
        </span>
        <span>
          <span style={{
            display: 'inline-block',
            width: '12px',
            height: '12px',
            backgroundColor: '#1976d2',
            borderRadius: '50%',
            marginRight: '5px'
          }}></span>
          Normal
        </span>
        <span>
          <span style={{
            display: 'inline-block',
            width: '12px',
            height: '12px',
            backgroundColor: '#f44336',
            borderRadius: '50%',
            marginRight: '5px'
          }}></span>
          Low (≤5)
        </span>
      </div>

      {chartData.length > 0 && (
        <div style={{
          marginTop: '15px',
          padding: '10px',
          backgroundColor: '#fff',
          borderRadius: '4px',
          fontSize: '14px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
            <div>
              <strong>First Score:</strong> {chartData[0].score}
            </div>
            <div>
              <strong>Latest Score:</strong> {chartData[chartData.length - 1].score}
            </div>
            <div>
              <strong>Overall Avg:</strong> {
                (chartData.reduce((sum, d) => sum + d.score, 0) / chartData.length).toFixed(1)
              }
            </div>
            <div>
              <strong>Total Sessions:</strong> {chartData.length}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ScoresOverTimeChart;