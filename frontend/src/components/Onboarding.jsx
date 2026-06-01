import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Onboarding({ authToken }) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    nickname: '',
    phone: '',
    birthday: '',
    gender: '',
    education: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/user/onboarding', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        navigate('/chat');
      }
    } catch (err) {
      console.error(err);
      alert('Failed to save profile');
    }
  };

  return (
    <div className="onboarding-page" style={{ 
      background: 'linear-gradient(135deg, #f3e8ff 0%, #fce7f3 50%, #fff1f1 100%)',
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '40px 20px',
      fontFamily: "'Outfit', sans-serif"
    }}>
      <div className="onboarding-card" style={{ 
        width: '100%', 
        maxWidth: '700px', 
        background: 'rgba(255,255,255,0.9)', 
        backdropFilter: 'blur(30px)', 
        WebkitBackdropFilter: 'blur(30px)',
        borderRadius: '32px', 
        padding: '50px', 
        boxShadow: '0 40px 100px rgba(0,0,0,0.1)',
        border: '1px solid rgba(255,255,255,0.8)',
        position: 'relative'
      }}>
        <style>{`
          @media (max-width: 600px) {
            .onboarding-card {
              padding: 30px 20px !important;
              border-radius: 0 !important;
              height: 100vh;
              overflow-y: auto;
            }
            .onboarding-card h2 {
              font-size: 1.8rem !important;
            }
            .grid-row {
              grid-template-columns: 1fr !important;
              gap: 15px !important;
            }
          }
        `}</style>
        <div style={{ textAlign: 'center', marginBottom: '50px' }}>
          <h1 style={{ 
            fontSize: '3rem', 
            fontWeight: '900', 
            background: 'linear-gradient(to right, #833ab4, #fd1d1d, #fcb045)', 
            WebkitBackgroundClip: 'text', 
            WebkitTextFillColor: 'transparent',
            marginBottom: '10px',
            letterSpacing: '-1.5px'
          }}>
            Personalize Your Experience ✨
          </h1>
          <p style={{ color: '#64748b', fontSize: '1.2rem', fontWeight: '400' }}>
            Help MyAlly understand you better so we can provide the best support.
          </p>
        </div>
        
        <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '20px' }}>
          {/* Row 1: Basic Info */}
          <div className="grid-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
            <div className="form-group">
              <label style={{ color: '#1e293b', fontWeight: '700', marginBottom: '8px', display: 'block', fontSize: '0.95rem' }}>
                Nickname
              </label>
              <input 
                type="text" 
                name="nickname" 
                className="premium-input" 
                placeholder="How should I call you?"
                value={formData.nickname} 
                onChange={handleChange} 
                required 
                style={{ width: '100%', padding: '14px 18px', borderRadius: '16px', background: 'rgba(255, 255, 255, 0.6)', border: '1px solid #e2e8f0', color: '#1e293b', fontSize: '1rem', outline: 'none' }}
              />
            </div>
            <div className="form-group">
              <label style={{ color: '#1e293b', fontWeight: '700', marginBottom: '8px', display: 'block', fontSize: '0.95rem' }}>
                Phone Number
              </label>
              <input 
                type="tel" 
                name="phone" 
                className="premium-input" 
                placeholder="+91..."
                value={formData.phone} 
                onChange={handleChange} 
                required 
                style={{ width: '100%', padding: '14px 18px', borderRadius: '16px', background: 'rgba(255, 255, 255, 0.6)', border: '1px solid #e2e8f0', color: '#1e293b', fontSize: '1rem', outline: 'none' }}
              />
            </div>
            <div className="form-group">
              <label style={{ color: '#1e293b', fontWeight: '700', marginBottom: '8px', display: 'block', fontSize: '0.95rem' }}>Gender</label>
              <select 
                name="gender" 
                className="premium-input" 
                value={formData.gender} 
                onChange={handleChange} 
                required
                style={{ width: '100%', padding: '14px 18px', borderRadius: '16px', background: 'rgba(255,255,255,0.6)', border: '1px solid #e2e8f0', color: '#1e293b', cursor: 'pointer', outline: 'none', fontSize: '1rem' }}
              >
                <option value="">Select...</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Non-binary">Non-binary</option>
                <option value="Prefer not to say">Prefer not to say</option>
              </select>
            </div>
          </div>

          {/* Row 2: Secondary Info */}
          <div className="grid-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <div className="form-group">
              <label style={{ color: '#1e293b', fontWeight: '700', marginBottom: '8px', display: 'block', fontSize: '0.95rem' }}>Birthday</label>
              <input 
                type="date" 
                name="birthday" 
                className="premium-input" 
                value={formData.birthday} 
                onChange={handleChange} 
                required
                style={{ width: '100%', padding: '14px 18px', borderRadius: '16px', background: 'rgba(255, 255, 255, 0.6)', border: '1px solid #e2e8f0', color: '#1e293b', fontSize: '1rem', outline: 'none' }}
              />
            </div>
            <div className="form-group">
              <label style={{ color: '#1e293b', fontWeight: '700', marginBottom: '8px', display: 'block', fontSize: '0.95rem' }}>Education</label>
              <input 
                type="text" 
                name="education" 
                className="premium-input"
                placeholder="College Student..."
                value={formData.education} 
                onChange={handleChange} 
                required
                style={{ width: '100%', padding: '14px 18px', borderRadius: '16px', background: 'rgba(255,255,255,0.6)', border: '1px solid #e2e8f0', color: '#1e293b', outline: 'none', fontSize: '1rem' }}
              />
            </div>
          </div>



          <button 
            type="submit" 
            className="start-journey-btn" 
            style={{ 
              marginTop: '10px', 
              padding: '16px', 
              fontSize: '1.2rem', 
              fontWeight: '900', 
              background: 'linear-gradient(to right, #833ab4, #fd1d1d, #fcb045)',
              border: 'none',
              borderRadius: '16px',
              color: 'white',
              cursor: 'pointer',
              transition: '0.4s',
              boxShadow: '0 10px 20px rgba(253, 29, 29, 0.2)'
            }}
          >
            Start My Journey
          </button>
        </form>
      </div>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&display=swap');
        @keyframes slideUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        .premium-input:focus {
          border-color: #fd1d1d !important;
          background: white !important;
          box-shadow: 0 0 0 4px rgba(253, 29, 29, 0.1);
        }
        .start-journey-btn:hover {
          transform: translateY(-4px);
          box-shadow: 0 20px 40px rgba(253, 29, 29, 0.5);
        }
        .start-journey-btn:active {
          transform: translateY(0);
        }
      `}</style>
    </div>
  );
}
