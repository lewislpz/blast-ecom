import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('application placeholder', () => {
  it('identifies the product and does not imply that checkout is available', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: 'La tienda está en preparación' }),
    ).toBeVisible()
    expect(
      screen.getByText(/todavía no permite realizar compras/),
    ).toBeVisible()
  })
})
