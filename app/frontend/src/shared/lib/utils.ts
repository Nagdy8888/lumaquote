import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
/** Merge conditional class names using Tailwind conflict resolution, returning one canonical class string. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
