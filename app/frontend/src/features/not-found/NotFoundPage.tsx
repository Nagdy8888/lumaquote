import { Link } from "react-router-dom";
import { Button } from "@/shared/ui/button";

/**
 * Tell signed-in staff that the address matches no page and offer the two
 * working starting points. Inputs: none. Output: static markup rendered inside
 * the authenticated shell for any unmatched route. Side effects: none, no data
 * is requested. Authority: none; the page names no resource, so it cannot
 * reveal whether a record exists.
 */
export function NotFoundPage() {
  return (
    <section>
      <div className="page-heading">
        <div>
          <h1>This page does not exist.</h1>
          <p>
            The address may be mistyped or the page may have moved. Go back to
            the overview or open your inbox.
          </p>
        </div>
      </div>
      <div className="not-found-actions">
        <Button asChild>
          <Link to="/">Go to overview</Link>
        </Button>
        <Button variant="outline" asChild>
          <Link to="/inbox">Open inbox</Link>
        </Button>
      </div>
    </section>
  );
}
