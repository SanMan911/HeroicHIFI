// Shared date formatter — every user-visible date in the app must use these
// helpers so we maintain consistent dd-mm-yyyy presentation throughout.

const pad = (n) => String(n).padStart(2, "0");

/** Format an ISO string (or Date) as `dd-mm-yyyy`. Returns "—" for falsy input. */
export function formatDate(iso) {
  if (!iso) return "—";
  try {
    const d = iso instanceof Date ? iso : new Date(iso);
    if (Number.isNaN(d.getTime())) return "—";
    return `${pad(d.getDate())}-${pad(d.getMonth() + 1)}-${d.getFullYear()}`;
  } catch {
    return "—";
  }
}

/** Format an ISO string as `dd-mm-yyyy HH:MM`. Returns "—" for falsy input. */
export function formatDateTime(iso) {
  if (!iso) return "—";
  try {
    const d = iso instanceof Date ? iso : new Date(iso);
    if (Number.isNaN(d.getTime())) return "—";
    return `${pad(d.getDate())}-${pad(d.getMonth() + 1)}-${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  } catch {
    return "—";
  }
}

/** Compact tenure label `dd-mm-yyyy → dd-mm-yyyy` or `Since dd-mm-yyyy` if open-ended. */
export function tenureRange(start, end, sinceLabel = "Since") {
  if (!start) return "";
  return end ? `${formatDate(start)} → ${formatDate(end)}` : `${sinceLabel} ${formatDate(start)}`;
}
