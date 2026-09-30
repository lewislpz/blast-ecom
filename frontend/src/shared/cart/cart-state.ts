import { createContext } from 'react'

export type CartLine = { productId: string; quantity: number }
export type CartContextValue = {
  lines: CartLine[]
  count: number
  add: (productId: string) => void
  setQuantity: (productId: string, quantity: number) => void
  remove: (productId: string) => void
  clear: () => void
}

export const CartContext = createContext<CartContextValue | null>(null)
