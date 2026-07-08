/*
 * cfmdb_search.js — client-side reimplementation of the CFMDB (CFTR1) search
 * functions for the static preservation archive. The original Tapestry server
 * that answered these forms is gone; this reproduces the SAME inputs, matching
 * rules and result columns against a prebuilt index (records.json).
 *
 * Handles: Basic Text Search (SearchPage), Advanced Text Search
 * (AdvancedSearchPage), and the Precision + Criteria searches (MutationSearch).
 * Injected into each of those archived pages at build time; it neutralises the
 * dead form POST and renders results in-page.
 */
(function () {
  "use strict";
  var DATA = null, PENDING = [];
  function detailHref(sp) {
    // works whether the page lives at site root or under mutations/
    var base = location.pathname.indexOf("/mutations/") >= 0 ? "" : "mutations/";
    return base + "sp-" + sp + ".html";
  }
  function dataUrl() {
    return (location.pathname.indexOf("/mutations/") >= 0 ? "../" : "") + "records.json";
  }
  function load(cb) {
    if (DATA) return cb(DATA);
    PENDING.push(cb);
    if (PENDING.length > 1) return;
    fetch(dataUrl()).then(function (r) { return r.json(); }).then(function (d) {
      DATA = d; PENDING.splice(0).forEach(function (f) { f(DATA); });
    }).catch(function () {
      DATA = []; PENDING.splice(0).forEach(function (f) { f(DATA); });
    });
  }
  // lower-case, and canonicalise the delta symbol so "[delta]F508", "ΔF508"
  // and "deltaF508" all match the same records
  function norm(s) {
    return (s == null ? "" : String(s)).toLowerCase()
      .replace(/\[delta\]|Δ|∆|δ/g, "delta");
  }
  function names(r) { return [r.cdna_name, r.protein_name, r.legacy_name]; }
  function contribText(r) { return (r.contributors || []).map(function (c) { return c.names; }).join(" "); }
  function years(r) {
    return (r.contributors || []).map(function (c) { return c.date ? parseInt(c.date.slice(0, 4), 10) : null; })
      .filter(function (y) { return y; });
  }
  function fieldText(r, key) {
    switch (key) {
      case "all_names": return names(r).join(" ");
      case "cdnaName": return r.cdna_name;
      case "proteinName": return r.protein_name;
      case "name": return r.legacy_name;
      case "position": return r.cdna_name; // cDNA position lives inside the c. name
      case "phenotype": return (r.phenotype || []).join(" ");
      case "note": return r.other_details;
      case "contributors": return contribText(r);
      case "institute": return (r.institute || []).join(" ");
      case "ncchange": return r.nucleotide_change;
      case "consequence": return r.consequence;
      default: // All Fields
        return [names(r).join(" "), r.region, r.nucleotide_change, r.consequence,
          r.other_details, (r.phenotype || []).join(" "), contribText(r),
          (r.institute || []).join(" "), (r.reference || []).join(" ")].join(" ");
    }
  }
  function contains(r, key, term) { return norm(fieldText(r, key)).indexOf(norm(term)) >= 0; }

  function resultsTable(rows) {
    var h = ['<table border="1" cellspacing="2" width="100%" cellpadding="3" style="margin-top:12px">',
      '<tr>', th("cDNA Name"), th("Protein Name"), th("Legacy Name"), th("Region"),
      th("Description"), th("Consequence"), '</tr>'];
    rows.forEach(function (r) {
      h.push('<tr>',
        '<td><a href="' + detailHref(r.sp_id) + '">' + esc(r.cdna_name) + '</a></td>',
        td(r.protein_name), td(r.legacy_name), td(r.region),
        td(r.nucleotide_change), td(r.consequence), '</tr>');
    });
    h.push('</table>');
    return '<div style="font-size:small"><b>' + rows.length + '</b> mutation'
      + (rows.length === 1 ? '' : 's') + ' found</div>' + h.join("");
  }
  function th(t) { return '<td width="15%"><span class="thead">' + t + '</span></td>'; }
  function td(t) { return '<td>' + esc(t || "") + '</td>'; }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  }
  function mount(form) {
    var box = document.getElementById("cfmdb-results");
    if (!box) { box = document.createElement("div"); box.id = "cfmdb-results"; form.parentNode.insertBefore(box, form.nextSibling); }
    return box;
  }
  function show(form, rows) { mount(form).innerHTML = resultsTable(rows); }

  // ---- Basic Text Search (SearchPage) ----
  function wireBasic(form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var field = form.querySelector("#PropertySelection").value;
      var term = form.querySelector("#mutationSearchValue").value.trim();
      load(function (d) {
        var rows = !term ? [] : d.filter(function (r) { return contains(r, field, term); });
        show(form, rows);
      });
    });
  }

  // ---- Advanced Text Search (AdvancedSearchPage) ----
  var AD = [["cdnaname_ad", "cdnaName"], ["proteinname_ad", "proteinName"],
    ["mutationName_ad", "name"], ["ncchange_ad", "ncchange"],
    ["consequence_ad", "consequence"], ["original_node_ad", "note"],
    ["phenotype_ad", "phenotype"]];
  function multiVals(form, sel) {
    var el = form.querySelector(sel);
    if (!el) return [];
    return Array.prototype.filter.call(el.options, function (o) { return o.selected && o.value; })
      .map(function (o) { return norm(o.text || o.value); });
  }
  function wireAdvanced(form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var op = (form.querySelector('input[name="searchCriteria"]:checked') || {}).value; // 0=and 1=or
      var terms = AD.map(function (p) {
        var el = form.querySelector("#" + p[0]); return el && el.value.trim() ? [p[1], el.value.trim()] : null;
      }).filter(Boolean);
      var exons = multiVals(form, "#exonChooser"), introns = multiVals(form, "#intronChooser"),
        types = multiVals(form, "#mutationChooser");
      var fromY = intOr(form, "#fromYearChooser"), toY = intOr(form, "#toYearChooser");
      var inst = valOf(form, "#institute_ad"), contr = valOf(form, "#contributor_ad");
      load(function (d) {
        var rows = d.filter(function (r) {
          var checks = [];
          terms.forEach(function (t) { checks.push(contains(r, t[0], t[1])); });
          if (inst) checks.push(norm((r.institute || []).join(" ")).indexOf(norm(inst)) >= 0);
          if (contr) checks.push(norm(contribText(r)).indexOf(norm(contr)) >= 0);
          var regionChecks = [];
          if (exons.length || introns.length) {
            var reg = norm(r.region) + " " + norm(r.legacy_region);
            regionChecks = exons.concat(introns).map(function (x) { return reg.indexOf(x) >= 0; });
          }
          if (types.length) checks.push(types.indexOf(norm(r.func_type)) >= 0);
          var yy = years(r);
          if (fromY) checks.push(yy.some(function (y) { return y >= fromY; }));
          if (toY) checks.push(yy.some(function (y) { return y <= toY; }));
          var all = checks.concat(regionChecks.length ? [regionChecks.some(Boolean)] : []);
          if (!all.length) return false;
          return op === "0" ? all.every(Boolean) : all.some(Boolean);
        });
        show(form, rows);
      });
    });
  }
  function valOf(form, sel) { var el = form.querySelector(sel); return el ? el.value.trim() : ""; }
  function intOr(form, sel) { var v = valOf(form, sel); return v ? parseInt(v, 10) : null; }

  // ---- Precision Search (MutationSearch) ----
  function wirePrecision(form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var t0 = valOf(form, "#TextField"), t1 = valOf(form, "#TextField_0"), t2 = valOf(form, "#TextField_1");
      var term = [t0, t1, t2].filter(Boolean)[0] || "";
      var propMap = { "0": "cdnaName", "1": "proteinName", "2": "name", "3": "all", "4": "institute", "5": "contributors" };
      var field = propMap[valOf(form, "#PropertySelection")] || "all_names";
      load(function (d) {
        var rows = !term ? [] : d.filter(function (r) { return contains(r, field === "all" ? "" : field, term); });
        show(form, rows);
      });
    });
  }

  // ---- Criteria Search (MutationSearch) ----
  function wireCriteria(form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var structIdx = valOf(form, "#mutationTypeSelector");
      var STRUCT = { "1": "substitution", "2": "deletion", "3": "insertion",
        "4": "insertion/deletion", "5": "inversion", "6": "microsatellite", "7": "duplication" };
      var stype = STRUCT[structIdx] || "";
      var coding = multiVals(form, "#codingChooser"), noncoding = multiVals(form, "#nonCodingChooser");
      load(function (d) {
        var rows = d.filter(function (r) {
          if (stype && norm(r.struct_type) !== stype) return false;
          if (coding.length || noncoding.length) {
            var reg = norm(r.region) + " " + norm(r.legacy_region);
            if (!coding.concat(noncoding).some(function (x) { return reg.indexOf(x) >= 0; })) return false;
          }
          return true;
        });
        show(form, rows);
      });
    });
  }

  function init() {
    document.querySelectorAll("form").forEach(function (form) {
      // neutralise the dead Tapestry endpoint
      form.setAttribute("action", "#");
      if (form.querySelector("#mutationSearchValue")) wireBasic(form);
      else if (form.querySelector("#cdnaname_ad")) wireAdvanced(form);
      else if (form.id === "precisionSearchForm" || form.querySelector("#precisionSearchButton")) wirePrecision(form);
      else if (form.id === "criteriaSearchForm" || form.querySelector("#criteriaSearchButton")) wireCriteria(form);
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
