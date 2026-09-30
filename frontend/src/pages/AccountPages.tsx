import { useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import { api, ApiError, idempotencyKey } from '../shared/api/client'
import type {
  OrderOperationResponse,
  PaymentOperationResponse,
} from '../shared/api/generated'
import { useCart } from '../shared/cart/useCart'
import {
  ErrorMessage,
  Loading,
  PageIntro,
  Price,
  ProductArt,
} from '../shared/ui'

function messageFor(error: unknown): string {
  if (!(error instanceof ApiError))
    return 'No hemos podido conectar. Revisa tu conexión e inténtalo de nuevo.'
  if (error.code === 'AUTH_INVALID')
    return 'El correo o la contraseña no son correctos.'
  if (error.code === 'ACCOUNT_UNAVAILABLE')
    return 'No se ha podido crear la cuenta con esos datos.'
  if (error.code === 'PRICE_CHANGED')
    return 'El precio de un producto ha cambiado. Revisa el total actualizado antes de continuar.'
  if (error.code === 'OUT_OF_STOCK')
    return 'Ya no hay unidades suficientes. Ajusta la cantidad antes de continuar.'
  if (error.code === 'PRODUCT_UNAVAILABLE')
    return 'Uno de los productos ya no está disponible.'
  if (error.code === 'ORDER_EXPIRED')
    return 'El tiempo de reserva terminó. Vuelve a la tienda para iniciar otro pedido.'
  if (
    error.code === 'ORDER_NOT_PAYABLE' ||
    error.code === 'PAYMENT_ALREADY_RECORDED'
  )
    return 'Este pedido ya no admite otro intento de pago.'
  return error.fields.password ?? error.fields.email ?? error.message
}

export function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const registering = mode === 'register'

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const account = registering
        ? await api.register(email, password)
        : await api.login(email, password)
      setPassword('')
      if (registering) {
        setError(
          'Cuenta de demo creada. Ya puedes entrar con tus credenciales.',
        )
      } else {
        queryClient.setQueryData(['session'], account)
        await queryClient.invalidateQueries({ queryKey: ['session'] })
        navigate('/account/orders')
      }
    } catch (cause) {
      setError(messageFor(cause))
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page page-container">
      <div className="auth-art">
        <ProductArt index={1} />
        <p className="eyebrow">Tu espacio Blast</p>
        <h2>
          Las cosas buenas
          <br />
          te esperan.
        </h2>
        <p>Accede a tus pedidos y continúa donde lo dejaste.</p>
      </div>
      <section className="auth-panel">
        <Link to="/" className="back-link">
          ← Volver a la tienda
        </Link>
        <p className="eyebrow">
          {registering ? 'Empieza por aquí' : 'Qué bueno verte'}
        </p>
        <h1>{registering ? 'Crea tu cuenta.' : 'Bienvenido de vuelta.'}</h1>
        <p>
          {registering
            ? 'Crea una cuenta local de demostración.'
            : 'Entra para consultar tus pedidos.'}
        </p>
        <form className="form-stack" onSubmit={submit}>
          <label htmlFor="email">Correo electrónico</label>
          <input
            id="email"
            autoComplete="email"
            type="email"
            required
            maxLength={254}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            autoComplete={registering ? 'new-password' : 'current-password'}
            type="password"
            required
            minLength={registering ? 12 : undefined}
            maxLength={128}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          {registering && (
            <p className="field-hint">
              Al menos 12 caracteres. La cuenta se crea sólo para esta demo
              local.
            </p>
          )}
          {error && (
            <p
              className={
                registering && error.startsWith('Cuenta')
                  ? 'notice notice-success'
                  : 'notice notice-error'
              }
              role="alert"
            >
              {error}
            </p>
          )}
          <button
            className="button button-dark full-button"
            type="submit"
            disabled={busy}
          >
            {busy ? 'Un momento…' : registering ? 'Crear cuenta' : 'Entrar'}{' '}
            <span aria-hidden="true">→</span>
          </button>
        </form>
        <p className="auth-switch">
          {registering ? '¿Ya tienes cuenta?' : '¿Aún no tienes cuenta?'}{' '}
          <Link to={registering ? '/login' : '/register'}>
            {registering ? 'Entra aquí' : 'Regístrate'}
          </Link>
        </p>
        <p className="demo-copy">
          La creación de cuentas está disponible únicamente en el entorno local
          de demostración.
        </p>
      </section>
    </main>
  )
}

