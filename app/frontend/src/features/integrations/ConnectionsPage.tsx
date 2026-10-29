import "./connections.css";
import {
  AudioLines,
  Database,
  FileSpreadsheet,
  MessageCircle,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { useWorkspaceContext } from "@/shared/api/workspace-context";
import { Status, money } from "@/shared/ui/status";

const connections = [
  {
    key: "whatsapp",
    name: "WhatsApp",
    icon: MessageCircle,
    description:
      "Customer messages, English voice notes, label photos, and quotation delivery.",
    requirement:
      "Requires your Meta app, test number, authorized recipient, and a verified webhook.",
  },
  {
    key: "google",
    name: "Google Workspace",
    icon: FileSpreadsheet,
    description:
      "Authoritative prices and stock in Sheets. Identical quotation PDFs in Drive.",
    requirement:
      "Requires your OAuth consent, selected workbook, Drive folder, and signed Apps Script callback.",
  },
  {
    key: "ai",
    name: "OpenAI",
    icon: AudioLines,
    description:
      "Structured requirements, English transcription, and grounded product matching.",
    requirement:
      "Paid calls are separately enabled and guarded by spending reservations.",
  },
  {
    key: "langsmith",
    name: "LangSmith",
    icon: Workflow,
    description:
      "Workflow observability with opaque correlation IDs and explicitly limited exports.",
    requirement:
      "Configured credentials alone do not verify a trace. Customer content stays out of exports.",
  },
];

/** Display configured versus verified integration state honestly without exposing credentials or diagnostic payloads. */
export function ConnectionsPage() {
  const { data } = useWorkspaceContext();
  return (
    <section>
      <div className="page-heading">
        <div>
          <h1>A connected sales desk.</h1>
          <p>The right information, where your team already works.</p>
        </div>
        <ShieldCheck />
      </div>
      <div className="local-connection">
        <Database />
        <div>
          <h2>Local Supabase</h2>
          <p>
            PostgreSQL, staff authentication, and private documents. Application
            processes run directly on your computer.
          </p>
        </div>
        <Status value="Connected locally" />
      </div>
      <div className="connections-list">
        {connections.map((connection) => (
          <article key={connection.key}>
            <div className="connection-icon">
              <connection.icon />
            </div>
            <div>
              <h2>{connection.name}</h2>
              <p>{connection.description}</p>
              <small>{connection.requirement}</small>
            </div>
            <Status
              value={data.integrations[connection.key] ?? "not_connected"}
            />
          </article>
        ))}
      </div>
      <section className="allowance-panel">
        <h2>Bounded from the beginning.</h2>
        <div>
          <span>
            Initial estimated AI allowance<strong>$25.00</strong>
          </span>
          <span>
            Daily ceiling<strong>$5.00</strong>
          </span>
          <span>
            Estimated / reserved so far
            <strong>{money(data.usage.estimated_or_reserved)}</strong>
          </span>
        </div>
        <p>
          Reservation-based controls bound admission. Estimates are not provider
          invoices or guaranteed billed totals.
        </p>
      </section>
    </section>
  );
}
