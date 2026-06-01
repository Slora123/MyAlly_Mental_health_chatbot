import { useState, useEffect } from 'react';
import './CounselorDashboard.css';

export default function CounselorDashboard() {
  const [alerts, setAlerts] = useState([]);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const response = await fetch('/api/admin/alerts');
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    // Poll for new alerts every 10 seconds
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleResolve = async (id) => {
    try {
      await fetch(`/api/admin/resolve/${id}`, { method: 'POST' });
      fetchAlerts();
      if (selectedAlert?.id === id) setSelectedAlert(null);
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  return (
    <div className="admin-dashboard">
      <div className="admin-sidebar glass">
        <div className="admin-header">
          <h1>Guardian Panel</h1>
          <p>Counselor Dashboard</p>
        </div>
        
        <div className="alert-list">
          {loading && <p className="loading">Checking for alerts...</p>}
          {!loading && alerts.length === 0 && (
            <div className="empty-state">
              <span className="icon">🛡️</span>
              <p>All clear. No active crises.</p>
            </div>
          )}
          {alerts.map((alert) => (
            <div 
              key={alert.id} 
              className={`alert-item ${selectedAlert?.id === alert.id ? 'active' : ''} ${alert.status}`}
              onClick={() => setSelectedAlert(alert)}
            >
              <div className="alert-badge">HIGH RISK</div>
              <div className="alert-info">
                <span className="user-name">{alert.user_info.split('(')[0]}</span>
                <span className="timestamp">{new Date(alert.timestamp).toLocaleTimeString()}</span>
              </div>
              <p className="summary-snippet">{alert.summary.substring(0, 50)}...</p>
            </div>
          ))}
        </div>
      </div>

      <div className="admin-content">
        {selectedAlert ? (
          <div className="alert-detail glass">
            <div className="detail-header">
              <h2>Crisis Details</h2>
              <button className="resolve-btn" onClick={() => handleResolve(selectedAlert.id)}>
                Mark as Handled
              </button>
            </div>
            
            <section className="detail-section">
              <h3>User Contact</h3>
              <p className="info-text">{selectedAlert.user_info}</p>
            </section>

            <section className="detail-section">
              <h3>Trigger Message</h3>
              <div className="trigger-box glass">
                " {selectedAlert.trigger_message} "
              </div>
            </section>

            <section className="detail-section">
              <h3>AI Assessment Summary</h3>
              <div className="summary-box">
                {selectedAlert.summary}
              </div>
            </section>

          </div>
        ) : (
          <div className="placeholder glass">
            <img src="https://img.icons8.com/clouds/200/protection-mask.png" alt="Safety" />
            <h2>Safety First</h2>
            <p>Select an alert from the sidebar to view the risk assessment and contact details.</p>
          </div>
        )}
      </div>
    </div>
  );
}
