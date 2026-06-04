import React, { useState } from 'react';
import type { DiagnosticRequest } from '../types';

interface DiagnosticFormProps {
  onSubmit: (request: DiagnosticRequest) => void;
  isLoading: boolean;
}

const COMMON_MAKES = ['Volkswagen', 'Toyota', 'BMW', 'Ford', 'Audi', 'Honda', 'Chevrolet'];
const SUGGESTED_QUERIES = [
  { make: 'Volkswagen', model: 'Golf', year: 2018, query: 'P0420', label: 'VW Golf P0420 (Catalyst Efficiency)' },
  { make: 'Toyota', model: 'Corolla', year: 2015, query: 'P0171', label: 'Toyota Corolla P0171 (System Too Lean)' },
  { make: 'BMW', model: '3-Series', year: 2013, query: 'Oil leak', label: 'BMW 3-Series Oil Leak (N20/N52)' },
];

export const DiagnosticForm: React.FC<DiagnosticFormProps> = ({ onSubmit, isLoading }) => {
  const [make, setMake] = useState('');
  const [model, setModel] = useState('');
  const [year, setYear] = useState<number | ''>('');
  const [query, setQuery] = useState('');

  const [makeSuggestions, setMakeSuggestions] = useState<string[]>([]);
  const [showMakeSuggestions, setShowMakeSuggestions] = useState(false);

  const handleMakeChange = (val: string) => {
    setMake(val);
    if (val.trim() === '') {
      setMakeSuggestions([]);
    } else {
      const filtered = COMMON_MAKES.filter(m =>
        m.toLowerCase().startsWith(val.toLowerCase()) && m.toLowerCase() !== val.toLowerCase()
      );
      setMakeSuggestions(filtered);
    }
  };

  const handleSuggestionClick = (suggestion: typeof SUGGESTED_QUERIES[0]) => {
    setMake(suggestion.make);
    setModel(suggestion.model);
    setYear(suggestion.year);
    setQuery(suggestion.query);
    setShowMakeSuggestions(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!make || !model || !year || !query) return;

    onSubmit({
      make: make.trim(),
      model: model.trim(),
      year: Number(year),
      query: query.trim()
    });
  };

  return (
    <div className="glass-panel animate-slide-in" style={{ padding: '2rem', borderRadius: 'var(--radius-lg)' }}>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

        {/* Helper Test Scenarios */}
        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.75rem 1rem', borderRadius: 'var(--radius-md)', border: '1px dashed var(--border-color)' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: '0.5rem' }}>
            💡 Quick Actions
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {SUGGESTED_QUERIES.map((s, idx) => (
              <button
                key={idx}
                type="button"
                className="btn btn-secondary"
                disabled={isLoading}
                onClick={() => handleSuggestionClick(s)}
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem', borderRadius: 'var(--radius-sm)' }}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Form Inputs Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
          gap: '1rem'
        }}>
          {/* Make */}
          <div className="form-group" style={{ position: 'relative' }}>
            <label className="form-label">Make</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., Volkswagen"
              value={make}
              onChange={(e) => handleMakeChange(e.target.value)}
              onFocus={() => setShowMakeSuggestions(true)}
              onBlur={() => setTimeout(() => setShowMakeSuggestions(false), 200)}
              required
              disabled={isLoading}
            />
            {showMakeSuggestions && makeSuggestions.length > 0 && (
              <div style={{
                position: 'absolute',
                top: '100%',
                left: 0,
                right: 0,
                background: '#1e293b',
                border: '1px solid var(--border-color)',
                borderRadius: '0 0 var(--radius-md) var(--radius-md)',
                boxShadow: 'var(--shadow-lg)',
                zIndex: 10,
                maxHeight: '150px',
                overflowY: 'auto'
              }}>
                {makeSuggestions.map((suggestion) => (
                  <div
                    key={suggestion}
                    onMouseDown={() => {
                      setMake(suggestion);
                      setMakeSuggestions([]);
                    }}
                    style={{
                      padding: '0.6rem 1rem',
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                      color: 'var(--text-main)',
                      transition: 'background var(--transition-fast)'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    {suggestion}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Model */}
          <div className="form-group">
            <label className="form-label">Model</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., Golf"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          {/* Year */}
          <div className="form-group">
            <label className="form-label">Year</label>
            <input
              type="number"
              className="form-input"
              placeholder="e.g., 2018"
              value={year}
              onChange={(e) => setYear(e.target.value === '' ? '' : Number(e.target.value))}
              min={1980}
              max={2027}
              required
              disabled={isLoading}
            />
          </div>
        </div>

        {/* Query Input */}
        <div className="form-group">
          <label className="form-label">Symptom Description or OBD-II DTC Code</label>
          <textarea
            className="form-input"
            rows={3}
            placeholder="e.g., P0420 fault code, or 'squeaking sound when turning steering wheel'"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            required
            disabled={isLoading}
            style={{ resize: 'vertical' }}
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          className="btn btn-primary"
          disabled={isLoading || !make || !model || !year || !query}
          style={{ padding: '0.9rem 2rem', display: 'flex', gap: '0.5rem', width: '100%' }}
        >
          {isLoading ? (
            <>
              <span className="skeleton" style={{
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                display: 'inline-block'
              }} />
              Analyzing Vehicle Dynamics...
            </>
          ) : (
            'Diagnose'
          )}
        </button>
      </form>
    </div>
  );
};
