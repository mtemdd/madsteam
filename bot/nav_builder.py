"""
Genera el bloque <nav> consistente para todas las páginas del sitio.
Uso: from nav_builder import build_nav; build_nav("ofertas")
"""

SECTIONS = ["ofertas", "recomendaciones", "stream", "creadores"]

def build_nav(active_section):
    def item(key, label, href, sub_items):
        active_cls = " active" if key == active_section else ""
        subs = "\n        ".join(
            f'<a href="{s_href}">{s_label}</a>' for s_label, s_href in sub_items
        )
        return f'''    <li class="nav-item">
      <a href="{href}" class="{active_cls.strip()}">{label} <span class="nav-caret">▾</span></a>
      <div class="nav-dropdown">
        <div class="nav-dropdown-inner">
        {subs}
        </div>
      </div>
    </li>'''

    items = [
        item("ofertas", "Ofertas", "index.html", [
            ("Descuentos generales", "index.html"),
            ("Mínimos históricos", "minimos-historicos.html"),
            ("Próximas joyitas", "proximas-joyitas.html"),
        ]),
        item("recomendaciones", "Recomendaciones", "recomendaciones.html", [
            ("Para vos", "recomendaciones.html"),
            ("Juegos en tendencia", "recomendaciones.html#tendencias"),
        ]),
        item("stream", "Juegos del Stream", "stream.html", [
            ("En el canal ahora", "stream.html"),
            ("Próximos en stream", "stream.html#proximos"),
        ]),
        item("creadores", "Ofertas de Creadores", "creadores.html", [
            ("Por empresa", "creadores.html"),
        ]),
    ]

    nav = f'''<nav class="topnav">
  <a href="index.html" class="brand"><span class="mad">MAD</span><span class="steam">STEAM</span></a>
  <ul class="nav-links">
{chr(10).join(items)}
  </ul>
  <span class="nav-meta">ACTUALIZADO 19.06.2026</span>
</nav>'''
    return nav

if __name__ == "__main__":
    print(build_nav("ofertas"))
