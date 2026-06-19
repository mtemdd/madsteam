"""
update_site.py
Script principal — el robot diario corre esto.
Junta datos reales de Steam/ITAD, aplica las reglas de curaduría,
y reescribe los 6 archivos HTML del sitio (sin tocar styles.css ni el diseño).

Uso:
    python update_site.py

Variables de entorno requeridas:
    ITAD_API_KEY
    STEAM_API_KEY (opcional, solo afecta la sección de tendencias)
"""

import os
import sys
import curators
import html_builder

# Carpeta raíz del sitio (donde están index.html, styles.css, etc.)
# Los HTML viven en la raíz del repositorio, junto a este script en bot/
SITE_DIR = os.path.join(os.path.dirname(__file__), "..")

# Pool de candidatos para "Próximas Joyitas" — lista curada a mano,
# ya que no hay forma 100% automática de saber "lo nuevo y bueno" sin
# una fuente externa curada. Se puede ir actualizando con el tiempo.
UPCOMING_CANDIDATES_APPIDS = [
    2592160,   # Dispatch
    1030300,   # Hollow Knight: Silksong
    2767030,   # Marvel Rivals
    2050650,   # Resident Evil Requiem
    1888160,   # Clair Obscur: Expedition 33
    2379780,   # Balatro (DLC/expansiones)
    1933980,   # Split Fiction
    1903340,   # Monster Hunter Wilds
    2358720,   # Black Myth: Wukong
    1245620,   # Elden Ring (Shadow of the Erdtree referencia)
]

# Pool de candidatos para medir tendencias (jugadores concurrentes)
TRENDING_CANDIDATES_APPIDS = [
    1174180,   # Red Dead Redemption 2
    379720,    # DOOM
    730,       # CS2
    570,       # Dota 2
    1245620,   # Elden Ring
    1091500,   # Cyberpunk 2077
    1086940,   # Baldur's Gate 3
    271590,    # GTA V
    1938090,   # Call of Duty
    578080,    # PUBG
    252490,    # Rust
    1599340,   # Lost Ark
    1203220,   # NARAKA: BLADEPOINT
    1172470,   # Apex Legends
    359550,    # Rainbow Six Siege
    1085660,   # Destiny 2
    230410,    # Warframe
    582010,    # Monster Hunter World
    1593500,   # God of War
    1888930,   # The Last of Us Part I
]

# Editoras candidatas a chequear para "Ofertas de Creadores"
PUBLISHER_CANDIDATES = [
    "Square Enix",
    "Bethesda Softworks",
    "SEGA",
    "Capcom",
    "Devolver Digital",
    "2K",
]


def main():
    print("=== Actualizando MADSTEAM ===")

    print("\n[1/7] Ofertas Generales...")
    general_offers = curators.build_general_offers()
    print(f"  -> {len(general_offers)} juegos encontrados")

    print("\n[2/7] Mínimos Históricos...")
    historic_lows = curators.build_historic_lows()
    print(f"  -> {len(historic_lows)} juegos encontrados")

    print("\n[3/7] Próximas Joyitas...")
    upcoming = curators.build_upcoming_gems(UPCOMING_CANDIDATES_APPIDS)
    print(f"  -> {len(upcoming)} juegos encontrados")

    print("\n[4/7] Recomendaciones...")
    recommendations = curators.build_recommendations()
    print(f"  -> {len(recommendations)} juegos encontrados")

    print("\n[5/7] Tendencias...")
    trending = curators.build_trending(TRENDING_CANDIDATES_APPIDS)
    print(f"  -> {len(trending)} juegos encontrados")

    print("\n[6/7] Juegos del Stream...")
    stream_games = curators.build_stream_games()
    upcoming_stream = curators.build_upcoming_stream_games()
    print(f"  -> {len(stream_games)} juegos actuales, {len(upcoming_stream)} próximos")

    print("\n[7/7] Ofertas de Creadores...")
    publisher_deals = curators.build_publisher_deals(PUBLISHER_CANDIDATES)
    print(f"  -> {len(publisher_deals)} editoras encontradas")

    print("\nGenerando archivos HTML...")
    pages = {
        "index.html": html_builder.build_index_html(general_offers),
        "minimos-historicos.html": html_builder.build_minimos_historicos_html(historic_lows),
        "proximas-joyitas.html": html_builder.build_proximas_joyitas_html(upcoming),
        "recomendaciones.html": html_builder.build_recomendaciones_html(recommendations, trending),
        "stream.html": html_builder.build_stream_html(stream_games, upcoming_stream),
        "creadores.html": html_builder.build_creadores_html(publisher_deals),
    }

    os.makedirs(SITE_DIR, exist_ok=True)
    for filename, content in pages.items():
        path = os.path.join(SITE_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  -> {filename} actualizado")

    print("\n=== Listo ===")


if __name__ == "__main__":
    if not os.environ.get("ITAD_API_KEY"):
        print("ERROR: falta la variable de entorno ITAD_API_KEY", file=sys.stderr)
        sys.exit(1)
    main()
