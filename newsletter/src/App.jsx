import React from 'react';
import NewsletterComponent from './components/NewsletterComponent';
import BrowsingHistoryComponent from './components/BrowsingHistoryComponent';

function App() {
  return (
    <div className="App" style={{ maxWidth: '1200px', margin: '0 auto', padding: '16px' }}>
      <h1 style={{ 
        fontSize: '1.875rem', 
        fontWeight: 'bold', 
        textAlign: 'center', 
        marginBottom: '32px' 
      }}>
        BrowseInsight
      </h1>
      
      <div style={{ marginBottom: '40px' }}>
        <BrowsingHistoryComponent />
      </div>
      
      <div style={{ marginBottom: '40px' }}>
        <NewsletterComponent />
      </div>
    </div>
  );
}

export default App;