type CheckoutAddress = {
  recipient: string
  address_line_1: string
  address_line_2: string
  city: string
  region: string
  postal_code: string
  country_code: string
}

export function CheckoutPage() {
  const cart = useCart()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const session = useQuery({
    queryKey: ['session'],
    queryFn: api.currentUser,
    retry: false,
  })
  const productQueries = useQueries({
    queries: cart.lines.map((line) => ({
      queryKey: ['product', line.productId],
      queryFn: () => api.product(line.productId),
      staleTime: 0,
    })),
  })
  const products = cart.lines.map((line, index) => ({
    line,
    product: productQueries[index]?.data,
  }))
  const key = useRef<string | null>(null)
  const [error, setError] = useState('')
  const [priceConflict, setPriceConflict] = useState(false)
  const [priceReviewed, setPriceReviewed] = useState(false)
  const [address, setAddress] = useState<CheckoutAddress>({
    recipient: '',
    address_line_1: '',
    address_line_2: '',
    city: '',
    region: '',
    postal_code: '',
    country_code: 'ES',
  })
  const mutation = useMutation({
    mutationFn: () => {
      key.current ??= idempotencyKey()
      return api.createOrder(
        {
          items: products.flatMap(({ line, product }) =>
            product
              ? [
                  {
                    product_id: product.id,
                    quantity: line.quantity,
                    expected_unit_price: product.unit_price,
                  },
                ]
              : [],
          ),
          delivery_address: address,
        },
        key.current,
      )
    },
    onSuccess: async (order) => {
      key.current = null
      cart.clear()
      await queryClient.invalidateQueries({ queryKey: ['orders'] })
      navigate(`/orders/${order.id}`)
    },
    onError: async (cause) => {
      if (cause instanceof ApiError) key.current = null
      if (
        cause instanceof ApiError &&
        ['PRICE_CHANGED', 'PRODUCT_UNAVAILABLE', 'OUT_OF_STOCK'].includes(
          cause.code,
        )
      ) {
        setPriceConflict(cause.code === 'PRICE_CHANGED')
        setPriceReviewed(false)
        await Promise.all([
          queryClient.invalidateQueries({ queryKey: ['product'] }),
          queryClient.invalidateQueries({ queryKey: ['catalog'] }),
        ])
      }
      setError(messageFor(cause))
    },
  })
  const ready =
    session.data &&
    !session.isLoading &&
    products.length > 0 &&
    products.every(
      ({ product }, index) => product && !productQueries[index]?.isFetching,
    )
  const total = products.reduce(
    (sum, { line, product }) =>
      sum + Number(product?.unit_price ?? 0) * line.quantity,
    0,
  )

  if (session.isLoading || productQueries.some((query) => query.isLoading))
    return (
      <main className="page-container page-content">
        <Loading label="Preparando tu pedido…" />
      </main>
    )
  if (session.isError)
    return (
      <main className="page-container page-content">
        <ErrorMessage />
      </main>
    )
  if (!session.data)
    return (
      <main className="page-container page-content">
        <PageIntro kicker="Un paso más" title="Entra para continuar." />
        <div className="notice">
          La bolsa se conserva mientras esta página siga abierta.
        </div>
        <Link className="button button-dark" to="/login">
          Entrar o crear cuenta <span>→</span>
        </Link>
      </main>
    )
  if (!cart.lines.length)
    return (
      <main className="page-container page-content">
        <PageIntro kicker="Tu pedido" title="La bolsa está vacía." />
        <Link className="button button-dark" to="/">
          Volver a la tienda
        </Link>
      </main>
    )

  function updateAddress(field: keyof CheckoutAddress, value: string) {
    setAddress((current) => ({ ...current, [field]: value }))
    key.current = null
  }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    mutation.mutate()
  }

  return (
    <main className="page-container page-content checkout-page">
      <PageIntro kicker="Último paso" title="Prepara tu pedido.">
        El pago es una simulación del servidor. No se procesará ningún cobro.
      </PageIntro>
      <div className="demo-warning" role="note">
        <strong>Datos ficticios, por favor.</strong> La dirección queda guardada
        en los datos locales de este pedido. No introduzcas tu dirección real.
      </div>
      {error && (
        <div className="notice notice-error" role="alert">
          {error}
        </div>
      )}
      {priceConflict && (
        <div
          className="price-review"
          role="region"
          aria-label="Revisión del precio"
        >
          <span>↻</span>
          <div>
            <strong>Hemos actualizado la colección</strong>
            <p>
              Revisa los precios que aparecen en el resumen antes de confirmar
              el pedido.
            </p>
            <label>
              <input
                type="checkbox"
                checked={priceReviewed}
                onChange={(event) => setPriceReviewed(event.target.checked)}
              />{' '}
              He revisado y acepto los precios actualizados
            </label>
          </div>
        </div>
      )}
      <div className="checkout-layout">
        <form className="checkout-form" onSubmit={submit}>
          <section className="checkout-section">
            <span className="step-number">01</span>
            <div>
              <h2>¿A quién va dirigido?</h2>
              <p className="form-section-copy">
                Usa datos inventados. El envío real no está disponible.
              </p>
              <div className="form-grid">
                <label className="wide-field">
                  Nombre de prueba
                  <input
                    required
                    maxLength={160}
                    autoComplete="off"
                    value={address.recipient}
                    onChange={(event) =>
                      updateAddress('recipient', event.target.value)
                    }
                  />
                </label>
                <label className="wide-field">
                  Dirección ficticia
                  <input
                    required
                    maxLength={200}
                    autoComplete="off"
                    value={address.address_line_1}
                    onChange={(event) =>
                      updateAddress('address_line_1', event.target.value)
                    }
                  />
                </label>
                <label>
                  Ciudad
                  <input
                    required
                    maxLength={120}
                    autoComplete="off"
                    value={address.city}
                    onChange={(event) =>
                      updateAddress('city', event.target.value)
                    }
                  />
                </label>
                <label>
                  Código postal de prueba
                  <input
                    maxLength={32}
                    autoComplete="off"
                    value={address.postal_code}
                    onChange={(event) =>
                      updateAddress('postal_code', event.target.value)
                    }
                  />
                </label>
                <label>
                  Provincia / región
                  <input
                    maxLength={120}
                    autoComplete="off"
                    value={address.region}
                    onChange={(event) =>
                      updateAddress('region', event.target.value)
                    }
                  />
                </label>
                <label>
                  País
                  <input
                    required
                    minLength={2}
                    maxLength={2}
                    pattern="[A-Z]{2}"
                    autoComplete="off"
                    value={address.country_code}
                    onChange={(event) =>
                      updateAddress(
                        'country_code',
                        event.target.value.toUpperCase(),
                      )
                    }
                  />
                </label>
              </div>
            </div>
          </section>
          <section className="checkout-section payment-preview">
            <span className="step-number">02</span>
            <div>
              <h2>Pago de demostración</h2>
              <p>
                El resultado lo decide el servidor. No hay tarjeta ni proveedor
                de pagos conectado.
              </p>
              <div className="payment-chip">
                ✳ &nbsp; Simulación segura · sin cobro
              </div>
            </div>
          </section>
          <button
            className="button button-dark full-button checkout-submit"
            type="submit"
            disabled={
              !ready || mutation.isPending || (priceConflict && !priceReviewed)
            }
          >
            {mutation.isPending
              ? 'Creando pedido…'
              : 'Crear pedido de demostración'}{' '}
            <span aria-hidden="true">→</span>
          </button>
          <p className="checkout-terms">
            Al continuar confirmas que entiendes que se trata de una simulación
            local sin envío real.
          </p>
        </form>
        <aside className="cart-summary order-summary">
          <p className="eyebrow">Tu selección</p>
          <div className="summary-products">
            {products.map(
              ({ line, product }, index) =>
                product && (
                  <div className="summary-product" key={line.productId}>
                    <ProductArt index={index} />
                    <div>
                      <strong>{product.title}</strong>
                      <span>Cantidad: {line.quantity}</span>
                    </div>
                    <Price
                      value={(
                        Number(product.unit_price) * line.quantity
                      ).toFixed(2)}
                    />
                  </div>
                ),
            )}
          </div>
          <div className="summary-row">
            <span>Subtotal</span>
            <Price value={total.toFixed(2)} />
          </div>
          <div className="summary-row">
            <span>Envío</span>
            <span>0,00 €</span>
          </div>
          <div className="summary-row summary-total">
            <strong>Total orientativo</strong>
            <Price value={total.toFixed(2)} />
          </div>
          <p className="summary-note">
            El servidor recalcula todo al confirmar. Si el precio cambia,
            pediremos una nueva confirmación.
          </p>
        </aside>
      </div>
    </main>
  )
}

