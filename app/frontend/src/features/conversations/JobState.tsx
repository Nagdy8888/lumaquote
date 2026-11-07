import { LoaderCircle } from "lucide-react";
import type { Job } from "@/shared/api/types";
import { Status } from "@/shared/ui/status";

/**
 * Show what the assistant is doing for one conversation, from real job state only.
 * Input: the jobs of this conversation, newest first (the workspace list is bounded
 * to the 20 newest jobs company-wide and carries no timing or progress, so none is
 * shown). Only the newest `agent` job is considered. Output: a status line for
 * `queued` ("Assistant queued"), `running` ("Assistant is working") and
 * `failed` or `blocked` ("Assistant stopped" plus the error code with underscores as
 * spaces); nothing for `done`, for another kind of job, or when there is no job.
 * Side effects: none. Authority: display only; the server owns job state. The
 * spinner appears only while `running` and does not animate under reduced motion.
 */
export function JobState({ jobs }: { jobs: Job[] }) {
  const job = jobs.find((candidate) => candidate.kind === "agent");
  if (!job || job.status === "done") return null;
  const text =
    job.status === "running"
      ? "Assistant is working"
      : job.status === "queued"
        ? "Assistant queued"
        : job.status === "failed" || job.status === "blocked"
          ? `Assistant stopped${job.error_code ? `: ${job.error_code.replaceAll("_", " ")}` : ""}`
          : null;
  if (text === null) return null;
  return (
    <div className="job-state" role="status">
      <span>
        {job.status === "running" && (
          <LoaderCircle className="job-spinner" aria-hidden="true" />
        )}
        {text}
      </span>
      <Status value={job.status} />
    </div>
  );
}
