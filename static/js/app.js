document.addEventListener('DOMContentLoaded', () => {
  const escapeHtml = (value = '') => String(value).replace(/[&<>'"]/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

  // Imbuements: quantidade de materiais conforme o nível.
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

  // Elementos: fraquezas, ataques e proteções.
  document.querySelectorAll('[data-element-combobox]').forEach((wrapper) => {
    const select = wrapper.querySelector('.element-search-select');
    if (!select) return;

    const syncRows = (values) => {
      const selected = new Set((values || []).map(String));
      wrapper.querySelectorAll('[data-element-row]').forEach((row) => {
        const active = selected.has(row.dataset.elementRow);
        row.classList.toggle('d-none', !active);
        const checkbox = row.querySelector('[data-element-checkbox]');
        if (checkbox) checkbox.checked = active;
        const valueInput = row.querySelector('[data-element-value]');
        if (valueInput) {
          valueInput.disabled = !active;
          if (active && valueInput.value === '') valueInput.value = '0';
        }
      });
    };

    const control = new TomSelect(select, {
      plugins: { remove_button: { title: 'Remover' } },
      placeholder: select.dataset.placeholder || 'Pesquisar...',
      create: false,
      persist: false,
      closeAfterSelect: true,
      onInitialize() { syncRows(this.getValue()); },
      onChange(values) { syncRows(values); }
    });

    wrapper.querySelectorAll('[data-remove-element]').forEach((button) => {
      button.addEventListener('click', () => control.removeItem(button.dataset.removeElement));
    });
  });

  // Monstros da hunt: busca, seleção e remoção.
  const monsterSelect = document.querySelector('#huntMonsterSelect');
  let monsterControl = null;
  const syncMonsterRows = (values) => {
    const selected = new Set((values || []).map(String));
    document.querySelectorAll('[data-monster-row]').forEach((row) => {
      const active = selected.has(String(row.dataset.monsterId));
      row.classList.toggle('d-none', !active);
      const checkbox = row.querySelector('[data-monster-checkbox]');
      if (checkbox) checkbox.checked = active;
      row.querySelectorAll('[data-charm-fields] select').forEach((control) => {
        control.disabled = !active;
        if (control.tomselect) active ? control.tomselect.enable() : control.tomselect.disable();
      });
    });
  };

  if (monsterSelect) {
    monsterControl = new TomSelect(monsterSelect, {
      plugins: { remove_button: { title: 'Remover' } },
      placeholder: monsterSelect.dataset.placeholder || 'Pesquisar monstro...',
      create: false,
      closeAfterSelect: true,
      render: {
        option(data, escape) {
          const option = data.$option;
          const image = option?.dataset.image;
          const exp = option?.dataset.exp || '0';
          const life = option?.dataset.life || '0';
          return `<div class="ts-rich-option">${image ? `<img src="${escapeHtml(image)}" alt="">` : '<span class="ts-option-placeholder"><i class="bi bi-bug"></i></span>'}<span><strong>${escape(data.text)}</strong><small>${escape(exp)} EXP • ${escape(life)} life</small></span></div>`;
        },
        item(data, escape) { return `<div>${escape(data.text)}</div>`; }
      },
      onInitialize() { syncMonsterRows(this.getValue()); },
      onChange(values) { syncMonsterRows(values); }
    });
  }

  document.querySelectorAll('[data-remove-monster]').forEach((button) => {
    button.addEventListener('click', () => monsterControl?.removeItem(button.dataset.removeMonster));
  });

  // Charms pesquisáveis, com ícone quando disponível.
  document.querySelectorAll('.searchable-charm').forEach((select) => {
    new TomSelect(select, {
      allowEmptyOption: true,
      placeholder: select.dataset.placeholder || 'Pesquisar charm...',
      create: false,
      maxItems: 1,
      render: {
        option(data, escape) {
          const image = data.$option?.dataset.image;
          return `<div class="ts-rich-option">${image ? `<img src="${escapeHtml(image)}" alt="">` : '<span class="ts-option-placeholder"><i class="bi bi-gem"></i></span>'}<span><strong>${escape(data.text)}</strong><small>Charm</small></span></div>`;
        },
        item(data, escape) { return `<div>${escape(data.text)}</div>`; }
      }
    });
  });
});
