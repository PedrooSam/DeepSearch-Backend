'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

const RiskMap = dynamic(() => import('./RiskMap'), { ssr: false });

interface BeachRisk {
  beach_id: number;
  beach_name: string;
  city: string;
  state: string;
  latitude: number;
  longitude: number;
  probability: number;
  risk_level: string;
  incident_count: number;
  factors: Record<string, number>;
}

export default function MapaPage() {
  const [beaches, setBeaches] = useState<BeachRisk[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/risk-map/')
      .then((res) => {
        if (!res.ok) throw new Error('Erro ao buscar dados do mapa');
        return res.json();
      })
      .then((data) => {
        setBeaches(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem' }}>
        <div className="loading-spinner"></div>
        <p>Carregando mapa de risco...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-container" style={{ textAlign: 'center', padding: '4rem' }}>
        <p style={{ color: '#fca5a5' }}>Erro: {error}</p>
      </div>
    );
  }

  return (
    <div>
      <h2>Mapa de Risco</h2>
      <p>Visualize o nível de risco de ataque em cada praia monitorada.</p>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <span className="badge badge-danger">Alto</span>
        <span className="badge badge-warning">Moderado</span>
        <span className="badge badge-success">Baixo / Muito baixo</span>
      </div>

      <div className="glass-container" style={{ padding: '0', overflow: 'hidden', borderRadius: '12px' }}>
        <RiskMap beaches={beaches} />
      </div>
    </div>
  );
}
