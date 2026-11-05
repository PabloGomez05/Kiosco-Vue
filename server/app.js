// =============================================================================
// server/app.js
// Enrutador y Controladores de la API REST del Sistema de Kiosco
// Cumple la especificación OpenAPI 3.0.3 (docs/openapi.yaml)
// Materia: Programación II · Docente: José Olivera · Autor: Pablo Gómez
// =============================================================================

import crypto from 'node:crypto';
import {
  firmarTokenJWT,
  autenticarToken,
  autorizarRol,
  crearErrorUniforme
} from './middlewares/auth.js';
import { kioscoDB } from './services/kioscoEngine.js';

function leerJsonBody(req) {
  return new Promise((resolve, reject) => {
    if (req.body && typeof req.body === 'object') {
      return resolve(req.body);
    }
    let raw = '';
    req.on('data', chunk => {
      raw += chunk;
    });
    req.on('end', () => {
      if (!raw) return resolve({});
      try {
        resolve(JSON.parse(raw));
      } catch {
        reject(new Error('El cuerpo de la petición no es un JSON válido.'));
      }
    });
    req.on('error', reject);
  });
}

function responderJSON(res, status, payload) {
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, Idempotency-Key');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.end(JSON.stringify(payload));
}

function paginar(array, pageParam, limitParam) {
  const page = Math.max(1, parseInt(pageParam || '1', 10) || 1);
  const limit = Math.min(100, Math.max(1, parseInt(limitParam || '20', 10) || 20));
  const total_items = array.length;
  const total_pages = Math.max(1, Math.ceil(total_items / limit));
  const inicio = (page - 1) * limit;
  const data = array.slice(inicio, inicio + limit);
  return {
    data,
    meta: { page, limit, total_items, total_pages }
  };
}

