<template>
  <div id="app-wrapper">
    <nav class="navbar">
      <span class="navbar-brand">🏪 Mi Kiosco</span>
      <span class="navbar-subtitle">Administrador de Inventario</span>
    </nav>

    <main class="contenido">
      <div class="home-header">
        <div>
          <h1>📦 Inventario</h1>
          <p class="subtitulo">
            {{ totalProductos }} productos ·
            <span v-if="productosStockBajo > 0" class="texto-alerta">
              {{ productosStockBajo }} con stock bajo
            </span>
            <span v-else class="texto-ok">Todo en stock ✓</span>
          </p>
        </div>
      </div>

      <div class="layout-principal">
        <ProductoForm
          :producto="productoEditando"
          @guardar="guardarProducto"
          @cancelar="cancelarEdicion"
        />

        <div class="lista-section">
          <div class="filtros">
            <input
              v-model="busqueda"
              type="text"
              placeholder="🔍 Buscar producto..."
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
            @editar="seleccionarParaEditar"
            @eliminar="eliminarProducto"
          />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import ProductoForm from './components/ProductoForm.vue'
import ProductoLista from './components/ProductoLista.vue'

let siguienteId = 6

const productos = ref([
  { id: 1, nombre: 'Coca-Cola 500ml', categoria: 'Bebidas', precio: 1500, stock: 24 },
  { id: 2, nombre: 'Alfajor Havanna', categoria: 'Golosinas', precio: 900, stock: 4 },
  { id: 3, nombre: 'Papas Lays Clásicas', categoria: 'Snacks', precio: 2000, stock: 8 },
  { id: 4, nombre: 'Galletitas Oreo', categoria: 'Galletitas', precio: 1200, stock: 15 },
  { id: 5, nombre: 'Agua Mineral 500ml', categoria: 'Bebidas', precio: 800, stock: 40 },
])

const productoEditando = ref(null)

const busqueda = ref('')
const categoriaFiltro = ref('')

const categorias = ['Bebidas', 'Golosinas', 'Snacks', 'Galletitas', 'Helados', 'Varios']

const totalProductos = computed(() => productos.value.length)

const productosStockBajo = computed(() =>
  productos.value.filter(p => p.stock < 5).length
)

const productosFiltrados = computed(() => {
  let resultado = productos.value

  if (busqueda.value) {
    const termino = busqueda.value.toLowerCase()
    resultado = resultado.filter(p => p.nombre.toLowerCase().includes(termino))
  }

  if (categoriaFiltro.value) {
    resultado = resultado.filter(p => p.categoria === categoriaFiltro.value)
  }

  return resultado
})

watch(
  productos,
  (nuevaLista) => {
    console.log(`📦 Inventario actualizado: ${nuevaLista.length} productos`)
  },
  { deep: true }
)

function guardarProducto(datosProducto) {
  if (productoEditando.value) {
    const indice = productos.value.findIndex(p => p.id === productoEditando.value.id)
    if (indice !== -1) {
      productos.value[indice] = {
        ...datosProducto,
        id: productoEditando.value.id
      }
    }
    productoEditando.value = null
  } else {
    productos.value.push({
      ...datosProducto,
      id: siguienteId++
    })
  }
}

function seleccionarParaEditar(id) {
  const producto = productos.value.find(p => p.id === id)
  if (producto) {
    productoEditando.value = { ...producto }
  }
}

function eliminarProducto(id) {
  const producto = productos.value.find(p => p.id === id)
  if (producto && confirm(`¿Estás seguro de eliminar "${producto.nombre}"?`)) {
    productos.value = productos.value.filter(p => p.id !== id)
    if (productoEditando.value && productoEditando.value.id === id) {
      productoEditando.value = null
    }
  }
}

function cancelarEdicion() {
  productoEditando.value = null
}
</script>
