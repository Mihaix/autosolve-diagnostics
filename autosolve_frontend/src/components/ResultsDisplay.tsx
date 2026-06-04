import React, { useState } from 'react';
import type { DiagnosticResponse, DiagnosticRequest } from '../types';

interface ResultsDisplayProps {
  request: DiagnosticRequest;
  response: DiagnosticResponse;
}

export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ request, response }) => {
  const [completedSteps, setCompletedSteps] = useState<Record<number, boolean>>({});

  // Parse lines for core cause & solutions
  const causes = response.core_cause.split('\n').filter(line => line.trim() !== '');
  const steps = response.solution.split('\n').filter(line => line.trim() !== '');

  const toggleStep = (idx: number) => {
    setCompletedSteps(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  return (
    <div className="animate-slide-in" style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '1.5rem'
    }}>
      {/* Header Summary */}
      <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: 'var(--radius-md)' }}>
        <span className="form-label" style={{ fontSize: '0.7rem' }}>Vehicle Context</span>
        <h3 style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0.2rem 0' }}>
          {request.year} {request.make} {request.model}
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', fontStyle: 'italic' }}>
          Query: "{request.query}"
        </p>
      </div>

      {/* Section 1: Problem Explanation */}
      <div className="glass-panel" style={{ padding: '2rem', borderRadius: 'var(--radius-md)' }}>
        <h3 style={{ fontSize: '1.15rem', color: 'var(--color-primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          📝 Problem Explanation
        </h3>
        <p style={{ color: 'var(--text-main)', fontSize: '0.95rem', lineHeight: '1.7' }}>
          {response.problem_elaboration}
        </p>
      </div>

      {/* Section 2: Core Cause */}
      <div className="glass-panel" style={{ padding: '2rem', borderRadius: 'var(--radius-md)' }}>
        <h3 style={{ fontSize: '1.15rem', color: 'var(--color-secondary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          ⚠️ Identified Core Causes
        </h3>
        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {causes.map((cause, idx) => (
            <li key={idx} style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              fontSize: '0.95rem',
              background: 'rgba(255, 255, 255, 0.01)',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-sm)',
              borderLeft: '3px solid var(--color-secondary)'
            }}>
              <span style={{ color: 'var(--color-secondary)', fontWeight: 'bold' }}>•</span>
              <span>{cause.replace(/^[-•\d.\s]+/, '')}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Section 3: Step-by-Step Solution */}
      <div className="glass-panel" style={{ padding: '2rem', borderRadius: 'var(--radius-md)' }}>
        <h3 style={{ fontSize: '1.15rem', color: 'var(--color-primary)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          🔧 Step-by-Step Repair Procedure
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {steps.map((step, idx) => {
            const cleanStep = step.replace(/^[\d.\s]+/, ''); // remove numbering
            const isDone = !!completedSteps[idx];
            
            return (
              <div 
                key={idx}
                onClick={() => toggleStep(idx)}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '1rem',
                  padding: '1rem',
                  borderRadius: 'var(--radius-md)',
                  background: isDone ? 'rgba(16, 185, 129, 0.04)' : 'rgba(255, 255, 255, 0.02)',
                  border: isDone ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid var(--border-color)',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)'
                }}
                onMouseEnter={(e) => {
                  if (!isDone) e.currentTarget.style.borderColor = 'var(--color-primary)';
                }}
                onMouseLeave={(e) => {
                  if (!isDone) e.currentTarget.style.borderColor = 'var(--border-color)';
                }}
              >
                <div style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: 'var(--radius-sm)',
                  border: isDone ? '2px solid var(--color-success)' : '2px solid var(--text-dark)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  backgroundColor: isDone ? 'var(--color-success)' : 'transparent',
                  flexShrink: 0,
                  transition: 'all var(--transition-fast)'
                }}>
                  {isDone && <span style={{ color: '#fff', fontSize: '0.75rem', fontWeight: 'bold' }}>✓</span>}
                </div>
                <span style={{
                  fontSize: '0.95rem',
                  color: isDone ? 'var(--text-muted)' : 'var(--text-main)',
                  textDecoration: isDone ? 'line-through' : 'none',
                  transition: 'color var(--transition-fast)'
                }}>
                  {cleanStep}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Section 4: Source Citations */}
      {response.sources.length > 0 && (
        <div className="glass-panel" style={{ padding: '2rem', borderRadius: 'var(--radius-md)' }}>
          <h3 style={{ fontSize: '1.15rem', color: 'var(--text-main)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            📚 Grounded Retrieval Sources
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {response.sources.map((source, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                fontSize: '0.85rem',
                background: 'rgba(255, 255, 255, 0.02)',
                padding: '0.75rem 1rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-color)',
                color: 'var(--text-muted)'
              }}>
                <span style={{ fontSize: '1.1rem' }}>📄</span>
                <span>{source}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
