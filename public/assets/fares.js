// Renders fares ONLY from data/fares.json written by scripts/refresh_fares.py (Travelpayouts API).
// Shows only fares whose found_at is within max_age_hours (48 h) at the moment the page is viewed.
(function () {
  var es = location.pathname.indexOf('/es/') !== -1;
  var loc = es ? 'es-SV' : 'en-US';
  var url = (es ? '../' : '') + 'data/fares.json';
  function ago(ms) {
    var h = Math.floor(ms / 3600000);
    if (h < 1) return es ? 'hace menos de 1 hora' : 'less than 1 hour ago';
    if (h < 24) return es ? 'hace ' + h + (h === 1 ? ' hora' : ' horas') : h + (h === 1 ? ' hour ago' : ' hours ago');
    var dd = Math.floor(h / 24);
    return es ? 'hace ' + dd + (dd === 1 ? ' día' : ' días') : dd + (dd === 1 ? ' day ago' : ' days ago');
  }
  function d(iso) { // itinerary calendar date as written (local to the airport)
    var p = iso.slice(0, 10).split('-');
    return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2], 12)).toLocaleDateString(loc, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
  }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  fetch(url, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (data) {
    if (!data || data.status !== 'live' || !Array.isArray(data.fares)) return;
    var maxAge = (data.max_age_hours || 48) * 3600000, now = Date.now(), byCode = {};
    data.fares.forEach(function (f) {
      if (!f || !f.origin || typeof f.price !== 'number' || f.price <= 0 || !f.currency || !f.found_at || !f.departure_at) return;
      var age = now - new Date(f.found_at).getTime();
      if (age >= 0 && age <= maxAge && new Date(f.departure_at).getTime() > now) { f._age = age; byCode[f.origin] = f; }
    });
    var shown = 0;
    document.querySelectorAll('#fares-table tbody tr').forEach(function (tr) {
      var f = byCode[tr.getAttribute('data-code')], td = tr.querySelector('.fare');
      td.innerHTML = '';
      if (!f) { td.appendChild(el('span', 'small', es ? 'Sin tarifas recientes' : 'No recent fares')); return; }
      shown++;
      td.appendChild(el('div', 'found', (es ? 'Visto ' : 'Seen ') + ago(f._age)));
      var price = new Intl.NumberFormat(loc, { style: 'currency', currency: f.currency.toUpperCase(), maximumFractionDigits: 0 }).format(f.price);
      td.appendChild(el('b', null, (es ? 'Visto recientemente desde ' : 'Recently seen from ') + price + (es ? ' ida y vuelta' : ' round trip')));
      var stops = f.transfers === 0 ? (es ? 'ida directa' : 'nonstop out') : (f.transfers != null ? f.transfers + (es ? (f.transfers === 1 ? ' escala ida' : ' escalas ida') : (f.transfers === 1 ? ' stop out' : ' stops out')) : '');
      td.appendChild(el('div', 'small', (es ? 'Para ' : 'For ') + d(f.departure_at) + ' – ' + d(f.return_at) + (stops ? ' · ' + stops : '') + (f.airline ? ' · ' + f.airline : '') + (es ? ' · 1 adulto, económica' : ' · 1 adult, economy')));
      if (f.link) {
        var a = el('a', 'book', es ? 'Ver precio de hoy →' : "Check today's price →");
        a.href = f.link; a.target = '_blank'; a.rel = 'noopener sponsored nofollow';
        td.appendChild(a);
      }
    });
    var st = document.getElementById('fares-status');
    var upd = new Date(data.updated_at).toLocaleString(loc, { dateStyle: 'medium', timeStyle: 'short' });
    st.innerHTML = '';
    st.appendChild(el('b', null, es ? 'Precios vistos recientemente, no precios garantizados.' : 'Recently seen prices, not guaranteed prices.'));
    st.appendChild(document.createTextNode(' ' + (es
      ? 'Mostramos solo tarifas que otros viajeros encontraron en Aviasales en las últimas 48 horas. Los boletos baratos se agotan rápido y el precio de hoy puede ser mucho más alto: toque «Ver precio de hoy» para buscar en vivo. Precio por 1 adulto, ida y vuelta, en clase económica (datos revisados: ' + upd + '). Los enlaces son de afiliado: podemos ganar una comisión sin costo extra para usted.'
      : "We only show fares other travelers found on Aviasales in the last 48 hours. Cheap seats sell out fast and today's price can be much higher: tap \u201cCheck today's price\u201d to search live. Price per 1 adult, round trip, economy (data checked: " + upd + '). Links are affiliate links: we may earn a commission at no extra cost to you.')));
    if (!shown) st.appendChild(el('div', 'small', es ? 'Ahora mismo no hay tarifas de las últimas 48 horas.' : 'No fares from the last 48 hours right now.'));
  }).catch(function () {});
})();
