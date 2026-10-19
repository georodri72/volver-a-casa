#!/usr/bin/env python3
"""Generates the bilingual static site into public/. Run: python3 build.py
No dependencies. Every factual statement on guide pages carries a source link."""
import os, html, hashlib, json

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
CHECKED = "2026-10-17"
SITE = os.environ.get("SITE_URL", "https://volver-a-casa-ak17.onrender.com")  # absolute URLs for hreflang/canonical

SRC = {
 "state": ("U.S. Department of State – El Salvador", "https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/ElSalvador.html"),
 "embassy": ("U.S. Embassy San Salvador – Travel Requirements", "https://sv.usembassy.gov/services/travel-requirements/"),
 "dgme": ("Dirección General de Migración y Extranjería – Preguntas", "https://www.migracion.gob.sv/control-migratorio-preguntas/"),
 "reglamento": ("Reglamento de la Ley Especial de Migración y Extranjería (Art. 21)", "https://www.sela.org/wp-content/uploads/2023/07/reglamento-de-la-ley-especial-de-migracion-y-extranjeria-el-salvador.pdf"),
 "tim": ("Diario El Salvador – eliminación de la Tarjeta Migratoria de Ingreso", "https://diarioelsalvador.com/depais/extranjeros-ya-no-cancelaran-12-por-ingresar-al-pais/649765"),
 "cepa": ("CEPA – Aeropuerto Internacional de El Salvador", "https://www.cepa.gob.sv/servicios-aeropuerto-internacional-de-el-salvador/"),
 "cepafaq": ("CEPA – Preguntas frecuentes", "https://www.cepa.gob.sv/preguntas-frecuentes/"),
 "fids": ("CEPA – Itinerario de vuelos (FIDS)", "https://itinerario.cepa.gob.sv/"),
 "vip": ("SIMPLE SV – Servicio VIP del aeropuerto (CEPA)", "https://simple.sv/tramite/solicitud-del-servicio-vip-en-el-aeropuerto-internacional-de-el-salvador/modalidad-unica"),
 "tsa": ("TSA – Liquids, Aerosols, and Gels Rule", "https://www.tsa.gov/travel/security-screening/liquids-aerosols-gels-rule"),
 "cbp": ("CBP – Prohibited and Restricted Items", "https://www.cbp.gov/travel/us-citizens/know-before-you-go/prohibited-and-restricted-items"),
 "cdc": ("CDC – Travelers' Health: El Salvador", "https://wwwnc.cdc.gov/travel/destinations/traveler/none/el-salvador"),
 "step": ("Smart Traveler Enrollment Program (STEP)", "https://step.state.gov/"),
 "dulles": ("Washington Dulles (MWAA) – Nonstop destinations", "https://www.flydulles.com/nonstop-destinations"),
 "reagan": ("Reagan National (MWAA) – Nonstop destinations", "https://www.flyreagan.com/nonstop-destinations"),
 "csj": ("Código de Trabajo de El Salvador, Art. 190 (Corte Suprema de Justicia)", "https://www.csj.gob.sv/wp-content/uploads/2021/06/11-Co%CC%81digo-de-Trabajo-de-El-Salvador-Di%CC%81as-de-asueto.pdf"),
 "expedia": ("Expedia – 2026 Air Hacks report", "https://www.expedia.com/newsroom/expedia-2026-air-hacks/"),
 "tpdocs": ("Travelpayouts – Aviasales Data API documentation", "https://support.travelpayouts.com/hc/en-us/articles/203956163-Aviasales-Data-API"),
 "avsfaq": ("Aviasales – How our service works", "https://www.aviasales.com/faq/how-our-service-works"),
}
# Official baggage pages for airlines that appear in our DC-SAL fare data (code -> name, url).
BAGGAGE = {
 "AV": ("Avianca", "https://www.avianca.com/es/informacion-y-ayuda/equipaje/"),
 "UA": ("United", "https://www.united.com/en/us/fly/baggage/checked-bags.html"),
 "AA": ("American", "https://www.aa.com/web/i18n/travel-info/baggage/checked-baggage-policy.html"),
 "CM": ("Copa", "https://www.copaair.com/en-us/travel-information/baggage-information/checked-baggage/"),
 "F9": ("Frontier", "https://www.flyfrontier.com/travel/travel-info/bag-options/"),
}
MON_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MON_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MONTH_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
MONTH_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
def fdate(iso, es, year=False):
    y, m, d = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
    return (f"{d} {MON_ES[m-1]}" if es else f"{MON_EN[m-1]} {d}") + (f" {y}" if year and es else (f", {y}" if year else ""))
def load_json(rel, default):
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), rel)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default
def load_history():
    rows = []
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "history.jsonl")) as f:
            rows = [json.loads(l) for l in f if l.strip()]
    except (OSError, ValueError):
        pass
    return rows

def cite(*keys, lang="en"):
    label = "Fuente" if lang == "es" else "Source"
    links = ", ".join(f'<a href="{SRC[k][1]}" rel="noopener" target="_blank">{html.escape(SRC[k][0])}</a>' for k in keys)
    return f'<span class="cite">{label}: {links}</span>'

# Top-10 Salvadoran-origin metros (ACS 2024 1-yr, B03001) -> airports we query.
# Must stay in sync with ORIGINS in scripts/refresh_fares.py.
METROS = [
 ("la", "Los Angeles", "Los Ángeles", ["LAX"]),
 ("dc", "Washington DC", "Washington DC", ["IAD", "DCA", "BWI"]),
 ("ny", "New York", "Nueva York", ["JFK", "EWR"]),
 ("hou", "Houston", "Houston", ["IAH", "HOU"]),
 ("dfw", "Dallas–Fort Worth", "Dallas–Fort Worth", ["DFW"]),
 ("sf", "SF Bay Area", "Área de la Bahía (SF)", ["SFO", "OAK", "SJC"]),
 ("ie", "Inland Empire", "Inland Empire", ["ONT"]),
 ("bos", "Boston", "Boston", ["BOS"]),
 ("mia", "Miami", "Miami", ["MIA", "FLL"]),
 ("atl", "Atlanta", "Atlanta", ["ATL"]),
]
_CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "airports.json")
with open(_CFG) as _f:
    ACTIVE = [c for c in json.load(_f)["active"]]  # shared with scripts/refresh_fares.py

AIRPORT_NAMES = {
 "LAX": "Los Angeles Intl", "IAD": "Washington Dulles", "DCA": "Reagan National", "BWI": "Baltimore/Washington",
 "JFK": "New York JFK", "EWR": "Newark Liberty", "IAH": "Houston Bush", "HOU": "Houston Hobby",
 "DFW": "Dallas/Fort Worth", "SFO": "San Francisco", "OAK": "Oakland", "SJC": "San José",
 "ONT": "Ontario", "BOS": "Boston Logan", "MIA": "Miami", "FLL": "Fort Lauderdale", "ATL": "Atlanta",
}

