"""
MainWindow: the full Purple Download Manager UI.
"""
from __future__ import annotations
import os
import time
from PyQt5.QtCore import Qt, QVariantAnimation, QEasingCurve
from PyQt5.QtGui import QColor, QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QPlainTextEdit,
    QAbstractItemView, QSizePolicy, QCheckBox
)

from gui.theme import AnimatedBackground, GLOBAL_QSS, PURPLE_ACCENT, PURPLE_LIGHT, PINK_ACCENT, TEXT_LIGHT
from gui.widgets import GlowButton, AnimatedProgressBar
from core.downloader import DownloadWorker, human_size
from core.ytdlp_worker import YtDlpWorker
from core.utils import is_ytdlp_url


class DownloadRow:
    """Wraps all the widgets + worker for a single queued download."""

    def __init__(self, url: str, dest_dir: str, row_index: int, table: QTableWidget, audio_only: bool = False):
        self.url = url
        self.dest_dir = dest_dir
        self.row_index = row_index
        self.table = table
        self.worker = None  # DownloadWorker or YtDlpWorker
        self.status = "queued"
        self.is_ytdlp = is_ytdlp_url(url)
        self.audio_only = audio_only

        self.name_item = QTableWidgetItem(os.path.basename(url) or url)
        self.name_item.setToolTip(url)
        self.name_item.setFlags(self.name_item.flags() & ~Qt.ItemIsEditable)

        mode_text = "🎬 yt-dlp" if self.is_ytdlp else "📄 Direct"
        if self.is_ytdlp and self.audio_only:
            mode_text = "🎵 yt-dlp (MP3)"
        self.mode_item = QTableWidgetItem(mode_text)
        self.mode_item.setFlags(self.mode_item.flags() & ~Qt.ItemIsEditable)
        self.mode_item.setTextAlignment(Qt.AlignCenter)

        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setValue(0)

        self.status_item = QTableWidgetItem("Queued")
        self.status_item.setFlags(self.status_item.flags() & ~Qt.ItemIsEditable)
        self.status_item.setTextAlignment(Qt.AlignCenter)

        self.speed_item = QTableWidgetItem("--")
        self.speed_item.setFlags(self.speed_item.flags() & ~Qt.ItemIsEditable)
        self.speed_item.setTextAlignment(Qt.AlignCenter)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(2, 2, 2, 2)
        btn_layout.setSpacing(4)
        self.start_btn = GlowButton("▶", base_color=PURPLE_ACCENT)
        self.pause_btn = GlowButton("⏸", base_color="#5b3a8c")
        self.cancel_btn = GlowButton("✕", base_color="#7a2a4a")
        for b in (self.start_btn, self.pause_btn, self.cancel_btn):
            b.setFixedWidth(34)
            b.setMinimumHeight(28)
            btn_layout.addWidget(b)
        if self.is_ytdlp:
            # yt-dlp downloads can't be paused/resumed mid-stream
            self.pause_btn.setEnabled(False)
            self.pause_btn.setToolTip("Pause isn't supported for yt-dlp downloads")
        self.actions_widget = btn_row

    def set_status(self, text: str):
        self.status = text.lower()
        self.status_item.setText(text)


