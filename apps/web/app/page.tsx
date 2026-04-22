'use client';

import { useState } from 'react';
import { exportCsvUrl, exportXlsxUrl, fetchResults, runDefault, uploadFile } from '../lib/api';

type Row = {
  company_name: string;
  service_category: string;
  certificate_number: string;
  found_website: string;
  email: string;
  phone: string;
  website_match_score: number;
  contact_score: number;
  final_confidence: number;
  status: string;
  notes: string;
};

export default function HomePage() {
  const [rows, setRows] = useState<Row[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState('');
  const [missingEmail, setMissingEmail] = useState(false);
  const [missingPhone, setMissingPhone] = useState(false);
  const [selected, setSelected] = useState<Row | null>(null);

  async function doUpload() {
    if (!file) return;
    await uploadFile(file);
    alert('Uploaded');
  }

  async function run() {
    await runDefault(25);
    alert('Run started/completed for subset');
  }

  async function load() {
    const data = await fetchResults({ status: status || undefined, missing_email: missingEmail, missing_phone: missingPhone });
    setRows(data);
  }

  return (
    <main>
      <h1>Nigeria Contact Enricher</h1>
      <div style={{ display: 'grid', gap: 8, maxWidth: 960, background: '#fff', padding: 16, borderRadius: 8 }}>
        <h3>Upload</h3>
        <input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <button onClick={doUpload}>Upload Spreadsheet</button>

        <h3>Run Processing</h3>
        <button onClick={run}>Run Processing (subset)</button>

        <h3>Filters</h3>
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All</option>
          <option value="auto_accept">High confidence</option>
          <option value="review_needed">Review needed</option>
          <option value="no_match">No match</option>
        </select>
        <label><input type="checkbox" checked={missingEmail} onChange={(e) => setMissingEmail(e.target.checked)} /> Missing email</label>
        <label><input type="checkbox" checked={missingPhone} onChange={(e) => setMissingPhone(e.target.checked)} /> Missing phone</label>
        <button onClick={load}>Refresh Results</button>

        <div style={{ display: 'flex', gap: 8 }}>
          <a href={exportCsvUrl} target="_blank">Export CSV</a>
          <a href={exportXlsxUrl} target="_blank">Export XLSX</a>
        </div>
      </div>

      <table style={{ width: '100%', marginTop: 16, background: '#fff', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {['company name','service category','certificate number','found website','email','phone','website score','contact score','final confidence','status','notes'].map((h) => <th key={h} style={{ border: '1px solid #ddd', padding: 8 }}>{h}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} onClick={() => setSelected(r)} style={{ cursor: 'pointer' }}>
              <td style={{ border: '1px solid #ddd', padding: 8 }}>{r.company_name}</td>
              <td style={{ border: '1px solid #ddd', padding: 8 }}>{r.service_category}</td>
              <td style={{ border: '1px solid #ddd', padding: 8 }}>{r.certificate_number}</td>
              <td style={{ border: '1px solid #ddd', padding: 8 }}>{r.found_website}</td>
              <td style={{ border: '1px solid #ddd', padding: 8 }}>{r.email}</td>
              <td style={{ border: '1px solid #ddd', padding: 8 }}>{r.phone}</td>
              <td style={{ border: '1px solid #ddd', padding: 8 }}>{r.website_match_score}</td>
              <td style={{ border: '1px solid #ddd', padding: 8 }}>{r.contact_score}</td>
              <td style={{ border: '1px solid #ddd', padding: 8 }}>{r.final_confidence}</td>
              <td style={{ border: '1px solid #ddd', padding: 8 }}>{r.status}</td>
              <td style={{ border: '1px solid #ddd', padding: 8 }}>{r.notes}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {selected && (
        <div style={{ position: 'fixed', right: 20, top: 20, width: 420, background: '#fff', border: '1px solid #ddd', padding: 16 }}>
          <button onClick={() => setSelected(null)} style={{ float: 'right' }}>Close</button>
          <h3>Row Detail</h3>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(selected, null, 2)}</pre>
        </div>
      )}
    </main>
  );
}
