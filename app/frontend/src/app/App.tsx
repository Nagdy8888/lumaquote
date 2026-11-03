import { BrowserRouter, Route, Routes } from "react-router-dom";
import { useSession } from "@/shared/auth/session";
import { SignIn } from "@/features/auth/SignIn";
import { Overview } from "@/features/overview/Overview";
import { InboxPage } from "@/features/conversations/InboxPage";
import { NewRequest } from "@/features/conversations/NewRequest";
import { QuotationsPage } from "@/features/quotations/QuotationsPage";
import { CatalogPage } from "@/features/catalog/CatalogPage";
import { ConnectionsPage } from "@/features/integrations/ConnectionsPage";
import { NotFoundPage } from "@/features/not-found/NotFoundPage";
import { AppShell } from "./AppShell";

/** Route authenticated staff into the business workspace; server authorization remains authoritative. */
export function App() {
  const { session, loading } = useSession();
  if (loading)
    return (
      <main className="app-loading" aria-live="polite">
        Opening your workspace…
      </main>
    );
  if (!session) return <SignIn />;
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Overview />} />
          <Route path="inbox/:id?" element={<InboxPage />} />
          <Route path="requests/new" element={<NewRequest />} />
          <Route path="quotations" element={<QuotationsPage />} />
          <Route path="catalog" element={<CatalogPage />} />
          <Route path="integrations" element={<ConnectionsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
