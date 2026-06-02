'use client';

import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import Link from 'next/link';

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

const RISK_COLORS: Record<string, string> = {
  'Alto': '#ef4444',
  'Moderado': '#f59e0b',
  'Baixo': '#22c55e',
  'Muito baixo': '#22c55e',
};

const FACTOR_LABELS: Record<string, string> = {
  horario: 'Horário',
  estacao: 'Estação do ano',
  mare: 'Nível da maré',
  temperatura_mar: 'Temperatura do mar',
  historico_incidentes: 'Histórico de incidentes',
};

export default function RiskMap({ beaches }: { beaches: BeachRisk[] }) {
  const center: [number, number] = beaches.length > 0
    ? [beaches[0].latitude, beaches[0].longitude]
    : [-8.05, -34.87];

  return (
    <MapContainer
      center={center}
      zoom={12}
      style={{ height: '500px', width: '100%' }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {beaches.map((beach) => (
        <CircleMarker
          key={beach.beach_id}
          center={[beach.latitude, beach.longitude]}
          radius={14}
          fillColor={RISK_COLORS[beach.risk_level] || '#6b7280'}
          color={RISK_COLORS[beach.risk_level] || '#6b7280'}
          fillOpacity={0.7}
          weight={2}
        >
          <Popup>
            <div style={{ minWidth: '220px' }}>
              <h3 style={{ margin: '0 0 0.5rem', fontSize: '1rem', fontWeight: 700 }}>
                {beach.beach_name}
              </h3>
              <p style={{ margin: '0 0 0.25rem', fontSize: '0.85rem', color: '#64748b' }}>
                {beach.city}, {beach.state}
              </p>

              <div style={{
                margin: '0.75rem 0',
                padding: '0.5rem',
                borderRadius: '6px',
                background: RISK_COLORS[beach.risk_level] + '20',
                border: `1px solid ${RISK_COLORS[beach.risk_level]}`,
                textAlign: 'center',
              }}>
                <strong style={{ color: RISK_COLORS[beach.risk_level] }}>
                  Risco: {beach.risk_level}
                </strong>
                <br />
                <span style={{ fontSize: '0.8rem' }}>
                  Probabilidade: {(beach.probability * 100).toFixed(1)}%
                </span>
              </div>

              {Object.keys(beach.factors).length > 0 && (
                <div style={{ fontSize: '0.8rem', marginBottom: '0.75rem' }}>
                  <strong>Fatores:</strong>
                  <ul style={{ margin: '0.25rem 0 0', paddingLeft: '1rem' }}>
                    {Object.entries(beach.factors).map(([key, value]) => (
                      <li key={key}>
                        {FACTOR_LABELS[key] || key}: {(value * 100).toFixed(0)}%
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={{
                borderTop: '1px solid #e2e8f0',
                paddingTop: '0.5rem',
                fontSize: '0.85rem',
              }}>
                <p style={{ margin: '0 0 0.25rem' }}>
                  <strong>{beach.incident_count}</strong> incidente{beach.incident_count !== 1 ? 's' : ''} registrado{beach.incident_count !== 1 ? 's' : ''}
                </p>
                <Link
                  href={`/?beach=${beach.beach_id}`}
                  style={{ color: '#3b82f6', textDecoration: 'underline' }}
                >
                  Ver histórico →
                </Link>
              </div>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
