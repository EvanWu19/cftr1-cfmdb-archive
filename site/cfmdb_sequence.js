/*
 * cfmdb_sequence.js — client-side reimplementation of the Genomic DNA Sequence
 * viewer for the static archive. The original Tapestry page fetched a window of
 * the CFTR genomic sequence from a server endpoint (now dead / empty on GET);
 * this reproduces the same function against the captured CFTR.fasta
 * (189,638 nt) — a start-position + length query, plus a clickable ruler that
 * maps a pixel position to a genomic position. Injected into
 * GenomicDnaSequencePage at build time.
 */
(function () {
  "use strict";
  if (!/GenomicDnaSequencePage/i.test(location.pathname)) return;
  var LEN = { "0": 100, "1": 500, "2": 1000, "3": 2000, "4": 5000 };
  var SEQ = null;

  function load(cb) {
    if (SEQ !== null) return cb(SEQ);
    fetch("CFTR.fasta").then(function (r) { return r.text(); }).then(function (t) {
      SEQ = t.split(/\r?\n/).filter(function (l) { return l && l.charAt(0) !== ">"; })
        .join("").toUpperCase().replace(/[^ACGTN]/g, "");
      cb(SEQ);
    }).catch(function () { SEQ = ""; cb(SEQ); });
  }

  function pad(n, w) { n = String(n); while (n.length < w) n = " " + n; return n; }

  function fmt(seq, start) { // start = 1-based genomic position of seq[0]
    var out = [], i;
    for (i = 0; i < seq.length; i += 60) {
      var block = seq.substr(i, 60).replace(/(.{10})/g, "$1 ").replace(/ $/, "");
      out.push(pad(start + i, 9) + "  " + block);
    }
    return out.join("\n");
  }

  function render(box, start, len) {
    load(function (seq) {
      if (!seq.length) { box.innerHTML = "<i>Could not load CFTR.fasta.</i>"; return; }
      var s = Math.max(1, Math.min(start | 0 || 1, seq.length));
      var sub = seq.substr(s - 1, len);
      box.innerHTML =
        '<div style="font-size:small;margin:6px 0"><b>CFTR genomic sequence</b> — '
        + 'positions <b>' + s + '</b>–<b>' + (s + sub.length - 1) + '</b> of ' + seq.length
        + ' nt (' + len + ' nt window)</div>'
        + '<pre style="font:12px/1.35 monospace;background:#f6f8fa;border:1px solid #ddd;'
        + 'padding:8px;overflow:auto;white-space:pre">' + fmt(sub, s) + '</pre>';
    });
  }

  function ruler(onPick) {
    var wrap = document.createElement("div");
    wrap.style.cssText = "margin:8px 0";
    wrap.innerHTML =
      '<div style="font-size:small;margin-bottom:3px">Click the bar to jump to a genomic position '
      + '(0 – 189,638 nt):</div>'
      + '<div id="cfmdb-ruler" title="click to pick a position" style="position:relative;height:26px;'
      + 'width:760px;max-width:100%;background:linear-gradient(90deg,#cfe3f2,#9ec7e6);'
      + 'border:1px solid #6a9; cursor:crosshair;border-radius:3px"></div>'
      + '<div style="display:flex;justify-content:space-between;width:760px;max-width:100%;'
      + 'font-size:11px;color:#555">'
      + '<span>0</span><span>50k</span><span>100k</span><span>150k</span><span>189,638</span></div>';
    wrap.querySelector("#cfmdb-ruler").addEventListener("click", function (e) {
      var rect = this.getBoundingClientRect();
      var frac = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
      onPick(Math.max(1, Math.round(frac * 189638)));
    });
    return wrap;
  }

  function init() {
    var startEl = document.getElementById("start");
    var lenSel = document.getElementById("PropertySelection");
    var getBtn = document.getElementById("Submit");
    var form = startEl && startEl.closest ? startEl.closest("form") : null;
    if (!startEl || !form) return;

    // hide the dead server-image inputs (their .svc source no longer renders)
    Array.prototype.forEach.call(document.querySelectorAll('input[type="image"]'),
      function (im) { im.style.display = "none"; });

    var box = document.createElement("div");
    box.id = "cfmdb-seq-results";
    var rul = ruler(function (pos) { startEl.value = pos; run(); });
    form.parentNode.insertBefore(rul, form);
    form.parentNode.insertBefore(box, form.nextSibling);

    function run() {
      var len = LEN[lenSel ? lenSel.value : "3"] || 2000;
      render(box, parseInt(startEl.value, 10) || 1, len);
    }
    form.setAttribute("action", "#");
    form.addEventListener("submit", function (e) { e.preventDefault(); run(); });
    if (getBtn) getBtn.addEventListener("click", function (e) { e.preventDefault(); run(); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
