"""
Dibuja - Generador de Mapas de la Península de Baja California
===============================================================
Fuente de datos: Natural Earth (naturalearthdata.com) — Resolución 1:10m

Datasets disponibles:
  1. Estados/Provincias  (ne_10m_admin_1_states_provinces) — contornos
  2. Ciudades/Localidades (ne_10m_populated_places)         — puntos
  3. Países              (ne_10m_admin_0_countries)          — fronteras
  4. Carreteras           (ne_10m_roads)                     — líneas

El usuario puede elegir qué combinación de datasets mostrar en el mapa,
la paleta de colores (desde datos/paletas.json), y el área geográfica.

Dependencias: geopandas, matplotlib
"""

import os
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from shapely.ops import unary_union
from shapely.geometry import box

# ─── Configuración ────────────────────────────────────────────────────────────
DATOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos")
ARCHIVO_PALETAS = os.path.join(DATOS_DIR, "paletas.json")

# Definición de los 4 datasets de Natural Earth
DATASETS = {
    "estados": {
        "nombre": "Estados/Provincias (contornos)",
        "archivo": "ne_10m_admin_1_states_provinces.zip",
        "url": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip",
        "tipo": "poligono",
    },
    "ciudades": {
        "nombre": "Ciudades/Localidades (puntos)",
        "archivo": "ne_10m_populated_places.zip",
        "url": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip",
        "tipo": "punto",
    },
    "paises": {
        "nombre": "Países (fronteras)",
        "archivo": "ne_10m_admin_0_countries.zip",
        "url": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip",
        "tipo": "poligono",
    },
    "carreteras": {
        "nombre": "Carreteras principales",
        "archivo": "ne_10m_roads.zip",
        "url": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_roads.zip",
        "tipo": "linea",
    },
}

# Valores por defecto para la Península de Baja California
LAT_MIN_DEFAULT = 22.0
LAT_MAX_DEFAULT = 33.0
LON_MIN_DEFAULT = -120.0
LON_MAX_DEFAULT = -108.0


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNCIONES DE DESCARGA
# ═══════════════════════════════════════════════════════════════════════════════

def descargar_dataset(clave):
    """Descarga un dataset específico si no existe localmente."""
    ds = DATASETS[clave]
    ruta = os.path.join(DATOS_DIR, ds["archivo"])

    if os.path.exists(ruta):
        tamaño = os.path.getsize(ruta) / (1024 * 1024)
        print(f"  ✅ {ds['nombre']}: encontrado ({tamaño:.1f} MB)")
        return ruta

    os.makedirs(DATOS_DIR, exist_ok=True)
    print(f"  ⬇️  Descargando {ds['nombre']}...")
    print(f"      URL: {ds['url']}")

    try:
        import urllib.request
        urllib.request.urlretrieve(ds["url"], ruta)
        tamaño = os.path.getsize(ruta) / (1024 * 1024)
        print(f"  ✅ Descarga completada ({tamaño:.1f} MB)")
    except Exception as e:
        print(f"  ❌ Error al descargar {ds['nombre']}: {e}")
        if os.path.exists(ruta):
            os.remove(ruta)
        return None

    return ruta


def descargar_datasets_seleccionados(seleccion):
    """Descarga todos los datasets seleccionados."""
    print("=" * 60)
    print("  VERIFICANDO / DESCARGANDO DATOS")
    print("=" * 60)
    print(f"  Fuente: Natural Earth (naturalearthdata.com)")
    print("")

    rutas = {}
    for clave in seleccion:
        ruta = descargar_dataset(clave)
        if ruta:
            rutas[clave] = ruta
        else:
            print(f"  ⚠️  No se pudo obtener: {DATASETS[clave]['nombre']}")

    print("")
    return rutas


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNCIONES DE SELECCIÓN (USUARIO)
# ═══════════════════════════════════════════════════════════════════════════════

def pedir_datasets():
    """Permite al usuario elegir qué datasets incluir en el mapa."""
    print("=" * 60)
    print("  DATASETS DISPONIBLES (Natural Earth 1:10m)")
    print("=" * 60)
    print("")

    claves = list(DATASETS.keys())
    for i, clave in enumerate(claves, 1):
        ds = DATASETS[clave]
        marcado = "●" if clave == "estados" else "○"
        print(f"  {i}. [{marcado}] {ds['nombre']}")

    print("")
    print("  El dataset 1 (Estados) siempre se incluye como base.")
    print("  Escribe los números adicionales separados por coma.")
    print("  Ejemplo: 2,3 para agregar Ciudades y Países.")
    print("  Presiona ENTER para solo usar Estados.")
    print("-" * 60)

    entrada = input("  Datasets adicionales [solo 1]: ").strip()

    seleccion = ["estados"]  # siempre incluido

    if entrada:
        for parte in entrada.replace(" ", "").split(","):
            try:
                idx = int(parte) - 1
                if 0 <= idx < len(claves):
                    clave = claves[idx]
                    if clave not in seleccion:
                        seleccion.append(clave)
                else:
                    print(f"  ⚠️  Número {parte} fuera de rango, ignorado.")
            except ValueError:
                print(f"  ⚠️  '{parte}' no es un número válido, ignorado.")

    print(f"\n  📦 Datasets seleccionados:")
    for clave in seleccion:
        print(f"     ✓ {DATASETS[clave]['nombre']}")
    print("")

    return seleccion


