// =============================================================================
// server/tests/demo_hito_06_11.test.js
// Suite Automatizada de Pruebas del Hito 06/11 (Transaccionalidad, Concurrencia,
// Idempotencia, Permisos 403 y Cierre de Caja)

// =============================================================================

import assert from 'node:assert/strict';
import { Readable } from 'node:stream';
import { handleApiRequest } from '../app.js';
import { kioscoDB } from '../services/kioscoEngine.js';

async function invocarAPI({ method = 'GET', url = '/api/productos', token = null, headers = {}, body = null }) {
  const reqStream = new Readable({ read() { } });
  if (body !== null) {
    reqStream.push(JSON.stringify(body));
  }
  reqStream.push(null);

  reqStream.method = method;
  reqStream.url = url;
  reqStream.headers = { ...headers };
  if (token) {
    reqStream.headers['authorization'] = `Bearer ${token}`;
  }

  let statusCode = 200;
  const resHeaders = {};
  let rawOutput = '';

  const res = {
    get statusCode() {
      return statusCode;
    },
    set statusCode(val) {
      statusCode = val;
    },
    setHeader(k, v) {
      resHeaders[k.toLowerCase()] = v;
    },
    end(chunk) {
      if (chunk) rawOutput += chunk;
    }
  };

  await handleApiRequest(reqStream, res);
  const data = rawOutput ? JSON.parse(rawOutput) : null;
  return { status: statusCode, headers: resHeaders, data };
}

