'use client';

import { useEffect, useState } from 'react';

interface Incident {
  id: number;
  beach: number;
  date: string;
  incident_type: string;
  severity: string;
  description: string;
}

export default function Dashboard() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/incidentes/')
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setIncidents(data);
        } else {
          console.error('Resposta inesperada da API:', data);
          setIncidents([]);
        }
        setLoading(false);
      })
      .catch((err) => {
        console.error('Erro ao buscar incidências:', err);
        setLoading(false);
      });
  }, []);

  const getSeverityBadge = (severity: string) => {
    const s = severity.toLowerCase();
    if (s.includes('alta') || s.includes('grave') || s.includes('high')) return 'badge badge-danger';
    if (s.includes('media') || s.includes('média') || s.includes('medium')) return 'badge badge-warning';
    return 'badge badge-success';
  };

  return (
    <div>
      <h2>Dashboard de Incidências</h2>
      <p>Acompanhe e gerencie as incidências registradas nas praias.</p>

      {loading ? (
        <div style={{ textAlign: 'center' }}>
          <div className="loading-spinner"></div>
        </div>
      ) : incidents.length === 0 ? (
        <div className="glass-container" style={{ marginTop: '2rem', textAlign: 'center', padding: '4rem 2rem' }}>
          <p style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Nenhuma incidência registrada ainda.</p>
        </div>
      ) : (
        <div className="grid-cards">
          {incidents.map((incident) => (
            <div key={incident.id} className="glass-container">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>{incident.incident_type}</h3>
                <span className={getSeverityBadge(incident.severity)}>{incident.severity}</span>
              </div>
              <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                <strong>Data:</strong> {new Date(incident.date).toLocaleDateString('pt-BR')}
              </p>
              {incident.description && (
                <p style={{ fontSize: '0.95rem', color: '#cbd5e1' }}>{incident.description}</p>
              )}
              <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Praia ID: {incident.beach}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
