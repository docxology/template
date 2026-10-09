// Source-owned before-layout FontFace constructor. No installed-font discovery.
export async function loadSourceDefaultFonts(profile) {
  if (profile.schema_version !== "template-source-mermaid-licensed-default-font-v1" ||
      profile.family !== "Template Liberation Sans" || !Array.isArray(profile.faces) ||
      profile.faces.length !== 4) throw Error("Source Mermaid font profile differs");
  const observed = [];
  let total = 0;
  for (const face of profile.faces) {
    if (!Number.isInteger(face.bytes) || face.bytes <= 0 || typeof face.data !== "string" ||
        face.data.length > 699052 || (total += face.bytes) > 134217728 || face.bytes > 524288 ||
        face.family !== profile.family || !["400", "700"].includes(face.weight) ||
        !["normal", "italic"].includes(face.style)) throw Error("Source font finite profile differs");
    const buffer = Uint8Array.from(atob(face.data), c => c.charCodeAt(0));
    const hash = async () => Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", buffer)))
      .map(n => n.toString(16).padStart(2, "0")).join("");
    if (buffer.byteLength !== face.bytes || await hash() !== face.sha256)
      throw Error("Source font constructor body differs before consumption");
    const font = new FontFace(profile.family, buffer.buffer, {weight: face.weight, style: face.style});
    document.fonts.add(font);
    await font.load();
    if (font.status !== "loaded" || await hash() !== face.sha256)
      throw Error("Source font constructor body differs after actual FontFace consumption");
    observed.push(Object.fromEntries(["postscript_name", "family", "weight", "style", "sha256", "bytes"]
      .map(key => [key, face[key]])));
  }
  await document.fonts.ready;
  return {schema_version: profile.schema_version, family: profile.family,
    faces: observed, status: "loaded-before-layout"};
}
// END_SOURCE_BROWSER_CONSTRUCTOR

export function sourceDefaultBrowser(browser, profile, observations) {
  return new Proxy(browser, {
    get(target, key) {
      if (key !== "newPage") {
        const value = Reflect.get(target, key);
        return typeof value === "function" ? value.bind(target) : value;
      }
      return async () => {
        const page = await target.newPage();
        let observation;
        // evaluateOnNewDocument runs before the CLI's page script. Its async
        // loader is explicitly awaited by the real goto wrapper; installing a
        // callback alone would leave a FontFace/layout race.
        await page.evaluateOnNewDocument((source, value) => {
          const loader = (0, eval)("(" + source + ")");
          Object.defineProperty(globalThis, "__templateSourceDefaultFontPromise",
            {value: loader(value), writable: false, configurable: false});
        }, loadSourceDefaultFonts.toString(), profile);
        return new Proxy(page, {
          get(owner, property) {
            if (property === "goto") return async (...args) => {
              const result = await owner.goto(...args);
              const buffers = await owner.evaluate(() => globalThis.__templateSourceDefaultFontPromise);
              if (!buffers || buffers.status !== "loaded-before-layout") throw Error("Source font layout race");
              observation = {buffers, platform_fonts: [], used_default_faces: []};
              observations.push(observation);
              return result;
            };
            if (property === "close") return async (...args) => {
              try {
                if (observation) {
                  const client = await owner.createCDPSession();
                  try {
                    await client.send("DOM.enable"); await client.send("CSS.enable");
                    const document = await client.send("DOM.getDocument", {depth: -1});
                    const owners = [];
                    let count = 0;
                    function visit(node, inside) {
                      if (++count > 20000) throw Error("Source font owner DOM budget");
                      inside ||= node.nodeName.toLowerCase() === "svg";
                      if (inside && node.nodeType === 1 && !["style", "title", "desc"].includes(node.nodeName.toLowerCase()) &&
                          (node.children ?? []).some(child => child.nodeType === 3 && child.nodeValue.trim())) owners.push(node);
                      for (const child of node.children ?? []) visit(child, inside);
                    }
                    visit(document.root, false);
                    if (owners.length > 1000) throw Error("Source font actual owner allowance");
                    for (const node of owners) {
                      const {fonts} = await client.send("CSS.getPlatformFontsForNode", {nodeId: node.nodeId});
                      observation.platform_fonts.push(...fonts.filter(row => row.glyphCount > 0));
                      if (observation.platform_fonts.length > 1000) throw Error("Source actual font usage allowance");
                    }
                    observation.used_default_faces = [...new Set(observation.platform_fonts
                      .filter(face => face.isCustomFont && profile.faces.some(original => original.postscript_name === face.postScriptName))
                      .map(face => face.postScriptName))].sort();
                  } finally { await client.detach(); }
                }
              } finally { await owner.close(...args); }
            };
            const value = Reflect.get(owner, property);
            return typeof value === "function" ? value.bind(owner) : value;
          },
        });
      };
    },
  });
}

export function sourceDefaultMermaidConfig() {
  return {theme: "default", fontFamily: "Template Liberation Sans",
    themeVariables: {fontFamily: "Template Liberation Sans"}};
}

export function embedUsedSourceDefaultFaces(svg, profile, observation) {
  const names = observation.used_default_faces;
  if (!Array.isArray(names) || names.length > 4) throw Error("Source used-face census differs");
  if (!names.length) return svg;
  const faces = names.map(name => {
    const face = profile.faces.find(row => row.postscript_name === name);
    if (!face) throw Error("Source used face escaped its original fixed body owner");
    return face;
  });
  const css = "/*" + profile.license.replaceAll("*/", "* /") + "*/\n" + faces.map(face =>
    "@font-face{font-family:'Template Liberation Sans';font-style:" + face.style +
    ";font-weight:" + face.weight + ";src:url(data:font/ttf;base64," + face.data + ")}\n").join("");
  const escape = text => text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;");
  const text = Buffer.from(svg).toString("utf8");
  const opening = text.indexOf(">") + 1;
  if (!text.startsWith("<svg") || !opening) throw Error("Source font embedding requires its actual native SVG root");
  return Buffer.from(text.slice(0, opening) + '<style id="template-source-mermaid-licensed-fonts">' +
    escape(css) + "</style>" + text.slice(opening));
}
