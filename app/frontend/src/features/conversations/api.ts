import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { request } from "@/shared/api/client";
import { useSession } from "@/shared/auth/session";
import type {
  ConversationDetail,
  DraftInput,
  DecisionInput,
  OwnershipInput,
  TextInput,
  StaffReplyInput,
} from "@/shared/api/types";

export type ConversationCommand = (
  | { action: "draft"; body: DraftInput }
  | { action: "decision"; body: DecisionInput }
  | { action: "ownership"; body: OwnershipInput }
  | { action: "reply"; body: StaffReplyInput }
  | { action: "messages" | "customer-reply"; body: TextInput }
) & { key: string };

/**
 * Load the selected conversation using a staff-scoped query key; cancellation prevents
 * stale selection updates. Polling stays at 5 s even while live updates are connected
 * (see `useWorkspace`: worker-side results write no audit revision).
 */
export function useConversation(id?: string) {
  const { session } = useSession();
  return useQuery({
    queryKey: ["conversation", session?.user.id, id],
    enabled: !!id,
    /** Fetch the selected request with cancellation so stale navigation cannot overwrite current detail. */
    queryFn: function fetchConversation({ signal }) {
      return request<ConversationDetail>(`/conversations/${id}`, { signal });
    },
    refetchInterval: 5000,
    retry: 1,
  });
}

/** Apply one business action and reconcile affected conversation/aggregate caches after server confirmation. */
export function useConversationAction(id: string) {
  const client = useQueryClient();
  return useMutation({
    /** Send this scoped action with its stable operation ID; server state and permission checks remain authoritative. */
    mutationFn: function mutateConversation({
      action,
      body,
      key,
    }: ConversationCommand) {
      return request(
        `/conversations/${id}/${action}`,
        { method: "POST", body: JSON.stringify(body) },
        key,
      );
    },
    /** Invalidate affected detail and aggregates after confirmed mutation; never optimistically display approval or delivery. */
    onSuccess: function reconcileConversation() {
      return Promise.all([
        client.invalidateQueries({ queryKey: ["conversation"] }),
        client.invalidateQueries({ queryKey: ["workspace"] }),
      ]);
    },
  });
}
