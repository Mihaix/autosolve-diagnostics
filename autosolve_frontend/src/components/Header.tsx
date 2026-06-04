import React from 'react';
import { CarLogo } from './CarLogo';

export const Header: React.FC = () => {
  return (
    <header className="animate-fade-in" style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem 0.5rem 1rem 0.5rem',
      marginBottom: '3rem',
      marginTop: '1.5rem',
      gap: '1.5rem'
    }}>
      <CarLogo width={180} height={125} />
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
        <h1 style={{ 
          fontSize: '3.5rem', 
          fontWeight: 950, 
          margin: 0,
          fontStyle: 'italic',
          letterSpacing: '-0.05em',
          transform: 'skewX(-10deg)',
          display: 'inline-block',
          lineHeight: '1.05'
        }} className="text-gradient">
          AUTOSOLVE
        </h1>
        <div style={{ 
          fontSize: '0.9rem', 
          color: 'var(--text-muted)', 
          letterSpacing: '0.28em', 
          textTransform: 'uppercase', 
          fontWeight: 800,
          marginTop: '0.2rem',
          fontStyle: 'italic'
        }}>
          Engine diagnostics
        </div>
      </div>
    </header>
  );
};
