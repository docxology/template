const fs = require("node:fs");
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

test("wide math retains its complete content through local scrolling after viewport resizing", async ({ page }, testInfo) => {
  test.setTimeout(90000);
  const file = testInfo.outputPath("math-reflow.html");
  fs.mkdirSync(testInfo.outputDir, { recursive: true });
  const html = String.raw`<!doctype html><html lang="en"><head><meta charset="utf-8">
    <script src="https://cdn.jsdelivr.net/npm/mathjax@4.0.0/tex-chtml.js"></script>
    </head><body><h1>Equation reflow</h1><p><span class="math display">\[
    u_{n+1}=a_1x_1+a_2x_2+a_3x_3+a_4x_4+a_5x_5+a_6x_6+a_7x_7+a_8x_8
    \qquad{(17)}\]</span></p><p>Inline
    <span class="math inline">\(\texttt{LONG\_INLINE\_IDENTIFIER\_WITHOUT\_BREAK\_OPPORTUNITIES}\)</span>
    remains accessible.</p></body></html>`;
  fs.writeFileSync(file, html);
  const code = "from pathlib import Path; import sys; from infrastructure.rendering._web_assets import harden_mathjax_script; from infrastructure.rendering.web_renderer import WebRenderer; p=Path(sys.argv[1]); harden_mathjax_script(p); WebRenderer._embed_css(p)";
  const result = spawnSync("uv", ["run", "--locked", "python", "-c", code, file], { encoding: "utf8" });
  expect(result.status, result.stdout + result.stderr).toBe(0);
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto(pathToFileURL(file).href, { waitUntil: "domcontentloaded" });
  await settleMath(page);
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
