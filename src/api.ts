// Single entry point for reading book/chapter data from the public/api backend.
const API_ROOT = "/api/pt-br";
const API_BASE = `${API_ROOT}/blivre`;
const MANIFEST_URL = `${API_BASE}/manifest.json`;

type Manifest = Record<string, string>;

let manifestPromise: Promise<Manifest> | undefined;

// The manifest is only generated at build time (see scripts/generate-manifest.mjs),
// so production fetches use its content hash while dev falls back to a per-run timestamp.
const DEV_VERSION = String(Date.now());

function loadManifest(): Promise<Manifest> {
  if (!manifestPromise) {
    manifestPromise = fetch(MANIFEST_URL)
      .then((res) => (res.ok ? (res.json() as Promise<Manifest>) : {}))
      .catch(() => ({}));
  }
  return manifestPromise;
}

async function fetchJson<T>(
  base: string,
  path: string,
  versionKey: string,
): Promise<T> {
  const version = import.meta.env.DEV
    ? DEV_VERSION
    : (await loadManifest())[versionKey];
  const url = `${base}/${path}${version ? `?v=${version}` : ""}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export function getInit<T>(): Promise<T> {
  return fetchJson<T>(API_ROOT, "init.json", "init");
}

export function getChapter<T>(
  book: string,
  chapter: number | string,
): Promise<T> {
  return fetchJson<T>(
    API_BASE,
    `${book}/${chapter}.json`,
    `${book}-${chapter}`,
  );
}