# Photos: Wikimedia Commons, licenses verified via the Commons API (extmetadata) on 2026-10-18.
PHOTOS = {
 "coatepeque": dict(title="Coatepeque Vista.jpg", author="JMRAFFi", license="CC BY 4.0",
     license_url="https://creativecommons.org/licenses/by/4.0/", src="https://commons.wikimedia.org/wiki/File:Coatepeque_Vista.jpg",
     en="Lake Coatepeque, Santa Ana", es="Lago de Coatepeque, Santa Ana", sizes=[640, 1024, 1600], ratio=(4, 3)),
 "santa-ana": dict(title="Laguna cratérica del Volcán de Santa Ana - El Salvador.jpg", author="Erneestoo", license="CC BY-SA 4.0",
     license_url="https://creativecommons.org/licenses/by-sa/4.0/", src="https://commons.wikimedia.org/wiki/File:Laguna_crat%C3%A9rica_del_Volc%C3%A1n_de_Santa_Ana_-_El_Salvador.jpg",
     en="Crater lagoon of the Santa Ana Volcano (Ilamatepec)", es="Laguna del cráter del volcán de Santa Ana (Ilamatepec)", sizes=[480, 800], ratio=(4, 3)),
 "suchitoto": dict(title="Calles de Suchitoto Agosto..JPG", author="ElmerGuevara", license="CC BY-SA 3.0",
     license_url="https://creativecommons.org/licenses/by-sa/3.0/", src="https://commons.wikimedia.org/wiki/File:Calles_de_Suchitoto_Agosto..JPG",
     en="Cobblestone street in Suchitoto", es="Calle empedrada en Suchitoto", sizes=[480, 800], ratio=(3, 2)),
 "playa": dict(title="Playa de El Salvador.jpg", author="Rodrigo var351", license="CC BY-SA 4.0",
     license_url="https://creativecommons.org/licenses/by-sa/4.0/", src="https://commons.wikimedia.org/wiki/File:Playa_de_El_Salvador.jpg",
     en="Pacific coast beach, El Salvador", es="Playa en la costa del Pacífico, El Salvador", sizes=[480, 800], ratio=(4, 3)),
}

def img(key, lang, depth, sizes_attr, cls="", eager=False):
    p = PHOTOS[key]; w0, h0 = p["ratio"]; big = p["sizes"][-1]
    srcset = ", ".join(f"{depth}img/{key}-{w}.webp {w}w" for w in p["sizes"])
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<img class="{cls}" src="{depth}img/{key}-{p["sizes"][0]}.webp" srcset="{srcset}" sizes="{sizes_attr}" '
            f'width="{big}" height="{big*h0//w0}" alt="{html.escape(p[lang])}" {load}>')

T = {
 "en": {
  "lang": "en", "other": "es", "other_label": "Español", "prefix": "",
  "site": "Volver a Casa", "tag": "Travel guide &amp; fare tracker for Salvadorans flying home to El Salvador (SAL)",
  "nav": [("index.html", "Fares"), ("entry.html", "Entry rules"), ("airport.html", "SAL airport"), ("bring.html", "What to bring"), ("tips.html", "Safety &amp; tips"), ("calendar.html", "Cheapest dates"), ("buying.html", "Buying tickets"), ("prices.html", "How prices work")],
  "disclaimer": f"Guide information checked {CHECKED} against the official sources linked on each page. Rules change: always confirm with the source and your airline before you travel. This site is independent and not affiliated with any government or airline.",
  "foot_links": [("prices.html", "How our prices work"), ("credits.html", "Photo credits")],
 },
 "es": {
  "lang": "es", "other": "en", "other_label": "English", "prefix": "es/",
  "site": "Volver a Casa", "tag": "Guía de viaje y rastreador de tarifas para salvadoreños que vuelan a casa (SAL)",
  "nav": [("index.html", "Tarifas"), ("entry.html", "Requisitos de ingreso"), ("airport.html", "Aeropuerto SAL"), ("bring.html", "Qué llevar"), ("tips.html", "Seguridad y consejos"), ("calendar.html", "Fechas baratas"), ("buying.html", "Comprar boletos"), ("prices.html", "Cómo funcionan los precios")],
  "disclaimer": f"Información de la guía verificada el {CHECKED} con las fuentes oficiales enlazadas en cada página. Las reglas cambian: confirme siempre con la fuente y con su aerolínea antes de viajar. Este sitio es independiente y no está afiliado a ningún gobierno ni aerolínea.",
  "foot_links": [("prices.html", "Cómo funcionan nuestros precios"), ("credits.html", "Créditos de fotos")],
 },
}

