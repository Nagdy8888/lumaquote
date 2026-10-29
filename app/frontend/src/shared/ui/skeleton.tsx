import { cn } from "@/shared/lib/utils";

/** Render a noninteractive loading placeholder; never use it as a confirmed business state. */
function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      className={cn("animate-pulse rounded-md bg-accent", className)}
      {...props}
    />
  );
}

export { Skeleton };
