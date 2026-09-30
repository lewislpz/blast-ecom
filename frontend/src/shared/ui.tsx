import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { useQuery } from '@tanstack/react-query'

import { api } from './api/client'
import { useCart } from './cart/useCart'

export function Loading({ label = 'Cargando…' }: { label?: string }) {
  return (
    <p className="status-message" role="status" aria-live="polite">
      <span className="spinner" aria-hidden="true" /> {label}
    </p>
  )
}

export function ErrorMessage({ children }: { children?: ReactNode }) {
  return (
    <div className="notice notice-error" role="alert">
      {children ??
        'No hemos podido cargar estos datos. Comprueba tu conexión e inténtalo de nuevo.'}
    </div>
  )
}

export function PageIntro({
  kicker,
  title,
  children,
}: {
  kicker: string
  title: string
  children?: ReactNode
}) {
  return (
    <div className="page-intro">
      <p className="eyebrow">{kicker}</p>
      <h1>{title}</h1>
      {children && <p className="intro-copy">{children}</p>}
    </div>
  )
}

export function Price({
  value,
  currency = 'EUR',
}: {
  value: string
  currency?: string
}) {
  return (
    <span className="price">
      {new Intl.NumberFormat('es-ES', { style: 'currency', currency }).format(
        Number(value),
      )}
    </span>
  )
}

export function ProductArt({ index = 0 }: { index?: number }) {
  return (
    <div className={`product-art art-${index % 4}`} aria-hidden="true">
      <span className="art-orbit" />
      <span className="art-spark">✳</span>
      <span className="art-label">
        BLAST
        <br />
        OBJECTS
      </span>
    </div>
  )
}

export function Header() {
  const cart = useCart()
  const account = useQuery({
    queryKey: ['session'],
    queryFn: api.currentUser,
    retry: false,
  })
  return (
    <header className="site-header">
      <Link className="brand" to="/" aria-label="Blast Ecom, inicio">
        <span className="brand-mark">B.</span>
        <span>
          blast<span className="brand-light">ecom</span>
        </span>
      </Link>
      <nav className="main-nav" aria-label="Navegación principal">
        <Link to="/">Tienda</Link>
        <Link to="/account/orders">Mis pedidos</Link>
      </nav>
      <div className="header-actions">
        {account.data ? (
          <Link
            className="account-link"
            to="/account/orders"
            aria-label={`Cuenta de ${account.data.email}`}
          >
            <span className="avatar" aria-hidden="true">
              {account.data.email[0]?.toUpperCase()}
            </span>
            <span className="account-label">Mi cuenta</span>
          </Link>
        ) : (
          <Link className="account-link" to="/login">
            Entrar
          </Link>
        )}
        <Link
          className="cart-link"
          to="/cart"
          aria-label={`Carrito, ${cart.count} ${cart.count === 1 ? 'artículo' : 'artículos'}`}
        >
          <span aria-hidden="true">↗</span> <span>Bolsa</span>
          <span className="cart-count">{cart.count}</span>
        </Link>
      </div>
    </header>
  )
}

export function Footer() {
  return (
    <footer className="site-footer">
      <Link className="brand footer-brand" to="/">
        <span className="brand-mark">B.</span>
        <span>blastecom</span>
      </Link>
      <p>Una tienda de demostración local. Sin pagos ni envíos reales.</p>
      <span>© Blast Ecom · Demo</span>
    </footer>
  )
}