def asset_v(rel):
    """Short content hash so a deploy never serves new HTML with a CDN-cached old CSS/JS (Render edge s-maxage=300)."""
    with open(os.path.join(OUT, rel), "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]

def page(lang, fname, title, body, hero=None, lead=None):
    t = T[lang]
    depth = "../" if lang == "es" else ""
    other_href = ("../" if lang == "es" else "es/") + fname
    nav = "".join(f'<a href="{h}"{" aria-current=page" if h==fname else ""}>{l}</a>' for h, l in t["nav"])
    foot = " · ".join(f'<a href="{h}">{l}</a>' for h, l in t["foot_links"])
    skip = "Saltar al contenido" if lang == "es" else "Skip to content"
    preload = ""
    if hero == "home":
        p = PHOTOS["coatepeque"]
        preload = (f'<link rel="preload" as="image" type="image/webp" imagesrcset="' +
                   ", ".join(f"{depth}img/coatepeque-{w}.webp {w}w" for w in p["sizes"]) + '" imagesizes="100vw">')
    head_block = body if hero == "home" else f'<div class="pagehead"><div class="wrap"><h1>{title}</h1>{f"<p>{lead}</p>" if lead else ""}</div></div><main id="main" class="wrap prose">{body}</main>'
    if hero == "home":
        head_block = body
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · {t['site']}</title>
<meta name="description" content="{t['tag']}">
<meta name="theme-color" content="#0047AB">
<link rel="canonical" href="{SITE}/{t['prefix']}{'' if fname=='index.html' else fname}">
<link rel="alternate" hreflang="en" href="{SITE}/{'' if fname=='index.html' else fname}">
<link rel="alternate" hreflang="es" href="{SITE}/es/{'' if fname=='index.html' else fname}">
<link rel="alternate" hreflang="x-default" href="{SITE}/{'' if fname=='index.html' else fname}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%230047AB'/%3E%3Crect y='11' width='32' height='10' fill='%23fff'/%3E%3C/svg%3E">
{preload}
<link rel="stylesheet" href="{depth}assets/style.css?v={asset_v('assets/style.css')}">
</head>
<body>
<a class="skip" href="#main">{skip}</a>
<header class="site">
 <div class="wrap bar">
  <a class="brand" href="index.html"><span class="flag" aria-hidden="true"></span>{t['site']}</a>
  <a class="lang" href="{other_href}" hreflang="{t['other']}" lang="{t['other']}">{t['other_label']}</a>
 </div>
 <nav class="wrap nav" aria-label="{'Principal' if lang=='es' else 'Main'}">{nav}</nav>
</header>
{head_block}
<footer class="site">
 <div class="wrap">
  <p class="brandline"><span class="flag" aria-hidden="true"></span>{t['site']}</p>
  <p>{t['disclaimer']}</p>
  <p class="foot-links">{foot}</p>
 </div>
</footer>
</body>
</html>
"""

def ul(items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

def build():
    pages = {}
    for lang in ("en", "es"):
        es = lang == "es"
        depth = "../" if es else ""
        c = lambda *k: cite(*k, lang=lang)
        # ---------- HOME ----------
        metro_of = {code: (mid, ne, ns) for mid, ne, ns, codes in METROS for code in codes}
        active = [c for c in ACTIVE if c in metro_of]
        act_metros = [m for m in METROS if any(c in active for c in m[3])]
        single = len(act_metros) == 1
        chips = "".join(f'<button type="button" class="chip" data-metro="{mid}" aria-pressed="false">{html.escape(ne if not es else ns)}</button>' for mid, ne, ns, _ in act_metros)
        y = " y " if es else " and "
        codes_txt = y.join(", ".join(active[:-1]) and [", ".join(active[:-1]), active[-1]] or [active[-1]])
        names_txt = y.join(", ".join(f"{AIRPORT_NAMES[c]} ({c})" for c in active[:-1]) and [", ".join(f"{AIRPORT_NAMES[c]} ({c})" for c in active[:-1]), f"{AIRPORT_NAMES[active[-1]]} ({active[-1]})"] or [f"{AIRPORT_NAMES[active[-1]]} ({active[-1]})"])
        if single:
            mname = act_metros[0][2] if es else act_metros[0][1]
            fares_h = f"Tarifas desde {mname} ({codes_txt}) a San Salvador" if es else f"Fares from {mname} ({codes_txt}) to San Salvador"
            fares_sub = (f"Por ahora solo mostramos tarifas desde {names_txt}. Más ciudades próximamente. Mostramos solo tarifas vistas en las últimas 6 horas, para 1 adulto, ida y vuelta, en económica." if es else
                         f"For now we only show fares from {names_txt}. More cities coming soon. We only show fares seen in the last 6 hours, for 1 adult, round trip, economy.")
            hero_lead = (f"Tarifas vistas recientemente desde {mname} ({codes_txt}) a San Salvador, más requisitos de viaje con fuentes oficiales. Más ciudades próximamente." if es else
                         f"Recently seen fares from {mname} ({codes_txt}) to San Salvador, plus travel rules backed by official sources. More cities coming soon.")
            cta = f"Ver tarifas desde {mname}" if es else f"See fares from {mname}"
            chips_html = ""
            foot_note = ""
        else:
            fares_h = "Ver tarifas desde tu ciudad" if es else "See fares from your city"
            fares_sub = "Elige tu área. Mostramos solo tarifas vistas en las últimas 6 horas, para 1 adulto, ida y vuelta, en económica." if es else "Pick your area. We only show fares seen in the last 6 hours, for 1 adult, round trip, economy."
            hero_lead = "Tarifas vistas recientemente desde las ciudades con más salvadoreños en EE. UU., más requisitos de viaje con fuentes oficiales." if es else "Recently seen fares from the US cities where most Salvadorans live, plus travel rules backed by official sources."
            cta = fares_h
            chips_html = f''' <div class="chips" role="group" aria-label="{"Áreas metropolitanas" if es else "Metro areas"}">
  <button type="button" class="chip" data-metro="all" aria-pressed="true">{"Todas" if es else "All"}</button>{chips}
 </div>'''
            foot_note = f'<p class="small">{"Las 10 áreas metropolitanas de EE. UU. con más población de origen salvadoreño (Censo de EE. UU., ACS 2024, tabla B03001)." if es else "The 10 US metro areas with the largest Salvadoran-origin populations (US Census Bureau, ACS 2024 1-year, table B03001)."}</p>'
        cards = ""
        for mid, ne, ns, codes in [(metro_of[c][0], metro_of[c][1], metro_of[c][2], [c]) for c in active]:
            for code in codes:
                cards += (f'<li class="fcard" data-code="{code}" data-metro="{mid}"><p class="mlabel">{html.escape(ns if es else ne)}</p>'
                          f'<div class="fhead"><span class="code">{code}</span><span class="aname">{AIRPORT_NAMES[code]}</span><span class="arrow" aria-hidden="true">→ SAL</span></div>'
                          f'<div class="fare"><span class="muted">{"Tarifas próximamente" if es else "Fares coming soon"}</span></div></li>')
        groups = f'<ul class="fcards">{cards}</ul>'
        guide_tiles = [
            ("entry.html", "suchitoto", T[lang]["nav"][1][1], "Pasaporte, DUI, menores, efectivo" if es else "Passport, DUI, minors, cash limits"),
            ("airport.html", "coatepeque", T[lang]["nav"][2][1], "Horario, vuelos, estacionamiento, VIP" if es else "Hours, flight board, parking, VIP"),
            ("bring.html", "santa-ana", T[lang]["nav"][3][1], "Líquidos, comida al regresar, medicinas" if es else "Liquids, food coming back, medications"),
            ("tips.html", "playa", T[lang]["nav"][4][1], "Manejo, agua, playas, emergencias" if es else "Driving, water, beaches, emergencies"),
        ]
        tiles = "".join(f'<a class="tile" href="{h}">{img(k, lang, depth, "(min-width: 900px) 220px, (min-width: 600px) 45vw, 92vw")}<span class="tbody"><b>{t}</b><span>{s}</span></span></a>' for h, k, t, s in guide_tiles)
        home = f"""
<div class="hero">
 {img("coatepeque", lang, depth, "100vw", cls="hero-img", eager=True)}
 <div class="hero-shade"></div>
 <div class="wrap hero-text">
  <p class="eyebrow">{"Guía bilingüe · Vuelos a San Salvador (SAL)" if es else "Bilingual guide · Flights to San Salvador (SAL)"}</p>
  <h1>{"¿Vas de regreso a El Salvador?" if es else "Flying home to El Salvador?"}</h1>
  <p class="lead">{hero_lead}</p>
  <a class="btn" href="#fares">{cta} ↓</a>
 </div>
 <p class="photo-credit">{html.escape(PHOTOS["coatepeque"][lang])} · {PHOTOS["coatepeque"]["author"]}, {PHOTOS["coatepeque"]["license"]} · <a href="credits.html">{"créditos" if es else "credits"}</a></p>
</div>
<main id="main">
<section class="wrap section" id="fares" aria-labelledby="fares-h">
 <h2 id="fares-h">{fares_h}</h2>
 <p class="sub">{fares_sub} <a href="prices.html">{"Cómo funcionan nuestros precios" if es else "How our prices work"}</a></p>
{chips_html}
 <div id="fares-status" class="notice" role="status">
  <b>{"Tarifas próximamente." if es else "Fares coming soon."}</b>
  {"Estamos conectando una fuente de precios autorizada. No mostramos precios de ejemplo ni inventados." if es else "We are connecting a licensed price data source. We never show sample or made-up prices."}
 </div>
 <div id="fares-list" class="metros">{groups}</div>
 {foot_note}
 <p class="sub"><a href="calendar.html">{"Ver los precios más bajos vistos por fecha y por mes →" if es else "See the cheapest seen prices by date and month →"}</a></p>
</section>

<section class="band">
 <div class="wrap section">
  <h2>{"Antes de viajar" if es else "Before you fly"}</h2>
  <p class="sub">{"Requisitos y consejos con enlaces a fuentes oficiales." if es else "Rules and tips, each linked to an official source."}</p>
  <div class="tiles">{tiles}</div>
 </div>
</section>

<section class="wrap section" aria-labelledby="alerts-h">
 <div class="card alerts">
  <h2 id="alerts-h">{"Alertas de tarifas gratis por correo" if es else "Free fare alerts by email"}</h2>
  <p>{"Muy pronto podrá recibir un aviso cuando bajen los precios desde su aeropuerto." if es else "Soon you'll be able to get an email when prices drop from your airport."}</p>
  <form class="signup" onsubmit="return false;" aria-disabled="true">
   <label class="sr" for="em-{lang}">{"Correo" if es else "Email"}</label>
   <input id="em-{lang}" type="email" placeholder="{"su@correo.com" if es else "you@example.com"}" disabled>
   <button type="button" disabled>{"Próximamente" if es else "Coming soon"}</button>
  </form>
  <p class="small">{"El registro aún no está activo. No recopilamos correos todavía. Alertas Premium: más adelante." if es else "Sign-up is not active yet. We are not collecting any emails yet. Premium alerts: coming later."}</p>
 </div>
</section>
</main>
<script src="{depth}assets/fares.js?v={asset_v('assets/fares.js')}" defer></script>
"""
        pages[(lang, "index.html")] = ("Inicio" if es else "Home", home, "home", None)

        # ---------- HOW PRICES WORK ----------
        if es:
            prices = f"""
<h2>De dónde vienen los precios</h2>
<p>Los precios vienen de la <b>API de datos de Aviasales a través de Travelpayouts</b>. Son precios que otros viajeros vieron cuando buscaron vuelos en Aviasales, guardados en caché. No hacemos búsquedas en vivo ni vendemos boletos.</p>
<h2>Qué aeropuertos cubrimos</h2>
<p>Por ahora mostramos tarifas a San Salvador (SAL) solo desde {names_txt}. Más ciudades próximamente.</p>
<h2>Solo las últimas 6 horas</h2>
<p>Mostramos una tarifa solo si podemos confirmar que alguien la vio en las <b>últimas 6 horas</b> y si el vuelo sale en más de 48 horas. Usamos una ventana corta porque las tarifas baratas suelen agotarse en pocas horas: un precio visto hace un día puede ya no existir. Si no hay una tarifa así para un aeropuerto, verá «Sin tarifas recientes». Revisamos los datos cada hora, y la página vuelve a revisar la antigüedad cada vez que la abre.</p>
<h2>Los precios no están garantizados</h2>
<p>Los boletos baratos se agotan rápido. El precio de hoy puede ser mucho más alto que el visto recientemente. Por eso mostramos «Precio cuando se vio» y el botón dice «Ver precio de hoy»: abre una búsqueda en vivo en Aviasales. Los precios son por 1 adulto, ida y vuelta, en clase económica, en dólares.</p>
<h2>Impuestos y cargos</h2>
<p>La documentación de la API de Travelpayouts no indica si estos precios incluyen todos los impuestos y cargos, así que no lo prometemos. El equipaje puede costar aparte según la tarifa. El total final aparece en el sitio del vendedor antes de pagar. {c('tpdocs','avsfaq')}</p>
<h2>Calendario de fechas baratas</h2>
<p>La página <a href="calendar.html">Fechas baratas</a> usa la misma fuente, pero muestra el precio más bajo visto por fecha de salida en los últimos 7 días (el tiempo que la API guarda los datos). Cada precio muestra la fecha en que se vio. Son más antiguos que las tarifas de 6 horas de la página principal: úselos para comparar fechas. También guardamos una captura diaria para mostrar, cuando haya suficiente historial, qué meses han sido más baratos.</p>
<h2>Enlaces de afiliado</h2>
<p>Los botones son enlaces de afiliado de Travelpayouts/Aviasales. Si compra después de hacer clic, podemos ganar una comisión <b>sin costo extra para usted</b>. Esto no cambia qué tarifas mostramos.</p>
<h2>Nunca inventamos precios</h2>
<p>Cada precio de vuelo en el sitio viene de la API. No usamos precios de ejemplo ni estimados. La única cifra calculada será la mediana de precios vistos en la sección de historial, y estará identificada como tal. Si no hay datos recientes, lo decimos.</p>
"""
        else:
            prices = f"""
<h2>Where the prices come from</h2>
<p>Prices come from the <b>Aviasales Data API via Travelpayouts</b>. They are prices other travelers saw when they searched for flights on Aviasales, stored in a cache. We don't run live searches or sell tickets.</p>
<h2>Which airports we cover</h2>
<p>For now we show fares to San Salvador (SAL) only from {names_txt}. More cities coming soon.</p>
<h2>Only the last 6 hours</h2>
<p>We show a fare only if we can confirm someone saw it in the <b>last 6 hours</b> and the flight leaves more than 48 hours from now. We use a short window because cheap fares often sell out within hours: a price seen a day ago may already be gone. If an airport has no such fare, you'll see "No recent fares". We check for new data every hour, and the page re-checks each fare's age every time you open it.</p>
<h2>Prices are not guaranteed</h2>
<p>Cheap seats sell out fast. Today's price can be much higher than the recently seen one. That's why we label it "Price when seen" and the button says "Check today's price": it opens a live search on Aviasales. Prices are per 1 adult, round trip, economy, in US dollars.</p>
<h2>Taxes and fees</h2>
<p>Travelpayouts' API documentation doesn't say whether these prices include all taxes and fees, so we don't promise that they do. Bags may cost extra depending on the fare. The final total is shown on the seller's site before you pay. {c('tpdocs','avsfaq')}</p>
<h2>Cheapest-dates calendar</h2>
<p>The <a href="calendar.html">Cheapest dates</a> page uses the same source but shows the cheapest price seen per departure date over the last 7 days (how long the API keeps data). Each price shows the date it was seen. They are older than the 6-hour fares on the home page: use them to compare dates. We also save one daily snapshot so that, once there is enough history, we can show which months have been cheapest.</p>
<h2>Affiliate links</h2>
<p>The buttons are Travelpayouts/Aviasales affiliate links. If you book after clicking, we may earn a commission <b>at no extra cost to you</b>. It doesn't change which fares we show.</p>
<h2>We never invent prices</h2>
<p>Every flight price on this site comes from the API. We don't use sample or estimated prices. The only calculated figure will be the median of seen prices in the history section, labeled as such. If there's no recent data, we say so.</p>
"""
        pages[(lang, "prices.html")] = ("Cómo funcionan nuestros precios" if es else "How our prices work", prices, None,
                                        "Transparencia sobre las tarifas que mostramos." if es else "Plain answers about the fares we show.")

        # ---------- MONTH VIEW (calendar.html) ----------
        cal = load_json("public/data/calendar.json", None)
        hist = load_history()
        tax_note = ("La documentación de Travelpayouts no indica si estos precios incluyen todos los impuestos y cargos; el total final (impuestos, cargos y equipaje) aparece en el sitio del vendedor." if es else
                    "Travelpayouts' documentation does not say whether these prices include all taxes and fees; the final total (taxes, fees and bags) is shown on the seller's site.")
        import calendar as _calmod
        if not cal or not cal.get("days"):
            calbody = f'<div class="notice"><b>{"Sin tarifas recientes." if es else "No recent fares."}</b> {"Todavía no tenemos datos del calendario." if es else "We don't have calendar data yet."}</div>'
        else:
            days = cal["days"]
            seen = sorted(d["seen_date"] for d in days)
            gen = cal["generated_at"][:16].replace("T", " ")
            chk = "Ver precio de hoy" if es else "Check today's price"
            stops = lambda n: ("" if n is None else (("directo" if es else "nonstop") if n == 0 else f'{n} {"escala" if es else "stop"}{"" if n == 1 else ("s" if True else "")}'))
            summary = ""
            for m in cal["months"]:
                y, mo = int(m["month"][:4]), int(m["month"][5:7])
                mname = (f"{MONTH_ES[mo-1]} {y}" if es else f"{MONTH_EN[mo-1]} {y}")
                if m["min"] is None:
                    summary += f'<li class="mrow none"><span class="mname">{mname}</span><span class="muted">{"Sin tarifas recientes" if es else "No recent fares"}</span></li>'
                else:
                    summary += (f'<li class="mrow"><a href="#m-{m["month"]}"><span class="mname">{mname}</span>'
                                f'<span class="mprice">{"Desde" if es else "From"} ${m["min"]:,}</span>'
                                f'<span class="small">{m["min_origin"]} · {"sale" if es else "departs"} {fdate(m["min_depart_date"], es)} · {"visto el" if es else "seen"} {fdate(m["min_seen_date"], es)} · {m["days_with_data"]} {"días con datos" if es else ("day with data" if m["days_with_data"] == 1 else "days with data")}</span></a></li>')
            grids = ""
            dows = ["L", "M", "M", "J", "V", "S", "D"] if es else ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
            for m in cal["months"]:
                if m["min"] is None: continue
                y, mo = int(m["month"][:4]), int(m["month"][5:7])
                mname = (f"{MONTH_ES[mo-1]} {y}" if es else f"{MONTH_EN[mo-1]} {y}")
                md = [d for d in days if d["depart_date"].startswith(m["month"])]
                best = {}
                for d in md:
                    if d["depart_date"] not in best or d["price"] < best[d["depart_date"]]["price"]:
                        best[d["depart_date"]] = d
                cells = "".join(f'<span class="dow" aria-hidden="true">{w}</span>' for w in dows)
                first_wd, ndays = _calmod.monthrange(y, mo)
                cells += '<span class="cell pad" aria-hidden="true"></span>' * first_wd
                for dd in range(1, ndays + 1):
                    iso = f"{m['month']}-{dd:02d}"
                    f = best.get(iso)
                    if f:
                        lab = (f'{"Sale" if es else "Depart"} {fdate(iso, es)}, {"regresa" if es else "return"} {fdate(f["return_date"], es)}, {f["origin"]}: '
                               f'{"precio cuando se vio" if es else "price when seen"} ${f["price"]:,}, {"visto el" if es else "seen"} {fdate(f["seen_date"], es, True)}')
                        cells += (f'<a class="cell has" data-dep="{iso}" data-seen="{f["seen_date"]}" href="{html.escape(f["link"])}" rel="sponsored noopener" target="_blank" aria-label="{html.escape(lab)}" title="{html.escape(lab)}">'
                                  f'<span class="dn">{dd}</span><span class="dp">${f["price"]:,}</span><span class="do">{f["origin"]}</span></a>')
                    else:
                        cells += f'<span class="cell"><span class="dn">{dd}</span></span>'
                rows = "".join(
                    f'<li data-dep="{d["depart_date"]}" data-seen="{d["seen_date"]}"><b>${d["price"]:,}</b> · {d["origin"]} → SAL · {fdate(d["depart_date"], es)} – {fdate(d["return_date"], es)}'
                    f'{" · " + stops(d["transfers"]) + (" ida" if es else " out") if d.get("transfers") is not None else ""}{" · " + d["airline"] if d.get("airline") else ""}'
                    f' · {"visto el" if es else "seen"} {fdate(d["seen_date"], es)} · <a href="{html.escape(d["link"])}" rel="sponsored noopener" target="_blank">{chk}</a></li>'
                    for d in sorted(md, key=lambda x: (x["depart_date"], x["price"])))
                grids += (f'<section class="month" id="m-{m["month"]}"><h3>{mname} <span class="small">· {"desde" if es else "from"} ${m["min"]:,}</span></h3>'
                          f'<div class="cal" role="group" aria-label="{mname}">{cells}</div>'
                          f'<details><summary>{"Todas las tarifas de este mes" if es else "All fares this month"} ({len(md)})</summary><ul class="flist">{rows}</ul></details></section>')
            # When is it cheapest: needs enough daily snapshots
            snaps = len(hist)
            NEED = 28
            if snaps >= NEED:
                import statistics
                acc = {}
                for h in hist:
                    for mm, v in h.get("by_month", {}).items():
                        acc.setdefault(mm, []).append(v["min"])
                trs = "".join(f'<tr><td>{(MONTH_ES if es else MONTH_EN)[int(mm[5:7])-1]} {mm[:4]}</td><td>${statistics.median(v):,.0f}</td><td>{len(v)}</td></tr>' for mm, v in sorted(acc.items()))
                when = (f'<p>{"Mediana del precio más bajo visto cada día, por mes de salida, a partir de" if es else "Median of the cheapest price seen each day, by departure month, from"} {snaps} {"capturas diarias" if es else "daily snapshots"} ({fdate(hist[0]["date"], es, True)} – {fdate(hist[-1]["date"], es, True)}). {"Es historial de precios vistos, no una predicción." if es else "This is a history of seen prices, not a prediction."}</p>'
                        f'<table class="hist"><thead><tr><th>{"Mes de salida" if es else "Departure month"}</th><th>{"Mediana" if es else "Median"}</th><th>{"Días" if es else "Days"}</th></tr></thead><tbody>{trs}</tbody></table>')
            else:
                start = fdate(hist[0]["date"], es, True) if hist else ""
                when = (f'<p>{"Estamos guardando una captura diaria de estos precios" if es else "We are saving one daily snapshot of these prices"}{(" desde el " if es else " since ") + start if start else ""} ({snaps} {"hasta ahora" if es else "so far"}). '
                        f'{"Cuando tengamos al menos" if es else "Once we have at least"} {NEED} {"días de historial, mostraremos aquí qué meses han sido más baratos. Hasta entonces no hacemos afirmaciones sobre tendencias." if es else "days of history, we will show here which months have been cheapest. Until then we make no claims about trends."}</p>')
            calbody = f"""
<div class="notice" role="note"><b>{"Precios más bajos vistos en búsquedas recientes; pueden haber cambiado." if es else "Cheapest prices seen in recent searches; they may have changed."}</b>
{"Cada precio muestra la fecha en que alguien lo vio en Aviasales (hasta 7 días atrás). Son más antiguos que las tarifas de 6 horas de la página principal, así que úselos para comparar fechas, no como precio de compra." if es else "Each price shows the date someone saw it on Aviasales (up to 7 days ago). They are older than the 6-hour fares on the home page, so use them to compare dates, not as a price you can book."}
{"1 adulto, ida y vuelta, económica, en dólares, desde" if es else "1 adult, round trip, economy, in US dollars, from"} {codes_txt}. {tax_note}</div>
<p class="small">{"Precios vistos entre el" if es else "Prices seen between"} {fdate(seen[0], es, True)} {"y el" if es else "and"} {fdate(seen[-1], es, True)}. {"Datos actualizados" if es else "Data updated"} {gen} UTC. {"Fuente" if es else "Source"}: Aviasales (Travelpayouts Data API). <a href="prices.html">{"Cómo funcionan nuestros precios" if es else "How our prices work"}</a></p>
<h2>{"El más barato por mes" if es else "Cheapest by month"}</h2>
<ul class="months">{summary}</ul>
<p class="small">{"Pocos días con datos significa que pocas personas buscaron esas fechas; no quiere decir que no haya vuelos." if es else "Few days with data means few people searched those dates; it doesn't mean there are no flights."}</p>
<h2>{"Calendario por fecha de salida" if es else "Calendar by departure date"}</h2>
<p class="small">{"Cada día muestra el precio más bajo visto (DCA o IAD) y abre esa búsqueda en Aviasales." if es else "Each day shows the cheapest seen price (DCA or IAD) and opens that search on Aviasales."}</p>
{grids}
<h2 id="cheapest">{"¿Cuándo es más barato volar?" if es else "When is it cheapest to fly?"}</h2>
{when}
<script>(function(){{var now=Date.now(),max={cal.get("max_seen_days", 7)}*864e5+864e5,lead=2*864e5;document.querySelectorAll('[data-seen]').forEach(function(e){{var s=Date.parse(e.getAttribute('data-seen')+'T00:00:00Z'),d=Date.parse(e.getAttribute('data-dep')+'T00:00:00Z');if(now-s>max||d-now<lead){{if(e.tagName==='A'){{var n=document.createElement('span');n.className='cell';n.innerHTML='<span class="dn">'+e.querySelector('.dn').textContent+'</span>';e.replaceWith(n);}}else e.remove();}}}});}})();</script>
"""
        pages[(lang, "calendar.html")] = ("Fechas más baratas" if es else "Cheapest dates", calbody, None,
                                          (f"Precios más bajos vistos por fecha de salida desde {codes_txt}, próximos 12 meses." if es else f"Cheapest seen prices by departure date from {codes_txt}, next 12 months."))

        # ---------- BUYING TICKETS (buying.html) ----------
        seen_air = []
        for d in ((cal or {}).get("days") or []):
            if d.get("airline") in BAGGAGE and d["airline"] not in seen_air:
                seen_air.append(d["airline"])
        bag_links = ", ".join(f'<a href="{BAGGAGE[a][1]}" rel="noopener" target="_blank">{BAGGAGE[a][0]}</a>' for a in sorted(seen_air or BAGGAGE, key=lambda a: BAGGAGE[a][0]))
        if es:
            buying = f"""
<h2>Qué aerolíneas vuelan de Washington DC a San Salvador</h2>
{ul([
 f"El aeropuerto de Dulles (IAD) lista San Salvador como destino <b>sin escalas, todo el año</b>. {c('dulles')}",
 f"El tablero oficial del aeropuerto de El Salvador mostró vuelos de <b>Avianca</b> hacia Washington cuando lo revisamos (18 oct 2026). El tablero muestra solo los vuelos del día. {c('fids')}",
 f"Para Reagan National (DCA), revise la lista de destinos sin escala del aeropuerto. {c('reagan')}",
 "Aerolíneas que aparecen en las tarifas DC–SAL que vimos recientemente (pueden incluir conexiones): " + (", ".join(BAGGAGE[a][0] for a in sorted(seen_air, key=lambda a: BAGGAGE[a][0])) or "—") + ". Fuente: datos de Aviasales en esta página.",
 "Otras aerolíneas pueden volar la ruta por temporada. Confirme siempre en el sitio de la aerolínea.",
])}
<h2>Equipaje</h2>
<p>Las reglas y cargos de equipaje cambian según la aerolínea, la tarifa y la fecha de compra, por eso no copiamos montos aquí. Revise la página oficial de su aerolínea: {bag_links}.</p>
<p>En Aviasales, si una tarifa no muestra opción de equipaje, el vendedor dio una tarifa sin equipaje y puede agregarlo al reservar en el sitio del vendedor. {c('avsfaq')}</p>
<h2>Fechas para planear (feriados en El Salvador)</h2>
{ul([
 f"El artículo 190 del Código de Trabajo establece como asuetos: 1 de enero; jueves, viernes y sábado de Semana Santa; 1 de mayo; 6 de agosto; 15 de septiembre; 2 de noviembre; 25 de diciembre. En la ciudad de San Salvador también el 3 y 5 de agosto (fiestas agostinas). Puede haber otros asuetos por decretos posteriores. {c('csj')}",
 "Semana Santa 2027: jueves 25, viernes 26 y sábado 27 de marzo de 2027 (Domingo de Pascua: 28 de marzo).",
 "Todavía no tenemos suficiente historial para decir si las tarifas suben en estas fechas. Vea <a href='calendar.html'>Fechas baratas</a> para precios vistos por fecha.",
])}
<h2>Cuándo comprar</h2>
{ul([
 f"Según el informe 2026 Air Hacks de Expedia (promedios de todos los vuelos internacionales en económica comprados desde EE. UU., no específico de El Salvador), comprar 31–45 días antes ahorró en promedio $190 frente a comprar con 6 meses o más, y 8–15 días antes ahorró en promedio $225. {c('expedia')}",
 "Las tarifas baratas se agotan rápido: si encuentra un precio que le sirve, compare el total final en el sitio del vendedor antes de decidir.",
])}
<h2>Requisitos de ingreso</h2>
<p>Pasaporte, DUI, menores y efectivo: vea <a href="entry.html">Requisitos de ingreso</a>, con fuentes oficiales.</p>
<h2>Al comprar</h2>
{ul([
 f"Aviasales no vende boletos: lo envía al sitio del vendedor (aerolínea o agencia), donde paga y ve el total final. {c('avsfaq')}",
 "Compare el total final en el sitio del vendedor, no el precio que vio aquí ni en la lista de resultados.",
])}
"""
        else:
            buying = f"""
<h2>Which airlines fly Washington DC to San Salvador</h2>
{ul([
 f"Washington Dulles (IAD) lists San Salvador as a <b>year-round nonstop</b> destination. {c('dulles')}",
 f"El Salvador airport's official flight board showed <b>Avianca</b> flights to Washington when we checked (Oct 18, 2026). The board only shows that day's flights. {c('fids')}",
 f"For Reagan National (DCA), check the airport's nonstop destination list. {c('reagan')}",
 "Airlines that appear in DC–SAL fares we saw recently (may include connections): " + (", ".join(BAGGAGE[a][0] for a in sorted(seen_air, key=lambda a: BAGGAGE[a][0])) or "—") + ". Source: the Aviasales data on this site.",
 "Other airlines may fly the route seasonally. Always confirm on the airline's website.",
])}
<h2>Baggage</h2>
<p>Bag rules and fees depend on the airline, fare type and purchase date, so we don't copy amounts here. Check your airline's official page: {bag_links}.</p>
<p>On Aviasales, if a fare shows no baggage option, the seller supplied a no-bag fare and you can add bags when booking on the seller's site. {c('avsfaq')}</p>
<h2>Dates to plan around (holidays in El Salvador)</h2>
{ul([
 f"Article 190 of the Labor Code lists these paid holidays: January 1; Holy Thursday, Friday and Saturday; May 1; August 6; September 15; November 2; December 25. In the city of San Salvador also August 3 and 5 (fiestas agostinas). Later decrees may add other holidays. {c('csj')}",
 "Holy Week 2027: Thursday March 25, Friday March 26 and Saturday March 27, 2027 (Easter Sunday: March 28).",
 "We don't have enough history yet to say whether fares rise around these dates. See <a href='calendar.html'>Cheapest dates</a> for seen prices by date.",
])}
<h2>When to book</h2>
{ul([
 f"According to Expedia's 2026 Air Hacks report (averages across all international economy flights booked from the U.S., not specific to El Salvador), booking 31–45 days ahead saved $190 on average versus booking 6+ months out, and booking 8–15 days ahead saved $225 on average. {c('expedia')}",
 "Cheap fares sell out fast: if you find a price that works, compare the final total on the seller's site before you decide.",
])}
<h2>Entry rules</h2>
<p>Passport, DUI, minors and cash: see <a href="entry.html">Entry rules</a>, with official sources.</p>
<h2>When you book</h2>
{ul([
 f"Aviasales doesn't sell tickets: it sends you to the seller's site (airline or agency), where you pay and see the final total. {c('avsfaq')}",
 "Compare the final total on the seller's site, not the price you saw here or in the results list.",
])}
"""
        pages[(lang, "buying.html")] = ("Comprar boletos a El Salvador" if es else "Buying tickets to El Salvador", buying, None,
                                        "Aerolíneas, equipaje, feriados y consejos para comprar, con fuentes." if es else "Airlines, baggage, holidays and booking advice, with sources.")

        # ---------- CREDITS ----------
        rows = "".join(
            f'<li class="credit">{img(k, lang, depth, "160px")}<div><b>{html.escape(p[lang])}</b><br>'
            f'{"Autor" if es else "Author"}: {html.escape(p["author"])} · {"Licencia" if es else "License"}: <a href="{p["license_url"]}" rel="license noopener" target="_blank">{p["license"]}</a><br>'
            f'{"Fuente" if es else "Source"}: <a href="{p["src"]}" rel="noopener" target="_blank">Wikimedia Commons: {html.escape(p["title"])}</a><br>'
            f'<span class="small">{"Redimensionada y convertida a WebP." if es else "Resized and converted to WebP."}</span></div></li>' for k, p in PHOTOS.items())
        credits = f"""<p>{"Todas las fotos provienen de Wikimedia Commons. Verificamos la licencia de cada una en su página de Commons." if es else "All photos come from Wikimedia Commons. We checked each photo's license on its Commons page."}</p>
<ul class="credits">{rows}</ul>
<p class="small">{"Las fotos con licencia CC BY-SA se comparten bajo la misma licencia." if es else "CC BY-SA photos are shared under the same license."}</p>"""
        pages[(lang, "credits.html")] = ("Créditos de fotos" if es else "Photo credits", credits, None, None)

        # ---------- ENTRY ----------
        if es:
            entry = f"""
<h2>Si usted es salvadoreño(a)</h2>
{ul([
 f"Para ingresar al país, las personas salvadoreñas demuestran su nacionalidad con su <b>pasaporte o DUI</b>. {c('reglamento')}",
 f"Hijos/as de madre o padre salvadoreño con pasaporte extranjero pueden ingresar como salvadoreños presentando la <b>certificación de partida de nacimiento</b> que acredite la nacionalidad de los padres y la filiación. {c('reglamento')}",
 f"Según la Embajada de EE. UU., si su pasaporte estadounidense indica que nació en El Salvador, no se requiere tarjeta de turista ni prueba de fondos. {c('embassy')}",
 f"Para salir hacia Guatemala, Honduras o Nicaragua (CA-4) basta el DUI o pasaporte; para cualquier otro país se necesita pasaporte con al menos 6 meses de vigencia. {c('dgme')}",
])}
<h2>Ciudadanos estadounidenses (sin nacionalidad salvadoreña)</h2>
{ul([
 f"No se requiere visa para estancias de 90 días o menos. El pasaporte debe estar vigente al momento de entrar. {c('state')}",
 f"Acuerdo CA-4: al entrar legalmente a El Salvador, Guatemala, Honduras o Nicaragua puede moverse entre ellos hasta 90 días en total. {c('state')}",
 f"<b>Tarjeta de turista de $12:</b> las fuentes no coinciden. La página de la Embajada de EE. UU. aún la menciona (revisado el 18 oct 2026), pero Diario El Salvador informó el 1 de mayo de 2025 que la Asamblea Legislativa eliminó el cobro de $12 de la Tarjeta Migratoria de Ingreso. Confirme con Migración antes de viajar. {c('embassy','tim')}",
])}
<h2>Efectivo</h2>
<p>El Departamento de Estado indica un máximo de <b>$10,000</b> (USD) de entrada y salida; la página de la Embajada menciona $15,000 (USD). Ambas páginas revisadas el 18 oct 2026. Si lleva mucho efectivo, confirme el límite vigente. El dólar estadounidense es la moneda oficial. {c('state','embassy')}</p>
<h2>Viajando con niños</h2>
{ul([
 f"Lleve copia del acta de nacimiento de cada menor o prueba de su relación legal. {c('state')}",
 f"Un menor estadounidense que pase más de un año en El Salvador se considera residente; para salir sin uno de los padres necesita consentimiento notariado por un notario salvadoreño (no se acepta el notariado en la Embajada). Las autoridades a veces han impedido la salida de menores que viajaban sin sus padres o tutores. {c('state')}",
])}
<h2>Salud</h2>
<p>Se exige vacuna contra la fiebre amarilla si llega de ciertos países de Sudamérica o África. Consulte las recomendaciones del CDC. {c('state','cdc')}</p>
"""
        else:
            entry = f"""
<h2>If you are Salvadoran</h2>
{ul([
 f"Salvadorans prove their nationality on entry with a <b>passport or DUI</b>. {c('reglamento')}",
 f"Children of a Salvadoran mother or father who hold a foreign passport can enter as Salvadorans by presenting a <b>birth certificate</b> proving the parent's nationality and the relationship. {c('reglamento')}",
 f"Per the U.S. Embassy, if your U.S. passport shows you were born in El Salvador, neither the tourist card nor proof of funds is required. {c('embassy')}",
 f"To leave for Guatemala, Honduras or Nicaragua (CA-4) a DUI or passport is enough; for any other country you need a passport valid for at least 6 months. {c('dgme')}",
])}
<h2>U.S. citizens (without Salvadoran nationality)</h2>
{ul([
 f"No visa is required for stays of 90 days or less. Your passport must be valid at the time of entry. {c('state')}",
 f"CA-4 agreement: after legally entering El Salvador, Guatemala, Honduras or Nicaragua you can travel among them for up to 90 days total. {c('state')}",
 f"<b>$12 tourist card:</b> sources disagree. The U.S. Embassy page still lists it (checked Oct 18, 2026), but Diario El Salvador reported on May 1, 2025 that the Legislative Assembly eliminated the $12 entry card fee (Tarjeta Migratoria de Ingreso). Confirm with immigration before you travel. {c('embassy','tim')}",
])}
<h2>Cash</h2>
<p>The State Department lists a <b>$10,000</b> (USD) maximum on entry and exit; the Embassy page says $15,000 (USD). Both pages checked Oct 18, 2026. If you carry a lot of cash, confirm the current limit. The U.S. dollar is El Salvador's official currency. {c('state','embassy')}</p>
<h2>Traveling with children</h2>
{ul([
 f"Bring a copy of each child's birth certificate or other proof of your legal relationship. {c('state')}",
 f"A U.S. minor in El Salvador for more than one year is considered a resident; to leave without a parent they need consent notarized by a Salvadoran notary (U.S. Embassy notarization is not accepted). Authorities have sometimes blocked minors traveling without a parent or guardian from leaving. {c('state')}",
])}
<h2>Health</h2>
<p>Yellow fever vaccination is required if arriving from certain countries in South America or Africa. See CDC recommendations. {c('state','cdc')}</p>
"""
        pages[(lang, "entry.html")] = ("Requisitos de ingreso" if es else "Entry rules", entry)

        # ---------- AIRPORT ----------
        if es:
            airport = f"""
<p>El aeropuerto internacional es el <b>Aeropuerto Internacional de El Salvador San Óscar Arnulfo Romero y Galdámez</b> (código IATA: SAL), administrado por CEPA.</p>
{ul([
 f"Opera <b>las 24 horas, los 7 días</b>. Teléfono CEPA: (503) 2537-1300. {c('cepa')}",
 f"Llegadas y salidas en tiempo real: tablero oficial de vuelos. {c('fids')}",
 f"Estacionamiento general: $2.00 por hora o fracción, máximo $6.00 por día. Estacionamiento VIP: $12.00 por día o fracción. Carretilla para equipaje: $3.00. Tarifas en dólares según la página de CEPA en SIMPLE SV, revisada el 18 oct 2026; pueden cambiar. {c('vip')}",
 f"Servicio VIP (edecanes, trámite migratorio y aduana, retiro de equipaje) se solicita en línea; horario 6:15 a.m. a 9:15 p.m. Consulte el precio vigente en el trámite. {c('vip')}",
 f"Objetos perdidos: WhatsApp +503 7070-8312. Quejas contra aerolíneas (boleto, vuelo, equipaje): enlinea.defensoria.gob.sv/Viajero o teléfono 910. {c('cepafaq')}",
 f"Los empleados del gobierno de EE. UU. pueden viajar a cualquier hora entre San Salvador y el aeropuerto (excepción a su restricción nocturna). {c('state')}",
])}
<h2>Vuelos directos desde EE. UU.</h2>
<p>Las rutas sin escala cambian por temporada. Para verificar qué aerolíneas vuelan hoy desde su ciudad, use el tablero oficial de CEPA o el sitio de su aerolínea. {c('fids')}</p>
"""
        else:
            airport = f"""
<p>The international airport is <b>Aeropuerto Internacional de El Salvador San Óscar Arnulfo Romero y Galdámez</b> (IATA code: SAL), run by CEPA.</p>
{ul([
 f"Open <b>24 hours a day, 7 days a week</b>. CEPA phone: (503) 2537-1300. {c('cepa')}",
 f"Live arrivals and departures: the official flight board. {c('fids')}",
 f"General parking: $2.00 per hour or fraction, max $6.00 per day. VIP parking: $12.00 per day or fraction. Luggage cart: $3.00. Fees in US dollars as listed on CEPA's SIMPLE SV page, checked Oct 18, 2026; they may change. {c('vip')}",
 f"VIP service (escort, immigration and customs processing, baggage pickup) is booked online; hours 6:15 a.m. to 9:15 p.m. Check the current price on the booking page. {c('vip')}",
 f"Lost and found: WhatsApp +503 7070-8312. Airline complaints (ticket, flight, baggage): enlinea.defensoria.gob.sv/Viajero or phone 910. {c('cepafaq')}",
 f"U.S. government employees may travel at any hour between San Salvador and the airport (an exception to their night-travel restriction). {c('state')}",
])}
<h2>Nonstop flights from the U.S.</h2>
<p>Nonstop routes change by season. To check which airlines fly from your city today, use CEPA's official flight board or your airline's website. {c('fids')}</p>
"""
        pages[(lang, "airport.html")] = ("Aeropuerto SAL" if es else "SAL airport", airport)

        # ---------- BRING ----------
        if es:
            bring = f"""
<h2>Al salir de EE. UU. (equipaje de mano)</h2>
{ul([
 f"Líquidos, aerosoles, geles, cremas y pastas: envases de <b>3.4 oz (100 ml) o menos</b>, en una bolsa de un cuarto de galón. Lo más grande va en el equipaje documentado. Medicinas y alimentos para bebés están exentos. {c('tsa')}",
])}
<h2>Al llegar a El Salvador</h2>
{ul([
 f"Es ilegal ingresar armas, municiones y casquillos. {c('state')}",
 f"Productos con THC, incluyendo la mayoría de productos de CBD, son ilegales en El Salvador. {c('state')}",
 f"Lleve sus medicinas en el empaque original con la receta del médico, y verifique que sean legales en El Salvador. {c('state')}",
 f"Grupos que llevan donaciones de insumos o medicinas deben coordinar antes con la Superintendencia de Regulación Sanitaria (consultas@srs.gob.sv). {c('state')}",
])}
<h2>Al regresar a EE. UU. (comida de casa)</h2>
{ul([
 f"Se permiten productos de panadería y ciertos quesos. Muchos alimentos preparados son admisibles, pero casi cualquier producto que contenga carne no lo es. {c('cbp')}",
 f"En general se admiten condimentos, vinagres, aceites, especias empacadas, miel, café y té. Es mejor evitar traer arroz. {c('cbp')}",
 f"Toda planta o producto vegetal (incluyendo artesanías de paja) debe declararse a CBP. Hay multas civiles por no declarar productos agrícolas. Las frutas y verduras frescas dependen de su origen y destino. {c('cbp')}",
])}
<h2>Dinero</h2>
<p>El dólar es la moneda oficial. Algunos negocios no aceptan tarjeta o cobran recargo: lleve efectivo. Los cajeros a veces están fuera de servicio y cobran comisiones altas. {c('state')}</p>
"""
        else:
            bring = f"""
<h2>Leaving the U.S. (carry-on)</h2>
{ul([
 f"Liquids, aerosols, gels, creams and pastes: containers of <b>3.4 oz (100 ml) or less</b> in one quart-sized bag. Larger items go in checked baggage. Medications and infant/child nourishment are exempt. {c('tsa')}",
])}
<h2>Arriving in El Salvador</h2>
{ul([
 f"It is illegal to bring guns, ammunition, or spent shells/casings into El Salvador. {c('state')}",
 f"Items containing THC, including most CBD products, are illegal in El Salvador. {c('state')}",
 f"Carry prescription medication in its original packaging with your doctor's prescription, and check that it's legal in El Salvador. {c('state')}",
 f"Groups bringing donated supplies or medicine should clear them first with the Superintendencia de Regulación Sanitaria (consultas@srs.gob.sv). {c('state')}",
])}
<h2>Coming back to the U.S. (food from home)</h2>
{ul([
 f"Bakery items and certain cheeses are allowed. Many prepared foods are admissible, but almost anything containing meat is not. {c('cbp')}",
 f"As a general rule, condiments, vinegars, oils, packaged spices, honey, coffee and tea are admissible. It's best to avoid bringing rice. {c('cbp')}",
 f"Every plant or plant product (including straw handicrafts) must be declared to CBP, and there are civil penalties for failing to declare agricultural items. Fresh fruit and vegetables depend on where they came from and where you're going. {c('cbp')}",
])}
<h2>Money</h2>
<p>The U.S. dollar is the official currency. Some places don't take cards or charge a fee, so bring cash. ATMs are often out of order and can charge high fees. {c('state')}</p>
"""
        pages[(lang, "bring.html")] = ("Qué llevar" if es else "What to bring", bring)

        # ---------- TIPS ----------
        if es:
            tips = f"""
<p>El Departamento de Estado de EE. UU. mantiene a El Salvador en <b>Nivel 1: tome precauciones normales</b> (emitido el 25 de junio de 2026). {c('state')}</p>
<h2>Importante saber</h2>
{ul([
 f"<b>Cero tolerancia al alcohol al manejar:</b> cualquier nivel de alcohol es delito, con 2 a 5 años de prisión. Hay controles aleatorios. {c('state')}",
 f"Puede manejar con licencia extranjera hasta 30 días. Evite manejar de noche y en caminos sin pavimentar. {c('state')}",
 f"El Régimen de Excepción (desde marzo de 2022) sigue vigente y suspende ciertas garantías constitucionales; varios ciudadanos estadounidenses han sido detenidos. {c('state')}",
 f"Las playas del Pacífico tienen corrientes fuertes; respete las banderas rojas o negras. {c('state')}",
 f"El agua del grifo generalmente no es segura para beber; use agua embotellada con sello intacto. {c('state')}",
 f"Temporada de huracanes: junio a noviembre. Temporada lluviosa (inundaciones y deslaves): mayo a octubre. Hay sismos frecuentes. {c('state')}",
 f"Inscríbase en STEP para recibir alertas de la Embajada (ciudadanos de EE. UU.). {c('step')}",
])}
<h2>Emergencias</h2>
{ul([
 f"Policía: <b>911</b> · Ambulancia: <b>132</b> · Línea contra violencia doméstica: <b>126</b>. {c('state')}",
 f"Embajada de EE. UU. en San Salvador: +503 2501-2999. {c('state')}",
])}
"""
        else:
            tips = f"""
<p>The U.S. State Department rates El Salvador <b>Level 1: Exercise normal precautions</b> (issued June 25, 2026). {c('state')}</p>
<h2>Know before you go</h2>
{ul([
 f"<b>Zero tolerance for drinking and driving:</b> any blood alcohol level is a criminal offense, with 2 to 5 years in prison. Police run random checks. {c('state')}",
 f"You can drive on a foreign license for up to 30 days. Avoid driving at night and on unpaved roads. {c('state')}",
 f"The State of Exception (since March 2022) remains in effect and suspends some constitutional rights; several U.S. citizens have been detained under it. {c('state')}",
 f"Pacific beaches have strong currents and undertows; stay out when red or black flags are up. {c('state')}",
 f"Tap water is generally unsafe to drink; use major-brand bottled water with an intact seal. {c('state')}",
 f"Hurricane season: June–November. Rainy season (floods, landslides): May–October. Earthquakes are frequent. {c('state')}",
 f"U.S. citizens: enroll in STEP for Embassy alerts. {c('step')}",
])}
<h2>Emergencies</h2>
{ul([
 f"Police: <b>911</b> · Ambulance: <b>132</b> · Domestic violence hotline: <b>126</b>. {c('state')}",
 f"U.S. Embassy San Salvador: +503 2501-2999. {c('state')}",
])}
"""
        pages[(lang, "tips.html")] = ("Seguridad y consejos" if es else "Safety & tips", tips)

    leads = {
     "entry.html": ("Pasaporte, DUI, menores y efectivo, con fuentes oficiales.", "Passport, DUI, minors and cash, with official sources."),
     "airport.html": ("Aeropuerto Internacional de El Salvador San Óscar Arnulfo Romero y Galdámez.", "El Salvador International Airport San Óscar Arnulfo Romero y Galdámez."),
     "bring.html": ("Qué llevar en la maleta, y qué puede traer de regreso.", "What to pack, and what you can bring back."),
     "tips.html": ("Seguridad, manejo, salud y emergencias.", "Safety, driving, health and emergencies."),
    }
    for (lang, fname), val in pages.items():
        if len(val) == 2:
            title, body = val; hero = None; lead = leads.get(fname, (None, None))[0 if lang == "es" else 1]
        else:
            title, body, hero, lead = val
        d = os.path.join(OUT, T[lang]["prefix"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, fname), "w") as f:
            f.write(page(lang, fname, html.escape(title), body, hero=hero, lead=lead))
    print("built", len(pages), "pages")

if __name__ == "__main__":
    build()
