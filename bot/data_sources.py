"""
data_sources.py
Funciones para traer datos reales de Steam y IsThereAnyDeal (ITAD).
Todas las funciones devuelven estructuras de datos limpias en español,
listas para que html_builder.py las use.
"""

import os
import time
import requests

ITAD_API_KEY = os.environ.get("ITAD_API_KEY")
STEAM_API_KEY = os.environ.get("STEAM_API_KEY")

ITAD_BASE = "https://api.isthereanydeal.com"
STEAM_STORE_BASE = "https://store.steampowered.com/api"

# Reseñas mínimas para considerar "buen juego"
MIN_REVIEW_SCORE = 80          # % de reseñas positivas
MIN_REVIEW_COUNT = 1000        # cantidad mínima de reseñas para que el % sea confiable


def _itad_get(path, params=None):
    params = dict(params or {})
    params["key"] = ITAD_API_KEY
    r = requests.get(f"{ITAD_BASE}{path}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def _itad_post(path, body, params=None):
    params = dict(params or {})
    params["key"] = ITAD_API_KEY
    r = requests.post(f"{ITAD_BASE}{path}", params=params, json=body, timeout=20)
    r.raise_for_status()
    return r.json()


def itad_lookup_by_appid(appid):
    """
    Convierte un Steam appid al ID interno de ITAD (gid) usando el
    endpoint de lookup que acepta appid directamente.
    Devuelve None si no se encuentra el juego.
    """
    data = _itad_get("/games/lookup/v1", {"appid": appid})
    if not data.get("found"):
        return None
    game = data.get("game", {})
    return game.get("id")  # gid (UUID)


def itad_lookup_many_by_appid(appids):
    """Versión en lote: devuelve dict {appid: gid}."""
    out = {}
    for appid in appids:
        gid = itad_lookup_by_appid(appid)
        if gid:
            out[appid] = gid
        time.sleep(0.05)  # ser amable con el rate limit
    return out


def itad_current_deals(limit=200, offset=0):
    """
    Trae el listado de ofertas activas en Steam según ITAD.
    Devuelve lista de dicts: gid, title, precio actual, precio original, %descuento, url.
    NOTA: este endpoint NO devuelve el Steam appid directo; para conseguirlo
    hay que usar /lookup/shop/{shopId}/id/v1 en sentido inverso.

    El parámetro 'shops' espera una lista de IDs numéricos de tienda.
    61 = Steam dentro del catálogo de tiendas de ITAD.
    """
    body = {
        "country": "US",
        "offset": offset,
        "limit": limit,
        "shops": [61],
        "sort": "-cut",
    }
    r = requests.post(
        f"{ITAD_BASE}/deals/v2",
        params={"key": ITAD_API_KEY},
        json=body,
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    results = []
    for item in data.get("list", []):
        deal = item.get("deal", {})
        results.append({
            "gid": item.get("id"),
            "title": item.get("title"),
            "price_new": (deal.get("price") or {}).get("amount"),
            "price_old": (deal.get("regular") or {}).get("amount"),
            "discount": deal.get("cut"),
            "url": deal.get("url"),
        })
    return results


def itad_gid_to_appid(gids):
    """
    Resuelve gids de ITAD a Steam appids usando el lookup inverso
    /lookup/shop/{shopId}/id/v1 (shopId 61 = Steam).
    Devuelve dict {gid: appid}.

    La API puede devolver, para cada gid, ya sea un string único
    ("app/12345") o una lista de strings (["app/12345"]) -- se
    manejan ambos casos.
    """
    if not gids:
        return {}
    data = _itad_post("/lookup/shop/61/id/v1", list(gids))
    out = {}
    for gid, shop_id_raw in data.items():
        shop_id = shop_id_raw
        if isinstance(shop_id_raw, list):
            shop_id = shop_id_raw[0] if shop_id_raw else None
        if shop_id and isinstance(shop_id, str) and shop_id.startswith("app/"):
            try:
                out[gid] = int(shop_id.replace("app/", ""))
            except ValueError:
                continue
    return out


def itad_price_overview(gids):
    """
    Para una lista de gids, devuelve precio actual + mínimo histórico.
    """
    if not gids:
        return {}
    data = _itad_post("/games/overview/v2", list(gids), params={"country": "US"})
    out = {}
    for entry in data.get("prices", []):
        gid = entry.get("id")
        current = entry.get("current") or {}
        historic = entry.get("lowest") or {}
        cur_price = (current.get("price") or {}).get("amount")
        hist_price = (historic.get("price") or {}).get("amount")
        out[gid] = {
            "price_new": cur_price,
            "price_old": (current.get("regular") or {}).get("amount"),
            "discount": current.get("cut"),
            "historic_low": hist_price,
            "is_historic_low": (
                cur_price is not None
                and hist_price is not None
                and cur_price <= hist_price
            ),
        }
    return out


def steam_app_details(appid):
    """
    Trae descripción corta, imágenes (capsule/header) y datos básicos desde
    la Store API pública de Steam (no requiere key).
    """
    params = {"appids": appid, "l": "spanish", "cc": "ar"}
    r = requests.get(f"{STEAM_STORE_BASE}/appdetails", params=params, timeout=20)
    if r.status_code != 200:
        return None
    data = r.json()
    entry = data.get(str(appid), {})
    if not entry.get("success"):
        return None
    d = entry["data"]
    return {
        "title": d.get("name"),
        "desc": d.get("short_description"),
        "cover": f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg",
        "header": d.get("header_image"),
        "tags": [g["description"] for g in d.get("genres", [])][:3],
        "publisher": (d.get("publishers") or [None])[0],
        "release_date": d.get("release_date", {}).get("date"),
        "is_recent_release": False,  # se calcula aparte si hace falta
    }


def steam_app_reviews(appid):
    """
    Trae el % de reseñas positivas y la cantidad total, usando el endpoint
    público appreviews (no requiere key).
    """
    params = {"json": 1, "language": "all", "purchase_type": "all", "num_per_page": 0}
    r = requests.get(
        f"https://store.steampowered.com/appreviews/{appid}", params=params, timeout=20
    )
    if r.status_code != 200:
        return None
    data = r.json()
    summary = data.get("query_summary", {})
    total = summary.get("total_reviews", 0)
    positive = summary.get("total_positive", 0)
    score = round((positive / total) * 100) if total else 0
    return {
        "review_score": score,
        "review_count": total,
        "review_desc": summary.get("review_score_desc", ""),
    }


def is_good_game(appid):
    """
    Aplica la regla de calidad acordada: reseñas 'Muy positivas' o mejor,
    con volumen suficiente para ser confiable.
    """
    reviews = steam_app_reviews(appid)
    if reviews is None:
        return False
    return (
        reviews["review_count"] >= MIN_REVIEW_COUNT
        and reviews["review_score"] >= MIN_REVIEW_SCORE
    )


def steam_concurrent_players(appid):
    """Jugadores concurrentes ahora mismo (para la zona de tendencias)."""
    if not STEAM_API_KEY:
        return None
    params = {"appid": appid, "key": STEAM_API_KEY}
    r = requests.get(
        "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/",
        params=params, timeout=20
    )
    if r.status_code != 200:
        return None
    return r.json().get("response", {}).get("player_count")


def steam_featured_categories():
    """
    Trae las categorías destacadas de la home de Steam, incluyendo
    'specials' (ofertas), útil como fuente adicional de candidatos.
    """
    r = requests.get(f"{STEAM_STORE_BASE}/featuredcategories", params={"cc": "ar", "l": "spanish"}, timeout=20)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    print("ITAD_API_KEY set:", bool(ITAD_API_KEY))
    print("STEAM_API_KEY set:", bool(STEAM_API_KEY))
