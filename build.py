#!/usr/bin/env python3
"""Generates the bilingual static site into public/. Run: python3 build.py
No dependencies. Every factual statement on guide pages carries a source link."""
import os, html

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
CHECKED = "2026-10-17"

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
}

def cite(*keys, lang="en"):
    label = "Fuente" if lang == "es" else "Source"
    links = ", ".join(f'<a href="{SRC[k][1]}" rel="noopener" target="_blank">{html.escape(SRC[k][0])}</a>' for k in keys)
    return f'<span class="cite">{label}: {links}</span>'

# Origin airports serving the top-10 Salvadoran-origin metros (ACS 2024 1-yr, see launch_plan.md)
AIRPORTS = [
 ("Los Angeles", "LAX"), ("Los Angeles / Inland Empire", "ONT"),
 ("Washington DC / Baltimore", "IAD"),
 ("New York", "JFK"), ("New York / New Jersey", "EWR"),
 ("Houston", "IAH"), ("Houston", "HOU"),
 ("Dallas–Fort Worth", "DFW"),
 ("San Francisco", "SFO"), ("Oakland", "OAK"),
 ("Boston", "BOS"), ("Miami", "MIA"), ("Atlanta", "ATL"),
]

T = {
 "en": {
  "lang": "en", "other": "es", "other_label": "Español", "prefix": "",
  "site": "Volver a Casa", "tag": "Travel guide &amp; fare tracker for Salvadorans flying home to El Salvador (SAL)",
  "nav": [("index.html", "Home &amp; fares"), ("entry.html", "Entry rules"), ("airport.html", "SAL airport"), ("bring.html", "What to bring"), ("tips.html", "Safety &amp; tips")],
  "disclaimer": f"Information checked {CHECKED} against the official sources linked on each page. Rules change: always confirm with the source and your airline before you travel. This site is independent and not affiliated with any government or airline.",
 },
 "es": {
  "lang": "es", "other": "en", "other_label": "English", "prefix": "es/",
  "site": "Volver a Casa", "tag": "Guía de viaje y rastreador de tarifas para salvadoreños que vuelan a casa (SAL)",
  "nav": [("index.html", "Inicio y tarifas"), ("entry.html", "Requisitos de ingreso"), ("airport.html", "Aeropuerto SAL"), ("bring.html", "Qué llevar"), ("tips.html", "Seguridad y consejos")],
  "disclaimer": f"Información verificada el {CHECKED} con las fuentes oficiales enlazadas en cada página. Las reglas cambian: confirme siempre con la fuente y con su aerolínea antes de viajar. Este sitio es independiente y no está afiliado a ningún gobierno ni aerolínea.",
 },
}

def page(lang, fname, title, body):
    t = T[lang]
    depth = "../" if lang == "es" else ""
    other_href = ("../" if lang == "es" else "es/") + fname
    nav = "".join(f'<a href="{h}"{" class=active" if h==fname else ""}>{l}</a>' for h, l in t["nav"])
    alt_en = f'/{fname}'; alt_es = f'/es/{fname}'
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · {t['site']}</title>
<meta name="description" content="{t['tag']}">
<link rel="alternate" hreflang="en" href="{alt_en}">
<link rel="alternate" hreflang="es" href="{alt_es}">
<link rel="stylesheet" href="{depth}assets/style.css">
</head>
<body>
<header>
 <div class="wrap top">
  <a class="brand" href="index.html">🇸🇻 {t['site']}</a>
  <a class="lang" href="{other_href}" hreflang="{t['other']}">{t['other_label']}</a>
 </div>
 <div class="wrap"><p class="tag">{t['tag']}</p><nav>{nav}</nav></div>
</header>
<main class="wrap">
<h1>{title}</h1>
{body}
</main>
<footer><div class="wrap"><p>{t['disclaimer']}</p></div></footer>
</body>
</html>
"""

def ul(items):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"

def build():
    pages = {}
    for lang in ("en", "es"):
        es = lang == "es"
        c = lambda *k: cite(*k, lang=lang)
        rows = "".join(f'<tr data-code="{code}"><td>{html.escape(city)}</td><td><b>{code}</b> → SAL</td><td class="fare">—</td></tr>' for city, code in AIRPORTS)
        # ---------- HOME ----------
        home = f"""