def cargar_paletas():
    """Carga las paletas de colores desde el archivo JSON."""
    if not os.path.exists(ARCHIVO_PALETAS):
        print(f"  ⚠️  No se encontró: {ARCHIVO_PALETAS}")
        return [paleta_por_defecto()]

    try:
        with open(ARCHIVO_PALETAS, "r", encoding="utf-8") as f:
            data = json.load(f)
        paletas = data.get("paletas", [])
        if not paletas:
            return [paleta_por_defecto()]
        print(f"  ✅ Se cargaron {len(paletas)} paletas desde paletas.json\n")
        return paletas
    except Exception as e:
        print(f"  ❌ Error al leer paletas: {e}")
        return [paleta_por_defecto()]


def paleta_por_defecto():
    """Retorna la paleta clásica como fallback."""
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
    """Muestra las paletas disponibles y permite elegir una."""
    print("=" * 60)
    print("  PALETAS DE COLORES")
    print("=" * 60)
    print("")

    for i, p in enumerate(paletas, 1):
        nombre = p.get("nombre", f"Paleta {i}")
        print(f"  {i}. {nombre}")

    print("")
    print("-" * 60)
    entrada = input(f"  Elige una paleta [1]: ").strip()

    if entrada == "":
        seleccion = 0
    else:
        try:
            seleccion = int(entrada) - 1
        except ValueError:
            seleccion = 0

    if seleccion < 0 or seleccion >= len(paletas):
        seleccion = 0

    elegida = paletas[seleccion]
    print(f"\n  🎨 Paleta: {elegida.get('nombre', 'Sin nombre')}\n")
    return elegida


def pedir_coordenadas():
    """Pide al usuario las coordenadas de latitud y longitud."""
    print("=" * 60)
    print("  ÁREA DEL MAPA")
    print("=" * 60)
    print(f"  Valores por defecto (Península de Baja California):")
    print(f"    Lat: {LAT_MIN_DEFAULT}° a {LAT_MAX_DEFAULT}°")
    print(f"    Lon: {LON_MIN_DEFAULT}° a {LON_MAX_DEFAULT}°")
    print("  Presiona ENTER para valores por defecto.")
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
#  FUNCIONES DE CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════════════════════

def cargar_estados(ruta, lat_min, lat_max, lon_min, lon_max):
    """Carga y filtra los estados de Baja California."""
    print("  Cargando estados...")
    gdf = gpd.read_file(f"zip://{ruta}")

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

    print(f"    Estados: {list(baja['name'].values)}")
    return baja


def cargar_ciudades(ruta, lat_min, lat_max, lon_min, lon_max):
    """Carga ciudades dentro del área seleccionada."""
    print("  Cargando ciudades...")
    gdf = gpd.read_file(f"zip://{ruta}")

    # Filtrar por el bounding box del área
    area = box(lon_min, lat_min, lon_max, lat_max)
    ciudades = gdf[gdf.geometry.within(area)].copy()

    # Intentar filtrar solo México si hay columna adecuada
    if "SOV0NAME" in ciudades.columns:
        ciudades_mx = ciudades[ciudades["SOV0NAME"] == "Mexico"]
        if not ciudades_mx.empty:
            ciudades = ciudades_mx
    elif "ADM0NAME" in ciudades.columns:
        ciudades_mx = ciudades[ciudades["ADM0NAME"] == "Mexico"]
        if not ciudades_mx.empty:
            ciudades = ciudades_mx

    print(f"    Ciudades encontradas: {len(ciudades)}")
    if len(ciudades) > 0 and "NAME" in ciudades.columns:
        nombres = sorted(ciudades["NAME"].tolist())
        print(f"    Nombres: {', '.join(nombres[:15])}" +
              (f" ... (+{len(nombres)-15} más)" if len(nombres) > 15 else ""))
    return ciudades


