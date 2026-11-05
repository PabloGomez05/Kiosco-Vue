# Kiosk Management & Inventory System

> **Proyecto Integrador – Tecnicatura Superior en Desarrollo de Software**
> Materia: Programación II | Octubre 2026

Sistema web para la gestión de **inventario, ventas y cierre de caja** de pequeños kioscos. Reemplaza los cuadernos y planillas manuales, evitando errores de stock y dando trazabilidad para decidir reposiciones.

## ✨ Funcionalidades

- **Inventario (CRUD):** productos, categorías y proveedores.
- **Control de stock con alertas:** descuento automático al confirmar una venta y aviso visual de stock bajo.
- **Punto de venta / carrito:** subtotales, total y registro de la venta.
- **Historial de ventas y cierre de caja** diario.
- **Reportes y métricas** exportables a CSV.
- **Roles:** administrador y vendedor.

## 🛠️ Stack

| Capa | Tecnologías |
|------|-------------|
| Frontend | Vue.js 3 (Composition API), Vite, Vue Router, Axios |
| Backend | Node.js + Express |
| Base de datos | MySQL (3FN) |
| Autenticación | JWT + bcrypt |

## 🚀 Puesta en marcha

```bash
git clone https://github.com/PabloGomez05/Kiosco-Vue.git
cd Kiosco-Vue
npm install
cp .env.example .env   # configurar credenciales de MySQL y JWT
npm run dev            # http://localhost:5173
```

## 📄 Documentación, Base de Datos y Especificación API

- **Documentación técnica oficial (v2.1):** matriz de trazabilidad de observaciones, arquitectura, DER de 10 entidades en 3FN, reglas de negocio transaccionales, concurrencia, matriz RBAC y plan de trabajo:  
  👉 [Documentación_Proyecto_Kiosco.docx](./Documentación_Proyecto_Kiosco.docx)
- **Diagrama Entidad-Relación (DER v2.1):**  
  👉 [er_diagram_completo.png](./database/er_diagram_completo.png)
- **Scripts SQL (MySQL 8.0 / InnoDB / utf8mb4):**  
  - Creación DDL (10 tablas, `DECIMAL`, `CHECK`, `ON DELETE RESTRICT`, índices): [database/schema.sql](./database/schema.sql)
  - Datos semilla de demostración: [database/seeds/datos_demo.sql](./database/seeds/datos_demo.sql)
  - Migración incremental v2.0 → v2.1: [database/migrations/001_v2.0_a_v2.1_pagos_historial_indices.sql](./database/migrations/001_v2.0_a_v2.1_pagos_historial_indices.sql)
  - Prueba de transaccionalidad, concurrencia y auditoría: [database/pruebas/concurrencia_ventas.sql](./database/pruebas/concurrencia_ventas.sql)
- **Especificación OpenAPI 3.0.3 (Swagger):** errores uniformes, validaciones, paginación e idempotencia:  
  👉 [docs/openapi.yaml](./docs/openapi.yaml)


## 🙋‍♂️ Autor

**Pablo Gomez**
