import type { JSX } from 'react'

import './App.css'

function App(): JSX.Element {
  return (
    <main className="landing-page">
      <p className="eyebrow">Blast Ecom</p>
      <h1>La tienda está en preparación</h1>
      <p>
        Esta aplicación de demostración todavía no permite realizar compras. El
        catálogo y el proceso de pedido se incorporarán en los siguientes
        incrementos.
      </p>
    </main>
  )
}

export default App
