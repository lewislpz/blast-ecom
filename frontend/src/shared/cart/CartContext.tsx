import { useMemo, useState, type ReactNode } from 'react'

import { CartContext, type CartContextValue, type CartLine } from './cart-state'

export function CartProvider({ children }: { children: ReactNode }) {
  const [lines, setLines] = useState<CartLine[]>([])
  const value = useMemo<CartContextValue>(
    () => ({
      lines,
      count: lines.reduce((total, line) => total + line.quantity, 0),
      add(productId) {
        setLines((current) => {
          const existing = current.find((line) => line.productId === productId)
          if (existing) {
            return current.map((line) =>
              line.productId === productId
                ? { ...line, quantity: Math.min(line.quantity + 1, 99) }
                : line,
            )
          }
          return [...current, { productId, quantity: 1 }]
        })
      },
      setQuantity(productId, quantity) {
        setLines((current) =>
          quantity < 1
            ? current.filter((line) => line.productId !== productId)
            : current.map((line) =>
                line.productId === productId
                  ? { ...line, quantity: Math.min(quantity, 99) }
                  : line,
              ),
        )
      },
      remove(productId) {
        setLines((current) =>
          current.filter((line) => line.productId !== productId),
        )
      },
      clear() {
        setLines([])
      },
    }),
    [lines],
  )
  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}
