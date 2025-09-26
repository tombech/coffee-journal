import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Dot, ReferenceLine } from 'recharts';
import { apiFetch } from '../config';

function ScoresOverTimeChart({ grinderId }) {
  const [chartData, setChartData] = useState([]);
  const [timeSeparators, setTimeSeparators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [grinderName, setGrinderName] = useState('');
  const [monthHeaders, setMonthHeaders] = useState([]);
  const [zoomDomain, setZoomDomain] = useState(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectionStart, setSelectionStart] = useState(null);
  const [selectionEnd, setSelectionEnd] = useState(null);

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

      // Process data for the chart - calculate rolling averages
      const processedData = [];
      const shortWindowSize = 3; // 3-session rolling average

      data.data.forEach((point, index) => {
        // Calculate short-term rolling average (3 sessions)
        let shortAvgScore = point.score;
        if (data.data.length >= shortWindowSize) {
          const start = Math.max(0, index - Math.floor(shortWindowSize / 2));
          const end = Math.min(data.data.length, index + Math.floor(shortWindowSize / 2) + 1);
          const window = data.data.slice(start, end);
          shortAvgScore = window.reduce((sum, p) => sum + p.score, 0) / window.length;
        }


        // Calculate time-based 7-day rolling average
        let weeklyAvgScore = point.score;
        const currentDate = new Date(point.date);
        const sevenDaysAgo = new Date(currentDate.getTime() - (7 * 24 * 60 * 60 * 1000));

        // Find all sessions within the last 7 days (including current)
        const weeklyWindow = data.data.filter((p, i) => {
          const pDate = new Date(p.date);
          return pDate >= sevenDaysAgo && pDate <= currentDate && i <= index;
        });

        if (weeklyWindow.length > 0) {
          weeklyAvgScore = weeklyWindow.reduce((sum, p) => sum + p.score, 0) / weeklyWindow.length;
        }

        const dateObj = new Date(point.date);

        processedData.push({
          date: point.date,
          score: point.score,
          shortAverage: parseFloat(shortAvgScore.toFixed(2)),
          weeklyAverage: parseFloat(weeklyAvgScore.toFixed(2)),
          product: point.product_name,
          method: point.brew_method,
          index: index + 1,
          dateObj: dateObj,
          // Full date for tooltip
          fullDate: dateObj.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric',
            year: '2-digit'
          })
        });
      });

      // Add smart time formatting based on timespan
      const timeSpanDays = Math.ceil((processedData[processedData.length - 1]?.dateObj - processedData[0]?.dateObj) / (1000 * 60 * 60 * 24));

      processedData.forEach((point, index) => {
        if (timeSpanDays <= 14) {
          // Short timespan: show day + weekday
          point.timeDisplay = point.dateObj.toLocaleDateString('en-US', {
            weekday: 'short',
            day: 'numeric'
          });
        } else if (timeSpanDays <= 60) {
          // Medium timespan: show month + day
          point.timeDisplay = point.dateObj.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
          });
        } else {
          // Long timespan: show month + year for monthly markers
          const isMonthStart = index === 0 ||
            point.dateObj.getMonth() !== processedData[index - 1].dateObj.getMonth();

          if (isMonthStart) {
            point.timeDisplay = point.dateObj.toLocaleDateString('en-US', {
              month: 'short',
              year: '2-digit'
            });
          } else {
            point.timeDisplay = point.dateObj.getDate().toString();
          }
        }
      });

      // Add time period separators and month headers
      const timeSeparators = [];
      const monthHeaders = [];
      let currentMonth = null;
      let monthStartIndex = 0;

      processedData.forEach((point, index) => {
        const currentDate = point.dateObj;
        const monthKey = `${currentDate.getFullYear()}-${currentDate.getMonth()}`;

        // Track month changes for headers
        if (currentMonth !== monthKey) {
          if (currentMonth !== null) {
            // Finish previous month header
            monthHeaders[monthHeaders.length - 1].endIndex = index - 1;
            monthHeaders[monthHeaders.length - 1].width = index - monthStartIndex;
          }

          // Start new month header
          monthHeaders.push({
            month: currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
            startIndex: index,
            endIndex: index,
            width: 1
          });
          currentMonth = monthKey;
          monthStartIndex = index;

          // Add month separator line (except for first month)
          if (index > 0) {
            timeSeparators.push({
              index: index,
              type: 'month',
              xValue: point.timeDisplay
            });
          }
        }

        // Check for week boundaries (Monday) - but not at month boundaries
        if (index > 0) {
          const previousDate = processedData[index - 1].dateObj;
          if (currentDate.getDay() === 1 && previousDate.getDay() !== 1 &&
              currentDate.getMonth() === previousDate.getMonth()) {
            timeSeparators.push({
              index: index,
              type: 'week',
              xValue: point.timeDisplay
            });
          }
        }
      });

      // Finish last month header
      if (monthHeaders.length > 0) {
        monthHeaders[monthHeaders.length - 1].endIndex = processedData.length - 1;
        monthHeaders[monthHeaders.length - 1].width = processedData.length - monthStartIndex;
      }

      setChartData(processedData);
      setTimeSeparators(timeSeparators);
      setMonthHeaders(monthHeaders);
      console.log('Time separators calculated:', timeSeparators);
      console.log('Month headers calculated:', monthHeaders);
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
            {data.fullDate}
          </p>
          <p style={{ margin: '2px 0', color: '#2e7d32' }}>Score: {data.score}</p>
          <p style={{ margin: '2px 0', color: '#1976d2' }}>3-session avg: {data.shortAverage}</p>
          <p style={{ margin: '2px 0', color: '#d32f2f' }}>7-day avg: {data.weeklyAverage}</p>
          <p style={{ margin: '2px 0', fontSize: '0.9em' }}>{data.product}</p>
          <p style={{ margin: '2px 0', fontSize: '0.9em' }}>{data.method}</p>
        </div>
      );
    }
    return null;
  };

  // Calculate trend direction based on weekly averages for better insights
  const getTrendAnalysis = () => {
    if (chartData.length < 7) return null; // Need at least a week's worth of data

    const firstThird = chartData.slice(0, Math.floor(chartData.length / 3));
    const lastThird = chartData.slice(-Math.floor(chartData.length / 3));

    // Use weekly averages instead of raw scores for more stable trend analysis
    const firstAvg = firstThird.reduce((sum, d) => sum + d.weeklyAverage, 0) / firstThird.length;
    const lastAvg = lastThird.reduce((sum, d) => sum + d.weeklyAverage, 0) / lastThird.length;

    const improvement = lastAvg - firstAvg;

    if (improvement > 0.2) return { direction: 'improving', value: improvement };
    if (improvement < -0.2) return { direction: 'declining', value: Math.abs(improvement) };
    return { direction: 'stable', value: Math.abs(improvement) };
  };

  const trendAnalysis = getTrendAnalysis();

  // Convert mouse position to chart data index
  const getDataIndexFromMouse = (e, chartContainer) => {
    if (!chartContainer || !chartData.length) return null;

    const rect = chartContainer.getBoundingClientRect();
    // More accurate chart area calculation based on Recharts margins
    const chartLeft = rect.left + (rect.width * 0.12); // ~12% left margin
    const chartRight = rect.right - (rect.width * 0.12); // ~12% right margin
    const chartWidth = chartRight - chartLeft;

    if (e.clientX < chartLeft || e.clientX > chartRight) return null;

    const relativeX = (e.clientX - chartLeft) / chartWidth;
    const visibleData = getVisibleData();

    // Clamp to valid range
    const clampedX = Math.max(0, Math.min(1, relativeX));
    const dataIndex = Math.round(clampedX * (visibleData.length - 1));

    // Map back to original chartData index if zoomed
    if (zoomDomain) {
      return Math.max(0, Math.min(chartData.length - 1, zoomDomain.startIndex + dataIndex));
    }
    return Math.max(0, Math.min(chartData.length - 1, dataIndex));
  };

  // Mouse selection handlers
  const handleMouseDown = (e) => {
    if (!chartData.length) return;

    // Don't start selection if clicking on brush-related elements
    const target = e.target;
    const targetClasses = target.className || '';

    // Check if clicking on brush elements (Recharts uses these class names)
    if (targetClasses.includes('recharts-brush') ||
        target.closest('.recharts-brush') ||
        targetClasses.includes('brush')) {
      return; // Don't interfere with brush interactions
    }

    // Also check by position as backup
    const rect = e.currentTarget.getBoundingClientRect();
    const relativeY = (e.clientY - rect.top) / rect.height;
    if (relativeY > 0.88) {
      return; // Bottom area reserved for brush
    }

    const chartContainer = e.currentTarget;
    const dataIndex = getDataIndexFromMouse(e, chartContainer);

    if (dataIndex !== null) {
      setIsSelecting(true);
      setSelectionStart(dataIndex);
      setSelectionEnd(dataIndex);
    }
  };

  const handleMouseMove = (e) => {
    if (!isSelecting || selectionStart === null || !chartData.length) return;

    const chartContainer = e.currentTarget;
    const dataIndex = getDataIndexFromMouse(e, chartContainer);

    if (dataIndex !== null) {
      setSelectionEnd(dataIndex);
    }
  };

  const handleMouseUp = () => {
    if (isSelecting && selectionStart !== null && selectionEnd !== null) {
      const startIndex = Math.min(selectionStart, selectionEnd);
      const endIndex = Math.max(selectionStart, selectionEnd);

      // Only zoom if selection spans more than 2 points
      if (endIndex - startIndex > 2) {
        setZoomDomain({ startIndex, endIndex });
      }
    }

    setIsSelecting(false);
    setSelectionStart(null);
    setSelectionEnd(null);
  };

  // Reset zoom
  const resetZoom = () => {
    setZoomDomain(null);
  };

  // Pan functions for when zoomed
  const panLeft = () => {
    if (!zoomDomain) return;
    const domainSize = zoomDomain.endIndex - zoomDomain.startIndex;
    const panAmount = Math.max(1, Math.floor(domainSize * 0.25)); // Pan by 25% of current view

    const newStart = Math.max(0, zoomDomain.startIndex - panAmount);
    const newEnd = Math.min(chartData.length - 1, newStart + domainSize);

    setZoomDomain({ startIndex: newStart, endIndex: newEnd });
  };

  const panRight = () => {
    if (!zoomDomain) return;
    const domainSize = zoomDomain.endIndex - zoomDomain.startIndex;
    const panAmount = Math.max(1, Math.floor(domainSize * 0.25)); // Pan by 25% of current view

    const newEnd = Math.min(chartData.length - 1, zoomDomain.endIndex + panAmount);
    const newStart = Math.max(0, newEnd - domainSize);

    setZoomDomain({ startIndex: newStart, endIndex: newEnd });
  };


  // Get visible data based on zoom
  const getVisibleData = () => {
    if (!zoomDomain) return chartData;
    return chartData.slice(zoomDomain.startIndex, zoomDomain.endIndex + 1);
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
        Brewing Progress Timeline
      </h3>
      <p style={{ marginBottom: '20px', color: '#666', textAlign: 'center', fontSize: '14px' }}>
        Track your brewing skill development and equipment performance over time
      </p>

      {/* Month Headers - Calendar Style */}
      {monthHeaders.length > 0 && (
        <div style={{
          marginBottom: '10px',
          display: 'flex',
          fontSize: '14px',
          fontWeight: 'bold',
          color: '#333',
          borderBottom: '2px solid #e0e0e0',
          paddingBottom: '8px'
        }}>
          {monthHeaders.map((header, index) => (
            <div
              key={index}
              style={{
                flex: header.width,
                textAlign: 'center',
                padding: '4px',
                borderRight: index < monthHeaders.length - 1 ? '1px solid #ccc' : 'none'
              }}
            >
              {header.month}
            </div>
          ))}
        </div>
      )}

      {/* Time Period Context Bar with Zoom Controls */}
      {chartData.length > 0 && (
        <div style={{
          marginBottom: '15px',
          padding: '8px 12px',
          backgroundColor: '#f8f9fa',
          borderRadius: '4px',
          border: '1px solid #e0e0e0',
          fontSize: '12px',
          color: '#666',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>
            {chartData.length} sessions from {chartData[0].fullDate} to {chartData[chartData.length - 1].fullDate}
            ({Math.ceil((chartData[chartData.length - 1]?.dateObj - chartData[0]?.dateObj) / (1000 * 60 * 60 * 24))} days)
          </span>
          {zoomDomain && (
            <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
              <button
                onClick={panLeft}
                style={{
                  padding: '4px 8px',
                  fontSize: '11px',
                  backgroundColor: '#1976d2',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer'
                }}
                title="Pan left"
              >
                ← Pan
              </button>
              <button
                onClick={panRight}
                style={{
                  padding: '4px 8px',
                  fontSize: '11px',
                  backgroundColor: '#1976d2',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer'
                }}
                title="Pan right"
              >
                Pan →
              </button>
              <button
                onClick={resetZoom}
                style={{
                  padding: '4px 8px',
                  fontSize: '11px',
                  backgroundColor: '#2e7d32',
                  color: 'white',
                  border: 'none',
                  borderRadius: '3px',
                  cursor: 'pointer'
                }}
              >
                Reset Zoom
              </button>
            </div>
          )}
        </div>
      )}

      <div
        style={{
          position: 'relative'
        }}
      >
        {/* Chart interaction overlay - excludes brush area */}
        <div
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '75%', // Only cover the main chart area, not the brush
            cursor: isSelecting ? 'crosshair' : 'crosshair',
            userSelect: 'none',
            zIndex: 1,
            pointerEvents: isSelecting ? 'auto' : 'auto'
          }}
        />
        {/* Selection overlay */}
        {isSelecting && selectionStart !== null && selectionEnd !== null && (() => {
          const visibleData = getVisibleData();
          const startPos = Math.min(selectionStart, selectionEnd);
          const endPos = Math.max(selectionStart, selectionEnd);
          const totalLength = chartData.length - 1;

          // Calculate relative positions within the visible area
          let relativeStart, relativeEnd;
          if (zoomDomain) {
            relativeStart = (startPos - zoomDomain.startIndex) / (zoomDomain.endIndex - zoomDomain.startIndex);
            relativeEnd = (endPos - zoomDomain.startIndex) / (zoomDomain.endIndex - zoomDomain.startIndex);
          } else {
            relativeStart = startPos / totalLength;
            relativeEnd = endPos / totalLength;
          }

          const leftPercent = 12 + relativeStart * 76; // Chart area is roughly 12%-88% of container
          const widthPercent = Math.max(0.5, (relativeEnd - relativeStart) * 76); // Minimum width for visibility

          return (
            <div
              style={{
                position: 'absolute',
                top: '20px',
                left: `${leftPercent}%`,
                width: `${widthPercent}%`,
                height: 'calc(100% - 90px)',
                backgroundColor: 'rgba(46, 125, 50, 0.2)',
                border: '1px dashed #2e7d32',
                pointerEvents: 'none',
                zIndex: 10
              }}
            />
          );
        })()}

          <ResponsiveContainer width="100%" height={400}>
            <LineChart
              data={getVisibleData()}
              margin={{ top: 20, right: 80, left: 60, bottom: 70 }}
            >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#d0d0d0"
              strokeWidth={1}
            />
            <XAxis
              dataKey="timeDisplay"
              tick={{ fontSize: 12, angle: 0 }}
              height={50}
              interval={chartData.length > 20 ? Math.floor(chartData.length / 12) : chartData.length > 10 ? Math.floor(chartData.length / 8) : 0}
              axisLine={{ stroke: '#999', strokeWidth: 2 }}
              tickLine={{ stroke: '#999', strokeWidth: 1 }}
            />
            <YAxis
              domain={[0, 10]}
              ticks={[0, 2, 4, 6, 8, 10]}
              label={{ value: 'Score', angle: -90, position: 'insideLeft', style: { textAnchor: 'middle' } }}
              tick={{ fontSize: 12 }}
              axisLine={{ stroke: '#999', strokeWidth: 2 }}
              tickLine={{ stroke: '#999', strokeWidth: 1 }}
            />
          <Tooltip content={<CustomTooltip />} />
          <Legend />

          {/* Time period separators - calendar style */}
          {timeSeparators.map((separator, sepIndex) => (
            <ReferenceLine
              key={`separator-${sepIndex}`}
              x={separator.xValue}
              stroke={separator.type === 'month' ? '#d32f2f' : '#e0e0e0'}
              strokeDasharray={separator.type === 'month' ? '4 2' : '2 2'}
              strokeWidth={separator.type === 'month' ? 2 : 1}
              strokeOpacity={separator.type === 'month' ? 0.8 : 0.5}
            />
          ))}

          {/* Short-term trend line */}
          <Line
            type="monotone"
            dataKey="shortAverage"
            stroke="#1976d2"
            strokeWidth={2}
            dot={false}
            name="Short Trend (3-session)"
            connectNulls
          />

          {/* Weekly time-based trend line */}
          <Line
            type="monotone"
            dataKey="weeklyAverage"
            stroke="#d32f2f"
            strokeWidth={2.5}
            dot={false}
            name="Weekly Trend (7-day)"
            connectNulls
            strokeDasharray="5 5"
          />

          {/* Individual scores - subtle background */}
          <Line
            type="monotone"
            dataKey="score"
            stroke="#90a4ae"
            strokeWidth={1}
            dot={{ r: 2, fill: '#90a4ae' }}
            name="Individual Sessions"
            connectNulls
          />

        </LineChart>
      </ResponsiveContainer>

      {/* Manual right Y-axis labels */}
      <div style={{
        position: 'absolute',
        right: '55px',
        top: '15px',
        height: '250px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '12px',
        color: '#666',
        pointerEvents: 'none'
      }}>
        <span>10</span>
        <span>8</span>
        <span>6</span>
        <span>4</span>
        <span>2</span>
        <span>0</span>
      </div>

      {/* Right Y-axis label */}
      <div style={{
        position: 'absolute',
        right: '20px',
        top: '40%',
        transform: 'translateY(-50%) rotate(90deg)',
        fontSize: '12px',
        color: '#666',
        fontWeight: 'normal',
        transformOrigin: 'center',
        pointerEvents: 'none'
      }}>
        Score
      </div>
      </div>

      <div style={{
        marginTop: '15px',
        display: 'flex',
        gap: '30px',
        fontSize: '13px',
        color: '#666',
        justifyContent: 'center',
        alignItems: 'center',
        flexWrap: 'wrap'
      }}>
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{
            display: 'inline-block',
            width: '20px',
            height: '2px',
            backgroundColor: '#1976d2',
            marginRight: '8px'
          }}></span>
          <strong>Short Trend</strong> (3-session avg)
        </span>
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{
            display: 'inline-block',
            width: '20px',
            height: '2.5px',
            backgroundColor: '#d32f2f',
            marginRight: '8px',
            backgroundImage: 'repeating-linear-gradient(90deg, #d32f2f 0, #d32f2f 5px, transparent 5px, transparent 10px)'
          }}></span>
          <strong>Weekly Trend</strong> (7-day avg)
        </span>
        <span style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{
            display: 'inline-block',
            width: '6px',
            height: '6px',
            backgroundColor: '#90a4ae',
            borderRadius: '50%',
            marginRight: '8px'
          }}></span>
          Individual Sessions
        </span>
      </div>

      {/* Interactive Controls Instructions */}
      <div style={{
        marginTop: '10px',
        fontSize: '11px',
        color: '#888',
        textAlign: 'center',
        fontStyle: 'italic'
      }}>
        💡 <strong>Click + drag</strong> to select time range to zoom {zoomDomain && ' • Use pan buttons to navigate'}
      </div>

      {chartData.length > 0 && (
        <div style={{
          marginTop: '20px',
          padding: '15px',
          backgroundColor: '#fff',
          borderRadius: '6px',
          border: '1px solid #e0e0e0'
        }}>
          {/* Trend Analysis */}
          {trendAnalysis && (
            <div style={{
              marginBottom: '15px',
              padding: '10px',
              backgroundColor: trendAnalysis.direction === 'improving' ? '#e8f5e8' :
                               trendAnalysis.direction === 'declining' ? '#ffeaea' : '#f5f5f5',
              borderRadius: '4px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '16px', fontWeight: 'bold', marginBottom: '5px' }}>
                Trend: {trendAnalysis.direction === 'improving' ? '📈 Improving' :
                        trendAnalysis.direction === 'declining' ? '📉 Declining' : '➡️ Stable'}
              </div>
              <div style={{ fontSize: '13px', color: '#666' }}>
                {trendAnalysis.direction === 'improving' && `Average improvement of +${trendAnalysis.value.toFixed(1)} points`}
                {trendAnalysis.direction === 'declining' && `Average decline of -${trendAnalysis.value.toFixed(1)} points`}
                {trendAnalysis.direction === 'stable' && 'Consistent performance over time'}
              </div>
            </div>
          )}

          {/* Summary Statistics */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '15px', textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#333' }}>
                {chartData.length}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Total Sessions</div>
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#2e7d32' }}>
                {(chartData.reduce((sum, d) => sum + d.score, 0) / chartData.length).toFixed(1)}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Average Score</div>
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#1976d2' }}>
                {Math.max(...chartData.map(d => d.score))}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Best Score</div>
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#1976d2' }}>
                {chartData[chartData.length - 1].shortAverage}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Current Short Trend</div>
            </div>
            <div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#d32f2f' }}>
                {chartData[chartData.length - 1].weeklyAverage}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>Current Weekly Trend</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ScoresOverTimeChart;