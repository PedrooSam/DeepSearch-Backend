'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';interface Incident {
  id: number;
  beach: number;
  date: string;
  incident_type: string;
  severity: string;
  description: string;
}

export default function Dashboard() {
  const router = useRouter();
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

  const handleDelete = async (id: number) => {
    if (confirm('Tem certeza que deseja excluir esta incidência?')) {
      try {
        const res = await fetch(`http://localhost:8000/api/incidentes/${id}/`, {
          method: 'DELETE',
        });
        if (res.ok) {
          setIncidents(incidents.filter(incident => incident.id !== id));
        } else {
          alert('Erro ao excluir incidência.');
        }
      } catch (err) {
        console.error('Erro ao excluir:', err);
        alert('Erro ao excluir incidência.');
      }
    }
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
              <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Praia ID: {incident.beach}</span>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button 
                    onClick={() => router.push(`/editar/${incident.id}`)}
                    className="btn"
                    style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid rgba(255,255,255,0.2)' }}
                  >
                    Editar
                  </button>
                  <button 
                    onClick={() => handleDelete(incident.id)}
                    className="btn"
                    style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', border: '1px solid rgba(239, 68, 68, 0.3)' }}
                  >
                    Excluir
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
