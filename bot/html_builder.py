"""
html_builder.py
Genera los 6 archivos HTML del sitio, inyectando los datos reales
en el mismo diseño/estructura que ya fue aprobado por Mate.
No toca styles.css.
"""

import json
from datetime import datetime
from nav_builder import build_nav

TODAY = datetime.now().strftime("%d.%m.%Y")


def _cards_js(games):
    """Convierte una lista de dicts de juego a JS literal embebido."""
    return json.dumps(games, ensure_ascii=False, indent=2)


def _render_grid_script(var_name, container_id, games):
    return f"""
const {var_name} = {_cards_js(games)};

function renderGrid_{var_name}() {{
  const grid = document.getElementById('{container_id}');
  {var_name}.forEach(g => {{
    const card = document.createElement('a');
    card.className = 'game-card-link';
    card.href = g.url;
    card.target = '_blank';
    card.rel = 'noopener';

    const discountBadge = g.discount < 0
      ? `<span class="card-discount-badge">${{g.discount}}%</span>` : '';
    const historicBadge = g.historic
      ? `<span class="card-historic-badge">Mínimo histórico</span>` : '';
    const priceBlock = (g.discount < 0 && g.priceOld)
      ? `<span class="price-old">$${{g.priceOld.toFixed(2)}}</span><span class="price-new">$${{g.priceNew.toFixed(2)}}</span>`
      : `<span class="price-new">$${{(g.priceNew || 0).toFixed(2)}}</span>`;

    card.innerHTML = `
      <div class="game-card">
        <div class="card-inner">
          ${{discountBadge}}
          ${{historicBadge}}
          <img class="card-cover" src="${{g.cover}}" alt="${{g.title}}" loading="lazy">
          <div class="card-title-bar"><h3>${{g.title}}</h3></div>
        </div>
        <div class="expand-panel">
          <div class="expand-panel-inner">
            <img class="expand-header-img" src="${{g.header}}" alt="${{g.title}}">
            <p class="expand-desc">${{g.desc}}</p>
            <div class="expand-tags">${{g.tags.map(t => `<span class="tag">${{t}}</span>`).join('')}}</div>
            <div class="price-row">
              <div class="price-info">${{priceBlock}}</div>
              <span class="btn-steam">Ver en Steam</span>
            </div>
          </div>
        </div>
      </div>
    `;
    grid.appendChild(card);
  }});
}}
renderGrid_{var_name}();
"""


def build_page_shell(active_section, title, eyebrow, heading, subtitle, body_html):
    nav = build_nav(active_section)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — MADSTEAM</title>
<link rel="stylesheet" href="styles.css">
</head>
<body>

{nav}

<header class="section-header">
  <span class="eyebrow">{eyebrow}</span>
  <h1>{heading}</h1>
  <p>{subtitle}</p>
</header>

{body_html}

<footer class="footer">
  Datos actualizados automáticamente — fuente: Steam &amp; IsThereAnyDeal — última actualización {TODAY}
</footer>

</body>
</html>
"""


def build_index_html(general_offers):
    script = f"<script>{_render_grid_script('games', 'grid', general_offers)}</script>"
    body = f'<main class="game-grid" id="grid"></main>\n{script}'
    return build_page_shell(
        "ofertas", "Ofertas", "Zona 01 / Catálogo completo", "Ofertas Generales",
        "Juegos de buena reputación con descuento activo. Pasá el mouse para ver detalles y precio.",
        body,
    )


def build_minimos_historicos_html(historic_lows):
    script = f"<script>{_render_grid_script('games', 'grid', historic_lows)}</script>"
    body = f'<main class="game-grid" id="grid"></main>\n{script}'
    return build_page_shell(
        "ofertas", "Mínimos Históricos", "Zona 01b / Precio más bajo de la historia",
        "Mínimos Históricos",
        "Buenos juegos al precio más bajo que tuvieron jamás en Steam.",
        body,
    )


def build_proximas_joyitas_html(upcoming):
    script = f"<script>{_render_grid_script('games', 'grid', upcoming)}</script>"
    body = f'<main class="game-grid" id="grid"></main>\n{script}'
    return build_page_shell(
        "ofertas", "Próximas Joyitas", "Zona 01c / Radar de lanzamientos",
        "Próximas Joyitas",
        "Títulos recientes con muy buenas reseñas, con o sin descuento.",
        body,
    )


def build_recomendaciones_html(recommendations, trending):
    script1 = _render_grid_script('games', 'grid', recommendations)
    script2 = _render_grid_script('tendencias', 'grid-tendencias', trending)
    body = f"""<main class="game-grid" id="grid"></main>

