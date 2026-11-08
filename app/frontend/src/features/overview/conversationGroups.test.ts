import { describe, expect, it } from "vitest";
import { isOpenConversation } from "./conversationGroups";

describe("isOpenConversation", () => {
  /** Quoted, order_pending, declined and ordered conversations are not open requests any more. */
  it("excludes finished and order statuses", () => {
    for (const status of ["quoted", "order_pending", "declined", "ordered"])
      expect(isOpenConversation(status)).toBe(false);
  });

  /** Work in progress, including a request that needs a person, stays open. */
  it("keeps working statuses open", () => {
    for (const status of ["new", "clarifying", "review", "needs_staff"])
      expect(isOpenConversation(status)).toBe(true);
  });
});
