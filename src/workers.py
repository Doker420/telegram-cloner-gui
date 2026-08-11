import asyncio
from PyQt6.QtCore import QObject, QThread, pyqtSignal


class WorkerSignals(QObject):
    finished = pyqtSignal(str, object)
    error = pyqtSignal(str, str)
    event = pyqtSignal(str, dict)


class AsyncWorker(QThread):
    def __init__(self):
        super().__init__()
        self._queue: asyncio.Queue = None
        self._running = True
        self.signals = WorkerSignals()
        self.loop = None

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._dispatcher())

    async def _dispatcher(self):
        self._queue = asyncio.Queue()
        while self._running:
            try:
                token, coro = await asyncio.wait_for(self._queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            try:
                result = await coro
                self.signals.finished.emit(token, result)
            except Exception as e:
                self.signals.error.emit(token, str(e))
            finally:
                self._queue.task_done()

    def submit(self, token, coro):
        if self.loop and self.loop.is_running() and self._queue:
            asyncio.run_coroutine_threadsafe(self._queue.put((token, coro)), self.loop)

    def emit_event(self, event, payload):
        self.signals.event.emit(event, payload)

    def stop(self):
        self._running = False
        self.quit()
        self.wait()
