'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Beach {
  id: number;
  name: string;
}

export default function NovaIncidencia() {
  const router = useRouter();
  const [beaches, setBeaches] = useState<Beach[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    beach: '',
    date: '',
    incident_type: '',
    severity: 'Baixa',
    description: '',
  });

  useEffect(() => {
    fetch('http://localhost:8000/api/praias/')
      .then((res) => res.json())
      .then((data) => setBeaches(data))
      .catch((err) => console.error('Erro ao buscar praias:', err));
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await fetch('http://localhost:8000/api/incidentes/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!res.ok) {
        throw new Error('Falha ao criar incidência. Verifique os dados.');
      }

      router.push('/');
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="glass-container" style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2>Nova Incidência</h2>
      <p style={{ marginBottom: '2rem' }}>Preencha os dados abaixo para registrar uma nova incidência.</p>

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.2)', border: '1px solid #ef4444', borderRadius: '8px', marginBottom: '1.5rem', color: '#fca5a5' }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="beach">Praia</label>
          <select 
            id="beach" 
            name="beach" 
            className="form-select" 
            value={formData.beach}
            onChange={handleChange}
            required
          >
            <option value="">Selecione uma praia...</option>
            {beaches.map(b => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="date">Data da Incidência</label>
          <input 
            type="date" 
            id="date" 
            name="date" 
            className="form-input" 
            value={formData.date}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="incident_type">Tipo de Incidência</label>
          <input 
            type="text" 
            id="incident_type" 
            name="incident_type" 
            className="form-input" 
            value={formData.incident_type}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="severity">Gravidade</label>
          <select 
            id="severity" 
            name="severity" 
            className="form-select" 
            value={formData.severity}
            onChange={handleChange}
            required
          >
            <option value="Baixa">Baixa</option>
            <option value="Média">Média</option>
            <option value="Alta">Alta</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="description">Descrição (Opcional)</label>
          <textarea 
            id="description" 
            name="description" 
            className="form-textarea" 
            placeholder="Detalhes adicionais sobre a incidência..."
            value={formData.description}
            onChange={handleChange}
          ></textarea>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
          <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%' }}>
            {loading ? 'Salvando...' : 'Registrar Incidência'}
          </button>
        </div>
      </form>
    </div>
  );
}
