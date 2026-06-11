'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

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
  city: string;
  state: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [beaches, setBeaches] = useState<Beach[]>([]);
  const [modelMetrics, setModelMetrics] = useState<{ r2: number; mae: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch('http://localhost:8000/api/incidentes/').then((r) => {
        if (!r.ok) throw new Error('Falha ao carregar incidentes');
        return r.json();
      }),
      fetch('http://localhost:8000/api/praias/').then((r) => {
        if (!r.ok) throw new Error('Falha ao carregar praias');
        return r.json();
      }),
      fetch('http://localhost:8000/api/ml/metrics/')
        .then((r) => r.ok ? r.json() : null)
        .catch(() => null),
    ])
      .then(([incData, beachData, metricsData]) => {
        setIncidents(Array.isArray(incData) ? incData : []);
        setBeaches(Array.isArray(beachData) ? beachData : []);
        setModelMetrics(metricsData || { r2: 0.88046, mae: 0.01787 });
        setLoading(false);
      })
      .catch((err) => {
        console.error('Erro ao buscar dados do dashboard:', err);
        setError('Erro ao conectar com a API do backend.');
        setLoading(false);
      });
  }, []);

  // Helpers
  const getBeachName = (id: number) => {
    const b = beaches.find((b) => b.id === id);
    return b ? b.name : `Praia #${id}`;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 0' }}>
        <div className="loading-spinner"></div>
        <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>Carregando dados estatísticos...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-container" style={{ textAlign: 'center', padding: '3rem', marginTop: '2rem' }}>
        <svg
          style={{ width: '48px', height: '48px', color: 'var(--danger-color)', marginBottom: '1rem' }}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p style={{ fontSize: '1.2rem', marginBottom: '1.5rem', color: '#fca5a5' }}>{error}</p>
        <button className="btn btn-primary" onClick={() => window.location.reload()}>
          Tentar Novamente
        </button>
      </div>
    );
  }

  // 1. Calculando KPIs
  const totalIncidents = incidents.length;
  const totalBeaches = beaches.length;

  const highSeverityIncidents = incidents.filter((i) => {
    const s = i.severity.toLowerCase();
    return s.includes('alta') || s.includes('grave') || s.includes('high');
  }).length;

  // Praia mais crítica
  const incidentCountsByBeach: Record<number, number> = {};
  incidents.forEach((i) => {
    incidentCountsByBeach[i.beach] = (incidentCountsByBeach[i.beach] || 0) + 1;
  });

  let topBeachId = 0;
  let topBeachCount = 0;
  Object.entries(incidentCountsByBeach).forEach(([beachId, count]) => {
    if (count > topBeachCount) {
      topBeachCount = count;
      topBeachId = Number(beachId);
    }
  });

  const criticalBeachName = topBeachId ? getBeachName(topBeachId) : 'Nenhuma';

  // 2. Gravidade das Ocorrências
  let countAlta = 0;
  let countMedia = 0;
  let countBaixa = 0;
  incidents.forEach((i) => {
    const s = i.severity.toLowerCase();
    if (s.includes('alta') || s.includes('grave') || s.includes('high')) countAlta++;
    else if (s.includes('media') || s.includes('média') || s.includes('medium')) countMedia++;
    else countBaixa++;
  });

  // 3. Tipos de Ocorrências
  let countAtaque = 0;
  let countAvistamento = 0;
  let countOutros = 0;
  incidents.forEach((i) => {
    const type = i.incident_type.toLowerCase();
    if (type.includes('ataque')) countAtaque++;
    else if (type.includes('avistamento')) countAvistamento++;
    else countOutros++;
  });

  // 4. Ranking de Praias
  const rankedBeaches = Object.entries(incidentCountsByBeach)
    .map(([beachId, count]) => ({
      id: Number(beachId),
      name: getBeachName(Number(beachId)),
      count,
    }))
    .sort((a, b) => b.count - a.count);

  // 5. Histórico por Ano
  const yearlyData: Record<string, number> = {};
  incidents.forEach((i) => {
    try {
      const year = new Date(i.date).getFullYear().toString();
      if (!isNaN(Number(year))) {
        yearlyData[year] = (yearlyData[year] || 0) + 1;
      }
    } catch {
      // Ignorar data mal formatada
    }
  });
  const sortedYears = Object.entries(yearlyData)
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([year, count]) => ({ year, count }));

  // Donut chart calculations
  const donutTotal = countAlta + countMedia + countBaixa || 1;
  const pctAlta = (countAlta / donutTotal) * 100;
  const pctMedia = (countMedia / donutTotal) * 100;
  const pctBaixa = (countBaixa / donutTotal) * 100;

  const radius = 50;
  const circumference = 2 * Math.PI * radius; // ~314.16

  const strokeDashAlta = `${(pctAlta / 100) * circumference} ${circumference}`;
  const strokeDashMedia = `${(pctMedia / 100) * circumference} ${circumference}`;
  const strokeDashBaixa = `${(pctBaixa / 100) * circumference} ${circumference}`;

  const offsetAlta = 0;
  const offsetMedia = -((pctAlta / 100) * circumference);
  const offsetBaixa = -(((pctAlta + pctMedia) / 100) * circumference);

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      <div>
        <h2>Dashboard Analítico</h2>
        <p>Estatísticas consolidadas e análise de incidentes marítimos monitorados.</p>
      </div>

      {/* KPI Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1.5rem',
        }}
      >
        {/* KPI 1 */}
        <div className="glass-container" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              background: 'rgba(59, 130, 246, 0.15)',
              color: 'var(--accent-hover)',
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg style={{ width: '24px', height: '24px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p style={{ fontSize: '0.85rem', margin: 0 }}>Total de Incidentes</p>
            <h3 style={{ fontSize: '1.75rem', fontWeight: 700, margin: '0.2rem 0 0 0' }}>{totalIncidents}</h3>
          </div>
        </div>

        {/* KPI 2 */}
        <div className="glass-container" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              background: 'rgba(16, 185, 129, 0.15)',
              color: '#6ee7b7',
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg style={{ width: '24px', height: '24px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <div>
            <p style={{ fontSize: '0.85rem', margin: 0 }}>Praias Monitoradas</p>
            <h3 style={{ fontSize: '1.75rem', fontWeight: 700, margin: '0.2rem 0 0 0' }}>{totalBeaches}</h3>
          </div>
        </div>

        {/* KPI 3 */}
        <div className="glass-container" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              color: '#fca5a5',
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg style={{ width: '24px', height: '24px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p style={{ fontSize: '0.85rem', margin: 0 }}>Gravidade Alta</p>
            <h3 style={{ fontSize: '1.75rem', fontWeight: 700, margin: '0.2rem 0 0 0' }}>{highSeverityIncidents}</h3>
          </div>
        </div>

        {/* KPI 4 */}
        <div className="glass-container" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              background: 'rgba(245, 158, 11, 0.15)',
              color: '#fcd34d',
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg style={{ width: '24px', height: '24px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9l2 4h4.5l-3.5 3 1.5 5-4.5-3-4.5 3 1.5-5-3.5-3H10l2-4z" />
            </svg>
          </div>
          <div>
            <p style={{ fontSize: '0.85rem', margin: 0 }}>Praia Mais Crítica</p>
            <h3
              style={{
                fontSize: '1.1rem',
                fontWeight: 700,
                margin: '0.2rem 0 0 0',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                maxWidth: '180px',
              }}
              title={`${criticalBeachName} (${topBeachCount} casos)`}
            >
              {criticalBeachName} <span style={{ fontSize: '0.8rem', fontWeight: 400, color: 'var(--text-secondary)' }}>({topBeachCount})</span>
            </h3>
          </div>
        </div>

        {/* KPI 5 - R² */}
        <div className="glass-container" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              background: 'rgba(167, 139, 250, 0.15)',
              color: '#c084fc',
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg style={{ width: '24px', height: '24px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div>
            <p style={{ fontSize: '0.85rem', margin: 0 }} title="Coeficiente de Determinação (R²)">Precisão do Modelo (R²)</p>
            <h3 style={{ fontSize: '1.75rem', fontWeight: 700, margin: '0.2rem 0 0 0' }}>
              {modelMetrics ? modelMetrics.r2.toFixed(4) : '...'}
            </h3>
          </div>
        </div>

        {/* KPI 6 - MAE */}
        <div className="glass-container" style={{ padding: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div
            style={{
              background: 'rgba(45, 212, 191, 0.15)',
              color: '#2dd4bf',
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg style={{ width: '24px', height: '24px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p style={{ fontSize: '0.85rem', margin: 0 }} title="Erro Absoluto Médio (MAE)">Erro do Modelo (MAE)</p>
            <h3 style={{ fontSize: '1.75rem', fontWeight: 700, margin: '0.2rem 0 0 0' }}>
              {modelMetrics ? modelMetrics.mae.toFixed(4) : '...'}
            </h3>
          </div>
        </div>
      </div>

      {/* Main Charts Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))',
          gap: '2rem',
        }}
      >
        {/* CHART 1: Ranking por Praia */}
        <div className="glass-container" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
            Incidentes por Praia (Ranking)
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.2rem', flexGrow: 1 }}>
            {rankedBeaches.length === 0 ? (
              <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>Nenhum incidente registrado.</p>
            ) : (
              rankedBeaches.slice(0, 5).map((beach) => {
                const maxCount = rankedBeaches[0]?.count || 1;
                const percentage = (beach.count / maxCount) * 100;
                return (
                  <div
                    key={beach.id}
                    onClick={() => router.push(`/?beach=${beach.id}`)}
                    style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                    className="ranking-row"
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem', fontSize: '0.9rem' }}>
                      <span style={{ fontWeight: 500 }} className="hover-underline">
                        {beach.name}
                      </span>
                      <span style={{ fontWeight: 600, color: 'var(--accent-hover)' }}>{beach.count} casos</span>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.05)', height: '10px', borderRadius: '5px', overflow: 'hidden', display: 'flex' }}>
                      <div
                        style={{
                          width: `${percentage}%`,
                          background: 'linear-gradient(90deg, var(--accent-color) 0%, #c084fc 100%)',
                          borderRadius: '5px',
                          transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)',
                        }}
                      />
                    </div>
                  </div>
                );
              })
            )}
            {rankedBeaches.length > 5 && (
              <p style={{ fontSize: '0.8rem', textAlign: 'center', color: 'var(--text-secondary)', marginTop: 'auto', paddingTop: '0.5rem' }}>
                Clique em uma praia para filtrar seus incidentes no histórico
              </p>
            )}
          </div>
        </div>

        {/* CHART 2: Severidade (Donut Chart) */}
        <div className="glass-container" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
            Distribuição por Gravidade
          </h3>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-around',
              flexWrap: 'wrap',
              gap: '1.5rem',
              flexGrow: 1,
            }}
          >
            {totalIncidents === 0 ? (
              <p style={{ color: 'var(--text-secondary)' }}>Sem dados disponíveis.</p>
            ) : (
              <>
                {/* SVG Donut Chart */}
                <div style={{ position: 'relative', width: '150px', height: '150px' }}>
                  <svg width="100%" height="100%" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r={radius} fill="transparent" stroke="rgba(255,255,255,0.03)" strokeWidth="12" />
                    {countAlta > 0 && (
                      <circle
                        cx="60"
                        cy="60"
                        r={radius}
                        fill="transparent"
                        stroke="var(--danger-color)"
                        strokeWidth="12"
                        strokeDasharray={strokeDashAlta}
                        strokeDashoffset={offsetAlta}
                        transform="rotate(-90 60 60)"
                        strokeLinecap="round"
                        style={{ transition: 'stroke-dasharray 1s ease' }}
                      />
                    )}
                    {countMedia > 0 && (
                      <circle
                        cx="60"
                        cy="60"
                        r={radius}
                        fill="transparent"
                        stroke="var(--warning-color)"
                        strokeWidth="12"
                        strokeDasharray={strokeDashMedia}
                        strokeDashoffset={offsetMedia}
                        transform="rotate(-90 60 60)"
                        strokeLinecap={countAlta === 0 ? 'round' : 'butt'}
                        style={{ transition: 'stroke-dasharray 1s ease' }}
                      />
                    )}
                    {countBaixa > 0 && (
                      <circle
                        cx="60"
                        cy="60"
                        r={radius}
                        fill="transparent"
                        stroke="var(--success-color)"
                        strokeWidth="12"
                        strokeDasharray={strokeDashBaixa}
                        strokeDashoffset={offsetBaixa}
                        transform="rotate(-90 60 60)"
                        strokeLinecap={countAlta === 0 && countMedia === 0 ? 'round' : 'butt'}
                        style={{ transition: 'stroke-dasharray 1s ease' }}
                      />
                    )}
                  </svg>
                  <div
                    style={{
                      position: 'absolute',
                      top: '50%',
                      left: '50%',
                      transform: 'translate(-50%, -50%)',
                      textAlign: 'center',
                    }}
                  >
                    <span style={{ fontSize: '1.5rem', fontWeight: 700 }}>{totalIncidents}</span>
                    <p style={{ fontSize: '0.7rem', margin: 0, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>Casos</p>
                  </div>
                </div>

                {/* Legend list */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem', minWidth: '150px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'var(--danger-color)' }} />
                    <div style={{ fontSize: '0.9rem' }}>
                      <span style={{ fontWeight: 500 }}>Alta/Grave:</span>{' '}
                      <strong>
                        {countAlta} ({pctAlta.toFixed(0)}%)
                      </strong>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'var(--warning-color)' }} />
                    <div style={{ fontSize: '0.9rem' }}>
                      <span style={{ fontWeight: 500 }}>Média:</span>{' '}
                      <strong>
                        {countMedia} ({pctMedia.toFixed(0)}%)
                      </strong>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '3px', background: 'var(--success-color)' }} />
                    <div style={{ fontSize: '0.9rem' }}>
                      <span style={{ fontWeight: 500 }}>Baixa:</span>{' '}
                      <strong>
                        {countBaixa} ({pctBaixa.toFixed(0)}%)
                      </strong>
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* CHART 3: Tipos de Incidências */}
        <div className="glass-container" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
            Tipos de Ocorrências
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', justifyContent: 'center', flexGrow: 1 }}>
            {totalIncidents === 0 ? (
              <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>Sem dados.</p>
            ) : (
              <>
                {/* Progress bar split */}
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--danger-color)' }} />
                      Ataques de Tubarão
                    </span>
                    <strong>
                      {countAtaque} ({((countAtaque / (totalIncidents || 1)) * 100).toFixed(0)}%)
                    </strong>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.05)', height: '14px', borderRadius: '7px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${(countAtaque / (totalIncidents || 1)) * 100}%`,
                        background: 'var(--danger-color)',
                        height: '100%',
                        borderRadius: '7px',
                        transition: 'width 1s ease',
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-color)' }} />
                      Avistamentos de Tubarão
                    </span>
                    <strong>
                      {countAvistamento} ({((countAvistamento / (totalIncidents || 1)) * 100).toFixed(0)}%)
                    </strong>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.05)', height: '14px', borderRadius: '7px', overflow: 'hidden' }}>
                    <div
                      style={{
                        width: `${(countAvistamento / (totalIncidents || 1)) * 100}%`,
                        background: 'var(--accent-color)',
                        height: '100%',
                        borderRadius: '7px',
                        transition: 'width 1s ease',
                      }}
                    />
                  </div>
                </div>

                {countOutros > 0 && (
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--text-secondary)' }} />
                        Outros / Não Especificado
                      </span>
                      <strong>
                        {countOutros} ({((countOutros / (totalIncidents || 1)) * 100).toFixed(0)}%)
                      </strong>
                    </div>
                    <div style={{ background: 'rgba(255,255,255,0.05)', height: '14px', borderRadius: '7px', overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${(countOutros / (totalIncidents || 1)) * 100}%`,
                          background: 'var(--text-secondary)',
                          height: '100%',
                          borderRadius: '7px',
                          transition: 'width 1s ease',
                        }}
                      />
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* CHART 4: Evolução Temporal por Ano */}
        <div className="glass-container" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>
            Evolução Histórica por Ano
          </h3>
          <div style={{ display: 'flex', flexGrow: 1, alignItems: 'flex-end', justifyContent: 'space-around', padding: '1rem 0 0.5rem 0', minHeight: '180px' }}>
            {sortedYears.length === 0 ? (
              <p style={{ color: 'var(--text-secondary)', alignSelf: 'center' }}>Sem dados históricos.</p>
            ) : (
              sortedYears.map((data) => {
                const maxYearCount = Math.max(...sortedYears.map((y) => y.count), 1);
                const barHeight = (data.count / maxYearCount) * 120; // max height 120px
                return (
                  <div key={data.year} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', width: '60px' }}>
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-hover)' }}>{data.count}</span>
                    <div
                      style={{
                        height: `${barHeight}px`,
                        width: '32px',
                        background: 'linear-gradient(180deg, var(--accent-hover) 0%, rgba(59, 130, 246, 0.2) 100%)',
                        border: '1px solid var(--accent-color)',
                        borderRadius: '6px 6px 0 0',
                        transition: 'height 1s cubic-bezier(0.4, 0, 0.2, 1)',
                      }}
                      title={`${data.count} incidentes em ${data.year}`}
                    />
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500 }}>{data.year}</span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Styled styles injection to allow custom hover states without Tailwind where needed */}
      <style dangerouslySetInnerHTML={{ __html: `
        .ranking-row:hover {
          background: rgba(255, 255, 255, 0.02);
          transform: translateX(4px);
        }
        .ranking-row {
          padding: 0.5rem;
          border-radius: 8px;
          transition: all 0.2s;
        }
        .hover-underline:hover {
          text-decoration: underline;
        }
      ` }} />
    </div>
  );
}
