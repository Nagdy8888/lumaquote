import "./connections.css";
import {
  AudioLines,
  Database,
  FileSpreadsheet,
  Mail,
  MessageCircle,
  Send,
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
      "Requires a Meta app or the Twilio Sandbox, an authorized recipient, and a verified webhook.",
  },
  {
    key: "telegram",
    name: "Telegram",
    icon: Send,
    description:
      "Customer messages, voice notes, label photos, and quotation PDFs through your bot.",
    requirement:
      "Requires a bot token from BotFather and the allowed customer user ids. No tunnel needed.",
  },
  {
    key: "email",
    name: "Gmail",
    icon: Mail,
    description:
      "Customer requests sent to your Gmail under the LumaQuote label, with replies and quotation PDFs sent from Gmail.",
    requirement:
      "Runs through your Apps Script project and the signed gateway. Only allowlisted senders that Gmail authenticates reach the agent.",
  },
  {
    key: "google",
    name: "Google Workspace",
    icon: FileSpreadsheet,
    description:
      "Authoritative prices and stock in Sheets. Apps Script sends signed snapshots after edits and on an approximately one-minute timer.",
    requirement:
      "Runs through your Apps Script project and a selected workbook. Drive export of the approved PDF also runs through Apps Script and has not run in Google yet.",
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
      "Workflow observability: every agent step, model call and tool call with its inputs and outputs.",
    requirement:
      "Keys, tokens and phone numbers are masked before export. Configured credentials alone do not verify a trace.",
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
