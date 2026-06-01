import { useState, useEffect } from 'react';

export default function Sidebar({ authToken, currentSessionId, onSelectSession }) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authToken) {
      fetchSessions();
    }
  }, [authToken]);

  const fetchSessions = async (retries = 2) => {
    try {
      const res = await fetch('/api/chats', {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      if (res.status === 401 && retries > 0) {
        // Brief token refresh race — retry after a short delay
        setTimeout(() => fetchSessions(retries - 1), 800);
        return;
      }
      if (res.ok) {
        const data = await res.json();
        setSessions(data.sessions || []);
      }
    } catch (err) {
      console.error('Failed to fetch sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (isoStr) => {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      const now = new Date();
      const diffDays = Math.floor((now - d) / 86400000);
      if (diffDays === 0) return 'Today';
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 7) return `${diffDays}d ago`;
      return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    } catch { return ''; }
  };

  return (
    <div style={{
      width: '100%',
      height: '100%',
      background: 'rgba(255, 245, 240, 0.92)',
      backdropFilter: 'blur(24px)',
      WebkitBackdropFilter: 'blur(24px)',
      borderRight: '1px solid rgba(255, 255, 255, 0.6)',
      display: 'flex',
      flexDirection: 'column',
      fontFamily: "'Inter', sans-serif",
      overflowY: 'auto',
    }}>
      {/* Header */}
      <div style={{
        padding: '24px 20px 16px',
        borderBottom: '1px solid rgba(0,0,0,0.05)',
      }}>
        <p style={{
          margin: 0,
          fontSize: '11px',
          fontWeight: 700,
          letterSpacing: '0.08em',
          color: 'rgba(60, 26, 26, 0.45)',
          textTransform: 'uppercase',
        }}>
          Chat History
        </p>
      </div>

      {/* Session list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 10px' }}>
        {loading ? (
          <div style={{ padding: '20px 10px', textAlign: 'center' }}>
            {[...Array(4)].map((_, i) => (
              <div key={i} style={{
                height: '52px', borderRadius: '14px',
                background: 'rgba(0,0,0,0.05)',
                marginBottom: '8px',
                animation: 'pulse 1.4s ease-in-out infinite',
                animationDelay: `${i * 0.15}s`,
              }} />
            ))}
          </div>
        ) : sessions.length === 0 ? (
          <div style={{
            padding: '30px 16px',
            textAlign: 'center',
            color: 'rgba(60,26,26,0.4)',
            fontSize: '13px',
            lineHeight: 1.6,
          }}>
            <div style={{ fontSize: '28px', marginBottom: '10px' }}>💬</div>
            No past chats yet.<br />Start a conversation!
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = currentSessionId === session.id;
            return (
              <button
                key={session.id}
                onClick={() => onSelectSession(session.id)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '10px 12px',
                  marginBottom: '4px',
                  borderRadius: '14px',
                  border: isActive
                    ? '1.5px solid rgba(240, 112, 96, 0.4)'
                    : '1.5px solid transparent',
                  background: isActive
                    ? 'rgba(240, 112, 96, 0.10)'
                    : 'transparent',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.18s ease',
                }}
                onMouseEnter={e => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'rgba(0,0,0,0.04)';
                    e.currentTarget.style.border = '1.5px solid rgba(0,0,0,0.06)';
                  }
                }}
                onMouseLeave={e => {
                  if (!isActive) {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.border = '1.5px solid transparent';
                  }
                }}
              >
                <span style={{ fontSize: '16px', flexShrink: 0 }}>💬</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{
                    margin: 0,
                    fontSize: '13px',
                    fontWeight: isActive ? 700 : 500,
                    color: isActive ? '#d94f3a' : '#3c1a1a',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    lineHeight: 1.3,
                  }}>
                    {session.title || 'Chat'}
                  </p>
                  <p style={{
                    margin: 0,
                    fontSize: '11px',
                    color: 'rgba(60,26,26,0.4)',
                    marginTop: '2px',
                  }}>
                    {formatDate(session.updated_at || session.created_at)}
                  </p>
                </div>
                {isActive && (
                  <div style={{
                    width: '6px', height: '6px',
                    borderRadius: '50%',
                    background: '#f07060',
                    flexShrink: 0,
                  }} />
                )}
              </button>
            );
          })
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.8; }
        }
      `}</style>
    </div>
  );
}
