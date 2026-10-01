import { execFileSync } from 'node:child_process'
import { resolve } from 'node:path'

import { expect, test, type Page } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

const password = `Blast-${crypto.randomUUID()}-Demo!`
const email = `customer-${crypto.randomUUID()}@example.test`
let productTitle = ''

async function checkout(page: Page) {
  await page.getByRole('link', { name: 'Tienda', exact: true }).click()
  await page
    .getByRole('button', { name: `Añadir ${productTitle} a la bolsa` })
    .click()
  await page.getByRole('link', { name: /Carrito,/ }).click()
  await page.getByRole('button', { name: /Continuar/ }).click()
  await page.getByLabel('Nombre de prueba').fill('Cliente de prueba')
  await page.getByLabel('Dirección ficticia').fill('Calle Inventada 123')
  await page.getByLabel('Ciudad').fill('Madrid')
  await page.getByLabel('Código postal de prueba').fill('28000')
  await page
    .getByRole('button', { name: /Crear pedido de demostración/ })
    .click()
  await expect(
    page.getByRole('heading', { name: 'Gracias por tu pedido.' }),
  ).toBeVisible()
}

test.describe('local customer purchase journey', () => {
  test.beforeAll(() => {
    if (process.env.BLAST_ECOM_E2E_ALLOW_DATA_WRITES !== 'true') {
      throw new Error(
        'E2E creates fictional local products, customer accounts and orders. Set BLAST_ECOM_E2E_ALLOW_DATA_WRITES=true only for a disposable local database.',
      )
    }
    const fixtureTag = `e2e-${crypto.randomUUID()}`
    productTitle = `Taza Aurora ${crypto.randomUUID().slice(0, 8)}`
    const setupScript = [
      'from decimal import Decimal',
      'from modules.inventory.models import StockItem',
      'from modules.products.models import Category, Product',
      `tag = ${JSON.stringify(fixtureTag)}`,
      `title = ${JSON.stringify(productTitle)}`,
      'category = Category.objects.create(slug=tag, name="E2E demo")',
      'product = Product.objects.create(sku=tag.upper(), category=category, title=title, description="Fictional browser test product.", unit_price=Decimal("18.50"), active=True)',
      'StockItem.objects.create(product=product, on_hand=5, reserved=0)',
    ].join('\n')
    execFileSync(
      'uv',
      ['run', '--locked', 'python', 'manage.py', 'shell', '-c', setupScript],
      {
        cwd: resolve(process.cwd(), '../backend'),
        env: { ...process.env, DJANGO_DEBUG: 'true' },
        stdio: 'pipe',
      },
    )
  })

  test('registers, purchases through simulated payment and cancels an awaiting order', async ({
    page,
  }) => {
    await page.goto('/register')
    await page.getByLabel('Correo electrónico').fill(email)
    await page.getByLabel('Contraseña').fill(password)
    await page.getByRole('button', { name: 'Crear cuenta' }).click()
    await expect(page.getByRole('status')).toContainText('Cuenta de demo creada')
    await page.getByRole('link', { name: 'Entra aquí' }).click()

    await page.getByLabel('Correo electrónico').fill(email)
    await page.getByLabel('Contraseña').fill(password)
    await page.getByRole('button', { name: 'Entrar' }).click()
    await expect(
      page.getByRole('heading', { name: 'Tus pedidos.' }),
    ).toBeVisible()

    await checkout(page)
    await page.getByRole('button', { name: 'Simular pago' }).click()
    await expect(page.getByRole('status')).toContainText('Confirmado')
    await expect(page.getByText(/Pago de demostración aceptado/)).toBeVisible()

    await checkout(page)
    await page.getByRole('button', { name: 'Cancelar pedido' }).click()
    await expect(page.getByRole('status')).toContainText('Cancelado')
    await page.getByRole('link', { name: 'Mis pedidos', exact: true }).click()
    await expect(
      page.getByRole('heading', { name: 'Tus pedidos.' }),
    ).toBeVisible()
    await expect(page.getByText('Confirmado')).toBeVisible()
    await expect(page.getByText('Cancelado')).toBeVisible()
  })
})

test('storefront and account entry pages have no critical or serious accessibility violations', async ({
  page,
}) => {
  for (const route of [
    '/',
    '/login',
    '/register',
    '/password-reset',
    '/reset-password',
    '/verify-email',
  ]) {
    await page.goto(route)
    await expect(page.locator('.route-content h1').first()).toBeVisible()
    const results = await new AxeBuilder({ page }).analyze()
    const significantViolations = results.violations.filter((violation) =>
      ['critical', 'serious'].includes(violation.impact ?? ''),
    )
    expect(
      significantViolations.map(
        (violation) =>
          `${violation.impact} ${violation.id}: ${violation.nodes.map((node) => `${node.target.join(' ')} ${node.failureSummary ?? ''}`).join('; ')}`,
      ),
      `Accessibility violations on ${route}`,
    ).toEqual([])
  }
})

test('password recovery presents the same local-only response without revealing an account', async ({
  page,
}) => {
  await page.goto('/password-reset')
  await page.getByLabel('Correo electrónico').fill('unknown@example.test')
  await page.getByRole('button', { name: /Enviar instrucciones/ }).click()

  await expect(page.getByRole('status')).toContainText(
    'Si la cuenta puede recuperarse',
  )
  await expect(page.getByText(/no envía correo real/)).toBeVisible()
})
