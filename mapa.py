"""
Mapa de la Península de Baja California (contorno + zonas)
==========================================================
Fuente de datos: Natural Earth (naturalearthdata.com)
  - Dataset: Admin 1 – States, Provinces (1:10m de resolución)

Capas de zonas:
  - Lee archivos JSON de zonas desde datos/capas_zonas.json
  - Cada archivo contiene puntos con: id, nombre, latitud, longitud, figura, color
  - Las figuras se dibujan proporcionales (100m de diámetro)
  - Al ejecutar, el usuario elige cuáles archivos de zonas activar

Dependencias: geopandas, matplotlib, numpy
"""

import os
import json
import math
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import matplotlib.patches as mpatches
from shapely.ops import unary_union

# ─── Configuración ────────────────────────────────────────────────────────────
DATOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
ARCHIVO_ZIP = os.path.join(DATOS_DIR, "ne_10m_admin_1_states_provinces.zip")
ARCHIVO_PALETAS = os.path.join(DATOS_DIR, "paletas.json")
ARCHIVO_CAPAS_ZONAS = os.path.join(DATOS_DIR, "capas_zonas.json")
URL_DATOS = (
    "https://naciscdn.org/naturalearth/10m/cultural/"
    "ne_10m_admin_1_states_provinces.zip"
)

# Valores por defecto para la Península de Baja California
LAT_MIN_DEFAULT = 22.0
LAT_MAX_DEFAULT = 33.0
LON_MIN_DEFAULT = -120.0
LON_MAX_DEFAULT = -108.0

# Mapeo de nombres de colores en español a códigos hex
COLORES_ESPAÑOL = {
    "rojo":       "#e63946",
    "azul":       "#1d3557",
    "verde":      "#2a9d8f",
    "amarillo":   "#f4a261",
    "naranja":    "#e76f51",
    "morado":     "#6a0dad",
    "rosa":       "#ff69b4",
    "negro":      "#000000",
    "blanco":     "#ffffff",
    "gris":       "#888888",
    "cafe":       "#8b4513",
    "cyan":       "#00bcd4",
    "magenta":    "#e91e63",
    "turquesa":   "#40e0d0",
    "dorado":     "#ffd700",
    "plateado":   "#c0c0c0",
}


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNCIONES DE DESCARGA
# ═══════════════════════════════════════════════════════════════════════════════

def descargar_datos():
    """Descarga el archivo ZIP de Natural Earth si no existe localmente."""
    if os.path.exists(ARCHIVO_ZIP):
        tamaño = os.path.getsize(ARCHIVO_ZIP) / (1024 * 1024)
        print(f"✅ Datos cartográficos: encontrados ({tamaño:.1f} MB)")
        return ARCHIVO_ZIP

    os.makedirs(DATOS_DIR, exist_ok=True)
    print("=" * 60)
    print("  DESCARGANDO DATOS DE NATURAL EARTH")
    print("=" * 60)
    print(f"  URL: {URL_DATOS}")
    print("  Descargando... (esto puede tardar un momento)")

    try:
        import urllib.request
        urllib.request.urlretrieve(URL_DATOS, ARCHIVO_ZIP)
        tamaño = os.path.getsize(ARCHIVO_ZIP) / (1024 * 1024)
        print(f"  ✅ Descarga completada ({tamaño:.1f} MB)\n")
    except Exception as e:
        print(f"  ❌ Error al descargar: {e}")
        if os.path.exists(ARCHIVO_ZIP):
            os.remove(ARCHIVO_ZIP)
        raise

    return ARCHIVO_ZIP


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNCIONES DE PALETAS
# ═══════════════════════════════════════════════════════════════════════════════

def cargar_paletas():
    """Carga las paletas de colores desde el archivo JSON."""
    if not os.path.exists(ARCHIVO_PALETAS):
        return [paleta_por_defecto()]
    try:
        with open(ARCHIVO_PALETAS, "r", encoding="utf-8") as f:
            data = json.load(f)
        paletas = data.get("paletas", [])
        if not paletas:
            return [paleta_por_defecto()]
        print(f"  ✅ Paletas: {len(paletas)} disponibles")
        return paletas
    except Exception as e:
        print(f"  ❌ Error al leer paletas: {e}")
        return [paleta_por_defecto()]


