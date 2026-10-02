// Les poids OCR et le moteur proviennent de dépendances npm. Ils ne sont pas
// versionnés dans Git : npm install les recrée et Vite les sert localement.
import { mkdir, copyFile, readdir } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const root = resolve(dirname(new URL(import.meta.url).pathname), '..');
const destination = resolve(root, 'public/ocr');
await mkdir(destination, { recursive: true });
const tessRoot = dirname(require.resolve('tesseract.js/package.json'));
const coreRoot = dirname(require.resolve('tesseract.js-core/package.json'));
const languageRoot = dirname(require.resolve('@tesseract.js-data/fra/package.json'));
async function locateLanguage(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  for (const e of entries) if (e.name === 'fra.traineddata.gz') return resolve(directory, e.name);
  for (const e of entries) {
    if (e.isDirectory()) {
      const result = await locateLanguage(resolve(directory, e.name));
      if (result) return result;
    }
  }
  return null;
}
const preferred = resolve(languageRoot, '4.0.0_best_int/fra.traineddata.gz');
let lang;
try { await copyFile(preferred, resolve(destination, 'fra.traineddata.gz')); lang = preferred; }
catch { lang = await locateLanguage(languageRoot); if (!lang) throw new Error('Modèle OCR français introuvable.'); await copyFile(lang, resolve(destination, 'fra.traineddata.gz')); }
await copyFile(resolve(tessRoot, 'dist/worker.min.js'), resolve(destination, 'worker.min.js'));
await copyFile(resolve(coreRoot, 'tesseract-core-lstm.wasm.js'), resolve(destination, 'tesseract-core-lstm.wasm.js'));
await copyFile(resolve(coreRoot, 'tesseract-core-lstm.wasm'), resolve(destination, 'tesseract-core-lstm.wasm'));
console.log('OCR prêt : worker, moteur WASM et langue française servis localement.');
