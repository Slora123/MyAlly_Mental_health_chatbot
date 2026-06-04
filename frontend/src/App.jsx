import React, { useState, useEffect, useRef, Fragment } from 'react';
import { apiFetch } from './api';
import { Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import Header from './components/Header';
import MessageBubble from './components/MessageBubble';
import WelcomeBanner from './components/WelcomeBanner';
import TypingIndicator from './components/TypingIndicator';
import Sidebar from './components/Sidebar';
import Login from './components/Login';
import Onboarding from './components/Onboarding';
import CounselorDashboard from './CounselorDashboard';
import { detectThemeFromText } from './themes';
import { auth } from './firebase';
import { onAuthStateChanged, signOut } from 'firebase/auth';
import { botDefault, botFemale, botMale } from './assets/images.js';

// Map stored key strings to actual image data URLs
const AVATAR_MAP = { female: botFemale, male: botMale, default: '/logo.png' };
function resolveAvatar(value) {
  if (!value) return null;
  // If it's a known key, resolve it
  if (AVATAR_MAP[value]) return AVATAR_MAP[value];
  // Otherwise it's a custom base64 data URL — return as-is
  return value;
}
import './App.css';

// ── Chat cache helpers (module-level, not recreated on render) ──────────────
function saveChatCache(msgs, sid, uid) {
  try {
    const key = `myally_chat_cache_${uid || 'anon'}`;
    localStorage.setItem(key, JSON.stringify({ messages: msgs, session_id: sid, ts: Date.now() }));
  } catch (_) {}
}
function loadChatCache(uid) {
  try {
    const key = `myally_chat_cache_${uid || 'anon'}`;
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const cached = JSON.parse(raw);
    if (Date.now() - cached.ts > 86400000) return null; // expire after 24h
    return cached;
  } catch (_) { return null; }
}

// ── Date Formatting Helpers ───────────────────────────────────────────
function formatChatDate(dateString) {
  if (!dateString) return null;
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return null;

  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);

  const isSameDay = (d1, d2) => d1.getDate() === d2.getDate() &&
                                d1.getMonth() === d2.getMonth() &&
                                d1.getFullYear() === d2.getFullYear();

  if (isSameDay(date, today)) {
    return 'Today';
  } else if (isSameDay(date, yesterday)) {
    return 'Yesterday';
  } else {
    const options = { weekday: 'short', day: 'numeric', month: 'short' };
    return date.toLocaleDateString('en-US', options);
  }
}

// ── Profile cache helpers ──────────────────────────────────────────────
function saveProfileCache(profile, uid) {
  try {
    const key = `myally_profile_cache_${uid || 'anon'}`;
    localStorage.setItem(key, JSON.stringify({ profile, ts: Date.now() }));
  } catch (_) {}
}
function loadProfileCache(uid) {
  try {
    const key = `myally_profile_cache_${uid || 'anon'}`;
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const cached = JSON.parse(raw);
    if (Date.now() - cached.ts > 86400000) return null; // expire after 24h
    return cached.profile;
  } catch (_) { return null; }
}


export default function App() {
  const navigate = useNavigate();
  // Use sessionStorage so each browser tab has its own independent auth state.
  // Closing a tab or opening a new tab always starts fresh at the login page.
  // Use localStorage so the session survives page refreshes and browser restarts
  const [authToken, setAuthTokenState] = useState(localStorage.getItem('myally_token'));
  const [loading, setLoading] = useState(true);
  const isAdmin = window.location.pathname === '/admin';

  const setAuthToken = (token) => {
    if (token) {
      localStorage.setItem('myally_token', token);
    } else {
      localStorage.removeItem('myally_token');
      localStorage.removeItem('myally_explicit_login');
    }
    setAuthTokenState(token);
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        console.log("👤 [App] Auth state changed: User is logged in", user.email);
        try {
          const token = await user.getIdToken(/* forceRefresh */ false);
          localStorage.setItem('myally_token', token);
          localStorage.setItem('myally_explicit_login', 'true');
          setAuthTokenState(token);
        } catch (e) {
          console.warn('Failed to get token, logging out:', e);
          localStorage.removeItem('myally_token');
          localStorage.removeItem('myally_explicit_login');
          setAuthTokenState(null);
          navigate('/');
        }
      } else {
        console.log("👤 [App] No Firebase user. Clearing all tokens.");
        localStorage.removeItem('myally_token');
        localStorage.removeItem('myally_explicit_login');
        setAuthTokenState(null);
        navigate('/');
      }
      setLoading(false);
    });
    return () => unsubscribe();
  }, [navigate]);


  if (loading) {
    return (
      <div style={{
        height: '100vh', display: 'flex', flexDirection: 'column', 
        justifyContent: 'center', alignItems: 'center', 
        background: 'linear-gradient(135deg, #f3e8ff 0%, #fce7f3 50%, #fff1f1 100%)',
        fontFamily: "'Outfit', sans-serif"
      }}>
        <div className="loader"></div>
        <h2 style={{ marginTop: '20px', color: '#1e293b' }}>Initializing MyAlly...</h2>
      </div>
    );
  }

  if (isAdmin) {
    return <CounselorDashboard />;
  }

  return (
    <Routes>
      <Route path="/" element={<Login setAuthToken={setAuthToken} />} />
      <Route path="/onboarding" element={
        authToken ? <Onboarding authToken={authToken} /> : <Navigate to="/" />
      } />
      <Route path="/chat" element={
        (authToken && localStorage.getItem('myally_explicit_login') === 'true') 
          ? <ChatApp authToken={authToken} setAuthToken={setAuthToken} /> 
          : <Navigate to="/" />
      } />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}

