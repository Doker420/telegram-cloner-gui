from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QCheckBox, QLineEdit, QFormLayout, QDoubleSpinBox,
    QSpinBox, QProgressBar, QTextEdit, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt


class ClonePage(QWidget):
    def __init__(self, engine, worker, accounts_mgr, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.worker = worker
        self.accounts = accounts_mgr
        self._current_token = None
        self._selection = {}
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Аккаунт:"))
        self.account_combo = QComboBox()
        top.addWidget(self.account_combo, 1)
        layout.addLayout(top)

        info = QHBoxLayout()
        self.source_label = QLabel("Источник: не выбран")
        self.targets_label = QLabel("Цели: не выбраны")
        info.addWidget(self.source_label)
        info.addWidget(self.targets_label)
        info.addStretch()
        layout.addLayout(info)

        opts = QGroupBox("Параметры клонирования")
        form = QFormLayout(opts)
        self.clear_chk = QCheckBox("Очистить цель перед клонированием")
        self.clear_chk.setChecked(True)
        form.addRow(self.clear_chk)
        self.promo_chk = QCheckBox("Добавить промо-текст")
        self.promo_chk.setChecked(True)
        form.addRow(self.promo_chk)
        self.promo_edit = QLineEdit()
        form.addRow("Промо текст:", self.promo_edit)
        self.hashtags_edit = QLineEdit()
        form.addRow("Хэштеги:", self.hashtags_edit)
        self.delay_min = QDoubleSpinBox()
        self.delay_min.setRange(0, 60)
        self.delay_min.setValue(2)
        self.delay_max = QDoubleSpinBox()
        self.delay_max.setRange(0, 60)
        self.delay_max.setValue(8)
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(self.delay_min)
        delay_layout.addWidget(QLabel("—"))
        delay_layout.addWidget(self.delay_max)
        form.addRow("Задержка (сек):", delay_layout)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(0, 10000)
        self.limit_spin.setSpecialValueText("Без лимита")
        form.addRow("Лимит сообщений:", self.limit_spin)
        layout.addWidget(opts)

        btns = QHBoxLayout()
        self.start_btn = QPushButton("🚀 Запустить клонирование")
        self.start_btn.clicked.connect(self._start)
        self.stop_btn = QPushButton("⛔ Остановить")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop)
        btns.addWidget(self.start_btn)
        btns.addWidget(self.stop_btn)
        btns.addStretch()
        layout.addLayout(btns)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log, 1)

    def _connect_signals(self):
        self.worker.signals.finished.connect(self._on_finished)
        self.worker.signals.error.connect(self._on_error)
        self.worker.signals.event.connect(self._on_event)

    def refresh_accounts(self, accounts):
        self.account_combo.clear()
        for acc in accounts:
            self.account_combo.addItem(acc.get("name", acc.get("session", "")), acc.get("session", ""))

    def set_selection(self, sel):
        self._selection = sel
        if sel.get("source_title"):
            self.source_label.setText(f"Источник: {sel['source_title']}")
        else:
            self.source_label.setText("Источник: не выбран")
        if sel.get("target_titles"):
            self.targets_label.setText(f"Цели: {', '.join(sel['target_titles'][:3])}{'...' if len(sel['target_titles'])>3 else ''}")
        else:
            self.targets_label.setText("Цели: не выбраны")

    def _start(self):
        if not self._selection:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите чаты на вкладке «Чаты»")
            return
        session = self._selection.get("session")
        source_id = self._selection.get("source_id")
        target_ids = self._selection.get("target_ids", [])
        if not session or not source_id or not target_ids:
            QMessageBox.warning(self, "Ошибка", "Неполный выбор чатов")
            return

        proxy = ""
        for acc in self.accounts.all():
            if acc.get("session") == session:
                proxy = acc.get("proxy", "")
                break

        options = {
            "proxy": proxy,
            "clear_target": self.clear_chk.isChecked(),
            "add_promo": self.promo_chk.isChecked(),
            "bot_link": self.promo_edit.text().strip(),
            "hashtags": [h.strip() for h in self.hashtags_edit.text().split() if h.strip()],
            "delay_min": self.delay_min.value(),
            "delay_max": self.delay_max.value(),
            "limit": self.limit_spin.value(),
        }

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress.setValue(0)
        self.log.clear()
        self.log.append(f"🚀 Запуск клонирования... Источник: {source_id}, Целей: {len(target_ids)}")

        token = f"clone_{session}"
        self._current_token = token

        def event_cb(event, payload):
            self.worker.emit_event(f"{token}_{event}", payload)

        self.worker.submit(token, self.engine.start_clone(session, source_id, target_ids, options, event_cb=event_cb))

    def _stop(self):
        if self._current_token:
            session = self._current_token.replace("clone_", "", 1)
            self.engine.cancel(session)
            self.log.append("⛔ Остановка...")

    def _on_finished(self, token, result):
        if not token.startswith("clone_"):
            return
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        if isinstance(result, dict):
            ok = result.get("ok", False)
            total = result.get("total", 0)
            success = result.get("success", 0)
            failed = result.get("failed", 0)
            cancelled = result.get("cancelled", False)
            if cancelled:
                self.log.append("⚠️ Клонирование прервано")
            elif ok:
                self.log.append(f"✅ Готово! Всего: {total}, Успешно: {success}, Ошибок: {failed}")
            else:
                self.log.append("❌ Ошибка клонирования")
            if total:
                self.progress.setValue(100 if not cancelled else self.progress.value())
        else:
            self.log.append("✅ Завершено")
        self._current_token = None

    def _on_error(self, token, error):
        if not token.startswith("clone_"):
            return
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.log.append(f"❌ Ошибка: {error}")
        self._current_token = None

    def _on_event(self, token, payload):
        if not token.startswith("clone_"):
            return
        parts = token.split("_", 2)
        event = parts[2] if len(parts) >= 3 else token
        if event == "log":
            self.log.append(str(payload))
        elif event == "progress":
            done = payload.get("index", 0)
            total = payload.get("total", 1)
            self.progress.setRange(0, total)
            self.progress.setValue(done)
        elif event == "error":
            self.log.append(f"⚠️ {payload}")
