import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';

interface SettingsMenuProps {
  darkMode: boolean;
  onToggleDarkMode: () => void;
}

export default function SettingsMenu({ darkMode, onToggleDarkMode }: SettingsMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  return (
    <div ref={menuRef} style={{ position: 'relative' }}>
      {/* Settings Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          padding: '10px 16px',
          borderRadius: '8px',
          background: darkMode 
            ? 'rgba(255, 255, 255, 0.1)' 
            : 'rgba(255, 255, 255, 0.95)',
          border: darkMode
            ? '1px solid rgba(255, 255, 255, 0.2)'
            : '1px solid rgba(0, 0, 0, 0.1)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontSize: '14px',
          fontWeight: 600,
          color: darkMode ? '#e2e8f0' : '#475569',
          transition: 'all 0.2s',
          backdropFilter: 'blur(10px)',
          zIndex: 1100,
          boxShadow: darkMode
            ? '0 2px 8px rgba(0, 0, 0, 0.3)'
            : '0 2px 8px rgba(0, 0, 0, 0.1)',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = darkMode
            ? 'rgba(255, 255, 255, 0.15)'
            : 'rgba(255, 255, 255, 1)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = darkMode
            ? 'rgba(255, 255, 255, 0.1)'
            : 'rgba(255, 255, 255, 0.95)';
        }}
      >
        <svg 
          width="16" 
          height="16" 
          viewBox="0 0 24 24" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round"
        >
          <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
        Settings
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          style={{
            position: 'fixed',
            top: '60px',
            right: '20px',
            width: '200px',
            background: darkMode ? '#1e293b' : 'white',
            borderRadius: '8px',
            boxShadow: darkMode
              ? '0 8px 24px rgba(0, 0, 0, 0.5)'
              : '0 8px 24px rgba(0, 0, 0, 0.15)',
            border: darkMode
              ? '1px solid rgba(255, 255, 255, 0.1)'
              : '1px solid rgba(0, 0, 0, 0.1)',
            padding: '6px',
            zIndex: 1100,
            animation: 'slideDown 0.2s ease-out',
          }}
        >
          <style jsx>{`
            @keyframes slideDown {
              from {
                opacity: 0;
                transform: translateY(-10px);
              }
              to {
                opacity: 1;
                transform: translateY(0);
              }
            }
          `}</style>

          {/* Home */}
          <Link
            href="/"
            onClick={() => setIsOpen(false)}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '10px 12px',
              borderRadius: '6px',
              background: 'transparent',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 500,
              color: darkMode ? '#e2e8f0' : '#334155',
              transition: 'all 0.2s',
              textDecoration: 'none',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = darkMode
                ? 'rgba(255, 255, 255, 0.08)'
                : 'rgba(0, 0, 0, 0.04)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            Home
          </Link>

          {/* Dark Mode Toggle */}
          <button
            onClick={() => {
              onToggleDarkMode();
            }}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 12px',
              borderRadius: '6px',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 500,
              color: darkMode ? '#e2e8f0' : '#334155',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = darkMode
                ? 'rgba(255, 255, 255, 0.08)'
                : 'rgba(0, 0, 0, 0.04)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            <span>{darkMode ? 'Dark' : 'Light'}</span>
            <div
              style={{
                width: '38px',
                height: '20px',
                borderRadius: '10px',
                background: darkMode ? '#667eea' : '#cbd5e1',
                position: 'relative',
                transition: 'all 0.3s',
              }}
            >
              <div
                style={{
                  width: '16px',
                  height: '16px',
                  borderRadius: '50%',
                  background: 'white',
                  position: 'absolute',
                  top: '2px',
                  left: darkMode ? '20px' : '2px',
                  transition: 'all 0.3s',
                  boxShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
                }}
              />
            </div>
          </button>

          {/* About */}
          <Link
            href="/about"
            onClick={() => setIsOpen(false)}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '10px 12px',
              borderRadius: '6px',
              background: 'transparent',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 500,
              color: darkMode ? '#e2e8f0' : '#334155',
              transition: 'all 0.2s',
              textDecoration: 'none',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = darkMode
                ? 'rgba(255, 255, 255, 0.08)'
                : 'rgba(0, 0, 0, 0.04)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            About
          </Link>
        </div>
      )}
    </div>
  );
}
