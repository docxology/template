// Source-pinned CLI11 public rendering API, one genuine browser/fresh pages.
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

function literalFile(filename, limit) {
  if (typeof filename !== "string" || !path.isAbsolute(filename)) {
    throw new Error("ordered Source adapter requires explicit absolute literal files");
  }
  const info = fs.lstatSync(filename);
  if (!info.isFile() || info.isSymbolicLink() || info.size > limit) {
    throw new Error("ordered Source adapter input is not a bounded regular file");
  }
  return fs.readFileSync(filename);
}
function sha(data) { return createHash("sha256").update(data).digest("hex"); }
function keys(value, expected) {
  return value !== null && !Array.isArray(value) && typeof value === "object" &&
    JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...expected].sort());
}
if (process.argv.length !== 3 || !/^20\.[0-9]+\.[0-9]+$/.test(process.versions.node)) {
  throw new Error("ordered Source11 adapter requires actual Node20 and one literal request");
}
const request = JSON.parse(literalFile(process.argv[2], 1024 * 1024));
if (!keys(request, ["schema_version", "package_root", "dependency_root", "puppeteer_config", "render_profile", "occurrences", "result_output"]) ||
    request.schema_version !== "template-mermaid-source11-ordered-batch-request-v1" ||
    !Array.isArray(request.occurrences) || !(request.occurrences.length > 0 && request.occurrences.length <= 100)) {
  throw new Error("ordered Source11 request differs from its exact finite declared schema");
}
const expectedProfile = {
  theme: "default", font_embed: false, background_color: "white",
  viewport_width: 1400, viewport_height: 900, device_scale_factor: 1,
};
if (!keys(request.render_profile, Object.keys(expectedProfile)) ||
    Object.entries(expectedProfile).some(([key, value]) => request.render_profile[key] !== value)) {
  throw new Error("ordered Source11 adapter cannot alter its actual default-theme profile");
}
for (const name of ["package_root", "dependency_root", "puppeteer_config", "result_output"]) {
  if (typeof request[name] !== "string" || !path.isAbsolute(request[name]) || request[name].length > 4096) {
    throw new Error("ordered Source11 adapter requires explicit bounded nominated roots");
  }
}
const dependency = fs.realpathSync(request.dependency_root);
const packageRoot = fs.realpathSync(request.package_root);
if (packageRoot !== path.join(dependency, "@mermaid-js", "mermaid-cli")) {
  throw new Error("ordered Source package is not its independently nominated complete npm member");
}
const packageInfo = JSON.parse(literalFile(path.join(packageRoot, "package.json"), 1024 * 1024));
if (packageInfo.name !== "@mermaid-js/mermaid-cli" || packageInfo.version !== "11.16.0" ||
    packageInfo.exports?.["."]?.default !== "./src/index.js") {
  throw new Error("ordered Source package is not actual locked CLI11.16.0");
}
const config = JSON.parse(literalFile(request.puppeteer_config, 1024 * 1024));
if (!keys(config, ["executablePath", "userDataDir", "args"]) ||
    !path.isAbsolute(config.executablePath) || !path.isAbsolute(config.userDataDir) ||
    !Array.isArray(config.args) || config.args.some(value => typeof value !== "string")) {
  throw new Error("ordered Source browser profile requires its exact original literal configuration");
}
const cwd = fs.realpathSync(process.cwd());
const inputNames = new Set();
const outputNames = new Set();
function outputName(filename) {
  if (typeof filename !== "string" || !path.isAbsolute(filename) || filename.length > 4096 ||
      fs.realpathSync(path.dirname(filename)) !== cwd || fs.existsSync(filename) || outputNames.has(filename)) {
    throw new Error("ordered Source output must be fresh and confined to its actual private process directory");
  }
  outputNames.add(filename);
}
outputName(request.result_output);
for (const [ordinal, row] of request.occurrences.entries()) {
  if (!keys(row, ["ordinal", "identity", "input", "input_sha256", "svg_output", "png_output"]) ||
      row.ordinal !== ordinal || typeof row.identity !== "string" || !row.identity || row.identity.length > 1024 ||
      inputNames.has(row.identity) || !/^[0-9a-f]{64}$/.test(row.input_sha256) || !row.input.endsWith(".mmd")) {
    throw new Error("ordered Source identity/body occurrence census changed or was deduplicated");
  }
  inputNames.add(row.identity);
  if (sha(literalFile(row.input, 1024 * 1024)) !== row.input_sha256) {
    throw new Error("ordered Source original normalized body bytes changed before actual native render");
  }
  outputName(row.svg_output); outputName(row.png_output);
  if (!row.svg_output.endsWith(".svg") || !row.png_output.endsWith(".png")) {
    throw new Error("ordered Source original output format differs");
  }
}
const apiPath = path.join(packageRoot, "src/index.js");
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
const require = createRequire(apiPath);
const puppeteerPath = fs.realpathSync(require.resolve("puppeteer"));
if (!puppeteerPath.startsWith(dependency + path.sep)) {
  throw new Error("actual Source puppeteer provider escapes its complete independently held npm root");
}
const [{ renderMermaid }, { default: puppeteer }] = await Promise.all([
  import(pathToFileURL(apiPath).href), import(pathToFileURL(puppeteerPath).href),
]);
if (typeof renderMermaid !== "function" || typeof puppeteer?.launch !== "function") {
  throw new Error("actual Source11 package has no admitted renderMermaid/browser API");
}
let browser;
const rows = [];
try {
  browser = await puppeteer.launch({ headless: "shell", ...config });
  for (const row of request.occurrences) {
    const data = literalFile(row.input, 1024 * 1024);
    if (sha(data) !== row.input_sha256) throw new Error("Source body changed during ordered original rendering");
    const definition = data.toString("utf8");
    const observed = { ordinal: row.ordinal, identity: row.identity, input_sha256: row.input_sha256 };
    for (const kind of ["svg", "png"]) {
      // Actual public API creates/closes a new page for every format. Nothing
      // collapses duplicate bodies or reuses one native output for two owners.
      const rendered = await renderMermaid(browser, definition, kind, {
        viewport: { width: 1400, height: 900, deviceScaleFactor: 1 },
        backgroundColor: "white", mermaidConfig: { theme: "default" },
      });
      const body = Buffer.from(rendered.data);
      if (!body.length || body.length > 67108864) throw new Error("native original artifact exceeds existing finite bytes");
      const output = row[kind + "_output"];
      fs.writeFileSync(output, body, { flag: "wx", mode: 0o600 });
      observed[kind] = { output, sha256: sha(body), bytes: body.length };
    }
    if (sha(literalFile(row.input, 1024 * 1024)) !== row.input_sha256) {
      throw new Error("Source original body changed after actual ordered native artifacts");
    }
    rows.push(observed);
  }
} finally {
  if (browser) await browser.close();
}
fs.writeFileSync(request.result_output, JSON.stringify({
  schema_version: "template-mermaid-source11-actual-ordered-batch-artifacts-v1",
  pid: process.pid, owner_pid: process.ppid, occurrences: rows,
}) + "\n", { flag: "wx", mode: 0o600 });
retainLiveLoadedReport("after-run");
