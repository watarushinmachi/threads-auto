// 共通スライドナビ：矢印/スペース/クリックで移動、リサイズで16:9をフィット
(function () {
  const slides = Array.from(document.querySelectorAll('.slide'));
  const deck = document.querySelector('.deck');
  const pager = document.querySelector('.pager');
  let i = 0;

  function show(n) {
    i = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach((s, idx) => s.classList.toggle('active', idx === i));
    if (pager) pager.textContent = (i + 1) + ' / ' + slides.length;
  }
  function next() { show(i + 1); }
  function prev() { show(i - 1); }

  document.addEventListener('keydown', (e) => {
    if (['ArrowRight', 'ArrowDown', ' ', 'PageDown'].includes(e.key)) { e.preventDefault(); next(); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); prev(); }
    else if (e.key === 'Home') show(0);
    else if (e.key === 'End') show(slides.length - 1);
  });
  document.addEventListener('click', (e) => {
    if (e.target.closest('a')) return;
    // 画面左1/4クリックで戻る、それ以外で進む
    (e.clientX < window.innerWidth * 0.25) ? prev() : next();
  });

  // 16:9をウィンドウにフィット
  function fit() {
    if (!deck) return;
    const scale = Math.min(window.innerWidth / 1280, window.innerHeight / 720);
    deck.style.transform = 'scale(' + scale + ')';
  }
  window.addEventListener('resize', fit);
  fit();
  show(0);
})();
