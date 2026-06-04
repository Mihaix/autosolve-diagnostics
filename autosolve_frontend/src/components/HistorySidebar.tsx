import React from 'react';
import type { HistoryItem } from '../types';

interface HistorySidebarProps {
  history: HistoryItem[];
  onSelect: (item: HistoryItem) => void;
  onClear: () => void;
  selectedId?: string;
}

export const HistorySidebar: React.FC<HistorySidebarProps> = ({ history, onSelect, onClear, selectedId }) => {
  return (
    <div className="glass-panel animate-fade-in" style={{
      padding: '1.5rem',
      borderRadius: 'var(--radius-lg)',
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
      height: '100%',
      maxHeight: '75vh',
      overflowY: 'auto'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 750, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          ⏱️ History
        </h3>
        {history.length > 0 && (
          <button 
            onClick={onClear}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--color-danger)',
              fontSize: '0.75rem',
              fontWeight: 600,
              cursor: 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.05em'
            }}
          >
            Clear All
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '2rem 1rem',
          color: 'var(--text-dark)',
          fontSize: '0.85rem',
          border: '1px dashed var(--border-color)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem'
        }}>
          <span>📭</span>
          <span>No search history yet. Your diagnostics will appear here.</span>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {history.map((item) => {
            const isSelected = selectedId === item.id;
            return (
              <div
                key={item.id}
                onClick={() => onSelect(item)}
                style={{
                  padding: '1rem',
                  borderRadius: 'var(--radius-md)',
                  background: isSelected ? 'rgba(56, 189, 248, 0.08)' : 'rgba(255, 255, 255, 0.01)',
                  border: isSelected ? '1px solid var(--color-primary)' : '1px solid var(--border-color)',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.transform = 'translateX(4px)';
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.15)';
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.transform = 'translateX(0)';
                    e.currentTarget.style.borderColor = 'var(--border-color)';
                    e.currentTarget.style.background = 'rgba(255, 255, 255, 0.01)';
                  }
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.25rem' }}>
                  <span style={{
                    fontSize: '0.85rem',
                    fontWeight: 700,
                    color: isSelected ? 'var(--color-primary)' : 'var(--text-main)'
                  }}>
                    {item.request.make} {item.request.model}
                  </span>
                  <span style={{
                    fontSize: '0.7rem',
                    color: 'var(--text-dark)',
                    fontWeight: 500
                  }}>
                    {item.request.year}
                  </span>
                </div>
                <div style={{
                  fontSize: '0.8rem',
                  color: 'var(--text-muted)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  marginBottom: '0.4rem'
                }}>
                  {item.request.query}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{
                    fontSize: '0.7rem',
                    color: item.response.is_fallback ? 'var(--color-warning)' : 'var(--color-success)',
                    fontWeight: 600,
                    textTransform: 'uppercase'
                  }}>
                    {item.response.is_fallback ? 'Fallback' : `${Math.round(item.response.confidence_score * 100)}% Conf`}
                  </span>
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-dark)' }}>
                    {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