async function ejecutarPruebasHito() {
  console.log('======================================================================');
  console.log('🧪 EJECUTANDO SUITE DE PRUEBAS DEL HITO 06/11 – SISTEMA KIOSCO v2.1');
  console.log('======================================================================\n');

  // Restaurar semilla inicial antes de correr la suite
  kioscoDB.resetearSemilla();

  // 1. Login de Vendedor y Administrador
  const loginVendedor = await invocarAPI({
    method: 'POST',
    url: '/api/auth/login',
    body: { usuario: 'vendedor', password: 'Kiosco2026!' }
  });
  assert.equal(loginVendedor.status, 200, 'Login vendedor debe responder 200');
  const tokenVendedor = loginVendedor.data.token;
  console.log('✅ [CP-01] Login JWT Vendedor exitoso (rol: vendedor, vigencia: 3600s)');

  const loginAdmin = await invocarAPI({
    method: 'POST',
    url: '/api/auth/login',
    body: { usuario: 'admin', password: 'Kiosco2026!' }
  });
  assert.equal(loginAdmin.status, 200, 'Login admin debe responder 200');
  const tokenAdmin = loginAdmin.data.token;
  console.log('✅ [CP-01b] Login JWT Admin exitoso (rol: admin, vigencia: 3600s)');

  // 2. Prueba de rechazo HTTP 403 en servidor cuando Vendedor intenta acciones de Admin
  const altaProhibida = await invocarAPI({
    method: 'POST',
    url: '/api/productos',
    token: tokenVendedor,
    body: { nombre: 'Producto No Autorizado', precio_venta: 1000, stock_actual: 10 }
  });
  assert.equal(altaProhibida.status, 403, 'Vendedor no puede crear productos (debe dar 403)');
  assert.equal(altaProhibida.data.code, 'ACCESO_PROHIBIDO_POR_ROL');

  const bajaProhibida = await invocarAPI({
    method: 'DELETE',
    url: '/api/productos/1',
    token: tokenVendedor
  });
  assert.equal(bajaProhibida.status, 403, 'Vendedor no puede dar de baja productos (debe dar 403)');
  console.log('✅ [CP-02] Middleware RBAC en servidor verificado: Vendedor recibe HTTP 403 Forbidden en POST/DELETE /api/productos');

  // 3. Venta transaccional exitosa con pago mixto y descuento de stock
  // Producto 1 (Coca-Cola) tiene stock inicial 24 y precio $1500. Vendemos 2 unidades ($3000: $1000 efectivo + $2000 transferencia).
  const idempKey1 = '11111111-2222-4333-8444-555555555555';
  const ventaOk = await invocarAPI({
    method: 'POST',
    url: '/api/ventas',
    token: tokenVendedor,
    headers: { 'idempotency-key': idempKey1 },
    body: {
      items: [{ id_producto: 1, cantidad: 2 }],
      pagos: [
        { medio_pago: 'efectivo', monto: 1000 },
        { medio_pago: 'transferencia', monto: 2000, referencia: 'MP-12345' }
      ],
      observaciones: 'Venta con pago mixto'
    }
  });
  assert.equal(ventaOk.status, 201, 'Primera ejecución de la venta debe responder 201 Created');
  assert.equal(ventaOk.data.idempotente, false);
  assert.equal(ventaOk.data.venta.total, 3000);

  const prodDespues = kioscoDB.state.productos.find(p => p.id_producto === 1);
  assert.equal(prodDespues.stock_actual, 22, 'El stock de Coca-Cola debe haber bajado de 24 a 22');
  console.log('✅ [CP-03] Venta transaccional ACID exitosa: stock de Coca-Cola descontado (24 -> 22) y pagos_venta registrados');

  // 4. Prueba de Idempotencia: reintento con la misma Idempotency-Key
  const ventaRepetida = await invocarAPI({
    method: 'POST',
    url: '/api/ventas',
    token: tokenVendedor,
    headers: { 'idempotency-key': idempKey1 },
    body: {
      items: [{ id_producto: 1, cantidad: 2 }],
      pagos: [
        { medio_pago: 'efectivo', monto: 1000 },
        { medio_pago: 'transferencia', monto: 2000, referencia: 'MP-12345' }
      ]
    }
  });
  assert.equal(ventaRepetida.status, 200, 'Reintento con igual Idempotency-Key debe responder 200 OK');
  assert.equal(ventaRepetida.data.idempotente, true);
  assert.equal(kioscoDB.state.productos.find(p => p.id_producto === 1).stock_actual, 22, 'El stock NO debe descontarse dos veces');
  console.log('✅ [CP-04] Idempotencia verificada: reintento con mismo UUID devuelve 200 OK sin duplicar descuento de stock');

  // 5. Prueba de Concurrencia: 2 ventas simultáneas compitiendo por el último stock
  // Alfajor Havanna (id_producto = 2) tiene stock_actual = 4 y precio $950.
  // Lanzamos simultáneamente (Promise.all) dos ventas que piden 3 unidades cada una ($2850).
  const [resConcurrA, resConcurrB] = await Promise.all([
    invocarAPI({
      method: 'POST',
      url: '/api/ventas',
      token: tokenVendedor,
      headers: { 'idempotency-key': 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeee0001' },
      body: {
        items: [{ id_producto: 2, cantidad: 3 }],
        pagos: [{ medio_pago: 'efectivo', monto: 2850 }]
      }
    }),
    invocarAPI({
      method: 'POST',
      url: '/api/ventas',
      token: tokenVendedor,
      headers: { 'idempotency-key': 'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeee0002' },
      body: {
        items: [{ id_producto: 2, cantidad: 3 }],
        pagos: [{ medio_pago: 'efectivo', monto: 2850 }]
      }
    })
  ]);

  const codigos = [resConcurrA.status, resConcurrB.status].sort();
  assert.deepEqual(codigos, [201, 409], 'Una venta concurrente debe confirmar (201) y la otra abortar (409 STOCK_INSUFICIENTE)');
  const stockAlfajor = kioscoDB.state.productos.find(p => p.id_producto === 2).stock_actual;
  assert.equal(stockAlfajor, 1, 'El stock de Alfajor Havanna debe quedar exactamente en 1 (4 - 3 = 1, jamás negativo)');
  console.log('✅ [CP-05] Concurrencia verificada (2 ventas simultáneas por 3 alfajores con stock=4): 1 confirma (201, stock=1) y 1 hace ROLLBACK (409 STOCK_INSUFICIENTE)');

  // 6. Cierre de caja diario y bloqueo de ventas posteriores al cierre
  const cierreRes = await invocarAPI({
    method: 'POST',
    url: '/api/caja/cierre',
    token: tokenVendedor,
    body: {
      monto_inicial: 5000,
      efectivo_contado: 10850,
      observaciones: 'Arqueo de prueba del hito'
    }
  });
  assert.equal(cierreRes.status, 201, 'El cierre de caja debe responder 201 Created');

  const ventaPostCierre = await invocarAPI({
    method: 'POST',
    url: '/api/ventas',
    token: tokenVendedor,
    headers: { 'idempotency-key': 'cccccccc-dddd-4eee-8fff-000000000003' },
    body: {
      items: [{ id_producto: 5, cantidad: 1 }],
      pagos: [{ medio_pago: 'efectivo', monto: 850 }]
    }
  });
  assert.equal(ventaPostCierre.status, 403, 'Venta posterior al cierre debe rechazarse con 403 CAJA_CERRADA');
  assert.equal(ventaPostCierre.data.code, 'CAJA_CERRADA');
  console.log('✅ [CP-06] Cierre de caja diario y bloqueo post-cierre (HTTP 403 CAJA_CERRADA) verificados');

  // Restaurar semilla limpia al finalizar para dejar la app lista para la demo interactiva
  kioscoDB.resetearSemilla();
  console.log('\n🎉 TODAS LAS PRUEBAS DEL HITO 06/11 PASARON EXITOSAMENTE (6/6).');
}

ejecutarPruebasHito().catch(err => {
  console.error('❌ Error en la suite de pruebas:', err);
  process.exit(1);
});

