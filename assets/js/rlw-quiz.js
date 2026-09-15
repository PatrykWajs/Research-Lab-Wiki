/* Research Lab Wiki — self-test quiz engine.
 * Vanilla JS, no deps. Loaded via Material `extra_javascript`.
 * Hydrates every <div class="rlw-quiz" data-*> on the page.
 * Reads its question bank INLINE from a child
 *   <script type="application/json" class="rlw-quiz-data">{"questions":[...]}</script>
 * so there is no fetch (works under any base path, e.g. /Research-Lab-Wiki/).
 * Learn mode: pick an answer -> reveal the correct one + a one-line why -> at the end,
 * score + best-ever (localStorage) + a review of what you missed. Bilingual UI via data-lang.
 */
(function () {
  "use strict";

  var UI = {
    en: {
      kicker: "Self-test",
      start_title: "Test yourself",
      start_sub: "{n} questions drawn from this page's findings. Pick an answer, see why, and learn.",
      start_btn: "Start",
      q: "Question", of: "of",
      correct: "Correct", incorrect: "Not quite", why: "Why",
      next: "Next", finish: "See score",
      end_title: "Your score", best: "Best",
      review_h: "Review what you missed", answer: "Answer",
      clean: "Clean sweep — nothing missed.", again: "Try again",
      err: "Quiz could not load."
    },
    el: {
      kicker: "Αυτο-έλεγχος",
      start_title: "Δοκίμασε τον εαυτό σου",
      start_sub: "{n} ερωτήσεις από τα ευρήματα αυτής της σελίδας. Διάλεξε απάντηση, δες το γιατί, και μάθε.",
      start_btn: "Ξεκίνα",
      q: "Ερώτηση", of: "από",
      correct: "Σωστά", incorrect: "Όχι ακριβώς", why: "Γιατί",
      next: "Επόμενη", finish: "Δες το σκορ",
      end_title: "Το σκορ σου", best: "Καλύτερο",
      review_h: "Δες τι έχασες", answer: "Απάντηση",
      clean: "Τέλεια — δεν έχασες τίποτα.", again: "Δοκίμασε ξανά",
      err: "Το κουίζ δεν φόρτωσε."
    }
  };
  var KEYS = ["A", "B", "C", "D", "E", "F"];

  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt != null) e.textContent = txt;
    return e;
  }
  function shuffle(a) {
    a = a.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1)), t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function parseCfg(node) {
    var ds = node.dataset;
    var count = parseInt(ds.count || "12", 10);
    if (isNaN(count) || count < 1) count = 12;
    var lang = ds.lang === "el" ? "el" : "en";
    return { count: count, lang: lang, t: UI[lang], id: ds.id || ("rlw:" + (location.pathname || "")) };
  }

  function readBank(node) {
    var s = node.querySelector("script.rlw-quiz-data");
    if (!s) return null;
    try {
      var d = JSON.parse(s.textContent);
      var qs = d && d.questions ? d.questions : (Array.isArray(d) ? d : null);
      if (!qs) return null;
      // keep only well-formed items
      return qs.filter(function (q) {
        return q && q.q && Array.isArray(q.options) && q.options.length >= 2 &&
          typeof q.a === "number" && q.a >= 0 && q.a < q.options.length;
      });
    } catch (e) { return null; }
  }

  function bestKey(cfg) { return "rlw-quiz:best:" + cfg.id; }
  function readBest(cfg) { try { return JSON.parse(localStorage.getItem(bestKey(cfg))); } catch (e) { return null; } }
  function writeBest(cfg, score, total) {
    try {
      var c = readBest(cfg);
      if (!c || score / total > c.score / c.total) {
        localStorage.setItem(bestKey(cfg), JSON.stringify({ score: score, total: total }));
      }
    } catch (e) { /* private mode / blocked storage */ }
  }

  function mountQuiz(node, bank) {
    var cfg = parseCfg(node), t = cfg.t;
    node.textContent = "";                       // clear the inline <script> + whitespace
    var card = el("div", "rlw-card");
    node.appendChild(card);
    var state = { qs: [], i: 0, score: 0, missed: [] };

    function draw() {
      var take = Math.min(cfg.count, bank.length);
      state.qs = shuffle(bank).slice(0, take);
      state.i = 0; state.score = 0; state.missed = [];
    }

    function renderStart() {
      card.textContent = "";
      card.appendChild(el("div", "rlw-kicker", t.kicker));
      card.appendChild(el("h3", "rlw-h", t.start_title));
      card.appendChild(el("p", "rlw-sub", t.start_sub.replace("{n}", String(Math.min(cfg.count, bank.length)))));
      var b = readBest(cfg);
      if (b) card.appendChild(el("div", "rlw-best", t.best + ": " + b.score + "/" + b.total));
      var btn = el("button", "rlw-btn", t.start_btn);
      btn.addEventListener("click", function () { draw(); renderQ(); });
      card.appendChild(btn);
    }

    function renderQ() {
      card.textContent = "";
      var q = state.qs[state.i];
      var head = el("div", "rlw-head");
      head.appendChild(el("span", "rlw-kicker", q.tier || t.kicker));
      head.appendChild(el("span", "rlw-counter", t.q + " " + (state.i + 1) + " " + t.of + " " + state.qs.length));
      card.appendChild(head);

      var pr = document.createElement("progress");
      pr.className = "rlw-progress"; pr.max = state.qs.length; pr.value = state.i;
      card.appendChild(pr);

      card.appendChild(el("p", "rlw-prompt", q.q));

      var opts = shuffle(q.options.map(function (label, idx) { return { label: label, correct: idx === q.a }; }));
      var wrap = el("div", "rlw-opts");
      var answered = false;
      opts.forEach(function (o, idx) {
        var btn = el("button", "rlw-opt");
        btn.appendChild(el("span", "rlw-opt-key", KEYS[idx]));
        btn.appendChild(el("span", "rlw-opt-label", o.label));
        btn.addEventListener("click", function () {
          if (answered) return;
          answered = true;
          Array.prototype.forEach.call(wrap.children, function (c) { c.disabled = true; });
          opts.forEach(function (oo, j) { if (oo.correct) wrap.children[j].classList.add("is-correct"); });
          if (o.correct) { state.score++; } else { btn.classList.add("is-wrong"); state.missed.push(q); }

          var fb = el("div", "rlw-feedback");
          fb.appendChild(el("div", "rlw-verdict " + (o.correct ? "ok" : "no"), o.correct ? t.correct : t.incorrect));
          if (q.why) {
            var w = el("div", "rlw-explain");
            w.appendChild(el("strong", null, t.why + ": "));
            w.appendChild(document.createTextNode(q.why));
            fb.appendChild(w);
          }
          card.appendChild(fb);

          var last = state.i === state.qs.length - 1;
          var nb = el("button", "rlw-btn", last ? t.finish : t.next);
          nb.addEventListener("click", function () { if (last) { renderEnd(); } else { state.i++; renderQ(); } });
          card.appendChild(nb);
        });
        wrap.appendChild(btn);
      });
      card.appendChild(wrap);
    }

    function renderEnd() {
      card.textContent = "";
      var total = state.qs.length;
      writeBest(cfg, state.score, total);
      var end = el("div", "rlw-end");
      end.appendChild(el("h3", "rlw-h", t.end_title));
      end.appendChild(el("div", "rlw-score", state.score + " / " + total));
      end.appendChild(el("div", "rlw-score-pct", Math.round(100 * state.score / total) + "%"));
      var b = readBest(cfg);
      if (b) end.appendChild(el("div", "rlw-best", t.best + ": " + b.score + "/" + b.total));
      end.appendChild(el("h4", "rlw-missed-h", t.review_h));
      if (!state.missed.length) {
        end.appendChild(el("p", "rlw-sub", t.clean));
      } else {
        var m = el("div", "rlw-missed");
        state.missed.forEach(function (q) {
          var it = el("div", "rlw-missed-item");
          it.appendChild(el("div", "rlw-missed-q", q.q));
          it.appendChild(el("div", "rlw-missed-a", t.answer + ": " + q.options[q.a]));
          if (q.why) it.appendChild(el("div", "rlw-missed-an", q.why));
          m.appendChild(it);
        });
        end.appendChild(m);
      }
      var again = el("button", "rlw-btn", t.again);
      again.addEventListener("click", function () { draw(); renderQ(); });
      end.appendChild(again);
      card.appendChild(end);
    }

    renderStart();
  }

  function authorError(node, msg) { node.textContent = ""; node.appendChild(el("div", "rlw-quiz-err", msg)); }

  function hydrateAll() {
    var nodes = document.querySelectorAll(".rlw-quiz:not([data-rlw-ready])");
    if (!nodes.length) return;
    nodes.forEach(function (n) {
      if (n.getAttribute("data-rlw-ready")) return;
      n.setAttribute("data-rlw-ready", "1");
      var bank = readBank(n);
      var lang = n.dataset.lang === "el" ? "el" : "en";
      if (!bank || !bank.length) { authorError(n, UI[lang].err); return; }
      try { mountQuiz(n, bank); } catch (e) { authorError(n, UI[lang].err); }
    });
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(hydrateAll);
  } else if (document.readyState !== "loading") {
    hydrateAll();
  } else {
    document.addEventListener("DOMContentLoaded", hydrateAll);
  }
})();
