# Sistema de Gestión e Inventario para Kiosco (`Kiosco-Vue`)

> **Proyecto Final Integrador – Tecnicatura Superior en Desarrollo de Software**  
> **Materia:** Programación II · **Docente:** Prof. José Olivera · **Autor:** Pablo Hernán Gómez

Sistema web de Punto de Venta (POS), control de inventario y arqueo diario de caja para kioscos. Desarrollado bajo una arquitectura en **3 capas** que combina una interfaz reactiva en **Vue.js 3 (Composition API)**, una **API REST en Node.js** con autenticación **JWT** y control de acceso por roles (**RBAC**), y un modelo relacional transaccional **ACID en Tercera Forma Normal (3FN)** sobre **MySQL 8.0 (InnoDB)**.

---

## ✨ Funcionalidades Principales

- **Punto de Venta (Carrito POS) Transaccional:**
  - Registro atómico de ventas con descuento inmediato de stock (`START TRANSACTION` + `SELECT ... FOR UPDATE` + `COMMIT` / `ROLLBACK`).
  - Soporte para **Pago Único** o **Pago Mixto** (ej. parte en efectivo y parte por transferencia/débito) a través de la entidad asociativa `pagos_venta` (`1:N`).
  - Protección contra cobros duplicados mediante cabecera de idempotencia (`Idempotency-Key` UUID v4).
- **Catálogo, Inventario y Trazabilidad:**
  - ABM de productos y categorías dinámicas con baja lógica (`activo = 0` / `ON DELETE RESTRICT`).
  - Alertas visuales automáticas de stock crítico (`stock_actual <= stock_minimo`).
  - Bitácora inmutable de variaciones de inventario (`movimientos_stock`) e historial auditable de cambios de precios (`historial_precios`).
- **Seguridad JWT y Permisos en Servidor (RBAC):**
  - Roles diferenciados (`admin` y `vendedor`) validados por endpoint en el backend (`server/middlewares/auth.js`), respondiendo `HTTP 403 Forbidden` ante accesos no autorizados.
- **Arqueo y Cierre de Caja Diario:**
  - Conciliación del turno (`cierres_caja`) y bloqueo automático post-cierre (`403 CAJA_CERRADA`).

---

## 🛠️ Stack Tecnológico

| Capa | Tecnologías |
| :--- | :--- |
| **Frontend (SPA)** | Vue.js 3 (`<script setup>`, `ref`, `computed`, `defineProps`, `defineEmits`), Vite, CSS3 |
| **Backend (API REST)** | Node.js (ES Modules), Servidor HTTP REST, Middleware JWT (`HS256` con `node:crypto`) |
| **Base de Datos** | MySQL 8.0 (`InnoDB`, `utf8mb4`, 10 tablas en 3FN), Pool de conexiones `mysql2/promise` + Motor transaccional local para demostración inmediata |
| **Contrato y Pruebas** | Especificación OpenAPI 3.0.3 (Swagger) y suite de pruebas automatizadas (`npm run test:hito`) |

---

## 🚀 Puesta en Marcha Rápida

```bash
git clone https://github.com/PabloGomez05/Kiosco-Vue.git
cd Kiosco-Vue
npm install
npm run dev          # Levanta Frontend Vue 3 + API REST integrada en http://localhost:5173
```

### Comandos adicionales
```bash
npm run test:hito    # Ejecuta la suite automatizada de 6 pruebas (Login JWT, 403, Venta ACID, Idempotencia, Concurrencia y Cierre de Caja)
npm run server       # Ejecuta el servidor API REST de forma independiente en http://localhost:3000
npm run build        # Compila el frontend de producción en dist/
```

---

## 📂 Estructura del Repositorio y Material Entregado

```text
Kiosco-Vue/
├── Documentación_Proyecto_Kiosco.docx   # Documentación técnica completa (v2.1)
├── presentacion_defensa.html            # Presentación interactiva de diapositivas expuesta en clase
├── database/
│   ├── schema.sql                       # DDL ejecutable en MySQL 8.0 (10 tablas en 3FN, DECIMAL, CHECK, RESTRICT, INDEX)
│   ├── er_diagram_completo.png          # Diagrama Entidad-Relación (DER) final de 10 entidades
│   ├── seeds/datos_demo.sql             # Datos semilla iniciales (usuarios, categorías, proveedores, productos, venta y stock)
│   ├── migrations/                      # Script de migración incremental v2.0 -> v2.1
│   └── pruebas/concurrencia_ventas.sql  # Script de transacción con SELECT ... FOR UPDATE y prueba de 2 sesiones concurrentes
├── docs/
│   ├── openapi.yaml                     # Especificación OpenAPI 3.0.3 (Swagger) con ErrorResponse, paginación e idempotencia
│   └── ui_mockup_pos.png                # Maqueta visual del Punto de Venta
├── server/
│   ├── app.js                           # Enrutador y controladores REST
│   ├── index.js                         # Punto de entrada del servidor HTTP standalone
│   ├── middlewares/auth.js              # Autenticación JWT (401) y autorización por rol RBAC (403)
│   ├── services/ventaMysqlService.js    # Pool de conexión MySQL 8.0 (mysql2/promise) y transacción SQL ACID
│   ├── services/kioscoEngine.js         # Motor transaccional con bloqueo exclusivo (Mutex) y Rollback por snapshot
│   └── tests/demo_hito_06_11.test.js    # Suite de verificación automatizada extremo a extremo
└── src/
    ├── App.vue                          # Componente raíz orquestador del POS
    ├── components/ProductoLista.vue     # Catálogo con búsqueda reactiva y alertas de stock bajo
    ├── components/CarritoVenta.vue      # Carrito POS con soporte de pago único y pago mixto
    └── components/ProductoForm.vue      # Formulario de alta y edición de productos
```

---

## 📄 Enlaces Directos al Material de Entrega y Exposición

- 📘 **Documentación Técnica Oficial (Word):** [Documentación_Proyecto_Kiosco.docx](./Documentación_Proyecto_Kiosco.docx)
- 🖥️ **Presentación Interactiva de Defensa (HTML):** [presentacion_defensa.html](./presentacion_defensa.html)
- 🗂️ **Diagrama Entidad-Relación (DER 3FN):** [database/er_diagram_completo.png](./database/er_diagram_completo.png)
- 🗄️ **Script DDL MySQL 8.0:** [database/schema.sql](./database/schema.sql)
- 🌱 **Datos Semilla SQL:** [database/seeds/datos_demo.sql](./database/seeds/datos_demo.sql)
- ⚡ **Prueba SQL de Concurrencia (`SELECT ... FOR UPDATE`):** [database/pruebas/concurrencia_ventas.sql](./database/pruebas/concurrencia_ventas.sql)
- 📑 **Contrato API REST (OpenAPI 3.0.3):** [docs/openapi.yaml](./docs/openapi.yaml)

---

## 🙋‍♂️ Autor

**Pablo Hernán Gómez**  
*Tecnicatura Superior en Desarrollo de Software – Programación II*
