---
name: LumaQuote
description: Graphite and copper lighting sales workspace
colors:
  primary: "#8d452c"
  primary-foreground: "#ffffff"
  graphite: "#191e1f"
  scene-graphite: "#202727"
  background: "#f5f4f0"
  foreground: "#24292a"
  secondary: "#e9e7e1"
  muted-foreground: "#666b68"
  border: "#dcded5"
  card: "#ffffff"
  copper-highlight: "#c59372"
  focus: "#b67151"
  review-surface: "#f6eddb"
  review-text: "#81611e"
  approved-surface: "#eaf0e6"
  approved-text: "#48643a"
  blocked-surface: "#fae8df"
  blocked-text: "#944a32"
typography:
  display:
    fontFamily: '"Space Grotesk Variable", sans-serif'
    fontSize: "39px"
    fontWeight: 400
    lineHeight: 1.12
    letterSpacing: "-0.035em"
  headline:
    fontFamily: '"Space Grotesk Variable", sans-serif'
    fontSize: "29px"
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: "-0.03em"
  title:
    fontFamily: '"Space Grotesk Variable", sans-serif'
    fontSize: "17px"
    fontWeight: 500
    letterSpacing: "-0.03em"
  body:
    fontFamily: '"IBM Plex Sans", sans-serif'
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: '"IBM Plex Sans", sans-serif'
    fontSize: "12px"
    fontWeight: 500
rounded:
  sm: "6px"
  md: "8px"
  lg: "12px"
  pill: "9999px"
spacing:
  compact: "8px"
  control: "12px"
  standard: "16px"
  panel: "24px"
  section: "28px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.primary-foreground}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    height: "36px"
  button-outline:
    backgroundColor: "{colors.background}"
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    height: "36px"
  button-ghost:
    textColor: "{colors.foreground}"
    rounded: "{rounded.md}"
    height: "36px"
  navigation:
    backgroundColor: "{colors.graphite}"
  working-container:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.lg}"
    padding: "20px 24px"
  input:
    rounded: "{rounded.md}"
    height: "36px"
    padding: "4px 12px"
  status-review:
    backgroundColor: "{colors.review-surface}"
    textColor: "{colors.review-text}"
    rounded: "{rounded.pill}"
    padding: "3px 7px"
---

# Design System: LumaQuote

## Overview

**Creative North Star: "The Lighting Sales Desk"**

The lighting supplier?s sales desk combines a graphite navigation frame, warm copper actions, and light mineral working surfaces. It feels restrained and practical: dense operational information remains readable while Space Grotesk gives titles and totals a distinct character.

Depth comes mainly from tonal separation and fine borders. The optional procedural lighting scene supplies a controlled presentation moment; the workspace stays usable with its static fallback and reduced motion. Surface-specific composition belongs in docs/UI_DIRECTION.md.

**Key Characteristics:**
- Graphite framing with mineral working panels.
- Warm copper for primary actions and selective emphasis.
- Compact, readable information with explicit textual states.
- Optional illustrative 3D with a complete static fallback.

This record was extracted from styles.css, app/shell.css, feature CSS and shared UI primitives after the scoped finish review. Local accessibility evidence in .local/ui-accessibility.json reports zero axe violations for Overview and Inbox at desktop and portrait sizes. This is bounded local evidence, not a complete accessibility certification or proof of PDF output, external delivery, or production readiness.

## Colors

Warm copper supplies action emphasis against graphite framing and mineral neutrals. Frontmatter records the actual source values; the sidecar's generated tonal ramps are exploratory swatches, not additional application tokens.

### Primary
- **Warm Copper:** Primary buttons and key actions.
- **Copper Highlight:** Brand mark and restrained emphasis on dark surfaces.
- **Focus Copper:** Visible keyboard outline.

### Secondary
- **Review Amber, Approved Olive, Blocked Clay:** Paired surface/text colors communicate operational states through words as well as hue.

### Neutral
- **Graphite / Scene Graphite:** Navigation and the lighting presentation surface.
- **Mineral Background / Secondary:** Workspace and subdued support surfaces.
- **Ink / Muted Ink:** Main and supporting text.
- **Fine Mineral Border / White Card:** Separators and working containers.

**The Textual State Rule.** Status color always accompanies a readable state label.

## Typography

**Display Font:** Space Grotesk Variable, sans-serif.
**Body Font:** IBM Plex Sans, sans-serif.

Both families are self-hosted through fontsource imports; body weights are 400, 500 and 600. The geometric display face distinguishes headings and numeric totals from compact operational copy.

