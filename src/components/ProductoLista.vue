<template>
  <div class="tabla-container">
    <table class="tabla-productos">
      <thead>
        <tr>
          <th>Nombre</th>
          <th>Categoría</th>
          <th>Precio</th>
          <th>Stock</th>
          <th>Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="producto in productos"
          :key="producto.id"
          :class="{ 'stock-bajo': producto.stock < 5 }"
        >
          <td class="td-nombre">{{ producto.nombre }}</td>
          <td>
            <span class="badge" :class="'badge-' + producto.categoria.toLowerCase()">
              {{ producto.categoria }}
            </span>
          </td>
          <td class="td-precio">${{ producto.precio.toLocaleString('es-AR') }}</td>
          <td class="td-stock">
            <span v-if="producto.stock < 5" class="stock-alerta">⚠️</span>
            {{ producto.stock }} uds.
          </td>
          <td class="td-acciones">
            <button class="btn btn-editar" @click="emit('editar', producto.id)">
              ✏️ Editar
            </button>
            <button class="btn btn-eliminar" @click="emit('eliminar', producto.id)">
              🗑️ Eliminar
            </button>
          </td>
        </tr>

        <tr v-if="productos.length === 0">
          <td colspan="5" class="td-vacio">
            No se encontraron productos
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

const emit = defineEmits(['editar', 'eliminar'])
</script>
