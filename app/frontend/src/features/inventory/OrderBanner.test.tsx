import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { OrderBanner } from "./OrderBanner";
import { pendingOrder, renderWithClient } from "./testkit";

const request = vi.fn();
vi.mock("@/shared/api/client", () => ({
  request: (...args: unknown[]) => request(...args),
  downloadFile: vi.fn(),
}));
vi.mock("@/shared/auth/session", () => ({
  useSession: () => ({ session: { user: { id: "staff-1" } }, loading: false }),
}));
afterEach(cleanup);

describe("OrderBanner", () => {
  /** Shows only this conversation's pending order, and confirming sends an idempotency key and refreshes. */
  it("confirms the order with an idempotency key and invalidates the caches", async () => {
    request.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/orders?")
          ? {
              items: [
                pendingOrder({ id: "other", conversation_id: "c2" }),
                pendingOrder(),
              ],
            }
          : pendingOrder({ status: "confirmed" }),
      ),
    );
    const { invalidate } = renderWithClient(
      <OrderBanner conversationId="c1" quoteNumber="LQ-1001" />,
    );
    expect(
      await screen.findByText("Customer accepted LQ-1001 revision 2"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Confirm order" }));
    await waitFor(() =>
      expect(request).toHaveBeenCalledWith(
        "/orders/o1/confirm",
        { method: "POST" },
        expect.stringMatching(/.{8,}/),
      ),
    );
    await waitFor(() => {
      const keys = invalidate.mock.calls.map((call) => call[0]?.queryKey?.[0]);
      expect(keys).toEqual(
        expect.arrayContaining(["inventory", "workspace", "conversation"]),
      );
    });
  });

  /** Nothing renders when this conversation has no pending order. */
  it("renders nothing without a pending order for the conversation", async () => {
    request.mockResolvedValue({
      items: [pendingOrder({ conversation_id: "other" })],
    });
    const { container } = renderWithClient(
      <OrderBanner conversationId="c1" quoteNumber="LQ-1001" />,
    );
    await waitFor(() => expect(request).toHaveBeenCalled());
    expect(container).toBeEmptyDOMElement();
  });

  /** The server's plain refusal appears inline under the buttons. */
  it("shows the server message when confirming fails", async () => {
    request.mockImplementation((path: string) =>
      path.startsWith("/orders?")
        ? Promise.resolve({ items: [pendingOrder()] })
        : Promise.reject(new Error("This order is already cancelled.")),
    );
    renderWithClient(<OrderBanner conversationId="c1" quoteNumber={null} />);
    fireEvent.click(await screen.findByRole("button", { name: "Confirm order" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "This order is already cancelled.",
    );
  });

  /** Cancel needs a reason of at least three characters before it can be sent. */
  it("cancels with a reason", async () => {
    request.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/orders?") ? { items: [pendingOrder()] } : pendingOrder({ status: "cancelled" }),
      ),
    );
    renderWithClient(<OrderBanner conversationId="c1" quoteNumber="LQ-1" />);
    fireEvent.click(await screen.findByRole("button", { name: "Cancel order" }));
    const dialog = await screen.findByRole("dialog");
    const send = within(dialog).getByRole("button", { name: "Cancel order" });
    expect(send).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Reason/), {
      target: { value: "Customer called" },
    });
    expect(send).toBeEnabled();
    fireEvent.click(send);
    await waitFor(() =>
      expect(request).toHaveBeenCalledWith(
        "/orders/o1/cancel",
        { method: "POST", body: JSON.stringify({ reason: "Customer called" }) },
        expect.any(String),
      ),
    );
  });
});
