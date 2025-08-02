import React from 'react';
import { version } from '../version';

function VersionFooter() {
  const shortCommit = version.commit.substring(0, 8);
  const buildDate = new Date(version.buildDate).toLocaleDateString();

  return (
    <footer style={{
      marginTop: '40px',
      padding: '20px',
      borderTop: '1px solid #e0e0e0',
      textAlign: 'center',
      fontSize: '12px',
      color: '#666',
      backgroundColor: '#f8f9fa'
    }}>
      <div>
        Coffee Journal v{version.version}
      </div>
      <div style={{ marginTop: '4px' }}>
        Build: {shortCommit} • {buildDate}
      </div>
    </footer>
  );
}

export default VersionFooter;