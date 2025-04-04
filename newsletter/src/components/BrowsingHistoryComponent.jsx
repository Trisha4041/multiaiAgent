import React, { useState, useEffect } from 'react';

const BrowsingHistoryComponent = () => {
  const [historyItems, setHistoryItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState(7); // Default 7 days
  const [searchTerm, setSearchTerm] = useState('');
  const [stats, setStats] = useState({
    commonKeywords: [],
    totalTime: 0,
    domainDistribution: []
  });
  const [extensionAvailable, setExtensionAvailable] = useState(false);

  // Check if Chrome extension API is available
  useEffect(() => {
    const isAvailable = typeof chrome !== 'undefined' && chrome.history && typeof chrome.history.search === 'function';
    setExtensionAvailable(isAvailable);
    setLoading(!isAvailable);
  }, []);
  
  // New effect: fetch when extension becomes available
  useEffect(() => {
    if (extensionAvailable) {
      fetchHistory(timeRange, searchTerm);
    }
  }, [extensionAvailable]);
  
  // Fetch history based on time range and search term
  const fetchHistory = (days, term = '') => {
    if (!extensionAvailable) {
      console.warn("Cannot fetch history: Chrome extension API not available");
      setLoading(false);
      return;
    }
    
    setLoading(true);
    const millisecondsPerDay = 24 * 60 * 60 * 1000;
    const startTime = Date.now() - (days * millisecondsPerDay);

    try {
      chrome.history.search({
        text: term,
        startTime: startTime,
        maxResults: 1000
      }, (items) => {
        // Sort by most recent first
        const sortedItems = items.sort((a, b) => b.lastVisitTime - a.lastVisitTime);
        setHistoryItems(sortedItems);
        calculateStats(sortedItems);
        setLoading(false);
      });
    } catch (error) {
      console.error("Error fetching history:", error);
      setLoading(false);
      setHistoryItems([]);
    }
  };

  // Calculate statistics from history items
  const calculateStats = (items) => {
    // Extract keywords from titles
    const keywords = {};
    const domains = {};
    
    items.forEach(item => {
      // Process title for keywords
      if (item.title) {
        const words = item.title.toLowerCase()
          .split(/\s+/)
          .filter(word => word.length > 3 && !['https', 'http', 'www', 'com', 'org', 'the', 'and', 'that'].includes(word));
        
        words.forEach(word => {
          keywords[word] = (keywords[word] || 0) + 1;
        });
      }
      
      // Calculate domain distribution
      try {
        const url = new URL(item.url);
        const domain = url.hostname;
        domains[domain] = (domains[domain] || 0) + 1;
      } catch (e) {
        // Skip invalid URLs
      }
    });
    
    // Get top keywords
    const topKeywords = Object.entries(keywords)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([keyword, count]) => ({ keyword, count }));
    
    // Get domain distribution
    const topDomains = Object.entries(domains)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([domain, count]) => ({ domain, count }));
    
    // Estimate total browsing time (very rough estimate)
    const averageTimePerPage = 2 * 60 * 1000; // 2 minutes per page in milliseconds
    const totalTime = items.length * averageTimePerPage;
    
    setStats({
      commonKeywords: topKeywords,
      totalTime: totalTime,
      domainDistribution: topDomains
    });
  };

  // Format milliseconds to human-readable time
  const formatTime = (milliseconds) => {
    const hours = Math.floor(milliseconds / (1000 * 60 * 60));
    const minutes = Math.floor((milliseconds % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours} hours, ${minutes} minutes`;
  };

  // Export to CSV
  const exportToCSV = () => {
    const headers = ['Title', 'URL', 'Visit Time'];
    const rows = historyItems.map(item => [
      `"${item.title?.replace(/"/g, '""') || 'Untitled'}"`,
      `"${item.url}"`,
      `"${new Date(item.lastVisitTime).toLocaleString()}"`
    ]);
    
    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `chrome_history_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
  };

  // Handle search
  const handleSearch = () => {
    fetchHistory(timeRange, searchTerm);
  };

  // Handle time range change
  const handleTimeRangeChange = (e) => {
    const days = parseInt(e.target.value);
    setTimeRange(days);
    fetchHistory(days, searchTerm);
  };

  if (!extensionAvailable && !loading) {
    return (
      <div className="browsing-history-container">
        <h2>Browsing History Analytics</h2>
        <div className="error-message">
          <p>Chrome history extension API is not available.</p>
          <p>Please make sure that:</p>
          <ul>
            <li>The extension is properly installed</li>
            <li>The extension has the necessary permissions</li>
            <li>You're running this in a Chrome extension context</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="browsing-history-container">
      <h2>Browsing History Analytics</h2>
      
      {/* Controls */}
      <div className="controls">
        <div className="search-controls">
          <select 
            value={timeRange} 
            onChange={handleTimeRangeChange}
            className="time-range-select"
            disabled={!extensionAvailable || loading}
          >
            <option value="1">Last 1 Day</option>
            <option value="7">Last 7 Days</option>
            <option value="30">Last 30 Days</option>
            <option value="90">Last 90 Days</option>
          </select>
          
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search history..."
            className="search-input"
            disabled={!extensionAvailable || loading}
          />
          
          <button 
            onClick={handleSearch} 
            className="search-btn"
            disabled={!extensionAvailable || loading}
          >
            🔍 Search
          </button>
        </div>
        
        <div className="action-buttons">
          <button 
            onClick={exportToCSV} 
            className="export-btn"
            disabled={!extensionAvailable || loading || historyItems.length === 0}
          >
            📄 Export CSV
          </button>
          <button
            onClick={() => {
              setSearchTerm('');
              setTimeRange(7);
              fetchHistory(7, '');
            }}
            className="reset-btn"
            disabled={!extensionAvailable || loading}
          >
            🔄 Reset
          </button>
        </div>
      </div>

      {/* Statistics Display */}
      <div className="stats-container">
        <div className="stat-box">
          <h3>Browsing Summary</h3>
          <p>Pages visited: <strong>{historyItems.length}</strong></p>
          <p>Estimated time spent: <strong>{formatTime(stats.totalTime)}</strong></p>
        </div>

        <div className="stat-box">
          <h3>Top Keywords</h3>
          {stats.commonKeywords.length > 0 ? (
            <ul className="keyword-list">
              {stats.commonKeywords.slice(0, 5).map((item, index) => (
                <li key={index}>
                  <span className="keyword">{item.keyword}</span>
                  <span className="count">{item.count}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p>No keywords found</p>
          )}
        </div>

        <div className="stat-box">
          <h3>Most Visited Websites</h3>
          {stats.domainDistribution.length > 0 ? (
            <ul className="domain-list">
              {stats.domainDistribution.slice(0, 5).map((item, index) => (
                <li key={index}>
                  <span className="domain">{item.domain}</span>
                  <span className="count">{item.count} visits</span>
                </li>
              ))}
            </ul>
          ) : (
            <p>No domain data available</p>
          )}
        </div>
      </div>

      {/* History List */}
      <div className="history-section">
        <h3>Recent Browsing Activity</h3>
        {loading ? (
          <div className="loading">Loading history...</div>
        ) : (
          <div className="history-list">
            {historyItems.length > 0 ? (
              historyItems.map((item, index) => (
                <div key={index} className="history-item">
                  <h4 className="item-title">{item.title || 'Untitled'}</h4>
                  <p className="item-url">
                    <a href={item.url} target="_blank" rel="noopener noreferrer">
                      {item.url}
                    </a>
                  </p>
                  <p className="item-time">
                    {new Date(item.lastVisitTime).toLocaleString()}
                  </p>
                </div>
              ))
            ) : (
              <div className="no-results">No history items found</div>
            )}
          </div>
        )}
      </div>

      <style jsx>{`
        .browsing-history-container {
          font-family: Arial, sans-serif;
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
        }
        
        h2 {
          text-align: center;
          color: #333;
        }
        
        .controls {
          margin-bottom: 20px;
        }
        
        .search-controls, .action-buttons {
          display: flex;
          gap: 10px;
          margin-bottom: 10px;
        }
        
        .time-range-select, .search-input, button {
          padding: 8px 12px;
          border: 1px solid #ccc;
          border-radius: 4px;
        }
        
        .search-input {
          flex-grow: 1;
        }
        
        button {
          background-color: #4285f4;
          color: white;
          border: none;
          cursor: pointer;
          font-weight: bold;
        }

        button:disabled {
          background-color: #cccccc;
          cursor: not-allowed;
        }
        
        button:hover:not(:disabled) {
          background-color: #3367d6;
        }
        
        .stats-container {
          display: flex;
          flex-wrap: wrap;
          gap: 20px;
          margin-bottom: 30px;
        }
        
        .stat-box {
          flex: 1;
          min-width: 200px;
          background-color: #f5f5f5;
          border-radius: 8px;
          padding: 15px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        h3 {
          margin-top: 0;
          color: #333;
          border-bottom: 1px solid #ddd;
          padding-bottom: 5px;
        }
        
        .keyword-list, .domain-list {
          list-style: none;
          padding: 0;
        }
        
        .keyword-list li, .domain-list li {
          display: flex;
          justify-content: space-between;
          padding: 5px 0;
        }
        
        .history-list {
          max-height: 500px;
          overflow-y: auto;
          border: 1px solid #ddd;
          border-radius: 4px;
        }
        
        .history-item {
          padding: 15px;
          border-bottom: 1px solid #eee;
        }
        
        .history-item:last-child {
          border-bottom: none;
        }
        
        .item-title {
          margin: 0 0 5px 0;
          font-size: 16px;
          color: #1a0dab;
        }
        
        .item-url {
          margin: 5px 0;
          font-size: 14px;
          color: #006621;
          word-break: break-all;
        }
        
        .item-time {
          margin: 5px 0 0 0;
          font-size: 12px;
          color: #666;
        }
        
        .loading, .no-results {
          padding: 20px;
          text-align: center;
          color: #666;
        }

        .error-message {
          background-color: #fff3f3;
          border: 1px solid #ffcaca;
          padding: 20px;
          border-radius: 8px;
          margin-top: 20px;
          color: #d32f2f;
        }

        .error-message ul {
          margin-top: 10px;
          padding-left: 20px;
        }
      `}</style>
    </div>
  );
};

export default BrowsingHistoryComponent;