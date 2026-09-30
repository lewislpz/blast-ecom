import { afterEach, describe, expect, it, vi } from 'vitest'

import { api, clearCsrfToken } from './client'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('same-origin API client', () => {
  afterEach(() => {
    clearCsrfToken()
    vi.unstubAllGlobals()
  })

  it('fetches CSRF before unsafe requests, sends the session cookie and refreshes after login', async () => {
    const calls: { url: string; init?: RequestInit }[] = []
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input)
        calls.push({ url, init })
        if (url.endsWith('/auth/csrf/')) {
          return jsonResponse({ csrf_token: `token-${calls.length}` })
        }
        if (url.endsWith('/auth/login/')) {
          return jsonResponse({ id: 'user-id', email: 'demo@example.test' })
        }
        return new Response(null, { status: 204 })
      },
    )
    vi.stubGlobal('fetch', fetchMock)

    await api.login('demo@example.test', 'example-password')
    await api.logout()

    const loginHeaders = new Headers(calls[1]?.init?.headers)
    const logoutHeaders = new Headers(calls[3]?.init?.headers)
    expect(calls.map((call) => call.url)).toEqual([
      '/api/v1/auth/csrf/',
      '/api/v1/auth/login/',
      '/api/v1/auth/csrf/',
      '/api/v1/auth/logout/',
    ])
    expect(loginHeaders.get('X-CSRFToken')).toBe('token-1')
    expect(logoutHeaders.get('X-CSRFToken')).toBe('token-3')
    expect(
      calls.every((call) => call.init?.credentials === 'same-origin'),
    ).toBe(true)
    expect(calls[1]?.init?.body).toBe(
      JSON.stringify({
        email: 'demo@example.test',
        password: 'example-password',
      }),
    )
  })

  it('preserves server error codes and field validation without exposing response internals', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      if (String(input).endsWith('/auth/csrf/'))
        return jsonResponse({ csrf_token: 'token' })
      return jsonResponse(
        {
          type: 'about:blank',
          title: 'Invalid request',
          status: 400,
          detail: 'The operation could not be completed.',
          code: 'INVALID_INPUT',
          request_id: 'request-id',
          field_errors: [
            {
              field: 'email',
              code: 'invalid',
              message: 'Enter a valid email.',
            },
          ],
        },
        400,
      )
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(api.login('bad', 'password')).rejects.toMatchObject({
      status: 400,
      code: 'INVALID_INPUT',
      fields: { email: 'Enter a valid email.' },
    })
  })

  it('sends the caller-provided idempotency key and makes only one network attempt', async () => {
    const fetchMock = vi.fn(
      async (input: RequestInfo | URL, _init?: RequestInit) => {
        void _init
        if (String(input).endsWith('/auth/csrf/'))
          return jsonResponse({ csrf_token: 'token' })
        return jsonResponse(
          {
            code: 'PRICE_CHANGED',
            detail: 'The operation could not be completed.',
          },
          409,
        )
      },
    )
    vi.stubGlobal('fetch', fetchMock)

    const request = api.createOrder(
      {
        items: [
          {
            product_id: 'product-id',
            quantity: 1,
            expected_unit_price: '12.50',
          },
        ],
        delivery_address: {
          recipient: 'Demo User',
          address_line_1: 'Fictional Street 1',
          city: 'Madrid',
          country_code: 'ES',
        },
      },
      'f0e63e1a-48ab-4c93-a9bb-48cf83f97925',
    )

    await expect(request).rejects.toMatchObject({ code: 'PRICE_CHANGED' })
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(
      new Headers(fetchMock.mock.calls[1]?.[1]?.headers).get('Idempotency-Key'),
    ).toBe('f0e63e1a-48ab-4c93-a9bb-48cf83f97925')
  })
})
