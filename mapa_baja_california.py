"""
Mapa de la Península de Baja California (contorno)
===================================================
Fuente de datos: Natural Earth (naturalearthdata.com)
  - Dataset: Admin 1 – States, Provinces (1:10m de resolución)
  - Es una fuente pública, gratuita y ampliamente utilizada en cartografía.

Dependencias: geopandas, matplotlib

Características:
  - Descarga el archivo de datos localmente y lo reutiliza en ejecuciones futuras.
  - Pide al usuario latitud y longitud para definir el área del mapa.
  - Permite elegir entre paletas de colores definidas en datos/paletas.json.
"""

import os
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from shapely.ops import unary_union

# ─── Configuración ────────────────────────────────────────────────────────────
DATOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
ARCHIVO_ZIP = os.path.join(DATOS_DIR, "ne_10m_admin_1_states_provinces.zip")
ARCHIVO_PALETAS = os.path.join(DATOS_DIR, "paletas.json")
URL_DATOS = (
    "https://naciscdn.org/naturalearth/10m/cultural/"
    "ne_10m_admin_1_states_provinces.zip"
)

# Valores por defecto para la Península de Baja California
LAT_MIN_DEFAULT = 22.0
LAT_MAX_DEFAULT = 33.0
LON_MIN_DEFAULT = -120.0
LON_MAX_DEFAULT = -108.0


# ─── 1. Descargar datos (solo si no existen localmente) ───────────────────────
def descargar_datos():
    """Descarga el archivo ZIP de Natural Earth si no existe localmente."""
    if os.path.exists(ARCHIVO_ZIP):
        tamaño = os.path.getsize(ARCHIVO_ZIP) / (1024 * 1024)
        print(f"✅ Archivo de datos encontrado localmente: {ARCHIVO_ZIP}")
        print(f"   Tamaño: {tamaño:.1f} MB")
        print(f"   No es necesario descargar de nuevo.\n")
        return ARCHIVO_ZIP

    # Crear directorio si no existe
    os.makedirs(DATOS_DIR, exist_ok=True)

    print("=" * 60)
    print("  DESCARGANDO DATOS DE NATURAL EARTH")
    print("=" * 60)
    print(f"  Fuente: https://www.naturalearthdata.com/")
    print(f"  Dataset: Admin 1 – States, Provinces (1:10m)")
    print(f"  URL: {URL_DATOS}")
    print(f"  Destino: {ARCHIVO_ZIP}")
    print("")
    print("  Descargando... (esto puede tardar un momento)")

    try:
        import urllib.request
        urllib.request.urlretrieve(URL_DATOS, ARCHIVO_ZIP)
        tamaño = os.path.getsize(ARCHIVO_ZIP) / (1024 * 1024)
        print(f"  ✅ Descarga completada ({tamaño:.1f} MB)")
        print(f"  Archivo guardado en: {ARCHIVO_ZIP}")
        print(f"  En futuras ejecuciones se usará este archivo local.\n")
    except Exception as e:
        print(f"  ❌ Error al descargar: {e}")
        if os.path.exists(ARCHIVO_ZIP):
            os.remove(ARCHIVO_ZIP)
        raise

    return ARCHIVO_ZIP


# ─── 2. Cargar paletas de colores ─────────────────────────────────────────────
def cargar_paletas():
    """Carga las paletas de colores desde el archivo JSON."""
    if not os.path.exists(ARCHIVO_PALETAS):
        print(f"  ⚠️  No se encontró el archivo de paletas: {ARCHIVO_PALETAS}")
        print(f"  Usando paleta por defecto.\n")
        return [paleta_por_defecto()]

    try:
        with open(ARCHIVO_PALETAS, "r", encoding="utf-8") as f:
            data = json.load(f)
        paletas = data.get("paletas", [])
        if not paletas:
            print("  ⚠️  El archivo de paletas está vacío. Usando paleta por defecto.\n")
            return [paleta_por_defecto()]
        print(f"  ✅ Se cargaron {len(paletas)} paletas desde: {ARCHIVO_PALETAS}\n")
        return paletas
    except Exception as e:
        print(f"  ❌ Error al leer paletas: {e}")
        print(f"  Usando paleta por defecto.\n")
        return [paleta_por_defecto()]


def paleta_por_defecto():
    """Retorna la paleta clásica como fallback."""
    return {
        "nombre": "Clásico (fondo blanco)",
        "fondo_figura": "#ffffff",
        "fondo_mapa": "#ffffff",
        "relleno_tierra": "#f5e6ca",
        "contorno": "#1a3c6e",
        "division_estados": "#cc3333",
        "texto_etiquetas": "#1a1a1a",
        "texto_stroke": "#ffffff",
        "titulo": "#1a3c6e",
        "subtitulo": "#666666",
        "ejes_texto": "#333333",
        "ejes_ticks": "#444444",
        "ejes_bordes": "#cccccc",
        "cuadricula": "#cccccc",
        "cuadricula_alpha": 0.3,
        "texto_info": "#777777",
        "indicador_norte": "#1a3c6e"
    }


