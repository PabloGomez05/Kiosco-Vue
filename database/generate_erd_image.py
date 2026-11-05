import os
from PIL import Image, ImageDraw, ImageFont

# Canvas size
WIDTH = 2250
HEIGHT = 1650
BG_COLOR = (248, 250, 252)  # Slate 50

img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
draw = ImageDraw.Draw(img)

# Fonts
font_title = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 32)
font_subtitle = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
font_tbl_header = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 19)
font_attr_name = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
font_attr_bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 14)
font_attr_type = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 13)
font_badge = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 11)
font_rel = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 13)

# Draw Title
draw.text((50, 30), "Diagrama Entidad-Relación Completo (DER v2.1) – Sistema Kiosco", fill=(15, 23, 42), font=font_title)
draw.text((50, 74), "10 Entidades en 3FN · Separación Producto / Historial Precios / Stock / Venta / Detalle / Pagos · MySQL 8.0 InnoDB", fill=(71, 85, 105), font=font_subtitle)

tables = {
    "CATEGORIAS": {
        "box": (50, 150, 360, 210),
        "header_color": (30, 41, 59),
        "fields": [
            ("id_categoria", "INT AUTO_INC", True, False),
            ("nombre", "VARCHAR(50) UQ", False, False),
            ("descripcion", "VARCHAR(255)", False, False),
            ("activo", "BOOLEAN DEF 1", False, False),
        ]
    },
    "PRODUCTOS": {
        "box": (520, 150, 450, 440),
        "header_color": (15, 76, 129),
        "fields": [
            ("id_producto", "INT AUTO_INC", True, False),
            ("codigo", "VARCHAR(50) UQ", False, False),
            ("nombre", "VARCHAR(100) UQ", False, False),
            ("descripcion", "VARCHAR(255)", False, False),
            ("id_categoria", "INT NOT NULL", False, True),
            ("id_proveedor", "INT NULL", False, True),
            ("precio_compra", "DECIMAL(12,2) >=0", False, False),
            ("precio_venta", "DECIMAL(12,2) >0", False, False),
            ("stock_actual", "INT CHECK >=0", False, False),
            ("stock_minimo", "INT CHECK >=0", False, False),
            ("activo", "BOOLEAN DEF 1", False, False),
            ("actualizado_en", "DATETIME", False, False),
        ]
    },
    "PROVEEDORES": {
        "box": (1100, 150, 410, 290),
        "header_color": (30, 41, 59),
        "fields": [
            ("id_proveedor", "INT AUTO_INC", True, False),
            ("razon_social", "VARCHAR(100)", False, False),
            ("cuit", "CHAR(13) UQ REGEXP", False, False),
            ("contacto", "VARCHAR(100)", False, False),
            ("telefono", "VARCHAR(30)", False, False),
            ("email", "VARCHAR(100)", False, False),
            ("activo", "BOOLEAN DEF 1", False, False),
        ]
    },
    "HISTORIAL_PRECIOS": {
        "box": (1640, 150, 460, 260),
        "header_color": (3, 105, 161),
        "fields": [
            ("id_historial", "INT AUTO_INC", True, False),
            ("id_producto", "INT NOT NULL", False, True),
            ("precio_compra", "DECIMAL(12,2) >=0", False, False),
            ("precio_venta", "DECIMAL(12,2) >0", False, False),
            ("vigente_desde", "DATETIME IDX", False, False),
            ("id_usuario", "INT NOT NULL", False, True),
        ]
    },
    "DETALLE_VENTAS": {
        "box": (520, 700, 450, 265),
        "header_color": (14, 116, 144),
        "fields": [
            ("id_detalle", "INT AUTO_INC", True, False),
            ("id_venta", "INT UQ(vta,prod)", False, True),
            ("id_producto", "INT UQ(vta,prod)", False, True),
            ("cantidad", "INT CHECK >0", False, False),
            ("precio_unitario", "DECIMAL(12,2) Hist.", False, False),
            ("subtotal", "DECIMAL(12,2) GEN", False, False),
        ]
    },
    "VENTAS": {
        "box": (1100, 620, 440, 300),
        "header_color": (16, 185, 129),
        "fields": [
            ("id_venta", "INT AUTO_INC", True, False),
            ("idempotency_key", "CHAR(36) UQ UUID", False, False),
            ("id_usuario", "INT NOT NULL", False, True),
            ("fecha_hora", "DATETIME IDX", False, False),
            ("total", "DECIMAL(12,2) >0", False, False),
            ("estado", "ENUM('confirmada','anulada')", False, False),
            ("observaciones", "VARCHAR(255)", False, False),
        ]
    },
    "USUARIOS": {
        "box": (1680, 560, 440, 320),
        "header_color": (71, 85, 105),
        "fields": [
            ("id_usuario", "INT AUTO_INC", True, False),
            ("nombre_completo", "VARCHAR(100)", False, False),
            ("usuario", "VARCHAR(50) UQ", False, False),
            ("email", "VARCHAR(100) UQ", False, False),
            ("password_hash", "VARCHAR(255) bcrypt", False, False),
            ("rol", "ENUM('admin','vendedor')", False, False),
            ("activo", "BOOLEAN DEF 1", False, False),
            ("creado_en", "DATETIME", False, False),
        ]
    },
    "MOVIMIENTOS_STOCK": {
        "box": (50, 1110, 450, 390),
        "header_color": (194, 65, 12),
        "fields": [
            ("id_movimiento", "INT AUTO_INC", True, False),
            ("id_producto", "INT NOT NULL IDX", False, True),
            ("id_usuario", "INT NOT NULL IDX", False, True),
            ("tipo", "ENUM('ingreso','venta','ajuste..')", False, False),
            ("cantidad", "INT CHECK >0", False, False),
            ("stock_anterior", "INT CHECK >=0", False, False),
            ("stock_posterior", "INT CHECK +/- cant", False, False),
            ("id_venta", "INT NULL", False, True),
            ("motivo", "VARCHAR(255)", False, False),
            ("fecha_hora", "DATETIME IDX", False, False),
        ]
    },
    "PAGOS_VENTA": {
        "box": (600, 1110, 440, 240),
        "header_color": (5, 150, 105),
        "fields": [
            ("id_pago", "INT AUTO_INC", True, False),
            ("id_venta", "INT UQ(vta,medio)", False, True),
            ("medio_pago", "ENUM('efec','transf','deb','cred')", False, False),
            ("monto", "DECIMAL(12,2) >0", False, False),
            ("referencia", "VARCHAR(100) NULL", False, False),
        ]
    },
    "CIERRES_CAJA": {
        "box": (1160, 1060, 470, 510),
        "header_color": (109, 40, 217),
        "fields": [
            ("id_cierre", "INT AUTO_INC", True, False),
            ("id_usuario", "INT UQ(usr,fecha)", False, True),
            ("fecha", "DATE UQ(usr,fecha)", False, False),
            ("cerrado_en", "DATETIME", False, False),
            ("cantidad_ventas", "INT CHECK >=0", False, False),
            ("monto_inicial", "DECIMAL(12,2) >=0", False, False),
            ("total_efectivo", "DECIMAL(12,2) >=0", False, False),
            ("total_transferencia", "DECIMAL(12,2) >=0", False, False),
            ("total_debito", "DECIMAL(12,2) >=0", False, False),
            ("total_credito", "DECIMAL(12,2) >=0", False, False),
            ("total_ventas", "DECIMAL(12,2) GEN", False, False),
            ("efectivo_esperado", "DECIMAL(12,2) GEN", False, False),
            ("efectivo_contado", "DECIMAL(12,2) >=0", False, False),
            ("diferencia", "DECIMAL(12,2) GEN", False, False),
            ("observaciones", "VARCHAR(255)", False, False),
        ]
    }
}

