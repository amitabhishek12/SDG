// Thin API client. All requests go through the same origin (/api), proxied to
// the FastAPI backend in dev.

const BASE = import.meta.env.VITE_API_BASE || "";

async function jsonOrThrow(res) {
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function getConfig() {
  return jsonOrThrow(await fetch(`${BASE}/api/config`));
}

export async function getErps() {
  const data = await jsonOrThrow(await fetch(`${BASE}/api/erps`));
  return data.erps;
}

export async function searchTables(erpId, q) {
  const url = `${BASE}/api/erp-tables/search?erp_id=${encodeURIComponent(
    erpId
  )}&q=${encodeURIComponent(q)}`;
  return jsonOrThrow(await fetch(url));
}

// Returns the full table schema: { erp_id, table, description, source, fields }
export async function getErpSchema(erpId, table) {
  const url = `${BASE}/api/erp-schema?erp_id=${encodeURIComponent(
    erpId
  )}&table=${encodeURIComponent(table)}`;
  return jsonOrThrow(await fetch(url));
}

export async function uploadSchema(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/api/upload-schema`, {
    method: "POST",
    body: form,
  });
  const data = await jsonOrThrow(res);
  return data.schema;
}

export async function getPreview(schema) {
  const res = await fetch(`${BASE}/api/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ schema }),
  });
  return jsonOrThrow(res);
}

export async function generate(schema, count, fmt) {
  const res = await fetch(`${BASE}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ schema, count, fmt }),
  });
  if (!res.ok) {
    let detail = `Generation failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  const blob = await res.blob();
  const cd = res.headers.get("Content-Disposition") || "";
  const match = cd.match(/filename=([^;]+)/);
  const filename = match ? match[1].trim() : `synthetic_data.${fmt}`;
  return { blob, filename };
}

export function templateUrl(fmt) {
  return `${BASE}/api/template?fmt=${fmt}`;
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
