import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { DocumentButton } from "./document-button";

vi.mock("@/shared/api/client", () => ({ documentUrl: vi.fn() }));
import { documentUrl } from "@/shared/api/client";

/** Isolate document lifecycle tests so a previous dialog or blob cannot affect the next case. */
afterEach(/** Remove prior rendered document state and restore test doubles. */
function cleanDocumentFixture() {
  cleanup();
  vi.restoreAllMocks();
});

describe("Authorized document viewer", /** Group authorized document fetch and private URL lifecycle assertions. */
function documentSuite() {
  /** Rejecting a protected fetch must show a recoverable error rather than opening a misleading empty document. */
  it("shows an authorized fetch failure without opening a document", /** Prove protected-fetch rejection remains recoverable without showing a document. */
async function failedDocument() {
    vi.mocked(documentUrl).mockRejectedValue(
      new Error("Document access was denied."),
    );
    render(
      <DocumentButton path="/quotes/fixture/pdf" title="Fixture quotation" />,
    );
    fireEvent.click(screen.getByRole("button", { name: "View PDF" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Document access was denied.",
    );
    expect(screen.queryByTitle("Fixture quotation")).not.toBeInTheDocument();
  });

  /** Closing the modal must revoke its private temporary URL and remove the embedded document. */
  it("releases the private blob after closing", /** Prove closing the viewer releases its private URL capability. */
async function releaseDocument() {
    vi.mocked(documentUrl).mockResolvedValue("blob:private-fixture");
    const revoke = vi.fn();
    vi.stubGlobal("URL", Object.assign(URL, { revokeObjectURL: revoke }));
    HTMLDialogElement.prototype.showModal = /** Provide native dialog-open semantics absent from the DOM test environment. */
function showModal() {
      this.setAttribute("open", "");
    };
    HTMLDialogElement.prototype.close = /** Provide native dialog-close semantics absent from the DOM test environment. */
function close() {
      this.removeAttribute("open");
    };
    render(
      <DocumentButton path="/quotes/fixture/pdf" title="Fixture quotation" />,
    );
    fireEvent.click(screen.getByRole("button", { name: "View PDF" }));
    await screen.findByTitle("Fixture quotation");
    fireEvent.click(screen.getByRole("button", { name: "Close document" }));
    await waitFor(/** Wait for the effect cleanup to revoke the exact private document URL. */
function assertReleased() {
      expect(revoke).toHaveBeenCalledWith("blob:private-fixture");
    });
    expect(screen.queryByTitle("Fixture quotation")).not.toBeInTheDocument();
  });
});
