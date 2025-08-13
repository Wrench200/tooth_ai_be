(function () {
  const byId = (id) => document.getElementById(id);
  const toastHost = byId('toastHost');
  function toast(message) {
    const el = document.createElement('div');
    el.className = 'toast';
    el.textContent = message;
    toastHost.appendChild(el);
    setTimeout(() => el.remove(), 2800);
  }

  const themeBtn = byId('themeToggle');
  function applyTheme(next) {
    document.body.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) {}
    themeBtn.textContent = next === 'dark' ? '☀️' : '🌙';
  }
  themeBtn.addEventListener('click', () => {
    const cur = document.body.getAttribute('data-theme') || 'light';
    applyTheme(cur === 'light' ? 'dark' : 'light');
  });

  window.UI = {
    toast,
    showUser(user) {
      const chip = byId('userChip');
      const name = byId('userName');
      const avatar = byId('userAvatar');
      if (!user) { chip.classList.add('hidden'); return; }
      name.textContent = user.username || user.email || 'User';
      if (user.profile_picture) { avatar.src = user.profile_picture; avatar.classList.remove('hidden'); }
      else { avatar.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAAAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=='; }
      chip.classList.remove('hidden');
    },
    showSidebar(show) {
      const sb = document.getElementById('sidebar');
      if (!sb) return;
      sb.classList.toggle('hidden', !show);
    }
  };
})();


