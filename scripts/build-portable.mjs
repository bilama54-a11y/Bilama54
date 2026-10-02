import { build, mergeConfig } from 'vite';
import config from '../vite.config.js';
import { readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const root = resolve(new URL('..', import.meta.url).pathname);
const outDir = resolve(root, '.cache/portable-build');
await build(mergeConfig(config, {
  configFile: false,
  build: { outDir, emptyOutDir: true, assetsInlineLimit: 1000000, rollupOptions: { output: { inlineDynamicImports: true } } },
}));
let html = await readFile(resolve(outDir, 'index.html'), 'utf8');
const scriptPath = html.match(/<script[^>]+src="([^"]+)"[^>]*><\/script>/)?.[1];
const cssPath = html.match(/<link[^>]+href="([^"]+\.css)"[^>]*>/)?.[1];
if (!scriptPath || !cssPath) throw new Error('Entrée compilée introuvable.');
let javascript = await readFile(resolve(outDir, '.' + scriptPath), 'utf8');
let css = await readFile(resolve(outDir, '.' + cssPath), 'utf8');

const files = {
  '/icons/matchlab.svg': ['image/svg+xml', 'public/icons/matchlab.svg'],
  '/icons/matchlab-192.png': ['image/png', 'public/icons/matchlab-192.png'],
  '/icons/matchlab-512.png': ['image/png', 'public/icons/matchlab-512.png'],
  '/teams/arsenal.svg': ['image/svg+xml', 'public/teams/arsenal.svg'],
  '/teams/leeds.svg': ['image/svg+xml', 'public/teams/leeds.svg'],
  '/fonts/manrope.woff2': ['font/woff2', 'public/fonts/manrope.woff2'],
  '/fonts/dm-sans.woff2': ['font/woff2', 'public/fonts/dm-sans.woff2'],
};
const assets = {};
for (const [url, [mime, path]] of Object.entries(files)) {
  const dataUrl = `data:${mime};base64,${(await readFile(resolve(root, path))).toString('base64')}`;
  assets[url] = dataUrl;
  javascript = javascript.replaceAll(url, dataUrl);
  css = css.replaceAll(url, dataUrl);
  html = html.replaceAll(url, dataUrl);
}
const worker = (await readFile(resolve(root, 'public/ocr/worker.min.js'))).toString('base64');
const core = (await readFile(resolve(root, 'public/ocr/tesseract-core-lstm.wasm.js'))).toString('base64');
const fra = (await readFile(resolve(root, 'public/ocr/fra.traineddata.gz'))).toString('base64');
// Les modèles sont embarqués ; ce fetch virtuel n’émet aucune requête réseau.
const prefix = `const __language = ${JSON.stringify(fra)}; const __fetch = self.fetch.bind(self); self.fetch = async (input, init) => { const url = typeof input === 'string' ? input : input.url; if (/\\/fra\\.traineddata(?:\\.gz)?(?:\\?.*)?$/.test(url)) { const raw=atob(__language); const bytes=Uint8Array.from(raw, c=>c.charCodeAt(0)); return new Response(bytes, {status:200,headers:{'Content-Type':'application/octet-stream'}}); } return __fetch(input,init); };\n`;
// Le cœur est déclaré dans le même worker : pas d’importScripts entre des
// origines opaques file://, ce qui rend l’OCR réellement autonome.
const bootstrap = `(() => { const decode = value => Uint8Array.from(atob(value), c=>c.charCodeAt(0)); const text = value => new TextDecoder().decode(decode(value)); const worker = URL.createObjectURL(new Blob([${JSON.stringify(prefix)}, text(${JSON.stringify(core)}), '\\n', text(${JSON.stringify(worker)})], {type:'application/javascript'})); globalThis.MATCHLAB_PORTABLE = {workerPath:worker,corePath:'embedded-tesseract-core.js',assets:${JSON.stringify(assets)}}; })();`;
html = html.replace(/<link[^>]+rel="manifest"[^>]*>/, '');
html = html.replace(/<link[^>]+href="[^"]+\.css"[^>]*>/, () => `<style>${css}</style>`);
html = html.replace(/<script[^>]+src="[^"]+"[^>]*><\/script>/, () => `<script>${bootstrap.replaceAll('</script', '<\\/script')}</script><script type="module">${javascript.replaceAll('</script', '<\\/script')}</script>`);
html = html.replace('<title>MatchLab — La donnée, pas le hasard.</title>', '<title>MatchLab — Application autonome</title>');
const licenses = [
  ['Manrope', 'public/fonts/LICENSE-Manrope.txt'],
  ['DM Sans', 'public/fonts/LICENSE-DM-Sans.txt'],
  ['Tesseract.js', 'node_modules/tesseract.js/LICENSE.md'],
  ['Tesseract.js core', 'node_modules/tesseract.js-core/LICENSE'],
  ['Modèle français', 'node_modules/@tesseract.js-data/fra/LICENSE'],
  ['Lucide', 'node_modules/lucide-react/LICENSE'],
  ['React', 'node_modules/react/LICENSE'],
  ['React DOM', 'node_modules/react-dom/LICENSE'],
];
const notices = [];
for (const [label, path] of licenses) {
  try { notices.push(`${label}\n${await readFile(resolve(root, path), 'utf8')}`); } catch { /* Certains paquets utilisent un autre nom de fichier. */ }
}
html = html.replace('<head>', () => `<head>\n<!-- Licences des ressources intégrées\n${notices.join('\n\n').replaceAll('-->', '-- >')}\n-->`);
await writeFile(resolve(root, 'MatchLab.html'), html);
console.log(`MatchLab.html créé : ${(Buffer.byteLength(html)/1024/1024).toFixed(2)} Mo, interface + OCR + modèles intégrés, sans serveur.`);