def paleta_por_defecto():
    return {
        "nombre": "Clásico (fondo blanco)",
        "fondo_figura": "#ffffff", "fondo_mapa": "#ffffff",
        "relleno_tierra": "#f5e6ca", "contorno": "#1a3c6e",
        "division_estados": "#cc3333", "texto_etiquetas": "#1a1a1a",
        "texto_stroke": "#ffffff", "titulo": "#1a3c6e",
        "subtitulo": "#666666", "ejes_texto": "#333333",
        "ejes_ticks": "#444444", "ejes_bordes": "#cccccc",
        "cuadricula": "#cccccc", "cuadricula_alpha": 0.3,
        "texto_info": "#777777", "indicador_norte": "#1a3c6e",
    }


def pedir_paleta(paletas):
    """Muestra las paletas y permite elegir una."""
    print("=" * 60)
    print("  PALETAS DE COLORES")
    print("=" * 60)
    for i, p in enumerate(paletas, 1):
        print(f"  {i}. {p.get('nombre', f'Paleta {i}')}")
    print("-" * 60)
    entrada = input("  Elige una paleta [1]: ").strip()
    try:
        sel = int(entrada) - 1 if entrada else 0
    except ValueError:
        sel = 0
    if sel < 0 or sel >= len(paletas):
        sel = 0
    print(f"\n  🎨 Paleta: {paletas[sel].get('nombre', '?')}\n")
    return paletas[sel]


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNCIONES DE ZONAS
# ═══════════════════════════════════════════════════════════════════════════════

def cargar_capas_zonas():
    """Lee el archivo de registro de capas de zonas."""
    if not os.path.exists(ARCHIVO_CAPAS_ZONAS):
        print("  ⚠️  No se encontró capas_zonas.json — sin capas de zonas.")
        return []

    try:
        with open(ARCHIVO_CAPAS_ZONAS, "r", encoding="utf-8") as f:
            data = json.load(f)
        archivos = data.get("archivos", [])
        print(f"  ✅ Capas de zonas: {len(archivos)} archivo(s) registrado(s)")
        return archivos
    except Exception as e:
        print(f"  ❌ Error al leer capas_zonas.json: {e}")
        return []


def pedir_zonas_activas(capas):
    """Permite al usuario elegir cuáles archivos de zonas activar."""
    if not capas:
        return []

    print("=" * 60)
    print("  CAPAS DE ZONAS DISPONIBLES")
    print("=" * 60)
    print(f"  (Registradas en datos/capas_zonas.json)")
    print("")

    for i, capa in enumerate(capas, 1):
        archivo = capa.get("archivo", "?")
        desc = capa.get("descripcion", "Sin descripción")
        ruta = os.path.join(DATOS_DIR, archivo)
        existe = "✅" if os.path.exists(ruta) else "❌ NO ENCONTRADO"
        print(f"  {i}. {archivo}")
        print(f"     {desc}  [{existe}]")
        print("")

    print("  Escribe los números separados por coma para activar.")
    print("  Ejemplo: 1,2 para activar las dos primeras.")
    print("  Presiona ENTER para no activar ninguna.")
    print("-" * 60)
    entrada = input("  Capas a activar [ninguna]: ").strip()

    if not entrada:
        print("  → Sin capas de zonas activadas.\n")
        return []

    activas = []
    for parte in entrada.replace(" ", "").split(","):
        try:
            idx = int(parte) - 1
            if 0 <= idx < len(capas):
                archivo = capas[idx].get("archivo", "")
                ruta = os.path.join(DATOS_DIR, archivo)
                if os.path.exists(ruta):
                    activas.append(capas[idx])
                else:
                    print(f"  ⚠️  Archivo '{archivo}' no encontrado, ignorado.")
            else:
                print(f"  ⚠️  Número {parte} fuera de rango.")
        except ValueError:
            print(f"  ⚠️  '{parte}' no es válido.")

    if activas:
        print(f"\n  📌 Capas activadas: {len(activas)}")
        for c in activas:
            print(f"     ✓ {c.get('archivo', '?')}")
    else:
        print("  → Sin capas de zonas activadas.")
    print("")

    return activas


