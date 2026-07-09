/*
 * cfmdb_sequence.js — client-side reimplementation of the two CFMDB sequence
 * viewers for the static archive. The original Tapestry pages fetched sequence
 * windows from server endpoints; those are reproduced here against sequences
 * recovered before retirement:
 *   - Genomic DNA Sequence  -> CFTR.fasta (189,638 nt)
 *   - mRNA(cDNA) & Polypeptide -> sequence/cftr_cdna.txt (4,443 nt CDS),
 *     cftr_protein_1letter.txt (1,480 aa), cftr_protein_3letter.txt
 * Both give a start-position + length query plus a clickable ruler; the mRNA
 * page also switches between DNA / three-letter / one-letter representations,
 * exactly like the original's three links.
 */
(function () {
  "use strict";
  var path = location.pathname;
  var LEN = { "0": 100, "1": 500, "2": 1000, "3": 2000, "4": 5000 };

  function pad(n, w) { n = String(n); while (n.length < w) n = " " + n; return n; }
  function grouped(s, size) { return s.replace(new RegExp("(.{" + size + "})", "g"), "$1 ").replace(/ $/, ""); }

  function fetchText(url) {
    return fetch(url).then(function (r) { return r.text(); });
  }
  function pre(t) {
    return '<pre style="font:12px/1.35 monospace;background:#f6f8fa;border:1px solid #ddd;'
      + 'padding:8px;overflow:auto;white-space:pre">' + t + '</pre>';
  }
  function hideDeadImages() {
    Array.prototype.forEach.call(document.querySelectorAll('input[type="image"]'),
      function (im) { im.style.display = "none"; });
  }
  function ruler(max, label, onPick) {
    var w = document.createElement("div");
    w.style.cssText = "margin:8px 0";
    w.innerHTML = '<div style="font-size:small;margin-bottom:3px">Click the bar to jump to a '
      + label + ' position (0 – ' + max.toLocaleString() + '):</div>'
      + '<div class="cfmdb-ruler" title="click to pick a position" style="position:relative;'
      + 'height:24px;width:760px;max-width:100%;background:linear-gradient(90deg,#cfe3f2,#9ec7e6);'
      + 'border:1px solid #6a9;cursor:crosshair;border-radius:3px"></div>';
    w.querySelector(".cfmdb-ruler").addEventListener("click", function (e) {
      var rect = this.getBoundingClientRect();
      var frac = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
      onPick(Math.max(1, Math.round(frac * max)));
    });
    return w;
  }

  // ---------------- Genomic DNA Sequence page ----------------
  function genomic() {
    var SEQ = null;
    var startEl = document.getElementById("start");
    var lenSel = document.getElementById("PropertySelection");
    var getBtn = document.getElementById("Submit");
    var form = startEl && startEl.closest ? startEl.closest("form") : null;
    if (!startEl || !form) return;
    hideDeadImages();
    var box = document.createElement("div"); box.id = "cfmdb-seq-results";
    form.parentNode.insertBefore(ruler(189638, "genomic", function (p) { startEl.value = p; run(); }), form);
    form.parentNode.insertBefore(box, form.nextSibling);

    function render(seq, start, len, plain) {
      var s = Math.max(1, Math.min(start | 0 || 1, seq.length));
      var sub = seq.substr(s - 1, len), body, i, out = [];
      if (plain) {                       // "sequence only copy" — no numbering/spacing
        body = sub;
      } else {
        for (i = 0; i < sub.length; i += 60) out.push(pad(s + i, 9) + "  " + grouped(sub.substr(i, 60), 10));
        body = out.join("\n");
      }
      box.innerHTML = '<div style="font-size:small;margin:6px 0"><b>CFTR genomic sequence</b> — positions <b>'
        + s + '</b>–<b>' + (s + sub.length - 1) + '</b> of ' + seq.length + ' nt'
        + (plain ? ' (sequence-only copy)' : '') + '</div>' + pre(body);
    }
    function run(plain) {
      var len = LEN[lenSel ? lenSel.value : "3"] || 2000, start = parseInt(startEl.value, 10) || 1;
      if (SEQ !== null) return render(SEQ, start, len, plain);
      fetchText("CFTR.fasta").then(function (t) {
        SEQ = t.split(/\r?\n/).filter(function (l) { return l && l.charAt(0) !== ">"; })
          .join("").toUpperCase().replace(/[^ACGTN]/g, "");
        render(SEQ, start, len, plain);
      });
    }
    form.setAttribute("action", "#");
    form.addEventListener("submit", function (e) { e.preventDefault(); run(false); });
    if (getBtn) getBtn.addEventListener("click", function (e) { e.preventDefault(); run(false); });
    var svc = document.getElementById("ServiceLink");   // "DNA sequence" plain-copy link
    if (svc) svc.addEventListener("click", function (e) { e.preventDefault(); run(true); });
  }

  // ---------------- mRNA(cDNA) & Polypeptide page ----------------
  function mrna() {
    var startEl = document.getElementById("TextField");
    var lenSel = document.getElementById("PropertySelection");
    var form = startEl && startEl.closest ? startEl.closest("form") : null;
    if (!startEl || !form) return;
    hideDeadImages();
    var D = {};                       // cdna / p1 / p3
    var state = { start: 1, len: 2000, mode: 0 };  // 0 DNA, 1 three-letter, 2 one-letter
    var box = document.createElement("div"); box.id = "cfmdb-seq-results";
    form.parentNode.insertBefore(ruler(4443, "cDNA nucleotide", function (p) { startEl.value = p; state.start = p; run(); }), form);
    form.parentNode.insertBefore(box, form.nextSibling);

    function ensure(cb) {
      if (D.cdna) return cb();
      Promise.all([fetchText("sequence/cftr_cdna.txt"), fetchText("sequence/cftr_protein_1letter.txt"),
        fetchText("sequence/cftr_protein_3letter.txt")]).then(function (a) {
          D.cdna = a[0].replace(/\s+/g, ""); D.p1 = a[1].replace(/\s+/g, ""); D.p3 = a[2].replace(/\s+/g, "");
          cb();
        }).catch(function () { box.innerHTML = "<i>Could not load sequence data.</i>"; });
    }
    function renderDNA(s, len) {
      var sub = D.cdna.substr(s - 1, len), out = [], i;
      for (i = 0; i < sub.length; i += 60) out.push(pad(s + i, 6) + "  " + grouped(sub.substr(i, 60), 10));
      return { title: "cDNA (coding) — nt " + s + "–" + (s + sub.length - 1) + " of " + D.cdna.length, body: out.join("\n") };
    }
    function renderProt(s, len, three) {
      var aaFrom = Math.floor((s - 1) / 3), aaTo = Math.floor((s - 1 + len) / 3);
      var out = [], i, aa, per = three ? 15 : 60;
      for (i = aaFrom; i < aaTo; i += per) {
        var line = "";
        for (var j = i; j < Math.min(i + per, aaTo); j++) {
          aa = three ? D.p3.substr(j * 3, 3) : D.p1.charAt(j);
          line += aa + (three ? " " : ((j - i + 1) % 10 === 0 ? " " : ""));
        }
        out.push(pad(i + 1, 6) + "  " + line.replace(/ $/, ""));
      }
      return { title: (three ? "Three-letter" : "One-letter") + " polypeptide — residues "
        + (aaFrom + 1) + "–" + aaTo + " of " + D.p1.length, body: out.join("\n") };
    }
    function links() {
      function a(m, t) {
        return '<a href="#" data-mode="' + m + '" class="cfmdb-mode" style="margin-right:14px;'
          + (state.mode === m ? "font-weight:bold;text-decoration:none" : "") + '">' + t + '</a>';
      }
      return '<div style="font-size:small;margin:6px 0">Show as: '
        + a(0, "DNA sequence") + a(1, "Three-letter polypeptide") + a(2, "One-letter polypeptide") + '</div>';
    }
    function run() {
      state.start = parseInt(startEl.value, 10) || 1;
      state.len = LEN[lenSel ? lenSel.value : "3"] || 2000;
      ensure(function () {
        var s = Math.max(1, Math.min(state.start, D.cdna.length));
        var r = state.mode === 0 ? renderDNA(s, state.len) : renderProt(s, state.len, state.mode === 1);
        box.innerHTML = links() + '<div style="font-size:small;margin:6px 0"><b>' + r.title + '</b></div>' + pre(r.body);
        Array.prototype.forEach.call(box.querySelectorAll(".cfmdb-mode"), function (el) {
          el.addEventListener("click", function (e) { e.preventDefault(); state.mode = +el.getAttribute("data-mode"); run(); });
        });
      });
    }
    // wire the page's own three representation links too
    [["ServiceLink", 0], ["ServiceLink_0", 1], ["ServiceLink_1", 2]].forEach(function (p) {
      var el = document.getElementById(p[0]);
      if (el) el.addEventListener("click", function (e) { e.preventDefault(); state.mode = p[1]; run(); });
    });
    form.setAttribute("action", "#");
    form.addEventListener("submit", function (e) { e.preventDefault(); state.mode = 0; run(); });
    Array.prototype.forEach.call(form.querySelectorAll('input[type="submit"]'), function (b) {
      b.addEventListener("click", function (e) { e.preventDefault(); state.mode = 0; run(); });
    });
  }

  function init() {
    if (/GenomicDnaSequencePage/i.test(path)) genomic();
    else if (/MRnaPolypeptideSequencePage/i.test(path)) mrna();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
