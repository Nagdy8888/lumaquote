import { useQuery } from "@tanstack/react-query";
import { request } from "@/shared/api/client";
import type { Workspace } from "@/shared/api/types";
import { useSession } from "@/shared/auth/session";

/**
 * Fetch the current staff workspace with an identity-scoped cache and bounded
 * background reconciliation. `live` is true while the event stream is open; polling
 * then slows to a 30 s safety net instead of 8 s and is never removed.
 */
export function useWorkspace(live = false) {
  const { session } = useSession();
  return useQuery({
    queryKey: ["workspace", session?.user.id],
    enabled: !!session,
    /** Fetch the current staff workspace through authenticated API access. */
    queryFn: function loadWorkspace() {
      return request<Workspace>("/workspace");
    },
    refetchInterval: live ? 30000 : 8000,
    retry: 1,
  });
}
