function toggleDropdown(taskId) {
  const dd = document.getElementById('dropdown-' + taskId);
  document.querySelectorAll('.dropdown-content')
    .forEach(d => { if (d !== dd) d.style.display = 'none'; });
  dd.style.display = dd.style.display === 'block' ? 'none' : 'block';
}

function selectFriend(e, taskId) {
  e.stopPropagation();
  const card = e.currentTarget;
  const clientId   = card.getAttribute('data-client-id');
  const clientName = card.getAttribute('data-client-name');
  const dropdown   = document.getElementById('dropdown-' + taskId);
  const selected   = document.getElementById('selected-' + taskId);
  const placeholder= document.getElementById('placeholder-' + taskId);

  // remove from dropdown
  card.remove();

  // remove placeholder if first selection
  if (placeholder) {
    placeholder.remove();
  }

  // create avatar bubble
  const bub = document.createElement('div');
  bub.className = 'selected-friend';
  bub.setAttribute('data-client-id', clientId);
  bub.innerHTML = `<img src="/static/profile_pics/${clientId}.png"
                    alt="${clientName}" title="${clientName}">`;
  // click avatar to deselect
  bub.addEventListener('click', () => {
    bub.remove();
    // restore card in dropdown
    dropdown.appendChild(card);
    // if no more selected, put placeholder back
    if (selected.children.length === 0) {
      const ph = document.createElement('div');
      ph.className = 'friend-placeholder';
      ph.id = 'placeholder-' + taskId;
      ph.innerHTML = `<img src="/static/profile_pics/placeholder.png"
                         alt="No assignee" />`;
      selected.appendChild(ph);
    }
  });

  selected.appendChild(bub);
}

document.addEventListener('click', function(e) {
  if (!e.target.closest('.dropdown-wrapper')) {
    document.querySelectorAll('.dropdown-content')
      .forEach(d => d.style.display = 'none');
  }
});
