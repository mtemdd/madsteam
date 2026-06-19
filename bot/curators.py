"""
curators.py
Aplica las reglas de negocio acordadas con Mate para decidir qué juegos
van en cada sección de la página. Combina datos de data_sources.py.
"""

import time
from datetime import datetime, timedelta
import data_sources as ds

# Lista fija de juegos del stream — Mate la actualiza acá cuando cambia.
# Formato: appid de Steam (se puede sacar de la URL de la tienda).
# Lista fija de juegos del stream — Mate la actualiza acá cuando cambia.
# Formato: appid de Steam (se puede sacar de la URL de la tienda).
# VACÍA por ahora -- esperando la lista real de Mate.
STREAM_GAMES_APPIDS = []

# Lista fija de juegos ANUNCIADOS para futuros streams (agenda).
# Mate la actualiza acá cuando anuncia algo nuevo. Puede quedar vacía.
UPCOMING_STREAM_GAMES_APPIDS = []

# Wishlist personal de Mate (de la memoria del proyecto) — se usa para Recomendaciones
WISHLIST_APPIDS = {
    "Hades": 1145360,
    "Cuphead": 268910,
    "Stardew Valley": 413150,
    "DOOM": 379720,
    "GTA V": 271590,
    "Red Dead Redemption 2": 1174180,
    "Dispatch": 2592160,
}

# Géneros/gustos conocidos para armar Recomendaciones
GENEROS_PREFERIDOS = ["Roguelike", "Sandbox", "Simulation", "Action", "Adventure"]


def build_general_offers(max_items=20):
    """
    Ofertas Generales: juegos en descuento (cualquier %) que cumplen
    el filtro de calidad (reseñas Muy positivas o mejor).
    """
    deals = ds.itad_current_deals(limit=250)
    gids = [d["gid"] for d in deals]
    appid_map = ds.itad_gid_to_appid(gids)

    results = []
    for deal in deals:
        appid = appid_map.get(deal["gid"])
        if not appid:
            continue
        if not ds.is_good_game(appid):
            continue
        details = ds.steam_app_details(appid)
        if not details:
            continue
        results.append(_merge_card(appid, details, deal))
        if len(results) >= max_items:
            break
        time.sleep(0.05)
    return results


def build_historic_lows(max_items=20):
    """
    Mínimos Históricos: juego en su precio más bajo histórico + reseñas
    Muy positivas o mejor.
    """
    deals = ds.itad_current_deals(limit=250)
    gids = [d["gid"] for d in deals]
    overview = ds.itad_price_overview(gids)
    appid_map = ds.itad_gid_to_appid(gids)

    results = []
    for deal in deals:
        gid = deal["gid"]
        ov = overview.get(gid, {})
        if not ov.get("is_historic_low"):
            continue
        appid = appid_map.get(gid)
        if not appid or not ds.is_good_game(appid):
            continue
        details = ds.steam_app_details(appid)
        if not details:
            continue
        card = _merge_card(appid, details, deal)
        card["historic"] = True
        results.append(card)
        if len(results) >= max_items:
            break
        time.sleep(0.05)
    return results


def build_upcoming_gems(candidate_appids, max_items=20):
    """
    Próximas Joyitas: lanzamientos recientes con muy buenas reseñas,
    con o sin descuento. candidate_appids es una lista que se arma
    a mano (no hay forma automática confiable de "lo nuevo y bueno"
    sin una fuente curada externa).
    """
    results = []
    for appid in candidate_appids:
        if not ds.is_good_game(appid):
            continue
        details = ds.steam_app_details(appid)
        if not details:
            continue
        gid = ds.itad_lookup_by_appid(appid)
        overview = ds.itad_price_overview([gid]) if gid else {}
        price_info = overview.get(gid, {"price_new": None, "discount": 0})
        card = _merge_card(appid, details, {
            "price_new": price_info.get("price_new"),
            "price_old": price_info.get("price_old"),
            "discount": price_info.get("discount") or 0,
            "url": f"https://store.steampowered.com/app/{appid}",
        })
        results.append(card)
        if len(results) >= max_items:
            break
        time.sleep(0.05)
    return results


def build_recommendations(max_items=20):
    """
    Recomendaciones: juegos en oferta que matchean los géneros/gustos
    conocidos de Mate.
    """
    deals = ds.itad_current_deals(limit=250)
    gids = [d["gid"] for d in deals]
    appid_map = ds.itad_gid_to_appid(gids)

    results = []
    for deal in deals:
        appid = appid_map.get(deal["gid"])
        if not appid:
            continue
        details = ds.steam_app_details(appid)
        if not details:
            continue
        if not any(g in details["tags"] for g in GENEROS_PREFERIDOS):
            continue
        if not ds.is_good_game(appid):
            continue
        results.append(_merge_card(appid, details, deal))
        if len(results) >= max_items:
            break
        time.sleep(0.05)
    return results