class MainWindow(QMainWindow):
    COLUMNS = ["File", "Mode", "Progress", "Speed", "Status", "Actions"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Purple Download Manager — All-in-One")
        self.resize(980, 620)
        self.setAcceptDrops(True)
        self.setStyleSheet(GLOBAL_QSS)

        self.rows: list[DownloadRow] = []
        self.dest_dir = os.path.join(os.path.expanduser("~"), "Downloads")

        self._build_ui()
        self._animate_title()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        background = AnimatedBackground(self)
        self.setCentralWidget(background)

        outer = QVBoxLayout(background)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        # ---- Header ----
        header = QVBoxLayout()
        self.title_label = QLabel("✨ Purple Download Manager")
        self.title_label.setObjectName("TitleLabel")
        subtitle = QLabel(
            "Direct file links download instantly · YouTube / TikTok / X / SoundCloud "
            "and more are handled automatically via yt-dlp."
        )
        subtitle.setObjectName("SubtitleLabel")
        subtitle.setWordWrap(True)
        header.addWidget(self.title_label)
        header.addWidget(subtitle)
        outer.addLayout(header)

        # ---- URL input row ----
        input_row = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "Paste a URL — a file link, or a YouTube/TikTok/X/SoundCloud/etc. link…"
        )
        self.url_input.returnPressed.connect(self.add_url_from_input)
        self.audio_only_checkbox = QCheckBox("🎵 Audio only (MP3)")
        self.audio_only_checkbox.setToolTip(
            "Applies to yt-dlp links (YouTube etc.) — extracts audio as MP3 instead of video.\n"
            "Requires ffmpeg to be installed and on PATH."
        )
        add_btn = GlowButton("＋ Add", base_color=PURPLE_ACCENT)
        add_btn.clicked.connect(self.add_url_from_input)
        browse_txt_btn = GlowButton("Import .txt", base_color="#5b3a8c")
        browse_txt_btn.clicked.connect(self.import_txt_file)
        input_row.addWidget(self.url_input, 4)
        input_row.addWidget(self.audio_only_checkbox, 0)
        input_row.addWidget(add_btn, 1)
        input_row.addWidget(browse_txt_btn, 1)
        outer.addLayout(input_row)

        # ---- Destination row ----
        dest_row = QHBoxLayout()
        self.dest_label = QLabel(f"📁 Save to: {self.dest_dir}")
        choose_dir_btn = GlowButton("Change folder", base_color="#5b3a8c")
        choose_dir_btn.clicked.connect(self.choose_folder)
        dest_row.addWidget(self.dest_label, 4)
        dest_row.addWidget(choose_dir_btn, 1)
        outer.addLayout(dest_row)

        # ---- Table ----
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)       # File
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Mode
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)       # Progress
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Speed
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Actions
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(260)
        outer.addWidget(self.table, 3)

        # ---- Global controls ----
        controls_row = QHBoxLayout()
        start_all_btn = GlowButton("▶ Start All", base_color=PURPLE_ACCENT)
        start_all_btn.clicked.connect(self.start_all)
        pause_all_btn = GlowButton("⏸ Pause All", base_color="#5b3a8c")
        pause_all_btn.clicked.connect(self.pause_all)
        clear_btn = GlowButton("🧹 Clear Completed", base_color="#7a2a4a")
        clear_btn.clicked.connect(self.clear_completed)
        controls_row.addWidget(start_all_btn)
        controls_row.addWidget(pause_all_btn)
        controls_row.addWidget(clear_btn)
        controls_row.addStretch(1)
        outer.addLayout(controls_row)

        # ---- Log console ----
        log_label = QLabel("Activity log")
        log_label.setObjectName("SubtitleLabel")
        outer.addWidget(log_label)
        self.log = QPlainTextEdit()
        self.log.setObjectName("LogConsole")
        self.log.setReadOnly(True)
        self.log.setFixedHeight(120)
        outer.addWidget(self.log)

        self._log("Ready. Add a URL above or drag & drop a .txt file of links.")

    def _animate_title(self):
        """Slowly cycle the title's text color through purple/pink shades."""
        self._title_anim = QVariantAnimation(self)
        self._title_anim.setStartValue(QColor(PURPLE_LIGHT))
        self._title_anim.setKeyValueAt(0.5, QColor(PINK_ACCENT))
        self._title_anim.setEndValue(QColor(PURPLE_LIGHT))
        self._title_anim.setDuration(3000)
        self._title_anim.setLoopCount(-1)
        self._title_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._title_anim.valueChanged.connect(
            lambda c: self.title_label.setStyleSheet(
                f"font-size: 26px; font-weight: 800; letter-spacing: 1px; color: {c.name()};"
            )
        )
        self._title_anim.start()

    # ------------------------------------------------------------------
    # Drag & drop
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for qurl in event.mimeData().urls():
                local_path = qurl.toLocalFile()
                if local_path and local_path.lower().endswith(".txt"):
                    self._add_urls_from_file(local_path)
                elif qurl.toString().startswith("http"):
                    self.add_url(qurl.toString())
        elif event.mimeData().hasText():
            for line in event.mimeData().text().splitlines():
                line = line.strip()
                if line.startswith("http"):
                    self.add_url(line)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder", self.dest_dir)
        if folder:
            self.dest_dir = folder
            self.dest_label.setText(f"📁 Save to: {self.dest_dir}")
            self._log(f"Destination folder set to {folder}")

    def add_url_from_input(self):
        url = self.url_input.text().strip()
        if url:
            self.add_url(url)
            self.url_input.clear()

    def import_txt_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import URL list", "", "Text files (*.txt)")
        if path:
            self._add_urls_from_file(path)

    def _add_urls_from_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                count = 0
                for line in f:
                    line = line.strip()
                    if line and line.startswith("http"):
                        self.add_url(line)
                        count += 1
            self._log(f"Imported {count} URL(s) from {os.path.basename(path)}")
        except OSError as e:
            self._log(f"⚠ Failed to read {path}: {e}")

    def add_url(self, url: str):
        row_index = self.table.rowCount()
        self.table.insertRow(row_index)

        audio_only = self.audio_only_checkbox.isChecked()
        row = DownloadRow(url, self.dest_dir, row_index, self.table, audio_only=audio_only)
        self.table.setItem(row_index, 0, row.name_item)
        self.table.setItem(row_index, 1, row.mode_item)
        self.table.setCellWidget(row_index, 2, row.progress_bar)
        self.table.setItem(row_index, 3, row.speed_item)
        self.table.setItem(row_index, 4, row.status_item)
        self.table.setCellWidget(row_index, 5, row.actions_widget)

        row.start_btn.clicked.connect(lambda: self.start_row(row))
        row.pause_btn.clicked.connect(lambda: self.toggle_pause_row(row))
        row.cancel_btn.clicked.connect(lambda: self.cancel_row(row))

        self.rows.append(row)
        tag = "yt-dlp" if row.is_ytdlp else "direct"
        self._log(f"Added ({tag}): {url}")

    def start_row(self, row: DownloadRow):
        if row.worker and row.worker.isRunning():
            return
        row.dest_dir = self.dest_dir

        if row.is_ytdlp:
            worker = YtDlpWorker(row.url, row.dest_dir, audio_only=row.audio_only)
        else:
            worker = DownloadWorker(row.url, row.dest_dir)
        row.worker = worker

        worker.filename_ready.connect(lambda name, r=row: r.name_item.setText(name))
        worker.progress.connect(lambda pct, speed, eta, r=row: self._on_progress(r, pct, speed, eta))
        worker.status_changed.connect(lambda status, r=row: self._on_status(r, status))
        worker.finished_ok.connect(lambda path, r=row: self._on_finished(r, path))
        worker.failed.connect(lambda err, r=row: self._on_failed(r, err))

        worker.start()
        row.set_status("Connecting…")
        engine = "yt-dlp" if row.is_ytdlp else "direct"
        self._log(f"Starting download ({engine}): {row.url}")

    def toggle_pause_row(self, row: DownloadRow):
        if row.is_ytdlp:
            return  # yt-dlp downloads don't support pause/resume
        if not row.worker or not row.worker.isRunning():
            return
        if row.status == "paused":
            row.worker.resume()
            row.progress_bar.set_active(True)
            self._log(f"Resumed: {row.name_item.text()}")
        else:
            row.worker.pause()
            row.progress_bar.set_active(False)
            self._log(f"Paused: {row.name_item.text()}")

    def cancel_row(self, row: DownloadRow):
        if row.worker and row.worker.isRunning():
            row.worker.cancel()
            self._log(f"Cancelling: {row.name_item.text()}")
        row.set_status("Cancelled")
        row.progress_bar.mark_error()

    def start_all(self):
        for row in self.rows:
            if row.status in ("queued", "cancelled", "error"):
                self.start_row(row)

    def pause_all(self):
        for row in self.rows:
            if row.worker and row.worker.isRunning() and row.status == "downloading":
                self.toggle_pause_row(row)

    def clear_completed(self):
        keep = []
        remove_indices = []
        for i, row in enumerate(self.rows):
            if row.status == "done":
                remove_indices.append(row.row_index)
            else:
                keep.append(row)
        for idx in sorted(remove_indices, reverse=True):
            self.table.removeRow(idx)
        # Reindex remaining rows
        self.rows = keep
        for new_index, row in enumerate(self.rows):
            row.row_index = new_index
        self._log("Cleared completed downloads.")

    # ------------------------------------------------------------------
    # Worker signal handlers
    # ------------------------------------------------------------------
    def _on_progress(self, row: DownloadRow, pct: int, speed: str, eta: str):
        row.progress_bar.animate_to(pct)
        row.speed_item.setText(speed if speed else "--")
        row.status_item.setText(f"Downloading · {eta}")

    def _on_status(self, row: DownloadRow, status: str):
        pretty = {
            "connecting": "Connecting…",
            "downloading": "Downloading…",
            "processing": "Processing…",
            "paused": "Paused",
            "cancelled": "Cancelled",
            "error": "Error",
            "done": "Done ✔",
        }.get(status, status)
        row.set_status(pretty)

    def _on_finished(self, row: DownloadRow, path: str):
        row.progress_bar.animate_to(100)
        row.progress_bar.mark_success()
        row.set_status("Done ✔")
        self._log(f"✅ Finished: {path}")

    def _on_failed(self, row: DownloadRow, err: str):
        row.progress_bar.mark_error()
        row.set_status("Error")
        self._log(f"❌ Error downloading {row.url}: {err}")

    # ------------------------------------------------------------------
    def _log(self, message: str):
        stamp = time.strftime("%H:%M:%S")
        self.log.appendPlainText(f"[{stamp}] {message}")

    def closeEvent(self, event):
        for row in self.rows:
            if row.worker and row.worker.isRunning():
                row.worker.cancel()
                row.worker.wait(500)
        super().closeEvent(event)
