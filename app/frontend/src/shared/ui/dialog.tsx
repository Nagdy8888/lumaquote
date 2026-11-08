import * as React from "react";
import { Dialog as DialogPrimitive } from "radix-ui";
import { XIcon } from "lucide-react";
import { cn } from "@/shared/lib/utils";

/** Root of one modal: owns open state and focus trapping; callers supply `open` and `onOpenChange` or a trigger. */
function Dialog(props: React.ComponentProps<typeof DialogPrimitive.Root>) {
  return <DialogPrimitive.Root data-slot="dialog" {...props} />;
}

/** Close control that composes onto a child button; closing never submits anything. */
function DialogClose(
  props: React.ComponentProps<typeof DialogPrimitive.Close>,
) {
  return <DialogPrimitive.Close data-slot="dialog-close" {...props} />;
}

/**
 * Modal surface with an overlay, a labelled close button and Escape/outside-click dismissal.
 * Radix moves focus into the content on open and back to the trigger on close. There is no
 * open/close animation, so reduced-motion preferences need no special case. `side="right"`
 * renders a full-height drawer instead of a centered dialog. Callers must render a
 * `DialogTitle` and should render a `DialogDescription`.
 */
function DialogContent({
  className,
  children,
  side = "center",
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Content> & {
  side?: "center" | "right";
}) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay
        data-slot="dialog-overlay"
        className="fixed inset-0 z-50 bg-black/50"
      />
      <DialogPrimitive.Content
        data-slot="dialog-content"
        data-side={side}
        className={cn(
          "fixed z-50 grid gap-4 border bg-background p-6 shadow-lg outline-none",
          side === "center"
            ? "top-1/2 left-1/2 max-h-[90vh] w-[calc(100%-2rem)] max-w-lg -translate-x-1/2 -translate-y-1/2 overflow-y-auto rounded-lg"
            : "inset-y-0 right-0 w-full max-w-md grid-rows-[auto_1fr] overflow-y-auto",
          className,
        )}
        {...props}
      >
        {children}
        <DialogPrimitive.Close
          data-slot="dialog-close"
          className="absolute top-4 right-4 rounded-sm opacity-70 hover:opacity-100 focus-visible:ring-[3px] focus-visible:ring-ring/50 [&_svg]:size-4"
        >
          <XIcon />
          <span className="sr-only">Close</span>
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

/** Stack the title and description at the top of a dialog. */
function DialogHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="dialog-header"
      className={cn("flex flex-col gap-1.5 pr-6 text-left", className)}
      {...props}
    />
  );
}

/** Right-align the action buttons at the bottom of a dialog; wraps on narrow screens. */
function DialogFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="dialog-footer"
      className={cn("flex flex-wrap justify-end gap-2", className)}
      {...props}
    />
  );
}

/** Accessible name of the dialog (announced on open). */
function DialogTitle({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      data-slot="dialog-title"
      className={cn("text-lg leading-none font-medium", className)}
      {...props}
    />
  );
}

/** Accessible description of the dialog (announced after the title). */
function DialogDescription({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      data-slot="dialog-description"
      className={cn("text-sm text-muted-foreground", className)}
      {...props}
    />
  );
}

export {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
};
