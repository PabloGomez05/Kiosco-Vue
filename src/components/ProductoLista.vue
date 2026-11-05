<template>
  <div class="tabla-container">
    <table class="tabla-productos">
      <thead>
        <tr>
          <th>Producto</th>
          <th>Categoría</th>
          <th>Precio Venta</th>
          <th>Stock Actual</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="producto in productos"
          :key="producto.id_producto || producto.id"
          :class="{ 'stock-bajo': esStockBajo(producto) }"
        >
          <td class="td-nombre">
            <div>{{ producto.nombre }}</div>
            <small v-if="producto.codigo" class="codigo-prod">Cód: {{ producto.codigo }}</small>
          </td>
          <td>
            <span class="badge" :class="'badge-' + (producto.categoria || 'varios').toLowerCase()">
              {{ producto.categoria }}
            </span>
          </td>
          <td class="td-precio">
            ${{ Number(producto.precio_venta ?? producto.precio).toLocaleString('es-AR') }}
          </td>
          <td class="td-stock">
            <span v-if="esStockBajo(producto)" class="stock-alerta" title="Stock en o por debajo del mínimo">⚠️</span>
            <strong>{{ producto.stock_actual ?? producto.stock }}</strong> uds.
            <small class="stock-min-label">(mín: {{ producto.stock_minimo ?? 5 }})</small>
          </td>
          <td class="td-acciones">
            <button
              class="btn btn-carrito"
              :disabled="(producto.stock_actual ?? producto.stock) <= 0"
              @click="emit('agregar-carrito', producto)"
            >
              🛒 + Carrito
            </button>
            <button
              class="btn btn-editar"
              @click="emit('editar', producto.id_producto || producto.id)"
            >
              ✏️
            </button>
            <button
              class="btn btn-eliminar"
              title="Baja lógica (activo = false)"
              @click="emit('eliminar', producto.id_producto || producto.id)"
            >
              🗑️
            </button>
          </td>
        </tr>

        <tr v-if="productos.length === 0">
          <td colspan="5" class="td-vacio">
            No se encontraron productos activos para el filtro seleccionado
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  productos: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['agregar-carrito', 'editar', 'eliminar'])

function esStockBajo(p) {
  const actual = p.stock_actual ?? p.stock ?? 0
  const minimo = p.stock_minimo ?? 5
  return actual <= minimo
}
</script>
