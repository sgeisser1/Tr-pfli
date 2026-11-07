// fluidi – Verlaufsdiagramm mit uPlot (vendor/uplot, MIT). uPlot ist global (klassisches Skript).

const COL = { moist: '#4aa8de', band: 'rgba(74,168,222,0.18)', temp: '#8a847a', thr: '#1f6f9c', grid: '#e4e0d9', axis: '#6e695f' };
const nf1 = new Intl.NumberFormat('de-CH', { maximumFractionDigits: 1 });

function tickFormatter(rangeS) {
  let opt;
  if (rangeS <= 2 * 86400) opt = { hour: '2-digit', minute: '2-digit' };
  else if (rangeS <= 62 * 86400) opt = { day: 'numeric', month: 'numeric' };
  else opt = { month: 'short', year: '2-digit' };
  const f = new Intl.DateTimeFormat('de-CH', opt);
  return (u, splits) => splits.map((s) => f.format(new Date(s * 1000)));
}

const legendTime = new Intl.DateTimeFormat('de-CH', { dateStyle: 'short', timeStyle: 'short' });

/**
 * Zeichnet die Reihe (Format GET /plants/{id}/series) in container. Gibt { destroy } zurück.
 */
export function renderChart(container, s) {
  const U = window.uPlot;
  container.replaceChildren();
  if (!U) {
    container.textContent = 'Diagramm-Bibliothek nicht geladen.';
    return { destroy() {} };
  }
  const agg = s.res !== 'raw';
  const data = [s.t, s.moisture];
  const series = [
    { label: 'Zeit', value: (u, v) => (v == null ? '–' : legendTime.format(new Date(v * 1000))) },
    { label: agg ? 'Feuchte (Mittel)' : 'Feuchte', stroke: COL.moist, width: 2, scale: '%', spanGaps: false,
      value: (u, v) => (v == null ? '–' : `${nf1.format(v)} %`), points: { show: !agg && s.t.length < 80, size: 4 } },
  ];
  const bands = [];
  if (agg && s.moisture_min && s.moisture_max) {
    data.push(s.moisture_max, s.moisture_min);
    series.push(
      { label: 'Max', stroke: 'transparent', scale: '%', value: (u, v) => (v == null ? '–' : `${nf1.format(v)} %`), points: { show: false } },
      { label: 'Min', stroke: 'transparent', scale: '%', value: (u, v) => (v == null ? '–' : `${nf1.format(v)} %`), points: { show: false } },
    );
    bands.push({ series: [2, 3], fill: COL.band });
  }
  data.push(s.temp_c);
  series.push({ label: 'Temperatur', stroke: COL.temp, width: 1, scale: '°C', dash: [4, 3],
    value: (u, v) => (v == null ? '–' : `${nf1.format(v)} °C`), points: { show: false } });

  const thr = s.threshold_pct;
  const width = Math.max(280, container.clientWidth || 600);
  const height = width < 520 ? 230 : 300;
  const opts = {
    width, height,
    series, bands,
    cursor: { drag: { x: true, y: false }, points: { size: 6 } },
    legend: { live: true },
    scales: { x: { time: true }, '%': { range: [0, 100] }, '°C': { range: (u, mn, mx) => [Math.floor((mn ?? 15) - 2), Math.ceil((mx ?? 30) + 2)] } },
    axes: [
      { stroke: COL.axis, grid: { stroke: COL.grid }, ticks: { stroke: COL.grid }, values: tickFormatter(s.to - s.from) },
      { scale: '%', stroke: COL.axis, grid: { stroke: COL.grid }, ticks: { stroke: COL.grid }, values: (u, v) => v.map((x) => `${x} %`), size: 50 },
      { scale: '°C', side: 1, stroke: COL.temp, grid: { show: false }, ticks: { show: false }, values: (u, v) => v.map((x) => `${x}°`), size: 40 },
    ],
    hooks: {
      draw: [
        (u) => {
          if (thr == null) return;
          const ctx = u.ctx;
          const y = Math.round(u.valToPos(thr, '%', true));
          ctx.save();
          ctx.strokeStyle = COL.thr;
          ctx.lineWidth = 1.5 * devicePixelRatio;
          ctx.setLineDash([6 * devicePixelRatio, 4 * devicePixelRatio]);
          ctx.beginPath();
          ctx.moveTo(u.bbox.left, y);
          ctx.lineTo(u.bbox.left + u.bbox.width, y);
          ctx.stroke();
          ctx.fillStyle = COL.thr;
          ctx.font = `${11 * devicePixelRatio}px system-ui, sans-serif`;
          ctx.fillText(`Giessen unter ${thr} %`, u.bbox.left + 6 * devicePixelRatio, y - 5 * devicePixelRatio);
          ctx.restore();
        },
      ],
    },
  };
  const u = new U(opts, data, container);
  const ro = new ResizeObserver(() => {
    const w = Math.max(280, container.clientWidth);
    if (Math.abs(w - u.width) > 4) u.setSize({ width: w, height: w < 520 ? 230 : 300 });
  });
  ro.observe(container);
  return {
    destroy() {
      ro.disconnect();
      u.destroy();
    },
  };
}
