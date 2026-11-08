import { Download, Sheet } from "lucide-react";
import { Button } from "@/shared/ui/button";
import {
  useDownloadWorkbook,
  useQueueSheetExport,
  useSheetExport,
  type SheetExport,
} from "./api";

/**
 * Plain-language status line for the latest Google Sheets export. Pure. Output: a sentence for
 * queued ("Apps Script picks it up within about a minute"), claimed, done (row counts per tab
 * and the completion time) or failed (the short error code); an empty string for none.
 */
export function sheetStatusText(exp: SheetExport | undefined): string {
  if (!exp || exp.status === "none") return "";
  if (exp.status === "queued")
    return "Queued. Apps Script picks it up within about a minute.";
  if (exp.status === "claimed")
    return "Apps Script is writing the Google Sheet…";
  if (exp.status === "failed")
    return `Failed${exp.error_code ? ` (${exp.error_code.replaceAll("_", " ")})` : ""}. You can export again.`;
  const counts = Object.entries(exp.row_counts ?? {})
    .map(([tab, rows]) => `${tab.replaceAll("_", " ")} ${rows}`)
    .join(", ");
  const at = exp.completed_at
    ? new Date(exp.completed_at).toLocaleTimeString("en-US", {
        hour: "numeric",
        minute: "2-digit",
      })
    : "";
  return `Done${at ? ` at ${at}` : ""}. Rows written: ${counts || "none"}.`;
}

/**
 * Export controls for the stock page. "Download Excel" fetches the workbook with the bearer token
 * and saves it under the server's filename. "Export to Google Sheets" queues a signed export that
 * Apps Script pulls (about a minute); the status line below re-reads every 5 s while queued or
 * claimed and stays visible after done or failed. Both buttons are disabled while their request
 * is running, and while an export is queued or claimed, so a click cannot stack exports. Errors
 * (for example the 10 per minute download limit) are shown inline in plain words.
 */
export function ExportToolbar() {
  const download = useDownloadWorkbook();
  const queue = useQueueSheetExport();
  const latest = useSheetExport();
  const status = latest.data?.status;
  const busy = status === "queued" || status === "claimed";
  const error = download.error ?? queue.error;
  return (
    <div className="inv-toolbar">
      <Button
        variant="outline"
        disabled={download.isPending}
        onClick={() => download.mutate()}
      >
        <Download data-icon="inline-start" />
        {download.isPending ? "Preparing…" : "Download Excel"}
      </Button>
      <Button
        variant="outline"
        disabled={queue.isPending || busy}
        onClick={() => queue.mutate()}
      >
        <Sheet data-icon="inline-start" />
        {queue.isPending ? "Queuing…" : "Export to Google Sheets"}
      </Button>
      <p className="inv-export-status" role="status" aria-live="polite">
        {sheetStatusText(latest.data)}
      </p>
      {error && (
        <p className="error-text" role="alert">
          {error.message}
        </p>
      )}
    </div>
  );
}
