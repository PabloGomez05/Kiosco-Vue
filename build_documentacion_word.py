import os
import docx
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

doc = Document()

# Set standard page margins (2.5 cm)
for section in doc.sections:
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)
    section.different_first_page_header_footer = False

    # Add page number in footer
    footer = section.footer
    f_p = footer.paragraphs[0]
    f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    f_run = f_p.add_run("Sistema de Gestión e Inventario para Kiosco · v2.1 · Programación II · Página ")
    f_run.font.name = "Calibri"
    f_run.font.size = Pt(9)
    f_run.font.color.rgb = RGBColor(148, 163, 184)
    f_p_xml = f_p._p
    fldSimple = parse_xml(r'<w:fldSimple %s w:instr="PAGE"/>' % nsdecls('w'))
    f_p_xml.append(fldSimple)

# Colors
C_NAVY = RGBColor(15, 23, 42)      # #0F172A
C_BLUE = RGBColor(30, 64, 175)     # #1E40AF
C_SLATE = RGBColor(51, 65, 85)     # #334155
C_BODY = RGBColor(30, 41, 59)      # #1E293B
C_MUTED = RGBColor(100, 116, 139)  # #64748B
HEX_HEADER_BG = "1E293B"           # Slate 800
HEX_ZEBRA = "F8FAFC"               # Slate 50
HEX_BORDER = "CBD5E1"

# Normal Style
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(10.5)
font.color.rgb = C_BODY
style.paragraph_format.line_spacing = 1.15
style.paragraph_format.space_after = Pt(4)

def set_cell_bg(cell, hex_color):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_borders(cell, top=None, bottom=None, left=None, right=None):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = parse_xml(f'<w:tcBorders {nsdecls("w")}/>')
    for b_name, b_val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        if b_val:
            node = parse_xml(f'<w:{b_name} {nsdecls("w")} w:val="{b_val.get("val","single")}" w:sz="{b_val.get("sz","4")}" w:space="0" w:color="{b_val.get("color", HEX_BORDER)}"/>')
            tcBorders.append(node)
        else:
            node = parse_xml(f'<w:{b_name} {nsdecls("w")} w:val="none"/>')
            tcBorders.append(node)
    tcPr.append(tcBorders)

