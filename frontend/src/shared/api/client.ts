import type {
  Account,
  CsrfToken,
  OrderDetailResponse,
  OrderListPage,
  OrderOperationResponse,
  PaymentOperationResponse,
  PaginatedCategoryList,
  PaginatedProductList,
  ProblemDetail,
  Product,
} from './generated'

const API_ROOT = '/api/v1'
let csrfToken: string | undefined

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly fields: Record<string, string>

  constructor(
    status: number,
    code: string,
    message: string,
    fields: Record<string, string> = {},
  ) {
    super(message)
    this.status = status
    this.code = code
    this.fields = fields
    this.name = 'ApiError'
  }
}

async function decode<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T
  const payload: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const problem = payload as Partial<ProblemDetail> | null
    const fieldErrors = Array.isArray(problem?.field_errors)
      ? Object.fromEntries(
          problem.field_errors.map((error) => [error.field, error.message]),
        )
      : {}
    throw new ApiError(
      response.status,
      problem?.code ?? 'REQUEST_FAILED',
      problem?.detail ??
        'No se pudo completar la solicitud. Inténtalo de nuevo.',
      fieldErrors,
    )
  }
  return payload as T
}

async function getCsrfToken(): Promise<string> {
  if (csrfToken) return csrfToken
  const response = await fetch(`${API_ROOT}/auth/csrf/`, {
    credentials: 'same-origin',
    headers: { Accept: 'application/json' },
  })
  const result = await decode<CsrfToken>(response)
  csrfToken = result.csrf_token
  return csrfToken
}

export function clearCsrfToken(): void {
  csrfToken = undefined
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  idempotencyKey?: string,
): Promise<T> {
  const method = (options.method ?? 'GET').toUpperCase()
  const headers = new Headers(options.headers)
  headers.set('Accept', 'application/json')
  if (options.body) headers.set('Content-Type', 'application/json')
  if (idempotencyKey) headers.set('Idempotency-Key', idempotencyKey)
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    headers.set('X-CSRFToken', await getCsrfToken())
  }
  return decode<T>(
    await fetch(`${API_ROOT}${path}`, {
      ...options,
      method,
      headers,
      credentials: 'same-origin',
    }),
  )
}

export const api = {
  async categories(): Promise<PaginatedCategoryList> {
    return request('/categories/')
  },
  async products(): Promise<PaginatedProductList> {
    return request('/products/?page_size=100&ordering=title')
  },
  async product(id: string): Promise<Product> {
    return request(`/products/${encodeURIComponent(id)}/`)
  },
  async currentUser(): Promise<Account | null> {
    try {
      return await request('/auth/me/')
    } catch (error) {
      if (error instanceof ApiError && error.status === 403) return null
      throw error
    }
  },
  async register(
    email: string,
    password: string,
  ): Promise<Account | { detail: string }> {
    return request<Account>('/auth/register/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  },
  async login(email: string, password: string): Promise<Account> {
    const account = await request<Account>('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    clearCsrfToken()
    return account
  },
  async requestPasswordReset(email: string): Promise<{ detail: string }> {
    return request('/auth/password-reset/', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  },
  async confirmPasswordReset(input: {
    user_id: string
    token: string
    password: string
  }): Promise<{ detail: string }> {
    return request('/auth/password-reset/confirm/', {
      method: 'POST',
      body: JSON.stringify(input),
    })
  },
  async requestEmailVerification(): Promise<{ detail: string }> {
    return request('/auth/email-verification/', { method: 'POST' })
  },
  async requestPublicEmailVerification(
    email: string,
  ): Promise<{ detail: string }> {
    return request('/auth/email-verification/request/', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  },
  async confirmEmailVerification(
    token: string,
  ): Promise<{ verified: boolean }> {
    return request('/auth/email-verification/confirm/', {
      method: 'POST',
      body: JSON.stringify({ token }),
    })
  },
  async logout(): Promise<void> {
    await request('/auth/logout/', { method: 'POST' })
    clearCsrfToken()
  },
  async orders(): Promise<OrderListPage> {
    return request('/orders/?page_size=100')
  },
  async order(id: string): Promise<OrderDetailResponse> {
    return request(`/orders/${encodeURIComponent(id)}/`)
  },
  async createOrder(
    body: {
      items: {
        product_id: string
        quantity: number
        expected_unit_price: string
      }[]
      delivery_address: {
        recipient: string
        address_line_1: string
        address_line_2?: string
        city: string
        region?: string
        postal_code?: string
        country_code: string
      }
    },
    key: string,
  ): Promise<OrderOperationResponse> {
    return request(
      '/orders/',
      { method: 'POST', body: JSON.stringify(body) },
      key,
    )
  },
  async simulatePayment(
    id: string,
    key: string,
  ): Promise<PaymentOperationResponse> {
    return request(
      `/orders/${encodeURIComponent(id)}/payment/`,
      { method: 'POST' },
      key,
    )
  },
  async cancelOrder(id: string, key: string): Promise<OrderOperationResponse> {
    return request(
      `/orders/${encodeURIComponent(id)}/cancel/`,
      { method: 'POST' },
      key,
    )
  },
}

export function idempotencyKey(): string {
  return crypto.randomUUID()
}