export function OrdersPage() {
  const queryClient = useQueryClient()
  const session = useQuery({
    queryKey: ['session'],
    queryFn: api.currentUser,
    retry: false,
  })
  const orders = useQuery({
    queryKey: ['orders'],
    queryFn: api.orders,
    enabled: Boolean(session.data),
  })
  const cart = useCart()
  const navigate = useNavigate()
  const logout = useMutation({
    mutationFn: api.logout,
    onSuccess: async () => {
      cart.clear()
      queryClient.clear()
      navigate('/')
    },
  })
  if (session.isLoading)
    return (
      <main className="page-container page-content">
        <Loading label="Comprobando tu sesión…" />
      </main>
    )
  if (session.isError)
    return (
      <main className="page-container page-content">
        <ErrorMessage />
      </main>
    )
  if (!session.data)
    return (
      <main className="page-container page-content">
        <PageIntro
          kicker="Tu cuenta"
          title="Inicia sesión para ver tus pedidos."
        />
        <Link className="button button-dark" to="/login">
          Entrar <span>→</span>
        </Link>
      </main>
    )
  return (
    <main className="page-container page-content">
      <div className="orders-page-heading">
        <PageIntro kicker="Tu cuenta" title="Tus pedidos.">
          {session.data.email}
        </PageIntro>
        <button
          className="text-button"
          type="button"
          disabled={logout.isPending}
          onClick={() => logout.mutate()}
        >
          Cerrar sesión ↗
        </button>
      </div>
      {logout.isError && (
        <ErrorMessage>
          No se pudo cerrar la sesión. Inténtalo de nuevo.
        </ErrorMessage>
      )}
      {orders.isLoading ? (
        <Loading label="Cargando tus pedidos…" />
      ) : orders.isError ? (
        <ErrorMessage />
      ) : !orders.data?.results.length ? (
        <div className="empty-state orders-empty">
          <span className="empty-icon">◷</span>
          <h2>Aún no hay pedidos.</h2>
          <p>
            Cuando confirmes tu primera compra de demostración, aparecerá aquí.
          </p>
          <Link className="text-button" to="/">
            Descubrir la tienda →
          </Link>
        </div>
      ) : (
        <div className="order-list">
          {orders.data.results.map((order) => (
            <Link
              className="order-card"
              key={order.id}
              to={`/orders/${order.id}`}
            >
              <div>
                <p className="product-sku">
                  Pedido · {order.id.slice(0, 8).toUpperCase()}
                </p>
                <strong>
                  {new Date(order.created_at).toLocaleDateString('es-ES', {
                    dateStyle: 'long',
                  })}
                </strong>
                <span>
                  {order.items.length}{' '}
                  {order.items.length === 1 ? 'artículo' : 'artículos'}
                </span>
              </div>
              <OrderState state={order.state} />
              <Price value={order.total} currency={order.currency} />
              <span className="order-chevron" aria-hidden="true">
                →
              </span>
            </Link>
          ))}
        </div>
      )}
    </main>
  )
}

