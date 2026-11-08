"""Modal is the only production provider. Expectations never enter the sandbox."""

from abc import ABC, abstractmethod
import json
import threading
import time
from .config import ROOT, settings


class ExecutionProvider(ABC):
    @abstractmethod
    def create_execution(self, payload, on_created): ...
    @abstractmethod
    def get_execution_status(self, id): ...
    @abstractmethod
    def get_execution_result(self, id): ...
    @abstractmethod
    def cancel_execution(self, id): ...
    @abstractmethod
    def terminate_execution(self, id): ...


class ModalProvider(ExecutionProvider):
    def __init__(self):
        import modal

        self.modal = modal
        self.client = (
            modal.Client.from_credentials(settings.modal_token_id, settings.modal_token_secret)
            if settings.modal_token_id and settings.modal_token_secret
            else None
        )
        self.app = modal.App.lookup("ml-code-trainer", create_if_missing=True, client=self.client)
        self.image = (
            modal.Image.debian_slim(python_version="3.12")
            .apt_install("util-linux", "passwd")
            .pip_install("numpy==2.4.2", "pandas==3.0.0", "scikit-learn==1.8.0")
            .pip_install("torch==2.10.0", index_url="https://download.pytorch.org/whl/cpu")
            .run_commands("useradd --uid 1000 --no-create-home learner")
            .add_local_file(str(ROOT / "content/runner.py"), "/opt/runner.py", copy=True)
        )
        self.results = {}

    def create_execution(self, payload, on_created):
        # No volumes, secret bindings, credential env, inbound ports, or GPU.
        sandbox = self.modal.Sandbox.create(
            "sleep",
            "35",
            app=self.app,
            image=self.image,
            cpu=1.0,
            memory=(2048, 2048),
            timeout=35,
            block_network=True,
            workdir="/tmp",
            env={"OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"},
            secrets=[],
            client=self.client,
        )
        id = sandbox.object_id
        on_created(id)
        try:
            process = sandbox.exec("runuser", "-u", "learner", "--", "python", "-I", "/opt/runner.py", timeout=30)
            process.stdin.write(json.dumps(payload))
            process.stdin.write_eof()
            process.stdin.drain()
            parts = []
            count = 0
            error = []
            overflow = threading.Event()

            def collect(stream, destination):
                nonlocal count
                for chunk in stream:
                    count += len(chunk.encode("utf-8"))
                    if count > 65536:
                        overflow.set()
                        sandbox.terminate()
                        return
                    destination.append(chunk)

            threads = [
                threading.Thread(target=collect, args=(process.stdout, parts), daemon=True),
                threading.Thread(target=collect, args=(process.stderr, error), daemon=True),
            ]
            for t in threads:
                t.start()
            started = time.monotonic()
            process.wait()
            for t in threads:
                t.join(timeout=2)
            if time.monotonic() - started >= 30:
                raise TimeoutError("Sandbox execution timed out")
            if overflow.is_set():
                raise RuntimeError("Output limit exceeded")
            if process.returncode != 0:
                raise RuntimeError("Sandbox process failed")
            self.results[id] = json.loads("".join(parts))
            return id
        finally:
            sandbox.terminate()

    def get_execution_status(self, id):
        if id in self.results:
            return "completed"
        sandbox = self.modal.Sandbox.from_id(id)
        return "running" if sandbox.poll() is None else "failed"

    def get_execution_result(self, id):
        return self.results.pop(id)

    def cancel_execution(self, id):
        self.modal.Sandbox.from_id(id).terminate()

    def terminate_execution(self, id):
        self.cancel_execution(id)
