-- =============================================================================
-- SISTEMA DE GESTIÓN E INVENTARIO PARA KIOSCO
-- Script DDL de creación de la base de datos · MySQL 8.0.16 o superior
-- Materia: Programación II · Tecnicatura Superior en Desarrollo de Software
-- Autor: Pablo · Versión del modelo: 2.1 (02/11/2026)
--
-- Uso (desde la carpeta Kiosco-Vue):
--   mysql -u root -p < database/schema.sql
--   mysql -u root -p kiosk_db < database/seeds/datos_demo.sql
--
-- ATENCIÓN: el script es re-ejecutable porque BORRA y vuelve a crear kiosk_db.
--           No ejecutarlo sobre una base con datos que se quieran conservar.
--
-- Criterios de diseño:
--   * Motor InnoDB (transacciones ACID, bloqueos de fila, claves foráneas).
--   * utf8mb4 (soporta tildes, ñ y emojis); collation accent-insensitive.
--   * Montos en DECIMAL (exactos). Nunca FLOAT/DOUBLE para dinero.
--   * Claves foráneas con ON DELETE RESTRICT: no se borra nada referenciado;
--     las bajas son lógicas (columna activo).
--   * Índices explícitos y con nombre en claves foráneas y columnas de fecha.
--   * Cada columna lleva COMMENT: el diccionario de datos se obtiene de
--     information_schema, así la documentación no se desincroniza del DDL.
-- =============================================================================

DROP DATABASE IF EXISTS kiosk_db;
CREATE DATABASE kiosk_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE kiosk_db;

-- -----------------------------------------------------------------------------
-- 1. usuarios: personas que operan el sistema y su rol
-- -----------------------------------------------------------------------------
CREATE TABLE usuarios (
  id_usuario      INT          NOT NULL AUTO_INCREMENT                COMMENT 'Identificador del usuario',
  nombre_completo VARCHAR(100) NOT NULL                               COMMENT 'Nombre y apellido',
  usuario         VARCHAR(50)  NOT NULL                               COMMENT 'Nombre de inicio de sesión (único)',
  email           VARCHAR(100) NOT NULL                               COMMENT 'Correo electrónico (único)',
  password_hash   VARCHAR(255) NOT NULL                               COMMENT 'Hash bcrypt; nunca se guarda la contraseña',
  rol             ENUM('admin','vendedor') NOT NULL DEFAULT 'vendedor' COMMENT 'Rol que valida el middleware del servidor',
  activo          BOOLEAN      NOT NULL DEFAULT TRUE                  COMMENT 'Baja lógica: FALSE impide iniciar sesión',
  creado_en       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP     COMMENT 'Fecha y hora de alta',
  CONSTRAINT pk_usuarios         PRIMARY KEY (id_usuario),
  CONSTRAINT uq_usuarios_usuario UNIQUE (usuario),
  CONSTRAINT uq_usuarios_email   UNIQUE (email)
) ENGINE=InnoDB COMMENT='Usuarios del sistema (admin o vendedor)';

-- -----------------------------------------------------------------------------
-- 2. categorias: clasificación de productos
-- -----------------------------------------------------------------------------
CREATE TABLE categorias (
  id_categoria INT          NOT NULL AUTO_INCREMENT COMMENT 'Identificador de la categoría',
  nombre       VARCHAR(50)  NOT NULL                COMMENT 'Nombre de la categoría (único)',
  descripcion  VARCHAR(255) NULL                    COMMENT 'Descripción opcional',
  activo       BOOLEAN      NOT NULL DEFAULT TRUE   COMMENT 'Baja lógica',
  CONSTRAINT pk_categorias        PRIMARY KEY (id_categoria),
  CONSTRAINT uq_categorias_nombre UNIQUE (nombre)
) ENGINE=InnoDB COMMENT='Categorías de productos';

-- -----------------------------------------------------------------------------
-- 3. proveedores: quién abastece la mercadería
-- -----------------------------------------------------------------------------
CREATE TABLE proveedores (
  id_proveedor INT          NOT NULL AUTO_INCREMENT COMMENT 'Identificador del proveedor',
  razon_social VARCHAR(100) NOT NULL                COMMENT 'Razón social',
  cuit         CHAR(13)     NOT NULL                COMMENT 'CUIT con formato XX-XXXXXXXX-X (único)',
  contacto     VARCHAR(100) NULL                    COMMENT 'Persona de contacto',
  telefono     VARCHAR(30)  NULL                    COMMENT 'Teléfono',
  email        VARCHAR(100) NULL                    COMMENT 'Correo electrónico',
  activo       BOOLEAN      NOT NULL DEFAULT TRUE   COMMENT 'Baja lógica',
  CONSTRAINT pk_proveedores        PRIMARY KEY (id_proveedor),
  CONSTRAINT uq_proveedores_cuit   UNIQUE (cuit),
  CONSTRAINT chk_proveedores_cuit  CHECK (REGEXP_LIKE(cuit, '^[0-9]{2}-[0-9]{8}-[0-9]$'))
) ENGINE=InnoDB COMMENT='Proveedores de mercadería';

