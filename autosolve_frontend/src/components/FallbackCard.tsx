import React from 'react';
import type { DiagnosticRequest, DiagnosticResponse } from '../types';

interface FallbackCardProps {
  request: DiagnosticRequest;
  response: DiagnosticResponse;
}

export const FallbackCard: React.FC<FallbackCardProps> = ({ request, response }) => {
  return (
    <div className="glass-panel animate-slide-in" style={{
      padding: '2.5rem',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid rgba(245, 158, 11, 0.3)',
      boxShadow: 'var(--shadow-lg), var(--shadow-glow-warning)',
      display: 'flex',
      flexDirection: 'column',
      gap: '1.5rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          width: '50px',
          height: '50px',
          borderRadius: '50%',
          backgroundColor: 'rgba(245, 158, 11, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '1.75rem',
          color: 'var(--color-warning)',
          border: '1px solid rgba(245, 158, 11, 0.3)'
        }}>
          ⚠️
        </div>
        <div>
          <span style={{
            fontSize: '0.75rem',
            color: 'var(--color-warning)',
            fontWeight: 700,
            textTransform: 'uppercase',
            letterSpacing: '0.1em'
          }}>
            Zero-Hallucination Fallback Triggered
          </span>
          <h3 style={{ fontSize: '1.35rem', fontWeight: 700, margin: 0 }}>
            Unverified Vehicle Fault Combination
          </h3>
        </div>
      </div>

      <div style={{
        background: 'rgba(0, 0, 0, 0.2)',
        padding: '1.25rem 1.5rem',
        borderRadius: 'var(--radius-md)',
        borderLeft: '4px solid var(--color-warning)',
        fontSize: '0.95rem',
        lineHeight: '1.6',
        color: 'var(--text-main)'
      }}>
        <strong>System Notice:</strong> The vector database search did not return any certified documentation chunks matching <strong>{request.make} {request.model} ({request.year})</strong> for the query <strong>"{request.query}"</strong>. To prevent safety risks and hallucinated torque values or part specifications, the LLM generator has degraded to a secure non-technical advice fallback.
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <h4 style={{ fontSize: '1rem', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
            Recommended Action:
          </h4>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            {response.solution}
          </p>
        </div>

        <div style={{
          borderTop: '1px solid var(--border-color)',
          paddingTop: '1rem',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '1.5rem'
        }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dark)' }}>
            <strong>Confidence Score:</strong> {response.confidence_score}
          </div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-dark)' }}>
            <strong>Safety Guardrails:</strong> Enforced (Zero Hallucinations)
          </div>
        </div>
      </div>
    </div>
  );
};
