/* Research Lab Wiki — progressive enhancement. No dependencies.
   One file serves hub + article pages; every feature is guarded by element presence. */
(function () {
  "use strict";

  // 1) Reading-progress bar (article pages)
  var bar = document.querySelector(".progress > span");
  if (bar) {
    var update = function () {
      var h = document.documentElement;
      var max = h.scrollHeight - h.clientHeight;
      var top = h.scrollTop || document.body.scrollTop;
      bar.style.width = (max > 0 ? (top / max) * 100 : 0) + "%";
    };
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  // 2) Table-of-contents active-section highlight (article pages)
  var toc = document.querySelector("nav.toc");
  if (toc && "IntersectionObserver" in window) {
    var links = {};
    Array.prototype.forEach.call(toc.querySelectorAll('a[href^="#"]'), function (a) {
      links[a.getAttribute("href").slice(1)] = a;
    });
    var targets = Object.keys(links)
      .map(function (id) { return document.getElementById(id); })
      .filter(Boolean);
    var current = null;
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) current = e.target.id; });
      Object.keys(links).forEach(function (id) {
        links[id].classList.toggle("active", id === current);
      });
    }, { rootMargin: "-70px 0px -70% 0px", threshold: 0 });
    targets.forEach(function (t) { obs.observe(t); });
  }

  // 3) Hub search / filter (hub page)
  var filter = document.querySelector("input.filter");
  var cards = document.querySelector(".cards");
  if (filter && cards) {
    var items = Array.prototype.slice.call(cards.querySelectorAll(".card"));
    var empty = document.querySelector(".no-results");
    filter.addEventListener("input", function () {
      var q = filter.value.trim().toLowerCase();
      var shown = 0;
      items.forEach(function (card) {
        var match = !q || card.textContent.toLowerCase().indexOf(q) !== -1;
        card.style.display = match ? "" : "none";
        if (match) shown++;
      });
      if (empty) empty.style.display = shown === 0 ? "block" : "none";
    });
  }
})();