def cargar_zonas(capas_activas):
    """Carga todas las zonas de los archivos activos."""
    todas_zonas = []

    for capa in capas_activas:
        archivo = capa.get("archivo", "")
        ruta = os.path.join(DATOS_DIR, archivo)

        try:
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
            zonas = data.get("zonas", [])
            nombre_capa = data.get("nombre", archivo)
            print(f"  📂 {nombre_capa}: {len(zonas)} zonas cargadas")

            for z in zonas:
                z["_archivo_origen"] = archivo
                z["_nombre_capa"] = nombre_capa
            todas_zonas.extend(zonas)

        except Exception as e:
            print(f"  ❌ Error al leer {archivo}: {e}")

    if todas_zonas:
        print(f"  Total de zonas: {len(todas_zonas)}\n")
    return todas_zonas


def resolver_color(nombre_color):
    """Convierte un nombre de color en español a código hex."""
    nombre = nombre_color.lower().strip()
    if nombre in COLORES_ESPAÑOL:
        return COLORES_ESPAÑOL[nombre]
    # Si ya es un código hex, devolverlo tal cual
    if nombre.startswith("#"):
        return nombre
    # Intentar como nombre de color de matplotlib
    return nombre


def metros_a_grados(metros, latitud):
    """
    Convierte metros a grados de longitud/latitud.
    100m ≈ 0.0009° en latitud (más o menos constante)
    En longitud depende de la latitud: 100m ≈ 0.0009° / cos(lat)
    """
    grados_lat = metros / 111_320.0  # 1 grado ≈ 111,320 metros
    grados_lon = metros / (111_320.0 * math.cos(math.radians(latitud)))
    return grados_lat, grados_lon


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNCIONES DE COORDENADAS
# ═══════════════════════════════════════════════════════════════════════════════

def pedir_coordenadas():
    """Pide al usuario las coordenadas de latitud y longitud."""
    print("=" * 60)
    print("  ÁREA DEL MAPA")
    print("=" * 60)
    print(f"  Por defecto: Lat [{LAT_MIN_DEFAULT}°, {LAT_MAX_DEFAULT}°]"
          f"  Lon [{LON_MIN_DEFAULT}°, {LON_MAX_DEFAULT}°]")
    print("  ENTER = valores por defecto.")
    print("-" * 60)

    entrada = input(f"  Latitud mínima  [{LAT_MIN_DEFAULT}]: ").strip()
    lat_min = float(entrada) if entrada else LAT_MIN_DEFAULT

    entrada = input(f"  Latitud máxima  [{LAT_MAX_DEFAULT}]: ").strip()
    lat_max = float(entrada) if entrada else LAT_MAX_DEFAULT

    entrada = input(f"  Longitud mínima [{LON_MIN_DEFAULT}]: ").strip()
    lon_min = float(entrada) if entrada else LON_MIN_DEFAULT

    entrada = input(f"  Longitud máxima [{LON_MAX_DEFAULT}]: ").strip()
    lon_max = float(entrada) if entrada else LON_MAX_DEFAULT

    if lat_min >= lat_max:
        lat_min, lat_max = lat_max, lat_min
    if lon_min >= lon_max:
        lon_min, lon_max = lon_max, lon_min

    print(f"\n  📍 Área: Lat [{lat_min}°, {lat_max}°]  Lon [{lon_min}°, {lon_max}°]\n")
    return lat_min, lat_max, lon_min, lon_max


# ═══════════════════════════════════════════════════════════════════════════════
#  CARGA DE DATOS CARTOGRÁFICOS
# ═══════════════════════════════════════════════════════════════════════════════

