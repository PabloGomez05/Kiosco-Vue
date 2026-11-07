// =============================================================================
// server/services/ventaMysqlService.js
// Conexión a Base de Datos MySQL 8.0 (Pool mysql2/promise) e Implementación
// Transaccional SQL (START TRANSACTION -> SELECT ... FOR UPDATE -> COMMIT/ROLLBACK)
// =============================================================================

import mysql from 'mysql2/promise';

/**
 * Crea el Pool de Conexiones hacia MySQL 8.0 (Base de datos: kiosk_db)
 */
export function crearPoolMysql() {
  return mysql.createPool({
    host: process.env.DB_HOST || '127.0.0.1',
    port: Number(process.env.DB_PORT || 3306),
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '',
    database: process.env.DB_NAME || 'kiosk_db',
    waitForConnections: true,
    connectionLimit: 10,
    decimalNumbers: true
  });
}

export async function registrarVentaEnMySQL(pool, { idempotencyKey, idUsuario, items, pagos, observaciones }) {
  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();

    // 1. Verificar idempotencia por UUID
    const [existente] = await conn.execute(
      'SELECT id_venta, total, fecha_hora, estado FROM ventas WHERE idempotency_key = ?',
      [idempotencyKey]
    );
    if (existente.length > 0) {
      await conn.rollback();
      return { idempotente: true, venta: existente[0] };
    }

    // 2. Verificar que el vendedor no haya cerrado ya su caja del día
    const [cierreHoy] = await conn.execute(
      'SELECT id_cierre FROM cierres_caja WHERE id_usuario = ? AND fecha = CURDATE()',
      [idUsuario]
    );
    if (cierreHoy.length > 0) {
      const err = new Error('Caja cerrada: el vendedor ya consolidó su cierre en la fecha actual.');
      err.status = 403;
      err.code = 'CAJA_CERRADA';
      throw err;
    }

    // 3. Bloqueo pesimista SELECT ... FOR UPDATE en orden ascendente de id_producto (previene deadlocks)
    const idsOrdenados = [...new Set(items.map(i => Number(i.id_producto)))].sort((a, b) => a - b);
    const placeholders = idsOrdenados.map(() => '?').join(', ');
    const [productosRows] = await conn.execute(
      `SELECT id_producto, nombre, precio_venta, stock_actual, activo
         FROM productos
        WHERE id_producto IN (${placeholders})
        ORDER BY id_producto
          FOR UPDATE`,
      idsOrdenados
    );

    const mapaProductos = new Map(productosRows.map(p => [Number(p.id_producto), p]));
    let totalCalculado = 0;

    for (const item of items) {
      const prod = mapaProductos.get(Number(item.id_producto));
      if (!prod || !prod.activo) {
        const err = new Error(`El producto ID ${item.id_producto} no existe o se encuentra inactivo.`);
        err.status = 404;
        err.code = 'PRODUCTO_NO_DISPONIBLE';
        throw err;
      }
      if (Number(prod.stock_actual) < Number(item.cantidad)) {
        const err = new Error(
          `Stock insuficiente para '${prod.nombre}' (disponible: ${prod.stock_actual}, solicitado: ${item.cantidad}).`
        );
        err.status = 409;
        err.code = 'STOCK_INSUFICIENTE';
        throw err;
      }
      totalCalculado += Number(prod.precio_venta) * Number(item.cantidad);
    }

    totalCalculado = Math.round(totalCalculado * 100) / 100;
    const sumaPagos = Math.round(pagos.reduce((acc, p) => acc + Number(p.monto), 0) * 100) / 100;

    if (Math.abs(sumaPagos - totalCalculado) > 0.01) {
      const err = new Error(
        `La suma de los pagos ($${sumaPagos.toFixed(2)}) no coincide con el total de la venta ($${totalCalculado.toFixed(2)}).`
      );
      err.status = 400;
      err.code = 'MONTO_PAGO_INVALIDO';
      throw err;
    }

    // 4. Insertar cabecera de venta
    const [resVenta] = await conn.execute(
      'INSERT INTO ventas (idempotency_key, id_usuario, total, estado, observaciones) VALUES (?, ?, ?, "confirmada", ?)',
      [idempotencyKey, idUsuario, totalCalculado.toFixed(2), observaciones || null]
    );
    const idVenta = resVenta.insertId;

    // 5. Insertar detalle_ventas, actualizar stock_actual e insertar movimientos_stock
    for (const item of items) {
      const prod = mapaProductos.get(Number(item.id_producto));
      const cantidad = Number(item.cantidad);
      const stockAnterior = Number(prod.stock_actual);
      const stockPosterior = stockAnterior - cantidad;

      await conn.execute(
        'INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario) VALUES (?, ?, ?, ?)',
        [idVenta, prod.id_producto, cantidad, prod.precio_venta]
      );

      await conn.execute(
        'UPDATE productos SET stock_actual = ? WHERE id_producto = ?',
        [stockPosterior, prod.id_producto]
      );

      await conn.execute(
        `INSERT INTO movimientos_stock
          (id_producto, id_usuario, tipo, cantidad, stock_anterior, stock_posterior, id_venta, motivo)
         VALUES (?, ?, 'venta', ?, ?, ?, ?, ?)`,
        [prod.id_producto, idUsuario, cantidad, stockAnterior, stockPosterior, idVenta, `Venta ticket #${idVenta}`]
      );
    }

    // 6. Insertar medios de pago en la entidad asociativa pagos_venta
    for (const pago of pagos) {
      await conn.execute(
        'INSERT INTO pagos_venta (id_venta, medio_pago, monto, referencia) VALUES (?, ?, ?, ?)',
        [idVenta, pago.medio_pago, Number(pago.monto).toFixed(2), pago.referencia || null]
      );
    }

    await conn.commit();
    return { idempotente: false, id_venta: idVenta, total: totalCalculado };
  } catch (error) {
    await conn.rollback();
    throw error;
  } finally {
    conn.release();
  }
}

