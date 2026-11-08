/* global channel */
/* The iframe has an opaque origin and permits network access only to the Pyodide CDN. */
let worker, url, active;
const report = (data) => self.parent.postMessage({ ...data, channel }, "*");
addEventListener("message", ({ source, data }) => {
  if (source !== self.parent || data?.channel !== channel) return;
  if (data.command === "stop") {
    worker?.terminate();
    if (url) URL.revokeObjectURL(url);
    return;
  }
  if (data.command === "init" && !worker) {
    const start = performance.now();
    url = URL.createObjectURL(
      new Blob([data.bootstrap], { type: "application/javascript" }),
    );
    worker = new Worker(url);
    worker.onmessage = ({ data }) => report(data);
    worker.onerror = () =>
      report({
        id: active,
        phase: "error",
        message: "Python Workerの起動に失敗しました。",
      });
    report({ phase: "worker", elapsed_ms: performance.now() - start });
  }
  if (data.command === "run" || data.command === "prepare")
    active = data.payload.id;
  worker?.postMessage(data.payload);
});
report({ phase: "ready" });
