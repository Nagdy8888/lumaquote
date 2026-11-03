import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SectionSwitch } from "./SectionSwitch";

afterEach(cleanup);

describe("SectionSwitch", () => {
  /** Choosing the other option reports it, and re-pressing the selected option never reports an empty value. */
  it("reports the chosen section and ignores deselection", () => {
    const onChange = vi.fn();
    render(
      <SectionSwitch
        value="conversation"
        onChange={onChange}
        needsApproval={false}
      />,
    );
    fireEvent.click(screen.getByRole("radio", { name: "Quotation" }));
    expect(onChange).toHaveBeenCalledWith("quotation");
    onChange.mockClear();
    fireEvent.click(screen.getByRole("radio", { name: "Conversation" }));
    expect(onChange).not.toHaveBeenCalled();
  });

  /** The approval badge appears on the Quotation option only while the quote awaits approval. */
  it("shows Needs approval only when approval is pending", () => {
    const { rerender } = render(
      <SectionSwitch value="conversation" onChange={vi.fn()} needsApproval />,
    );
    expect(screen.getByRole("radio", { name: /Quotation/ })).toHaveTextContent(
      "Needs approval",
    );
    rerender(
      <SectionSwitch
        value="conversation"
        onChange={vi.fn()}
        needsApproval={false}
      />,
    );
    expect(screen.queryByText("Needs approval")).toBeNull();
  });
});
