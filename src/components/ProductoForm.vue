<template>
  <div class="form-container">
    <h2>{{ esEdicion ? '✏️ Editar Producto' : '➕ Nuevo Producto' }}</h2>

    <form @submit.prevent="guardar" class="formulario">
      <div class="campo">
        <label for="nombre">Nombre del producto</label>
        <input
          id="nombre"
          v-model="nombre"
          type="text"
          placeholder="Ej: Coca-Cola 500ml"
          required
        />
      </div>

      <div class="campo">
        <label for="categoria">Categoría</label>
        <select id="categoria" v-model="categoria" required>
          <option value="" disabled>Seleccionar categoría</option>
          <option v-for="cat in categorias" :key="cat" :value="cat">
            {{ cat }}
          </option>
        </select>
      </div>

      <div class="campo-fila">
        <div class="campo">
          <label for="precio">Precio ($)</label>
          <input
            id="precio"
            v-model.number="precio"
            type="number"
            min="0"
            step="1"
            placeholder="Ej: 1500"
            required
          />
        </div>

        <div class="campo">
          <label for="stock">Stock (unidades)</label>
          <input
            id="stock"
            v-model.number="stock"
            type="number"
            min="0"
            step="1"
            placeholder="Ej: 24"
            required
          />
        </div>
      </div>

      <div class="form-acciones">
        <button type="submit" class="btn btn-guardar">
          💾 {{ esEdicion ? 'Actualizar' : 'Guardar' }}
        </button>
        <button type="button" class="btn btn-cancelar" @click="cancelar">
          ↩️ Cancelar
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  producto: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['guardar', 'cancelar'])

const nombre = ref('')
const categoria = ref('')
const precio = ref(null)
const stock = ref(null)

const categorias = ['Bebidas', 'Golosinas', 'Snacks', 'Galletitas', 'Helados', 'Varios']

const esEdicion = computed(() => props.producto !== null)

watch(
  () => props.producto,
  (nuevoProducto) => {
    if (nuevoProducto) {
      nombre.value = nuevoProducto.nombre
      categoria.value = nuevoProducto.categoria
      precio.value = nuevoProducto.precio
      stock.value = nuevoProducto.stock
    } else {
      limpiarFormulario()
    }
  },
  { immediate: true }
)

function guardar() {
  emit('guardar', {
    nombre: nombre.value,
    categoria: categoria.value,
    precio: precio.value,
    stock: stock.value
  })
  limpiarFormulario()
}

function cancelar() {
  limpiarFormulario()
  emit('cancelar')
}

function limpiarFormulario() {
  nombre.value = ''
  categoria.value = ''
  precio.value = null
  stock.value = null
}
</script>
