/**
 * @file <layer>/<slice>/index.ts
 * Public API for the <slice> slice. Only symbols re-exported below may be
 * consumed from outside the slice. Reaching past this file is forbidden by
 * the FSD lint rules (see steiger.config.ts).
 */

// UI ---------------------------------------------------------------
export { ExampleComponent } from "./ui/example-component"

// Model ------------------------------------------------------------
export { useExample } from "./model/use-example"
export type { ExampleState } from "./model/types"

// API --------------------------------------------------------------
export { fetchExample } from "./api/fetch-example"
