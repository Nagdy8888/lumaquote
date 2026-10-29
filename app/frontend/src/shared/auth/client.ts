import { createClient } from "@supabase/supabase-js";

/** Local Auth client; only public Supabase configuration may cross into the browser. */
export const auth = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
  {
    auth: {
      persistSession: true,
      storage: sessionStorage,
      detectSessionInUrl: false,
    },
  },
);
