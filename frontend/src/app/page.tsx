'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface Incident {
  id: number;
  beach: number;
  date: string;
  incident_type: string;
  severity: string;
  description: string;
}

interface Beach {
  id: number;
  name: string;
}

export default function Dashboard() {
  return (
    <Suspense fallback={
      <div style={{ textAlign: 'center', padding: '4rem 0' }}>
        <div className="loading-spinner"></div>
        <p>Carregando histórico...</p>
      </div>
    }>
      <IncidentList />
    </Suspense>
  );
}

function IncidentList() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const beachFilter = searchParams.get('beach');

  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [beaches, setBeaches] = useState<Beach[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch('http://localhost:8000/api/incidentes/').then(r => r.json()),
      fetch('http://localhost:8000/api/praias/').then(r => r.json()),
    ])
      .then(([incData, beachData]) => {
        setIncidents(Array.isArray(incData) ? incData : []);
        setBeaches(Array.isArray(beachData) ? beachData : []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Erro ao buscar dados:', err);
        setLoading(false);
      });
  }, []);

  const filteredIncidents = beachFilter
    ? incidents.filter(i => i.beach === Number(beachFilter))
    : incidents;

  const getBeachName = (id: number) => {
    const b = beaches.find(b => b.id === id);
    return b ? b.name : `Praia #${id}`;
  };

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
      <h2>Histórico de Incidências</h2>
      {beachFilter ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <p>Filtrando por: <strong>{getBeachName(Number(beachFilter))}</strong></p>
          <button
            onClick={() => router.push('/')}
            className="btn"
            style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', background: 'rgba(255,255,255,0.1)', color: 'white', border: '1px solid rgba(255,255,255,0.2)' }}
          >
            Limpar filtro
          </button>
        </div>
      ) : (
        <p>Acompanhe e gerencie as incidências registradas nas praias.</p>
      )}

      {loading ? (
        <div style={{ textAlign: 'center' }}>
          <div className="loading-spinner"></div>
        </div>
      ) : filteredIncidents.length === 0 ? (
        <div className="glass-container" style={{ marginTop: '2rem', textAlign: 'center', padding: '4rem 2rem' }}>
          <p style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>
            {beachFilter ? 'Nenhuma incidência registrada para esta praia.' : 'Nenhuma incidência registrada ainda.'}
          </p>
        </div>
      ) : (
        <div className="grid-cards">
          {filteredIncidents.map((incident) => (
            <div key={incident.id} className="glass-container">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>{incident.incident_type}</h3>
                <span className={getSeverityBadge(incident.severity)}>{incident.severity}</span>
              </div>
              <p style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                <strong>Data:</strong> {new Date(incident.date).toLocaleDateString('pt-BR')}
              </p>
              <p style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                <strong>Praia:</strong> {getBeachName(incident.beach)}
              </p>
              {incident.description && (
                <p style={{ fontSize: '0.95rem', color: '#cbd5e1' }}>{incident.description}</p>
              )}
              <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'flex-end' }}>
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
