-- =============================================================================
-- SISTEMA DE GESTIÓN E INVENTARIO PARA KIOSCO
-- Migración 001: Evolución del esquema v2.0 -> v2.1
-- Materia: Programación II · Docente: José Olivera · Autor: Pablo
--
-- Propósito:
--   Aplica sobre una base creada con la versión 2.0 los cambios solicitados
--   en la segunda devolución docente:
--     1. Crea la tabla historial_precios (separa precios históricos del estado
--        actual del producto).
--     2. Crea la entidad asociativa pagos_venta (permite pagos mixtos y elimina
--        el atributo medio_pago de la cabecera ventas).
--     3. Agrega idempotency_key (UUID único) en ventas para garantizar
--        idempotencia ante reintentos de red o doble clic.
--     4. Crea los índices explícitos en claves foráneas y columnas de fecha.
-- =============================================================================

USE kiosk_db;

-- 1. Tabla de historial de precios
CREATE TABLE IF NOT EXISTS historial_precios (
  id_historial  INT           NOT NULL AUTO_INCREMENT COMMENT 'Identificador del registro',
  id_producto   INT           NOT NULL                COMMENT 'FK a productos',
  precio_compra DECIMAL(12,2) NOT NULL                COMMENT 'Costo a partir de vigente_desde',
  precio_venta  DECIMAL(12,2) NOT NULL                COMMENT 'Precio de venta a partir de vigente_desde',
  vigente_desde DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Momento en que empezó a regir',
  id_usuario    INT           NOT NULL                COMMENT 'FK a usuarios: quién cargó el precio',
  CONSTRAINT pk_historial_precios      PRIMARY KEY (id_historial),
  CONSTRAINT chk_historial_precio_comp CHECK (precio_compra >= 0),
  CONSTRAINT chk_historial_precio_vta  CHECK (precio_venta > 0),
  INDEX idx_historial_producto_fecha (id_producto, vigente_desde),
  INDEX idx_historial_usuario (id_usuario),
  CONSTRAINT fk_historial_producto FOREIGN KEY (id_producto)
    REFERENCES productos (id_producto) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_historial_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios (id_usuario) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB COMMENT='Historial de precios por producto';

-- 2. Entidad asociativa pagos_venta (venta <-> medio de pago)
CREATE TABLE IF NOT EXISTS pagos_venta (
  id_pago    INT           NOT NULL AUTO_INCREMENT COMMENT 'Identificador del pago',
  id_venta   INT           NOT NULL                COMMENT 'FK a ventas',
  medio_pago ENUM('efectivo','transferencia','debito','credito') NOT NULL COMMENT 'Medio de pago utilizado',
  monto      DECIMAL(12,2) NOT NULL                COMMENT 'Importe imputado a la venta (sin el vuelto)',
  referencia VARCHAR(100)  NULL                    COMMENT 'Nro. de operación de transferencia o tarjeta',
  CONSTRAINT pk_pagos_venta       PRIMARY KEY (id_pago),
  CONSTRAINT uq_pagos_venta_medio UNIQUE (id_venta, medio_pago),
  CONSTRAINT chk_pagos_monto      CHECK (monto > 0),
  CONSTRAINT fk_pagos_venta FOREIGN KEY (id_venta)
    REFERENCES ventas (id_venta) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB COMMENT='Pagos de cada venta por medio de pago';

