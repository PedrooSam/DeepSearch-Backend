import type { Metadata } from 'next'
import './globals.css'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'DeepSearch | Incidências',
  description: 'Gerenciamento de Incidências Marítimas',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="pt-BR">
      <body>
        <div className="page-wrapper animate-fade-in">
          <header className="header">
            <div>
              <h1>DeepSearch</h1>
              <p>Monitoramento de Praias e Incidências</p>
            </div>
            <nav style={{ display: 'flex', gap: '1rem' }}>
              <Link href="/" className="btn btn-secondary">Dashboard</Link>
              <Link href="/nova" className="btn btn-primary">+ Nova Incidência</Link>
            </nav>
          </header>
          <main>
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
