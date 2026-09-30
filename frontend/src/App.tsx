import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes, useLocation } from 'react-router'
import { useEffect, useState } from 'react'

import { CartProvider } from './shared/cart/CartContext'
import { Footer, Header } from './shared/ui'
import { AccountPagesPlaceholder } from './pages/AccountPagesPlaceholder'
import {
  AuthPage,
  CheckoutPage,
  OrderDetailPage,
  OrdersPage,
} from './pages/AccountPages'
import { CartPage, CatalogPage, ProductPage } from './pages/StorePages'
import './styles/global.css'

function StoreRoutes() {
  return (
    <CartProvider>
      <BrowserRouter>
        <div className="app-shell">
          <RouteFocus />
          <Header />
          <div className="route-content">
            <Routes>
              <Route path="/" element={<CatalogPage />} />
              <Route path="/products/:id" element={<ProductPage />} />
              <Route path="/cart" element={<CartPage />} />
              <Route path="/login" element={<AuthPage mode="login" />} />
              <Route path="/register" element={<AuthPage mode="register" />} />
              <Route path="/checkout" element={<CheckoutPage />} />
              <Route path="/account/orders" element={<OrdersPage />} />
              <Route path="/orders/:id" element={<OrderDetailPage />} />
              <Route path="*" element={<AccountPagesPlaceholder />} />
            </Routes>
          </div>
          <Footer />
        </div>
      </BrowserRouter>
    </CartProvider>
  )
}

function RouteFocus() {
  const { pathname } = useLocation()
  useEffect(() => {
    const heading = document.querySelector<HTMLElement>(
      '.route-content main h1',
    )
    if (!heading) return
    heading.tabIndex = -1
    heading.focus({ preventScroll: true })
  }, [pathname])
  return null
}

export default function App() {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { retry: false, refetchOnWindowFocus: false },
          mutations: { retry: false },
        },
      }),
  )
  return (
    <QueryClientProvider client={queryClient}>
      <StoreRoutes />
    </QueryClientProvider>
  )
}
