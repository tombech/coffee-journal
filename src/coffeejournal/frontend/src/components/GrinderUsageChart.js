import React, { useState, useEffect } from 'react';
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { apiFetch } from '../config';

function GrinderUsageChart({ grinderId }) {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [grinderName, setGrinderName] = useState('');

  // Helper function to format grams/kilograms
  const formatWeight = (grams) => {
    if (grams >= 1000) {
      // Round to nearest 100g (0.1kg)
      const kg = Math.round(grams / 100) / 10;
      return `${kg}kg`;
    }
    return `${Math.round(grams)}g`;
  };

  useEffect(() => {
    fetchUsageData();
  }, [grinderId]);

  const fetchUsageData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch(`/grinders/${grinderId}/usage-over-time`);

      if (!response.ok) {
        throw new Error(`Failed to fetch usage data: ${response.status}`);
      }

      const data = await response.json();
      setGrinderName(data.grinder_name);

      // Process data for the chart
      const processedData = [];
      let cumulativeTotal = 0;

      data.data.forEach((point) => {
        cumulativeTotal += point.grams_ground;

        const dateObj = new Date(point.date);
        processedData.push({
          date: point.date,
          gramsGround: point.grams_ground,
          cumulativeTotal: cumulativeTotal,
          dateObj: dateObj,
          // Format date for display
          dateDisplay: dateObj.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
          })
        });
      });

      setChartData(processedData);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching usage data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={{ padding: '20px', textAlign: 'center' }}>Loading usage data...</div>;
  if (error) return <div style={{ padding: '20px', color: '#d32f2f' }}>Error loading usage chart: {error}</div>;
  if (chartData.length === 0) return <div style={{ padding: '20px', textAlign: 'center' }}>No usage data found for this grinder.</div>;

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length > 0) {
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
            {data.dateObj.toLocaleDateString('en-US', {
              weekday: 'short',
              month: 'short',
              day: 'numeric',
              year: 'numeric'
            })}
          </p>
          <p style={{ margin: '2px 0', color: '#1976d2' }}>Daily: {data.gramsGround}g</p>
          <p style={{ margin: '2px 0', color: '#2e7d32' }}>Total: {data.cumulativeTotal}g</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{
      marginTop: '30px',
      padding: '20px',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
    }}>
      <h3 style={{ marginBottom: '20px', color: '#333', textAlign: 'center' }}>
        Daily Grinding Usage
      </h3>
      <p style={{ marginBottom: '20px', color: '#666', textAlign: 'center', fontSize: '14px' }}>
        Track daily coffee grinding amounts and cumulative usage over time
      </p>

      <div style={{ position: 'relative' }}>
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart
            data={chartData}
            margin={{ top: 20, right: 80, left: 60, bottom: 70 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#d0d0d0"
              strokeWidth={1}
            />
            <XAxis
              dataKey="dateDisplay"
              tick={{ fontSize: 12 }}
              height={50}
              interval={chartData.length > 20 ? Math.floor(chartData.length / 12) : chartData.length > 10 ? Math.floor(chartData.length / 8) : 0}
              axisLine={{ stroke: '#999', strokeWidth: 2 }}
              tickLine={{ stroke: '#999', strokeWidth: 1 }}
            />
            <YAxis
              yAxisId="left"
              orientation="left"
              label={{ value: 'Daily Grams', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }}
              tick={{ fontSize: 12 }}
              axisLine={{ stroke: '#999', strokeWidth: 2 }}
              tickLine={{ stroke: '#999', strokeWidth: 1 }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              label={{ value: 'Cumulative Total (g)', angle: 90, position: 'insideRight', style: { textAnchor: 'middle' } }}
              tick={{ fontSize: 12 }}
              axisLine={{ stroke: '#999', strokeWidth: 2 }}
              tickLine={{ stroke: '#999', strokeWidth: 1 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Daily bars */}
            <Bar
              yAxisId="left"
              dataKey="gramsGround"
              fill="#1976d2"
              name="Daily Grams Ground"
              opacity={0.8}
            />

            {/* Cumulative line */}
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="cumulativeTotal"
              stroke="#2e7d32"
              strokeWidth={3}
              dot={{ r: 4, fill: '#2e7d32' }}
              name="Cumulative Total"
              connectNulls
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Summary Statistics */}
      {chartData.length > 0 && (
        <div style={{
          marginTop: '20px',
          padding: '15px',
          backgroundColor: '#fff',
          borderRadius: '6px',
          border: '1px solid #e0e0e0'
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '15px', textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#333' }}>
                {chartData.length}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Active Days</div>
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#1976d2' }}>
                {formatWeight(Math.round(chartData.reduce((sum, d) => sum + d.gramsGround, 0) / chartData.length))}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Avg Daily</div>
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#2e7d32' }}>
                {formatWeight(chartData[chartData.length - 1].cumulativeTotal)}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Ground</div>
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#d32f2f' }}>
                {formatWeight(Math.max(...chartData.map(d => d.gramsGround)))}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Highest Day</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default GrinderUsageChart;