// Packaged SDK adapter for the admitted Mermaid CLI 11.16.0 public run API.
// Manuscripts supply diagram text only; no manuscript JavaScript is imported.
import fs from "node:fs";
import { createRequire } from "node:module";
import { sourceDefaultBrowser, sourceDefaultMermaidConfig, embedUsedSourceDefaultFaces } from "./_mermaid_source_font_default.mjs";
import path from "node:path";
import { createHash } from "node:crypto";
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
const keys = ["font_profile", "font_profile_sha256", "input", "output", "output_format", "package_root", "puppeteer_config", "render_profile", "schema_version"];
if (request === null || Array.isArray(request) ||
    JSON.stringify(Object.keys(request).sort()) !== JSON.stringify(keys) ||
    request.schema_version !== "template-mermaid-v11-source-pinned-default-theme-viewport-licensed-font-request-v2" ||
    !["svg", "png"].includes(request.output_format)) {
  throw new Error("Mermaid adapter request differs from its finite admitted schema");
}
// Source-pinned CLI11 has no fontEmbed API. Its declared default theme,
// platform fonts and exact source paint are admitted independently; this
// profile never borrows CLI12 font embedding or native proof.
if (!/^24\.[0-9]+\.[0-9]+$/.test(process.versions.node)) {
  throw new Error("Source-pinned Mermaid11 requires its genuinely selected Node24 profile");
}
const expectedProfile = {
  theme: "default", font_embed: false, background_color: "white",
  source_default_font: "template-source-mermaid-licensed-default-font-v1", source_used_face_embedding: true,
  viewport_width: 1400, viewport_height: 900, device_scale_factor: 1,
};
const profile = request.render_profile;
if (profile === null || Array.isArray(profile) || typeof profile !== "object" ||
    JSON.stringify(Object.keys(profile).sort()) !== JSON.stringify(Object.keys(expectedProfile).sort()) ||
    Object.entries(expectedProfile).some(([key, value]) =>
      typeof profile[key] !== typeof value || profile[key] !== value)) {
  throw new Error("Mermaid adapter rendering profile changes the source-owned legacy default theme");
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
if (packageInfo.name !== "@mermaid-js/mermaid-cli" || packageInfo.version !== "11.16.0" ||
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
// Genuine live diagnostic API observations are retained in the supervised raw
// stdout. They report loaded names, not a body-hash/kernel/cache admission.
// Keep environment variables, host credentials and network metadata private.
if (typeof process.report?.getReport !== "function" ||
    typeof process.report.excludeNetwork !== "boolean") {
  throw new Error("Source11 Node profile lacks its actual bounded live diagnostic API");
}
process.report.excludeNetwork = true;
function libraryIdentity(info) {
  return Object.fromEntries(["dev", "ino", "nlink", "mode", "size", "mtimeNs", "ctimeNs"].map(
    name => [name, String(info[name])],
  ));
}
function observeLiveLibraryBody(filename) {
  let descriptor;
  try {
    descriptor = fs.openSync(filename, "r");
    const before = fs.fstatSync(descriptor, { bigint: true });
    if (!before.isFile() || before.size > 536870912n) {
      throw new Error("loaded-library-file-kind-or-byte-bound");
    }
    const hash = createHash("sha256");
    const buffer = Buffer.alloc(1048576);
    let consumed = 0;
    for (;;) {
      const count = fs.readSync(descriptor, buffer, 0, buffer.length, null);
      if (count === 0) break;
      consumed += count;
      if (BigInt(consumed) > before.size) throw new Error("loaded-library-grew");
      hash.update(buffer.subarray(0, count));
    }
    const after = fs.fstatSync(descriptor, { bigint: true });
    const resolvedAfter = fs.statSync(filename, { bigint: true });
    const beforeIdentity = libraryIdentity(before);
    const afterIdentity = libraryIdentity(after);
    if (BigInt(consumed) !== before.size ||
        JSON.stringify(beforeIdentity) !== JSON.stringify(afterIdentity) ||
        JSON.stringify(afterIdentity) !== JSON.stringify(libraryIdentity(resolvedAfter))) {
      throw new Error("actual-loaded-library-body-or-physical-identity-changed");
    }
    return { path: filename, status: "observed-regular-body", bytes: consumed,
      sha256: hash.digest("hex"), identity_before: beforeIdentity, identity_after: afterIdentity };
  } catch (error) {
    return { path: filename, status: "unsupported-loaded-provider", reason:
      typeof error.code === "string" ? error.code : "actual-loaded-library-file-or-byte-custody-refused" };
  } finally {
    if (descriptor !== undefined) fs.closeSync(descriptor);
  }
}
function retainLiveLoadedReport(phase) {
  const report = process.report.getReport();
  if (report?.header?.processId !== process.pid ||
      report.header.nodejsVersion !== process.version ||
      !Array.isArray(report.sharedObjects) || report.sharedObjects.length > 4096 ||
      report.sharedObjects.some(name => typeof name !== "string" ||
        !path.isAbsolute(name) || name.length > 4096 || name.includes("\0"))) {
    throw new Error("Actual Node diagnostic API lacks its finite original loaded-library observation");
  }
  const loadedLibraryBodies = report.sharedObjects.map(observeLiveLibraryBody);
  const observedBytes = loadedLibraryBodies.reduce((total, row) => total + (row.bytes ?? 0), 0);
  if (observedBytes > 1073741824) {
    throw new Error("Source11 actual live loaded-library body closure exceeds its existing finite byte bound");
  }
  const encoded = JSON.stringify({
    schema_version: "template-native-source11-node-live-loaded-report-v1",
    api: "process.report.getReport", phase, pid: process.pid, owner_pid: process.ppid,
    node_version: process.version, platform: process.platform, architecture: process.arch,
    shared_objects: report.sharedObjects, loaded_library_bodies: loadedLibraryBodies,
    remaining_admission: ["source-required loaded library bodies and shared-cache/kernel closure"],
  }) + "\n";
  if (Buffer.byteLength(encoded, "utf8") > 2 * 1024 * 1024) {
    throw new Error("Source11 actual live loaded-library record exceeds original raw-stream capacity");
  }
  process.stdout.write(encoded);
}
retainLiveLoadedReport("before-import");
const fontBody = Buffer.from(literalFile(request.font_profile, 67108864));
if (createHash("sha256").update(fontBody).digest("hex") !== request.font_profile_sha256)
  throw Error("Source font profile input differs");
const fontProfile = JSON.parse(fontBody);
const require = createRequire(apiPath);
const [{renderMermaid}, {default: puppeteer}] = await Promise.all([
  import(pathToFileURL(apiPath).href), import(pathToFileURL(require.resolve("puppeteer")).href),
]);
const observations = [];
const browser = await puppeteer.launch({headless: "shell", ...config});
try {
  const rendered = await renderMermaid(sourceDefaultBrowser(browser, fontProfile, observations),
    literalFile(request.input, 1048576), request.output_format, {
      mermaidConfig: sourceDefaultMermaidConfig(), backgroundColor: "white",
      viewport: {width: 1400, height: 900, deviceScaleFactor: 1},
    });
  if (observations.length !== 1) throw Error("Source before-layout font invocation differs");
  const output = request.output_format === "svg" ?
    embedUsedSourceDefaultFaces(rendered.data, fontProfile, observations[0]) : Buffer.from(rendered.data);
  fs.writeFileSync(request.output, output);
  fs.writeFileSync(request.output + ".source-fonts.json", JSON.stringify(observations[0]) + "\n");
} finally { await browser.close(); }

retainLiveLoadedReport("after-run");
