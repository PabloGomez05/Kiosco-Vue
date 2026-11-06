// =============================================================================
// middlewares/auth.js
// Autenticación Stateless con JWT (HS256, expiración 1 hora) y Control de Roles
// =============================================================================

import crypto from 'node:crypto';

const JWT_SECRET = process.env.JWT_SECRET || 'kiosco_jwt_secret_programacion_ii_2026';
const JWT_EXPIRES_IN_SECONDS = 3600; // 1 hora exacta

function base64UrlEncode(input) {
  const buf = Buffer.isBuffer(input) ? input : Buffer.from(String(input), 'utf8');
  return buf.toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

function base64UrlDecode(str) {
  let b64 = str.replace(/-/g, '+').replace(/_/g, '/');
  while (b64.length % 4 !== 0) b64 += '=';
  return Buffer.from(b64, 'base64').toString('utf8');
}

/**
 * Genera un token JWT firmado con HMAC-SHA256 (HS256) válido por 1 hora.
 */
export function firmarTokenJWT(usuario) {
  const ahora = Math.floor(Date.now() / 1000);
  const header = { alg: 'HS256', typ: 'JWT' };
  const payload = {
    sub: usuario.id_usuario,
    id_usuario: usuario.id_usuario,
    usuario: usuario.usuario,
    nombre_completo: usuario.nombre_completo,
    rol: usuario.rol,
    iat: ahora,
    exp: ahora + JWT_EXPIRES_IN_SECONDS
  };

  const encodedHeader = base64UrlEncode(JSON.stringify(header));
  const encodedPayload = base64UrlEncode(JSON.stringify(payload));
  const data = `${encodedHeader}.${encodedPayload}`;
  const signature = base64UrlEncode(
    crypto.createHmac('sha256', JWT_SECRET).update(data).digest()
  );

  return {
    token: `${data}.${signature}`,
    expires_in: JWT_EXPIRES_IN_SECONDS
  };
}

/**
 * Verifica la firma criptográfica y la vigencia temporal de un token JWT.
 */
export function verificarTokenJWT(token) {
  const partes = String(token || '').split('.');
  if (partes.length !== 3) {
    throw new Error('Formato de token JWT inválido.');
  }
  const [encodedHeader, encodedPayload, signature] = partes;
  const data = `${encodedHeader}.${encodedPayload}`;
  const expectedSig = base64UrlEncode(
    crypto.createHmac('sha256', JWT_SECRET).update(data).digest()
  );

  if (signature !== expectedSig) {
    throw new Error('Firma de token JWT inválida.');
  }

  const payload = JSON.parse(base64UrlDecode(encodedPayload));
  const ahora = Math.floor(Date.now() / 1000);
  if (!payload.exp || payload.exp < ahora) {
    throw new Error('El token JWT ha expirado (vigencia máxima: 1 hora).');
  }
  return payload;
}

/**
 * Construye una respuesta de error uniforme según el esquema ErrorResponse de OpenAPI 3.0.
 */
export function crearErrorUniforme(code, message, path, details = []) {
  return {
    code,
    message,
    details,
    timestamp: new Date().toISOString(),
    path
  };
}

/**
 * Middleware: valida que la petición incluya un header Authorization: Bearer <token> válido.
 */
export function autenticarToken(req) {
  const authHeader = req.headers['authorization'] || req.headers['Authorization'];
  const token = authHeader && authHeader.startsWith('Bearer ') ? authHeader.slice(7).trim() : null;

  if (!token) {
    return {
      ok: false,
      status: 401,
      body: crearErrorUniforme(
        'NO_AUTENTICADO',
        'Acceso denegado: no se suministró un token Bearer JWT.',
        req.url
      )
    };
  }

  try {
    const payload = verificarTokenJWT(token);
    req.user = payload;
    return { ok: true, user: payload };
  } catch (err) {
    return {
      ok: false,
      status: 401,
      body: crearErrorUniforme(
        'TOKEN_INVALIDO_O_EXPIRADO',
        err.message || 'Token inválido o expirado.',
        req.url
      )
    };
  }
}

/**
 * Middleware de autorización RBAC en servidor: verifica que el rol del token
 * pertenezca a la lista de roles permitidos para el endpoint.
 */
export function autorizarRol(req, rolesPermitidos) {
  if (!req.user || !rolesPermitidos.includes(req.user.rol)) {
    return {
      ok: false,
      status: 403,
      body: crearErrorUniforme(
        'ACCESO_PROHIBIDO_POR_ROL',
        `Acceso prohibido (HTTP 403): el rol '${req.user?.rol || 'anónimo'}' no tiene permisos para este endpoint. Se requiere: [${rolesPermitidos.join(', ')}].`,
        req.url,
        [{ field: 'rol', issue: `Rol actual '${req.user?.rol}' no autorizado` }]
      )
    };
  }
  return { ok: true };
}