-- -----------------------------------------------------------------------------
-- 4. productos: datos del producto + estado ACTUAL (precio vigente y stock).
--    La historia vive en otras tablas:
--      - historial_precios  -> cambios de precio en el tiempo
--      - movimientos_stock  -> cada entrada/salida de unidades
--      - detalle_ventas     -> precio al que se vendió cada unidad
-- -----------------------------------------------------------------------------
CREATE TABLE productos (
  id_producto    INT           NOT NULL AUTO_INCREMENT COMMENT 'Identificador del producto',
  codigo         VARCHAR(50)   NULL                    COMMENT 'Código interno o de barras (único si se informa)',
  nombre         VARCHAR(100)  NOT NULL                COMMENT 'Nombre comercial (único)',
  descripcion    VARCHAR(255)  NULL                    COMMENT 'Presentación o detalle',
  id_categoria   INT           NOT NULL                COMMENT 'FK a categorias',
  id_proveedor   INT           NULL                    COMMENT 'FK a proveedores (proveedor habitual)',
  precio_compra  DECIMAL(12,2) NOT NULL                COMMENT 'Costo vigente',
  precio_venta   DECIMAL(12,2) NOT NULL                COMMENT 'Precio de venta vigente',
  stock_actual   INT           NOT NULL DEFAULT 0      COMMENT 'Unidades disponibles; solo cambia junto con un movimiento_stock',
  stock_minimo   INT           NOT NULL DEFAULT 0      COMMENT 'Umbral de alerta de stock bajo',
  activo         BOOLEAN       NOT NULL DEFAULT TRUE   COMMENT 'Baja lógica: FALSE lo oculta del punto de venta',
  creado_en      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de alta',
  actualizado_en DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Última modificación',
  CONSTRAINT pk_productos              PRIMARY KEY (id_producto),
  CONSTRAINT uq_productos_codigo       UNIQUE (codigo),
  CONSTRAINT uq_productos_nombre       UNIQUE (nombre),
  CONSTRAINT chk_productos_precio_comp CHECK (precio_compra >= 0),
  CONSTRAINT chk_productos_precio_vta  CHECK (precio_venta > 0),
  CONSTRAINT chk_productos_stock       CHECK (stock_actual >= 0),
  CONSTRAINT chk_productos_stock_min   CHECK (stock_minimo >= 0),
  INDEX idx_productos_categoria (id_categoria),
  INDEX idx_productos_proveedor (id_proveedor),
  CONSTRAINT fk_productos_categoria FOREIGN KEY (id_categoria)
    REFERENCES categorias (id_categoria) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_productos_proveedor FOREIGN KEY (id_proveedor)
    REFERENCES proveedores (id_proveedor) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB COMMENT='Catálogo de productos: datos, precio vigente y stock actual';

-- -----------------------------------------------------------------------------
-- 5. historial_precios: un registro por cada precio que tuvo un producto
-- -----------------------------------------------------------------------------
CREATE TABLE historial_precios (
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

-- -----------------------------------------------------------------------------
-- 6. ventas: cabecera del ticket
--    total es una redundancia CONTROLADA: debe ser igual a la suma de los
--    subtotales y a la suma de los pagos. La API lo verifica dentro de la
--    transacción y database/pruebas/verificar_consistencia.sql lo audita.
-- -----------------------------------------------------------------------------
CREATE TABLE ventas (
  id_venta        INT           NOT NULL AUTO_INCREMENT COMMENT 'Número de ticket',
  idempotency_key CHAR(36)      NOT NULL                COMMENT 'UUID enviado por el cliente; evita registrar dos veces la misma venta',
  id_usuario      INT           NOT NULL                COMMENT 'FK a usuarios: vendedor que cobró',
  fecha_hora      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Momento de la venta',
  total           DECIMAL(12,2) NOT NULL                COMMENT 'Importe total (= suma de subtotales = suma de pagos)',
  estado          ENUM('confirmada','anulada') NOT NULL DEFAULT 'confirmada' COMMENT 'Estado del ticket',
  observaciones   VARCHAR(255)  NULL                    COMMENT 'Notas o motivo de anulación',
  CONSTRAINT pk_ventas             PRIMARY KEY (id_venta),
  CONSTRAINT uq_ventas_idempotency UNIQUE (idempotency_key),
  CONSTRAINT chk_ventas_total      CHECK (total > 0),
  INDEX idx_ventas_usuario_fecha (id_usuario, fecha_hora),
  INDEX idx_ventas_fecha (fecha_hora),
  CONSTRAINT fk_ventas_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios (id_usuario) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB COMMENT='Cabecera de cada venta (ticket)';

-- -----------------------------------------------------------------------------
-- 7. detalle_ventas: entidad asociativa que resuelve la relación N:M
--    ventas <-> productos. Congela el precio del momento de la venta.
--    subtotal es una columna GENERADA: no puede quedar inconsistente.
-- -----------------------------------------------------------------------------
CREATE TABLE detalle_ventas (
  id_detalle      INT           NOT NULL AUTO_INCREMENT COMMENT 'Identificador del renglón',
  id_venta        INT           NOT NULL                COMMENT 'FK a ventas',
  id_producto     INT           NOT NULL                COMMENT 'FK a productos',
  cantidad        INT           NOT NULL                COMMENT 'Unidades vendidas',
  precio_unitario DECIMAL(12,2) NOT NULL                COMMENT 'Precio congelado al momento de la venta',
  subtotal        DECIMAL(12,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED COMMENT 'Calculado: cantidad x precio_unitario',
  CONSTRAINT pk_detalle_ventas       PRIMARY KEY (id_detalle),
  CONSTRAINT uq_detalle_venta_prod   UNIQUE (id_venta, id_producto),
  CONSTRAINT chk_detalle_cantidad    CHECK (cantidad > 0),
  CONSTRAINT chk_detalle_precio      CHECK (precio_unitario >= 0),
  INDEX idx_detalle_producto (id_producto),
  CONSTRAINT fk_detalle_venta FOREIGN KEY (id_venta)
    REFERENCES ventas (id_venta) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_detalle_producto FOREIGN KEY (id_producto)
    REFERENCES productos (id_producto) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB COMMENT='Renglones de cada venta (resuelve N:M ventas-productos)';

-- -----------------------------------------------------------------------------
-- 8. pagos_venta: entidad asociativa venta <-> medio de pago.
--    Permite pagos mixtos (ej.: parte efectivo, parte transferencia).
--    El medio de pago vive SOLO acá (no se duplica en ventas).
-- -----------------------------------------------------------------------------
CREATE TABLE pagos_venta (
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

-- -----------------------------------------------------------------------------
-- 9. movimientos_stock: bitácora inmutable de entradas y salidas.
--    Invariante: stock_actual de un producto = suma de ingresos - egresos.
-- -----------------------------------------------------------------------------
CREATE TABLE movimientos_stock (
  id_movimiento   INT          NOT NULL AUTO_INCREMENT COMMENT 'Identificador del movimiento',
  id_producto     INT          NOT NULL                COMMENT 'FK a productos',
  id_usuario      INT          NOT NULL                COMMENT 'FK a usuarios: quién lo registró',
  tipo            ENUM('ingreso','venta','ajuste_positivo','ajuste_negativo','anulacion_venta') NOT NULL COMMENT 'Naturaleza del movimiento',
  cantidad        INT          NOT NULL                COMMENT 'Unidades movidas (siempre positiva)',
  stock_anterior  INT          NOT NULL                COMMENT 'Stock antes del movimiento',
  stock_posterior INT          NOT NULL                COMMENT 'Stock después del movimiento',
  id_venta        INT          NULL                    COMMENT 'FK a ventas (solo tipos venta y anulacion_venta)',
  motivo          VARCHAR(255) NULL                    COMMENT 'Remito, motivo del ajuste u observación',
  fecha_hora      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Momento del movimiento',
  CONSTRAINT pk_movimientos_stock PRIMARY KEY (id_movimiento),
  CONSTRAINT chk_mov_cantidad     CHECK (cantidad > 0),
  CONSTRAINT chk_mov_stock_ant    CHECK (stock_anterior >= 0),
  CONSTRAINT chk_mov_stock_post   CHECK (stock_posterior >= 0),
  CONSTRAINT chk_mov_aritmetica   CHECK (
    (tipo IN ('ingreso','ajuste_positivo','anulacion_venta') AND stock_posterior = stock_anterior + cantidad)
    OR (tipo IN ('venta','ajuste_negativo') AND stock_posterior = stock_anterior - cantidad)
  ),
  CONSTRAINT chk_mov_venta        CHECK ((tipo IN ('venta','anulacion_venta')) = (id_venta IS NOT NULL)),
  CONSTRAINT chk_mov_motivo_ajuste CHECK (tipo NOT IN ('ajuste_positivo','ajuste_negativo') OR motivo IS NOT NULL),
  INDEX idx_mov_producto_fecha (id_producto, fecha_hora),
  INDEX idx_mov_usuario (id_usuario),
  INDEX idx_mov_venta (id_venta),
  INDEX idx_mov_fecha (fecha_hora),
  CONSTRAINT fk_mov_producto FOREIGN KEY (id_producto)
    REFERENCES productos (id_producto) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_mov_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios (id_usuario) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT fk_mov_venta FOREIGN KEY (id_venta)
    REFERENCES ventas (id_venta) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB COMMENT='Bitácora de movimientos de stock';

-- -----------------------------------------------------------------------------
-- 10. cierres_caja: arqueo diario por vendedor (fotografía inmutable).
--     Los totales por medio se copian de pagos_venta al cerrar: si después
--     se corrigiera algo, el cierre conserva lo que se arqueó ese día.
-- -----------------------------------------------------------------------------
CREATE TABLE cierres_caja (
  id_cierre           INT           NOT NULL AUTO_INCREMENT COMMENT 'Identificador del cierre',
  id_usuario          INT           NOT NULL                COMMENT 'FK a usuarios: vendedor que cierra',
  fecha               DATE          NOT NULL                COMMENT 'Jornada cerrada (un cierre por vendedor y día)',
  cerrado_en          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Momento exacto del cierre',
  cantidad_ventas     INT           NOT NULL DEFAULT 0      COMMENT 'Tickets confirmados de la jornada',
  monto_inicial       DECIMAL(12,2) NOT NULL DEFAULT 0      COMMENT 'Efectivo con el que se abrió la caja (cambio)',
  total_efectivo      DECIMAL(12,2) NOT NULL DEFAULT 0      COMMENT 'Cobrado en efectivo',
  total_transferencia DECIMAL(12,2) NOT NULL DEFAULT 0      COMMENT 'Cobrado por transferencia o QR',
  total_debito        DECIMAL(12,2) NOT NULL DEFAULT 0      COMMENT 'Cobrado con tarjeta de débito',
  total_credito       DECIMAL(12,2) NOT NULL DEFAULT 0      COMMENT 'Cobrado con tarjeta de crédito',
  total_ventas        DECIMAL(12,2) GENERATED ALWAYS AS (total_efectivo + total_transferencia + total_debito + total_credito) STORED COMMENT 'Calculado: suma de los cuatro medios',
  efectivo_esperado   DECIMAL(12,2) GENERATED ALWAYS AS (monto_inicial + total_efectivo) STORED COMMENT 'Calculado: efectivo que debería haber en la caja',
  efectivo_contado    DECIMAL(12,2) NOT NULL                COMMENT 'Efectivo contado físicamente por el vendedor',
  diferencia          DECIMAL(12,2) GENERATED ALWAYS AS (efectivo_contado - monto_inicial - total_efectivo) STORED COMMENT 'Calculado: sobrante (+) o faltante (-)',
  observaciones       VARCHAR(255)  NULL                    COMMENT 'Explicación de diferencias',
  CONSTRAINT pk_cierres_caja         PRIMARY KEY (id_cierre),
  CONSTRAINT uq_cierres_usuario_fecha UNIQUE (id_usuario, fecha),
  CONSTRAINT chk_cierres_cantidad    CHECK (cantidad_ventas >= 0),
  CONSTRAINT chk_cierres_inicial     CHECK (monto_inicial >= 0),
  CONSTRAINT chk_cierres_efectivo    CHECK (total_efectivo >= 0),
  CONSTRAINT chk_cierres_transf      CHECK (total_transferencia >= 0),
  CONSTRAINT chk_cierres_debito      CHECK (total_debito >= 0),
  CONSTRAINT chk_cierres_credito     CHECK (total_credito >= 0),
  CONSTRAINT chk_cierres_contado     CHECK (efectivo_contado >= 0),
  INDEX idx_cierres_fecha (fecha),
  CONSTRAINT fk_cierres_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios (id_usuario) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB COMMENT='Cierres de caja diarios por vendedor';
