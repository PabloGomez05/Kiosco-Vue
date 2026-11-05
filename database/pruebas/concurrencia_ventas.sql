-- =============================================================================
-- SISTEMA DE GESTIÓN E INVENTARIO PARA KIOSCO
-- Script de Prueba de Transaccionalidad, Concurrencia y Auditoría · MySQL 8.0
-- Materia: Programación II · Docente: José Olivera · Autor: Pablo
--
-- Este archivo contiene:
--   1. Procedimiento transaccional completo de una venta (con bloqueo pesimista
--      SELECT ... FOR UPDATE para evitar stock negativo bajo concurrencia).
--   2. Guía paso a paso para reproducir en 2 terminales la prueba de dos ventas
--      concurrentes que compiten por el último stock disponible.
--   3. Consultas de auditoría para verificar las invariantes de consistencia.
-- =============================================================================

USE kiosk_db;

-- =============================================================================
-- PARTE 1: TRANSACCIÓN MODELO DE UNA VENTA CON BLOQUEO ATÓMICO DE FILA
-- =============================================================================
-- Ejemplo: El vendedor (id_usuario = 2) vende 2 unidades de "Alfajor Havanna"
-- (id_producto = 2, cuyo stock actual en la semilla es 4).
-- =============================================================================

START TRANSACTION;

-- Paso 1: Bloquear las filas de los productos involucrados en orden ascendente
--         de id_producto (ordenar por PK evita deadlocks entre transacciones).
SELECT id_producto, nombre, precio_venta, stock_actual
  FROM productos
 WHERE id_producto IN (2)
   AND activo = TRUE
 ORDER BY id_producto
   FOR UPDATE;

-- (En el backend Express se verifica aquí: si stock_actual < cantidad_solicitada,
--  se ejecuta ROLLBACK y se devuelve HTTP 409 Conflict con código STOCK_INSUFICIENTE.
--  Además, si aun así se intentara descontar más del stock disponible, la
--  restricción chk_productos_stock CHECK (stock_actual >= 0) aborta el UPDATE).

-- Paso 2: Insertar cabecera del ticket con clave de idempotencia única (UUID v4)
INSERT INTO ventas (idempotency_key, id_usuario, total, estado, observaciones)
VALUES ('a1b2c3d4-e5f6-4789-abcd-ef0123456789', 2, 1900.00, 'confirmada', 'Prueba transaccional');

SET @nueva_venta_id = LAST_INSERT_ID();

-- Paso 3: Insertar renglones congelando el precio_unitario vigente (subtotal se calcula solo)
INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario)
VALUES (@nueva_venta_id, 2, 2, 950.00);

-- Paso 4: Registrar el/los medios de pago en la entidad asociativa pagos_venta
INSERT INTO pagos_venta (id_venta, medio_pago, monto, referencia)
VALUES (@nueva_venta_id, 'efectivo', 1900.00, NULL);

-- Paso 5: Descontar stock de manera atómica
UPDATE productos
   SET stock_actual = stock_actual - 2
 WHERE id_producto = 2;

-- Paso 6: Dejar trazabilidad en movimientos_stock (validado por chk_mov_aritmetica)
INSERT INTO movimientos_stock (id_producto, id_usuario, tipo, cantidad, stock_anterior, stock_posterior, id_venta, motivo)
VALUES (2, 2, 'venta', 2, 4, 2, @nueva_venta_id, CONCAT('Venta ticket #', @nueva_venta_id));

COMMIT;


-- =============================================================================
-- PARTE 2: DEMOSTRACIÓN DE CONCURRENCIA (2 VENTAS SIMULTÁNEAS)
-- =============================================================================
-- Escenario: Quedan exactamente 2 unidades de Alfajor Havanna (id_producto = 2).
--            Dos cajeros (Sesión A y Sesión B) intentan vender 2 unidades cada
--            uno al mismo tiempo.
--
-- SESIÓN A (Terminal 1):
--   USE kiosk_db;
--   START TRANSACTION;
--   SELECT id_producto, stock_actual FROM productos WHERE id_producto = 2 FOR UPDATE;
--   -- Obtiene stock_actual = 2 y mantiene el bloqueo exclusivo (X-lock) sobre la fila.
--
-- SESIÓN B (Terminal 2, ejecutada antes de que la Sesión A haga COMMIT):
--   USE kiosk_db;
--   START TRANSACTION;
--   SELECT id_producto, stock_actual FROM productos WHERE id_producto = 2 FOR UPDATE;
--   -- Queda en espera (bloqueada por InnoDB) hasta que la Sesión A libere el lock.
--
-- SESIÓN A (Terminal 1 continúa):
--   UPDATE productos SET stock_actual = stock_actual - 2 WHERE id_producto = 2;
--   -- ... (inserta venta, detalle, pago y movimiento_stock) ...
--   COMMIT;
--   -- Stock queda en 0 y se libera el bloqueo.
--
-- SESIÓN B (Terminal 2 se desbloquea automáticamente):
--   -- El SELECT ... FOR UPDATE de la Sesión B retorna ahora stock_actual = 0
--   -- (lectura actual gracias al bloqueo pesimista).
--   -- El backend detecta stock_actual (0) < cantidad (2) y ejecuta:
--   ROLLBACK;
--   -- (Y aun si ejecutara UPDATE productos SET stock_actual = stock_actual - 2,
--   --  MySQL rechaza la sentencia con:
--   --  ERROR 3819 (HY000): Check constraint 'chk_productos_stock' is violated).
-- =============================================================================


-- =============================================================================
-- PARTE 3: CONSULTAS DE VERIFICACIÓN DE CONSISTENCIA (AUDITORÍA)
-- =============================================================================
-- Ninguna de estas 3 consultas debe devolver filas en una base consistente:

-- 3.1 Ventas cuyo total no coincide con la suma de sus renglones:
SELECT v.id_venta, v.total, COALESCE(SUM(d.subtotal), 0) AS suma_detalles
  FROM ventas v
  LEFT JOIN detalle_ventas d ON d.id_venta = v.id_venta
 GROUP BY v.id_venta, v.total
HAVING v.total <> suma_detalles;

-- 3.2 Ventas cuyo total no coincide con la suma de sus pagos:
SELECT v.id_venta, v.total, COALESCE(SUM(p.monto), 0) AS suma_pagos
  FROM ventas v
  LEFT JOIN pagos_venta p ON p.id_venta = v.id_venta
 GROUP BY v.id_venta, v.total
HAVING v.total <> suma_pagos;

-- 3.3 Productos cuyo stock_actual no coincide con el balance de movimientos_stock:
SELECT pr.id_producto,
       pr.nombre,
       pr.stock_actual,
       COALESCE(SUM(
         CASE
           WHEN m.tipo IN ('ingreso','ajuste_positivo','anulacion_venta') THEN  m.cantidad
           WHEN m.tipo IN ('venta','ajuste_negativo')                     THEN -m.cantidad
         END
       ), 0) AS stock_segun_movimientos
  FROM productos pr
  LEFT JOIN movimientos_stock m ON m.id_producto = pr.id_producto
 GROUP BY pr.id_producto, pr.nombre, pr.stock_actual
HAVING pr.stock_actual <> stock_segun_movimientos;