# ─── 3. Pedir paleta al usuario ──────────────────────────────────────────────
def pedir_paleta(paletas):
    """Muestra las paletas disponibles y permite elegir una."""
    print("=" * 60)
    print("  PALETAS DE COLORES DISPONIBLES")
    print("=" * 60)
    print(f"  (Archivo: datos/paletas.json)")
    print("")

    for i, p in enumerate(paletas, 1):
        nombre = p.get("nombre", f"Paleta {i}")
        fondo = p.get("fondo_figura", "?")
        contorno = p.get("contorno", "?")
        relleno = p.get("relleno_tierra", "?")
        print(f"  {i}. {nombre}")
        print(f"     Fondo: {fondo}  |  Contorno: {contorno}  |  Relleno: {relleno}")
        print("")

    print("-" * 60)
    entrada = input(f"  Elige una paleta [1]: ").strip()

    if entrada == "":
        seleccion = 0
    else:
        try:
            seleccion = int(entrada) - 1
        except ValueError:
            print("  ⚠️  Valor no válido. Usando paleta 1.")
            seleccion = 0

    if seleccion < 0 or seleccion >= len(paletas):
        print(f"  ⚠️  Opción fuera de rango. Usando paleta 1.")
        seleccion = 0

    elegida = paletas[seleccion]
    print(f"\n  🎨 Paleta seleccionada: {elegida.get('nombre', 'Sin nombre')}\n")
    return elegida


# ─── 4. Pedir coordenadas al usuario ─────────────────────────────────────────
def pedir_coordenadas():
    """Pide al usuario las coordenadas de latitud y longitud para el mapa."""
    print("=" * 60)
    print("  CONFIGURACIÓN DEL ÁREA DEL MAPA")
    print("=" * 60)
    print(f"  Valores por defecto (Península de Baja California):")
    print(f"    Latitud:  {LAT_MIN_DEFAULT}° a {LAT_MAX_DEFAULT}°")
    print(f"    Longitud: {LON_MIN_DEFAULT}° a {LON_MAX_DEFAULT}°")
    print("")
    print("  Presiona ENTER para usar los valores por defecto,")
    print("  o escribe nuevos valores.")
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
        print("  ⚠️  Latitud mínima debe ser menor que la máxima. Intercambiando...")
        lat_min, lat_max = lat_max, lat_min

    if lon_min >= lon_max:
        print("  ⚠️  Longitud mínima debe ser menor que la máxima. Intercambiando...")
        lon_min, lon_max = lon_max, lon_min

    print(f"\n  📍 Área seleccionada:")
    print(f"     Latitud:  {lat_min}° a {lat_max}°")
    print(f"     Longitud: {lon_min}° a {lon_max}°\n")

    return lat_min, lat_max, lon_min, lon_max


# ─── 5. Cargar y filtrar datos ────────────────────────────────────────────────
def cargar_datos(archivo):
    """Carga el shapefile y filtra los estados de Baja California."""
    print("Cargando datos geográficos...")
    gdf = gpd.read_file(f"zip://{archivo}")
    print(f"  Total de registros cargados: {len(gdf)}")

    estados_peninsula = ["Baja California", "Baja California Sur"]
    baja = gdf[
        (gdf["admin"] == "Mexico") &
        (gdf["name"].isin(estados_peninsula))
    ].copy()

    if baja.empty:
        print("  Buscando estados con coincidencia parcial...")
        mexico_states = gdf[gdf["admin"] == "Mexico"]
        baja = mexico_states[
            mexico_states["name"].str.contains("Baja", case=False, na=False)
        ].copy()

    print(f"  Estados encontrados: {list(baja['name'].values)}\n")
    return baja


