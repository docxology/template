const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const { pathToFileURL } = require("node:url");
const { expect, test } = require("@playwright/test");

async function settleMath(page) {
  await page.waitForFunction(() => typeof window.MathJax?.startup?.document?.rerenderPromise === "function");
  await page.evaluate(async () => {
    await window.MathJax.startup.promise;
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    await window.templateMathJaxReflowPromise;
    await document.fonts.ready;
  });
}

function prepareMathPage(file, html, local = false) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, html);
  const code = "from pathlib import Path; import sys; from infrastructure.rendering._web_assets import harden_mathjax_script, install_local_mathjax_assets, embed_favicon, write_favicon_file; from infrastructure.rendering.web_renderer import WebRenderer; target = Path(sys.argv[1]); harden_mathjax_script(target); harden_mathjax_script(target); embed_favicon(target); write_favicon_file(target.parent); WebRenderer._embed_css(target); install_local_mathjax_assets(target, repo_root=Path.cwd()) if sys.argv[2] == 'local' else None";
  const result = spawnSync("uv", ["run", "--locked", "python", "-c", code, file, local ? "local" : "cdn"], { encoding: "utf8" });
  expect(result.status, result.stdout + result.stderr).toBe(0);
}

async function serveMathPage(file) {
  const root = path.dirname(file);
  const types = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".json": "application/json", ".woff2": "font/woff2" };
  const server = http.createServer((request, response) => {
    const target = path.resolve(root, "." + new URL(request.url, "http://localhost").pathname);
    const relative = path.relative(root, target);
    if (relative.startsWith("..") || path.isAbsolute(relative) || !fs.existsSync(target) || !fs.statSync(target).isFile()) {
      response.writeHead(404).end();
      return;
    }
    response.writeHead(200, { "Content-Type": types[path.extname(target)] || "application/octet-stream" });
    fs.createReadStream(target).pipe(response);
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const origin = `http://127.0.0.1:${server.address().port}`;
  return {
    origin,
    url: `${origin}/${path.basename(file)}`,
    close: () => new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve())),
  };
}

test("wide math retains its complete content through local scrolling after viewport resizing", async ({ page }, testInfo) => {
  test.setTimeout(90000);
  const file = testInfo.outputPath("math-reflow.html");
  fs.mkdirSync(testInfo.outputDir, { recursive: true });
  const html = String.raw`<!doctype html><html lang="en"><head><meta charset="utf-8">
    <script>window.templateAuthoredMathFixtureRan = true;</script>
    <script data-template-mathjax-config="stale">window.templateStaleMathFixtureRan = true; window.MathJax = {startup: {typeset: false}};</script>
    <script nonce="authored-proof" type="text/javascript" defer src="https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js"></script>
    </head><body><h1>Equation reflow</h1><p><span class="math display">\[
    u_{n+1}=a_1x_1+a_2x_2+a_3x_3+a_4x_4+a_5x_5+a_6x_6+a_7x_7+a_8x_8
    \qquad{(17)}\]</span></p><p>Inline
    <span class="math inline">\(\texttt{LONG\_INLINE\_IDENTIFIER\_WITHOUT\_BREAK\_OPPORTUNITIES}\)</span>
    remains accessible.</p></body></html>`;
  prepareMathPage(file, html);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(pathToFileURL(file).href, { waitUntil: "domcontentloaded" });
  await settleMath(page);
  expect(await page.evaluate(() => ({
    authored: window.templateAuthoredMathFixtureRan,
    stale: typeof window.templateStaleMathFixtureRan,
    loaders: [...document.scripts]
      .filter((script) => script.src.includes("mathjax@4.0.0/tex-chtml.js"))
      .map((script) => ({ nonce: script.nonce, type: script.type, defer: script.defer })),
  }))).toEqual({
    authored: true,
    stale: "undefined",
    loaders: [{ nonce: "authored-proof", type: "text/javascript", defer: true }],
  });
  const source = await page.evaluate(() => MathJax.startup.document.getMathItemsWithin(document.body).map((item) => item.math));
  expect(source).toHaveLength(2);
  for (const width of [640, 320, 1440, 320]) {
    await page.setViewportSize({ width, height: 900 });
    await settleMath(page);
    const geometry = await page.evaluate(() => ({
      width: innerWidth,
      document: document.documentElement.scrollWidth,
      body: document.body.scrollWidth,
      rootOverflow: getComputedStyle(document.documentElement).overflowX,
      bodyOverflow: getComputedStyle(document.body).overflowX,
      error: window.templateMathJaxReflowError || null,
      source: MathJax.startup.document.getMathItemsWithin(document.body).map((item) => item.math),
      math: [...document.querySelectorAll("span.math")].map((element) => {
        const port = element.querySelector('mjx-container[display="true"]') || element;
        const math = element.querySelector("mjx-math");
        port.scrollLeft = 0;
        const width = port.clientWidth;
        const contentWidth = port.scrollWidth;
        port.scrollLeft = contentWidth;
        return {
          width, contentWidth, scrollLeft: port.scrollLeft,
          overflow: getComputedStyle(port).overflowX,
          left: port.getBoundingClientRect().left,
          right: port.getBoundingClientRect().right,
          mathRightAtEnd: math.getBoundingClientRect().right,
          text: math.textContent,
        };
      }),
    }));
    expect(geometry.error).toBeNull();
    expect(geometry.source).toEqual(source);
    expect(geometry.document).toBeLessThanOrEqual(width + 1);
    expect(geometry.body).toBeLessThanOrEqual(width + 1);
    expect(["hidden", "clip"]).not.toContain(geometry.rootOverflow);
    expect(["hidden", "clip"]).not.toContain(geometry.bodyOverflow);
    expect(geometry.math).toHaveLength(2);
    expect(geometry.math[0].text).toContain("(17)");
    for (const math of geometry.math) {
      expect(math.left).toBeGreaterThanOrEqual(-1);
      expect(math.right).toBeLessThanOrEqual(width + 1);
      if (math.contentWidth > math.width + 1) {
        expect(["auto", "scroll"]).toContain(math.overflow);
        expect(math.scrollLeft).toBeGreaterThan(0);
        expect(math.mathRightAtEnd).toBeLessThanOrEqual(math.right + 1);
      }
    }
  }
});