def set_cell_margins(cell, top=100, bottom=100, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def add_title(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(23)
    run.bold = True
    run.font.color.rgb = C_NAVY
    return p

def add_subtitle(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(12.5)
    run.font.color.rgb = C_BLUE
    return p

def add_meta_box(metadata):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_bg(cell, "F1F5F9")
    set_cell_margins(cell, 140, 140, 220, 220)
    set_cell_borders(cell, left={"val": "single", "sz": "24", "color": "1E40AF"},
                          top={"val": "single", "sz": "4", "color": HEX_BORDER},
                          bottom={"val": "single", "sz": "4", "color": HEX_BORDER},
                          right={"val": "single", "sz": "4", "color": HEX_BORDER})
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.2
    for idx, (label, val) in enumerate(metadata):
        r1 = p.add_run(f"{label}: ")
        r1.bold = True
        r1.font.size = Pt(10)
        r1.font.color.rgb = C_NAVY
        suffix = "\n" if idx < len(metadata) - 1 else ""
        r2 = p.add_run(f"{val}{suffix}")
        r2.font.size = Pt(10)
        r2.font.color.rgb = C_SLATE
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(15.5)
    run.bold = True
    run.font.color.rgb = C_NAVY
    return p

def add_h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(11)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(12.5)
    run.bold = True
    run.font.color.rgb = C_BLUE
    return p

def add_h3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Calibri'
    run.font.size = Pt(11)
    run.bold = True
    run.font.color.rgb = C_SLATE
    return p

def add_p(text, bold_prefix=None, italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(5)
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.color.rgb = C_NAVY
    run = p.add_run(text)
    run.italic = italic
    run.font.color.rgb = C_BODY
    return p

def add_bullet(text, bold_prefix=None, level=0):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.left_indent = Inches(0.25 * (level + 1))
    if bold_prefix:
        r_pre = p.add_run(bold_prefix)
        r_pre.bold = True
        r_pre.font.color.rgb = C_NAVY
    run = p.add_run(text)
    run.font.color.rgb = C_BODY
    return p

def add_callout(title, text, color="1E40AF", bg="EFF6FF"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_bg(cell, bg)
    set_cell_margins(cell, 110, 110, 170, 170)
    set_cell_borders(cell, left={"val": "single", "sz": "24", "color": color},
                          top={"val": "single", "sz": "4", "color": HEX_BORDER},
                          bottom={"val": "single", "sz": "4", "color": HEX_BORDER},
                          right={"val": "single", "sz": "4", "color": HEX_BORDER})
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    if title:
        r_t = p.add_run(f"📌 {title}\n")
        r_t.bold = True
        r_t.font.size = Pt(10)
        r_t.font.color.rgb = C_NAVY
    r_body = p.add_run(text)
    r_body.font.size = Pt(9.5)
    r_body.font.color.rgb = C_BODY
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def add_code_block(code_text):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_bg(cell, "F8FAFC")
    set_cell_margins(cell, 110, 110, 150, 150)
    set_cell_borders(cell, left={"val": "single", "sz": "12", "color": "94A3B8"},
                          top={"val": "single", "sz": "4", "color": HEX_BORDER},
                          bottom={"val": "single", "sz": "4", "color": HEX_BORDER},
                          right={"val": "single", "sz": "4", "color": HEX_BORDER})
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(code_text)
    run.font.name = 'Consolas'
    run.font.size = Pt(8.2)
    run.font.color.rgb = RGBColor(15, 23, 42)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)

def create_styled_table(headers, rows, col_widths=None):
    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    hdr_cells = tbl.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = h
        set_cell_bg(hdr_cells[i], HEX_HEADER_BG)
        set_cell_margins(hdr_cells[i], 100, 100, 120, 120)
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        for run in p.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(9.2)
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)

    for r_idx, row in enumerate(rows):
        row_cells = tbl.rows[r_idx + 1].cells
        bg_color = HEX_ZEBRA if (r_idx % 2 == 1) else "FFFFFF"
        for c_idx, val in enumerate(row):
            row_cells[c_idx].text = str(val)
            set_cell_bg(row_cells[c_idx], bg_color)
            set_cell_margins(row_cells[c_idx], 75, 75, 110, 110)
            set_cell_borders(row_cells[c_idx],
                             top={"val": "single", "sz": "4", "color": HEX_BORDER},
                             bottom={"val": "single", "sz": "4", "color": HEX_BORDER},
                             left={"val": "single", "sz": "4", "color": HEX_BORDER},
                             right={"val": "single", "sz": "4", "color": HEX_BORDER})
            p = row_cells[c_idx].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.05
            for run in p.runs:
                run.font.name = 'Calibri'
                run.font.size = Pt(8.8)
                run.font.color.rgb = C_BODY

    if col_widths:
        for r in tbl.rows:
            for c_idx, w in enumerate(col_widths):
                r.cells[c_idx].width = Inches(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(5)
    return tbl

print("Construyendo documento oficial v2.1...")

# ==============================================================================
# PORTADA Y METADATOS
# ==============================================================================
add_title("Sistema de Gestión e Inventario para Kiosco")
add_subtitle("Documentación Técnica Oficial v2.1 · Arquitectura, DER en 3FN, DDL, Concurrencia, API OpenAPI y Trazabilidad")

meta = [
    ("Materia", "Programación II"),
    ("Carrera", "Tecnicatura Superior en Desarrollo de Software"),
    ("Modalidad", "Proyecto Integrador Individual"),
    ("Desarrollador", "Pablo (Trabajo individual)"),
    ("Docente a Cargo", "José Olivera"),
    ("Versión del Documento", "2.1 (Actualización para Hito del 06/11 y Entrega Final del 27/11)"),
    ("Fecha de Actualización", "02 de noviembre de 2026")
]
add_meta_box(meta)

# ==============================================================================
# CONTROL DE VERSIONES E ÍNDICE GENERAL
# ==============================================================================
add_h2("Control de Versiones del Documento")
ver_headers = ["Versión", "Fecha", "Autor", "Resumen de Cambios Realizados"]
ver_rows = [
    ["1.0", "15/10/2026", "Pablo", "Propuesta inicial del proyecto: problema, roles, 5 funcionalidades core, stack, modelo preliminar de 6 entidades y alcance MVP."],
    ["2.0", "22/10/2026", "Pablo", "Respuesta a la 1.ª devolución docente: incorporación de cierres_caja y movimientos_stock, precio histórico, baja lógica, reglas de negocio y plan individual."],
    ["2.1", "02/11/2026", "Pablo", "Respuesta a la 2.ª devolución docente (hito 06/11): matriz de trazabilidad, desacoplamiento de pagos_venta e historial_precios (10 entidades en 3FN), índices explícitos, scripts de semillas/migraciones/concurrencia, idempotencia y especificación OpenAPI 3.0."]
]
create_styled_table(ver_headers, ver_rows, [0.7, 1.0, 0.8, 4.0])

add_h2("Índice General de Contenidos")
idx_headers = ["Sección", "Título de la Sección", "Archivos y Artefactos Relacionados"]
idx_rows = [
    ["Sección 0", "Matriz de Trazabilidad (Observación → Cambio → Evidencia)", "Documentación_Proyecto_Kiosco.docx"],
    ["Sección 1", "Problema a Resolver y Visión General", "README.md"],
    ["Sección 2", "Usuarios, Roles y Matriz Rol – Endpoint – Acción – Prueba 403", "docs/openapi.yaml"],
    ["Sección 3", "Alcance del Proyecto, Priorización MoSCoW Refinada y Fuera de Alcance", "Documentación_Proyecto_Kiosco.docx"],
    ["Sección 4", "Stack Tecnológico Justificado y Aclaración de Base Previa vs. Nuevo", "src/App.vue, src/components/*"],
    ["Sección 5", "Modelo de Datos v2.1 (10 Entidades en 3FN), DER, Diccionario y DDL SQL", "database/schema.sql, database/er_diagram_completo.png"],
    ["Sección 6", "Reglas de Negocio, Transaccionalidad ACID y Prueba de Concurrencia", "database/pruebas/concurrencia_ventas.sql"],
    ["Sección 7", "Seguridad del Servidor (JWT, Middlewares por Endpoint y Prepared Statements)", "middlewares/auth.js (especificación)"],
    ["Sección 8", "Especificación API REST (OpenAPI 3.0, Errores Uniformes, Paginación e Idempotencia)", "docs/openapi.yaml"],
    ["Sección 9", "Historias de Usuario con Criterios de Aceptación (Gherkin)", "Documentación_Proyecto_Kiosco.docx"],
    ["Sección 10", "Estrategia de Pruebas (Funcionales, Seguridad 403 y Concurrencia)", "database/pruebas/concurrencia_ventas.sql"],
    ["Sección 11", "Requisitos No Funcionales (RNF)", "Documentación_Proyecto_Kiosco.docx"],
    ["Sección 12", "Cronograma Actualizado (Hito de Avance 06/11 y Entrega Final 27/11)", "Documentación_Proyecto_Kiosco.docx"],
    ["Sección 13", "Mockup de Interfaz Gráfica del Punto de Venta", "Documentación_Proyecto_Kiosco.docx"]
]
create_styled_table(idx_headers, idx_rows, [0.9, 3.6, 2.0])

# ==============================================================================
# 0. MATRIZ DE TRAZABILIDAD DE OBSERVACIONES DOCENTES
# ==============================================================================
add_h1("0. Matriz de Trazabilidad: Observación Recibida → Cambio Realizado → Evidencia")
add_p("Cumpliendo con la recomendación de la segunda devolución docente, la siguiente matriz vincula cada observación "
      "recibida con la decisión técnica adoptada y la evidencia concreta dentro del repositorio y de este documento:")

traza_headers = ["Ref.", "Observación Recibida del Docente", "Cambio Técnico Realizado", "Evidencia (Sección / Archivo)"]
traza_rows = [
    ["1.ª Dev.\nObs. 2a",
     "Falta entidad cierres_caja, mecanismo de reposición (movimientos_stock), precio_unitario en detalle, stock_minimo, estados de venta, explicación N:M y baja lógica (activo).",
     "Se modelaron las tablas cierres_caja y movimientos_stock; se congeló precio_unitario en detalle_ventas; se agregó activo en todas las tablas maestras y se explicitó la N:M.",
     "Secciones 5.1, 5.2 y 5.3\ndatabase/schema.sql"],
    ["1.ª Dev.\nObs. 2e",
     "Aclarar qué significa 'base ya desarrollada' en el frontend: qué existía, quién lo hizo y qué es nuevo.",
     "Se incorporó la declaración de autoría individual y el cuadro comparativo 'Estado Previo (Prácticas) vs. Desarrollo Nuevo (Cursada)'.",
     "Sección 4.1\nsrc/App.vue"],
    ["2.ª Dev.\nDER",
     "Verificar que no haya duplicación entre Venta, VentaDetalle y Pago; si una venta admite varios medios de pago, modelarlo como entidad asociativa. Separar stock, precios históricos y datos del producto.",
     "• Se eliminó medio_pago de ventas y se creó la entidad asociativa pagos_venta (admite 1 o varios medios de pago por ticket sin duplicar cabecera ni renglones).\n• Se creó historial_precios para separar la vigencia histórica de precios de los datos actuales del producto.",
     "Secciones 5.1 y 5.2\ndatabase/er_diagram_completo.png\ndatabase/schema.sql"],
    ["2.ª Dev.\nDDL",
     "Usar DECIMAL para montos, CHECK para cantidades y stock no negativo, ON DELETE RESTRICT, índices en FKs y fechas, utf8mb4, script de creación, migraciones y datos semilla.",
     "• Todos los importes usan DECIMAL(12,2).\n• CHECK en precios, cantidades, stock >= 0 y aritmética de movimientos.\n• Índices explícitos idx_* en todas las FKs y columnas fecha/fecha_hora.\n• Se separaron schema.sql, seeds/datos_demo.sql y migrations/001_*.sql.",
     "Sección 5.3 y 5.4\ndatabase/schema.sql\ndatabase/seeds/datos_demo.sql\ndatabase/migrations/"],
    ["2.ª Dev.\nTransacc.",
     "Documentar y probar el flujo de venta con BEGIN, bloqueo/actualización atómica de stock, inserción de venta y detalle, y COMMIT/ROLLBACK. Probar dos ventas concurrentes para demostrar que no hay stock negativo.",
     "Se documentó la transacción completa con SELECT ... FOR UPDATE (ordenado por id_producto para evitar deadlocks) y se incluyó el script reproducible de 2 sesiones concurrentes compitiendo por el último stock.",
     "Sección 6.2 y Sección 10\ndatabase/pruebas/concurrencia_ventas.sql"],
    ["2.ª Dev.\nPermisos",
     "Que el middleware valide en servidor por endpoint, no solo en el frontend. Agregar pruebas de respuesta 403 y una matriz rol–endpoint–acción.",
     "Se construyó la Matriz Rol–Endpoint–Acción con el resultado exacto para Anónimo (401), Vendedor (200/201 o 403) y Admin, más casos de prueba de rechazo 403.",
     "Sección 2.1 y Sección 7\ndocs/openapi.yaml"],
    ["2.ª Dev.\nAPI REST",
     "Sumar OpenAPI/Swagger, errores uniformes, validaciones, paginación e idempotencia en la creación de ventas.",
     "• Se creó la especificación completa en docs/openapi.yaml.\n• Esquema uniforme ErrorResponse.\n• Paginación (page, limit, meta).\n• Header Idempotency-Key + columna UNIQUE idempotency_key CHAR(36) en ventas.",
     "Sección 8\ndocs/openapi.yaml\ndatabase/schema.sql"],
    ["2.ª Dev.\nMoSCoW",
     "Acotar el MVP a login, productos/stock, venta transaccional, cierre diario y permisos. Reportes avanzados, exportaciones o UI muy pulida como Should/Could.",
     "Se reordenó la matriz MoSCoW concentrando el Must Have exclusivamente en los 5 pilares del núcleo transaccional y pasando reportes/CSV a Should/Could.",
     "Sección 3.2\nSección 12 (Hito 06/11)"]
]
create_styled_table(traza_headers, traza_rows, [0.7, 2.0, 2.3, 1.5])

# ==============================================================================
# 1. PROBLEMA A RESOLVER Y OBJETIVOS
# ==============================================================================
add_h1("1. Problema a Resolver y Visión General")
add_p("Los kioscos y pequeños comercios barriales operan habitualmente bajo esquemas de gestión manuales y descentralizados: "
      "anotaciones en cuadernos, planillas sueltas o memoria del personal de turno. Esta modalidad genera cuatro problemáticas críticas:")

add_bullet("Se desconoce la disponibilidad real de mercadería hasta que el cliente solicita el producto en mostrador, ocasionando pérdidas de ventas.", "Quiebres de stock no detectados: ")
add_bullet("Al coexistir pagos en efectivo, transferencias/QR y tarjetas, el cierre de turno manual es propenso a diferencias de caja y falta de responsabilidad individual.", "Falta de trazabilidad en el arqueo diario: ")
add_bullet("Cuando cambia el precio de un artículo, modificarlo sin historial ni congelamiento en el detalle de venta altera los importes históricos facturados.", "Distorsión de precios históricos: ")
add_bullet("El stock baja con las ventas y sube con entregas de proveedores, pero sin una bitácora de movimientos es imposible auditar faltantes o ajustes.", "Ausencia de auditoría de movimientos: ")

add_p("El sistema propuesto digitaliza la operación diaria de punta a punta: catálogo con baja lógica y vigencia de precios, "
      "ingreso y ajuste auditado de stock, punto de venta transaccional con soporte de pagos mixtos y arqueo diario inmutable por vendedor.")

# ==============================================================================
# 2. USUARIOS, ROLES Y MATRIZ ROL – ENDPOINT – ACCIÓN – PRUEBA 403
# ==============================================================================
add_h1("2. Usuarios, Roles y Matriz Rol – Endpoint – Acción")
add_p("El sistema implementa Control de Acceso Basado en Roles (RBAC) validado obligatoriamente en el servidor mediante "
      "los middlewares autenticarToken (verifica firma y expiración JWT de 1 hora) y autorizarRol (verifica el rol incluido en el payload):")

add_bullet("Dueño o responsable del kiosco. Tiene acceso completo al ABM de catálogo (productos, categorías, proveedores), ajustes manuales de inventario, anulación de ventas, visualización de todos los cierres de caja, reportes y gestión de usuarios.", "Rol Administrador (admin): ")
add_bullet("Operador de mostrador. Su alcance se centra en consultar el catálogo activo, registrar ventas transaccionales, registrar ingresos de mercadería por reposición, consultar las ventas de su turno y ejecutar su propio cierre de caja diario.", "Rol Vendedor / Cajero (vendedor): ")

add_h2("2.1 Matriz Rol – Endpoint – Acción y Verificación de Respuesta 403")
rbac_headers = ["Método y Endpoint", "Acción de Negocio", "Middleware en Servidor", "Anónimo", "Rol Vendedor", "Rol Admin"]
rbac_rows = [
    ["POST /api/auth/login", "Iniciar sesión y obtener JWT (1h)", "Público (rate-limited)", "200 OK", "200 OK", "200 OK"],
    ["GET /api/productos", "Listar catálogo paginado y stock", "autenticarToken", "401 Unauth.", "200 OK (solo activos)", "200 OK (todos)"],
    ["POST /api/productos", "Alta de nuevo producto y precio", "autenticarToken + autorizarRol(['admin'])", "401 Unauth.", "403 Forbidden", "201 Created"],
    ["PUT /api/productos/:id", "Modificar producto / actualizar precio", "autenticarToken + autorizarRol(['admin'])", "401 Unauth.", "403 Forbidden", "200 OK"],
    ["DELETE /api/productos/:id", "Baja lógica (activo = FALSE)", "autenticarToken + autorizarRol(['admin'])", "401 Unauth.", "403 Forbidden", "200 OK"],
    ["GET /api/stock/movimientos", "Consultar bitácora de stock", "autenticarToken", "401 Unauth.", "200 OK", "200 OK"],
    ["POST /api/stock/movimientos", "Registrar reposición (tipo=ingreso)", "autenticarToken", "401 Unauth.", "201 Created", "201 Created"],
    ["POST /api/stock/movimientos", "Ajuste positivo/negativo de stock", "autenticarToken + autorizarRol(['admin'])", "401 Unauth.", "403 Forbidden", "201 Created"],
    ["POST /api/ventas", "Confirmar venta transaccional ACID", "autenticarToken + cajaAbierta", "401 Unauth.", "201 Created", "201 Created"],
    ["GET /api/ventas", "Listar historial paginado de ventas", "autenticarToken (filtro por rol)", "401 Unauth.", "200 OK (propias)", "200 OK (todas)"],
    ["POST /api/ventas/:id/anular", "Anular venta y restituir stock", "autenticarToken + autorizarRol(['admin'])", "401 Unauth.", "403 Forbidden", "200 OK"],
    ["GET /api/caja/estado", "Consultar acumulados del día actual", "autenticarToken", "401 Unauth.", "200 OK (propia)", "200 OK"],
    ["POST /api/caja/cierre", "Ejecutar arqueo y cierre diario", "autenticarToken", "401 Unauth.", "201 Created (propia)", "201 Created"],
    ["GET /api/reportes/resumen", "Métricas por período (día/sem/mes)", "autenticarToken + autorizarRol(['admin'])", "401 Unauth.", "403 Forbidden", "200 OK"],
    ["GET /api/reportes/export-csv", "Descargar reporte en archivo CSV", "autenticarToken + autorizarRol(['admin'])", "401 Unauth.", "403 Forbidden", "200 OK"]
]
create_styled_table(rbac_headers, rbac_rows, [1.5, 1.5, 1.5, 0.65, 0.7, 0.65])

# ==============================================================================
# 3. ALCANCE, PRIORIZACIÓN MOSCOW REFINADA Y FUERA DE ALCANCE
# ==============================================================================
add_h1("3. Alcance del Proyecto y Matriz MoSCoW Refinada")
add_p("Atendiendo a la recomendación docente ('un MVP sólido, transaccional y bien documentado vale más que un sistema más amplio pero frágil'), "
      "se acotó estrictamente el núcleo imprescindible (Must Have) a los cinco pilares transaccionales y de seguridad:")

moscow_headers = ["Prioridad MoSCoW", "Alcance Acotado y Módulos Incluidos", "Criterio de Entrega (Hito 06/11 vs. Final 27/11)"]
moscow_rows = [
    ["1. MUST HAVE\n(Núcleo Indispensable del MVP)",
     "1. Login y Permisos en Servidor: JWT (1h), bcrypt y middlewares autenticarToken / autorizarRol con respuestas 401/403.\n"
     "2. Productos y Stock: ABM con baja lógica (activo), stock_actual, stock_minimo y bitácora movimientos_stock.\n"
     "3. Venta Transaccional ACID: Carrito POS con bloqueo SELECT ... FOR UPDATE, idempotencia, precio congelado y pagos_venta.\n"
     "4. Cierre Diario de Caja: Arqueo por vendedor y fecha (UNIQUE) con desglose por medio de pago y bloqueo post-cierre.",
     "Innegociable. La base de datos y la demo mínima del flujo de venta con descuento de stock se presentan en el Hito del 06/11; el cierre y pulido integral se entregan el 27/11."],
    ["2. SHOULD HAVE\n(Segundo Nivel - Deseable)",
     "• Alertas visuales de stock crítico y filtros rápidos en el catálogo.\n"
     "• Historial de precios (historial_precios) automático ante cada cambio de lista.\n"
     "• Anulación de venta confirmada (solo rol admin) con restitución transaccional de stock.",
     "El modelo de datos ya lo soporta al 100% en database/schema.sql. Su interfaz de usuario se completa para la entrega del 27/11."],
    ["3. COULD HAVE\n(Tercer Nivel - Opcional / Recortable)",
     "• Panel de reportes analíticos avanzados por período (día, semana, mes).\n"
     "• Exportación de listados y reportes a archivo plano CSV.\n"
     "• Pulido estético avanzado de la interfaz de usuario.",
     "Módulos no críticos para la integridad transaccional. Solo se abordan una vez verificado y probado el 100% del Must Have."],
    ["4. WON'T HAVE\n(Fuera de Alcance del MVP)",
     "• Integración con pasarelas de pago reales (Mercado Pago API, Posnet).\n"
     "• Emisión de factura electrónica fiscal (AFIP / ARCA).\n"
     "• Aplicación móvil nativa.\n"
     "• Órdenes de compra automáticas a proveedores.\n"
     "• Lector físico de código de barras / hardware externo.\n"
     "• Operación multilocal o multisucursal.",
     "Excluido explícitamente para preservar el foco académico en la arquitectura de tres capas, seguridad e integridad de datos."]
]
create_styled_table(moscow_headers, moscow_rows, [1.5, 3.0, 2.0])

# ==============================================================================
# 4. STACK TECNOLÓGICO Y ACLARACIÓN DE BASE DESARROLLADA
# ==============================================================================
add_h1("4. Stack Tecnológico Justificado y Base Previa vs. Nuevo")

stack_headers = ["Capa", "Tecnología", "Justificación Técnica"]
stack_rows = [
    ["Frontend", "Vue.js 3 (Composition API, <script setup>), Vite, Vue Router",
     "Reactividad declarativa, componentes modulares y navegación protegida por rol en el cliente."],
    ["Backend", "Node.js + Express + mysql2/promise",
     "API REST estructurada en capas (rutas, middlewares, controladores, servicios) con soporte nativo de pool de conexiones y transacciones explícitas."],
    ["Base de Datos", "MySQL 8.0 (Motor InnoDB, utf8mb4)",
     "Cumplimiento ACID, bloqueo pesimista de fila (SELECT ... FOR UPDATE), restricciones CHECK nativas, columnas generadas e integridad referencial ON DELETE RESTRICT."],
    ["Seguridad", "JWT (jsonwebtoken) + bcrypt",
     "Autenticación stateless con expiración de 1 hora y hash irreversible de contraseñas (10 salt rounds)."],
    ["Contrato API", "OpenAPI 3.0.3 (Swagger) + Axios",
     "Especificación formal documentada en docs/openapi.yaml con esquemas de validación, paginación, idempotencia y errores uniformes."]
]
create_styled_table(stack_headers, stack_rows, [1.3, 2.2, 3.0])

add_h2("4.1 Aclaración sobre la 'Base ya desarrollada' en Frontend (Obs. 2e)")
add_callout("Declaración de Autoría y Delimitación",
    "El prototipo existente al inicio en la carpeta src/ (App.vue, ProductoForm.vue y ProductoLista.vue) fue programado "
    "íntegramente por mí de manera individual durante las prácticas de la materia. Operaba únicamente con un arreglo en memoria "
    "volátil sin backend, sin base de datos, sin autenticación y sin módulo de ventas.")

prev_headers = ["Componente / Capa", "Estado Previo (Prácticas en Memoria)", "Desarrollo Nuevo en el Proyecto Integrador"]
prev_rows = [
    ["Datos y Persistencia", "Arreglo local hardcodeado en App.vue.", "Base MySQL 8.0 en 3FN (10 tablas, DDL, semillas, migraciones y transacciones ACID)."],
    ["Backend y Seguridad", "Inexistente.", "Servidor Express, middlewares JWT + RBAC, consultas preparadas y contrato OpenAPI 3.0."],
    ["Módulo de Ventas", "Inexistente.", "Carrito POS con bloqueo atómico de stock, idempotencia (UUID) y desglose en pagos_venta."],
    ["Stock y Caja", "Propiedad numérica sin trazabilidad.", "Bitácora inmutable movimientos_stock y arqueo diario cierres_caja por vendedor."]
]
create_styled_table(prev_headers, prev_rows, [1.6, 2.2, 2.7])

# ==============================================================================
# 5. MODELO DE DATOS v2.1 (10 ENTIDADES EN 3FN), DER Y DDL
# ==============================================================================
add_h1("5. Modelo de Datos v2.1 (10 Entidades en 3FN), DER y DDL")
add_p("En la versión 2.1 se perfeccionó el modelo relacional siguiendo las indicaciones del profesor para garantizar "
      "la separación estricta de responsabilidades y eliminar cualquier duplicación de datos:")

add_bullet("La cabecera ventas registra únicamente los datos propios del ticket (id_venta, idempotency_key, id_usuario, fecha_hora, total, estado). Los renglones viven en detalle_ventas y los cobros en la nueva entidad asociativa pagos_venta. De este modo, si un cliente abona una compra combinando efectivo y transferencia (pago mixto), se insertan dos filas en pagos_venta asociadas al mismo id_venta sin duplicar datos del ticket ni de sus productos.", "1. Separación limpia entre Venta, Detalle y Pago (pagos_venta): ")
add_bullet("La tabla productos conserva solo los atributos descriptivos y el estado vigente (precio_compra, precio_venta, stock_actual, stock_minimo). Cada cambio en la lista de precios se registra en historial_precios (con fecha vigente_desde y usuario responsable); el precio cobrado en cada ticket queda congelado en detalle_ventas.precio_unitario; y cada variación de unidades queda respaldada en movimientos_stock.", "2. Separación entre Producto, Precios Históricos y Stock: ")
add_bullet("En detalle_ventas, el campo subtotal se define como GENERATED ALWAYS AS (cantidad * precio_unitario) STORED. En cierres_caja, los campos total_ventas, efectivo_esperado y diferencia también son columnas generadas almacenadas, haciendo imposible por diseño que exista una discrepancia aritmética en una fila.", "3. Columnas Generadas Almacenadas (Invariantes en el Motor): ")
add_bullet("Se definieron índices B-Tree con nombre explícito en todas las claves foráneas y en las columnas temporales (idx_ventas_fecha, idx_ventas_usuario_fecha, idx_mov_producto_fecha, idx_mov_fecha, idx_cierres_fecha, idx_historial_producto_fecha) para optimizar los filtros por rango de fechas y los arqueos.", "4. Índices Explícitos en Claves Foráneas y Fechas: ")

add_h2("5.1 Diagrama Entidad-Relación Completo (DER v2.1)")
erd_img_path = r"c:\Users\pablo\Dropbox\Programación II\Vue.js\Proyecto final Vue\Kiosco-Vue\database\er_diagram_completo.png"
if os.path.exists(erd_img_path):
    doc.add_picture(erd_img_path, width=Inches(6.5))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_run = cap.add_run("Figura 1: Diagrama Entidad-Relación v2.1 con 10 entidades en 3FN, claves PK/FK, índices y cardinalidades")
    c_run.font.size = Pt(8.5)
    c_run.italic = True
    c_run.font.color.rgb = C_MUTED
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

add_h2("5.2 Resumen de las 10 Entidades y sus Restricciones Clave")
ent_headers = ["Entidad (Tabla)", "Clave Primaria", "Claves Foráneas (ON DELETE RESTRICT)", "Restricciones UNIQUE, CHECK e Índices"]
ent_rows = [
    ["1. usuarios", "id_usuario", "—", "UQ(usuario), UQ(email), ENUM rol('admin','vendedor')"],
    ["2. categorias", "id_categoria", "—", "UQ(nombre)"],
    ["3. proveedores", "id_proveedor", "—", "UQ(cuit), CHECK REGEXP formato XX-XXXXXXXX-X"],
    ["4. productos", "id_producto", "id_categoria -> categorias\nid_proveedor -> proveedores", "UQ(codigo), UQ(nombre), CHECK(precio_compra>=0, precio_venta>0, stock_actual>=0, stock_minimo>=0), IDX categoria/proveedor"],
    ["5. historial_precios", "id_historial", "id_producto -> productos\nid_usuario -> usuarios", "CHECK(precio_compra>=0, precio_venta>0), IDX(id_producto, vigente_desde)"],
    ["6. ventas", "id_venta", "id_usuario -> usuarios", "UQ(idempotency_key), CHECK(total>0), IDX(id_usuario, fecha_hora), IDX(fecha_hora)"],
    ["7. detalle_ventas", "id_detalle", "id_venta -> ventas\nid_producto -> productos", "UQ(id_venta, id_producto), CHECK(cantidad>0, precio_unitario>=0), subtotal GENERATED STORED"],
    ["8. pagos_venta", "id_pago", "id_venta -> ventas", "UQ(id_venta, medio_pago), CHECK(monto>0), ENUM medio_pago"],
    ["9. movimientos_stock", "id_movimiento", "id_producto -> productos\nid_usuario -> usuarios\nid_venta -> ventas (NULL)", "CHECK(cantidad>0, stock_ant>=0, stock_post>=0), CHECK aritmético exacto (+/-), IDX(id_producto, fecha_hora)"],
    ["10. cierres_caja", "id_cierre", "id_usuario -> usuarios", "UQ(id_usuario, fecha), CHECK montos>=0, columnas GENERATED: total_ventas, efectivo_esperado, diferencia"]
]
create_styled_table(ent_headers, ent_rows, [1.3, 1.0, 1.8, 2.4])

add_h2("5.3 Organización de Scripts SQL en el Repositorio")
add_bullet("Creación limpia e idempotente de las 10 tablas en MySQL 8.0 con utf8mb4, InnoDB, CHECKs, FKs e índices.", "database/schema.sql: ")
add_bullet("Datos semilla ejecutables dentro de una transacción (usuarios admin y vendedor, 5 categorías, 3 proveedores, 5 productos, historial de precios, ingresos iniciales de stock y 1 venta con pago mixto).", "database/seeds/datos_demo.sql: ")
add_bullet("Script de migración incremental que documenta el paso de la versión 2.0 a la 2.1.", "database/migrations/001_v2.0_a_v2.1_pagos_historial_indices.sql: ")
add_bullet("Transacción modelo con SELECT ... FOR UPDATE, prueba guiada de 2 ventas concurrentes y 3 consultas de auditoría de consistencia.", "database/pruebas/concurrencia_ventas.sql: ")

add_h2("5.4 Extracto Principal del DDL (database/schema.sql)")
ddl_excerpt = """CREATE DATABASE kiosk_db CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE kiosk_db;

CREATE TABLE productos (
  id_producto    INT           NOT NULL AUTO_INCREMENT,
  codigo         VARCHAR(50)   NULL,
  nombre         VARCHAR(100)  NOT NULL,
  id_categoria   INT           NOT NULL,
  id_proveedor   INT           NULL,
  precio_compra  DECIMAL(12,2) NOT NULL,
  precio_venta   DECIMAL(12,2) NOT NULL,
  stock_actual   INT           NOT NULL DEFAULT 0,
  stock_minimo   INT           NOT NULL DEFAULT 0,
  activo         BOOLEAN       NOT NULL DEFAULT TRUE,
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
) ENGINE=InnoDB;

CREATE TABLE ventas (
  id_venta        INT           NOT NULL AUTO_INCREMENT,
  idempotency_key CHAR(36)      NOT NULL,
  id_usuario      INT           NOT NULL,
  fecha_hora      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  total           DECIMAL(12,2) NOT NULL,
  estado          ENUM('confirmada','anulada') NOT NULL DEFAULT 'confirmada',
  observaciones   VARCHAR(255)  NULL,
  CONSTRAINT pk_ventas             PRIMARY KEY (id_venta),
  CONSTRAINT uq_ventas_idempotency UNIQUE (idempotency_key),
  CONSTRAINT chk_ventas_total      CHECK (total > 0),
  INDEX idx_ventas_usuario_fecha (id_usuario, fecha_hora),
  INDEX idx_ventas_fecha (fecha_hora),
  CONSTRAINT fk_ventas_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios (id_usuario) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE detalle_ventas (
  id_detalle      INT           NOT NULL AUTO_INCREMENT,
  id_venta        INT           NOT NULL,
  id_producto     INT           NOT NULL,
  cantidad        INT           NOT NULL,
  precio_unitario DECIMAL(12,2) NOT NULL,
  subtotal        DECIMAL(12,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED,
  CONSTRAINT pk_detalle_ventas     PRIMARY KEY (id_detalle),
  CONSTRAINT uq_detalle_venta_prod UNIQUE (id_venta, id_producto),
  CONSTRAINT chk_detalle_cantidad  CHECK (cantidad > 0),
  CONSTRAINT chk_detalle_precio    CHECK (precio_unitario >= 0),
  INDEX idx_detalle_producto (id_producto),
  CONSTRAINT fk_detalle_venta    FOREIGN KEY (id_venta)    REFERENCES ventas (id_venta)       ON DELETE RESTRICT,
  CONSTRAINT fk_detalle_producto FOREIGN KEY (id_producto) REFERENCES productos (id_producto) ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE pagos_venta (
  id_pago    INT           NOT NULL AUTO_INCREMENT,
  id_venta   INT           NOT NULL,
  medio_pago ENUM('efectivo','transferencia','debito','credito') NOT NULL,
  monto      DECIMAL(12,2) NOT NULL,
  referencia VARCHAR(100)  NULL,
  CONSTRAINT pk_pagos_venta       PRIMARY KEY (id_pago),
  CONSTRAINT uq_pagos_venta_medio UNIQUE (id_venta, medio_pago),
  CONSTRAINT chk_pagos_monto      CHECK (monto > 0),
  CONSTRAINT fk_pagos_venta FOREIGN KEY (id_venta) REFERENCES ventas (id_venta) ON DELETE RESTRICT
) ENGINE=InnoDB;"""
add_code_block(ddl_excerpt)

# ==============================================================================
# 6. REGLAS DE NEGOCIO, TRANSACCIONALIDAD Y CONCURRENCIA
# ==============================================================================
add_h1("6. Reglas de Negocio, Transaccionalidad ACID y Prueba de Concurrencia")

add_h2("6.1 Reglas de Negocio Fundamentales")
add_bullet("No se permite confirmar una venta si algún ítem solicita una cantidad mayor a stock_actual. Se valida preventivamente en Vue y autoritativamente en el servidor dentro de la transacción.", "RN-01 Stock Nunca Negativo: ")
add_bullet("Toda confirmación de venta inserta en ventas, detalle_ventas, pagos_venta, descuenta productos.stock_actual e inserta en movimientos_stock dentro de una única transacción InnoDB. Si falla cualquier paso, se ejecuta ROLLBACK total.", "RN-02 Atomicidad Total de la Venta: ")
add_bullet("Cada vendedor realiza un único cierre por fecha (UNIQUE(id_usuario, fecha)). Antes de registrar una venta se verifica que no exista un cierre del vendedor para CURDATE(); si existe, se rechaza con HTTP 403 CAJA_CERRADA.", "RN-03 Caja Diaria por Vendedor y Bloqueo Post-Cierre: ")
add_bullet("La suma de pagos_venta.monto para un id_venta debe coincidir exactamente con ventas.total (que a su vez coincide con SUM(detalle_ventas.subtotal)).", "RN-04 Cuadratura Exacta de Medios de Pago: ")
add_bullet("Ninguna entidad referenciada históricamente se elimina con DELETE físico; se desactiva con activo = FALSE y las FKs aplican ON DELETE RESTRICT.", "RN-05 Baja Lógica e Inmutabilidad Histórica: ")

add_h2("6.2 Flujo Transaccional de Venta y Control de Concurrencia (SELECT ... FOR UPDATE)")
add_p("Para evitar condiciones de carrera (race conditions) cuando dos vendedores intentan vender simultáneamente las últimas unidades "
      "de un mismo artículo, el servicio de ventas utiliza bloqueo pesimista de fila en InnoDB:")

tx_code = """// Servicio transaccional en Node.js + Express (mysql2/promise)
export async function registrarVentaTransaccional(pool, { idempotencyKey, idUsuario, items, pagos, observaciones }) {
  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction(); // START TRANSACTION

    // 1. Idempotencia: verificar si la clave UUID ya fue procesada previamente
    const [previa] = await conn.execute('SELECT id_venta FROM ventas WHERE idempotency_key = ?', [idempotencyKey]);
    if (previa.length > 0) {
      await conn.rollback();
      return { idempotente: true, id_venta: previa[0].id_venta };
    }

    // 2. Verificar que la caja del día del vendedor siga abierta
    const [cierre] = await conn.execute(
      'SELECT id_cierre FROM cierres_caja WHERE id_usuario = ? AND fecha = CURDATE()',
      [idUsuario]
    );
    if (cierre.length > 0) {
      throw { status: 403, code: 'CAJA_CERRADA', message: 'La caja del día ya fue cerrada para este usuario.' };
    }

    // 3. Bloquear las filas de productos en orden ascendente de ID (previene deadlocks)
    const idsOrdenados = [...new Set(items.map(i => i.id_producto))].sort((a, b) => a - b);
    const placeholders = idsOrdenados.map(() => '?').join(',');
    const [productosDB] = await conn.execute(
      `SELECT id_producto, nombre, precio_venta, stock_actual, activo
         FROM productos
        WHERE id_producto IN (${placeholders})
        ORDER BY id_producto
          FOR UPDATE`,
      idsOrdenados
    );

    // 4. Validar stock disponible y calcular total con el precio vigente de la BD
    let totalCalculado = 0;
    const mapProd = new Map(productosDB.map(p => [p.id_producto, p]));
    for (const item of items) {
      const prod = mapProd.get(item.id_producto);
      if (!prod || !prod.activo) {
        throw { status: 404, code: 'PRODUCTO_NO_DISPONIBLE', message: `Producto ID ${item.id_producto} inexistente o inactivo.` };
      }
      if (prod.stock_actual < item.cantidad) {
        throw {
          status: 409,
          code: 'STOCK_INSUFICIENTE',
          message: `Stock insuficiente para '${prod.nombre}' (disponible: ${prod.stock_actual}, solicitado: ${item.cantidad}).`
        };
      }
      totalCalculado += Number(prod.precio_venta) * item.cantidad;
    }

    // 5. Validar que la suma de pagos coincida exactamente con el total calculado
    const sumaPagos = pagos.reduce((acc, p) => acc + Number(p.monto), 0);
    if (Math.abs(sumaPagos - totalCalculado) > 0.001) {
      throw { status: 400, code: 'MONTO_PAGO_INVALIDO', message: 'La suma de los medios de pago no coincide con el total.' };
    }

    // 6. Insertar cabecera de venta
    const [resVenta] = await conn.execute(
      'INSERT INTO ventas (idempotency_key, id_usuario, total, estado, observaciones) VALUES (?, ?, ?, "confirmada", ?)',
      [idempotencyKey, idUsuario, totalCalculado.toFixed(2), observaciones || null]
    );
    const idVenta = resVenta.insertId;

    // 7. Insertar detalle_ventas, descontar stock e insertar movimientos_stock
    for (const item of items) {
      const prod = mapProd.get(item.id_producto);
      const stockAnterior = prod.stock_actual;
      const stockPosterior = stockAnterior - item.cantidad;

      await conn.execute(
        'INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario) VALUES (?, ?, ?, ?)',
        [idVenta, item.id_producto, item.cantidad, prod.precio_venta]
      );
      await conn.execute(
        'UPDATE productos SET stock_actual = ? WHERE id_producto = ?',
        [stockPosterior, item.id_producto]
      );
      await conn.execute(
        `INSERT INTO movimientos_stock
         (id_producto, id_usuario, tipo, cantidad, stock_anterior, stock_posterior, id_venta, motivo)
         VALUES (?, ?, 'venta', ?, ?, ?, ?, ?)`,
        [item.id_producto, idUsuario, item.cantidad, stockAnterior, stockPosterior, idVenta, `Venta ticket #${idVenta}`]
      );
    }

    // 8. Insertar desglose de pagos en pagos_venta
    for (const pago of pagos) {
      await conn.execute(
        'INSERT INTO pagos_venta (id_venta, medio_pago, monto, referencia) VALUES (?, ?, ?, ?)',
        [idVenta, pago.medio_pago, Number(pago.monto).toFixed(2), pago.referencia || null]
      );
    }

    await conn.commit(); // COMMIT ATÓMICO
    return { idempotente: false, id_venta: idVenta, total: totalCalculado };
  } catch (err) {
    await conn.rollback(); // ROLLBACK TOTAL ANTE CUALQUIER FALLO
    throw err;
  } finally {
    conn.release();
  }
}"""
add_code_block(tx_code)

add_h2("6.3 Traza de la Prueba de Dos Ventas Concurrentes")
add_p("Escenario: El producto 'Alfajor Havanna' (id_producto = 2) tiene stock_actual = 2. Dos cajeros (Sesión A y Sesión B) "
      "envían simultáneamente una venta por 2 unidades cada uno:")

conc_headers = ["Instante", "Sesión A (Cajero 1 - Pide 2 unid.)", "Sesión B (Cajero 2 - Pide 2 unid.)", "Stock en BD y Estado del Lock InnoDB"]
conc_rows = [
    ["T1", "START TRANSACTION;\nSELECT stock_actual FROM productos WHERE id_producto = 2 FOR UPDATE;\n→ Lee stock_actual = 2.",
     "START TRANSACTION;",
     "stock_actual = 2.\nSesión A adquiere bloqueo exclusivo (X-Lock) sobre la fila id_producto = 2."],
    ["T2", "Inserta ventas, detalle_ventas, pagos_venta y ejecuta:\nUPDATE productos SET stock_actual = 0 WHERE id_producto = 2;",
     "SELECT stock_actual FROM productos WHERE id_producto = 2 FOR UPDATE;\n→ Queda en espera (WAIT) bloqueada por InnoDB.",
     "stock_actual = 0 (en la transacción A aún no confirmada). Sesión B espera liberación del X-Lock."],
    ["T3", "Inserta movimientos_stock (4 -> 2 -> 0) y ejecuta:\nCOMMIT;",
     "(Sigue en espera hasta el instante exacto del COMMIT de A).",
     "stock_actual = 0 confirmado en disco. Se libera el X-Lock de la fila."],
    ["T4", "Retorna HTTP 201 Created al Cajero 1.",
     "Se desbloquea el SELECT ... FOR UPDATE y retorna el valor actualizado: stock_actual = 0.\nComo 0 < 2 solicitados, ejecuta ROLLBACK y retorna HTTP 409 STOCK_INSUFICIENTE.",
     "stock_actual = 0 (jamás pasa a -2). Integridad preservada bajo concurrencia real."]
]
create_styled_table(conc_headers, conc_rows, [0.6, 2.1, 2.1, 1.7])

# ==============================================================================
# 7. SEGURIDAD DEL SERVIDOR
# ==============================================================================
add_h1("7. Seguridad en el Servidor (Autenticación, RBAC e Inyección SQL)")
add_bullet("El token JWT se firma con HS256 (JWT_SECRET en .env) y expira en 1 hora (expiresIn: '1h'). Incluye sub (id_usuario), usuario y rol.", "1. Autenticación JWT con Expiración Estricta: ")
add_bullet("Ningún endpoint confía en el estado del cliente Vue. El middleware autorizarRol(['admin']) devuelve HTTP 403 Forbidden con formato uniforme ante cualquier intento de escalación de privilegios.", "2. Validación de Rol por Endpoint en Servidor: ")
add_bullet("Todas las consultas usan exclusivamente parámetros posicionales (?) con mysql2/promise. Ningún dato de entrada se concatena en cadenas SQL.", "3. Prevención Total de Inyección SQL: ")

# ==============================================================================
# 8. ESPECIFICACIÓN DE LA API REST (OPENAPI 3.0, ERRORES, PAGINACIÓN E IDEMPOTENCIA)
# ==============================================================================
add_h1("8. Especificación de la API REST (OpenAPI 3.0 / Swagger)")
add_p("El contrato completo de la API se encuentra especificado en el archivo docs/openapi.yaml bajo el estándar OpenAPI 3.0.3. "
      "Incorpora cuatro mecanismos clave solicitados en la segunda devolución docente:")

add_h2("8.1 Contrato Uniforme de Errores (ErrorResponse)")
add_p("Cualquier error de validación (400), falta de token (401), permiso insuficiente (403), recurso no hallado (404), "
      "conflicto de negocio como stock insuficiente o caja cerrada (409) o fallo inesperado (500) retorna siempre la misma estructura JSON:")

err_json = """{
  "code": "STOCK_INSUFICIENTE",
  "message": "Stock insuficiente para 'Alfajor Havanna Chocolate 70g' (disponible: 2, solicitado: 3).",
  "details": [
    { "field": "items[0].cantidad", "issue": "Supera el stock_actual disponible (2)" }
  ],
  "timestamp": "2026-11-02T15:30:00.000Z",
  "path": "/api/ventas"
}"""
add_code_block(err_json)

add_h2("8.2 Paginación Estandarizada en Listados")
add_p("Los endpoints de colección (GET /api/productos, GET /api/ventas, GET /api/stock/movimientos) aceptan los parámetros "
      "de consulta page (por defecto 1) y limit (por defecto 20, máximo 100), devolviendo los resultados junto con el bloque meta "
      "(page, limit, total_items, total_pages).")

add_h2("8.3 Idempotencia en la Creación de Ventas")
add_p("El endpoint POST /api/ventas exige el encabezado HTTP Idempotency-Key con un UUID v4 generado por el frontend al iniciar el cobro. "
      "Este valor se almacena en la columna ventas.idempotency_key (con restricción UNIQUE). Si por microcorte de red o doble clic "
      "del cajero la petición se envía dos veces, el servidor detecta la clave existente y devuelve HTTP 200 OK con el ticket original "
      "sin volver a descontar el stock.")

# ==============================================================================
# 9. HISTORIAS DE USUARIO CON CRITERIOS DE ACEPTACIÓN
# ==============================================================================
add_h1("9. Historias de Usuario del Núcleo MVP")
hu_list = [
    ("HU-01: Inicio de Sesión y Bloqueo por Rol (403)",
     "Como usuario del sistema, quiero iniciar sesión con mis credenciales para operar según los permisos de mi rol.",
     "• Dado un usuario activo con credenciales válidas, Cuando envía POST /api/auth/login, Entonces recibe HTTP 200 con su JWT (vigencia 1h).\n"
     "• Dado un token con rol 'vendedor', Cuando intenta invocar POST /api/productos o GET /api/reportes/resumen, Entonces el middleware del servidor rechaza la petición con HTTP 403 Forbidden."),
    ("HU-02: Confirmación Transaccional de Venta con Descuento de Stock",
     "Como vendedor, quiero confirmar un carrito de venta indicando el/los medios de pago para descontar el stock de forma atómica.",
     "• Dado que la caja del día está abierta y todos los ítems tienen stock_actual >= cantidad, Cuando envía POST /api/ventas con Idempotency-Key, Entonces se insertan ventas, detalle_ventas, pagos_venta y movimientos_stock y se actualiza productos.stock_actual en una sola transacción.\n"
     "• Dado que algún producto no alcanza el stock solicitado, Cuando se procesa la solicitud, Entonces se ejecuta ROLLBACK total y se responde HTTP 409 STOCK_INSUFICIENTE."),
    ("HU-03: Reposición de Stock Auditada",
     "Como vendedor o administrador, quiero registrar el ingreso de mercadería recibida de un proveedor para incrementar el stock con trazabilidad.",
     "• Dado un producto activo y una cantidad > 0, Cuando envía POST /api/stock/movimientos con tipo='ingreso', Entonces stock_actual aumenta en esa cantidad y queda grabado stock_anterior y stock_posterior en movimientos_stock."),
    ("HU-04: Cierre Diario de Caja por Vendedor",
     "Como vendedor, quiero cerrar mi caja al finalizar mi turno para dejar asentado el arqueo por medio de pago.",
     "• Dado un vendedor sin cierre registrado en la fecha actual, Cuando confirma POST /api/caja/cierre con el efectivo contado, Entonces el sistema consolida los totales desde pagos_venta, calcula la diferencia y bloquea nuevas ventas del vendedor por el resto del día.")
]
for hu_t, hu_d, hu_c in hu_list:
    add_h2(hu_t)
    add_p(hu_d, bold_prefix="Narrativa: ")
    add_callout("Criterios de Aceptación", hu_c, color="059669", bg="ECFDF5")

# ==============================================================================
# 10. ESTRATEGIA DE PRUEBAS
# ==============================================================================
add_h1("10. Estrategia de Pruebas (Funcionales, Permisos 403 y Concurrencia)")
test_headers = ["ID", "Caso de Prueba", "Entrada / Procedimiento", "Resultado Esperado y Evidencia"]
test_rows = [
    ["CP-01", "Venta exitosa con pago mixto", "POST /api/ventas con 2 Coca-Colas + 1 Oreo ($4200: $2000 efectivo + $2200 transferencia).", "HTTP 201. Stock baja en 2 y 1. Se crean filas en ventas, detalle_ventas, pagos_venta y movimientos_stock."],
    ["CP-02", "Rechazo por stock insuficiente (Rollback)", "Producto con stock_actual = 2; se solicitan 3 unidades.", "HTTP 409 STOCK_INSUFICIENTE. Stock permanece en 2; no se crean filas en ventas."],
    ["CP-03", "Dos ventas concurrentes por el último stock", "2 sesiones ejecutan simultáneamente venta de 2 unidades cuando quedan 2 en stock.", "Sesión A confirma (HTTP 201, stock=0). Sesión B espera el lock y recibe HTTP 409 sin dejar stock negativo."],
    ["CP-04", "Idempotencia ante reintento de venta", "Enviar dos veces POST /api/ventas con el mismo header Idempotency-Key.", "La 1.ª responde 201 Created; la 2.ª responde 200 OK devolviendo el mismo id_venta sin descontar stock de nuevo."],
    ["CP-05", "Prueba de seguridad 403 en servidor", "Invocar POST /api/productos y DELETE /api/productos/1 con token de rol 'vendedor'.", "El middleware autorizarRol(['admin']) rechaza ambas peticiones con HTTP 403 Forbidden."],
    ["CP-06", "Bloqueo de venta posterior al cierre diario", "Ejecutar POST /api/caja/cierre y luego intentar POST /api/ventas con el mismo vendedor.", "HTTP 403 CAJA_CERRADA. La venta no se registra."]
]
create_styled_table(test_headers, test_rows, [0.6, 1.6, 2.1, 2.2])

# ==============================================================================
# 11. REQUISITOS NO FUNCIONALES (RNF)
# ==============================================================================
add_h1("11. Requisitos No Funcionales (RNF)")
add_bullet("Interfaz adaptable a pantallas de mostrador (desktop y tablet) con controles claros para operación rápida.", "RNF-01 Usabilidad y Diseño Responsive: ")
add_bullet("Tiempo de respuesta menor a 300 ms en lecturas paginadas gracias a los índices B-Tree en claves foráneas y fechas.", "RNF-02 Rendimiento: ")
add_bullet("Todas las respuestas de error cumplen el esquema ErrorResponse documentado en OpenAPI 3.0.", "RNF-03 Uniformidad de Errores: ")
add_bullet("Configuración externalizada en .env (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, JWT_SECRET, PORT).", "RNF-04 Portabilidad y Seguridad de Entorno: ")

# ==============================================================================
# 12. CRONOGRAMA ACTUALIZADO: HITO 06/11 Y ENTREGA FINAL 27/11
# ==============================================================================
add_h1("12. Cronograma Actualizado (Hito 06/11 y Entrega Final 27/11)")
add_p("De acuerdo con lo consensuado con el docente José Olivera, el plan de trabajo individual se organiza en torno "
      "al Hito de Avance del 06 de noviembre y la Entrega Final del 27 de noviembre:")

cron_headers = ["Etapa / Fecha", "Foco Principal", "Entregables Verificables"]
cron_rows = [
    ["Hito de Avance\n06/11/2026\n(No eliminatorio)",
     "Documentación v2.1 blindada + Base de datos ejecutable + Demo mínima del flujo de venta con descuento de stock.",
     "• Documentación Word v2.1 con matriz de trazabilidad.\n"
     "• DDL ejecutable en MySQL 8.0 (database/schema.sql + seeds + concurrencia).\n"
     "• DER final de 10 entidades (database/er_diagram_completo.png).\n"
     "• Especificación OpenAPI 3.0 (docs/openapi.yaml).\n"
     "• Demo funcional: backend Express + frontend Vue ejecutando una venta transaccional con descuento real de stock."],
    ["Sprint Intermedio\n07/11 al 16/11/2026",
     "Cierre de caja diario, reposición de stock y gestión completa de catálogo protegida por rol.",
     "• Pantalla y endpoint de reposición de stock (movimientos_stock).\n"
     "• Pantalla y endpoint de arqueo y cierre de caja diario (cierres_caja).\n"
     "• Pruebas automatizadas/manuales de rechazo HTTP 403 por rol."],
    ["Sprint de Cierre\n17/11 al 27/11/2026\n(Entrega Final)",
     "Integración final, pruebas de concurrencia y consistencia, reportes básicos y preparación de la defensa.",
     "• MVP completo probado de punta a punta.\n"
     "• Ejecución del script de verificación de consistencia sin discrepancias.\n"
     "• Repositorio final limpio y presentación para la defensa oral."]
]
create_styled_table(cron_headers, cron_rows, [1.4, 2.1, 3.0])

# ==============================================================================
# 13. MOCKUP DE INTERFAZ GRÁFICA
# ==============================================================================
add_h1("13. Interfaz Gráfica del Sistema (Mockup del Punto de Venta)")
add_p("A continuación se ilustra la maqueta visual del mostrador, integrando el catálogo con alertas de stock a la izquierda "
      "y el Carrito POS a la derecha:")

mockup_path = r"c:\Users\pablo\Dropbox\Programación II\Vue.js\Proyecto final Vue\Kiosco-Vue\docs\ui_mockup_pos.png"
if os.path.exists(mockup_path):
    doc.add_picture(mockup_path, width=Inches(6.5))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c_run = cap.add_run("Figura 2: Maqueta de la interfaz integrada de Inventario y Carrito de Compras (POS de Mostrador)")
    c_run.font.size = Pt(8.5)
    c_run.italic = True
    c_run.font.color.rgb = C_MUTED
    doc.add_paragraph().paragraph_format.space_after = Pt(6)

out_file = r"c:\Users\pablo\Dropbox\Programación II\Vue.js\Proyecto final Vue\Kiosco-Vue\Documentación_Proyecto_Kiosco.docx"
doc.save(out_file)
print(f"Documento v2.1 generado exitosamente en: {out_file}")
