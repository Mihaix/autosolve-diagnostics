import { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { DiagnosticForm } from './components/DiagnosticForm';
import { ResultsDisplay } from './components/ResultsDisplay';
import { FallbackCard } from './components/FallbackCard';
import { ConfidenceGauge } from './components/ConfidenceGauge';
import { HistorySidebar } from './components/HistorySidebar';
import { diagnose, checkApiHealth } from './services/api';
import type { DiagnosticRequest, DiagnosticResponse, HistoryItem } from './types';
import './App.css';

function App() {
  const [isMockMode, setIsMockMode] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [currentRequest, setCurrentRequest] = useState<DiagnosticRequest | null>(null);
  const [currentResponse, setCurrentResponse] = useState<DiagnosticResponse | null>(null);
  const [selectedHistoryId, setSelectedHistoryId] = useState<string | undefined>(undefined);
  const [history, setHistory] = useState<HistoryItem[]>([]);

  // Load history from LocalStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem('autosolve_history');
      if (stored) {
        setHistory(JSON.parse(stored));
      }
    } catch (e) {
      console.error('Failed to load search history:', e);
    }
  }, []);

  // Check API health on mount and every 10 seconds
  useEffect(() => {
    const checkStatus = async () => {
      const online = await checkApiHealth();
      // Auto-toggle mock mode to false if API is online (helper for dev)
      if (online) {
        setIsMockMode(false);
      }
    };
    
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleDiagnose = async (req: DiagnosticRequest) => {
    setIsLoading(true);
    setError(null);
    setCurrentRequest(req);
    setCurrentResponse(null);
    setSelectedHistoryId(undefined);

    try {
      const res = await diagnose(req, isMockMode);
      setCurrentResponse(res);

      // Add to search history list
      const newItem: HistoryItem = {
        id: Math.random().toString(36).substring(2, 11),
        request: req,
        response: res,
        timestamp: new Date().toISOString()
      };
      
      setHistory(prev => {
        const updated = [newItem, ...prev].slice(0, 20); // Keep top 20 items
        localStorage.setItem('autosolve_history', JSON.stringify(updated));
        return updated;
      });
      setSelectedHistoryId(newItem.id);
    } catch (err: any) {
      setError(err.message || 'An error occurred while fetching diagnostics.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectHistoryItem = (item: HistoryItem) => {
    setCurrentRequest(item.request);
    setCurrentResponse(item.response);
    setSelectedHistoryId(item.id);
    setError(null);
  };

  const handleClearHistory = () => {
    setHistory([]);
    localStorage.removeItem('autosolve_history');
    setSelectedHistoryId(undefined);
  };

  return (
    <div style={{
      maxWidth: '1400px',
      margin: '0 auto',
      padding: '0 1rem 3rem 1rem',
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh'
    }}>
      {/* Header section */}
      <Header />

      {/* Main Content Layout Grid */}
      <main className="main-layout-grid animate-fade-in">
        
        {/* Sidebar History Panel */}
        <aside style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <HistorySidebar 
            history={history}
            onSelect={handleSelectHistoryItem}
            onClear={handleClearHistory}
            selectedId={selectedHistoryId}
          />
        </aside>

        {/* Diagnostic Workspace */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '720px', width: '100%' }}>
          
          {/* Query Form component */}
          <DiagnosticForm onSubmit={handleDiagnose} isLoading={isLoading} />

          {/* Error Notification */}
          {error && (
            <div className="glass-panel" style={{
              padding: '1.25rem 1.5rem',
              borderRadius: 'var(--radius-md)',
              borderLeft: '4px solid var(--color-danger)',
              background: 'rgba(239, 68, 68, 0.05)',
              color: 'var(--text-main)',
              fontSize: '0.95rem'
            }}>
              <strong>⚠️ Connection Error:</strong> {error}
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Please check if the FastAPI backend is running on port 8000, or toggle <strong>Demo Mock Mode</strong> above to test local capabilities.
              </div>
            </div>
          )}

          {/* Loading Skeleton Loader */}
          {isLoading && (
            <div className="glass-panel" style={{ padding: '2rem', borderRadius: 'var(--radius-md)' }}>
              <div className="skeleton skeleton-title" style={{ width: '40%' }}></div>
              <div className="skeleton skeleton-text" style={{ width: '90%' }}></div>
              <div className="skeleton skeleton-text" style={{ width: '95%' }}></div>
              <div className="skeleton skeleton-text" style={{ width: '85%' }}></div>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
                <div className="skeleton" style={{ width: '80px', height: '80px', borderRadius: '50%' }}></div>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div className="skeleton skeleton-text" style={{ width: '30%' }}></div>
                  <div className="skeleton skeleton-text" style={{ width: '60%' }}></div>
                </div>
              </div>
            </div>
          )}

          {/* Results display panel */}
          {!isLoading && currentRequest && currentResponse && (
            currentResponse.is_fallback ? (
              <FallbackCard request={currentRequest} response={currentResponse} />
            ) : (
              <ResultsDisplay request={currentRequest} response={currentResponse} />
            )
          )}

          {/* Initial Welcome Screen */}
          {!isLoading && !currentResponse && (
            <div className="glass-panel" style={{
              padding: '3rem 2rem',
              borderRadius: 'var(--radius-lg)',
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '1.5rem'
            }}>
              <div style={{
                fontSize: '2.5rem',
                background: 'rgba(255,255,255,0.02)',
                width: '70px',
                height: '70px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid var(--border-color)'
              }}>
                🚙
              </div>
              <div>
                <h3 style={{ fontSize: '1.4rem', fontWeight: 700, marginBottom: '0.5rem' }}>
                  Awaiting Vehicle Diagnosis
                </h3>
                <p style={{ color: 'var(--text-muted)', maxWidth: '500px', margin: '0 auto', fontSize: '0.95rem' }}>
                  Enter your car details and symptoms or OBD-II codes above. The system will retrieve relevant workshop guidelines and produce clear, hallucination-free repair advice.
                </p>
              </div>
            </div>
          )}

        </section>

        {/* Right Column: Gauges & Metrics Panel */}
        <aside className="layout-stats-aside" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', position: 'sticky', top: '1.5rem', width: '100%', maxWidth: '280px' }}>
          <ConfidenceGauge score={currentResponse ? currentResponse.confidence_score : 0} />
          
          <div className="glass-panel" style={{ padding: '1.5rem', borderRadius: 'var(--radius-md)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <h4 style={{ color: 'var(--text-main)', marginBottom: '0.75rem', fontSize: '0.85rem' }}>RAG Pipeline Parameters</h4>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.3rem 0', borderBottom: '1px dashed rgba(255,255,255,0.03)' }}>
              <span>Model:</span>
              <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>Mistral-7B-v0.2</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.3rem 0', borderBottom: '1px dashed rgba(255,255,255,0.03)' }}>
              <span>Embeddings:</span>
              <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>all-MiniLM-L6</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.3rem 0' }}>
              <span>Chroma Filter:</span>
              <span style={{ color: 'var(--text-main)', fontWeight: 600 }}>Hard match</span>
            </div>
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;
