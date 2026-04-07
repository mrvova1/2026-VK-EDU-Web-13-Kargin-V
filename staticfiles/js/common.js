
  async function loadFragment(sel, url) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(res.status);
      const html = await res.text();
      document.querySelector(sel).innerHTML = html;
    } catch (e) {
      console.error('Не удалось загрузить', url, e);
    }
  }
