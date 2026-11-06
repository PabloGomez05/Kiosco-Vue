<template>
  <div class="form-container">
    <h2>🛒 Punto de Venta (Carrito POS)</h2>

    <div class="formulario carrito-card">
      <div class="idempotency-box">
        <span class="idemp-label">🔑 Idempotency-Key (UUID v4):</span>
        <code class="idemp-code">{{ idempotencyKey }}</code>
      </div>

      <div v-if="items.length === 0" class="carrito-vacio">
        Seleccioná productos de la tabla con el botón <strong>"🛒 + Carrito"</strong> para armar la venta.
      </div>

      <div v-else class="carrito-items">
        <div
          v-for="item in items"
          :key="item.id_producto"
          class="carrito-item"
          :class="{ 'item-excede-stock': item.cantidad > item.stock_disponible }"
        >
          <div class="item-info">
            <div class="item-nombre">{{ item.nombre }}</div>
            <div class="item-meta">
              ${{ item.precio_unitario.toLocaleString('es-AR') }} c/u ·
              <span>Stock disp.: {{ item.stock_disponible }}</span>
            </div>
            <div v-if="item.cantidad > item.stock_disponible" class="item-alerta-stock">
              ⚠️ Supera el stock disponible ({{ item.stock_disponible }} uds.)
            </div>
          </div>

          <div class="item-controles">
            <button type="button" class="btn-qty" @click="emit('cambiar-cantidad', item.id_producto, item.cantidad - 1)">−</button>
            <input
              type="number"
              class="input-qty"
              min="1"
              :value="item.cantidad"
              @input="e => emit('cambiar-cantidad', item.id_producto, Number(e.target.value))"
            />
            <button type="button" class="btn-qty" @click="emit('cambiar-cantidad', item.id_producto, item.cantidad + 1)">+</button>
            <div class="item-subtotal">
              ${{ (item.cantidad * item.precio_unitario).toLocaleString('es-AR') }}
            </div>
            <button type="button" class="btn-quitar" title="Quitar ítem" @click="emit('quitar-item', item.id_producto)">✕</button>
          </div>
        </div>
      </div>

      <div v-if="items.length > 0" class="pagos-section">
        <div class="pagos-header">
          <label>💳 Medios de Pago (entidad <code>pagos_venta</code>)</label>
          <label class="toggle-mixto">
            <input v-model="pagoMixto" type="checkbox" @change="ajustarModoPago" />
            Pago mixto (2 medios)
          </label>
        </div>

        <div v-if="!pagoMixto" class="campo">
          <select v-model="medioUnico" class="select-pago">
            <option value="efectivo">💵 Efectivo ($ {{ totalCarrito.toLocaleString('es-AR') }})</option>
            <option value="transferencia">📲 Transferencia / QR ($ {{ totalCarrito.toLocaleString('es-AR') }})</option>
            <option value="debito">💳 Tarjeta de Débito ($ {{ totalCarrito.toLocaleString('es-AR') }})</option>
            <option value="credito">💳 Tarjeta de Crédito ($ {{ totalCarrito.toLocaleString('es-AR') }})</option>
          </select>
        </div>

        <div v-else class="pago-mixto-grid">
          <div class="campo">
            <label>Efectivo ($)</label>
            <input
              v-model.number="montoEfectivoMixto"
              type="number"
              min="0"
              step="50"
              @input="recalcularTransferenciaMixta"
            />
          </div>
          <div class="campo">
            <label>Transferencia / QR ($)</label>
            <input
              v-model.number="montoTransferenciaMixto"
              type="number"
              min="0"
              step="50"
            />
          </div>
        </div>
      </div>

      <div class="carrito-total-box">
        <span>TOTAL A COBRAR:</span>
        <strong class="total-monto">${{ totalCarrito.toLocaleString('es-AR') }}</strong>
      </div>

      <div class="form-acciones carrito-acciones">
        <button
          type="button"
          class="btn btn-confirmar-venta"
          :disabled="items.length === 0 || procesando"
          @click="confirmar"
        >
          {{ procesando ? '⏳ Procesando transacción...' : '✅ Confirmar Venta Transaccional (ACID)' }}
        </button>
        <button
          type="button"
          class="btn btn-cancelar"
          :disabled="items.length === 0"
          @click="emit('vaciar')"
        >
          🗑️ Vaciar
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    required: true
  },
  idempotencyKey: {
    type: String,
    required: true
  },
  procesando: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['cambiar-cantidad', 'quitar-item', 'vaciar', 'confirmar-venta'])

const medioUnico = ref('efectivo')
const pagoMixto = ref(false)
const montoEfectivoMixto = ref(0)
const montoTransferenciaMixto = ref(0)

const totalCarrito = computed(() =>
  props.items.reduce((acc, item) => acc + item.cantidad * item.precio_unitario, 0)
)

watch(totalCarrito, (nuevoTotal) => {
  if (pagoMixto.value) {
    const mitad = Math.round(nuevoTotal / 2)
    montoEfectivoMixto.value = mitad
    montoTransferenciaMixto.value = nuevoTotal - mitad
  }
})

function ajustarModoPago() {
  if (pagoMixto.value) {
    const mitad = Math.round(totalCarrito.value / 2)
    montoEfectivoMixto.value = mitad
    montoTransferenciaMixto.value = totalCarrito.value - mitad
  }
}

function recalcularTransferenciaMixta() {
  const efec = Number(montoEfectivoMixto.value || 0)
  montoTransferenciaMixto.value = Math.max(0, totalCarrito.value - efec)
}

function confirmar() {
  let pagos = []
  if (!pagoMixto.value) {
    pagos = [{ medio_pago: medioUnico.value, monto: totalCarrito.value }]
  } else {
    if (montoEfectivoMixto.value > 0) {
      pagos.push({ medio_pago: 'efectivo', monto: Number(montoEfectivoMixto.value) })
    }
    if (montoTransferenciaMixto.value > 0) {
      pagos.push({
        medio_pago: 'transferencia',
        monto: Number(montoTransferenciaMixto.value),
        referencia: 'QR-DEMO-2026'
      })
    }
  }
  emit('confirmar-venta', { pagos })
}
</script>