def cargar_datos(archivo):
    """Carga el shapefile y filtra los estados de Baja California."""
    print("  Cargando datos cartográficos...")
    gdf = gpd.read_file(f"zip://{archivo}")

    estados_peninsula = ["Baja California", "Baja California Sur"]
    baja = gdf[
        (gdf["admin"] == "Mexico") &
        (gdf["name"].isin(estados_peninsula))
    ].copy()

    if baja.empty:
        mexico_states = gdf[gdf["admin"] == "Mexico"]
        baja = mexico_states[
            mexico_states["name"].str.contains("Baja", case=False, na=False)
        ].copy()

    print(f"  Estados: {list(baja['name'].values)}")
    return baja


# ═══════════════════════════════════════════════════════════════════════════════
#  GENERACIÓN DEL MAPA
# ═══════════════════════════════════════════════════════════════════════════════

def generar_mapa(baja, lat_min, lat_max, lon_min, lon_max, paleta, zonas):
    """Genera el mapa con contorno + zonas + tabla de referencia."""

    c = paleta

    # Unir geometrías
    peninsula_unida = unary_union(baja.geometry)

    # Proporciones
    ancho = lon_max - lon_min
    alto = lat_max - lat_min
    ratio = alto / ancho
    fig_alto = max(8, 10 * ratio)

    # Si hay zonas, crear 2 paneles: tabla (izquierda) + mapa (derecha)
    if zonas:
        fig, (ax_tabla, ax) = plt.subplots(
            1, 2,
            figsize=(14, fig_alto),
            gridspec_kw={"width_ratios": [1, 3]},
            facecolor=c.get("fondo_figura", "#ffffff")
        )
    else:
        fig, ax = plt.subplots(
            1, 1,
            figsize=(10, fig_alto),
            facecolor=c.get("fondo_figura", "#ffffff")
        )
        ax_tabla = None

    ax.set_facecolor(c.get("fondo_mapa", "#ffffff"))

    # ─── Relleno ──────────────────────────────────────────────────────────
    baja.plot(
        ax=ax,
        color=c.get("relleno_tierra", "#f5e6ca"),
        edgecolor="none",
        alpha=0.8
    )

    # ─── Contorno unificado ───────────────────────────────────────────────
    gpd.GeoSeries([peninsula_unida]).plot(
        ax=ax,
        facecolor="none",
        edgecolor=c.get("contorno", "#1a3c6e"),
        linewidth=1.5,
        alpha=0.9
    )

    # ─── División entre estados ───────────────────────────────────────────
    baja.boundary.plot(
        ax=ax,
        edgecolor=c.get("division_estados", "#cc3333"),
        linewidth=1.0,
        linestyle="--",
        alpha=0.6
    )

    # ─── Etiquetas de estados ─────────────────────────────────────────────
    for idx, row in baja.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(
            row["name"],
            xy=(centroid.x, centroid.y),
            fontsize=11, fontweight="bold",
            color=c.get("texto_etiquetas", "#1a1a1a"),
            ha="center", va="center",
            path_effects=[
                pe.withStroke(linewidth=3, foreground=c.get("texto_stroke", "#ffffff"))
            ]
        )

    # ─── DIBUJAR ZONAS (solo las visibles dentro del área) ───────────────
    zonas_visibles = []
    if zonas:
        zonas_visibles = [
            z for z in zonas
            if lat_min <= z.get("latitud", 0) <= lat_max
            and lon_min <= z.get("longitud", 0) <= lon_max
        ]
        if zonas_visibles:
            dibujar_zonas(ax, zonas_visibles, lat_min, lat_max, lon_min, lon_max, c)
            dibujar_tabla(ax_tabla, zonas_visibles, c)
            n_ocultas = len(zonas) - len(zonas_visibles)
            if n_ocultas > 0:
                print(f"  ⚠️  {n_ocultas} zona(s) fuera del área visible, no se muestran.")
        else:
            print("  ⚠️  Ninguna zona cae dentro del área seleccionada.")
            if ax_tabla is not None:
                ax_tabla.axis("off")

    # ─── Configurar límites ───────────────────────────────────────────────
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)

    # ─── Título ───────────────────────────────────────────────────────────
    ax.set_title(
        "Península de Baja California",
        color=c.get("titulo", "#1a3c6e"),
        fontsize=20, fontweight="bold", pad=20,
        fontfamily="sans-serif"
    )

    # Subtítulo
    n_visibles = len(zonas_visibles)
    subtexto = "Natural Earth 1:10m"
    if n_visibles > 0:
        subtexto += f" — {n_visibles} zonas de interés"
    ax.text(
        0.5, 1.02, subtexto,
        transform=ax.transAxes, ha="center",
        fontsize=9, color=c.get("subtitulo", "#666666"), style="italic"
    )

    # ─── Ejes ─────────────────────────────────────────────────────────────
    ax.set_xlabel("Longitud", color=c.get("ejes_texto", "#333333"), fontsize=10)
    ax.set_ylabel("Latitud", color=c.get("ejes_texto", "#333333"), fontsize=10)
    ax.tick_params(colors=c.get("ejes_ticks", "#444444"), labelsize=8)

    for spine in ax.spines.values():
        spine.set_edgecolor(c.get("ejes_bordes", "#cccccc"))
        spine.set_linewidth(0.5)

    ax.grid(
        True, alpha=c.get("cuadricula_alpha", 0.3),
        color=c.get("cuadricula", "#cccccc"),
        linestyle="-", linewidth=0.5
    )

    ax.text(
        0.95, 0.02, "Proyección: WGS84 (EPSG:4326)",
        transform=ax.transAxes, ha="right",
        fontsize=7, color=c.get("texto_info", "#777777")
    )

    # ─── Indicador del norte ──────────────────────────────────────────────
    cn = c.get("indicador_norte", "#1a3c6e")
    ax.annotate("N", xy=(0.95, 0.95), xycoords="axes fraction",
                fontsize=14, fontweight="bold", color=cn, ha="center", va="center")
    ax.annotate("↑", xy=(0.95, 0.92), xycoords="axes fraction",
                fontsize=18, color=cn, ha="center", va="center")

    # ─── Coordenadas ──────────────────────────────────────────────────────
    ax.text(
        0.05, 0.02,
        f"Área: Lat [{lat_min}°, {lat_max}°]  Lon [{lon_min}°, {lon_max}°]",
        transform=ax.transAxes, ha="left",
        fontsize=7, color=c.get("texto_info", "#777777")
    )

    # ─── Guardar y mostrar ────────────────────────────────────────────────
    plt.tight_layout()

    output_file = "mapa_baja_california.png"
    plt.savefig(
        output_file, dpi=200, bbox_inches="tight",
        facecolor=c.get("fondo_figura", "#ffffff"), edgecolor="none"
    )

    print("=" * 60)
    print(f"  ✅ Mapa guardado como '{output_file}'")
    print(f"     Resolución: 200 DPI")
    print(f"     Paleta: {c.get('nombre', '?')}")
    if zonas:
        print(f"     Zonas dibujadas: {len(zonas)}")
    print(f"     Área: Lat [{lat_min}°, {lat_max}°]  Lon [{lon_min}°, {lon_max}°]")
    print("=" * 60)

    plt.show()
    print("\n¡Listo! El mapa se ha generado exitosamente.")