# Draw tables
for tname, tdata in tables.items():
    x, y, w, h = tdata["box"]
    hdr_color = tdata["header_color"]

    # Shadow & Card
    draw.rounded_rectangle((x+4, y+4, x+w+4, y+h+4), radius=8, fill=(226, 232, 240))
    draw.rounded_rectangle((x, y, x+w, y+h), radius=8, fill=(255, 255, 255), outline=(203, 213, 225), width=2)

    # Header
    hdr_h = 40
    draw.rounded_rectangle((x, y, x+w, y+hdr_h), radius=8, fill=hdr_color)
    draw.rectangle((x, y+hdr_h-8, x+w, y+hdr_h), fill=hdr_color)
    draw.text((x+14, y+8), tname, fill=(255, 255, 255), font=font_tbl_header)

    curr_y = y + hdr_h + 6
    for fname, ftype, is_pk, is_fk in tdata["fields"]:
        badge_x = x + 10
        if is_pk:
            draw.rounded_rectangle((badge_x, curr_y, badge_x+26, curr_y+17), radius=4, fill=(254, 240, 138), outline=(202, 138, 4))
            draw.text((badge_x+4, curr_y+1), "PK", fill=(113, 63, 18), font=font_badge)
            badge_x += 32
        if is_fk:
            draw.rounded_rectangle((badge_x, curr_y, badge_x+26, curr_y+17), radius=4, fill=(224, 231, 255), outline=(79, 70, 229))
            draw.text((badge_x+4, curr_y+1), "FK", fill=(49, 46, 129), font=font_badge)
            badge_x += 32
        if not is_pk and not is_fk:
            badge_x += 6

        fn_font = font_attr_bold if (is_pk or is_fk) else font_attr_name
        draw.text((badge_x, curr_y), fname, fill=(15, 23, 42), font=fn_font)

        type_w = int(draw.textlength(ftype, font=font_attr_type))
        draw.text((x+w - type_w - 10, curr_y+1), ftype, fill=(100, 116, 139), font=font_attr_type)

        curr_y += 22
        draw.line((x+8, curr_y, x+w-8, curr_y), fill=(241, 245, 249), width=1)
        curr_y += 4