def cargar_paises(ruta, lat_min, lat_max, lon_min, lon_max):
    """Carga fronteras de países que intersectan con el área."""
    print("  Cargando países...")
    gdf = gpd.read_file(f"zip://{ruta}")

    # Filtrar México y Estados Unidos (vecinos de la península)
    paises_interes = ["Mexico", "United States of America"]
    if "ADMIN" in gdf.columns:
        paises = gdf[gdf["ADMIN"].isin(paises_interes)].copy()
    elif "NAME" in gdf.columns:
        paises = gdf[gdf["NAME"].isin(paises_interes)].copy()
    else:
        # Filtrar por bounding box
        area = box(lon_min, lat_min, lon_max, lat_max)
        paises = gdf[gdf.geometry.intersects(area)].copy()

    print(f"    Países cargados: {len(paises)}")
    return paises


def cargar_carreteras(ruta, lat_min, lat_max, lon_min, lon_max):
    """Carga carreteras dentro del área seleccionada."""
    print("  Cargando carreteras...")
    gdf = gpd.read_file(f"zip://{ruta}")

    # Filtrar por bounding box
    area = box(lon_min, lat_min, lon_max, lat_max)
    carreteras = gdf[gdf.geometry.intersects(area)].copy()

    print(f"    Segmentos de carretera: {len(carreteras)}")
    return carreteras


# ═══════════════════════════════════════════════════════════════════════════════
#  GENERACIÓN DEL MAPA
# ═══════════════════════════════════════════════════════════════════════════════

def generar_mapa(datos, lat_min, lat_max, lon_min, lon_max, paleta, seleccion):
    """Genera el mapa con todos los datasets seleccionados."""

    c = paleta  # alias corto

    # Calcular proporciones
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

    # ─── CAPA 1: Países (fondo, si está seleccionado) ─────────────────────
    if "paises" in datos and datos["paises"] is not None:
        paises = datos["paises"]
        # Dibujar como fondo suave
        paises.plot(
            ax=ax,
            color=c.get("relleno_tierra", "#f5e6ca"),
            edgecolor=c.get("contorno", "#1a3c6e"),
            linewidth=0.5,
            alpha=0.3
        )

    # ─── CAPA 2: Estados (siempre presente) ───────────────────────────────
    baja = datos["estados"]
    peninsula_unida = unary_union(baja.geometry)

    # Relleno
    baja.plot(
        ax=ax,
        color=c.get("relleno_tierra", "#f5e6ca"),
        edgecolor="none",
        alpha=0.8
    )

    # Contorno unificado
    gpd.GeoSeries([peninsula_unida]).plot(
        ax=ax,
        facecolor="none",
        edgecolor=c.get("contorno", "#1a3c6e"),
        linewidth=1.5,
        alpha=0.9
    )

    # División entre estados
    baja.boundary.plot(
        ax=ax,
        edgecolor=c.get("division_estados", "#cc3333"),
        linewidth=1.0,
        linestyle="--",
        alpha=0.6
    )

    # Etiquetas de estados
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

    # ─── CAPA 3: Carreteras (si está seleccionado) ────────────────────────
    if "carreteras" in datos and datos["carreteras"] is not None:
        carreteras = datos["carreteras"]
        if not carreteras.empty:
            carreteras.plot(
                ax=ax,
                color=c.get("division_estados", "#cc3333"),
                linewidth=0.8,
                alpha=0.5
            )

    # ─── CAPA 4: Ciudades (si está seleccionado) ──────────────────────────
    if "ciudades" in datos and datos["ciudades"] is not None:
        ciudades = datos["ciudades"]
        if not ciudades.empty:
            # Determinar columna de nombre
            col_nombre = "NAME" if "NAME" in ciudades.columns else "name"
            col_pop = None
            for candidato in ["POP_MAX", "POP_MIN", "pop_max", "pop_min"]:
                if candidato in ciudades.columns:
                    col_pop = candidato
                    break

            # Dibujar puntos
            ciudades.plot(
                ax=ax,
                color=c.get("indicador_norte", "#1a3c6e"),
                markersize=20,
                alpha=0.8,
                edgecolor=c.get("texto_stroke", "#ffffff"),
                linewidth=0.5,
                zorder=5
            )

            # Etiquetas de ciudades
            for idx, row in ciudades.iterrows():
                nombre = row.get(col_nombre, "")
                if not nombre:
                    continue
                x = row.geometry.x
                y = row.geometry.y

                # Tamaño de fuente según población
                fontsize = 7
                if col_pop and row.get(col_pop, 0):
                    pop = row[col_pop]
                    if pop > 500000:
                        fontsize = 10
                    elif pop > 100000:
                        fontsize = 9
                    elif pop > 50000:
                        fontsize = 8

                ax.annotate(
                    nombre,
                    xy=(x, y),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=fontsize,
                    color=c.get("texto_etiquetas", "#1a1a1a"),
                    path_effects=[
                        pe.withStroke(
                            linewidth=2,
                            foreground=c.get("texto_stroke", "#ffffff")
                        )
                    ],
                    zorder=6
                )

    # ─── Configurar límites ───────────────────────────────────────────────
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)

    # ─── Título ───────────────────────────────────────────────────────────
    ax.set_title(
        "Península de Baja California",
        color=c.get("titulo", "#1a3c6e"),
        fontsize=20,
        fontweight="bold",
        pad=20,
        fontfamily="sans-serif"
    )

    # Subtítulo con datasets activos
    capas_activas = [DATASETS[k]["nombre"].split("(")[0].strip() for k in seleccion]
    subtitulo = "Natural Earth 1:10m — Capas: " + ", ".join(capas_activas)
    ax.text(
        0.5, 1.02, subtitulo,
        transform=ax.transAxes, ha="center",
        fontsize=8, color=c.get("subtitulo", "#666666"), style="italic"
    )

    # ─── Ejes y decoración ────────────────────────────────────────────────
    ax.set_xlabel("Longitud", color=c.get("ejes_texto", "#333333"), fontsize=10)
    ax.set_ylabel("Latitud", color=c.get("ejes_texto", "#333333"), fontsize=10)
    ax.tick_params(colors=c.get("ejes_ticks", "#444444"), labelsize=8)

    for spine in ax.spines.values():
        spine.set_edgecolor(c.get("ejes_bordes", "#cccccc"))
        spine.set_linewidth(0.5)

    ax.grid(
        True,
        alpha=c.get("cuadricula_alpha", 0.3),
        color=c.get("cuadricula", "#cccccc"),
        linestyle="-", linewidth=0.5
    )

    ax.text(
        0.95, 0.02, "Proyección: WGS84 (EPSG:4326)",
        transform=ax.transAxes, ha="right",
        fontsize=7, color=c.get("texto_info", "#777777")
    )

    # Indicador del norte
    color_norte = c.get("indicador_norte", "#1a3c6e")
    ax.annotate("N", xy=(0.95, 0.95), xycoords="axes fraction",
                fontsize=14, fontweight="bold", color=color_norte,
                ha="center", va="center")
    ax.annotate("↑", xy=(0.95, 0.92), xycoords="axes fraction",
                fontsize=18, color=color_norte, ha="center", va="center")

    # Área mostrada
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
    print(f"     Paleta: {c.get('nombre', 'Sin nombre')}")
    print(f"     Capas: {', '.join(capas_activas)}")
    print(f"     Área: Lat [{lat_min}°, {lat_max}°]  Lon [{lon_min}°, {lon_max}°]")
    print("=" * 60)

    plt.show()
    print("\n¡Listo! El mapa se ha generado exitosamente.")