for (const mode of ["local", "cdn"]) {
  test(`large prose documents typeset all raw and Pandoc mathematics (${mode})`, async ({ page }, testInfo) => {
    test.setTimeout(120000);
    const file = testInfo.outputPath("large-book.html");
    const sources = Array.from({ length: 13 }, (_, index) => `x_{${index}}^2+1`);
    const equations = sources.map((source, index) => index % 2
      ? `<p data-equation>\\(${source}\\)</p>`
      : `<p data-equation><span class="math inline">\\(${source}\\)</span></p>`).join("");
    // Each ordinary span creates a scanner run, independently of equation size.
    const prose = "<span>Ordinary book prose. </span>".repeat(160000);
    prepareMathPage(file, `<!doctype html><html lang="en"><head><meta charset="utf-8">
      <script src="https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js"></script>
      </head><body><main><article>${equations}<div>${prose}</div></article></main></body></html>`, mode === "local");
    const server = await serveMathPage(file);
    const errors = [];
    const external = [];
    page.on("pageerror", (error) => errors.push(String(error)));
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("request", (request) => {
      if (/^https?:/.test(request.url()) && new URL(request.url()).origin !== server.origin) {
        external.push(request.url());
      }
    });
    try {
      await page.goto(server.url, { waitUntil: "domcontentloaded" });
      await settleMath(page);
      for (const width of [1280, 320, 1280]) {
        await page.setViewportSize({ width, height: 900 });
        await settleMath(page);
        const observed = await page.evaluate(() => ({
          sources: MathJax.startup.document.getMathItemsWithin(document.body).map((item) => item.math),
          equations: [...document.querySelectorAll("[data-equation] mjx-container")].map((element) => ({
            width: element.getBoundingClientRect().width,
            height: element.getBoundingClientRect().height,
          })),
          mathErrors: document.querySelectorAll("mjx-merror").length,
          invalidAria: [...document.querySelectorAll("mjx-speech[aria-roledescription]")].some(
            (element) => /[\u0080-\u009f]/.test(element.getAttribute("aria-roledescription"))
          ),
          reflowError: window.templateMathJaxReflowError || null,
        }));
        expect(observed.sources).toEqual(sources);
        expect(observed.equations).toHaveLength(sources.length);
        for (const equation of observed.equations) {
          expect(equation.width).toBeGreaterThan(0);
          expect(equation.height).toBeGreaterThan(0);
        }
        expect(observed.mathErrors).toBe(0);
        expect(observed.invalidAria).toBe(false);
        expect(observed.reflowError).toBeNull();
      }
      expect(errors).toEqual([]);
      if (mode === "local") expect(external).toEqual([]);
      else expect(external.some((url) => url.includes("/mathjax@4.0.0/tex-chtml.js"))).toBe(true);
    } finally {
      await server.close();
    }
  });
}

test("math discovery retains selected roots, text runs, and ignore/process boundaries", async ({ page }, testInfo) => {
  test.setTimeout(90000);
  const file = testInfo.outputPath("scoped-math.html");
  prepareMathPage(file, String.raw`<!doctype html><html lang="en"><head><meta charset="utf-8">
    <script>window.MathJax = {
      startup: {elements: ["#first", "#second"]},
      options: {ignoreHtmlClass: "omit", processHtmlClass: "include"}
    };</script>
    <script src="https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js"></script>
    </head><body>
    <div id="outside">\(q+1\)</div>
    <section id="first">
      <p>\(\frac{x}{2}<!-- a delimiter-spanning comment --><wbr>+1\)</p>
      <div class="omit"><p id="ignored">\(a+1\)</p><p class="include">\(b^2+1\)</p></div>
      <code id="skipped">\(z+1\)</code><code class="include">\(c+1\)</code>
    </section>
    <section id="second"><p>\(d+1\)</p><p>\begin{aligned}e&amp;=f+1\\g&amp;=h\end{aligned}</p></section>
    </body></html>`, true);
  const server = await serveMathPage(file);
  const errors = [];
  page.on("pageerror", (error) => errors.push(String(error)));
  try {
    await page.goto(server.url, { waitUntil: "domcontentloaded" });
    await settleMath(page);
    await expect(page.locator("#first mjx-container")).toHaveCount(3);
    await expect(page.locator("#second mjx-container")).toHaveCount(2);
    for (const id of ["outside", "ignored", "skipped"]) {
      await expect(page.locator(`#${id} mjx-container`)).toHaveCount(0);
      await expect(page.locator(`#${id}`)).toContainText(String.raw`\(`);
    }
    await expect(page.locator("#first mjx-mfrac")).toHaveCount(1);
    await expect(page.locator("#second mjx-mtable")).toHaveCount(1);
    await expect(page.locator("mjx-merror")).toHaveCount(0);
    await page.evaluate(async () => {
      await MathJax.typesetPromise([document.getElementById("outside")]);
    });
    await expect(page.locator("#outside mjx-container")).toHaveCount(1);
    expect(await page.evaluate(() => MathJax.startup.document
      .getMathItemsWithin(document.getElementById("outside")).map((item) => item.math))).toEqual(["q+1"]);
    expect(errors).toEqual([]);
  } finally {
    await server.close();
  }
});
