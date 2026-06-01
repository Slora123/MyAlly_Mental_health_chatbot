import { useState, useRef, useEffect } from 'react';
import { THEMES } from '../themes';
import styles from './Header.module.css';
import { botDefault, botFemale, botMale } from '../assets/images.js';

// Keys to store in Firestore — resolved back to images by App.jsx resolveAvatar()
const BOT_AVATAR_OPTIONS = [
  { key: 'female', img: botFemale },
  { key: 'male',   img: botMale   },
  { key: 'default', img: '/logo.png' },
];
const USER_AVATAR_OPTIONS = [
  { key: 'female', img: botFemale },
  { key: 'male',   img: botMale   },
];

export default function Header({ theme, onSetTheme, userEmail, authToken, onLogout, userProfile, myAllyAvatar, setMyAllyAvatar, userAvatar, setUserAvatar }) {
  const [themeOpen, setThemeOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const themeRef = useRef(null);
  const profileRef = useRef(null);
  const fileInputRef = useRef(null);
  const t = THEMES[theme];

  // Resolve bot avatar
  const botImg = myAllyAvatar || '/logo.png';

  // Get initials for user circle if no custom avatar
  const initials = userEmail ? userEmail.charAt(0).toUpperCase() : '?';

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e) => {
      if (themeRef.current && !themeRef.current.contains(e.target)) setThemeOpen(false);
      if (profileRef.current && !profileRef.current.contains(e.target)) setProfileOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        // Create an image element to draw onto a canvas for resizing
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          const MAX_WIDTH = 256;
          const MAX_HEIGHT = 256;
          let width = img.width;
          let height = img.height;

          if (width > height) {
            if (width > MAX_WIDTH) {
              height = Math.round(height *= MAX_WIDTH / width);
              width = MAX_WIDTH;
            }
          } else {
            if (height > MAX_HEIGHT) {
              width = Math.round(width *= MAX_HEIGHT / height);
              height = MAX_HEIGHT;
            }
          }

          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);

          // Compress image down to a smaller JPEG to ensure it fits in Firestore (1MB limit)
          const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
          setUserAvatar(dataUrl); // This will call handleSaveProfile in App.jsx
        };
        img.src = reader.result;
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <header className={styles.header}>
      {/* Left — Branding + Logo */}
      <div className={styles.profile}>
        <div className={styles.avatar} style={{ overflow: 'hidden', border: '2px solid white' }}>
          <img src={botImg} alt="MyAlly" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </div>
        <div className={styles.info}>
          <h2 className={styles.name}>MyAlly</h2>
          <p className={styles.status}>
            <span className={styles.onlineDot} aria-hidden="true" />
            <span id="header-status">{t.status}</span>
          </p>
        </div>
      </div>

      {/* Right — Theme Picker + Profile Circle */}
      <div className={styles.rightSection}>

        {/* Theme Picker */}
        <div className={styles.pickerWrap} ref={themeRef}>
          <button
            className={styles.themeBtn}
            onClick={() => { setThemeOpen((o) => !o); setProfileOpen(false); }}
            aria-expanded={themeOpen}
            aria-label="Change theme"
          >
            <span>{t.statusIcon}</span>
            <span className={styles.themeName}>{t.name}</span>
          </button>

          {themeOpen && (
            <div className={`${styles.dropdown} glass`} role="listbox">
              {Object.values(THEMES).map((th) => (
                <button
                  key={th.id}
                  className={`${styles.themeOption} ${theme === th.id ? styles.active : ''}`}
                  role="option"
                  aria-selected={theme === th.id}
                  onClick={() => { onSetTheme(th.id); setThemeOpen(false); }}
                >
                  <span>{th.icon}</span>
                  <span>{th.name}</span>
                  {theme === th.id && <span className={styles.checkMark}>✓</span>}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Profile Circle */}
        {userEmail && (
          <div className={styles.profileWrap} ref={profileRef}>
            <button
              id="profile-btn"
              className={styles.profileCircle}
              onClick={() => { setProfileOpen((o) => !o); setThemeOpen(false); }}
              aria-label="Profile menu"
              title={userEmail}
              style={{ overflow: 'hidden' }}
            >
              {userAvatar ? (
                <img src={userAvatar} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              ) : initials}
            </button>

            {profileOpen && (
              <div className={styles.profileDropdown} style={{ minWidth: '300px' }}>
                <div className={styles.profileEmailRow}>
                  <span className={styles.profileEmail}>{userEmail}</span>
                </div>
                
                <div className={styles.profileDivider} />
                
                {/* Change MyAlly Avatar */}
                <div style={{ padding: '8px 10px' }}>
                  <p style={{ fontSize: '11px', fontWeight: 800, color: 'rgba(0,0,0,0.4)', marginBottom: '8px', textTransform: 'uppercase' }}>Change MyAlly Avatar</p>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {BOT_AVATAR_OPTIONS.map(({ key, img }) => (
                      <button 
                        key={key}
                        onClick={() => setMyAllyAvatar(key)}
                        style={{ width: '40px', height: '40px', borderRadius: '50%', overflow: 'hidden', border: myAllyAvatar === img ? '2px solid #f07060' : '2px solid transparent', cursor: 'pointer', padding: 0 }}
                      >
                        <img src={img} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      </button>
                    ))}
                  </div>
                </div>

                <div className={styles.profileDivider} />

                {/* Change My Profile Avatar */}
                <div style={{ padding: '8px 10px' }}>
                  <p style={{ fontSize: '11px', fontWeight: 800, color: 'rgba(0,0,0,0.4)', marginBottom: '8px', textTransform: 'uppercase' }}>Your Avatar</p>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {USER_AVATAR_OPTIONS.map(({ key, img }) => (
                      <button 
                        key={key}
                        onClick={() => setUserAvatar(key)}
                        style={{ width: '40px', height: '40px', borderRadius: '50%', overflow: 'hidden', border: userAvatar === img ? '2px solid #f07060' : '2px solid transparent', cursor: 'pointer', padding: 0 }}
                      >
                        <img src={img} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      </button>
                    ))}
                    <button 
                      onClick={() => { fileInputRef.current.click(); }}
                      style={{ width: '40px', height: '40px', borderRadius: '50%', border: '2px solid #eee', background: 'white', color: '#666', fontSize: '18px', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                      title="Upload custom photo"
                    >
                      +
                    </button>
                    <input 
                      type="file" 
                      ref={fileInputRef} 
                      style={{ display: 'none' }} 
                      accept="image/*"
                      onChange={handleFileUpload}
                    />
                    {userAvatar && (
                      <button 
                        onClick={() => setUserAvatar(null)}
                        style={{ background: 'none', border: 'none', color: '#f07060', fontSize: '10px', fontWeight: 700, cursor: 'pointer', marginLeft: 'auto' }}
                      >
                        Reset
                      </button>
                    )}
                  </div>
                </div>

                <div className={styles.profileDivider} />
                
                <button
                  id="logout-btn"
                  className={styles.logoutBtn}
                  onClick={() => { setProfileOpen(false); onLogout(); }}
                >
                  Log out
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
