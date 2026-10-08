/* ストラテギコン図解サイト 共通スクリプト（最小限）
   1. 明暗の切り替え（ボタン .theme-toggle）。選んだ明暗はこのブラウザにだけ覚える
   2. 陣形図の差し込み：<div class="plate" data-src="…svg"> に SVG をインラインで入れる
      （インラインにしないと、ページの明暗の色が SVG に届かない。notes/plates.md §4.1）
      読み込めないとき（ファイルを直接開いたときなど）は、中の <img> がそのまま残る */
(function () {
  "use strict";
  var root = document.documentElement;

  function getStored() {
    try { return localStorage.getItem("theme"); } catch (e) { return null; }
  }
  function store(v) {
    try { localStorage.setItem("theme", v); } catch (e) { /* 保存できなくても表示は変わる */ }
  }
  var saved = getStored();
  if (saved === "light" || saved === "dark") root.setAttribute("data-theme", saved);

  function currentTheme() {
    var t = root.getAttribute("data-theme");
    if (t) return t;
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function setupToggle() {
    var btn = document.querySelector(".theme-toggle");
    if (!btn) return;
    function label() {
      btn.textContent = currentTheme() === "dark" ? "明るい表示へ" : "暗い表示へ";
    }
    label();
    btn.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      store(next);
      label();
    });
  }

  function inlinePlates() {
    var plates = document.querySelectorAll(".plate[data-src]");
    Array.prototype.forEach.call(plates, function (el) {
      if (!window.fetch) return;
      fetch(el.getAttribute("data-src"))
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
        .then(function (text) {
          var doc = new DOMParser().parseFromString(text, "image/svg+xml");
          var svg = doc.documentElement;
          if (!svg || svg.nodeName.toLowerCase() !== "svg") return;
          var img = el.querySelector("img");
          if (img) img.remove();
          el.insertBefore(document.importNode(svg, true), el.firstChild);
        })
        .catch(function () { /* <img> のまま表示する */ });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    setupToggle();
    inlinePlates();
  });
})();