async function handleLogout(setAuthToken) {
  try {
    await signOut(auth);
  } catch (e) {
    console.warn('Sign out error:', e);
  }
  localStorage.removeItem('myally_token');
  localStorage.removeItem('myally_explicit_login');
  setAuthToken(null);
  window.location.href = '/';
}

function ChatApp({ authToken, setAuthToken }) {

  const navigate = useNavigate();
  const uid = auth.currentUser?.uid || 'anon';

  // ── Load from caches synchronously — zero flicker on return visits ───────
  const cachedProfile = loadProfileCache(auth.currentUser?.uid);
  const cachedChats   = loadChatCache(auth.currentUser?.uid);

  const [messages, setMessages] = useState(cachedChats?.messages || []);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [theme, setTheme] = useState('calm');
  const [sessionId, setSessionId] = useState(cachedChats?.session_id || null);
  const [userEmail, setUserEmail] = useState(auth.currentUser?.email || cachedProfile?.email || '');
  // Profile loaded from cache immediately — updates in background from API
  const [userProfile, setUserProfile] = useState(cachedProfile || null);
  const [myAllyAvatar, setMyAllyAvatar] = useState(cachedProfile?.bot_avatar_url || null);
  const [userAvatar, setUserAvatar] = useState(cachedProfile?.avatar_url || null);

  const chatContainerRef = useRef(null);


  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  // Set body theme class on change
  useEffect(() => {
    document.body.className = `theme-${theme}`;
  }, [theme]);

  // Set initial theme class synchronously so CSS vars load right away
  if (typeof document !== 'undefined' && !document.body.className) {
    document.body.className = 'theme-calm';
  }


  // Load initial session on mount
  useEffect(() => {
    if (!authToken) return;

    const handleSessionExpired = () => {
      console.warn('\ud83d\udd12 Session expired \u2014 redirecting to login');
      localStorage.removeItem('myally_token');
      localStorage.removeItem('myally_explicit_login');
      setAuthToken(null);
      navigate('/');
    };

    // ── Fetch fresh history — fast timeouts, multi-retry ─────────────
    const fetchHistory = async (attempt = 1) => {
      try {
        const res = await apiFetch('/api/chats/all', {
          headers: { 'Authorization': `Bearer ${authToken}` },
          signal: AbortSignal.timeout(15000) // 15s — fail fast
        });
        if (res.status === 401) { handleSessionExpired(); return; }
        if (res.ok) {
          const data = await res.json();
          if (data.session_id) setSessionId(data.session_id);
          if (data.messages && data.messages.length > 0) {
            const loaded = data.messages.map(m => ({ role: m.role, text: m.content, time: m.created_at }));
            setMessages(loaded);
            saveChatCache(loaded, data.session_id, uid);
          }
        }
        setIsHistoryLoading(false);
      } catch (err) {
        if (attempt < 4) {
          // Retry up to 3 more times every 5s — backend waking up
          console.warn(`History fetch attempt ${attempt} failed, retry in 5s...`, err.message);
          setTimeout(() => fetchHistory(attempt + 1), 5000);
        } else {
          console.warn('All history fetch attempts failed. Showing empty chat.');
          setIsHistoryLoading(false);
        }
      }
    };

    // ── Fetch profile ──────────────────────────────────────────────
    const loadProfile = async () => {
      try {
        const r = await apiFetch('/api/user/profile', {
          headers: { 'Authorization': `Bearer ${authToken}` },
          signal: AbortSignal.timeout(15000)
        });
        if (r.status === 401) { handleSessionExpired(); return; }
        if (!r.ok) return;
        const profile = await r.json();
        if (profile.email) setUserEmail(profile.email);
        if (profile.avatar_url) setUserAvatar(profile.avatar_url);
        if (profile.bot_avatar_url) setMyAllyAvatar(profile.bot_avatar_url);
        setUserProfile(profile);
        // ✅ Save to cache so avatars load instantly on next visit
        saveProfileCache(profile, uid);
      } catch (_) { /* non-critical */ }
    };

    // ── Keep-alive — ping every 4 min so HF never sleeps ──────────
    const keepAlive = setInterval(() => {
      apiFetch('/api/health').catch(() => {});
    }, 4 * 60 * 1000);

    loadProfile();
    fetchHistory();

    return () => clearInterval(keepAlive);
  }, [authToken]);


  const handleSendMessage = async (textOverride) => {
    const text = textOverride || inputText;
    if (!text.trim() || isTyping) return;

    const userMsg = { role: 'user', text: text, time: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsTyping(true);
    // Reset height if it's a textarea
    const input = document.getElementById('chat-text-input');
    if (input) input.style.height = 'inherit';

    const detected = detectThemeFromText(text);
    if (detected) setTheme(detected);

    try {
      const response = await apiFetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });

      if (response.status === 401) {
        console.error('Session expired, logging out...');
        localStorage.removeItem('myally_token');
        localStorage.removeItem('myally_explicit_login');
        setAuthToken(null);
        navigate('/');

        return;
      }

      const data = await response.json();
      if (response.ok && data.session_id && data.session_id !== sessionId) {
        setSessionId(data.session_id);
      }

      let botText = data.reply;
      if (!response.ok) {
        botText = `Server Error: ${data.detail || response.statusText}`;
      } else if (!botText) {
        botText = "I'm sorry, I encountered an error. Please try again.";
      }

      const botMsg = {
        role: 'bot',
        text: botText,
        time: new Date().toISOString(),
      };
      setMessages((prev) => {
        const updated = [...prev, botMsg];
        // Keep cache up-to-date after every reply
        saveChatCache(updated, sessionId, uid);
        return updated;
      });
    } catch (err) {
      console.error('Chat error:', err);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSaveProfile = async (updates) => {
    if (!authToken) return;
    try {
      const res = await apiFetch('/api/user/onboarding', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(updates),
      });
      if (res.ok) {
        const data = await res.json();
        setUserProfile(data.user);
        // Keep profile cache in sync with latest changes
        saveProfileCache(data.user, uid);
      }

    } catch (err) {
      console.error('Failed to save profile:', err);
    }
  };

  return (
    <div className="app-wrapper">
      <div className="chat-glass-card" style={{ 
        position: 'relative', 
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column'
      }}>
        
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', minWidth: 0, position: 'relative' }}>
          
          <Header
            theme={theme}
            onSetTheme={setTheme}
            userEmail={userEmail}
            authToken={authToken}
            onLogout={() => handleLogout(setAuthToken)}
            userProfile={userProfile}
            myAllyAvatar={resolveAvatar(myAllyAvatar)}
            setMyAllyAvatar={(key) => { setMyAllyAvatar(key); handleSaveProfile({ bot_avatar_url: key }); }}
            userAvatar={resolveAvatar(userAvatar)}
            setUserAvatar={(key) => { setUserAvatar(key); handleSaveProfile({ avatar_url: key }); }}
          />
          <main className="chat-container" ref={chatContainerRef}>
            {/* Loading banner — only shown when NO cache and still fetching */}
            {isHistoryLoading && messages.length === 0 && (
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                justifyContent: 'center', padding: '40px 20px', gap: '12px',
                color: '#94a3b8', fontFamily: "'Outfit', sans-serif"
              }}>
                <div style={{
                  width: '36px', height: '36px', borderRadius: '50%',
                  border: '3px solid rgba(253,29,29,0.15)',
                  borderTopColor: '#fd1d1d',
                  animation: 'spin 0.8s linear infinite'
                }} />
                <p style={{ fontSize: '0.95rem', margin: 0 }}>Loading your chats...</p>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
              </div>
            )}
            {!isHistoryLoading && messages.length === 0 && (
              <WelcomeBanner onChipClick={(text) => handleSendMessage(text)} />
            )}
            {messages.length > 0 && messages.map((msg, i) => {
              const currentDateStr = formatChatDate(msg.time);
              const prevDateStr = i > 0 ? formatChatDate(messages[i - 1].time) : null;
              const showDateSeparator = currentDateStr !== prevDateStr;

              return (
                <Fragment key={i}>
                  {showDateSeparator && currentDateStr && (
                    <div className="chat-date-separator">
                      <span>{currentDateStr}</span>
                    </div>
                  )}
                  <MessageBubble 
                    item={msg} 
                    theme={theme} 
                    animate={i === messages.length - 1} 
                    botImg={resolveAvatar(myAllyAvatar) || (userProfile?.gender?.toLowerCase() === 'female' ? botFemale : (userProfile?.gender?.toLowerCase() === 'male' ? botMale : '/logo.png'))}
                    userAvatar={resolveAvatar(userAvatar)}
                  />
                </Fragment>
              );
            })}
            {isTyping && <TypingIndicator theme={theme} botImg={resolveAvatar(myAllyAvatar) || (userProfile?.gender?.toLowerCase() === 'female' ? botFemale : (userProfile?.gender?.toLowerCase() === 'male' ? botMale : '/logo.png'))} />}

          </main>
          <footer className="input-area">
            <div className="input-pill">
              <span className="input-icon">😊</span>
              <textarea
                id="chat-text-input"
                className="chat-input"
                placeholder="Type how you feel..."
                rows="1"
                value={inputText}
                onChange={(e) => {
                  setInputText(e.target.value);
                  e.target.style.height = 'inherit';
                  e.target.style.height = `${e.target.scrollHeight}px`;
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                    e.target.style.height = 'inherit';
                  }
                }}
              />
              <button id="send-message-btn" className="send-btn" onClick={() => handleSendMessage()} disabled={!inputText.trim() || isTyping}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"></line>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                </svg>
              </button>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}
