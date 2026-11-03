import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { Job } from "@/shared/api/types";
import { JobState } from "./JobState";

afterEach(cleanup);

/** Build one job with sensible defaults so each test names only what it varies. */
function job(overrides: Partial<Job>): Job {
  return {
    id: "00000000-0000-0000-0000-000000000001",
    conversation_id: "00000000-0000-0000-0000-0000000000c1",
    kind: "agent",
    status: "queued",
    error_code: null,
    ...overrides,
  };
}

describe("JobState", () => {
  /** A running agent job is announced as a status with the working text and a Running badge. */
  it("shows the working line for a running job", () => {
    render(<JobState jobs={[job({ status: "running" })]} />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "Assistant is working",
    );
    expect(screen.getByRole("status")).toHaveTextContent("Running");
  });

  /** A queued agent job says it is queued. */
  it("shows the queued line", () => {
    render(<JobState jobs={[job({ status: "queued" })]} />);
    expect(screen.getByRole("status")).toHaveTextContent("Assistant queued");
  });

  /** Failed and blocked jobs show the error code with underscores replaced by spaces. */
  it.each(["failed", "blocked"])(
    "shows the error code for a %s job",
    (status) => {
      render(
        <JobState
          jobs={[job({ status, error_code: "provider_unavailable" })]}
        />,
      );
      expect(screen.getByRole("status")).toHaveTextContent(
        "Assistant stopped: provider unavailable",
      );
    },
  );

  /** A stopped job without an error code still says it stopped. */
  it("omits the colon when no error code exists", () => {
    render(<JobState jobs={[job({ status: "failed" })]} />);
    expect(screen.getByRole("status").textContent).toContain(
      "Assistant stopped",
    );
    expect(screen.getByRole("status").textContent).not.toContain(":");
  });

  /** A finished newest job, no jobs, and non-agent jobs render nothing. */
  it("renders nothing for done, empty and non-agent jobs", () => {
    const { container, rerender } = render(
      <JobState jobs={[job({ status: "done" })]} />,
    );
    expect(container).toBeEmptyDOMElement();
    rerender(<JobState jobs={[]} />);
    expect(container).toBeEmptyDOMElement();
    rerender(
      <JobState jobs={[job({ kind: "drive_export", status: "running" })]} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  /** Only the newest agent job counts: an older running job is ignored when the newest is done. */
  it("uses the newest agent job only", () => {
    const { container } = render(
      <JobState
        jobs={[
          job({ id: "new", status: "done" }),
          job({ id: "old", status: "running" }),
        ]}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  /** The spinner is decorative and appears only for running jobs. */
  it("shows a hidden spinner only while running", () => {
    const { container, rerender } = render(
      <JobState jobs={[job({ status: "running" })]} />,
    );
    expect(container.querySelector(".job-spinner")).toHaveAttribute(
      "aria-hidden",
      "true",
    );
    rerender(<JobState jobs={[job({ status: "queued" })]} />);
    expect(container.querySelector(".job-spinner")).toBeNull();
  });
});