def dibujar_zonas(ax, zonas, lat_min, lat_max, lon_min, lon_max, paleta):
    """Dibuja las zonas de interés con un círculo de color y el ID adentro."""

    # Calcular tamaño del marcador proporcional al área visible
    rango_lat = lat_max - lat_min
    # Radio visual: ~0.8% del rango de latitud para ser visible
    radio_visual = rango_lat * 0.008

    for zona in zonas:
        lat = zona.get("latitud", 0)
        lon = zona.get("longitud", 0)
        zona_id = zona.get("id", "?")
        color_nombre = zona.get("color", "rojo")
        color = resolver_color(color_nombre)

        # Verificar que esté dentro del área visible
        if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
            continue

        # Factor de corrección para longitud (los grados no son cuadrados)
        cos_lat = math.cos(math.radians(lat))
        radio_lon = radio_visual / cos_lat if cos_lat > 0 else radio_visual

        # Dibujar círculo de color
        circulo = mpatches.Ellipse(
            (lon, lat),
            width=radio_lon * 2,
            height=radio_visual * 2,
            facecolor=color,
            edgecolor="black",
            linewidth=1.0,
            alpha=0.85,
            zorder=5
        )
        ax.add_patch(circulo)

        # ID centrado dentro del círculo
        # Elegir color de texto (blanco o negro) según brillo del fondo
        texto_color = _color_texto_contraste(color)
        ax.text(
            lon, lat, str(zona_id),
            ha="center", va="center",
            fontsize=7, fontweight="bold",
            color=texto_color,
            zorder=6,
            path_effects=[
                pe.withStroke(linewidth=1.5, foreground="black" if texto_color == "white" else "white")
            ]
        )


