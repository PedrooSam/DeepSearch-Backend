'use client';

import { useEffect, useState } from 'react';

interface Alert {
  id: number;
  beach: number;
  beach_name: string;
  alert_type: string;
  severity: string;
  title: string;
  message: string;
  reason_factors: Record<string, string | number>;
  safety_tips: string[];
  previous_risk_level: string;
  current_risk_level: string;
  nearest_safe_beach: number | null;
  nearest_safe_beach_name: string | null;
  nearest_safe_beach_lat: number | null;
  nearest_safe_beach_lon: number | null;
  created_at: string;
  expires_at: string;
}

interface Summary {
  total: number;
  high: number;
  medium: number;
  low: number;
  period_days: number;
}

const SEVERITY_STYLES: Record<string, { badge: string; bg: string; border: string; icon: string }> = {
  high: {
    badge: 'badge badge-danger',
    bg: 'rgba(239, 68, 68, 0.08)',
    border: 'rgba(239, 68, 68, 0.3)',
    icon: '🔴',
  },
  medium: {
    badge: 'badge badge-warning',
    bg: 'rgba(245, 158, 11, 0.08)',
    border: 'rgba(245, 158, 11, 0.3)',
    icon: '🟡',
  },
  low: {
    badge: 'badge badge-success',
    bg: 'rgba(16, 185, 129, 0.08)',
    border: 'rgba(16, 185, 129, 0.3)',
    icon: '🟢',
  },
};

const FACTOR_LABELS: Record<string, string> = {
  horario: 'Horário',
  estacao: 'Estação',
  ondas_m: 'Ondas',
  temperatura_mar: 'Temp. do mar',
  mare: 'Maré',
  historico_incidentes: 'Histórico',
};