def build_trending(candidate_appids, max_items=20):
    """
    Tendencias: ordenado por jugadores concurrentes ahora mismo.
    candidate_appids: pool de juegos populares sobre los que medimos
    (no existe un "top global" público sin scraping de SteamDB).
    """
    scored = []
    for appid in candidate_appids:
        players = ds.steam_concurrent_players(appid)
        if players is None:
            continue
        scored.append((appid, players))
        time.sleep(0.05)
    scored.sort(key=lambda x: x[1], reverse=True)

    results = []
    for appid, players in scored[:max_items]:
        details = ds.steam_app_details(appid)
        if not details:
            continue
        gid = ds.itad_lookup_by_appid(appid)
        overview = ds.itad_price_overview([gid]) if gid else {}
        price_info = overview.get(gid, {})
        card = _merge_card(appid, details, {
            "price_new": price_info.get("price_new"),
            "price_old": price_info.get("price_old"),
            "discount": price_info.get("discount") or 0,
            "url": f"https://store.steampowered.com/app/{appid}",
        })
        card["players"] = players
        results.append(card)
    return results


def build_stream_games():
    """
    Juegos del Stream: lista fija definida por Mate. Siempre aparecen,
    con o sin descuento.
    """
    return _build_fixed_list(STREAM_GAMES_APPIDS)


def build_upcoming_stream_games():
    """
    Próximos en stream: agenda de lo que Mate anunció para streams futuros.
    """
    return _build_fixed_list(UPCOMING_STREAM_GAMES_APPIDS)


def _build_fixed_list(appids):
    results = []
    for appid in appids:
        details = ds.steam_app_details(appid)
        if not details:
            continue
        gid = ds.itad_lookup_by_appid(appid)
        overview = ds.itad_price_overview([gid]) if gid else {}
        price_info = overview.get(gid, {})
        card = _merge_card(appid, details, {
            "price_new": price_info.get("price_new"),
            "price_old": price_info.get("price_old"),
            "discount": price_info.get("discount") or 0,
            "url": f"https://store.steampowered.com/app/{appid}",
        })
        results.append(card)
        time.sleep(0.05)
    return results


def build_publisher_deals(publisher_names, min_games=2, max_publishers=4):
    """
    Ofertas de Creadores: detecta qué editoras de la lista candidata
    tienen varios juegos en oferta ahora, priorizando las mejor reseñadas.
    publisher_names: lista de editoras candidatas a chequear (no hay forma
    de "descubrir automáticamente todas las editoras con evento" sin
    iterar sobre el catálogo completo, así que se mantiene una lista
    candidata razonable y se filtra cuál tiene oferta activa real).
    """
    deals = ds.itad_current_deals(limit=200)
    gids = [d["gid"] for d in deals]
    appid_map = ds.itad_gid_to_appid(gids)

    by_publisher = {}
    for deal in deals:
        appid = appid_map.get(deal["gid"])
        if not appid:
            continue
        details = ds.steam_app_details(appid)
        if not details or not details.get("publisher"):
            continue
        pub = details["publisher"]
        if pub not in publisher_names:
            continue
        if not ds.is_good_game(appid):
            continue
        card = _merge_card(appid, details, deal)
        by_publisher.setdefault(pub, []).append(card)
        time.sleep(0.05)

    # Quedarse con las editoras que tienen suficientes juegos en oferta
    qualified = {p: games for p, games in by_publisher.items() if len(games) >= min_games}
    # Ordenar por cantidad de ofertas y tomar las top N
    sorted_pubs = sorted(qualified.items(), key=lambda x: len(x[1]), reverse=True)
    return sorted_pubs[:max_publishers]


def _merge_card(appid, details, deal):
    """Combina datos de Steam + ITAD en la estructura que usa html_builder.py"""
    price_new = deal.get("price_new")
    price_old = deal.get("price_old")
    discount = deal.get("discount") or 0
    return {
        "appid": appid,
        "title": details["title"],
        "cover": details["cover"],
        "header": details["header"],
        "desc": details["desc"],
        "tags": details["tags"],
        "priceOld": price_old if price_old is not None else price_new,
        "priceNew": price_new,
        "discount": -abs(discount) if discount else 0,
        "historic": False,
        "url": deal.get("url") or f"https://store.steampowered.com/app/{appid}",
    }
