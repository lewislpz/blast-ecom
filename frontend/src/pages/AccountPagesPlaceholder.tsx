import { Link } from 'react-router'

export function AccountPagesPlaceholder() {
  return (
    <main className="page-container not-found">
      <p className="eyebrow">404 · No encontrado</p>
      <h1>Este rincón no existe.</h1>
      <Link className="button button-dark" to="/">
        Volver a la tienda <span>→</span>
      </Link>
    </main>
  )
}
