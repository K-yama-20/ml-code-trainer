import { useState } from "react";
import { CodeEditor } from "./CodeEditor";
import type { Problem } from "../types/domain";

export function answerLayout(p: Problem, code: string) {
  const starter = p.starter_code.replaceAll("\r\n", "\n");
  code = code.replaceAll("\r\n", "\n");
  const supplied = p.workspace?.provided_code
    ? p.workspace.provided_code.replaceAll("\r\n", "\n") +
      (p.workspace.mode === "function" && starter ? "\n\n" : "\n")
    : "";
  const invocation = p.workspace?.invocation
    ? (starter ? "\n\n" : "\n") + p.workspace.invocation
    : "";
  let before = "",
    after = "",
    value = code;
  let legacyEmpty = false,
    legacyCursor = 0;
  const explicit = p.editable_regions?.[0];
  const slot =
    p.type === "bugfix"
      ? null
      : starter.match(/\b___\b/g)?.length === 1
        ? /\b___\b/.exec(starter)
        : starter.match(/^[ \t]*pass[ \t]*$/gm)?.length === 1
          ? /(?<=^[ \t]*)pass(?=[ \t]*$)/m.exec(starter)
          : null;
  if (
    explicit &&
    explicit.start === starter.length &&
    explicit.end === explicit.start
  ) {
    before = starter;
    value = code.startsWith(before) ? code.slice(before.length) : code;
  } else if (slot) {
    const a = starter.slice(0, slot.index);
    const b = starter.slice(slot.index + slot[0].length);
    if (!p.workspace) {
      // Versions from before concrete workspaces allowed full-function answers.
      // Preserve that range and only remove the initial placeholder from view.
      if (code === starter) value = a + b;
      legacyEmpty = value === a + b;
      if (legacyEmpty) legacyCursor = a.length;
    } else if (
      code.length >= a.length + b.length &&
      code.startsWith(a) &&
      code.endsWith(b)
    ) {
      before = a;
      after = b;
      value =
        code === starter ? "" : code.slice(a.length, code.length - b.length);
    }
  } else if (code === starter && p.type !== "bugfix") {
    if (/^result\s*=\s*$/.test(starter)) value = "result = ";
    else if (
      /^# (ここに|必要な処理)/.test(starter) &&
      starter.trim().split("\n").length === 1
    )
      value = "";
  }
  return {
    prefix: supplied + before,
    suffix: after + (after.endsWith("\n") ? invocation.slice(1) : invocation),
    value,
    legacyEmpty,
    cursorOffset: /^result = *$/.test(value) ? value.length : legacyCursor,
    fixedLines: supplied ? supplied.split("\n").length - 1 : 0,
    encode: (v: string) => before + v + after,
  };
}

export function needsAnswer(p: Problem, code: string) {
  const layout = answerLayout(p, code);
  const value = layout.value.trim();
  return (
    p.type !== "bugfix" &&
    (code === p.starter_code ||
      layout.legacyEmpty ||
      !value ||
      /^result\s*=$/.test(value))
  );
}

export function AnswerWorkspace({
  p,
  code,
  onChange,
  fontSize,
  theme,
  errorLine,
  autoFocus,
  onFocusReady,
  onCompositionChange,
}: {
  p: Problem;
  code: string;
  onChange: (s: string) => void;
  fontSize: number;
  theme?: string;
  errorLine?: number;
  autoFocus?: boolean;
  onFocusReady?: (focus: (() => void) | null) => void;
  onCompositionChange?: (active: boolean) => void;
}) {
  // The mounted model owns edits. Only a problem change or an explicit reset
  // mounts a new workspace; draft sync never feeds text back into the model.
  const [layout] = useState(() => answerLayout(p, code));
  const { prefix, suffix, value, fixedLines, cursorOffset, encode } = layout;
  return (
    <CodeEditor
      value={prefix + value + suffix}
      uncontrolled
      fontSize={fontSize}
      theme={theme}
      errorLine={errorLine ? errorLine + fixedLines : undefined}
      onChange={(text) =>
        onChange(encode(text.slice(prefix.length, text.length - suffix.length)))
      }
      onMount={(editor, api) => {
        const model = editor.getModel()!;
        const end = () => model.getValueLength() - suffix.length;
        const push = model.pushEditOperations.bind(model);
        // Typing (including composition), paste, cut and editor commands share
        // this transaction entry point. Reject the whole batch before applying
        // anything. Native Monaco undo/redo then only sees allowed edits.
        model.setEOL(api.editor.EndOfLineSequence.LF);
        model.updateOptions({ trimAutoWhitespace: false });
        model.pushEditOperations = (selections, edits, compute, ...rest) => {
          if (
            edits.some(
              ({ range }) =>
                model.getOffsetAt(api.Range.getStartPosition(range)) <
                  prefix.length ||
                model.getOffsetAt(api.Range.getEndPosition(range)) > end(),
            )
          )
            return selections;
          return push(selections, edits, compute, ...rest);
        };
        editor.addCommand(
          api.KeyMod.CtrlCmd | api.KeyCode.KeyA,
          () => {
            const first = model.getPositionAt(prefix.length);
            const last = model.getPositionAt(end());
            editor.setSelection(api.Range.fromPositions(first, last));
          },
          "editorTextFocus",
        );
        if (fixedLines) {
          editor.createDecorationsCollection([
            {
              range: new api.Range(1, 1, fixedLines, 1),
              options: { isWholeLine: true, className: "fixed-code-line" },
            },
          ]);
        }
        onFocusReady?.(() => editor.focus());
        editor.onDidCompositionStart(() => onCompositionChange?.(true));
        editor.onDidCompositionEnd(() => onCompositionChange?.(false));
        editor.onDidDispose(() => {
          onFocusReady?.(null);
          onCompositionChange?.(false);
        });
        editor.setPosition(model.getPositionAt(prefix.length + cursorOffset));
        if (
          autoFocus ||
          (matchMedia("(min-width: 761px) and (pointer: fine)").matches &&
            document.activeElement === document.body)
        )
          editor.focus();
      }}
    />
  );
}
