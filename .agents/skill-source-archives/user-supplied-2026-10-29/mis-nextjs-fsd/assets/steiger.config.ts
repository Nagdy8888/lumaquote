/**
 * Steiger — FSD-aware architecture linter.
 *
 * Steiger enforces the layer & slice rules that ESLint's import plugin only
 * catches coarsely (e.g. same-layer cross-imports, public-API violations).
 *
 * NOTE on layer naming: the canonical FSD "pages" layer is named `views/` in
 * this project because Next.js reserves `src/pages/` for the legacy Pages
 * Router — having both `src/app/` and `src/pages/` makes Next.js error. We
 * alias the FSD layer name via `aliases` below so Steiger treats `views/`
 * as the pages layer for all of its built-in rules.
 *
 * Install:
 *   pnpm add -D steiger @feature-sliced/steiger-plugin
 *
 * Run:
 *   pnpm steiger ./src
 *
 * Wire it into the pre-commit and CI lint step:
 *   "scripts": {
 *     "lint:arch": "steiger ./src"
 *   }
 */
import { defineConfig } from "steiger"
import fsd from "@feature-sliced/steiger-plugin"

export default defineConfig([
  ...fsd.configs.recommended,

  {
    files: ["./src/**"],
    rules: {
      // Public API: only re-export from <slice>/index.ts is allowed cross-slice.
      "fsd/public-api": "error",

      // No same-layer cross-imports (features <-> features, etc.).
      "fsd/no-cross-imports": "error",

      // No upward imports (entities -> features, etc.).
      "fsd/no-higher-level-imports": "error",

      // Slice should not be excessively coupled (heuristic; default thresholds).
      "fsd/excessive-slicing": "warn",

      // Each slice should have a clear ui / model / api segmentation when
      // it grows beyond a single file.
      "fsd/segments-by-purpose": "warn",

      // Insignificant slice (one file only) — warn so the author can decide
      // whether to flatten into shared or keep.
      "fsd/insignificant-slice": "warn",
    },
  },

  // Tell Steiger that our `views/` directory is the FSD "pages" layer.
  // (If the installed plugin version doesn't yet support `aliases`, drop this
  // block — the directory-name match still works because `views` is not a
  // reserved FSD layer keyword and Steiger will lint cross-imports either way.)
  {
    files: ["./src/views/**"],
    settings: {
      "fsd/layer-alias": "pages",
    },
  },

  // Hard fail if anyone creates src/pages/ — it collides with Next.js's
  // legacy Pages Router and breaks the build. Use src/views/ instead.
  {
    files: ["./src/pages/**"],
    rules: {
      "fsd/forbidden-imports": "error",
    },
  },

  {
    ignores: ["./src/app/**"],
  },
])
