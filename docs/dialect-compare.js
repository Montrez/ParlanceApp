/** Shared renderer for dialect region-pair cards (local vs formal). */
(function (global) {
  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function line(name, text) {
    if (!text) return '';
    return '<strong>' + escapeHtml(name) + ':</strong> ' + text;
  }

  function illo(label, fromName, toName, pair, extraClass) {
    if (!pair || (!pair.from && !pair.to)) return '';
    return (
      '<div class="pair-illo' + (extraClass ? ' ' + extraClass : '') + '">' +
        '<span class="pair-illo-lab">' + escapeHtml(label) + '</span>' +
        '<p>' + line(fromName, pair.from) +
        (pair.from && pair.to ? '<br>' : '') +
        line(toName, pair.to) + '</p>' +
      '</div>'
    );
  }

  function pick(value, lang) {
    if (!value || typeof value === 'string') return value || '';
    return value[lang] || value.en || '';
  }

  function lexiconTable(rows, fromName, toName, labels) {
    if (!rows || !rows.length) return '';
    var html = '<div class="pair-lexicon-wrap"><table class="pair-lexicon"><thead><tr>' +
      '<th>' + escapeHtml(labels.idea || '') + '</th>' +
      '<th>' + escapeHtml(fromName) + '</th>' +
      '<th>' + escapeHtml(toName) + '</th>' +
      '</tr></thead><tbody>';
    rows.forEach(function (row) {
      html += '<tr><td>' + (row.idea || '') + '</td>' +
        '<td class="mono">' + (row.from || '') + '</td>' +
        '<td class="mono">' + (row.to || '') + '</td></tr>';
    });
    return html + '</tbody></table></div>';
  }

  function localizeItem(item, lang) {
    if (!item || typeof item === 'string') return item;
    return {
      point: pick(item.point, lang),
      why: pick(item.why, lang),
      note: pick(item.note, lang),
      local: item.local,
      formal: item.formal,
      lexicon: (item.lexicon || []).map(function (row) {
        return {
          idea: pick(row.idea, lang),
          from: row.from,
          to: row.to,
        };
      }),
    };
  }

  function renderPairItems(items, labels, fromName, toName, lang) {
    return (items || []).map(function (raw) {
      if (typeof raw === 'string') {
        return '<li>' + raw + '</li>';
      }
      var item = localizeItem(raw, lang || 'en');
      var html = '<li class="pair-item"><div class="pair-point">' + (item.point || '') + '</div>';
      if (item.why) html += '<p class="pair-why">' + item.why + '</p>';
      html += lexiconTable(item.lexicon, fromName, toName, labels);
      if (item.local || item.formal) {
        html += '<div class="pair-illos">';
        html += illo(labels.local, fromName, toName, item.local, '');
        html += illo(labels.formal, fromName, toName, item.formal, 'pair-illo-formal');
        html += '</div>';
      }
      if (item.note) html += '<p class="pair-note">' + item.note + '</p>';
      html += '</li>';
      return html;
    }).join('');
  }

  global.DialectCompare = { escapeHtml: escapeHtml, renderPairItems: renderPairItems };
})(window);
