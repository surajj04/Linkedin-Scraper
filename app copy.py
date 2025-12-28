import sys
import json
import time
import pandas as pd
from selenium import webdriver

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QTextEdit, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from main import start_scrap

LINKEDIN_URL = "https://www.linkedin.com/"


# ====================================================
# WORKER THREAD (USES EXISTING DRIVER)
# ====================================================
class ScraperWorker(QThread):
    log_signal = pyqtSignal(str)
    result_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    def __init__(self, driver, profile_url):
        super().__init__()
        self.driver = driver
        self.profile_url = profile_url

    def run(self):
        try:
            self.log_signal.emit("Opening profile URL...")
            self.driver.get(self.profile_url)

            self.log_signal.emit("Scraping started...")
            result = start_scrap(self.driver, self.profile_url)

            self.result_signal.emit(result)
            self.log_signal.emit("Scraping completed ✔")

        except Exception as e:
            self.log_signal.emit(f"Error: {str(e)}")

        finally:
            self.finished_signal.emit()


# ====================================================
# MAIN UI
# ====================================================
class LinkedInScraperUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkedIn Scraper")
        self.setMinimumSize(1200, 650)

        self.driver = None
        self.worker = None
        self.scraped_data = None

        self.init_ui()
        self.init_driver()

    # -------------------------------------------------
    def init_driver(self):
        self.log("Launching browser...")
        self.driver = webdriver.Chrome()
        self.driver.get(LINKEDIN_URL)

    # -------------------------------------------------
    def init_ui(self):
        main_layout = QHBoxLayout()

        # ============== LEFT PANEL =================
        left = QVBoxLayout()

        title = QLabel("LinkedIn Profile Scraper")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px;font-weight:bold;")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste LinkedIn profile URL")

        self.start_btn = QPushButton("Start Scraping")
        self.start_btn.clicked.connect(self.start_scraping)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.download_json_btn = QPushButton("Download JSON")
        self.download_json_btn.clicked.connect(self.download_json)
        self.download_json_btn.setEnabled(False)

        self.download_excel_btn = QPushButton("Download Excel")
        self.download_excel_btn.clicked.connect(self.download_excel)
        self.download_excel_btn.setEnabled(False)

        left.addWidget(title)
        left.addWidget(QLabel("Profile URL"))
        left.addWidget(self.url_input)
        left.addWidget(self.start_btn)
        left.addWidget(QLabel("Logs"))
        left.addWidget(self.log_box)
        left.addWidget(self.download_json_btn)
        left.addWidget(self.download_excel_btn)

        # ============== RIGHT PANEL =================
        right = QVBoxLayout()

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)

        right.addWidget(QLabel("Scraped Result"))
        right.addWidget(self.result_box)

        main_layout.addLayout(left, 1)
        main_layout.addLayout(right, 2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    # -------------------------------------------------
    def start_scraping(self):
        profile_url = self.url_input.text().strip()
        if not profile_url:
            QMessageBox.warning(self, "Missing URL", "Enter profile URL")
            return

        time.sleep(1)
        current_url = self.driver.current_url

        if "login" in current_url or "checkpoint" in current_url:
            reply = QMessageBox.question(
                self,
                "Login Required",
                "Please login in the opened browser.\n\nHave you completed login?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.start_btn.setEnabled(False)
        self.log_box.clear()
        self.result_box.clear()

        self.worker = ScraperWorker(self.driver, profile_url)
        self.worker.log_signal.connect(self.log)
        self.worker.result_signal.connect(self.show_result)
        self.worker.finished_signal.connect(self.scraping_finished)
        self.worker.start()

    # -------------------------------------------------
    def show_result(self, result):
        self.scraped_data = result
        self.result_box.setText(json.dumps(result, indent=4))
        self.download_json_btn.setEnabled(True)
        self.download_excel_btn.setEnabled(True)

    def scraping_finished(self):
        self.start_btn.setEnabled(True)

    def log(self, msg):
        self.log_box.append(msg)

    # -------------------------------------------------
    def download_json(self):
        if not self.scraped_data:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save JSON", "", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.scraped_data, f, indent=4)

    def download_excel(self):
        if not self.scraped_data:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Excel", "", "Excel (*.xlsx)")
        if path:
            df = pd.json_normalize(self.scraped_data)
            df.to_excel(path, index=False)

    # -------------------------------------------------
    def closeEvent(self, event):
        if self.driver:
            self.driver.quit()
        event.accept()


# ====================================================
# ENTRY POINT
# ====================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LinkedInScraperUI()
    window.show()
    sys.exit(app.exec())