export async function handleApiRequest(req, res) {
  if (req.method === 'OPTIONS') {
    return responderJSON(res, 200, { ok: true });
  }

  const parsedUrl = new URL(req.url, 'http://localhost');
  const pathname = parsedUrl.pathname;
  const query = Object.fromEntries(parsedUrl.searchParams.entries());

  try {
    // -------------------------------------------------------------------------
    // 1. POST /api/auth/login (Ruta pública)
    // -------------------------------------------------------------------------
    if (req.method === 'POST' && pathname === '/api/auth/login') {
      const body = await leerJsonBody(req);
      const { usuario, password } = body;

      if (!usuario || !password) {
        return responderJSON(
          res,
          400,
          crearErrorUniforme('DATOS_INCOMPLETOS', 'Debe ingresar usuario y contraseña.', pathname)
        );
      }

      const usr = kioscoDB.state.usuarios.find(
        u => u.usuario === String(usuario).trim() && u.activo
      );
      if (!usr || usr.password_plain !== String(password)) {
        return responderJSON(
          res,
          401,
          crearErrorUniforme('CREDENCIALES_INVALIDAS', 'Usuario o contraseña incorrectos.', pathname)
        );
      }

      const { token, expires_in } = firmarTokenJWT(usr);
      return responderJSON(res, 200, {
        token,
        expires_in,
        usuario: {
          id_usuario: usr.id_usuario,
          nombre_completo: usr.nombre_completo,
          usuario: usr.usuario,
          email: usr.email,
          rol: usr.rol
        }
      });
    }

    // -------------------------------------------------------------------------
    // Todas las rutas siguientes requieren JWT válido (Middleware autenticarToken)
    // -------------------------------------------------------------------------
    const authResult = autenticarToken(req);
    if (!authResult.ok) {
      return responderJSON(res, authResult.status, authResult.body);
    }

    // -------------------------------------------------------------------------
    // 2. GET /api/categorias (Roles: vendedor, admin)
    // -------------------------------------------------------------------------
    if (req.method === 'GET' && pathname === '/api/categorias') {
      const activas = kioscoDB.state.categorias.filter(c => c.activo);
      return responderJSON(res, 200, { data: activas });
    }

    // -------------------------------------------------------------------------
    // 3. GET /api/productos (Roles: vendedor, admin) con filtros y paginación
    // -------------------------------------------------------------------------
    if (req.method === 'GET' && pathname === '/api/productos') {
      const incluirInactivos = req.user.rol === 'admin' && query.incluir_inactivos === 'true';
      let lista = kioscoDB.state.productos
        .filter(p => (incluirInactivos ? true : p.activo))
        .map(p => {
          const cat = kioscoDB.state.categorias.find(c => c.id_categoria === p.id_categoria);
          const prov = kioscoDB.state.proveedores.find(pr => pr.id_proveedor === p.id_proveedor);
          return {
            ...p,
            categoria: cat ? cat.nombre : 'Sin categoría',
            proveedor: prov ? prov.razon_social : null,
            bajo_stock: p.stock_actual <= p.stock_minimo
          };
        });

      if (query.search) {
        const q = query.search.toLowerCase();
        lista = lista.filter(
          p =>
            p.nombre.toLowerCase().includes(q) ||
            (p.codigo && p.codigo.toLowerCase().includes(q))
        );
      }
      if (query.id_categoria) {
        lista = lista.filter(p => p.id_categoria === Number(query.id_categoria));
      }
      if (query.categoria) {
        lista = lista.filter(p => p.categoria === query.categoria);
      }
      if (query.bajo_stock === 'true') {
        lista = lista.filter(p => p.bajo_stock);
      }

      return responderJSON(res, 200, paginar(lista, query.page, query.limit));
    }

    // -------------------------------------------------------------------------
    // 4. POST /api/productos (Solo rol: admin -> Prueba 403 para vendedor)
    // -------------------------------------------------------------------------
    if (req.method === 'POST' && pathname === '/api/productos') {
      const rbac = autorizarRol(req, ['admin']);
      if (!rbac.ok) return responderJSON(res, rbac.status, rbac.body);

      const body = await leerJsonBody(req);
      const nombre = String(body.nombre || '').trim();
      const precioCompra = Number(body.precio_compra ?? Math.round(Number(body.precio_venta || 0) * 0.65));
      const precioVenta = Number(body.precio_venta ?? body.precio);
      const stockInicial = Number(body.stock_actual ?? body.stock ?? 0);
      const stockMinimo = Number(body.stock_minimo ?? 5);

      if (!nombre || isNaN(precioVenta) || precioVenta <= 0 || stockInicial < 0 || stockMinimo < 0) {
        return responderJSON(
          res,
          400,
          crearErrorUniforme(
            'VALIDACION_PRODUCTO',
            'Nombre obligatorio, precio de venta > 0 y stock >= 0.',
            pathname
          )
        );
      }

      const resultado = await kioscoDB.ejecutarEnTransaccion(async db => {
        if (db.productos.some(p => p.nombre.toLowerCase() === nombre.toLowerCase())) {
          const err = new Error(`Ya existe un producto con el nombre '${nombre}'.`);
          err.status = 409;
          err.code = 'PRODUCTO_DUPLICADO';
          throw err;
        }

        let idCat = Number(body.id_categoria || 0);
        if (!idCat && body.categoria) {
          const catObj = db.categorias.find(c => c.nombre === body.categoria);
          idCat = catObj ? catObj.id_categoria : 1;
        }
        if (!idCat) idCat = 1;

        const ahora = new Date().toISOString();
        const nuevoId = db.productos.reduce((max, p) => Math.max(max, p.id_producto), 0) + 1;
        const nuevoProd = {
          id_producto: nuevoId,
          codigo: body.codigo || `77900000000${nuevoId}`,
          nombre,
          descripcion: body.descripcion || null,
          id_categoria: idCat,
          id_proveedor: body.id_proveedor || 1,
          precio_compra: precioCompra,
          precio_venta: precioVenta,
          stock_actual: stockInicial,
          stock_minimo: stockMinimo,
          activo: true,
          creado_en: ahora,
          actualizado_en: ahora
        };
        db.productos.push(nuevoProd);

        const nextHistId = db.historial_precios.reduce((m, h) => Math.max(m, h.id_historial), 0) + 1;
        db.historial_precios.push({
          id_historial: nextHistId,
          id_producto: nuevoId,
          precio_compra: precioCompra,
          precio_venta: precioVenta,
          vigente_desde: ahora,
          id_usuario: req.user.id_usuario
        });

        if (stockInicial > 0) {
          const nextMovId = db.movimientos_stock.reduce((m, x) => Math.max(m, x.id_movimiento), 0) + 1;
          db.movimientos_stock.push({
            id_movimiento: nextMovId,
            id_producto: nuevoId,
            id_usuario: req.user.id_usuario,
            tipo: 'ingreso',
            cantidad: stockInicial,
            stock_anterior: 0,
            stock_posterior: stockInicial,
            id_venta: null,
            motivo: 'Stock inicial en alta de producto',
            fecha_hora: ahora
          });
        }

        return nuevoProd;
      });

      return responderJSON(res, 201, resultado);
    }

    // -------------------------------------------------------------------------
    // 5. PUT / DELETE /api/productos/:id (Solo rol: admin)
    // -------------------------------------------------------------------------
    const matchProdId = pathname.match(/^\/api\/productos\/(\d+)$/);
    if (matchProdId) {
      const idProd = Number(matchProdId[1]);
      const rbac = autorizarRol(req, ['admin']);
      if (!rbac.ok) return responderJSON(res, rbac.status, rbac.body);

      if (req.method === 'PUT') {
        const body = await leerJsonBody(req);
        const actualizado = await kioscoDB.ejecutarEnTransaccion(async db => {
          const prod = db.productos.find(p => p.id_producto === idProd);
          if (!prod) {
            const err = new Error(`Producto #${idProd} no encontrado.`);
            err.status = 404;
            err.code = 'NO_ENCONTRADO';
            throw err;
          }
          const ahora = new Date().toISOString();
          const nuevoPrecioVenta = Number(body.precio_venta ?? body.precio ?? prod.precio_venta);
          const nuevoPrecioCompra = Number(body.precio_compra ?? prod.precio_compra);

          if (nuevoPrecioVenta <= 0 || nuevoPrecioCompra < 0) {
            const err = new Error('Los precios deben ser válidos y mayores a cero.');
            err.status = 400;
            err.code = 'PRECIO_INVALIDO';
            throw err;
          }

          if (nuevoPrecioVenta !== prod.precio_venta || nuevoPrecioCompra !== prod.precio_compra) {
            const nextHistId = db.historial_precios.reduce((m, h) => Math.max(m, h.id_historial), 0) + 1;
            db.historial_precios.push({
              id_historial: nextHistId,
              id_producto: idProd,
              precio_compra: nuevoPrecioCompra,
              precio_venta: nuevoPrecioVenta,
              vigente_desde: ahora,
              id_usuario: req.user.id_usuario
            });
          }

          if (body.nombre) prod.nombre = String(body.nombre).trim();
          if (body.categoria) {
            const catObj = db.categorias.find(c => c.nombre === body.categoria);
            if (catObj) prod.id_categoria = catObj.id_categoria;
          }
          if (body.id_categoria) prod.id_categoria = Number(body.id_categoria);
          if (body.stock_minimo !== undefined) prod.stock_minimo = Number(body.stock_minimo);
          prod.precio_compra = nuevoPrecioCompra;
          prod.precio_venta = nuevoPrecioVenta;
          prod.actualizado_en = ahora;
          return prod;
        });

        return responderJSON(res, 200, actualizado);
      }

      if (req.method === 'DELETE') {
        const baja = await kioscoDB.ejecutarEnTransaccion(async db => {
          const prod = db.productos.find(p => p.id_producto === idProd);
          if (!prod) {
            const err = new Error(`Producto #${idProd} no encontrado.`);
            err.status = 404;
            err.code = 'NO_ENCONTRADO';
            throw err;
          }
          prod.activo = false;
          prod.actualizado_en = new Date().toISOString();
          return prod;
        });
        return responderJSON(res, 200, {
          message: `Baja lógica aplicada a '${baja.nombre}' (activo = false). Historial de ventas preservado.`,
          producto: baja
        });
      }
    }

    // -------------------------------------------------------------------------
    // 6. GET / POST /api/stock/movimientos
    // -------------------------------------------------------------------------
    if (pathname === '/api/stock/movimientos') {
      if (req.method === 'GET') {
        const lista = [...kioscoDB.state.movimientos_stock]
          .sort((a, b) => b.id_movimiento - a.id_movimiento)
          .map(m => {
            const prod = kioscoDB.state.productos.find(p => p.id_producto === m.id_producto);
            const usr = kioscoDB.state.usuarios.find(u => u.id_usuario === m.id_usuario);
            return {
              ...m,
              nombre_producto: prod ? prod.nombre : `Producto #${m.id_producto}`,
              usuario: usr ? usr.nombre_completo : `Usuario #${m.id_usuario}`
            };
          });
        return responderJSON(res, 200, paginar(lista, query.page, query.limit));
      }

      if (req.method === 'POST') {
        const body = await leerJsonBody(req);
        const tipo = body.tipo || 'ingreso';
        // Los ajustes manuales requieren rol admin; la reposición ('ingreso') la pueden hacer vendedor o admin
        if (tipo !== 'ingreso') {
          const rbac = autorizarRol(req, ['admin']);
          if (!rbac.ok) return responderJSON(res, rbac.status, rbac.body);
        }

        const mov = await kioscoDB.ejecutarEnTransaccion(async db => {
          const prod = db.productos.find(p => p.id_producto === Number(body.id_producto) && p.activo);
          if (!prod) {
            const err = new Error('Producto no encontrado o inactivo.');
            err.status = 404;
            err.code = 'PRODUCTO_NO_DISPONIBLE';
            throw err;
          }
          const cantidad = Number(body.cantidad);
          if (!Number.isInteger(cantidad) || cantidad <= 0) {
            const err = new Error('La cantidad debe ser un entero positivo.');
            err.status = 400;
            err.code = 'CANTIDAD_INVALIDA';
            throw err;
          }
          const motivo = String(body.motivo || '').trim();
          if (!motivo) {
            const err = new Error('El motivo o número de remito es obligatorio.');
            err.status = 400;
            err.code = 'MOTIVO_OBLIGATORIO';
            throw err;
          }

          const stockAnterior = prod.stock_actual;
          const esSuma = ['ingreso', 'ajuste_positivo'].includes(tipo);
          const stockPosterior = esSuma ? stockAnterior + cantidad : stockAnterior - cantidad;
          if (stockPosterior < 0) {
            const err = new Error(`El ajuste dejaría el stock en negativo (${stockPosterior}).`);
            err.status = 409;
            err.code = 'STOCK_INSUFICIENTE';
            throw err;
          }

          const ahora = new Date().toISOString();
          prod.stock_actual = stockPosterior;
          prod.actualizado_en = ahora;

          const nuevoMovId = db.movimientos_stock.reduce((m, x) => Math.max(m, x.id_movimiento), 0) + 1;
          const registro = {
            id_movimiento: nuevoMovId,
            id_producto: prod.id_producto,
            id_usuario: req.user.id_usuario,
            tipo,
            cantidad,
            stock_anterior: stockAnterior,
            stock_posterior: stockPosterior,
            id_venta: null,
            motivo,
            fecha_hora: ahora
          };
          db.movimientos_stock.push(registro);
          return { movimiento: registro, producto: prod };
        });

        return responderJSON(res, 201, mov);
      }
    }

    // -------------------------------------------------------------------------
    // 7. GET / POST /api/ventas (Núcleo Transaccional ACID + Idempotencia)
    // -------------------------------------------------------------------------
    if (pathname === '/api/ventas') {
      if (req.method === 'GET') {
        let ventas = [...kioscoDB.state.ventas].sort((a, b) => b.id_venta - a.id_venta);
        if (req.user.rol !== 'admin') {
          ventas = ventas.filter(v => v.id_usuario === req.user.id_usuario);
        }
        const detalladas = ventas.map(v => kioscoDB.armarVentaCompleta(v.id_venta));
        return responderJSON(res, 200, paginar(detalladas, query.page, query.limit));
      }

      if (req.method === 'POST') {
        const body = await leerJsonBody(req);
        const idempotencyKey =
          req.headers['idempotency-key'] ||
          req.headers['Idempotency-Key'] ||
          body.idempotency_key ||
          crypto.randomUUID();

        const resultado = await kioscoDB.registrarVenta({
          idempotencyKey: String(idempotencyKey).trim(),
          idUsuario: req.user.id_usuario,
          items: body.items,
          pagos: body.pagos,
          observaciones: body.observaciones
        });

        // Si la clave de idempotencia ya había sido procesada, responde 200 OK sin volver a descontar stock
        const statusCode = resultado.idempotente ? 200 : 201;
        return responderJSON(res, statusCode, resultado);
      }
    }

    // -------------------------------------------------------------------------
    // 8. GET /api/caja/estado y POST /api/caja/cierre
    // -------------------------------------------------------------------------
    if (req.method === 'GET' && pathname === '/api/caja/estado') {
      const hoy = new Date().toISOString().slice(0, 10);
      const cierreHoy = kioscoDB.state.cierres_caja.find(
        c => c.id_usuario === req.user.id_usuario && c.fecha === hoy
      );
      const ventasHoy = kioscoDB.state.ventas.filter(
        v =>
          v.id_usuario === req.user.id_usuario &&
          v.estado === 'confirmada' &&
          v.fecha_hora.slice(0, 10) === hoy
      );
      const idsVentasHoy = new Set(ventasHoy.map(v => v.id_venta));
      const pagosHoy = kioscoDB.state.pagos_venta.filter(p => idsVentasHoy.has(p.id_venta));

      const totales = { efectivo: 0, transferencia: 0, debito: 0, credito: 0, total: 0 };
      for (const p of pagosHoy) {
        totales[p.medio_pago] = Math.round(((totales[p.medio_pago] || 0) + p.monto) * 100) / 100;
        totales.total = Math.round((totales.total + p.monto) * 100) / 100;
      }

      return responderJSON(res, 200, {
        fecha: hoy,
        cerrada: Boolean(cierreHoy),
        cierre: cierreHoy || null,
        cantidad_ventas: ventasHoy.length,
        totales_acumulados: totales
      });
    }

    if (req.method === 'POST' && pathname === '/api/caja/cierre') {
      const body = await leerJsonBody(req);
      const cierre = await kioscoDB.ejecutarEnTransaccion(async db => {
        const hoy = new Date().toISOString().slice(0, 10);
        const existente = db.cierres_caja.find(
          c => c.id_usuario === req.user.id_usuario && c.fecha === hoy
        );
        if (existente) {
          const err = new Error('Ya existe un cierre de caja registrado para tu usuario en la fecha de hoy.');
          err.status = 409;
          err.code = 'CIERRE_YA_EXISTE';
          throw err;
        }

        const montoInicial = Number(body.monto_inicial ?? 0);
        const efectivoContado = Number(body.efectivo_contado ?? 0);
        if (isNaN(montoInicial) || montoInicial < 0 || isNaN(efectivoContado) || efectivoContado < 0) {
          const err = new Error('El monto inicial y el efectivo contado deben ser mayores o iguales a 0.');
          err.status = 400;
          err.code = 'MONTO_ARQUEO_INVALIDO';
          throw err;
        }

        const ventasHoy = db.ventas.filter(
          v =>
            v.id_usuario === req.user.id_usuario &&
            v.estado === 'confirmada' &&
            v.fecha_hora.slice(0, 10) === hoy
        );
        const idsVentas = new Set(ventasHoy.map(v => v.id_venta));
        const pagosHoy = db.pagos_venta.filter(p => idsVentas.has(p.id_venta));

        const sumPorMedio = { efectivo: 0, transferencia: 0, debito: 0, credito: 0 };
        for (const p of pagosHoy) {
          sumPorMedio[p.medio_pago] = Math.round((sumPorMedio[p.medio_pago] + p.monto) * 100) / 100;
        }

        const totalVentas =
          Math.round(
            (sumPorMedio.efectivo + sumPorMedio.transferencia + sumPorMedio.debito + sumPorMedio.credito) * 100
          ) / 100;
        const efectivoEsperado = Math.round((montoInicial + sumPorMedio.efectivo) * 100) / 100;
        const diferencia = Math.round((efectivoContado - efectivoEsperado) * 100) / 100;

        const nuevoIdCierre = db.cierres_caja.reduce((m, c) => Math.max(m, c.id_cierre), 0) + 1;
        const nuevoCierre = {
          id_cierre: nuevoIdCierre,
          id_usuario: req.user.id_usuario,
          fecha: hoy,
          cerrado_en: new Date().toISOString(),
          cantidad_ventas: ventasHoy.length,
          monto_inicial: montoInicial,
          total_efectivo: sumPorMedio.efectivo,
          total_transferencia: sumPorMedio.transferencia,
          total_debito: sumPorMedio.debito,
          total_credito: sumPorMedio.credito,
          total_ventas: totalVentas,
          efectivo_esperado: efectivoEsperado,
          efectivo_contado: efectivoContado,
          diferencia,
          observaciones: body.observaciones || null
        };
        db.cierres_caja.push(nuevoCierre);
        return nuevoCierre;
      });

      return responderJSON(res, 201, cierre);
    }

    // -------------------------------------------------------------------------
    // 9. POST /api/demo/reset (Restaurar datos semilla para repetir la demo)
    // -------------------------------------------------------------------------
    if (req.method === 'POST' && pathname === '/api/demo/reset') {
      kioscoDB.resetearSemilla();
      return responderJSON(res, 200, {
        message: 'Base de datos restaurada al estado semilla inicial (datos_demo.sql).'
      });
    }

    return responderJSON(
      res,
      404,
      crearErrorUniforme('ENDPOINT_NO_ENCONTRADO', `La ruta ${req.method} ${pathname} no existe.`, pathname)
    );
  } catch (err) {
    const status = err.status || 500;
    const code = err.code || 'ERROR_TRANSACCIONAL';
    return responderJSON(
      res,
      status,
      crearErrorUniforme(code, err.message || 'Error interno en el servidor.', pathname, err.details || [])
    );
  }
}
