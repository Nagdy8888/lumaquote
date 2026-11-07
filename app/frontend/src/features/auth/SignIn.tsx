import "./auth.css";
import { lazy, Suspense, useState, type FormEvent } from "react";
import { ArrowRight, Layers3, LockKeyhole } from "lucide-react";
import { auth } from "@/shared/auth/client";
import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { Field, FieldGroup, FieldLabel } from "@/shared/ui/field";
import { SceneBoundary } from "@/features/overview/SceneBoundary";

const PendantField = lazy(() => import("@/features/showcase/PendantField"));

/** Authenticate actual local staff; no hard-coded credential or automatic account creation reaches the browser. */
export function SignIn() {
  const [email, setEmail] = useState("sales@lumaquote.local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  /** Submit credentials to Supabase Auth and preserve entries after a bounded authentication failure. */
  async function signIn(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError("");
    const { error: failure } = await auth.auth.signInWithPassword({
      email,
      password,
    });
    if (failure)
      setError("Sign-in failed. Check your staff email and password.");
    setPending(false);
  }
  return (
    <main className="signin">
      <section className="signin-story">
        <SceneBoundary fallback={null}>
          <Suspense fallback={null}>
            <PendantField />
          </Suspense>
        </SceneBoundary>
        <div className="brand">
          <Layers3 />
          <span>
            LumaQuote<span className="brand-dot">.</span>
          </span>
        </div>
        <div>
          <h1>
            Better light.
            <br />
            Less back-and-forth.
          </h1>
          <p>
            Customer conversations become considered quotations.
            <br />
            Your team stays in control of every commitment.
          </p>
        </div>
        <span className="disclosure">
          Built for the sales desk. Fictional supplier data.
        </span>
      </section>
      <section className="signin-form">
        <LockKeyhole />
        <h2>Welcome to your workspace</h2>
        <p>Sign in with your local staff account.</p>
        <form onSubmit={signIn}>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="email">Staff email</FieldLabel>
              <Input
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </Field>
            <Field>
              <FieldLabel htmlFor="password">Password</FieldLabel>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </Field>
            {error && (
              <p role="alert" className="error-text">
                {error}
              </p>
            )}
            <Button type="submit" size="lg" disabled={pending}>
              {pending ? "Signing in…" : "Open workspace"}
              <ArrowRight data-icon="inline-end" />
            </Button>
          </FieldGroup>
        </form>
        <small>
          Local setup saves your generated credentials in
          <br />
          <code>.local/staff-access.json</code>.
        </small>
      </section>
    </main>
  );
}
