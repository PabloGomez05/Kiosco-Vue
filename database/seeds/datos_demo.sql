-- =============================================================================
-- SISTEMA DE GESTIÓN E INVENTARIO PARA KIOSCO
-- Datos Semilla (Seeds) de Demostración · MySQL 8.0
-- Materia: Programación II · Docente: José Olivera · Autor: Pablo
--
-- Ejecución (luego de correr database/schema.sql):
--   mysql -u root -p kiosk_db < database/seeds/datos_demo.sql
--
-- Contraseña de ambos usuarios de prueba: Kiosco2026!
-- (Hash bcrypt generado con 10 salt rounds)
-- =============================================================================

USE kiosk_db;

START TRANSACTION;

-- 1. Usuarios iniciales (1 Administrador y 1 Vendedor)
INSERT INTO usuarios (id_usuario, nombre_completo, usuario, email, password_hash, rol, activo) VALUES
(1, 'Pablo Administrador', 'admin', 'admin@kiosco.local', '$2b$10$wO8qGg0Oq6o8O/FhY3CqveFjJ8g41o4f2o8M/k7Q9H5G8yY9N1SZe', 'admin', TRUE),
(2, 'Juan Pérez (Cajero)', 'vendedor', 'juan@kiosco.local', '$2b$10$wO8qGg0Oq6o8O/FhY3CqveFjJ8g41o4f2o8M/k7Q9H5G8yY9N1SZe', 'vendedor', TRUE);

-- 2. Categorías del kiosco
INSERT INTO categorias (id_categoria, nombre, descripcion, activo) VALUES
(1, 'Bebidas',    'Gaseosas, aguas saborizadas, aguas minerales y energizantes', TRUE),
(2, 'Golosinas',  'Alfajores, chocolates, caramelos, gomitas y chicles', TRUE),
(3, 'Snacks',     'Papas fritas, palitos salados, maní y nachos', TRUE),
(4, 'Galletitas', 'Galletitas dulces, saladas y rellenas', TRUE),
(5, 'Varios',     'Encendedores, pilas, pañuelos descartables y otros artículos', TRUE);

-- 3. Proveedores habituales (con CUIT validado por expresión regular)
INSERT INTO proveedores (id_proveedor, razon_social, cuit, contacto, telefono, email, activo) VALUES
(1, 'Coca-Cola FEMSA de Buenos Aires S.A.', '30-52011245-8', 'Mariana López',  '011-5678-1234', 'pedidos@cocacola-femsa.com.ar', TRUE),
(2, 'Distribuidora Arcor S.A.I.C.',         '30-50279317-5', 'Carlos Gómez',   '011-4567-8901', 'ventas@arcor.com.ar', TRUE),
(3, 'Mondelēz Argentina S.A.',              '30-50085421-2', 'Roberto Díaz',   '011-6789-2345', 'contacto@mondelez.com.ar', TRUE);

-- 4. Productos del catálogo (stock inicial cargado junto con su movimiento_stock)
INSERT INTO productos (id_producto, codigo, nombre, descripcion, id_categoria, id_proveedor, precio_compra, precio_venta, stock_actual, stock_minimo, activo) VALUES
(1, '7790895000997', 'Coca-Cola Original 500ml',       'Botella PET descartable 500ml',       1, 1, 1000.00, 1500.00, 24,  6, TRUE),
(2, '7790040111103', 'Alfajor Havanna Chocolate 70g',  'Alfajor relleno con dulce de leche',  2, 2,  600.00,  950.00,  4,  8, TRUE),
(3, '7790310981234', 'Papas Lays Clásicas 85g',        'Bolsa mediana de papas fritas',       3, 3, 1300.00, 2000.00,  8,  5, TRUE),
(4, '7622300834128', 'Galletitas Oreo Regular 118g',   'Paquete de galletitas rellenas',      4, 3,  800.00, 1200.00, 15,  6, TRUE),
(5, '7790360000114', 'Agua Villavicencio Sin Gas 500ml','Botella PET 500ml',                  1, 1,  500.00,  850.00, 40, 10, TRUE);

-- 5. Historial de precios inicial (deja trazabilidad de cuándo se fijó el precio vigente)
INSERT INTO historial_precios (id_producto, precio_compra, precio_venta, id_usuario) VALUES
(1, 1000.00, 1500.00, 1),
(2,  600.00,  950.00, 1),
(3, 1300.00, 2000.00, 1),
(4,  800.00, 1200.00, 1),
(5,  500.00,  850.00, 1);

-- 6. Movimientos de stock iniciales (ingreso de inventario inicial)
INSERT INTO movimientos_stock (id_producto, id_usuario, tipo, cantidad, stock_anterior, stock_posterior, id_venta, motivo) VALUES
(1, 1, 'ingreso', 26, 0, 26, NULL, 'Inventario inicial - Remito #0001-00001234'),
(2, 1, 'ingreso',  4, 0,  4, NULL, 'Inventario inicial - Remito #0002-00004512'),
(3, 1, 'ingreso',  8, 0,  8, NULL, 'Inventario inicial - Remito #0003-00008810'),
(4, 1, 'ingreso', 16, 0, 16, NULL, 'Inventario inicial - Remito #0003-00008810'),
(5, 1, 'ingreso', 40, 0, 40, NULL, 'Inventario inicial - Remito #0001-00001234');

-- 7. Venta de ejemplo confirmada (2 Coca-Colas + 1 Oreo = $4200, pago mixto: $2000 efectivo + $2200 transferencia)
INSERT INTO ventas (id_venta, idempotency_key, id_usuario, total, estado, observaciones) VALUES
(1, '550e8400-e29b-41d4-a716-446655440000', 2, 4200.00, 'confirmada', 'Venta de mostrador de ejemplo');

INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario) VALUES
(1, 1, 2, 1500.00),
(1, 4, 1, 1200.00);

INSERT INTO pagos_venta (id_venta, medio_pago, monto, referencia) VALUES
(1, 'efectivo',      2000.00, NULL),
(1, 'transferencia', 2200.00, 'MP-OP-99887766');

-- Movimientos de stock generados por la venta #1 (dejan el stock en 24 y 15 respectivamente)
INSERT INTO movimientos_stock (id_producto, id_usuario, tipo, cantidad, stock_anterior, stock_posterior, id_venta, motivo) VALUES
(1, 2, 'venta', 2, 26, 24, 1, 'Venta ticket #1'),
(4, 2, 'venta', 1, 16, 15, 1, 'Venta ticket #1');

COMMIT;

