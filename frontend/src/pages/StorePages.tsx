import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import { useQueries, useQuery } from '@tanstack/react-query'

import { api } from '../shared/api/client'
import { useCart } from '../shared/cart/useCart'
import {
  ErrorMessage,
  Loading,
  PageIntro,
  Price,
  ProductArt,
} from '../shared/ui'

function useCatalog() {
  return useQuery({
    queryKey: ['catalog'],
    queryFn: api.products,
    staleTime: 30_000,
  })
}

function ProductCard({
  product,
  index,
}: {
  product: NonNullable<ReturnType<typeof useCatalog>['data']>['results'][number]
  index: number
}) {
  const cart = useCart()
  return (
    <article className="product-card">
      <Link
        to={`/products/${product.id}`}
        className="product-image-link"
        aria-label={`Ver ${product.title}`}
      >
        <ProductArt index={index} />
        <span className="product-category">{product.category.name}</span>
      </Link>
      <div className="product-card-copy">
        <div>
          <p className="product-sku">{product.sku}</p>
          <h3>
            <Link to={`/products/${product.id}`}>{product.title}</Link>
          </h3>
        </div>
        <div className="product-card-bottom">
          <Price value={product.unit_price} currency={product.currency} />
          <button
            type="button"
            className="icon-button"
            aria-label={`Añadir ${product.title} a la bolsa`}
            disabled={!product.in_stock}
            onClick={() => cart.add(product.id)}
          >
            {product.in_stock ? '+' : '—'}
          </button>
        </div>
        {!product.in_stock && <p className="stock-note">Agotado por ahora</p>}
      </div>
    </article>
  )
}

