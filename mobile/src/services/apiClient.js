import { httpDelete, httpGet, httpPatch, httpPost, httpPut } from './httpClient';

const buildQuery = (params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  });
  const out = query.toString();
  return out ? `?${out}` : '';
};

const normalizeBody = (body, headers = {}) => {
  if (body instanceof FormData) {
    const normalized = { ...headers };
    delete normalized['Content-Type'];
    return { body, headers: normalized };
  }

  if (body === undefined || body === null) return { body: undefined, headers };

  return {
    body,
    headers,
  };
};

const wrap = async (promise) => ({ data: await promise });

const api = {
  async get(url, config = {}) {
    const query = buildQuery(config.params);
    return wrap(httpGet(`${url}${query}`, { headers: config.headers }));
  },

  async post(url, body, config = {}) {
    const payload = normalizeBody(body, config.headers);
    return wrap(httpPost(url, payload.body, { headers: payload.headers }));
  },

  async put(url, body, config = {}) {
    const payload = normalizeBody(body, config.headers);
    return wrap(httpPut(url, payload.body, { headers: payload.headers }));
  },

  async patch(url, body, config = {}) {
    const payload = normalizeBody(body, config.headers);
    return wrap(httpPatch(url, payload.body, { headers: payload.headers }));
  },

  async delete(url, config = {}) {
    return wrap(httpDelete(url, { headers: config.headers }));
  },
};

export default api;
