'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function AlertBadge() {
  const [count, setCount] = useState(0);

  const fetchCount = () => {
    fetch('http://localhost:8000/api/monitoring/summary/?days=7')
      .then((res) => res.ok ? res.json() : null)
      .then((data) => {
        if (data) setCount(data.total);
      })
      .catch(() => null);
  };

  useEffect(() => {
    fetchCount();
    const interval = setInterval(fetchCount, 2 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Link href="/alertas" className="btn btn-secondary" style={{ position: 'relative' }}>
      Alertas
      {count > 0 && (
        <span style={{
          position: 'absolute',
          top: '-6px',
          right: '-6px',
          background: 'var(--danger-color)',
          color: 'white',
          fontSize: '0.7rem',
          fontWeight: 700,
          width: '20px',
          height: '20px',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 2px 8px rgba(239, 68, 68, 0.5)',
          animation: 'pulse 2s infinite',
        }}>
          {count > 99 ? '99+' : count}
        </span>
      )}
    </Link>
  );
}