<section class="card">
 <h2>{"Rastreador de tarifas a San Salvador (SAL)" if es else "Fare tracker to San Salvador (SAL)"}</h2>
 <div id="fares-status" class="notice">
  <b>{"Tarifas próximamente." if es else "Fares coming soon."}</b>
  {"Estamos conectando una fuente de precios autorizada. No mostramos precios de ejemplo ni inventados: verá tarifas reales aquí cuando estén disponibles." if es else "We are connecting a licensed price data source. We never show sample or made-up prices: real fares will appear here once they are available."}
 </div>
 <table class="fares" id="fares-table">
  <thead><tr><th>{"Área" if es else "Metro area"}</th><th>{"Ruta" if es else "Route"}</th><th>{"Tarifa más baja encontrada" if es else "Lowest fare found"}</th></tr></thead>
  <tbody>{rows}</tbody>
 </table>
 <p class="small">{"Aeropuertos de las 10 áreas metropolitanas con más población de origen salvadoreño (Censo de EE. UU., ACS 2024)." if es else "Airports serving the 10 US metro areas with the largest Salvadoran-origin populations (US Census Bureau, ACS 2024 1-year, table B03001)."}</p>
</section>

<section class="card">
 <h2>{"Alertas de tarifas gratis por correo" if es else "Free fare alerts by email"}</h2>
 <p>{"Muy pronto podrá recibir un aviso cuando bajen los precios desde su aeropuerto." if es else "Soon you'll be able to get an email when prices drop from your airport."}</p>
 <form class="signup" onsubmit="return false;" aria-disabled="true">
  <input type="email" placeholder="{"su@correo.com" if es else "you@example.com"}" disabled>
  <select disabled><option>{"Su aeropuerto" if es else "Your airport"}</option>{''.join(f'<option>{code}</option>' for _, code in AIRPORTS)}</select>
  <button disabled>{"Próximamente" if es else "Coming soon"}</button>
 </form>
 <p class="small">{"El registro aún no está activo. No recopilamos correos todavía." if es else "Sign-up is not active yet. We are not collecting any emails yet."}</p>
 <h3>{"Alertas Premium" if es else "Premium alerts"}</h3>
 <p class="small">{"Alertas más rápidas y personalizadas por una pequeña suscripción mensual: próximamente." if es else "Faster, personalized alerts for a small monthly subscription: coming later."}</p>
</section>

<section class="grid">
 <a class="tile" href="entry.html"><b>{T[lang]['nav'][1][1]}</b><span>{"Pasaporte, DUI, menores, efectivo" if es else "Passport, DUI, minors, cash limits"}</span></a>
 <a class="tile" href="airport.html"><b>{T[lang]['nav'][2][1]}</b><span>{"Horario, vuelos, estacionamiento, VIP" if es else "Hours, flight board, parking, VIP"}</span></a>
 <a class="tile" href="bring.html"><b>{T[lang]['nav'][3][1]}</b><span>{"Líquidos, comida al regresar, medicinas" if es else "Liquids, food coming back, medications"}</span></a>
 <a class="tile" href="tips.html"><b>{T[lang]['nav'][4][1]}</b><span>{"Manejo, agua, playas, emergencias" if es else "Driving, water, beaches, emergencies"}</span></a>
</section>
<script src="{'../' if es else ''}assets/fares.js" defer></script>
"""
        pages[(lang, "index.html")] = ("Volver a Casa" if es else "Volver a Casa", home)

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
 f"<b>Tarjeta de turista de $12:</b> las fuentes no coinciden. La página de la Embajada de EE. UU. aún la menciona, pero la prensa salvadoreña informó que la Asamblea Legislativa eliminó la Tarjeta Migratoria de Ingreso. Confirme con Migración antes de viajar. {c('embassy','tim')}",
])}
<h2>Efectivo</h2>
<p>El Departamento de Estado indica un máximo de <b>$10,000</b> de entrada y salida; la página de la Embajada menciona $15,000. Si lleva mucho efectivo, confirme el límite vigente. El dólar estadounidense es la moneda oficial. {c('state','embassy')}</p>
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
 f"<b>$12 tourist card:</b> sources disagree. The U.S. Embassy page still mentions it, but Salvadoran press reported the Legislative Assembly eliminated the entry card (Tarjeta Migratoria de Ingreso). Confirm with immigration before you travel. {c('embassy','tim')}",
])}
<h2>Cash</h2>
<p>The State Department lists a <b>$10,000</b> maximum on entry and exit; the Embassy page says $15,000. If you carry a lot of cash, confirm the current limit. The U.S. dollar is El Salvador's official currency. {c('state','embassy')}</p>
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
 f"Estacionamiento general: $2.00 por hora o fracción, máximo $6.00 por día. Estacionamiento VIP: $12.00 por día o fracción. Carretilla para equipaje: $3.00. {c('vip')}",
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
 f"General parking: $2.00 per hour or fraction, max $6.00 per day. VIP parking: $12.00 per day or fraction. Luggage cart: $3.00. {c('vip')}",
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

    for (lang, fname), (title, body) in pages.items():
        d = os.path.join(OUT, T[lang]["prefix"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, fname), "w") as f:
            f.write(page(lang, fname, html.escape(title), body))
    print("built", len(pages), "pages")

if __name__ == "__main__":
    build()
