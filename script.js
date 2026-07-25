document.querySelectorAll('.card').forEach((card) => {
  card.addEventListener('click', () => card.setAttribute('aria-label', `${card.querySelector('h3').textContent} 열기`));
});
