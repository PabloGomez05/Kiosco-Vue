// =============================================================================
// server/index.js
// Servidor HTTP Backend (Puerto 3000) para la API REST del Kiosco
// Materia: Programación II · Docente: José Olivera · Autor: Pablo Gómez
// =============================================================================

import http from 'node:http';
import { handleApiRequest } from './app.js';

const PORT = Number(process.env.PORT || 3000);

export function crearServidorHTTP() {
  return http.createServer((req, res) => {
    if (req.url && req.url.startsWith('/api')) {
      return handleApiRequest(req, res);
    }
    res.statusCode = 200;
    res.setHeader('Content-Type', 'application/json; charset=utf-8');
    res.end(
      JSON.stringify({
        service: 'Kiosco-Vue API REST v2.1',
        openapi: '/docs/openapi.yaml',
        status: 'online'
      })
    );
  });
}

if (import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const server = crearServidorHTTP();
  server.listen(PORT, () => {
    console.log(`🚀 API REST Kiosco-Vue v2.1 escuchando en http://localhost:${PORT}/api`);
  });
}
