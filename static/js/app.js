document.addEventListener('DOMContentLoaded', () => {
  const level = document.querySelector('#level');
  if (!level) return;
  const counts = { Basic: 1, Intricate: 2, Powerful: 3 };
  function updateItems() {
    const count = counts[level.value];
    document.querySelectorAll('.item-field').forEach((field, index) => {
      const active = index < count;
      field.classList.toggle('d-none', !active);
      field.querySelectorAll('input').forEach(input => input.required = active && input.name.includes('item_name'));
    });
    document.querySelector('#levelStars').textContent = '★'.repeat(count);
  }
  level.addEventListener('change', updateItems);
  updateItems();
});
