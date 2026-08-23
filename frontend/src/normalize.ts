// Client-side mirror of backend/app/normalize.py — used for immediate inline
// validation feedback as the user types; the backend re-validates authoritatively.

const PROTOCOL_RE = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//;
const SPLIT_RE = /[\s,]+/;

export function normalizeDomain(rawUrl: string): string | null {
  let url = rawUrl.trim();
  if (!url) return null;

  url = url.replace(PROTOCOL_RE, "");
  url = url.split("/")[0];
  url = url.split("?")[0];
  url = url.trim().toLowerCase();
  if (url.startsWith("www.")) url = url.slice(4);
  url = url.replace(/\.+$/, "");

  if (!url.includes(".") || url.includes(" ") || url === "") return null;
  return url;
}

export interface ParsedUrlList {
  valid: string[];
  invalid: string[];
}

export function parseUrlList(rawText: string): ParsedUrlList {
  const entries = rawText.split(SPLIT_RE).filter(Boolean);
  const valid: string[] = [];
  const invalid: string[] = [];
  const seen = new Set<string>();

  for (const entry of entries) {
    const domain = normalizeDomain(entry);
    if (domain === null) {
      invalid.push(entry);
      continue;
    }
    if (!seen.has(domain)) {
      seen.add(domain);
      valid.push(domain);
    }
  }

  return { valid, invalid };
}
