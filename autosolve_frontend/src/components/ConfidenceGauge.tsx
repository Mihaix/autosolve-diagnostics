import React from 'react';

interface ConfidenceGaugeProps {
  score: number;
}

export const ConfidenceGauge: React.FC<ConfidenceGaugeProps> = ({ score }) => {
  const percentage = Math.round(score * 100);
  
  // Dynamic color and label settings
  let color = 'var(--color-danger)';
  let label = 'LOW RAG POWER';
  let desc = 'Zero manual matches';

  if (score >= 0.75) {
    color = 'var(--color-success)';
    label = 'GROUNDED LIMIT';
    desc = 'Direct manual verification';
  } else if (score >= 0.20) {
    color = 'var(--color-accent)';
    label = 'BOOST STAGE';
    desc = 'High fuzzy match';
  } else {
    color = 'var(--color-secondary)';
    label = 'SAFE REDLINE';
    desc = 'Degraded fallback mode';
  }

  // Dashboard configuration
  // -135 deg to +135 deg (270 degree sweep)
  const startAngle = -135;
  const sweepAngle = 270;
  const needleRotation = startAngle + (score * sweepAngle);

  // Generate ticks around the tachometer ring
  const ticks = [];
  const totalTicks = 11; // 0 to 100% in 10% steps
  for (let i = 0; i < totalTicks; i++) {
    const tickPercent = i / (totalTicks - 1);
    const angle = startAngle + (tickPercent * sweepAngle);
    // Draw tick line from radius 68 to 74
    const rad = ((angle - 90) * Math.PI) / 180.0;
    const x1 = 100 + 66 * Math.cos(rad);
    const y1 = 100 + 66 * Math.sin(rad);
    const x2 = 100 + 74 * Math.cos(rad);
    const y2 = 100 + 74 * Math.sin(rad);
    
    // Label position just inside the tick
    const lx = 100 + 52 * Math.cos(rad);
    const ly = 100 + 52 * Math.sin(rad) + 3; // offset slightly for baseline vertical alignment
    
    ticks.push({ x1, y1, x2, y2, lx, ly, label: `${i}` }); // 0 to 10 represent RPM-style markings
  }

  return (
    <div className="glass-panel animate-slide-in" style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      padding: '1.75rem 1.5rem',
      borderRadius: 'var(--radius-lg)',
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      maxWidth: '260px',
      margin: '0 auto',
      position: 'relative',
      boxShadow: 'var(--shadow-lg)'
    }}>
      {/* Decorative Top Performance Plate */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: '50%',
        transform: 'translateX(-50%)',
        background: 'linear-gradient(90deg, var(--color-secondary), var(--color-primary))',
        padding: '0.15rem 1.5rem',
        borderRadius: '0 0 var(--radius-sm) var(--radius-sm)',
        fontSize: '0.6rem',
        fontWeight: 900,
        letterSpacing: '0.15em',
        textTransform: 'uppercase',
        color: '#fff',
        boxShadow: '0 2px 8px rgba(255, 94, 0, 0.3)'
      }}>
        Tachometer v2.0
      </div>

      <span className="form-label" style={{ marginTop: '0.5rem', marginBottom: '1.25rem', fontSize: '0.75rem', fontWeight: 800 }}>
        ⚡ Confidence Boost
      </span>

      <div style={{ position: 'relative', width: '200px', height: '170px' }}>
        <svg width="200" height="200" viewBox="0 0 200 200">
          <defs>
            {/* Speed dial gradients */}
            <linearGradient id="dialGrad" x1="0" y1="1" x2="1" y2="0">
              <stop offset="0%" stopColor="var(--color-primary)" />
              <stop offset="70%" stopColor="var(--color-accent)" />
              <stop offset="100%" stopColor="var(--color-secondary)" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>

          {/* Background Outer Ring */}
          <path 
            d="M 50.5 149.5 A 70 70 0 1 1 149.5 149.5" 
            fill="transparent" 
            stroke="rgba(255, 255, 255, 0.03)" 
            strokeWidth="10" 
            strokeLinecap="round"
          />

          {/* Active Colored Sweep Arc */}
          <path 
            d="M 50.5 149.5 A 70 70 0 1 1 149.5 149.5" 
            fill="transparent" 
            stroke="url(#dialGrad)" 
            strokeWidth="6" 
            strokeDasharray="330"
            // total circumference of 70-radius 270-degree arc is approx 330.
            // Offset controls active filling based on score
            strokeDashoffset={330 - (score * 330)}
            strokeLinecap="round"
            style={{ 
              transition: 'stroke-dashoffset 1s cubic-bezier(0.25, 0.8, 0.25, 1)',
              filter: `drop-shadow(0 0 3px ${color})`
            }}
          />

          {/* Redline high confidence marker (75% to 100%) */}
          <path 
            d="M 120 34 A 70 70 0 0 1 149.5 149.5" 
            fill="transparent" 
            stroke="var(--color-secondary)" 
            strokeWidth="4" 
            strokeDasharray="4 4"
            opacity="0.6"
          />

          {/* Tick Marks & Dashboard Numbers */}
          {ticks.map((tick, idx) => (
            <g key={idx}>
              <line 
                x1={tick.x1} 
                y1={tick.y1} 
                x2={tick.x2} 
                y2={tick.y2} 
                stroke={idx >= 8 ? 'var(--color-secondary)' : 'rgba(255, 255, 255, 0.2)'} 
                strokeWidth={idx % 2 === 0 ? 2 : 1} 
              />
              {idx % 2 === 0 && (
                <text 
                  x={tick.lx} 
                  y={tick.ly} 
                  fill={idx >= 8 ? 'var(--color-secondary)' : 'var(--text-muted)'} 
                  fontSize="8" 
                  fontWeight="800"
                  textAnchor="middle" 
                  fontFamily="var(--font-header)"
                >
                  {tick.label}
                </text>
              )}
            </g>
          ))}

          {/* Tachometer Center cap */}
          <circle cx="100" cy="100" r="14" fill="#0c0c14" stroke="var(--border-color)" strokeWidth="2" />
          <circle cx="100" cy="100" r="6" fill="var(--color-primary)" />

          {/* Animated Speed Needle */}
          <g 
            transform={`rotate(${needleRotation}, 100, 100)`} 
            style={{ transition: 'transform 1.2s cubic-bezier(0.1, 0.8, 0.2, 1)' }}
          >
            {/* Glowing needle body */}
            <line 
              x1="100" 
              y1="100" 
              x2="100" 
              y2="28" 
              stroke="var(--color-primary)" 
              strokeWidth="3.5" 
              strokeLinecap="round" 
              style={{ filter: 'url(#glow)' }}
            />
            {/* Aerodynamic needle tip pointer */}
            <polygon 
              points="97,32 103,32 100,20" 
              fill="var(--color-accent)" 
            />
          </g>

          {/* Central Label for Units */}
          <text 
            x="100" 
            y="130" 
            fill="var(--text-dark)" 
            fontSize="8" 
            fontWeight="950" 
            textAnchor="middle"
            letterSpacing="0.1em"
            fontFamily="var(--font-header)"
          >
            CONF % x10
          </text>
        </svg>

        {/* Digital Readout Panel Overlay */}
        <div style={{
          position: 'absolute',
          bottom: '22px',
          left: '50%',
          transform: 'translateX(-50%)',
          textAlign: 'center'
        }}>
          <span style={{
            fontSize: '1.9rem',
            fontWeight: 950,
            fontFamily: 'var(--font-header)',
            color: 'var(--text-main)',
            fontStyle: 'italic',
            letterSpacing: '-0.02em',
            textShadow: '0 0 10px rgba(255, 94, 0, 0.3)'
          }}>
            {percentage}%
          </span>
        </div>
      </div>

      <div style={{
        marginTop: '0.25rem',
        textAlign: 'center'
      }}>
        <span style={{
          display: 'block',
          fontSize: '0.75rem',
          fontWeight: 900,
          color: color,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          fontStyle: 'italic'
        }}>
          🏁 {label}
        </span>
        <span style={{
          display: 'block',
          fontSize: '0.7rem',
          color: 'var(--text-muted)',
          marginTop: '0.1rem'
        }}>
          {desc}
        </span>
      </div>
    </div>
  );
};
