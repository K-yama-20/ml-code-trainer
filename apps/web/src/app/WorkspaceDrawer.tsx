import { Menu, X } from "lucide-react";
import {
  useId,
  useRef,
  useState,
  type MouseEvent,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import "./WorkspaceDrawer.css";

export function WorkspaceDrawer({
  children,
  saveDraft,
}: {
  children: ReactNode;
  saveDraft: () => Promise<void> | undefined;
}) {
  const id = useId();
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const pending = useRef(false);
  const [saveError, setSaveError] = useState(false);
  const navigate = useNavigate();

  async function followLink(event: MouseEvent<HTMLDialogElement>) {
    const drawer = event.currentTarget;
    if (event.target === drawer) {
      drawer.close();
      return;
    }
    const link =
      event.target instanceof Element
        ? event.target.closest<HTMLAnchorElement>("a[href]")
        : null;
    if (
      !link ||
      event.defaultPrevented ||
      event.button !== 0 ||
      event.altKey ||
      event.ctrlKey ||
      event.metaKey ||
      event.shiftKey
    )
      return;

    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setSaveError(false);
    try {
      await saveDraft();
      if (drawer.open && drawer.isConnected) {
        drawer.close();
        navigate(link.pathname + link.search + link.hash);
      }
    } catch {
      setSaveError(true);
    } finally {
      pending.current = false;
    }
  }

  return (
    <>
      <button
        ref={trigger}
        type="button"
        className="icon-btn"
        aria-label="メニューを開く"
        aria-haspopup="dialog"
        aria-controls={id}
        onClick={() => {
          const drawer = dialog.current;
          if (!drawer || drawer.open) return;
          setSaveError(false);
          drawer.toggleAttribute(
            "data-keep-scrollbar-gutter",
            window.innerWidth > document.documentElement.clientWidth,
          );
          drawer.showModal();
        }}
      >
        <Menu size={19} />
      </button>
      {createPortal(
        <dialog
          id={id}
          ref={dialog}
          className="workspace-drawer"
          aria-label="Workspaceナビゲーション"
          onClickCapture={(event) => void followLink(event)}
          onClose={() => {
            if (!dialog.current?.open)
              trigger.current?.focus({ preventScroll: true });
          }}
          onKeyDown={(event) => {
            if (event.key !== "Tab") return;
            const focusable =
              event.currentTarget.querySelectorAll<HTMLElement>(
                "button, a[href]",
              );
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (document.activeElement === (event.shiftKey ? first : last)) {
              event.preventDefault();
              (event.shiftKey ? last : first).focus();
            }
          }}
        >
          <div className="workspace-drawer-panel">
            <button
              type="button"
              className="icon-btn workspace-drawer-close"
              aria-label="メニューを閉じる"
              onClick={() => dialog.current?.close()}
            >
              <X size={18} />
            </button>
            {children}
            {saveError && (
              <p className="workspace-drawer-error" role="alert">
                下書きを保存できませんでした。時間をおいてもう一度お試しください。
              </p>
            )}
          </div>
        </dialog>,
        document.body,
      )}
    </>
  );
}
