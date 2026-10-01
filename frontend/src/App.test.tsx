import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import App from './App'

const category = { id: 'category-id', slug: 'daily', name: 'Día a día' }
const products = {
  count: 1,
  next: null,
  previous: null,
  results: [
    {
      id: 'product-id',
      sku: 'BL-001',
      title: 'Taza Aurora',
      description: 'Una taza de prueba.',
      category,
      unit_price: '18.50',
      currency: 'EUR',
      in_stock: true,
      image_key: '',
    },
  ],
}

describe('customer storefront', () => {
  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('renders the live catalog and allows adding an item to the temporary cart', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/auth/me/')) return new Response(null, { status: 403 })
      if (url.includes('/products/')) return Response.json(products)
      if (url.includes('/categories/'))
        return Response.json({
          count: 1,
          next: null,
          previous: null,
          results: [category],
        })
      return new Response(null, { status: 404 })
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    expect(
      await screen.findByRole('heading', { name: 'Taza Aurora' }),
    ).toBeVisible()
    fireEvent.click(
      screen.getByRole('button', { name: 'Añadir Taza Aurora a la bolsa' }),
    )

    expect(
      screen.getByRole('link', { name: 'Carrito, 1 artículo' }),
    ).toHaveAttribute('href', '/cart')
  })

  it('shows an empty-search state and provides a filter recovery action', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/auth/me/')) return new Response(null, { status: 403 })
      if (url.includes('/products/'))
        return Response.json({
          count: 0,
          next: null,
          previous: null,
          results: [],
        })
      if (url.includes('/categories/'))
        return Response.json({
          count: 0,
          next: null,
          previous: null,
          results: [],
        })
      return new Response(null, { status: 404 })
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    expect(
      await screen.findByRole('heading', { name: 'Elige algo bueno.' }),
    ).toBeVisible()
    const search = screen.getByRole('textbox', { name: 'Buscar productos' })
    fireEvent.change(search, { target: { value: 'no-existe' } })
    expect(
      await screen.findByRole('heading', { name: 'No encontramos productos' }),
    ).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Limpiar filtros' }))
    await waitFor(() => expect(search).toHaveValue(''))
  })

  it('requests local password recovery without disclosing account existence', async () => {
    window.history.pushState({}, '', '/password-reset')
    const calls: string[] = []
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input)
      calls.push(url)
      if (url.endsWith('/auth/csrf/'))
        return Response.json({ csrf_token: 'local-csrf-token' })
      if (url.endsWith('/auth/password-reset/'))
        return Response.json(
          {
            detail:
              'If the account is eligible, password reset instructions were sent to the local development email console.',
          },
          { status: 202 },
        )
      return new Response(null, { status: 404 })
    })
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    fireEvent.change(screen.getByLabelText('Correo electrónico'), {
      target: { value: 'demo@example.test' },
    })
    fireEvent.click(
      screen.getByRole('button', { name: /Enviar instrucciones/ }),
    )

    expect(await screen.findByRole('status')).toHaveTextContent(
      'Si la cuenta puede recuperarse',
    )
    expect(calls).toContain('/api/v1/auth/password-reset/')
  })

  it('removes reset secrets from the address before submitting them in the body', async () => {
    const resetToken = 'test-reset-token-never-in-query'
    window.history.pushState(
      {},
      '',
      `/reset-password#user_id=account-id&token=${resetToken}`,
    )
    expect(window.location.hash).toContain(resetToken)
    const calls: { url: string; init?: RequestInit }[] = []
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input)
        calls.push({ url, init })
        if (url.endsWith('/auth/csrf/'))
          return Response.json({ csrf_token: 'local-csrf-token' })
        if (url.endsWith('/auth/password-reset/confirm/'))
          return Response.json({
            detail: 'The local demo password has been reset.',
          })
        return new Response(null, { status: 404 })
      },
    )
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    await waitFor(() => expect(window.location.hash).toBe(''))
    fireEvent.change(screen.getByLabelText('Nueva contraseña'), {
      target: { value: 'replacement-safe-password-123' },
    })
    fireEvent.change(screen.getByLabelText('Repite la contraseña'), {
      target: { value: 'replacement-safe-password-123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Cambiar contraseña' }))

    expect(await screen.findByRole('status')).toHaveTextContent(
      'has been reset',
    )
    const confirmation = calls.find((call) =>
      call.url.endsWith('/auth/password-reset/confirm/'),
    )
    expect(confirmation?.url).not.toContain(resetToken)
    expect(confirmation?.init?.body).toContain(resetToken)
  })

  it('confirms the demo email only after an explicit local action', async () => {
    const verificationToken = 'test-verification-token'
    window.history.pushState({}, '', `/verify-email#token=${verificationToken}`)
    const calls: { url: string; init?: RequestInit }[] = []
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input)
        calls.push({ url, init })
        if (url.endsWith('/auth/csrf/'))
          return Response.json({ csrf_token: 'local-csrf-token' })
        if (url.endsWith('/auth/email-verification/confirm/'))
          return Response.json({ verified: true })
        return new Response(null, { status: 404 })
      },
    )
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    await waitFor(() => expect(window.location.hash).toBe(''))
    expect(
      screen.getByText(/no demuestra la propiedad de un buzón real/i),
    ).toBeVisible()
    fireEvent.click(
      screen.getByRole('button', { name: 'Confirmar verificación local' }),
    )

    expect(await screen.findByRole('status')).toHaveTextContent(
      'ha quedado marcada como verificada',
    )
    const confirmation = calls.find((call) =>
      call.url.endsWith('/auth/email-verification/confirm/'),
    )
    expect(confirmation?.url).not.toContain(verificationToken)
    expect(confirmation?.init?.body).toContain(verificationToken)
  })
})
