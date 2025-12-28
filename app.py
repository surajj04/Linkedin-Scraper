import sys
import json
import pandas as pd
from selenium import webdriver
import time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QTextEdit, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# ---------------- IMPORT YOUR SCRAPER ----------------
from main import start_scrap  # your selenium scraping function

LINKEDIN_URL = "https://www.linkedin.com/"

# ====================================================
# WORKER THREAD
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
            self.log_signal.emit(f"Scraping started: {self.profile_url}")
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
        self.is_logged_in = False

        self.scraped_data_list = []
        self.scraped_names = []

        self.init_ui()
        self.init_driver_and_login_check()

    # ------------------- UI -------------------
    def init_ui(self):
        main_layout = QHBoxLayout()

        # LEFT PANEL
        left = QVBoxLayout()

        title = QLabel("LinkedIn Profile Scraper")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px;font-weight:bold;")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste LinkedIn profile URL")

        self.start_btn = QPushButton("Start Scraping")
        self.start_btn.clicked.connect(self.start_scraping)
        self.start_btn.setEnabled(False)

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

        # RIGHT PANEL
        right = QVBoxLayout()
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setPlaceholderText("Scraped profile names will appear here")

        right.addWidget(QLabel("Scraped Profiles"))
        right.addWidget(self.result_box)

        main_layout.addLayout(left, 1)
        main_layout.addLayout(right, 2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    # ------------------- DRIVER + LOGIN CHECK -------------------
    def init_driver_and_login_check(self):
        self.log("Opening browser...")
        self.driver = webdriver.Chrome()
        self.driver.get(LINKEDIN_URL)

        reply = QMessageBox.question(
            self,
            "Login Required",
            "Have you manually logged in to LinkedIn in the browser?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.is_logged_in = True
            self.start_btn.setEnabled(True)
            self.log("Login confirmed. Ready to scrape.")
        else:
            QMessageBox.information(
                self,
                "Closing",
                "Please login first. Application will now close."
            )
            self.driver.quit()
            self.close()

    # ------------------- START SCRAPING -------------------
    def start_scraping(self):
        if not self.is_logged_in:
            QMessageBox.warning(self, "Login Required", "Please login first.")
            return

        profile_url = self.url_input.text().strip()
        if not profile_url:
            QMessageBox.warning(self, "Missing URL", "Please enter profile URL")
            return

        self.start_btn.setEnabled(False)
        self.url_input.clear()

        self.worker = ScraperWorker(self.driver, profile_url)
        self.worker.log_signal.connect(self.log)
        self.worker.result_signal.connect(self.handle_result)
        self.worker.finished_signal.connect(self.scraping_finished)
        self.worker.start()

    # ------------------- HANDLE RESULT -------------------
    def handle_result(self, result):
        self.scraped_data_list.append(result)

        name = result.get("basic_info", {}).get("name", "Unknown")
        self.scraped_names.append(name)
        self.result_box.setText("\n".join(self.scraped_names))

        self.download_json_btn.setEnabled(True)
        self.download_excel_btn.setEnabled(True)

    def scraping_finished(self):
        self.start_btn.setEnabled(True)
        self.log("Ready for next URL.")

    # ------------------- DOWNLOAD -------------------
    def download_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save JSON", "", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.scraped_data_list, f, indent=4)
            self.log(f"JSON saved: {path}")

    def download_excel(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Excel", "", "Excel (*.xlsx)")
        if path:
            df = pd.json_normalize(self.scraped_data_list)
            df.to_excel(path, index=False)
            self.log(f"Excel saved: {path}")

    # ------------------- LOG -------------------
    def log(self, msg):
        self.log_box.append(msg)

    # ------------------- CLOSE -------------------
    def closeEvent(self, event):
        if self.driver:
            self.driver.quit()
        event.accept()


# ====================================================
# APP ENTRY
# ====================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LinkedInScraperUI()
    window.show()
    sys.exit(app.exec())
