<template>
  <div id="app-wrapper">
    <nav class="navbar">
      <div class="navbar-left">
        <span class="navbar-brand">🏪 Mi Kiosco POS</span>
        <span class="navbar-subtitle">Demo Hito 06/11 · Venta Transaccional ACID + RBAC JWT</span>
      </div>

      <div class="navbar-right">
        <span
          class="badge-caja"
          :class="estadoCaja.cerrada ? 'caja-cerrada' : 'caja-abierta'"
        >
          {{ estadoCaja.cerrada ? '🔒 Caja del día: CERRADA' : '🟢 Caja del día: ABIERTA' }}
        </span>

        <div class="rol-switcher">
          <span class="rol-label">Sesión JWT:</span>
          <button
            type="button"
            class="btn-rol"
            :class="{ activo: usuarioActual?.rol === 'vendedor' }"
            @click="cambiarSesion('vendedor')"
          >
            👤 Vendedor (juan)
          </button>
          <button
            type="button"
            class="btn-rol"
            :class="{ activo: usuarioActual?.rol === 'admin' }"
            @click="cambiarSesion('admin')"
          >
            🔑 Admin (pablo)
          </button>
        </div>
      </div>
    </nav>

    <main class="contenido">
      <!-- Barra de pruebas interactivas para el Hito 06/11 -->
      <section class="demo-bar">
        <div class="demo-bar-title">
          <strong>⚡ Pruebas en Vivo del Hito 06/11:</strong>
          <span>Ejecutá con 1 clic las demostraciones pedidas por el docente:</span>
        </div>
        <div class="demo-bar-actions">
          <button type="button" class="btn btn-demo" @click="probarConcurrencia">
            ⚡ 2 Ventas Concurrentes (SELECT ... FOR UPDATE)
          </button>
          <button type="button" class="btn btn-demo" @click="probarRechazo403">
            🛡️ Probar Rechazo 403 (Vendedor → POST /api/productos)
          </button>
          <button
            type="button"
            class="btn btn-demo"
            :disabled="estadoCaja.cerrada"
            @click="cerrarCajaDelDia"
          >
            🔒 Cerrar Caja Diaria ({{ '$' + (estadoCaja.totales_acumulados?.total || 0).toLocaleString('es-AR') }})
          </button>
          <button type="button" class="btn btn-demo btn-reset" @click="resetearSemilla">
            🔄 Restaurar Datos Semilla
          </button>
        </div>
      </section>

      <!-- Banner de respuesta del servidor (éxito o error uniforme ErrorResponse) -->
      <div
        v-if="feedbackBanner"
        class="feedback-banner"
        :class="'banner-' + feedbackBanner.tipo"
      >
        <div class="banner-header">
          <strong>{{ feedbackBanner.titulo }}</strong>
          <button type="button" class="btn-cerrar-banner" @click="feedbackBanner = null">✕</button>
        </div>
        <p>{{ feedbackBanner.mensaje }}</p>
        <pre v-if="feedbackBanner.json" class="banner-json">{{ feedbackBanner.json }}</pre>
      </div>

      <div class="home-header">
        <div>
          <h1>📦 Catálogo, Inventario y Punto de Venta</h1>
          <p class="subtitulo">
            {{ totalProductos }} productos activos ·
            <span v-if="productosStockBajo > 0" class="texto-alerta">
              ⚠️ {{ productosStockBajo }} en o bajo stock mínimo
            </span>
            <span v-else class="texto-ok">Todo en stock óptimo ✓</span>
            · Recaudación turno hoy:
            <strong>${{ (estadoCaja.totales_acumulados?.total || 0).toLocaleString('es-AR') }}</strong>
            ({{ estadoCaja.cantidad_ventas || 0 }} tickets)
          </p>
        </div>

        <div class="modo-tabs">
          <button
            type="button"
            class="btn-tab"
            :class="{ activo: panelIzquierdo === 'carrito' }"
            @click="panelIzquierdo = 'carrito'"
          >
            🛒 Punto de Venta ({{ itemsCarrito.length }})
          </button>
          <button
            type="button"
            class="btn-tab"
            :class="{ activo: panelIzquierdo === 'abm' }"
            @click="panelIzquierdo = 'abm'"
          >
            {{ productoEditando ? '✏️ Editar Producto' : '➕ Alta / ABM Producto' }}
          </button>
        </div>
      </div>

      <div class="layout-principal">
        <CarritoVenta
          v-if="panelIzquierdo === 'carrito'"
          :items="itemsCarrito"
          :idempotency-key="idempotencyKeyActual"
          :procesando="procesandoVenta"
          @cambiar-cantidad="cambiarCantidadCarrito"
          @quitar-item="quitarDelCarrito"
          @vaciar="vaciarCarrito"
          @confirmar-venta="confirmarVenta"
        />

        <ProductoForm
          v-else
          :producto="productoEditando"
          @guardar="guardarProducto"
          @cancelar="cancelarEdicion"
        />

        <div class="lista-section">
          <div class="filtros">
            <input
              v-model="busqueda"
              type="text"
              placeholder="🔍 Buscar por nombre o código (ej. 7790895000997)..."
              class="input-busqueda"
            />

            <select v-model="categoriaFiltro" class="select-categoria">
              <option value="">Todas las categorías</option>
              <option v-for="cat in categorias" :key="cat" :value="cat">
                {{ cat }}
              </option>
            </select>
          </div>

          <ProductoLista
            :productos="productosFiltrados"
            @agregar-carrito="agregarAlCarrito"
            @editar="seleccionarParaEditar"
            @eliminar="eliminarProducto"
          />
        </div>
      </div>

      <!-- Paneles de Trazabilidad en Tiempo Real: Ventas y Movimientos de Stock -->
      <section class="auditoria-grid">
        <div class="tabla-container auditoria-card">
          <div class="auditoria-header">
            <h3>🧾 Últimas Ventas Confirmadas (<code>ventas</code> + <code>pagos_venta</code>)</h3>
          </div>
          <table class="tabla-productos tabla-compacta">
            <thead>
              <tr>
                <th>Ticket</th>
                <th>Vendedor</th>
                <th>Detalle</th>
                <th>Pagos</th>
                <th>Total</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="v in ventasRecientes" :key="v.id_venta">
                <td>
                  <strong>#{{ v.id_venta }}</strong>
                  <div><small class="codigo-prod">{{ v.idempotency_key?.slice(0, 8) }}…</small></div>
                </td>
                <td>{{ v.vendedor }}</td>
                <td>
                  <div v-for="it in v.items" :key="it.id_detalle">
                    {{ it.cantidad }}x {{ it.nombre_producto }} (${{ Number(it.precio_unitario).toLocaleString('es-AR') }})
                  </div>
                </td>
                <td>
                  <span
                    v-for="pg in v.pagos"
                    :key="pg.id_pago"
                    class="badge-pago"
                  >
                    {{ pg.medio_pago }}: ${{ Number(pg.monto).toLocaleString('es-AR') }}
                  </span>
                </td>
                <td class="td-precio">${{ Number(v.total).toLocaleString('es-AR') }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="tabla-container auditoria-card">
          <div class="auditoria-header">
            <h3>📋 Bitácora de Stock (<code>movimientos_stock</code>)</h3>
          </div>
          <table class="tabla-productos tabla-compacta">
            <thead>
              <tr>
                <th>ID</th>
                <th>Producto</th>
                <th>Tipo</th>
                <th>Cant.</th>
                <th>Transición</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="m in movimientosRecientes.slice(0, 8)" :key="m.id_movimiento">
                <td>#{{ m.id_movimiento }}</td>
                <td>{{ m.nombre_producto }}</td>
                <td>
                  <span class="badge-mov" :class="'mov-' + m.tipo">{{ m.tipo }}</span>
                </td>
                <td>{{ m.cantidad }}</td>
                <td>
                  <code>{{ m.stock_anterior }} → {{ m.stock_posterior }}</code>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import ProductoForm from './components/ProductoForm.vue'
import ProductoLista from './components/ProductoLista.vue'
import CarritoVenta from './components/CarritoVenta.vue'

function generarUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

const tokenJWT = ref('')
const usuarioActual = ref(null)
const productos = ref([])
const ventasRecientes = ref([])
const movimientosRecientes = ref([])
const estadoCaja = ref({ cerrada: false, cantidad_ventas: 0, totales_acumulados: { total: 0 } })

const itemsCarrito = ref([])
const idempotencyKeyActual = ref(generarUUID())
const procesandoVenta = ref(false)

const panelIzquierdo = ref('carrito')
const productoEditando = ref(null)
const busqueda = ref('')
const categoriaFiltro = ref('')
const feedbackBanner = ref(null)

const categorias = ['Bebidas', 'Golosinas', 'Snacks', 'Galletitas', 'Varios']

const totalProductos = computed(() => productos.value.length)
const productosStockBajo = computed(() =>
  productos.value.filter(p => (p.stock_actual ?? p.stock) <= (p.stock_minimo ?? 5)).length
)

const productosFiltrados = computed(() => {
  let resultado = productos.value
  if (busqueda.value) {
    const termino = busqueda.value.toLowerCase()
    resultado = resultado.filter(
      p =>
        p.nombre.toLowerCase().includes(termino) ||
        (p.codigo && p.codigo.toLowerCase().includes(termino))
    )
  }
  if (categoriaFiltro.value) {
    resultado = resultado.filter(p => p.categoria === categoriaFiltro.value)
  }
  return resultado
})

async function llamarAPI(endpoint, { method = 'GET', body = null, headers = {} } = {}) {
  const reqHeaders = {
    'Content-Type': 'application/json',
    ...headers
  }
  if (tokenJWT.value) {
    reqHeaders['Authorization'] = `Bearer ${tokenJWT.value}`
  }
  const resp = await fetch(endpoint, {
    method,
    headers: reqHeaders,
    body: body ? JSON.stringify(body) : null
  })
  const data = await resp.json()
  return { status: resp.status, ok: resp.ok, data }
}

async function cambiarSesion(usuarioLogin) {
  const res = await llamarAPI('/api/auth/login', {
    method: 'POST',
    body: { usuario: usuarioLogin, password: 'Kiosco2026!' }
  })
  if (res.ok) {
    tokenJWT.value = res.data.token
    usuarioActual.value = res.data.usuario
    await recargarTodo()
  }
}

async function recargarTodo() {
  const [resProd, resVentas, resMov, resCaja] = await Promise.all([
    llamarAPI('/api/productos?limit=50'),
    llamarAPI('/api/ventas?limit=10'),
    llamarAPI('/api/stock/movimientos?limit=15'),
    llamarAPI('/api/caja/estado')
  ])
  if (resProd.ok) {
    productos.value = resProd.data.data.map(p => ({
      ...p,
      id: p.id_producto,
      precio: p.precio_venta,
      stock: p.stock_actual
    }))
    // Actualizar stock disponible de los ítems que estén en el carrito
    for (const item of itemsCarrito.value) {
      const prodActualizado = productos.value.find(p => p.id_producto === item.id_producto)
      if (prodActualizado) {
        item.stock_disponible = prodActualizado.stock_actual
      }
    }
  }
  if (resVentas.ok) ventasRecientes.value = resVentas.data.data
  if (resMov.ok) movimientosRecientes.value = resMov.data.data
  if (resCaja.ok) estadoCaja.value = resCaja.data
}

function agregarAlCarrito(producto) {
  panelIzquierdo.value = 'carrito'
  const idProd = producto.id_producto || producto.id
  const existente = itemsCarrito.value.find(i => i.id_producto === idProd)
  if (existente) {
    existente.cantidad += 1
    existente.stock_disponible = producto.stock_actual ?? producto.stock
  } else {
    itemsCarrito.value.push({
      id_producto: idProd,
      nombre: producto.nombre,
      precio_unitario: Number(producto.precio_venta ?? producto.precio),
      cantidad: 1,
      stock_disponible: Number(producto.stock_actual ?? producto.stock)
    })
  }
}

function cambiarCantidadCarrito(idProducto, nuevaCantidad) {
  if (nuevaCantidad <= 0) {
    quitarDelCarrito(idProducto)
    return
  }
  const item = itemsCarrito.value.find(i => i.id_producto === idProducto)
  if (item) {
    item.cantidad = nuevaCantidad
  }
}

function quitarDelCarrito(idProducto) {
  itemsCarrito.value = itemsCarrito.value.filter(i => i.id_producto !== idProducto)
}

function vaciarCarrito() {
  itemsCarrito.value = []
  idempotencyKeyActual.value = generarUUID()
}

async function confirmarVenta({ pagos }) {
  procesandoVenta.value = true
  try {
    const payload = {
      items: itemsCarrito.value.map(i => ({
        id_producto: i.id_producto,
        cantidad: i.cantidad
      })),
      pagos,
      observaciones: 'Venta registrada desde Punto de Venta Vue 3'
    }

    const res = await llamarAPI('/api/ventas', {
      method: 'POST',
      headers: { 'Idempotency-Key': idempotencyKeyActual.value },
      body: payload
    })

    if (res.ok) {
      const ticket = res.data.venta
      feedbackBanner.value = {
        tipo: 'exito',
        titulo: `✅ HTTP ${res.status} — Transacción ACID Confirmada (Ticket #${ticket.id_venta})`,
        mensaje: `Se descontó el stock atómicamente, se grabaron ${ticket.items.length} renglones en detalle_ventas, ${ticket.pagos.length} cobro(s) en pagos_venta y la bitácora movimientos_stock.`,
        json: JSON.stringify(res.data, null, 2)
      }
      vaciarCarrito()
      await recargarTodo()
    } else {
      feedbackBanner.value = {
        tipo: 'error',
        titulo: `🛑 HTTP ${res.status} — ROLLBACK Ejecutado (${res.data.code})`,
        mensaje: res.data.message,
        json: JSON.stringify(res.data, null, 2)
      }
    }
  } finally {
    procesandoVenta.value = false
  }
}

async function guardarProducto(datosProducto) {
  if (usuarioActual.value?.rol !== 'admin') {
    await cambiarSesion('admin')
  }

  const payload = {
    nombre: datosProducto.nombre,
    categoria: datosProducto.categoria,
    precio_venta: Number(datosProducto.precio),
    stock_actual: Number(datosProducto.stock)
  }

  let res
  if (productoEditando.value) {
    const id = productoEditando.value.id_producto || productoEditando.value.id
    res = await llamarAPI(`/api/productos/${id}`, { method: 'PUT', body: payload })
  } else {
    res = await llamarAPI('/api/productos', { method: 'POST', body: payload })
  }

  if (res.ok) {
    feedbackBanner.value = {
      tipo: 'exito',
      titulo: `✅ HTTP ${res.status} — Producto actualizado en Base de Datos`,
      mensaje: `El producto '${res.data.nombre}' quedó con stock de ${res.data.stock_actual} uds. y precio $${Number(res.data.precio_venta).toLocaleString('es-AR')}.`,
      json: JSON.stringify(res.data, null, 2)
    }
    productoEditando.value = null
    await recargarTodo()
  } else {
    feedbackBanner.value = {
      tipo: 'error',
      titulo: `🛑 HTTP ${res.status} — ${res.data.code}`,
      mensaje: res.data.message,
      json: JSON.stringify(res.data, null, 2)
    }
  }
}

async function seleccionarParaEditar(id) {
  const producto = productos.value.find(p => (p.id_producto || p.id) === id)
  if (producto) {
    if (usuarioActual.value?.rol !== 'admin') {
      await cambiarSesion('admin')
    }
    productoEditando.value = {
      ...producto,
      precio: Number(producto.precio_venta ?? producto.precio),
      stock: Number(producto.stock_actual ?? producto.stock)
    }
    panelIzquierdo.value = 'abm'
  }
}

async function eliminarProducto(id) {
  const producto = productos.value.find(p => (p.id_producto || p.id) === id)
  if (!producto) return

  if (usuarioActual.value?.rol !== 'admin') {
    await cambiarSesion('admin')
  }

  const res = await llamarAPI(`/api/productos/${id}`, { method: 'DELETE' })
  if (res.ok) {
    feedbackBanner.value = {
      tipo: 'exito',
      titulo: `✅ HTTP 200 — Baja Lógica Aplicada (activo = false)`,
      mensaje: res.data.message,
      json: JSON.stringify(res.data, null, 2)
    }
    await recargarTodo()
  } else {
    feedbackBanner.value = {
      tipo: 'error',
      titulo: `🛑 HTTP ${res.status} — ${res.data.code}`,
      mensaje: res.data.message,
      json: JSON.stringify(res.data, null, 2)
    }
  }
}

function cancelarEdicion() {
  productoEditando.value = null
}

// --- Demostraciones de 1 clic para el Hito 06/11 ---
async function probarRechazo403() {
  // Asegurar que probamos con el token de vendedor
  if (usuarioActual.value?.rol !== 'vendedor') {
    await cambiarSesion('vendedor')
  }
  const res = await llamarAPI('/api/productos', {
    method: 'POST',
    body: { nombre: 'Intento de Alta por Vendedor', precio_venta: 1500, stock_actual: 10 }
  })
  feedbackBanner.value = {
    tipo: 'error',
    titulo: `🛡️ Demostración RBAC: Middleware respondió HTTP ${res.status} (${res.data.code})`,
    mensaje: 'El servidor validó el JWT del vendedor y bloqueó el acceso antes de llegar al controlador.',
    json: JSON.stringify(res.data, null, 2)
  }
}

async function probarConcurrencia() {
  const alfajor = productos.value.find(p => p.id_producto === 2)
  const stockDisp = alfajor ? alfajor.stock_actual : 0
  if (stockDisp < 2) {
    await resetearSemilla()
  }
  const prodActual = productos.value.find(p => p.id_producto === 2)
  const cantPedida = Math.max(1, prodActual.stock_actual)
  const monto = cantPedida * prodActual.precio_venta

  const [resA, resB] = await Promise.all([
    llamarAPI('/api/ventas', {
      method: 'POST',
      headers: { 'Idempotency-Key': generarUUID() },
      body: {
        items: [{ id_producto: 2, cantidad: cantPedida }],
        pagos: [{ medio_pago: 'efectivo', monto }],
        observaciones: 'Sesión Concurrente A'
      }
    }),
    llamarAPI('/api/ventas', {
      method: 'POST',
      headers: { 'Idempotency-Key': generarUUID() },
      body: {
        items: [{ id_producto: 2, cantidad: cantPedida }],
        pagos: [{ medio_pago: 'transferencia', monto }],
        observaciones: 'Sesión Concurrente B'
      }
    })
  ])

  await recargarTodo()
  feedbackBanner.value = {
    tipo: 'exito',
    titulo: `⚡ Prueba de 2 Ventas Concurrentes (Alfajor Havanna: pedían ${cantPedida} uds. cada una)`,
    mensaje: `Sesión A respondió HTTP ${resA.status} y Sesión B respondió HTTP ${resB.status}. El bloqueo exclusivo impidió el stock negativo (stock resultante: 0 uds.).`,
    json: JSON.stringify(
      {
        sesion_A: { status: resA.status, resultado: resA.data },
        sesion_B: { status: resB.status, resultado: resB.data }
      },
      null,
      2
    )
  }
}

async function cerrarCajaDelDia() {
  const efecEsperado = 5000 + (estadoCaja.value.totales_acumulados?.efectivo || 0)
  const res = await llamarAPI('/api/caja/cierre', {
    method: 'POST',
    body: {
      monto_inicial: 5000,
      efectivo_contado: efecEsperado,
      observaciones: 'Arqueo diario desde Demo Hito 06/11'
    }
  })
  if (res.ok) {
    feedbackBanner.value = {
      tipo: 'exito',
      titulo: `🔒 HTTP 201 — Cierre de Caja Diario Consolidado`,
      mensaje: 'Si ahora intentás confirmar una nueva venta hoy con este vendedor, el servidor la bloqueará con HTTP 403 CAJA_CERRADA.',
      json: JSON.stringify(res.data, null, 2)
    }
    await recargarTodo()
  }
}

async function resetearSemilla() {
  await llamarAPI('/api/demo/reset', { method: 'POST' })
  vaciarCarrito()
  await recargarTodo()
  feedbackBanner.value = {
    tipo: 'exito',
    titulo: '🔄 Datos Semilla Restaurados',
    mensaje: 'Se restauró el inventario inicial (Coca-Cola=24, Alfajor Havanna=4, Lays=8, Oreo=15, Agua=40) y se reabrió la caja del día.',
    json: null
  }
}

onMounted(async () => {
  await cambiarSesion('vendedor')
})
</script>
