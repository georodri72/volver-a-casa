// Renders fares ONLY when data/fares.json has status "live" and real fare records.
// Otherwise the "fares coming soon" notice stays and no numbers are shown.
(function () {
  var es = location.pathname.indexOf('/es/') !== -1;
  var url = (es ? '../' : '') + 'data/fares.json';
  fetch(url, { cache: 'no-store' }).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d || d.status !== 'live' || !Array.isArray(d.fares) || !d.fares.length) return;
    var byCode = {};
    d.fares.forEach(function (f) {
      if (f && f.origin && typeof f.price === 'number' && f.found_at && f.currency) byCode[f.origin] = f;
    });
    var shown = 0;
    document.querySelectorAll('#fares-table tbody tr').forEach(function (tr) {
      var f = byCode[tr.getAttribute('data-code')], td = tr.querySelector('.fare');
      if (!f) { td.textContent = es ? 'Sin datos recientes' : 'No recent data'; return; }
      shown++;
      var price = new Intl.NumberFormat(es ? 'es-SV' : 'en-US', { style: 'currency', currency: f.currency.toUpperCase(), maximumFractionDigits: 0 }).format(f.price);
      var when = new Date(f.found_at).toLocaleDateString(es ? 'es-SV' : 'en-US');
      td.innerHTML = '';
      var a = document.createElement(f.link ? 'a' : 'span');
      if (f.link) { a.href = f.link; a.target = '_blank'; a.rel = 'noopener sponsored'; }
      a.textContent = price + (f.round_trip ? (es ? ' ida y vuelta' : ' round trip') : (es ? ' solo ida' : ' one way'));
      td.appendChild(a);
      var s = document.createElement('div'); s.className = 'small';
      s.textContent = (es ? 'Encontrado el ' : 'Found ') + when + (f.departure_month ? ' · ' + (es ? 'salida ' : 'departs ') + f.departure_month : '');
      td.appendChild(s);
    });
    if (shown) {
      document.getElementById('fares-status').innerHTML = es
        ? 'Precios encontrados recientemente por otros viajeros (datos en caché de ' + (d.source || '') + '). Pueden cambiar; confirme el precio final al reservar. Actualizado: ' + new Date(d.updated_at).toLocaleString('es-SV') + '.'
        : 'Prices recently found by other travelers (cached data from ' + (d.source || '') + '). They can change; confirm the final price when booking. Updated: ' + new Date(d.updated_at).toLocaleString('en-US') + '.';
    }
  }).catch(function () {});
})();
