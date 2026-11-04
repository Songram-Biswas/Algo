/**
 * Minimal server-side Supabase admin client (no extra dependencies).
 *
 * Uses the SERVICE ROLE key, which bypasses Row Level Security.
 * NEVER import this from frontend code or expose the key to the browser.
 */

const DEFAULT_SUPABASE_URL = 'https://hqbkdivhdotpshgrkrmg.supabase.co';

function getConfig() {
  const url = (process.env.SUPABASE_URL || DEFAULT_SUPABASE_URL).replace(/\/+$/, '');
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceKey) {
    const err = new Error('SUPABASE_SERVICE_ROLE_KEY is not set.');
    err.code = 'CONFIG';
    throw err;
  }
  return { url, serviceKey };
}

async function request(path, { searchParams, ...init } = {}) {
  const { url, serviceKey } = getConfig();
  const target = new URL(url + path);
  if (searchParams) {
    for (const [k, v] of Object.entries(searchParams)) target.searchParams.set(k, v);
  }
  const res = await fetch(target, {
    ...init,
    headers: {
      apikey: serviceKey,
      Authorization: `Bearer ${serviceKey}`,
      'Content-Type': 'application/json',
      ...(init.headers || {}),
    },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    const err = new Error(`Supabase ${init.method || 'GET'} ${path} failed: ${res.status} ${body.slice(0, 300)}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

/**
 * Lists every Auth user (paginated through the GoTrue admin API).
 * @returns {Promise<Array<{ id: string, email?: string, user_metadata?: object, banned_until?: string }>>}
 */
async function listAllUsers({ perPage = 1000, maxPages = 50 } = {}) {
  const users = [];
  for (let page = 1; page <= maxPages; page += 1) {
    const data = await request('/auth/v1/admin/users', {
      searchParams: { page: String(page), per_page: String(perPage) },
    });
    const batch = Array.isArray(data) ? data : data.users || [];
    users.push(...batch);
    if (batch.length < perPage) break;
  }
  return users;
}

/**
 * PostgREST select helper.
 * @param {string} table
 * @param {Record<string,string>} query  e.g. { select: 'user_id,xp', pod_date: 'eq.2026-11-04' }
 */
function select(table, query = {}) {
  return request(`/rest/v1/${encodeURIComponent(table)}`, { searchParams: query });
}

module.exports = { listAllUsers, select };