# Relations (orthogonal, non-overlapping)
# 1. CATEGORIAS (1) -> PRODUCTOS (N)
draw.line([(410, 260), (520, 260)], fill=(37, 99, 235), width=3)
draw.text((418, 235), "1", fill=(15, 23, 42), font=font_tbl_header)
draw.text((498, 235), "N", fill=(15, 23, 42), font=font_tbl_header)
draw.text((435, 266), "clasifica", fill=(71, 85, 105), font=font_rel)

# 2. PROVEEDORES (1) -> PRODUCTOS (N)
draw.line([(1100, 260), (970, 260)], fill=(37, 99, 235), width=3)
draw.text((1080, 235), "1", fill=(15, 23, 42), font=font_tbl_header)
draw.text((980, 235), "N", fill=(15, 23, 42), font=font_tbl_header)
draw.text((1005, 266), "abastece", fill=(71, 85, 105), font=font_rel)

# 3. PRODUCTOS (1) -> HISTORIAL_PRECIOS (N) (routes cleanly above PROVEEDORES)
draw.line([(970, 180), (1040, 180), (1040, 122), (1580, 122), (1580, 220), (1640, 220)], fill=(3, 105, 161), width=3)
draw.text((980, 155), "1", fill=(15, 23, 42), font=font_tbl_header)
draw.text((1618, 195), "N", fill=(15, 23, 42), font=font_tbl_header)
draw.text((1210, 102), "registra vigencia histórica de precios (1:N)", fill=(3, 105, 161), font=font_rel)

# 4. PRODUCTOS (1) -> DETALLE_VENTAS (N)
draw.line([(745, 590), (745, 700)], fill=(14, 116, 144), width=3)
draw.text((755, 600), "1", fill=(15, 23, 42), font=font_tbl_header)
draw.text((755, 668), "N", fill=(15, 23, 42), font=font_tbl_header)
draw.text((640, 638), "ítem vendido", fill=(71, 85, 105), font=font_rel)

# 5. VENTAS (1) -> DETALLE_VENTAS (N)
draw.line([(1100, 770), (970, 770)], fill=(16, 185, 129), width=3)
draw.text((1080, 745), "1", fill=(15, 23, 42), font=font_tbl_header)
draw.text((980, 745), "N", fill=(15, 23, 42), font=font_tbl_header)
draw.text((1000, 776), "renglones", fill=(71, 85, 105), font=font_rel)

