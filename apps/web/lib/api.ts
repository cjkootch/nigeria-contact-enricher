const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export async function uploadFile(file: File) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API_BASE}/upload`, { method: 'POST', body: form });
  return res.json();
}

export async function runDefault(limit?: number) {
  const qs = limit ? `?limit=${limit}` : '';
  const res = await fetch(`${API_BASE}/runs/default${qs}`, { method: 'POST' });
  return res.json();
}

export async function fetchResults(filters: { status?: string; missing_email?: boolean; missing_phone?: boolean }) {
  const params = new URLSearchParams();
  if (filters.status) params.set('status', filters.status);
  if (filters.missing_email) params.set('missing_email', 'true');
  if (filters.missing_phone) params.set('missing_phone', 'true');
  const res = await fetch(`${API_BASE}/results?${params.toString()}`);
  return res.json();
}

export const exportCsvUrl = `${API_BASE}/export/csv`;
export const exportXlsxUrl = `${API_BASE}/export/xlsx`;
