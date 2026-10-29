/**
 * MIS app — Tailwind v4 configuration aligned to design tokens.
 *
 * Tailwind classes resolve to the CSS variables defined in `tokens.css`,
 * so a single token swap (or theme toggle) propagates everywhere.
 *
 * Drop alongside `tokens.css`; import `tokens.css` at the top of your
 * global stylesheet, then `@import "tailwindcss";` after it.
 */
import type { Config } from "tailwindcss"

const config: Config = {
  content: ["./src/**/*.{ts,tsx,mdx}"],
  theme: {
    extend: {
      // ── Colour — semantic, not literal ────────────────────────────────
      colors: {
        bg:          "var(--color-bg)",
        "surface-1": "var(--color-surface-1)",
        "surface-2": "var(--color-surface-2)",
        fg: {
          DEFAULT: "var(--color-fg)",
          muted:   "var(--color-fg-muted)",
          subtle:  "var(--color-fg-subtle)",
        },
        border: {
          DEFAULT: "var(--color-border)",
          strong:  "var(--color-border-strong)",
        },
        accent: {
          DEFAULT: "var(--color-accent)",
          fg:      "var(--color-accent-fg)",
          hover:   "var(--color-accent-hover)",
          soft:    "var(--color-accent-soft)",
        },
        danger:  { DEFAULT: "var(--color-danger)",  fg: "var(--color-danger-fg)",  soft: "var(--color-danger-soft)" },
        warning: { DEFAULT: "var(--color-warning)", fg: "var(--color-warning-fg)", soft: "var(--color-warning-soft)" },
        success: { DEFAULT: "var(--color-success)", fg: "var(--color-success-fg)", soft: "var(--color-success-soft)" },
        info:    { DEFAULT: "var(--color-info)",    fg: "var(--color-info-fg)",    soft: "var(--color-info-soft)" },
      },

      // ── Typography ────────────────────────────────────────────────────
      fontFamily: {
        sans:    "var(--font-sans)",
        display: "var(--font-display)",
        mono:    "var(--font-mono)",
      },
      fontSize: {
        xs:   ["var(--text-xs)",   { lineHeight: "var(--leading-snug)" }],
        sm:   ["var(--text-sm)",   { lineHeight: "var(--leading-normal)" }],
        md:   ["var(--text-md)",   { lineHeight: "var(--leading-normal)" }],
        lg:   ["var(--text-lg)",   { lineHeight: "var(--leading-snug)" }],
        xl:   ["var(--text-xl)",   { lineHeight: "var(--leading-tight)" }],
        "2xl":["var(--text-2xl)",  { lineHeight: "var(--leading-tight)" }],
      },
      fontWeight: {
        regular:  "var(--weight-regular)",
        medium:   "var(--weight-medium)",
        semibold: "var(--weight-semibold)",
      },
      letterSpacing: {
        display: "var(--tracking-display)",
        caps:    "var(--tracking-caps)",
      },

      // ── Spacing ───────────────────────────────────────────────────────
      spacing: {
        1: "var(--space-1)",
        2: "var(--space-2)",
        3: "var(--space-3)",
        4: "var(--space-4)",
        5: "var(--space-5)",
        6: "var(--space-6)",
        7: "var(--space-7)",
        8: "var(--space-8)",
      },

      // ── Radius ────────────────────────────────────────────────────────
      borderRadius: {
        sm:    "var(--radius-1)",
        DEFAULT: "var(--radius-2)",
        lg:    "var(--radius-3)",
        full:  "var(--radius-full)",
      },

      // ── Shadow ────────────────────────────────────────────────────────
      boxShadow: {
        1: "var(--shadow-1)",
        2: "var(--shadow-2)",
        3: "var(--shadow-3)",
      },

      // ── Motion ────────────────────────────────────────────────────────
      transitionDuration: {
        1: "var(--dur-1)",
        2: "var(--dur-2)",
        3: "var(--dur-3)",
      },
      transitionTimingFunction: {
        out:  "var(--ease-out)",
        in:   "var(--ease-in)",
        soft: "var(--ease-soft)",
      },

      // ── Z-index ───────────────────────────────────────────────────────
      zIndex: {
        sticky:   "var(--z-sticky)",
        dropdown: "var(--z-dropdown)",
        popover:  "var(--z-popover)",
        drawer:   "var(--z-drawer)",
        modal:    "var(--z-modal)",
        toast:    "var(--z-toast)",
        tooltip:  "var(--z-tooltip)",
      },
    },
  },
}

export default config
