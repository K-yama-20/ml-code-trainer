import { openDB } from "idb";
export interface LocalDraft {
  code: string;
  revision: number;
  savedAt: number;
  dirty: boolean;
}
const db = openDB("ml-code-trainer", 1, {
  upgrade(db) {
    db.createObjectStore("drafts");
  },
});
export async function readLocal(
  user: string,
  item: string,
): Promise<LocalDraft | undefined> {
  return (await db).get("drafts", `${user}:${item}`);
}
export async function writeLocal(
  user: string,
  item: string,
  draft: LocalDraft,
) {
  await (await db).put("drafts", draft, `${user}:${item}`);
}