function OrderState({ state }: { state: string }) {
  const labels: Record<string, string> = {
    awaiting_payment: 'Pendiente de pago',
    confirmed: 'Confirmado',
    failed: 'Fallido',
    cancelled: 'Cancelado',
    expired: 'Expirado',
  }
  return (
    <span
      className={`order-state state-${state}`}
      role="status"
      aria-live="polite"
    >
      {labels[state] ?? state}
    </span>
  )
}

export function OrderDetailPage() {
  const { id = '' } = useParams()
  const queryClient = useQueryClient()
  const session = useQuery({
    queryKey: ['session'],
    queryFn: api.currentUser,
    retry: false,
  })
  const order = useQuery({
    queryKey: ['order', id],
    queryFn: () => api.order(id),
    enabled: Boolean(session.data && id),
  })
  const key = useRef<string | null>(null)
  const action = useMutation<
    OrderOperationResponse | PaymentOperationResponse,
    Error,
    'payment' | 'cancel'
  >({
    mutationFn: (type: 'payment' | 'cancel') => {
      key.current ??= idempotencyKey()
      return type === 'payment'
        ? api.simulatePayment(id, key.current)
        : api.cancelOrder(id, key.current)
    },
    onSuccess: async () => {
      key.current = null
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['order', id] }),
        queryClient.invalidateQueries({ queryKey: ['orders'] }),
      ])
    },
    onError: (cause) => {
      if (cause instanceof ApiError) key.current = null
    },
  })
  if (session.isLoading || order.isLoading)
    return (
      <main className="page-container page-content">
        <Loading label="Cargando pedido…" />
      </main>
    )
  if (session.isError)
    return (
      <main className="page-container page-content">
        <ErrorMessage />
      </main>
    )
  if (!session.data)
    return (
      <main className="page-container page-content">
        <PageIntro kicker="Pedido" title="Entra para continuar." />
        <Link className="button button-dark" to="/login">
          Entrar
        </Link>
      </main>
    )
  if (order.isError || !order.data)
    return (
      <main className="page-container page-content">
        <ErrorMessage>
          Este pedido no está disponible en tu cuenta.
        </ErrorMessage>
        <Link className="text-button" to="/account/orders">
          Volver a mis pedidos
        </Link>
      </main>
    )
  const item = order.data
  const canAct = item.state === 'awaiting_payment'
  return (
    <main className="page-container page-content order-detail-page">
      <Link className="back-link" to="/account/orders">
        ← Mis pedidos
      </Link>
      <div className="order-detail-heading">
        <div>
          <p className="eyebrow">Pedido de demostración</p>
          <h1>Gracias por tu pedido.</h1>
          <p className="order-reference">
            Referencia {item.id.slice(0, 8).toUpperCase()} ·{' '}
            {new Date(item.created_at).toLocaleString('es-ES')}
          </p>
        </div>
        <OrderState state={item.state} />
      </div>
      <div className="notice demo-order-notice">
        Este pedido y su pago son simulados. No se ha realizado ningún cargo ni
        envío.
      </div>
      {item.state === 'awaiting_payment' && (
        <p className="reservation-note">
          Reserva temporal hasta{' '}
          {new Date(item.expires_at).toLocaleString('es-ES')}. El sistema la
          liberará si vence.
        </p>
      )}
      {action.error && (
        <div className="notice notice-error" role="alert">
          {messageFor(action.error)}
        </div>
      )}
      {item.state === 'confirmed' && (
        <div className="notice notice-success">
          Pago de demostración aceptado por el simulador. Pedido confirmado;
          esto no representa un envío.
        </div>
      )}
      {item.state === 'failed' && (
        <div className="notice notice-error">
          El simulador rechazó el pago. No se ha realizado ningún cargo.
        </div>
      )}
      <div className="order-detail-layout">
        <section className="order-items-panel">
          <h2>Artículos</h2>
          {item.items.map((line) => (
            <div className="order-item" key={line.product_id}>
              <div>
                <strong>{line.title}</strong>
                <span>
                  {line.sku} · {line.quantity} ud.
                </span>
              </div>
              <Price value={line.line_total} currency={item.currency} />
            </div>
          ))}
          <div className="summary-row summary-total">
            <strong>Total</strong>
            <Price value={item.total} currency={item.currency} />
          </div>
          <div className="delivery-panel">
            <h3>Dirección de prueba</h3>
            <p>
              {item.delivery_address.recipient}
              <br />
              {item.delivery_address.address_line_1}
              <br />
              {item.delivery_address.city}, {item.delivery_address.postal_code}
              <br />
              {item.delivery_address.country_code}
            </p>
          </div>
        </section>
        <aside className="cart-summary order-actions">
          <p className="eyebrow">Siguiente paso</p>
          {canAct ? (
            <>
              <p>
                Elige qué hacer con este pedido pendiente. El resultado del pago
                lo decide el servidor.
              </p>
              <button
                type="button"
                className="button button-dark full-button"
                disabled={action.isPending}
                onClick={() => action.mutate('payment')}
              >
                {action.isPending ? 'Procesando…' : 'Simular pago'}{' '}
                <span>→</span>
              </button>
              <button
                type="button"
                className="button button-outline full-button"
                disabled={action.isPending}
                onClick={() => action.mutate('cancel')}
              >
                Cancelar pedido
              </button>
              <p className="summary-note">
                No se solicitan ni procesan datos de tarjeta.
              </p>
            </>
          ) : (
            <>
              <p>Este pedido ya no admite acciones.</p>
              <Link
                className="button button-outline full-button"
                to="/account/orders"
              >
                Ver mis pedidos
              </Link>
            </>
          )}
        </aside>
      </div>
    </main>
  )
}