def _color_texto_contraste(hex_color):
    """Devuelve 'white' o 'black' según el brillo del color de fondo."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        # Luminancia relativa
        brillo = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "white" if brillo < 0.5 else "black"
    except Exception:
        return "black"


def dibujar_tabla(ax_tabla, zonas, paleta):
    """Dibuja una tabla compacta de referencia con ID y nombre."""

    c = paleta
    fondo = c.get("fondo_figura", "#ffffff")
    ax_tabla.set_facecolor(fondo)
    ax_tabla.set_xlim(0, 1)
    ax_tabla.set_ylim(0, 1)
    ax_tabla.axis("off")

    # Título
    ax_tabla.text(
        0.5, 0.97, "Zonas",
        ha="center", va="top",
        fontsize=11, fontweight="bold",
        color=c.get("titulo", "#1a3c6e"),
        transform=ax_tabla.transAxes
    )

    # Encabezados
    y_inicio = 0.94
    color_enc = c.get("ejes_texto", "#333333")
    ax_tabla.text(0.10, y_inicio, "ID", ha="center", va="top",
                  fontsize=8, fontweight="bold", color=color_enc)
    ax_tabla.text(0.25, y_inicio, "Nombre", ha="left", va="top",
                  fontsize=8, fontweight="bold", color=color_enc)

    # Línea separadora
    ax_tabla.plot([0.02, 0.98], [y_inicio - 0.012, y_inicio - 0.012],
                  color=c.get("ejes_bordes", "#cccccc"), linewidth=0.8,
                  transform=ax_tabla.transAxes)

    # Filas compactas
    n = len(zonas)
    espacio = y_inicio - 0.06
    alto_fila = min(0.025, espacio / max(n, 1))

    for i, zona in enumerate(zonas):
        y = y_inicio - 0.025 - (i * alto_fila)
        zona_id = zona.get("id", "?")
        nombre = zona.get("nombre", "?")

        # ID
        ax_tabla.text(
            0.10, y, str(zona_id),
            ha="center", va="center",
            fontsize=8, fontweight="bold",
            color=c.get("texto_etiquetas", "#1a1a1a"),
            transform=ax_tabla.transAxes
        )

        # Nombre
        ax_tabla.text(
            0.25, y, nombre,
            ha="left", va="center",
            fontsize=7,
            color=c.get("texto_etiquetas", "#1a1a1a"),
            transform=ax_tabla.transAxes
        )

    for spine in ax_tabla.spines.values():
        spine.set_visible(False)


# ═══════════════════════════════════════════════════════════════════════════════
#  PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   MAPA - PENÍNSULA DE BAJA CALIFORNIA + ZONAS            ║")
    print("║   Fuente: Natural Earth (naturalearthdata.com)            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("")

    # Paso 1: Verificar datos cartográficos
    archivo = descargar_datos()

    # Paso 2: Cargar paletas y elegir
    paletas = cargar_paletas()
    paleta = pedir_paleta(paletas)

    # Paso 3: Cargar capas de zonas y preguntar cuáles activar
    capas = cargar_capas_zonas()
    capas_activas = pedir_zonas_activas(capas)
    zonas = cargar_zonas(capas_activas) if capas_activas else []

    # Paso 4: Elegir área
    lat_min, lat_max, lon_min, lon_max = pedir_coordenadas()

    # Paso 5: Cargar datos cartográficos
    baja = cargar_datos(archivo)

    # Paso 6: Generar mapa
    generar_mapa(baja, lat_min, lat_max, lon_min, lon_max, paleta, zonas)