# 6. USUARIOS (1) -> VENTAS (N)
draw.line([(1680, 750), (1540, 750)], fill=(71, 85, 105), width=3)
draw.text((1660, 725), "1", fill=(15, 23, 42), font=font_tbl_header)
draw.text((1552, 725), "N", fill=(15, 23, 42), font=font_tbl_header)
draw.text((1570, 756), "opera venta", fill=(71, 85, 105), font=font_rel)

# 7. VENTAS (1) -> PAGOS_VENTA (N) (entidad asociativa de pagos)
draw.line([(1190, 920), (1190, 1050), (820, 1050), (820, 1110)], fill=(5, 150, 105), width=3)
draw.text((1200, 928), "1", fill=(15, 23, 42), font=font_tbl_header)
draw.text((830, 1080), "N", fill=(15, 23, 42), font=font_tbl_header)
draw.text((865, 1056), "pagos por medio (1:N, admite pago mixto)", fill=(5, 150, 105), font=font_rel)

# 8. PRODUCTOS (1) -> MOVIMIENTOS_STOCK (N)
draw.line([(520, 480), (465, 480), (465, 1110)], fill=(194, 65, 12), width=3)
draw.text((495, 455), "1", fill=(15, 23, 42), font=font_tbl_header)
draw.text((475, 1080), "N", fill=(15, 23, 42), font=font_tbl_header)
draw.text((335, 680), "bitácora de", fill=(194, 65, 12), font=font_rel)
draw.text((345, 700), "stock (1:N)", fill=(194, 65, 12), font=font_rel)

# 9. VENTAS (1) -> MOVIMIENTOS_STOCK (N)
draw.line([(1120, 920), (1120, 1005), (300, 1005), (300, 1110)], fill=(217, 119, 6), width=3)
draw.text((1098, 928), "1", fill=(15, 23, 42), font=font_tbl_header)
draw.text((310, 1080), "N", fill=(15, 23, 42), font=font_tbl_header)
draw.text((530, 982), "egreso / anulación de stock asociado al ticket (1:N)", fill=(217, 119, 6), font=font_rel)

# 10. USUARIOS (1) -> CIERRES_CAJA (N)
draw.line([(1900, 880), (1900, 1220), (1630, 1220)], fill=(109, 40, 217), width=3)
draw.text((1910, 890), "1", fill=(15, 23, 42), font=font_tbl_header)
draw.text((1645, 1192), "N", fill=(15, 23, 42), font=font_tbl_header)
draw.text((1675, 1228), "arqueo diario UQ(usuario,fecha)", fill=(109, 40, 217), font=font_rel)

# Legend at bottom right
draw.rounded_rectangle((1670, 1360, 2200, 1570), radius=8, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
draw.text((1690, 1375), "Convenciones y Reglas del Modelo v2.1", fill=(15, 23, 42), font=font_tbl_header)
draw.text((1690, 1412), "PK: Clave Primaria · FK: Clave Foránea (ON DELETE RESTRICT)", fill=(71, 85, 105), font=font_attr_bold)
draw.text((1690, 1440), "UQ: Restricción UNIQUE · IDX: Índice B-Tree explícito", fill=(71, 85, 105), font=font_attr_name)
draw.text((1690, 1468), "GEN: Columna calculada (GENERATED ALWAYS AS ... STORED)", fill=(71, 85, 105), font=font_attr_name)
draw.text((1690, 1496), "• DETALLE_VENTAS resuelve N:M entre VENTAS y PRODUCTOS", fill=(14, 116, 144), font=font_attr_bold)
draw.text((1690, 1524), "• PAGOS_VENTA desacopla pagos de la cabecera de VENTA", fill=(5, 150, 105), font=font_attr_bold)

out_dir = r"c:\Users\pablo\Dropbox\Programación II\Vue.js\Proyecto final Vue\Kiosco-Vue\database"
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "er_diagram_completo.png")
img.save(out_file, "PNG", dpi=(300, 300))
print(f"Diagrama v2.1 guardado en: {out_file}")
