// Canonical office-bearer posts. Stay in sync with
// /app/backend/data/office_posts.py — the backend enforces uniqueness for
// Chairman / Secretary / Treasurer (only one person can hold each). Assistant
// can be held by any number of people.
export const OFFICE_POSTS = [
  "Chairman",
  "Secretary",
  "Treasurer",
  "Assistant",
];

export const UNIQUE_POSTS = new Set(["Chairman", "Secretary", "Treasurer"]);
