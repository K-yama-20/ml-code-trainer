/* Runs only in an opaque-origin sandboxed iframe. Never receives auth or secrets. */
let py, globals;
const loaded = new Set();
const imports = {
  numpy: "import numpy",
  pandas: "import pandas",
  "scikit-learn":
    "from sklearn import model_selection, preprocessing, pipeline, linear_model, metrics",
};
self.onmessage = async ({ data }) => {
  const {
    action,
    id,
    code,
    cases,
    packages,
    indexURL,
    harness,
    required,
    execution,
  } = data;
  try {
    if (action === "init") {
      const start = performance.now();
      importScripts(`${indexURL}pyodide.js`);
      py = await self.loadPyodide({ indexURL });
      const init = performance.now();
      globals = py.toPy({});
      await py.runPythonAsync(
        harness.replace(/if __name__ == ['"]__main__['"]:[\s\S]*$/, ""),
        { globals },
      );
      self.postMessage({
        phase: "initialized",
        timings: {
          pyodide_ms: init - start,
          harness_ms: performance.now() - init,
        },
      });
      return;
    }

    const missing = packages.filter((name) => !loaded.has(name));
    const loadStarted = performance.now();
    if (missing.length) {
      self.postMessage({
        id,
        phase: "packages",
        message: `${missing.join(" / ")}を読み込んでいます…`,
      });
      await py.loadPackage(missing);
      await py.runPythonAsync(
        missing.map((name) => imports[name] ?? "").join("\n"),
        { globals },
      );
      for (const name of missing) loaded.add(name);
    }
    const packages_ms = missing.length ? performance.now() - loadStarted : 0;
    if (action === "prepare") {
      self.postMessage({
        id,
        phase: "prepared",
        timings: { packages_ms, packages_loaded: missing },
      });
      return;
    }
    globals.set(
      "_payload",
      JSON.stringify({
        code,
        execution: execution || {},
        cases: cases.map(({ setup, args }) => ({ setup, args })),
      }),
    );
    globals.set("_required", required ?? "");
    self.postMessage({ id, phase: "running" });
    const start = performance.now();
    const result = await py.runPythonAsync(
      "run_browser_payload(_payload, _required)",
      { globals },
    );
    const { retire, timings, ...verdict } = JSON.parse(result);
    self.postMessage({
      id,
      phase: "complete",
      result: verdict,
      retire,
      timings: { ...timings, packages_ms, packages_loaded: missing },
      elapsed_ms: performance.now() - start,
    });
  } catch (err) {
    self.postMessage({
      id,
      phase: "error",
      message: String(err).slice(0, 3000),
    });
  }
};
