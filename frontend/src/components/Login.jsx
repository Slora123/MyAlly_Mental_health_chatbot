import { useState } from 'react';
import { signInWithPopup } from 'firebase/auth';
import { useNavigate } from 'react-router-dom';
import { auth, googleProvider } from '../firebase';
import { loginMockup } from '../assets/images.js';

export default function Login({ setAuthToken }) {
  const navigate = useNavigate();
  const [role, setRole] = useState(null); // 'student' or 'admin'
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  const handleGoogleLogin = async (mode) => {
    if (isLoggingIn) return;
    setIsLoggingIn(true);

    try {
      const result = await signInWithPopup(auth, googleProvider);

      if (result?.user) {
        const token = await result.user.getIdToken();
        console.log('✅ [Login] Popup login successful for:', result.user.email);

        sessionStorage.setItem('myally_token', token);
        sessionStorage.setItem('myally_explicit_login', 'true');
        localStorage.setItem('myally_token', token);
        
        // CRITICAL: Tell App.jsx we are logged in so the gatekeeper lets us through
        setAuthToken(token);

        if (role === 'admin') {
          navigate('/admin');
          return;
        }

        // FIREBASE METADATA CHECK: Bypass backend check for returning users
        const createdTime = new Date(result.user.metadata.creationTime).getTime();
        const lastLoginTime = new Date(result.user.metadata.lastSignInTime).getTime();
        // If they just created the account, these times will be nearly identical
        const isBrandNewAccount = Math.abs(lastLoginTime - createdTime) < 5000; 

        if (mode === 'create') {
          if (!isBrandNewAccount) {
            // Returning user trying to create an account
            alert("You have already created an account! Please use 'Sign In with Google' instead.");
            setIsLoggingIn(false);
            return;
          } else {
            // Brand new user creating an account
            navigate('/onboarding');
            return;
          }
        } else if (mode === 'signin') {
          if (!isBrandNewAccount) {
            // Returning user signing in normally
            navigate('/chat');
            return;
          } else {
            // Brand new user who clicked "Sign in" instead of create
            // We should still send them to onboarding since they are new
            navigate('/onboarding');
            return;
          }
        }
      }
    } catch (error) {
      console.error('❌ Login failed:', error);
      setIsLoggingIn(false);
      setStatusMsg('');
      if (error.code === 'auth/popup-blocked') {
        alert('Popup was blocked by your browser! Please click "Open App in Full Screen" instead.');
      } else if (error.code !== 'auth/popup-closed-by-user') {
        alert('Login failed: ' + error.message);
      }
    }
  };


  // ── Role Selection Screen ──────────────────────────────────────────────────
  if (!role) {
    return (
      <div className="login-wrapper" style={{
        background: 'linear-gradient(135deg, #f3e8ff 0%, #fce7f3 50%, #fff1f1 100%)',
        minHeight: '100vh',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        fontFamily: "'Outfit', sans-serif",
        overflow: 'hidden'
      }}>
        <div className="role-selection-card" style={{
          display: 'flex', width: '92%', maxWidth: '1200px', height: '80vh',
          borderRadius: '48px', overflow: 'hidden',
          background: 'rgba(255, 250, 245, 0.85)',
          backdropFilter: 'blur(30px)', WebkitBackdropFilter: 'blur(30px)',
          border: '1px solid rgba(255, 255, 255, 0.5)',
          boxShadow: '0 40px 100px -20px rgba(253, 29, 29, 0.05)',
          position: 'relative'
        }}>
          {/* Left Side */}
          <div className="login-text-side" style={{ flex: 1, padding: '70px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <h1 style={{
              fontSize: '4.8rem', fontWeight: '900', color: '#1e293b',
              marginBottom: '10px', letterSpacing: '-2px', lineHeight: 1
            }}>
              Welcome to <br />
              <span style={{
                background: 'linear-gradient(to right, #833ab4, #fd1d1d, #fcb045)',
                WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
                display: 'inline-block'
              }}>
                MyAlly
              </span>
            </h1>
            <p style={{ color: '#64748b', fontSize: '1.3rem', marginBottom: '50px', fontWeight: '400' }}>
              Your dedicated space for mental wellness and support.
            </p>

            <div className="role-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div
                className="role-option"
                onClick={() => setRole('student')}
                style={{
                  background: 'rgba(255, 255, 255, 0.5)', padding: '40px 30px',
                  borderRadius: '28px', cursor: 'pointer',
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                  border: '1px solid rgba(0,0,0,0.03)',
                  textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '12px'
                }}
              >
                <div style={{ color: '#fd1d1d' }}>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                </div>
                <div>
                  <h2 style={{ color: '#1e293b', fontSize: '1.6rem', fontWeight: '700', marginBottom: '4px' }}>Student</h2>
                  <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>Personalized support</p>
                </div>
              </div>

              <div
                className="role-option"
                onClick={() => setRole('admin')}
                style={{
                  background: 'rgba(255, 255, 255, 0.5)', padding: '40px 30px',
                  borderRadius: '28px', cursor: 'pointer',
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                  border: '1px solid rgba(0,0,0,0.03)',
                  textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '12px'
                }}
              >
                <div style={{ color: '#833ab4' }}>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
                </div>
                <div>
                  <h2 style={{ color: '#1e293b', fontSize: '1.6rem', fontWeight: '700', marginBottom: '4px' }}>Counselor</h2>
                  <p style={{ color: '#94a3b8', fontSize: '0.95rem' }}>Guardian panel</p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Side: Image */}
          <div className="login-image-side" style={{
            flex: 1, 
            position: 'relative',
            borderRadius: '0 48px 48px 0', 
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#fff'
          }}>
            <img 
              src={loginMockup} 
              alt="MyAlly Mockup" 
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                display: loginMockup ? 'block' : 'none'
              }} 
            />
            {!loginMockup && <div style={{ color: '#ccc' }}>Loading preview...</div>}
          </div>
        </div>
        <style>{`
          @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&display=swap');
          
          @media (max-width: 900px) {
            .login-wrapper {
              overflow-y: auto !important;
              padding: 20px 15px !important; /* Added side space */
            }
            .role-selection-card {
              flex-direction: column !important;
              height: auto !important;
              width: 100% !important;
              border-radius: 32px !important;
              padding-bottom: 20px;
              margin: 0 auto;
            }
            .role-grid {
              grid-template-columns: 1fr !important; /* Stack Student/Counselor vertically */
            }
            .login-image-side {
              display: block !important;
              height: 200px !important;
              width: 100% !important;
              background-size: cover !important;
              background-position: center !important;
              border-radius: 0 0 32px 32px !important;
              order: 2; /* Move image below text on mobile */
            }
            .login-text-side {
              padding: 40px 24px !important;
              order: 1;
            }
            .auth-card {
              margin: 0 15px !important; /* Space from left and right */
              padding: 40px 24px !important;
            }
            h1 {
              font-size: 2.5rem !important;
            }
            p {
              font-size: 1.1rem !important;
            }
          }

          .role-option:hover {
            transform: translateY(-5px);
            background: white !important;
            border-color: #fd1d1d !important;
            box-shadow: 0 15px 30px rgba(253, 29, 29, 0.08);
          }
        `}</style>
      </div>
    );
  }

  const isEmbedded = window !== window.top;

  // ── Auth Action Screen ─────────────────────────────────────────────────────
  return (
    <div className="login-wrapper" style={{
      background: 'linear-gradient(135deg, #f3e8ff 0%, #fce7f3 50%, #ffedd5 100%)',
      minHeight: '100vh', display: 'flex', justifyContent: 'center',
      alignItems: 'center', fontFamily: "'Outfit', sans-serif"
    }}>
      <div className="auth-card" style={{
        width: '100%', maxWidth: '450px', padding: '60px 40px',
        borderRadius: '40px', background: 'rgba(255, 250, 245, 0.98)',
        textAlign: 'center', position: 'relative',
        boxShadow: '0 30px 60px -12px rgba(0,0,0,0.1)',
        animation: 'slideUp 0.6s cubic-bezier(0.2, 0.8, 0.2, 1)',
        border: '1px solid rgba(255, 255, 255, 0.5)'
      }}>
        <button
          onClick={() => setRole(null)}
          style={{
            background: 'rgba(0,0,0,0.03)', border: 'none', color: '#64748b',
            cursor: 'pointer', position: 'absolute', top: '30px', left: '30px',
            fontSize: '1.2rem', width: '40px', height: '40px', borderRadius: '50%',
            display: 'flex', alignItems: 'center', justifyContent: 'center', transition: '0.3s'
          }}
          className="back-btn"
        >
          ←
        </button>

        <h1 style={{ color: '#1e293b', fontSize: '2.5rem', fontWeight: '900', marginBottom: '10px' }}>
          {role === 'admin' ? 'Counselor' : 'Student'}
        </h1>
        <p style={{ color: '#64748b', fontSize: '1.1rem', marginBottom: '40px' }}>
          Secure access to your portal
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {isEmbedded ? (
            <button
              className="auth-btn"
              onClick={() => window.open(window.location.href, '_blank')}
              style={{
                background: 'linear-gradient(to right, #833ab4, #fd1d1d, #fcb045)',
                color: 'white', fontWeight: '800', padding: '18px', border: 'none',
                borderRadius: '16px', cursor: 'pointer',
                fontSize: '1.1rem', transition: '0.3s',
                boxShadow: '0 10px 20px rgba(253, 29, 29, 0.2)'
              }}
            >
              Open App in Full Screen
            </button>
          ) : (
            <button
              className="auth-btn"
              onClick={() => handleGoogleLogin('signin')}
              disabled={isLoggingIn}
              style={{
                background: 'linear-gradient(to right, #833ab4, #fd1d1d, #fcb045)',
                color: 'white', fontWeight: '800', padding: '18px', border: 'none',
                borderRadius: '16px', cursor: isLoggingIn ? 'not-allowed' : 'pointer',
                fontSize: '1.1rem', transition: '0.3s',
                boxShadow: '0 10px 20px rgba(253, 29, 29, 0.2)',
                opacity: isLoggingIn ? 0.7 : 1
              }}
            >
              {isLoggingIn ? 'Logging in...' : (role === 'student' ? 'Sign In with Google' : 'Continue with Google')}
            </button>
          )}

          {role === 'student' && !isEmbedded && (
            <button
              className="create-btn"
              onClick={() => handleGoogleLogin('create')}
              disabled={isLoggingIn}
              style={{
                background: 'rgba(0,0,0,0.03)', color: '#1e293b', fontWeight: '700',
                padding: '16px', border: '1px solid rgba(0,0,0,0.05)',
                borderRadius: '16px', cursor: isLoggingIn ? 'not-allowed' : 'pointer',
                fontSize: '1rem', transition: '0.3s',
                opacity: isLoggingIn ? 0.7 : 1
              }}
            >
              {isLoggingIn ? 'Please wait...' : 'Create Account'}
            </button>
          )}

          {isEmbedded && (
            <p style={{ color: '#ef4444', fontSize: '0.9rem', marginTop: '10px', fontWeight: '600' }}>
              Google Login is blocked inside iframes. Please open in full screen first!
            </p>
          )}

          <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '15px' }}>
            By continuing, you agree to our Terms of Service.
          </p>
        </div>
      </div>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&display=swap');
        @keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        .back-btn:hover { background: #f1f5f9; color: #1e293b; transform: scale(1.1); }
        .auth-btn:hover { transform: translateY(-3px); box-shadow: 0 15px 30px rgba(253, 29, 29, 0.4); }
        .create-btn:hover { background: rgba(0,0,0,0.06); transform: translateY(-2px); }
      `}</style>
    </div>
  );
}
