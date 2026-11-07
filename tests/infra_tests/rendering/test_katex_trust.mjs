import assert from "node:assert/strict";
import test from "node:test";
import katex from "katex";

const expression = String.raw`\href{https://example.invalid/katex-own-property-control}{x}`;
const hasAnchor = options => /<a\s[^>]*href=/.test(katex.renderToString(expression, options));

test("untrusted math keeps the documented trust=false default", () => {
  assert.equal(hasAnchor({}), false);
});
test("inherited options cannot enable trusted math", () => {
  assert.equal(hasAnchor(Object.create({trust: true})), false);
});
test("preexisting Object.prototype pollution cannot enable trusted math", () => {
  assert.equal(Object.hasOwn(Object.prototype, "trust"), false);
  try {
    Object.prototype.trust = true;
    assert.equal(hasAnchor({}), false);
  } finally {
    delete Object.prototype.trust;
  }
});
test("an explicit own trust option retains legitimate link rendering", () => {
  assert.equal(hasAnchor({trust: true}), true);
});