# ─── 6. Generar el mapa ──────────────────────────────────────────────────────
def generar_mapa(baja, lat_min, lat_max, lon_min, lon_max, paleta):
    """Genera el mapa con el contorno de la península usando la paleta elegida."""

    # Extraer colores de la paleta
    c = paleta  # alias corto

    # Unir geometrías para el contorno completo
    peninsula_unida = unary_union(baja.geometry)

    # Calcular proporciones del mapa
    ancho = lon_max - lon_min
    alto = lat_max - lat_min
    ratio = alto / ancho
    fig_ancho = 10
    fig_alto = max(6, fig_ancho * ratio)

    fig, ax = plt.subplots(
        1, 1,
        figsize=(fig_ancho, fig_alto),
        facecolor=c.get("fondo_figura", "#ffffff")
    )
    ax.set_facecolor(c.get("fondo_mapa", "#ffffff"))

    # Dibujar el relleno con un color suave
    baja.plot(
        ax=ax,
        color=c.get("relleno_tierra", "#f5e6ca"),
        edgecolor="none",
        alpha=0.8
    )

    # Dibujar el contorno de la península completa (unida)
    gpd.GeoSeries([peninsula_unida]).plot(
        ax=ax,
        facecolor="none",
        edgecolor=c.get("contorno", "#1a3c6e"),
        linewidth=1.5,
        alpha=0.9
    )

    # Dibujar la división entre los dos estados (línea interna)
    baja.boundary.plot(
        ax=ax,
        edgecolor=c.get("division_estados", "#cc3333"),
        linewidth=1.0,
        linestyle="--",
        alpha=0.6
    )

    # ─── Etiquetas de los estados ─────────────────────────────────────────
    for idx, row in baja.iterrows():
        centroid = row.geometry.centroid
        ax.annotate(
            row["name"],
            xy=(centroid.x, centroid.y),
            fontsize=11,
            fontweight="bold",
            color=c.get("texto_etiquetas", "#1a1a1a"),
            ha="center",
            va="center",
            path_effects=[
                pe.withStroke(
                    linewidth=3,
                    foreground=c.get("texto_stroke", "#ffffff")
                )
            ]
        )

    # ─── Configurar límites según lo que pidió el usuario ─────────────────
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)

    # ─── Título y subtítulo ───────────────────────────────────────────────
    ax.set_title(
        "Península de Baja California",
        color=c.get("titulo", "#1a3c6e"),
        fontsize=20,
        fontweight="bold",
        pad=20,
        fontfamily="sans-serif"
    )

    ax.text(
        0.5, 1.02,
        "Fuente: Natural Earth (naturalearthdata.com) — Resolución 1:10m",
        transform=ax.transAxes,
        ha="center",
        fontsize=9,
        color=c.get("subtitulo", "#666666"),
        style="italic"
    )

    # ─── Ejes ─────────────────────────────────────────────────────────────
    ax.set_xlabel("Longitud", color=c.get("ejes_texto", "#333333"), fontsize=10)
    ax.set_ylabel("Latitud", color=c.get("ejes_texto", "#333333"), fontsize=10)
    ax.tick_params(colors=c.get("ejes_ticks", "#444444"), labelsize=8)

    for spine in ax.spines.values():
        spine.set_edgecolor(c.get("ejes_bordes", "#cccccc"))
        spine.set_linewidth(0.5)

    # Cuadrícula sutil
    ax.grid(
        True,
        alpha=c.get("cuadricula_alpha", 0.3),
        color=c.get("cuadricula", "#cccccc"),
        linestyle="-",
        linewidth=0.5
    )

    # Proyección
    ax.text(
        0.95, 0.02,
        "Proyección: WGS84 (EPSG:4326)",
        transform=ax.transAxes,
        ha="right",
        fontsize=7,
        color=c.get("texto_info", "#777777")
    )

    # ─── Indicador del norte ──────────────────────────────────────────────
    color_norte = c.get("indicador_norte", "#1a3c6e")
    ax.annotate(
        "N",
        xy=(0.95, 0.95),
        xycoords="axes fraction",
        fontsize=14,
        fontweight="bold",
        color=color_norte,
        ha="center",
        va="center"
    )
    ax.annotate(
        "↑",
        xy=(0.95, 0.92),
        xycoords="axes fraction",
        fontsize=18,
        color=color_norte,
        ha="center",
        va="center"
    )

    # ─── Coordenadas del área mostrada ────────────────────────────────────
    ax.text(
        0.05, 0.02,
        f"Área: Lat [{lat_min}°, {lat_max}°]  Lon [{lon_min}°, {lon_max}°]",
        transform=ax.transAxes,
        ha="left",
        fontsize=7,
        color=c.get("texto_info", "#777777")
    )

    # ─── Guardar y mostrar ────────────────────────────────────────────────
    plt.tight_layout()

    output_file = "mapa_baja_california.png"
    plt.savefig(
        output_file,
        dpi=200,
        bbox_inches="tight",
        facecolor=c.get("fondo_figura", "#ffffff"),
        edgecolor="none"
    )

    nombre_paleta = c.get("nombre", "Sin nombre")
    print("=" * 60)
    print(f"  ✅ Mapa guardado como '{output_file}'")
    print(f"     Resolución: 200 DPI")
    print(f"     Paleta: {nombre_paleta}")
    print(f"     Área: Lat [{lat_min}°, {lat_max}°]")
    print(f"           Lon [{lon_min}°, {lon_max}°]")
    print(f"     Fuente: Natural Earth (1:10m)")
    print("=" * 60)

    plt.show()
    print("\n¡Listo! El mapa se ha generado exitosamente.")


# ─── PRINCIPAL ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   GENERADOR DE MAPA - PENÍNSULA DE BAJA CALIFORNIA       ║")
    print("║   Fuente: Natural Earth (naturalearthdata.com)            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("")

    # Paso 1: Descargar datos si no existen
    archivo = descargar_datos()

    # Paso 2: Cargar paletas y dejar al usuario elegir
    paletas = cargar_paletas()
    paleta = pedir_paleta(paletas)

    # Paso 3: Pedir coordenadas al usuario
    lat_min, lat_max, lon_min, lon_max = pedir_coordenadas()

    # Paso 4: Cargar y filtrar datos
    baja = cargar_datos(archivo)

    # Paso 5: Generar el mapa
    generar_mapa(baja, lat_min, lat_max, lon_min, lon_max, paleta)
