(function () {
  const root = document.getElementById('viewRoot');
  const logoutBtn = document.getElementById('logoutBtn');
  const userChip = document.getElementById('userChip');

  function getUser() {
    try { return JSON.parse(localStorage.getItem('user') || 'null'); } catch (e) { return null; }
  }
  function setUser(u) {
    if (!u) localStorage.removeItem('user');
    else localStorage.setItem('user', JSON.stringify(u));
    UI.showUser(u);
    UI.showSidebar(!!u);
    logoutBtn.classList.toggle('hidden', !u);
  }

  logoutBtn.addEventListener('click', () => { setUser(null); location.hash = '#/login'; });

  function viewLogin() {
    root.innerHTML = `
      <div class="center-layout">
        <div class="card" style="width:400px">
          <div class="title">Welcome back</div>
          <div class="muted">Sign in to continue</div>
          <div style="height:8px"></div>
          <form id="loginForm" class="grid">
            <div>
              <label>Email</label>
              <input type="email" name="email" required placeholder="you@example.com" />
            </div>
            <div>
              <label>Password</label>
              <input type="password" name="password" required placeholder="••••••" />
              <div style="margin-top:6px"><label><input type="checkbox" id="loginShowPwd" /> Show password</label></div>
            </div>
            <button class="btn primary" type="submit">Sign in</button>
            <div class="muted">No account? <a href="#/register">Create one</a></div>
          </form>
        </div>
      </div>`;

    const loginShow = document.getElementById('loginShowPwd');
    if (loginShow) loginShow.addEventListener('change', (e) => {
      const pwd = root.querySelector('#loginForm input[name="password"]');
      if (pwd) pwd.type = e.target.checked ? 'text' : 'password';
    });

    root.querySelector('#loginForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.currentTarget.querySelector('button');
      btn.disabled = true;
      btn.classList.add('loading');
      const fd = new FormData(e.currentTarget);
      const email = fd.get('email');
      const password = fd.get('password');
      try {
        const res = await API.login(email, password);
        setUser(res.user);
        UI.toast('Signed in');
        location.hash = '#/dashboard';
      } catch (err) {
        UI.toast('Login failed');
      } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
      }
    });
  }

  function viewRegister() {
    root.innerHTML = `
      <div class="center-layout">
        <div class="card" style="width:400px">
          <div class="title">Create account</div>
          <div class="muted">Fast setup to start branding</div>
          <div style="height:8px"></div>
          <form id="regForm" class="grid">
            <div>
              <label>Name</label>
              <input type="text" name="name" required placeholder="Jane Doe" />
            </div>
            <div>
              <label>Email</label>
              <input type="email" name="email" required placeholder="you@example.com" />
            </div>
            <div>
              <label>Password</label>
              <input type="password" name="password" minlength="6" required placeholder="Minimum 6 characters" />
              <div style="margin-top:6px"><label><input type="checkbox" id="regShowPwd" /> Show password</label></div>
            </div>
            <button class="btn" type="submit">Create account</button>
            <div class="muted">Already have an account? <a href="#/login">Sign in</a></div>
          </form>
        </div>
      </div>`;

    const regShow = document.getElementById('regShowPwd');
    if (regShow) regShow.addEventListener('change', (e) => {
      const pwd = root.querySelector('#regForm input[name="password"]');
      if (pwd) pwd.type = e.target.checked ? 'text' : 'password';
    });

    root.querySelector('#regForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.currentTarget.querySelector('button');
      btn.disabled = true;
      btn.classList.add('loading');
      const fd = new FormData(e.currentTarget);
      const userName = fd.get('name');
      const email = fd.get('email');
      const password = fd.get('password');
      try {
        const res = await API.register(userName, email, password);
        setUser(res.user);
        UI.toast('Account created');
        location.hash = '#/dashboard';
      } catch (err) {
        UI.toast('Registration failed');
      } finally {
        btn.disabled = false;
        btn.classList.remove('loading');
      }
    });
  }

  function viewDashboard() {
    const user = getUser();
    root.innerHTML = `
      <div class="hero">
        <div class="row">
          <div class="title">Dashboard</div>
          <span class="muted">Welcome, ${user?.username || user?.email}</span>
        </div>
        <div class="row">
          <a class="btn primary" href="#/create">Create Brand</a>
        </div>
      </div>
      <div class="grid cols-2">
        <div class="card">
          <div class="title">My Brands</div>
          <div id="brandList" class="list"></div>
        </div>
        <div class="card">
          <div class="title">Tips</div>
          <div class="muted">Answer the questions thoughtfully to get the best brand output.</div>
        </div>
      </div>`;

    (async () => {
      try {
        const res = await API.listBrands(user.userId);
        const list = root.querySelector('#brandList');
        list.innerHTML = '';
        if (!res?.brands?.length) {
          list.innerHTML = `<div class="empty">No brands yet. Click Create Brand to start.</div>`;
          return;
        }
        (res.brands || []).forEach((b) => {
          const el = document.createElement('div');
          el.className = 'item';
          el.innerHTML = `
            <div class="meta">
              <strong>${b.name || 'Untitled Brand'}</strong>
              <span class="muted">${b.id}</span>
            </div>
            <div class="actions">
              <a class="btn" href="#/brand/${b.id}">Open</a>
            </div>`;
          list.appendChild(el);
        });
      } catch (_) {
        // do nothing
      }
    })();
  }

  function viewCreateBrand() {
    const user = getUser();
    root.innerHTML = `
      <div class="card">
        <div class="title">Create a new brand</div>
        <div class="muted">You can create one brand per account. If you already created one, we'll resume your form.</div>
        <div style="height:10px"></div>
        <div id="existingBrand" class="hidden"></div>
        <div style="height:10px"></div>
        <button id="createBtn" class="btn primary">Create Brand</button>
      </div>`;

    (async () => {
      try {
        const res = await API.listBrands(user.userId);
        if (res?.brands?.length) {
          const b = res.brands[0];
          const host = root.querySelector('#existingBrand');
          host.classList.remove('hidden');
          host.innerHTML = `
            <div class="item">
              <div class="meta">
                <strong>Existing brand detected</strong>
                <span class="muted">${b.name || 'Untitled'} — ${b.id}</span>
              </div>
              <div class="actions">
                <a class="btn" href="#/wizard/${b.id}">Resume form</a>
              </div>
            </div>`;
        }
      } catch (_) {}
    })();

    const btn = root.querySelector('#createBtn');
    btn.addEventListener('click', async () => {
      btn.disabled = true; const prev = btn.textContent; btn.textContent = 'Creating...';
      try {
        const existing = await API.listBrands(user.userId);
        if (existing?.brands?.length) {
          location.hash = `#/wizard/${existing.brands[0].id}`;
          return;
        }
        const res = await API.createBrand(user.userId);
        if (res?.success && res.brand?.id) {
          UI.toast('Brand created');
          location.hash = `#/wizard/${res.brand.id}`;
          return;
        }
        const after = await API.listBrands(user.userId);
        if (after?.brands?.length) {
          location.hash = `#/wizard/${after.brands[0].id}`;
          return;
        }
        UI.toast(res?.message || 'Failed to create brand');
      } catch (_) {
        try {
          const list = await API.listBrands(user.userId);
          if (list?.brands?.length) {
            location.hash = `#/wizard/${list.brands[0].id}`;
            return;
          }
        } catch (_) {}
        UI.toast('Failed to create brand');
      } finally {
        btn.disabled = false; btn.textContent = prev;
      }
    });
  }

  function viewWizard(brandId) {
    const user = getUser();
    const sections = [
      { id: 1, title: 'Brand Strategy', count: 5 },
      { id: 2, title: 'Brand Communication', count: 2 },
      { id: 3, title: 'Brand Identity', count: 1 },
      { id: 4, title: 'Marketing & Social Media', count: 2 }
    ];
    const questionTexts = [
      "What’s your business idea, and what problem does it solve for people?",
      "If your brand were wildly successful in 10 years, what would the world look like?",
      "What are three words you want people to associate with your brand — and why?",
      "Describe your ideal customer — who are they, what are they struggling with, and how does your brand help?",
      "Who else is solving this problem, and what makes your solution different or better?",
      "What name do you want for your brand? Why did you choose it?",
      "What’s the boldest promise your brand can confidently make to its customers?",
      "How should your brand look and feel visually? (e.g., playful, elegant, bold, modern, classic, etc.)",
      "Where will your audience mostly interact with your brand? (Instagram, WhatsApp, TikTok, LinkedIn, etc.)",
      "What’s the main thing you want people to do when they see your content? (Trust you? Buy? Follow?)"
    ];
    const sectionOffsets = { 1: 0, 2: 5, 3: 7, 4: 8 };
    let sIdx = 0;
    let qIdx = 0;
    const cache = {};

    function globalIndex(sectionId, qOneBased) {
      return sectionOffsets[sectionId] + (qOneBased - 1);
    }

    function render() {
      const section = sections[sIdx];
      const qOne = qIdx + 1;
      const gIdx = globalIndex(section.id, qOne);
      const totalDone = sectionOffsets[section.id] + qOne;
      const total = 10;
      const textKey = `${section.id}-${qOne}`;
      const saved = cache[textKey] || '';
      const showSuggest = gIdx !== 0;

      root.innerHTML = `
        <div class="card">
          <div class="hero">
            <div class="row">
              <a class="btn" href="#/dashboard">← Exit</a>
              <div class="title">${section.title}</div>
            </div>
            <div class="row">
              <span class="muted">Question ${qOne} of ${section.count} in this section</span>
              <span class="muted"> | Overall ${totalDone} / ${total}</span>
            </div>
          </div>
          <div class="grid">
            <div class="card">
              <div class="title">${questionTexts[gIdx] || 'Question'}</div>
              <textarea id="answerInput" rows="6" placeholder="Type your answer...">${saved}</textarea>
              <div id="feedback" class="muted" style="margin-top:8px"></div>
              <div id="chips" class="grid" style="margin-top:8px"></div>
              <div class="row" style="margin-top:10px">
                <button id="backBtn" class="btn">Back</button>
                ${showSuggest ? '<button id="suggBtn" class="btn">Get suggestions</button>' : ''}
                <button id="nextBtn" class="btn primary">Validate & Next</button>
              </div>
            </div>
          </div>
        </div>`;

      const ans = document.getElementById('answerInput');
      const feedback = document.getElementById('feedback');
      const chips = document.getElementById('chips');
      document.getElementById('backBtn').addEventListener('click', () => {
        cache[textKey] = ans.value;
        if (qIdx > 0) { qIdx -= 1; render(); return; }
        if (sIdx > 0) { sIdx -= 1; qIdx = sections[sIdx].count - 1; render(); return; }
        location.hash = '#/dashboard';
      });
      const suggBtn = document.getElementById('suggBtn');
      if (suggBtn) {
        suggBtn.addEventListener('click', async () => {
          chips.innerHTML = '';
          cache[textKey] = ans.value;
          try {
            const res = await API.getSuggestions({ userId: user.userId, brandId, section: section.id, question: qOne });
            const normalize = (data) => {
              if (!data) return [];
              if (Array.isArray(data)) return data;
              if (typeof data === 'string') { try { const j = JSON.parse(data); return Array.isArray(j) ? j : [data]; } catch (_) { return [data]; } }
              if (data.options && Array.isArray(data.options)) return data.options;
              return [];
            };
            const opts = normalize(res?.suggestions);
            if (!opts.length) { UI.toast('No suggestions'); return; }
            opts.forEach(o => {
              const b = document.createElement('button');
              b.className = 'btn';
              b.textContent = o;
              b.addEventListener('click', () => { ans.value = o; });
              chips.appendChild(b);
            });
          } catch (e) { UI.toast('Failed to fetch suggestions'); }
        });
      }
      document.getElementById('nextBtn').addEventListener('click', async () => {
        const val = (ans.value || '').trim();
        feedback.textContent = '';
        if (!val) { feedback.textContent = 'Please enter an answer.'; return; }
        const btn = document.getElementById('nextBtn');
        btn.disabled = true; btn.textContent = 'Validating...';
        try {
          const result = await API.sendAnswer({ userId: user.userId, brandId, section: section.id, question: qOne, answer: val });
          if (result.ok) {
            cache[textKey] = val;
            if (qIdx + 1 < section.count) { qIdx += 1; render(); }
            else if (sIdx + 1 < sections.length) { sIdx += 1; qIdx = 0; render(); }
            else { UI.toast('All questions completed'); location.hash = `#/brand/${brandId}`; }
          } else {
            const msg = result?.data?.message || result?.data?.error || 'Validation failed. Please refine your answer.';
            feedback.textContent = msg;
          }
        } catch (e) {
          feedback.textContent = 'Validation failed. Please refine your answer.';
        } finally {
          btn.disabled = false; btn.textContent = 'Validate & Next';
        }
      });
    }

    render();
  }

  function viewBrand(brandId) {
    const tabs = ['overview','qa','results','final','assets'];
    root.innerHTML = `
      <div class="hero">
        <div class="row">
          <a class="btn" href="#/dashboard">← Back</a>
          <div class="title">Brand</div>
        </div>
        <div class="row">
          <div class="segmented" id="tabs">
            ${tabs.map((t,i)=>`<button data-tab="${t}" class="${i===0?'active':''}">${t.toUpperCase()}</button>`).join('')}
          </div>
        </div>
      </div>
      <div id="tabView"></div>`;

    const tabView = root.querySelector('#tabView');
    const switchTab = async (name) => {
      document.querySelectorAll('#tabs button').forEach(b=>b.classList.toggle('active', b.dataset.tab===name));
      if (name === 'overview') {
        const brand = await API.getBrand(brandId);
        const paid = await API.getPaidStatus(brandId).catch(()=>({payment_status:false}));
        tabView.innerHTML = `
          <div class="grid cols-2">
            <div class="card">
              <div class="title">Summary</div>
              <div class="muted">${brand.name || 'Untitled'}</div>
              <div style="height:8px"></div>
              <div class="list">
                <div class="item"><div class="meta"><strong>ID</strong><span class="muted">${brandId}</span></div></div>
                <div class="item"><div class="meta"><strong>Paid</strong><span class="muted">${paid.payment_status ? 'Yes' : 'No'}</span></div></div>
              </div>
              <div style="height:10px"></div>
              <button id="payBtn" class="btn primary">Pay Now</button>
            </div>
            <div class="card">
              <div class="title">PDF</div>
              <div class="muted">Download your brand book after generating results.</div>
              <div style="height:8px"></div>
              <a class="btn" href="${API.downloadPdfUrl(brandId)}" target="_blank">Download PDF</a>
            </div>
          </div>`;
        tabView.querySelector('#payBtn').addEventListener('click', async ()=>{
          try { await API.setPaid(brandId); UI.toast('Marked as paid'); switchTab('overview'); } catch(e){ UI.toast('Failed to set paid'); }
        });
      }
      if (name === 'qa') {
        const resp = await API.getFullBrand(brandId).catch(()=>null);
        const full = resp?.full_brand || resp; // support current and legacy shapes
        const answerId = full?.brand?.answerid || full?.brand?.answerId;
        tabView.innerHTML = `
          <div class="grid cols-2">
            <div class="card">
              <div class="title">Questions</div>
              <div id="qaForm" class="grid">
                <div>
                  <label>Section</label>
                  <select id="section"><option value="1">Brand Strategy</option><option value="2">Brand Communication</option><option value="3">Brand Identity</option><option value="4">Marketing</option></select>
                </div>
                <div>
                  <label>Question #</label>
                  <input id="question" type="number" min="1" max="10" value="1" />
                </div>
                <div>
                  <label>Your answer</label>
                  <textarea id="answer" rows="5" placeholder="Type your answer..."></textarea>
                </div>
                <div class="row">
                  <button id="suggestBtn" class="btn">Get Suggestions</button>
                  <button id="saveBtn" class="btn primary">Save Answer</button>
                </div>
              </div>
              <div id="suggestions" class="grid" style="margin-top:8px"></div>
            </div>
            <div class="card">
              <div class="title">Images</div>
              <div class="grid">
                <input id="imgPrompt" placeholder="Describe an image to generate..." />
                <button id="imgBtn" class="btn">Generate Image</button>
                <div id="imgGrid" class="grid cols-3"></div>
              </div>
            </div>
          </div>`;
        const uid = getUser().userId;
        tabView.querySelector('#suggestBtn').addEventListener('click', async ()=>{
          const section = Number(tabView.querySelector('#section').value);
          const q = Number(tabView.querySelector('#question').value);
          try {
            const res = await API.getSuggestions({ userId: uid, brandId, section, question: q });
            const host = tabView.querySelector('#suggestions'); host.innerHTML='';
            const normalize = (data) => {
              if (!data) return [];
              if (Array.isArray(data)) return data;
              if (typeof data === 'string') { try { const j = JSON.parse(data); return Array.isArray(j) ? j : [data]; } catch (_) { return [data]; } }
              if (data.options && Array.isArray(data.options)) return data.options;
              return [];
            };
            const opts = normalize(res?.suggestions);
            if (!opts.length) { UI.toast('No suggestions'); return; }
            opts.forEach(o => {
              const b = document.createElement('button');
              b.className = 'btn';
              b.textContent = o;
              b.addEventListener('click', () => { tabView.querySelector('#answer').value = o; });
              host.appendChild(b);
            });
          } catch(e){ UI.toast('No suggestions'); }
        });
        tabView.querySelector('#saveBtn').addEventListener('click', async ()=>{
          const section = Number(tabView.querySelector('#section').value);
          const q = Number(tabView.querySelector('#question').value);
          const text = tabView.querySelector('#answer').value;
          try { await API.sendAnswer({ userId: uid, brandId, section, question: q, answer: text }); UI.toast('Saved'); } catch(e){ UI.toast('Save failed'); }
        });
        tabView.querySelector('#imgBtn').addEventListener('click', async ()=>{
          const prompt = tabView.querySelector('#imgPrompt').value;
          if (!answerId) { UI.toast('Answer set not found'); return; }
          try { await API.generateImage({ prompt, answerId, section:1, question:1, userId: uid }); UI.toast('Image requested'); loadImages(); } catch(e){ UI.toast('Image failed'); }
        });
        async function loadImages(){
          const grid = tabView.querySelector('#imgGrid');
          grid.innerHTML='';
          try { const res = await API.listImages(answerId, uid); (res||[]).forEach(img=>{
            const card = document.createElement('div'); card.className='card';
            card.innerHTML = `<img src="${img.cloudinary_url}" alt="" style="max-width:100%; border-radius:8px" />`;
            grid.appendChild(card);
          }); } catch(e){}
        }
        if (answerId) loadImages();
      }
      if (name === 'results') {
        const uid = getUser().userId;
        tabView.innerHTML = `<div class="card"><div class="title">Results</div><button id="gen" class="btn primary">Generate</button><pre id="out" style="white-space:pre-wrap"></pre></div>`;
        tabView.querySelector('#gen').addEventListener('click', async ()=>{
          const out = tabView.querySelector('#out'); out.textContent = 'Generating...';
          try { const res = await API.generateResults(uid, brandId); out.textContent = JSON.stringify(res, null, 2); } catch(e){ out.textContent = 'Failed to generate'; }
        });
      }
      if (name === 'final') {
        const user = getUser();
        tabView.innerHTML = `
          <div class="card">
            <div class="title">Final (Paid) Results</div>
            <div class="muted">Enter details and generate final assets</div>
            <div class="grid cols-2" id="finalForm">
              <div><label>Your Name</label><input id="fn_name" value="${user.username||''}"/></div>
              <div><label>Your Email</label><input id="fn_email" value="${user.email||''}"/></div>
              <div><label>Phone Numbers</label><input id="fn_phone" /></div>
              <div><label>Registration Number</label><input id="fn_reg" /></div>
              <div><label>Website</label><input id="fn_web" placeholder="https://..."/></div>
              <div><label>Logo URL</label><input id="fn_logo" placeholder="https://..."/></div>
            </div>
            <div class="row" style="margin-top:10px">
              <button id="finalBtn" class="btn primary">Generate Final</button>
              <a class="btn" href="${API.downloadPdfUrl(brandId)}" target="_blank">Download PDF</a>
            </div>
            <pre id="finalOut" style="white-space:pre-wrap; margin-top:10px"></pre>
          </div>`;
        tabView.querySelector('#finalBtn').addEventListener('click', async ()=>{
          const payload = {
            userId: user.userId, brandId,
            userName: document.getElementById('fn_name').value,
            userEmail: document.getElementById('fn_email').value,
            userPhoneNumbers: document.getElementById('fn_phone').value,
            registrationNumber: document.getElementById('fn_reg').value,
            website: document.getElementById('fn_web').value,
            brandLogo: document.getElementById('fn_logo').value,
            others: {}
          };
          const out = document.getElementById('finalOut'); out.textContent='Generating final...';
          try { const res = await API.generateFinalResults(payload); out.textContent = JSON.stringify(res, null, 2); } catch(e){ out.textContent='Failed to generate'; }
        });
      }
      if (name === 'assets') {
        const resp = await API.getFullBrand(brandId).catch(()=>null);
        const full = resp?.full_brand || resp;
        tabView.innerHTML = `<div class="card"><div class="title">Assets</div><pre style="white-space:pre-wrap">${full?JSON.stringify(full,null,2):'No assets yet.'}</pre></div>`;
      }
    };

    document.querySelectorAll('#tabs button').forEach(b=> b.addEventListener('click', ()=> switchTab(b.dataset.tab)));
    switchTab('overview');
  }

  function router() {
    const user = getUser();
    const hash = location.hash || '#/dashboard';
    const needAuth = !(hash.startsWith('#/login') || hash.startsWith('#/register'));
    if (needAuth && !user) { viewLogin(); return; }
    if (!needAuth && user) { location.hash = '#/dashboard'; return; }
    if (hash.startsWith('#/login')) return viewLogin();
    if (hash.startsWith('#/register')) return viewRegister();
    if (hash.startsWith('#/dashboard')) return viewDashboard();
    if (hash.startsWith('#/create')) return viewCreateBrand();
    if (hash.startsWith('#/brand/')) return viewBrand(hash.split('/')[2]);
    if (hash.startsWith('#/wizard/')) return viewWizard(hash.split('/')[2]);
    return viewDashboard();
  }

  window.addEventListener('hashchange', router);
  setUser(getUser());
  router();
})();
