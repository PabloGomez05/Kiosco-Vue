// =============================================================================
// server/services/kioscoEngine.js
// Motor Transaccional Relacional (3FN) con Bloqueo Pesimista (Mutex Lock),
// Rollback Atómico, Idempotencia y Persistencia de Semillas
// Materia: Programación II · Docente: José Olivera · Autor: Pablo Gómez
// =============================================================================

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DATA_FILE = path.join(__dirname, '..', 'data', 'kiosk_state.json');

function fechaHoyISO() {
  return new Date().toISOString().slice(0, 10);
}

export function crearEstadoSemillaInicial() {
  const ahora = new Date().toISOString();
  return {
    usuarios: [
      { id_usuario: 1, nombre_completo: 'Pablo Administrador', usuario: 'admin', email: 'admin@kiosco.local', password_plain: 'Kiosco2026!', rol: 'admin', activo: true, creado_en: ahora },
      { id_usuario: 2, nombre_completo: 'Juan Pérez (Cajero)', usuario: 'vendedor', email: 'juan@kiosco.local', password_plain: 'Kiosco2026!', rol: 'vendedor', activo: true, creado_en: ahora }
    ],
    categorias: [
      { id_categoria: 1, nombre: 'Bebidas', descripcion: 'Gaseosas, aguas saborizadas, aguas minerales y energizantes', activo: true },
      { id_categoria: 2, nombre: 'Golosinas', descripcion: 'Alfajores, chocolates, caramelos, gomitas y chicles', activo: true },
      { id_categoria: 3, nombre: 'Snacks', descripcion: 'Papas fritas, palitos salados, maní y nachos', activo: true },
      { id_categoria: 4, nombre: 'Galletitas', descripcion: 'Galletitas dulces, saladas y rellenas', activo: true },
      { id_categoria: 5, nombre: 'Varios', descripcion: 'Encendedores, pilas, pañuelos descartables y otros artículos', activo: true }
    ],
    proveedores: [
      { id_proveedor: 1, razon_social: 'Coca-Cola FEMSA de Buenos Aires S.A.', cuit: '30-52011245-8', contacto: 'Mariana López', telefono: '011-5678-1234', email: 'pedidos@cocacola-femsa.com.ar', activo: true },
      { id_proveedor: 2, razon_social: 'Distribuidora Arcor S.A.I.C.', cuit: '30-50279317-5', contacto: 'Carlos Gómez', telefono: '011-4567-8901', email: 'ventas@arcor.com.ar', activo: true },
      { id_proveedor: 3, razon_social: 'Mondelēz Argentina S.A.', cuit: '30-50085421-2', contacto: 'Roberto Díaz', telefono: '011-6789-2345', email: 'contacto@mondelez.com.ar', activo: true }
    ],
    productos: [
      { id_producto: 1, codigo: '7790895000997', nombre: 'Coca-Cola Original 500ml', descripcion: 'Botella PET descartable 500ml', id_categoria: 1, id_proveedor: 1, precio_compra: 1000.00, precio_venta: 1500.00, stock_actual: 24, stock_minimo: 6, activo: true, creado_en: ahora, actualizado_en: ahora },
      { id_producto: 2, codigo: '7790040111103', nombre: 'Alfajor Havanna Chocolate 70g', descripcion: 'Alfajor relleno con dulce de leche', id_categoria: 2, id_proveedor: 2, precio_compra: 600.00, precio_venta: 950.00, stock_actual: 4, stock_minimo: 8, activo: true, creado_en: ahora, actualizado_en: ahora },
      { id_producto: 3, codigo: '7790310981234', nombre: 'Papas Lays Clásicas 85g', descripcion: 'Bolsa mediana de papas fritas', id_categoria: 3, id_proveedor: 3, precio_compra: 1300.00, precio_venta: 2000.00, stock_actual: 8, stock_minimo: 5, activo: true, creado_en: ahora, actualizado_en: ahora },
      { id_producto: 4, codigo: '7622300834128', nombre: 'Galletitas Oreo Regular 118g', descripcion: 'Paquete de galletitas rellenas', id_categoria: 4, id_proveedor: 3, precio_compra: 800.00, precio_venta: 1200.00, stock_actual: 15, stock_minimo: 6, activo: true, creado_en: ahora, actualizado_en: ahora },
      { id_producto: 5, codigo: '7790360000114', nombre: 'Agua Villavicencio Sin Gas 500ml', descripcion: 'Botella PET 500ml', id_categoria: 1, id_proveedor: 1, precio_compra: 500.00, precio_venta: 850.00, stock_actual: 40, stock_minimo: 10, activo: true, creado_en: ahora, actualizado_en: ahora }
    ],
    historial_precios: [
      { id_historial: 1, id_producto: 1, precio_compra: 1000.00, precio_venta: 1500.00, vigente_desde: ahora, id_usuario: 1 },
      { id_historial: 2, id_producto: 2, precio_compra: 600.00, precio_venta: 950.00, vigente_desde: ahora, id_usuario: 1 },
      { id_historial: 3, id_producto: 3, precio_compra: 1300.00, precio_venta: 2000.00, vigente_desde: ahora, id_usuario: 1 },
      { id_historial: 4, id_producto: 4, precio_compra: 800.00, precio_venta: 1200.00, vigente_desde: ahora, id_usuario: 1 },
      { id_historial: 5, id_producto: 5, precio_compra: 500.00, precio_venta: 850.00, vigente_desde: ahora, id_usuario: 1 }
    ],
    ventas: [
      { id_venta: 1, idempotency_key: '550e8400-e29b-41d4-a716-446655440000', id_usuario: 2, fecha_hora: ahora, total: 4200.00, estado: 'confirmada', observaciones: 'Venta de mostrador de ejemplo (Semilla inicial)' }
    ],
    detalle_ventas: [
      { id_detalle: 1, id_venta: 1, id_producto: 1, cantidad: 2, precio_unitario: 1500.00, subtotal: 3000.00 },
      { id_detalle: 2, id_venta: 1, id_producto: 4, cantidad: 1, precio_unitario: 1200.00, subtotal: 1200.00 }
    ],
    pagos_venta: [
      { id_pago: 1, id_venta: 1, medio_pago: 'efectivo', monto: 2000.00, referencia: null },
      { id_pago: 2, id_venta: 1, medio_pago: 'transferencia', monto: 2200.00, referencia: 'MP-OP-99887766' }
    ],
    movimientos_stock: [
      { id_movimiento: 1, id_producto: 1, id_usuario: 1, tipo: 'ingreso', cantidad: 26, stock_anterior: 0, stock_posterior: 26, id_venta: null, motivo: 'Inventario inicial - Remito #0001-00001234', fecha_hora: ahora },
      { id_movimiento: 2, id_producto: 2, id_usuario: 1, tipo: 'ingreso', cantidad: 4, stock_anterior: 0, stock_posterior: 4, id_venta: null, motivo: 'Inventario inicial - Remito #0002-00004512', fecha_hora: ahora },
      { id_movimiento: 3, id_producto: 3, id_usuario: 1, tipo: 'ingreso', cantidad: 8, stock_anterior: 0, stock_posterior: 8, id_venta: null, motivo: 'Inventario inicial - Remito #0003-00008810', fecha_hora: ahora },
      { id_movimiento: 4, id_producto: 4, id_usuario: 1, tipo: 'ingreso', cantidad: 16, stock_anterior: 0, stock_posterior: 16, id_venta: null, motivo: 'Inventario inicial - Remito #0003-00008810', fecha_hora: ahora },
      { id_movimiento: 5, id_producto: 5, id_usuario: 1, tipo: 'ingreso', cantidad: 40, stock_anterior: 0, stock_posterior: 40, id_venta: null, motivo: 'Inventario inicial - Remito #0001-00001234', fecha_hora: ahora },
      { id_movimiento: 6, id_producto: 1, id_usuario: 2, tipo: 'venta', cantidad: 2, stock_anterior: 26, stock_posterior: 24, id_venta: 1, motivo: 'Venta ticket #1', fecha_hora: ahora },
      { id_movimiento: 7, id_producto: 4, id_usuario: 2, tipo: 'venta', cantidad: 1, stock_anterior: 16, stock_posterior: 15, id_venta: 1, motivo: 'Venta ticket #1', fecha_hora: ahora }
    ],
    cierres_caja: []
  };
}

