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
})
