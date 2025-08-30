(function () {
  const JSON_HEADERS = { 'Content-Type': 'application/json' };
  const ok = (r) => { if (!r.ok) throw new Error('Request failed'); return r.json(); };
  const post = (url, body) => fetch(url, { method: 'POST', headers: JSON_HEADERS, body: JSON.stringify(body||{}) }).then(ok);
  const get = (url) => fetch(url).then(ok);
  const postSoft = async (url, body) => {
    const res = await fetch(url, { method: 'POST', headers: JSON_HEADERS, body: JSON.stringify(body||{}) });
    let data = null; try { data = await res.json(); } catch (_) { data = null; }
    return { ok: res.ok, status: res.status, data };
  };

  window.API = {
    // auth
    register: (userName, email, password) => post('/register_user', { userName, email, password }),
    login: (email, password) => post('/login', { email, password }),
    user: (userId) => post('/user', { userId }),

    // brands
    createBrand: (userId) => post('/create_brand', { userId }),
    listBrands: (userId) => post('/user_brands', { userId }),
    getBrand: (brandId) => post('/brand', { brandId }),
    getFullBrand: (brandId) => get(`/get_full_brand/${encodeURIComponent(brandId)}`),

    // q&a
    sendAnswer: (payload) => postSoft('/send_answer', payload),
    getSuggestions: (payload) => post('/get_suggestions', payload),

    // results
    generateResults: (userId, brandId) => post('/get_results', { userId, brandId }),
    generateFinalResults: (payload) => post('/get_final_results', payload),
    downloadPdfUrl: (brandId) => `/download_brand_pdf/${encodeURIComponent(brandId)}`,

    // images
    generateImage: (payload) => post('/generate_and_upload_image', payload),
    listImages: (answerId, userId) => post('/get_all_images', { answerId, userId }),
    deleteImage: (answerId, section, question, userId) => post('/delete_image', { answerId, section, question, userId }),

    // payment simulation
    setPaid: (brandId) => post('/update_brand_payment_status', { brandId, paymentStatus: true }),
    getPaidStatus: (brandId) => get(`/check_brand_payment_status/${encodeURIComponent(brandId)}`),
    getAdminStats: () => get('/admin/stats')
  };
})();