# ═══════════════════════════════════════════════════════════════════════════════
#  PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   DIBUJA - GENERADOR DE MAPAS BAJA CALIFORNIA            ║")
    print("║   Fuente: Natural Earth (naturalearthdata.com)            ║")
    print("║   4 datasets disponibles con selección de capas           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("")

    # Paso 1: Elegir datasets
    seleccion = pedir_datasets()

    # Paso 2: Descargar los datasets necesarios
    rutas = descargar_datasets_seleccionados(seleccion)

    # Paso 3: Elegir paleta
    paletas = cargar_paletas()
    paleta = pedir_paleta(paletas)

    # Paso 4: Elegir área
    lat_min, lat_max, lon_min, lon_max = pedir_coordenadas()

    # Paso 5: Cargar datos
    print("=" * 60)
    print("  CARGANDO DATOS GEOGRÁFICOS")
    print("=" * 60)

    datos_cargados = {}

    # Siempre cargar estados
    if "estados" in rutas:
        datos_cargados["estados"] = cargar_estados(
            rutas["estados"], lat_min, lat_max, lon_min, lon_max
        )

    # Cargar datasets opcionales
    if "ciudades" in rutas:
        datos_cargados["ciudades"] = cargar_ciudades(
            rutas["ciudades"], lat_min, lat_max, lon_min, lon_max
        )

    if "paises" in rutas:
        datos_cargados["paises"] = cargar_paises(
            rutas["paises"], lat_min, lat_max, lon_min, lon_max
        )

    if "carreteras" in rutas:
        datos_cargados["carreteras"] = cargar_carreteras(
            rutas["carreteras"], lat_min, lat_max, lon_min, lon_max
        )

    print("")

    # Paso 6: Generar mapa
    generar_mapa(datos_cargados, lat_min, lat_max, lon_min, lon_max, paleta, seleccion)
