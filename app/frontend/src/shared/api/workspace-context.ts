import { useOutletContext } from "react-router-dom";
import type { Workspace } from "./types";

export type WorkspaceContext = { data: Workspace; capture: boolean };

/** Read route-provided authorized workspace data without creating another remote-state store. */
export function useWorkspaceContext() {
  return useOutletContext<WorkspaceContext>();
}

/** Replace synthetic customer names in capture mode while leaving real workflow states visible. */
export function customerName(name: string, capture: boolean) {
  return capture ? "Project customer" : name;
}
