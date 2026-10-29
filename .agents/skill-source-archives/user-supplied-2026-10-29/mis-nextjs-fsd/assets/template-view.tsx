/**
 * @file views/<view-name>/ui/<view-name>-view.tsx
 * <View-name> view composition: combines widgets + features into the full page.
 *
 * The FSD "pages" layer lives at src/views/ in this codebase because Next.js
 * reserves src/pages/ for the legacy Pages Router. Routing files still live
 * under src/app/<route>/page.tsx and import the view from here.
 */
import type { Metadata } from "next"
import { LoginForm } from "@/features/login"
import { SiteFooter } from "@/widgets/site-footer"

/**
 * SEO metadata for the view. Re-exported from the view slice's index.ts and
 * consumed by the Next.js route file (`app/<route>/page.tsx`).
 */
export const metadata: Metadata = {
  title: "<View title>",
  description: "<View description>",
}

/**
 * Renders the <view-name> view composition.
 */
export function ExampleView() {
  return (
    <main>
      <LoginForm onSuccess={handleLoginSuccess} />
      <SiteFooter />
    </main>
  )
}

/**
 * Navigates onward once the login succeeds.
 *
 * @param userId - the id of the user who just signed in
 */
function handleLoginSuccess(userId: string): void {
  // example: redirect, telemetry, …
  void userId
}