class KioscoTransactionalDB {
  constructor() {
    this.state = this.cargarEstado();
    this.lockPromise = Promise.resolve();
  }

  cargarEstado() {
    try {
      if (fs.existsSync(DATA_FILE)) {
        return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
      }
    } catch {
      // Si no existe o está corrupto, regenerar desde semilla
    }
    const inicial = crearEstadoSemillaInicial();
    this.guardarEstado(inicial);
    return inicial;
  }

  guardarEstado(estado = this.state) {
    try {
      const dir = path.dirname(DATA_FILE);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(DATA_FILE, JSON.stringify(estado, null, 2), 'utf8');
    } catch {
      // Ignorar si el sistema de archivos es de solo lectura
    }
  }

  resetearSemilla() {
    this.state = crearEstadoSemillaInicial();
    this.guardarEstado(this.state);
    return this.state;
  }

  /**
   * Serializa transacciones concurrentes simulando el bloqueo exclusivo (X-Lock)
   * de SELECT ... FOR UPDATE en InnoDB. Si la función lanza un error, restaura
   * la instantánea previa (ROLLBACK total); si termina bien, persiste (COMMIT).
   */
  async ejecutarEnTransaccion(fn) {
    const prevLock = this.lockPromise;
    let releaseLock;
    this.lockPromise = new Promise(resolve => {
      releaseLock = resolve;
    });

    await prevLock;
    const snapshot = JSON.parse(JSON.stringify(this.state));
    try {
      const resultado = await fn(this.state);
      this.guardarEstado(this.state); // COMMIT
      return resultado;
    } catch (err) {
      this.state = snapshot; // ROLLBACK ATÓMICO
      throw err;
    } finally {
      releaseLock();
    }
  }

