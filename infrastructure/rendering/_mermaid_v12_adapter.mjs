// Packaged SDK adapter for the admitted Mermaid CLI 12.0.0 public run API.
// Manuscripts supply diagram text only; no manuscript JavaScript is imported.
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

function literalFile(filename, limit) {
  if (typeof filename !== "string" || !path.isAbsolute(filename)) {
    throw new Error("Mermaid adapter requires explicit absolute file inputs");
  }
  const info = fs.lstatSync(filename);
  if (!info.isFile() || info.isSymbolicLink() || info.size > limit) {
    throw new Error("Mermaid adapter input is not a bounded regular file");
  }
  return fs.readFileSync(filename, "utf8");
}

if (process.argv.length !== 3) {
  throw new Error("Mermaid adapter accepts exactly one literal JSON request file");
}
const request = JSON.parse(literalFile(process.argv[2], 1024 * 1024));
const keys = ["input", "output", "output_format", "package_root", "puppeteer_config", "render_profile", "schema_version"];
if (request === null || Array.isArray(request) ||
    JSON.stringify(Object.keys(request).sort()) !== JSON.stringify(keys) ||
    request.schema_version !== "template-mermaid-v12-legacy11-default-theme-viewport-request-v2" ||
    !["svg", "png"].includes(request.output_format)) {
  throw new Error("Mermaid adapter request differs from its finite admitted schema");
}
// CLI11 explicitly selected theme "default"; CLI12's omitted theme changed
// the selected diagram appearance/font. This fixed profile preserves that
// authoring baseline while keeping CLI12 font embedding and viewport bounds.
const expectedProfile = {
  theme: "default", font_embed: true, background_color: "white",
  viewport_width: 1400, viewport_height: 900, device_scale_factor: 1,
};
const profile = request.render_profile;
if (profile === null || Array.isArray(profile) || typeof profile !== "object" ||
    JSON.stringify(Object.keys(profile).sort()) !== JSON.stringify(Object.keys(expectedProfile).sort()) ||
    Object.entries(expectedProfile).some(([key, value]) =>
      typeof profile[key] !== typeof value || profile[key] !== value)) {
  throw new Error("Mermaid adapter rendering profile changes the source-owned default theme");
}
for (const name of ["package_root", "input", "output"]) {
  if (typeof request[name] !== "string" || !path.isAbsolute(request[name]) ||
      request[name].length > 4096) {
    throw new Error("Mermaid adapter paths require explicit bounded literals");
  }
}
if (!request.input.endsWith(".mmd") || !request.output.endsWith("." + request.output_format)) {
  throw new Error("Mermaid adapter requires original diagram data and its declared native output format");
}
literalFile(request.input, 1024 * 1024);
const packageInfo = JSON.parse(literalFile(path.join(request.package_root, "package.json"), 1024 * 1024));
if (packageInfo.name !== "@mermaid-js/mermaid-cli" || packageInfo.version !== "12.0.0" ||
    packageInfo.exports?.["."]?.default !== "./src/index.js") {
  throw new Error("Mermaid adapter has no admitted API profile for this selected package");
}
const config = request.puppeteer_config === null ? {} :
  JSON.parse(literalFile(request.puppeteer_config, 1024 * 1024));
if (config === null || Array.isArray(config) || typeof config !== "object") {
  throw new Error("Mermaid adapter Puppeteer configuration must be literal JSON data");
}
const apiPath = path.join(request.package_root, "src/index.js");
literalFile(apiPath, 1024 * 1024);
const { run } = await import(pathToFileURL(apiPath).href);
if (typeof run !== "function") {
  throw new Error("Selected Mermaid package does not export its admitted run API");
}
await run(request.input, request.output, {
  puppeteerConfig: { headless: "shell", ...config },
  quiet: true,
  outputFormat: request.output_format,
  parseMMDOptions: {
    mermaidConfig: { theme: "default" },
    backgroundColor: "white",
    fontEmbed: true,
    viewport: { width: 1400, height: 900, deviceScaleFactor: 1 },
  },
});
