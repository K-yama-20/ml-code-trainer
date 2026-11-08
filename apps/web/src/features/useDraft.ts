import { useEffect, useRef, useState } from "react";
import { userApi } from "../lib/api";
import { writeLocal } from "../lib/drafts";
export function useDraft(
  user: string,
  item: string,
  initial: string,
  initialRevision: number,
  remoteCode: string | null = null,
) {
  const [code, setCode] = useState(initial),
    [status, setStatus] = useState("保存済み");
  const latest = useRef(initial),
    revision = useRef(initialRevision),
    serverCode = useRef(remoteCode ?? ""),
    saving = useRef(false),
    conflict = useRef(false);
  const persist = async () => {
    await writeLocal(user, item, {
      code: latest.current,
      revision: revision.current,
      savedAt: Date.now(),
      dirty: serverCode.current !== latest.current,
    });
  };
  const sync = async () => {
    if (
      saving.current ||
      conflict.current ||
      serverCode.current === latest.current
    )
      return;
    saving.current = true;
    const captured = latest.current;
    try {
      const response = await userApi<{ revision: number }>(`/drafts/${item}`, {
        method: "PUT",
        body: JSON.stringify({ code: captured, revision: revision.current }),
      });
      revision.current = response.revision;
      serverCode.current = captured;
      await persist();
      setStatus(latest.current === captured ? "保存済み" : "ローカル保存済み");
    } catch (err) {
      if (err instanceof Error && "status" in err && err.status === 409) {
        conflict.current = true;
        setStatus("競合あり・ローカル保持中");
      } else setStatus("ローカル保存済み・同期待ち");
    } finally {
      saving.current = false;
    }
  };
  useEffect(() => {
    latest.current = code;
    setStatus("保存中…");
    const a = setTimeout(() => {
      persist()
        .then(() =>
          setStatus(
            conflict.current ? "競合あり・ローカル保持中" : "ローカル保存済み",
          ),
        )
        .catch(() => setStatus("保存失敗・コードをコピーしてください"));
    }, 1000);
    const b = setTimeout(() => {
      void sync();
    }, 5000);
    return () => {
      clearTimeout(a);
      clearTimeout(b);
    };
  }, [code]);
  useEffect(() => {
    const save = () => {
      void persist();
      void sync();
    };
    window.addEventListener("pagehide", save);
    return () => {
      window.removeEventListener("pagehide", save);
      void persist();
      void sync();
    };
  }, []);
  return {
    code,
    setCode,
    status,
    save: async () => {
      await persist();
      await sync();
    },
  };
}