export default function AlertasPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingLocation, setUsingLocation] = useState(false);
  const [locationStatus, setLocationStatus] = useState<string | null>(null);

  const fetchAlerts = (url: string) => {
    setLoading(true);
    setError(null);
    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error('Erro ao buscar alertas');
        return res.json();
      })
      .then((data) => {
        setAlerts(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  };

  const fetchSummary = () => {
    fetch('http://localhost:8000/api/monitoring/summary/?days=7')
      .then((res) => res.ok ? res.json() : null)
      .then((data) => setSummary(data))
      .catch(() => null);
  };

  useEffect(() => {
    fetchAlerts('http://localhost:8000/api/monitoring/alerts/');
    fetchSummary();

    const interval = setInterval(() => {
      if (!usingLocation) {
        fetchAlerts('http://localhost:8000/api/monitoring/alerts/');
      }
      fetchSummary();
    }, 2 * 60 * 1000); // 2 minutos

    return () => clearInterval(interval);
  }, [usingLocation]);

  const handleNearby = () => {
    if (!navigator.geolocation) {
      setLocationStatus('Geolocalização não suportada pelo navegador.');
      return;
    }

    setUsingLocation(true);
    setLocationStatus('Obtendo localização...');

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setLocationStatus(`Localização: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`);
        fetchAlerts(
          `http://localhost:8000/api/monitoring/nearby/?lat=${latitude}&lon=${longitude}&radius=5`
        );
      },
      (err) => {
        setLocationStatus('Não foi possível obter localização. Mostrando todos os alertas.');
        setUsingLocation(false);
        fetchAlerts('http://localhost:8000/api/monitoring/alerts/');
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const handleShowAll = () => {
    setUsingLocation(false);
    setLocationStatus(null);
    fetchAlerts('http://localhost:8000/api/monitoring/alerts/');
  };

  const formatTime = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatFactor = (key: string, value: string | number) => {
    const label = FACTOR_LABELS[key] || key;
    if (typeof value === 'number') {
      if (key === 'ondas_m') return `${label}: ${value}m`;
      if (key === 'temperatura_mar') return `${label}: ${value}°C`;
      return `${label}: ${(value * 100).toFixed(0)}%`;
    }
    return `${label}: ${value}`;
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div>
        <h2>Alertas e Monitoramento</h2>
        <p>Acompanhe alertas de mudanças de risco nas praias monitoradas.</p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem' }}>
          <div className="glass-container" style={{ padding: '1.25rem', textAlign: 'center' }}>
            <p style={{ fontSize: '0.8rem', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Total (7 dias)</p>
            <h3 style={{ fontSize: '2rem', fontWeight: 700, margin: '0.25rem 0 0' }}>{summary.total}</h3>
          </div>
          <div className="glass-container" style={{ padding: '1.25rem', textAlign: 'center', borderColor: 'rgba(239, 68, 68, 0.2)' }}>
            <p style={{ fontSize: '0.8rem', margin: 0, color: '#fca5a5' }}>Alta</p>
            <h3 style={{ fontSize: '2rem', fontWeight: 700, margin: '0.25rem 0 0', color: '#fca5a5' }}>{summary.high}</h3>
          </div>
          <div className="glass-container" style={{ padding: '1.25rem', textAlign: 'center', borderColor: 'rgba(245, 158, 11, 0.2)' }}>
            <p style={{ fontSize: '0.8rem', margin: 0, color: '#fcd34d' }}>Média</p>
            <h3 style={{ fontSize: '2rem', fontWeight: 700, margin: '0.25rem 0 0', color: '#fcd34d' }}>{summary.medium}</h3>
          </div>
          <div className="glass-container" style={{ padding: '1.25rem', textAlign: 'center', borderColor: 'rgba(16, 185, 129, 0.2)' }}>
            <p style={{ fontSize: '0.8rem', margin: 0, color: '#6ee7b7' }}>Baixa</p>
            <h3 style={{ fontSize: '2rem', fontWeight: 700, margin: '0.25rem 0 0', color: '#6ee7b7' }}>{summary.low}</h3>
          </div>
        </div>
      )}

      {/* Controls */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
        <button className="btn btn-primary" onClick={handleNearby}>
          <svg style={{ width: '16px', height: '16px', marginRight: '0.5rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Alertas perto de mim
        </button>
        {usingLocation && (
          <button className="btn btn-secondary" onClick={handleShowAll}>
            Ver todos
          </button>
        )}
        {locationStatus && (
          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{locationStatus}</span>
        )}
      </div>

      {/* Alert List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="loading-spinner"></div>
          <p>Carregando alertas...</p>
        </div>
      ) : error ? (
        <div className="glass-container" style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ color: '#fca5a5' }}>Erro: {error}</p>
          <button className="btn btn-primary" style={{ marginTop: '1rem' }} onClick={() => fetchAlerts('http://localhost:8000/api/monitoring/alerts/')}>
            Tentar novamente
          </button>
        </div>
      ) : alerts.length === 0 ? (
        <div className="glass-container" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <svg style={{ width: '48px', height: '48px', color: 'var(--success-color)', margin: '0 auto 1rem' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p style={{ fontSize: '1.2rem', color: 'var(--text-primary)' }}>Nenhum alerta ativo</p>
          <p style={{ fontSize: '0.9rem' }}>Todas as praias estão com condições estáveis no momento.</p>
        </div>
      ) : (
        <div className="grid-cards">
          {alerts.map((alert) => {
            const style = SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.low;
            return (
              <div
                key={alert.id}
                className="glass-container"
                style={{
                  borderColor: style.border,
                  background: style.bg,
                }}
              >
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600, margin: 0 }}>
                    {style.icon} {alert.title}
                  </h3>
                  <span className={style.badge}>{alert.severity === 'high' ? 'Alta' : alert.severity === 'medium' ? 'Média' : 'Baixa'}</span>
                </div>

                {/* Beach & Time */}
                <p style={{ fontSize: '0.85rem', margin: '0 0 0.5rem', color: 'var(--text-secondary)' }}>
                  {alert.beach_name} &middot; {formatTime(alert.created_at)}
                </p>

                {/* Message */}
                <p style={{ fontSize: '0.95rem', margin: '0.75rem 0', color: 'var(--text-primary)' }}>
                  {alert.message}
                </p>

                {/* Risk Change */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: '0.75rem 0', fontSize: '0.9rem' }}>
                  <span className="badge badge-success">{alert.previous_risk_level}</span>
                  <span style={{ color: 'var(--text-secondary)' }}>→</span>
                  <span className={alert.current_risk_level === 'Alto' ? 'badge badge-danger' : alert.current_risk_level === 'Moderado' ? 'badge badge-warning' : 'badge badge-success'}>
                    {alert.current_risk_level}
                  </span>
                </div>

                {/* Factors */}
                {Object.keys(alert.reason_factors).length > 0 && (
                  <div style={{ margin: '0.75rem 0', padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                    <p style={{ fontSize: '0.8rem', fontWeight: 600, margin: '0 0 0.4rem', color: 'var(--text-primary)' }}>Fatores:</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                      {Object.entries(alert.reason_factors).map(([key, value]) => (
                        <span key={key} className="badge badge-info" style={{ fontSize: '0.7rem' }}>
                          {formatFactor(key, value)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Safety Tips */}
                {alert.safety_tips.length > 0 && (
                  <div style={{ margin: '0.75rem 0', padding: '0.75rem', background: 'rgba(59, 130, 246, 0.05)', borderRadius: '8px', borderLeft: '3px solid var(--accent-color)' }}>
                    <p style={{ fontSize: '0.8rem', fontWeight: 600, margin: '0 0 0.4rem', color: 'var(--accent-hover)' }}>Dicas de segurança:</p>
                    <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      {alert.safety_tips.map((tip, idx) => (
                        <li key={idx} style={{ marginBottom: '0.2rem' }}>{tip}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Nearest Safe Beach */}
                {alert.nearest_safe_beach_name && (
                  <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(16, 185, 129, 0.05)', borderRadius: '8px', borderLeft: '3px solid var(--success-color)' }}>
                    <p style={{ fontSize: '0.85rem', margin: 0, color: '#6ee7b7' }}>
                      Praia segura mais próxima: <strong>{alert.nearest_safe_beach_name}</strong>
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
