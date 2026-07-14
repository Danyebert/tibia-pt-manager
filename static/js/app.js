document.addEventListener('DOMContentLoaded', () => {
  const level = document.querySelector('#level');
  const counts = { Basic: 1, Intricate: 2, Powerful: 3 };
  if (level) {
    const updateItems = () => {
      const count = counts[level.value] || 1;
      document.querySelectorAll('.item-field').forEach((field, index) => {
        const active = index < count;
        field.classList.toggle('d-none', !active);
        field.querySelectorAll('input').forEach(input => input.required = active && input.name.includes('item_name'));
      });
      const stars = document.querySelector('#levelStars');
      if (stars) stars.textContent = '★'.repeat(count);
    };
    level.addEventListener('change', updateItems);
    updateItems();
  }

  document.querySelectorAll('[data-monster-row]').forEach((row) => {
    const checkbox = row.querySelector('[data-monster-checkbox]');
    const fields = row.querySelector('[data-charm-fields]');
    if (!checkbox || !fields) return;
    const update = () => {
      fields.classList.toggle('is-disabled', !checkbox.checked);
      fields.querySelectorAll('select').forEach(control => control.disabled = !checkbox.checked);
    };
    checkbox.addEventListener('change', update);
    update();
  });
});