  armarVentaCompleta(idVenta) {
    const v = this.state.ventas.find(x => x.id_venta === Number(idVenta));
    if (!v) return null;
    const usr = this.state.usuarios.find(u => u.id_usuario === v.id_usuario);
    const items = this.state.detalle_ventas
      .filter(d => d.id_venta === v.id_venta)
      .map(d => {
        const prod = this.state.productos.find(p => p.id_producto === d.id_producto);
        return {
          ...d,
          nombre_producto: prod ? prod.nombre : `Producto #${d.id_producto}`
        };
      });
    const pagos = this.state.pagos_venta.filter(p => p.id_venta === v.id_venta);
    return {
      ...v,
      vendedor: usr ? usr.nombre_completo : `Usuario #${v.id_usuario}`,
      items,
      pagos
    };
  }

  /**
   * Ejecuta la transacción completa de venta con validación de idempotencia,
   * caja abierta, bloqueo de stock (SELECT ... FOR UPDATE), inserción en
   * ventas, detalle_ventas, pagos_venta, descuento en productos y auditoría en
   * movimientos_stock.
   */
  async registrarVenta({ idempotencyKey, idUsuario, items, pagos, observaciones }) {
    return this.ejecutarEnTransaccion(async (db) => {
      // 1. Idempotencia: si el UUID ya existe, retornar la venta original sin descontar stock dos veces
      const ventaPrevia = db.ventas.find(v => v.idempotency_key === idempotencyKey);
      if (ventaPrevia) {
        return {
          idempotente: true,
          venta: this.armarVentaCompleta(ventaPrevia.id_venta)
        };
      }

      // 2. Verificar que la caja del día del vendedor no esté cerrada
      const hoy = fechaHoyISO();
      const cierreHoy = db.cierres_caja.find(
        c => c.id_usuario === Number(idUsuario) && c.fecha === hoy
      );
      if (cierreHoy) {
        const err = new Error('Caja cerrada: tu turno de hoy ya fue consolidado. No se pueden registrar ventas posteriores al cierre.');
        err.status = 403;
        err.code = 'CAJA_CERRADA';
        throw err;
      }

      // 3. Validar estructura de items y pagos
      if (!Array.isArray(items) || items.length === 0) {
        const err = new Error('La venta debe incluir al menos un ítem en el carrito.');
        err.status = 400;
        err.code = 'CARRITO_VACIO';
        throw err;
      }
      if (!Array.isArray(pagos) || pagos.length === 0) {
        const err = new Error('Debe especificarse al menos un medio de pago.');
        err.status = 400;
        err.code = 'PAGOS_VACIOS';
        throw err;
      }

      // Consolidar cantidades si un mismo id_producto vino repetido
      const itemsConsolidados = [];
      for (const raw of items) {
        const idProd = Number(raw.id_producto);
        const cant = Number(raw.cantidad);
        if (!Number.isInteger(cant) || cant <= 0) {
          const err = new Error(`La cantidad para el producto ID ${idProd} debe ser un entero mayor a 0.`);
          err.status = 400;
          err.code = 'CANTIDAD_INVALIDA';
          throw err;
        }
        const existente = itemsConsolidados.find(i => i.id_producto === idProd);
        if (existente) {
          existente.cantidad += cant;
        } else {
          itemsConsolidados.push({ id_producto: idProd, cantidad: cant });
        }
      }

      // Ordenar por id_producto ascendente (misma disciplina que SELECT ... FOR UPDATE)
      itemsConsolidados.sort((a, b) => a.id_producto - b.id_producto);

      // 4. Verificar existencia, estado activo y stock disponible
      let totalCalculado = 0;
      for (const item of itemsConsolidados) {
        const prod = db.productos.find(p => p.id_producto === item.id_producto);
        if (!prod || !prod.activo) {
          const err = new Error(`El producto ID ${item.id_producto} no existe o fue dado de baja lógica.`);
          err.status = 404;
          err.code = 'PRODUCTO_NO_DISPONIBLE';
          throw err;
        }
        if (prod.stock_actual < item.cantidad) {
          const err = new Error(
            `Stock insuficiente para '${prod.nombre}' (stock disponible: ${prod.stock_actual}, solicitado: ${item.cantidad}).`
          );
          err.status = 409;
          err.code = 'STOCK_INSUFICIENTE';
          err.details = [{ field: 'cantidad', issue: `Disponible ${prod.stock_actual}, solicitado ${item.cantidad}` }];
          throw err;
        }
        totalCalculado += Number(prod.precio_venta) * item.cantidad;
      }

      totalCalculado = Math.round(totalCalculado * 100) / 100;

      // 5. Validar pagos_venta y cuadratura con el total
      const mediosValidos = ['efectivo', 'transferencia', 'debito', 'credito'];
      const mediosUsados = new Set();
      let sumaPagos = 0;
      for (const pago of pagos) {
        if (!mediosValidos.includes(pago.medio_pago)) {
          const err = new Error(`Medio de pago inválido: '${pago.medio_pago}'.`);
          err.status = 400;
          err.code = 'MEDIO_PAGO_INVALIDO';
          throw err;
        }
        if (mediosUsados.has(pago.medio_pago)) {
          const err = new Error(`El medio de pago '${pago.medio_pago}' está repetido en el mismo ticket (restricción uq_pagos_venta_medio).`);
          err.status = 400;
          err.code = 'MEDIO_PAGO_DUPLICADO';
          throw err;
        }
        const monto = Number(pago.monto);
        if (isNaN(monto) || monto <= 0) {
          const err = new Error('El monto de cada medio de pago debe ser mayor a 0.');
          err.status = 400;
          err.code = 'MONTO_PAGO_INVALIDO';
          throw err;
        }
        mediosUsados.add(pago.medio_pago);
        sumaPagos += monto;
      }

      sumaPagos = Math.round(sumaPagos * 100) / 100;
      if (Math.abs(sumaPagos - totalCalculado) > 0.01) {
        const err = new Error(
          `La suma de pagos ($${sumaPagos.toFixed(2)}) no coincide con el total de la venta ($${totalCalculado.toFixed(2)}).`
        );
        err.status = 400;
        err.code = 'MONTO_PAGO_INVALIDO';
        throw err;
      }

      // 6. Insertar cabecera en ventas
      const ahora = new Date().toISOString();
      const nuevoIdVenta = db.ventas.reduce((max, v) => Math.max(max, v.id_venta), 0) + 1;
      db.ventas.push({
        id_venta: nuevoIdVenta,
        idempotency_key: idempotencyKey,
        id_usuario: Number(idUsuario),
        fecha_hora: ahora,
        total: totalCalculado,
        estado: 'confirmada',
        observaciones: observaciones || null
      });

      // 7. Insertar detalle_ventas, actualizar productos.stock_actual e insertar movimientos_stock
      let nextDetalleId = db.detalle_ventas.reduce((max, d) => Math.max(max, d.id_detalle), 0) + 1;
      let nextMovId = db.movimientos_stock.reduce((max, m) => Math.max(max, m.id_movimiento), 0) + 1;

      for (const item of itemsConsolidados) {
        const prod = db.productos.find(p => p.id_producto === item.id_producto);
        const stockAnterior = prod.stock_actual;
        const stockPosterior = stockAnterior - item.cantidad;
        const subtotal = Math.round(prod.precio_venta * item.cantidad * 100) / 100;

        db.detalle_ventas.push({
          id_detalle: nextDetalleId++,
          id_venta: nuevoIdVenta,
          id_producto: prod.id_producto,
          cantidad: item.cantidad,
          precio_unitario: prod.precio_venta,
          subtotal
        });

        prod.stock_actual = stockPosterior;
        prod.actualizado_en = ahora;

        db.movimientos_stock.push({
          id_movimiento: nextMovId++,
          id_producto: prod.id_producto,
          id_usuario: Number(idUsuario),
          tipo: 'venta',
          cantidad: item.cantidad,
          stock_anterior: stockAnterior,
          stock_posterior: stockPosterior,
          id_venta: nuevoIdVenta,
          motivo: `Venta ticket #${nuevoIdVenta}`,
          fecha_hora: ahora
        });
      }

      // 8. Insertar en la entidad asociativa pagos_venta
      let nextPagoId = db.pagos_venta.reduce((max, p) => Math.max(max, p.id_pago), 0) + 1;
      for (const pago of pagos) {
        db.pagos_venta.push({
          id_pago: nextPagoId++,
          id_venta: nuevoIdVenta,
          medio_pago: pago.medio_pago,
          monto: Math.round(Number(pago.monto) * 100) / 100,
          referencia: pago.referencia || null
        });
      }

      return {
        idempotente: false,
        venta: this.armarVentaCompleta(nuevoIdVenta)
      };
    });
  }
}

export const kioscoDB = new KioscoTransactionalDB();