export function CatalogPage() {
  const catalog = useCatalog()
  const categories = useQuery({
    queryKey: ['categories'],
    queryFn: api.categories,
    staleTime: 60_000,
  })
  const [category, setCategory] = useState('all')
  const [search, setSearch] = useState('')
  const products = useMemo(() => {
    const needle = search.trim().toLocaleLowerCase('es')
    return (catalog.data?.results ?? []).filter((product) => {
      const matchesCategory =
        category === 'all' || product.category.id === category
      const matchesSearch =
        !needle ||
        `${product.title} ${product.description ?? ''}`
          .toLocaleLowerCase('es')
          .includes(needle)
      return matchesCategory && matchesSearch
    })
  }, [catalog.data, category, search])

  return (
    <>
      <section className="hero-section">
        <div className="hero-copy">
          <p className="eyebrow">
            <span className="eyebrow-dot" /> Objetos para todos los días
          </p>
          <h1>
            Un poco de
            <br />
            <span>asombro.</span>
          </h1>
          <p>
            Diseño útil, detalles inesperados y pequeñas cosas que hacen mejor
            el día.
          </p>
          <a className="button button-dark" href="#catalogo">
            Explorar la tienda <span aria-hidden="true">↓</span>
          </a>
          <p className="hero-footnote">
            Colección de demostración · Envíos no disponibles
          </p>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="hero-sun" />
          <div className="hero-orbit orbit-one" />
          <div className="hero-orbit orbit-two" />
          <div className="hero-object">
            <span>✳</span>
          </div>
          <span className="hero-side-note">
            BUEN DISEÑO
            <br />
            SIN COMPLICACIONES
          </span>
          <span className="hero-number">01—04</span>
        </div>
      </section>

      <section className="catalog-section page-container" id="catalogo">
        <div className="catalog-heading">
          <div>
            <p className="eyebrow">La selección</p>
            <h2>Elige algo bueno.</h2>
          </div>
          <label className="search-field">
            <span className="visually-hidden">Buscar productos</span>
            <span aria-hidden="true">⌕</span>
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Busca algo…"
            />
          </label>
        </div>
        <div className="catalog-tools">
          <div
            className="category-filter"
            role="group"
            aria-label="Filtrar por categoría"
          >
            <button
              className={category === 'all' ? 'filter-active' : ''}
              onClick={() => setCategory('all')}
              type="button"
              aria-pressed={category === 'all'}
            >
              Todo
            </button>
            {(categories.data?.results ?? []).map((item) => (
              <button
                className={category === item.id ? 'filter-active' : ''}
                key={item.id}
                onClick={() => setCategory(item.id)}
                type="button"
                aria-pressed={category === item.id}
              >
                {item.name}
              </button>
            ))}
          </div>
          <span className="result-count">
            {catalog.data ? `${products.length} productos` : 'Colección'}
          </span>
        </div>
        {catalog.isLoading ? (
          <Loading label="Cargando la colección…" />
        ) : catalog.isError ? (
          <ErrorMessage />
        ) : products.length ? (
          <div className="product-grid">
            {products.map((product, index) => (
              <ProductCard key={product.id} product={product} index={index} />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <span className="empty-icon">✳</span>
            <h3>No encontramos productos</h3>
            <p>Prueba otra búsqueda o vuelve a ver toda la selección.</p>
            <button
              type="button"
              className="text-button"
              onClick={() => {
                setSearch('')
                setCategory('all')
              }}
            >
              Limpiar filtros
            </button>
          </div>
        )}
      </section>
      <DemoNotice />
    </>
  )
}

export function ProductPage() {
  const { id = '' } = useParams()
  const product = useQuery({
    queryKey: ['product', id],
    queryFn: () => api.product(id),
    enabled: Boolean(id),
  })
  const cart = useCart()
  if (product.isLoading)
    return (
      <main className="page-container page-content">
        <Loading label="Cargando producto…" />
      </main>
    )
  if (product.isError)
    return (
      <main className="page-container page-content">
        <ErrorMessage />
        <Link className="text-button" to="/">
          Volver a la tienda
        </Link>
      </main>
    )
  const item = product.data
  if (!item) return null
  return (
    <main className="page-container product-detail">
      <Link to="/" className="back-link">
        ← Volver a la tienda
      </Link>
      <div className="product-detail-grid">
        <ProductArt index={2} />
        <div className="product-detail-copy">
          <p className="eyebrow">
            {item.category.name} · {item.sku}
          </p>
          <h1>{item.title}</h1>
          <Price value={item.unit_price} currency={item.currency} />
          <p className="product-description">
            {item.description ||
              'Una pieza seleccionada para acompañarte en tu día a día.'}
          </p>
          <p
            className={
              item.in_stock ? 'availability' : 'availability unavailable'
            }
          >
            <span />
            {item.in_stock ? 'Disponible en esta demo' : 'Agotado por ahora'}
          </p>
          <button
            className="button button-dark add-to-cart"
            type="button"
            disabled={!item.in_stock}
            onClick={() => cart.add(item.id)}
          >
            {item.in_stock ? 'Añadir a la bolsa' : 'No disponible'}{' '}
            <span aria-hidden="true">↗</span>
          </button>
          <p className="demo-copy">
            Precio y disponibilidad verificados por el servidor. Simulación
            local, sin compra real.
          </p>
        </div>
      </div>
    </main>
  )
}

export function CartPage() {
  const cart = useCart()
  const products = useQueries({
    queries: cart.lines.map((line) => ({
      queryKey: ['product', line.productId],
      queryFn: () => api.product(line.productId),
    })),
  })
  const navigate = useNavigate()
  const loading = products.some((query) => query.isLoading)
  const failed = products.some((query) => query.isError)
  const lines = cart.lines
    .map((line, index) => ({ line, product: products[index]?.data }))
    .filter((item) => item.product)
  const total = lines.reduce(
    (sum, item) =>
      sum + Number(item.product?.unit_price ?? 0) * item.line.quantity,
    0,
  )
  return (
    <main className="page-container page-content">
      <PageIntro kicker="Tu selección" title="La bolsa.">
        {cart.count
          ? `${cart.count} ${cart.count === 1 ? 'artículo' : 'artículos'} seleccionados.`
          : 'Todavía no has elegido nada.'}
      </PageIntro>
      {loading ? (
        <Loading label="Actualizando tu bolsa…" />
      ) : failed ? (
        <ErrorMessage />
      ) : !lines.length ? (
        <div className="empty-state cart-empty">
          <span className="empty-icon">↗</span>
          <h2>Vamos a encontrar algo.</h2>
          <p>
            Tu bolsa vive en esta sesión y se vacía al cerrar o recargar la
            página.
          </p>
          <Link to="/" className="button button-dark">
            Ver la tienda <span>→</span>
          </Link>
        </div>
      ) : (
        <div className="cart-layout">
          <div className="cart-lines">
            {lines.map(
              ({ line, product }, index) =>
                product && (
                  <article className="cart-line" key={line.productId}>
                    <ProductArt index={index} />
                    <div className="cart-product-info">
                      <p className="product-sku">{product.sku}</p>
                      <h2>
                        <Link to={`/products/${product.id}`}>
                          {product.title}
                        </Link>
                      </h2>
                      <Price value={product.unit_price} />
                    </div>
                    <label className="quantity-field">
                      <span className="visually-hidden">
                        Cantidad de {product.title}
                      </span>
                      <button
                        type="button"
                        aria-label={`Reducir cantidad de ${product.title}`}
                        onClick={() =>
                          cart.setQuantity(product.id, line.quantity - 1)
                        }
                      >
                        −
                      </button>
                      <input
                        type="number"
                        min="1"
                        max="99"
                        value={line.quantity}
                        onChange={(event) =>
                          cart.setQuantity(
                            product.id,
                            Number(event.target.value),
                          )
                        }
                      />
                      <button
                        type="button"
                        aria-label={`Aumentar cantidad de ${product.title}`}
                        onClick={() =>
                          cart.setQuantity(product.id, line.quantity + 1)
                        }
                      >
                        +
                      </button>
                    </label>
                    <button
                      type="button"
                      className="remove-link"
                      onClick={() => cart.remove(product.id)}
                    >
                      Quitar
                    </button>
                  </article>
                ),
            )}
          </div>
          <aside className="cart-summary">
            <p className="eyebrow">Resumen</p>
            <div className="summary-row">
              <span>Subtotal estimado</span>
              <Price value={total.toFixed(2)} />
            </div>
            <div className="summary-row">
              <span>Envío</span>
              <span>—</span>
            </div>
            <p className="summary-note">
              El servidor confirma el precio final al crear el pedido. En esta
              demo no hay envío real.
            </p>
            <button
              type="button"
              className="button button-dark full-button"
              onClick={() => navigate('/checkout')}
            >
              Continuar <span>→</span>
            </button>
            <Link className="continue-link" to="/">
              Seguir mirando
            </Link>
          </aside>
        </div>
      )}
    </main>
  )
}

export function DemoNotice() {
  return (
    <aside className="demo-banner page-container">
      <span className="demo-banner-icon">✳</span>
      <div>
        <strong>Una demo, no una tienda real.</strong>
        <p>
          Los pagos son simulados y el envío no está conectado. No introduzcas
          información financiera.
        </p>
      </div>
      <span className="demo-pill">MODO DEMO</span>
    </aside>
  )
}