<header class="section-header" id="tendencias" style="padding-top: 0;">
  <span class="eyebrow">En tendencia</span>
  <h1 style="font-size: clamp(24px, 4vw, 36px);">Lo que está jugando todo el mundo</h1>
</header>

<main class="game-grid" id="grid-tendencias"></main>

<script>
{script1}
{script2}
</script>"""
    return build_page_shell(
        "recomendaciones", "Recomendaciones", "Zona 02 / Curado para vos", "Recomendaciones",
        "Basado en tus gustos: roguelikes, sandbox, simulación y más.",
        body,
    )


def build_stream_html(stream_games, upcoming_stream_games=None):
    upcoming_stream_games = upcoming_stream_games or []

    if stream_games:
        script1 = _render_grid_script('games', 'grid', stream_games)
        body = f'<main class="game-grid" id="grid"></main>\n'
        games_script = f"<script>\n{script1}\n"
    else:
        body = '''<p style="padding: 0 48px 40px; color: var(--white-dim); font-family: var(--font-body);">
  Todavía no hay juegos cargados para esta sección.
</p>
'''
        games_script = "<script>\n"

    if upcoming_stream_games:
        script2 = _render_grid_script('proximos', 'grid-proximos', upcoming_stream_games)
        body += f"""
<header class="section-header" id="proximos" style="padding-top: 0;">
  <span class="eyebrow">Agenda</span>
  <h1 style="font-size: clamp(24px, 4vw, 36px);">Próximos en stream</h1>
</header>

<main class="game-grid" id="grid-proximos"></main>

{games_script}{script2}
</script>"""
    else:
        body += f"""
<header class="section-header" id="proximos" style="padding-top: 0;">
  <span class="eyebrow">Agenda</span>
  <h1 style="font-size: clamp(24px, 4vw, 36px);">Próximos en stream</h1>
</header>
<p style="padding: 0 48px 40px; color: var(--white-dim); font-family: var(--font-body);">
  Todavía no hay próximos juegos anunciados para el stream.
</p>

{games_script}
</script>"""

    return build_page_shell(
        "stream", "Juegos del Stream", "Zona 03 / El canal", "Juegos del Stream",
        "Lo que se juega en el canal, con su precio actual.",
        body,
    )


def build_creadores_html(publisher_deals):
    """publisher_deals: lista de tuplas (nombre_editora, [juegos])"""
    blocks_html = []
    scripts = []
    for idx, (pub_name, games) in enumerate(publisher_deals):
        container_id = f"publisher-grid-{idx}"
        var_name = f"pub{idx}"
        steam_publisher_url = f"https://store.steampowered.com/search/?publisher={pub_name.replace(' ', '+')}"
        blocks_html.append(f"""
<section class="publisher-block">
  <div class="publisher-header">
    <a class="publisher-logo-link" href="{steam_publisher_url}" target="_blank" rel="noopener">
      <div style="padding: 14px 18px; font-family: var(--font-display); font-weight: 800;">{pub_name}</div>
    </a>
    <div class="publisher-info">
      <h2>{pub_name}</h2>
      <p>{len(games)} juegos en oferta — tocá el logo para ver todo el catálogo</p>
    </div>
  </div>
  <div class="publisher-grid" id="{container_id}"></div>
</section>
""")
        scripts.append(_render_grid_script(var_name, container_id, games))

    body = "<main id='publishers'>" + "\n".join(blocks_html) + "</main>"
    body += "\n<script>\n" + "\n".join(scripts) + "\n</script>"

    return build_page_shell(
        "creadores", "Ofertas de Creadores", "Zona 04 / Editores y estudios",
        "Ofertas de Creadores",
        "Editoras con eventos de descuento activos esta semana.",
        body,
    )
