// Renders fares ONLY from data/fares.json written by scripts/refresh_fares.py (Travelpayouts API).
// If status isn't "live", the "fares coming soon" notice stays and no numbers are shown.
(function () {
  var es = location.pathname.indexOf('/es/') !== -1;
  var loc = es ? 'es-SV' : 'en-US';
  var url = (es ? '../' : '') + 'data/fares.json';
  function ago(dateStr) {
    if (!dateStr) return '';
    var days = Math.floor((Date.now() - new Date(dateStr + 'T12:00:00Z').getTime()) / 86400000);
    if (days <= 0) return es ? 'hoy' : 'today';
    if (days === 1) return es ? 'hace 1 día' : '1 day ago';
    return es ? 'hace ' + days + ' días' : days + ' days ago';
  }
  function d(iso) { // show the local calendar date as written in the itinerary
    var p = iso.slice(0, 10).split('-');
    return new Date(Date.UTC(+p[0], +p[1] - 1, +p[2], 12)).toLocaleDateString(loc, { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
  }
  fetch(url, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (data) {
    if (!data || data.status !== 'live' || !Array.isArray(data.fares)) return;
    var byCode = {};
    data.fares.forEach(function (f) {
      if (f && f.origin && typeof f.price === 'number' && f.price > 0 && f.currency && f.departure_at) byCode[f.origin] = f;
    });
    var shown = 0;
    document.querySelectorAll('#fares-table tbody tr').forEach(function (tr) {
      var f = byCode[tr.getAttribute('data-code')], td = tr.querySelector('.fare');
      td.innerHTML = '';
      if (!f) { td.textContent = es ? 'Sin tarifas recientes' : 'No recent fares'; return; }
      shown++;
      var price = new Intl.NumberFormat(loc, { style: 'currency', currency: f.currency.toUpperCase(), maximumFractionDigits: 0 }).format(f.price);
      var strong = document.createElement('b');
      strong.textContent = price + (f.round_trip ? (es ? ' ida y vuelta' : ' round trip') : (es ? ' solo ida' : ' one way'));
      td.appendChild(strong);
      var stops = f.transfers === 0 ? (es ? 'directo (ida)' : 'nonstop out') : (f.transfers != null ? f.transfers + (es ? ' escala(s) ida' : ' stop(s) out') : '');
      var s = document.createElement('div'); s.className = 'small';
      s.textContent = d(f.departure_at) + (f.return_at ? ' – ' + d(f.return_at) : '') + (stops ? ' · ' + stops : '') + (f.airline ? ' · ' + f.airline : '');
      td.appendChild(s);
      var s2 = document.createElement('div'); s2.className = 'small';
      s2.textContent = (es ? 'Encontrado ' : 'Found ') + ago(f.found_on);
      td.appendChild(s2);
      if (f.link) {
        var a = document.createElement('a');
        a.href = f.link; a.target = '_blank'; a.rel = 'noopener sponsored nofollow'; a.className = 'book';
        a.textContent = es ? 'Ver vuelos →' : 'See flights →';
        td.appendChild(a);
      }
    });
    var st = document.getElementById('fares-status');
    if (shown) {
      var upd = new Date(data.updated_at).toLocaleString(loc, { dateStyle: 'medium', timeStyle: 'short' });
      st.innerHTML = '';
      var b = document.createElement('b');
      b.textContent = es ? 'Tarifas en caché de búsquedas recientes. Los precios pueden cambiar.' : 'Cached from recent searches. Prices may change.';
      st.appendChild(b);
      st.appendChild(document.createTextNode(' ' + (es
        ? 'Son los precios más bajos que otros viajeros encontraron en Aviasales en los últimos días, no precios garantizados. Confirme el precio final antes de comprar. Datos obtenidos: ' + upd + '. Los enlaces son de afiliado: podemos ganar una comisión sin costo extra para usted.'
        : 'These are the lowest prices other travelers found on Aviasales in the past few days, not guaranteed prices. Confirm the final price before you buy. Data fetched: ' + upd + '. Links are affiliate links: we may earn a commission at no extra cost to you.')));
    }
  }).catch(function () {});
})();
