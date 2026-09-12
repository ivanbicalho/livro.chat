#!/usr/bin/env node
// Generates public/api/pt-br/blivre/manifest.json mapping "book-chapter" -> content hash,
// so api.ts can append a cache-busting ?v= query param when fetching chapter JSON files.
import { createHash } from "node:crypto";
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const PT_BR_ROOT = join(__dirname, "..", "..", "public", "api", "pt-br");
const API_ROOT = join(PT_BR_ROOT, "blivre");
const MANIFEST_PATH = join(API_ROOT, "manifest.json");

function hashFile(path) {
    const content = readFileSync(path);
    return createHash("sha1").update(content).digest("hex").slice(0, 10);
}

function buildManifest() {
    const manifest = {};
    manifest.init = hashFile(join(PT_BR_ROOT, "init.json"));
    for (const entry of readdirSync(API_ROOT, { withFileTypes: true })) {
        if (!entry.isDirectory()) continue;
        const bookDir = join(API_ROOT, entry.name);
        const chapterFiles = readdirSync(bookDir).filter((file) => file.endsWith(".json"));
        for (const file of chapterFiles) {
            const chapter = file.slice(0, -".json".length);
            manifest[`${entry.name}-${chapter}`] = hashFile(join(bookDir, file));
        }
    }
    return manifest;
}

const manifest = buildManifest();
writeFileSync(MANIFEST_PATH, JSON.stringify(manifest));
console.log(`Generated manifest with ${Object.keys(manifest).length} entries -> ${MANIFEST_PATH}`);
