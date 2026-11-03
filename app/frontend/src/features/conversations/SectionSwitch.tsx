import { Status } from "@/shared/ui/status";
import { ToggleGroup, ToggleGroupItem } from "@/shared/ui/toggle-group";

export type InboxSection = "conversation" | "quotation";

/**
 * Let a narrow (portrait) screen choose between the conversation and the quotation.
 * Inputs: the selected section, a change callback, and whether the quotation awaits
 * approval (adds the server-derived "Needs approval" badge so the decision is
 * discoverable). Output: a two-option segmented control; an empty value from
 * deselecting the current option is ignored so one option is always selected. It is
 * hidden by CSS above 680 px, where all columns show. Side effects: none beyond the
 * callback. Authority: display only; it hides nothing from the server's rules and both
 * panels stay mounted so unsaved quotation edits survive switching.
 */
export function SectionSwitch({
  value,
  onChange,
  needsApproval,
}: {
  value: InboxSection;
  onChange: (next: InboxSection) => void;
  needsApproval: boolean;
}) {
  return (
    <div className="inbox-section-switch">
      <ToggleGroup
        type="single"
        value={value}
        onValueChange={(next) => {
          if (next === "conversation" || next === "quotation") onChange(next);
        }}
        variant="outline"
        size="lg"
        aria-label="Show conversation or quotation"
      >
        <ToggleGroupItem value="conversation">Conversation</ToggleGroupItem>
        <ToggleGroupItem value="quotation">
          Quotation
          {needsApproval && <Status value="review" />}
        </ToggleGroupItem>
      </ToggleGroup>
    </div>
  );
}
