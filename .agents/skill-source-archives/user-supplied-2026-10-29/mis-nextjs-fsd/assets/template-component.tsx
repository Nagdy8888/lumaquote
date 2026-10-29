/**
 * @file features/<feature-name>/ui/<component-name>.tsx
 * <One-sentence summary of what this component does and where it is used>.
 */
"use client"

import { useState } from "react"
import type { ReactNode } from "react"
import { Button } from "@/shared/ui/button"

/**
 * Props for {@link ExampleComponent}.
 */
export interface ExampleComponentProps {
  /** Initial value shown in the input. */
  initialValue?: string
  /** Called when the user submits the form. */
  onSubmit: (value: string) => void
  /** Optional slot rendered beneath the input. */
  children?: ReactNode
}

/**
 * <One-line summary in imperative mood>.
 *
 * <Optional longer description, wrap at ~80 chars>.
 *
 * @param props - see {@link ExampleComponentProps}
 */
export function ExampleComponent({
  initialValue = "",
  onSubmit,
  children,
}: ExampleComponentProps) {
  const [value, setValue] = useState(initialValue)

  /**
   * Handles the submit click — validates and forwards the value upward.
   */
  function handleSubmit() {
    if (!value.trim()) return
    onSubmit(value.trim())
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        handleSubmit()
      }}
    >
      <input value={value} onChange={(e) => setValue(e.target.value)} />
      {children}
      <Button onClick={handleSubmit}>Submit</Button>
    </form>
  )
}
