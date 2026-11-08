import Editor, { loader, type OnMount } from "@monaco-editor/react";
import * as monaco from "monaco-editor/editor/editor.api.js";
import "monaco-editor/languages/definitions/python/register.js";
import EditorWorker from "monaco-editor/editor/editor.worker.js?worker";
import { useEffect, useRef } from "react";
import { Loading } from "./ui";
self.MonacoEnvironment = { getWorker: () => new EditorWorker() };
loader.config({ monaco });
monaco.editor.defineTheme("trainer-dark", {
  base: "vs-dark",
  inherit: true,
  rules: [
    { token: "comment", foreground: "6D829D" },
    { token: "keyword", foreground: "B9A0FF" },
    { token: "string", foreground: "A6D8A0" },
    { token: "number", foreground: "EABD83" },
    { token: "identifier", foreground: "D8E4F5" },
  ],
  colors: {
    "editor.background": "#101A2B",
    "editor.foreground": "#D8E4F5",
    "editorLineNumber.foreground": "#50617B",
    "editorLineNumber.activeForeground": "#B3C6E1",
    "editor.lineHighlightBackground": "#152238",
    "editor.selectionBackground": "#29456F",
    "editorIndentGuide.background1": "#203049",
  },
});
export function CodeEditor({
  value,
  onChange,
  fontSize = 14,
  theme = "dark",
  readOnly = false,
  errorLine,
  jump,
  onMount,
  uncontrolled = false,
}: {
  value: string;
  onChange?: (v: string) => void;
  fontSize?: number;
  theme?: string;
  readOnly?: boolean;
  errorLine?: number;
  jump?: number;
  onMount?: OnMount;
  uncontrolled?: boolean;
}) {
  const ref = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  useEffect(() => {
    const model = ref.current?.getModel();
    if (model)
      monaco.editor.setModelMarkers(
        model,
        "python",
        errorLine
          ? [
              {
                startLineNumber: errorLine,
                endLineNumber: errorLine,
                startColumn: 1,
                endColumn: model.getLineMaxColumn(
                  Math.min(errorLine, model.getLineCount()),
                ),
                message: "Pythonのエラー行",
                severity: monaco.MarkerSeverity.Error,
              },
            ]
          : [],
      );
  }, [errorLine, value]);
  useEffect(() => {
    if (jump) {
      ref.current?.revealLineInCenter(jump);
      ref.current?.setPosition({ lineNumber: jump, column: 1 });
    }
  }, [jump]);
  return (
    <Editor
      height="100%"
      language="python"
      value={uncontrolled ? undefined : value}
      defaultValue={value}
      theme={
        theme === "light" ||
        (theme === "system" &&
          matchMedia("(prefers-color-scheme: light)").matches)
          ? "vs"
          : "trainer-dark"
      }
      loading={<Loading />}
      onChange={(v) => onChange?.(v ?? "")}
      onMount={(editor, api) => {
        ref.current = editor;
        onMount?.(editor, api);
      }}
      options={{
        fontSize,
        fontLigatures: false,
        fontFamily: '"Cascadia Code", "JetBrains Mono", Consolas, monospace',
        lineHeight: 25,
        minimap: { enabled: false },
        padding: { top: 22, bottom: 20 },
        scrollBeyondLastLine: false,
        readOnly,
        automaticLayout: true,
        tabSize: 4,
        insertSpaces: true,
        wordWrap: "on",
        quickSuggestions: false,
        suggestOnTriggerCharacters: false,
        wordBasedSuggestions: "off",
        parameterHints: { enabled: false },
        bracketPairColorization: { enabled: true },
        renderLineHighlight: uncontrolled ? "none" : "line",
        smoothScrolling: true,
        accessibilitySupport: "on",
        contextmenu: true,
      }}
    />
  );
}