### Hierarchy
- **Display:** Lighting heading; its base token grows to 48px above 1650px and becomes 35px on portrait screens.
- **Headline:** Page titles; 26px at the compact rail breakpoint and 25px on portrait screens.
- **Title:** Section headings; quote context uses 16px and portrait context 19px.
- **Body / Label:** Most workflow copy uses the compact frontmatter roles; controls retain their shared 14px default where no feature override applies.
- **Metrics:** Space Grotesk at 34px, increasing to 40px on wide screens and reducing to 32px on portrait screens.

**The Two-Face Rule.** Space Grotesk carries headings and totals; IBM Plex Sans carries operational reading and controls.

## Layout

The shell uses a 224px rail beside a flexible main column. It narrows to 190px below 1250px and a 74px icon rail below 1050px. At 680px it becomes a sticky 62px top navigation bar with a disclosure menu for remaining destinations. The body has a 360px minimum width. Main padding is 34px 35px by default, 28px 24px at compact desktop sizes, 25px 18px on portrait screens, and 40px 55px above 1650px.

The Inbox places a 245px request column, flexible conversation column with a 300px minimum, and 330px quotation panel side by side. At 900px the quote panel moves under the conversation; portrait layouts stack the working sections. Overview's lighting surface splits evenly on desktop and stacks on portrait screens; four metrics become two columns. Reused gaps and padding favor the spacing rhythm in frontmatter rather than a rigid universal grid.

## Elevation & Depth

Working panels are mainly flat, separated by borders and surface tones. Shared outline buttons and inputs carry a subtle utility shadow. The mobile navigation disclosure uses a soft overlay shadow (0 12px 24px #0a140d33). The catalog's illustrated object has a local material shadow; it is not a general card-elevation rule. The procedural scene has its own contact shadows.

**The Working Surface Rule.** Establish panel hierarchy through tone and borders before adding elevation.

## Shapes

Controls use the medium radius, compact product and terms surfaces the small radius, and major scene or register containers the large radius. Status badges are pills. Icons are SVG, not textual glyph substitutes; product thumbnails may use simple CSS geometry.

## Components

### Buttons

Restrained, compact controls. Primary buttons use copper with white text, the medium radius and a 36px default height; a leading icon reduces horizontal padding. Hover reduces primary opacity to 90%. Outline buttons use the workspace surface and a thin border; ghost buttons gain the secondary surface on hover. Disabled controls reduce opacity and block pointer events. Keyboard focus uses a copper border/ring; the global focus outline is 3px with a 4px offset.

### Chips

Compact, textual status pills use feature-specific state colors. Review and clarifying share amber; approved and quoted use olive; blocked and failed use clay. Neutral states remain quiet. A badge is not automatically an interactive control.

### Cards / Containers

White or mineral panels use fine borders and large corners where contained; the quotation panel uses a pale working surface and a dividing edge. Padding commonly spans 18?24px. Avoid treating every section as a raised card.

### Inputs / Fields

Shared fields use a transparent background, fine border, medium corners and a 36px height. Feature quantity fields are smaller at 28px. Focus adds a copper ring; invalid state uses destructive red, and disabled state reduces opacity. Validation belongs to the owning workflow; styling does not imply acceptance.

### Navigation

Graphite navigation uses muted light text, a lighter active surface and a slightly darker hover surface. Desktop links pair SVG icons with text; compact rail links retain accessible names. Portrait navigation keeps key routes visible and places additional destinations in a native disclosure menu.

### Illustrative Lighting Scene

A lazy procedural luminaire responds to orbit and three labeled radio temperature choices. Rendering is demand-driven, zoom/pan are disabled, and pixel ratio is capped at 1.5. Reduced-motion preference immediately selects the meaningful static fallback, including when the preference changes. Loading, unavailable WebGL, and scene errors also retain a fallback. The global reduced-motion media query removes animation and transitions and restores automatic scrolling. This is illustrative presentation, never photometric or manufacturer evidence.

## Do's and Don'ts

### Do:
- **Do** keep primary actions copper and working panels light.
- **Do** pair each status color with its truthful textual state.
- **Do** retain visible keyboard focus and meaningful navigation names.
- **Do** preserve the static scene fallback and reduced-motion behavior.

### Don't:
- **Don?t** make WebGL a requirement for a commercial task.
- **Don?t** present the procedural luminaire as a verified product render.
- **Don?t** replace actual workflow states with decorative success claims.
