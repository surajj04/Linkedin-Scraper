import sys
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QTextEdit, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# ---------------- IMPORT YOUR SCRAPER ----------------
from main import start_scrap  # Your selenium scraping function

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
        self.profile_url = profile_url
        self.driver = driver

    def run(self):
        try:
            # Check if login is required
            current_url = self.driver.current_url
            if "login" in current_url or "checkpoint/challenge" in current_url:
                self.log_signal.emit("LinkedIn login required...")
                time.sleep(1)

            self.log_signal.emit(f"Starting scraping: {self.profile_url}")
            result = start_scrap(self.driver, self.profile_url)
            self.result_signal.emit(result)
            self.log_signal.emit(f"Scraping completed for: {self.profile_url}")

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
        self.scraped_data_list = []  # Store all scraped results
        self.scraped_names = []      # Store names to display in result box
        self.worker = None

        self.init_ui()
        self.init_driver()

    # ------------------- INIT UI -------------------
    def init_ui(self):
        main_layout = QHBoxLayout()

        # ===== LEFT PANEL =====
        left_layout = QVBoxLayout()

        title = QLabel("LinkedIn Profile Scraper")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px; font-weight:bold;")

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

        left_layout.addWidget(title)
        left_layout.addWidget(QLabel("Profile URL"))
        left_layout.addWidget(self.url_input)
        left_layout.addWidget(self.start_btn)
        left_layout.addWidget(QLabel("Logs"))
        left_layout.addWidget(self.log_box)
        left_layout.addWidget(self.download_json_btn)
        left_layout.addWidget(self.download_excel_btn)

        # ===== RIGHT PANEL =====
        right_layout = QVBoxLayout()

        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setPlaceholderText("Scraped profile names will appear here")

        right_layout.addWidget(QLabel("Scraped Profiles"))
        right_layout.addWidget(self.result_box)

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    # ------------------- INIT DRIVER -------------------
    def init_driver(self):
        self.log("Opening browser...")
        self.driver = webdriver.Chrome()
        self.driver.get(LINKEDIN_URL)
        self.log("Browser opened. Please login if required.")

    # ------------------- START SCRAPING -------------------
    def start_scraping(self):
        profile_url = self.url_input.text().strip()

        if not profile_url:
            QMessageBox.warning(self, "Missing URL", "Please enter profile URL")
            return

        # If login required, ask user
        current_url = self.driver.current_url
        if "login" in current_url or "checkpoint/challenge" in current_url:
            reply = QMessageBox.question(
                self,
                "Login Confirmation",
                "Have you completed LinkedIn login in the browser?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.start_btn.setEnabled(False)
        self.url_input.clear()
        self.log_box.append(f"Scraping URL: {profile_url}")

        # Start worker
        self.worker = ScraperWorker(self.driver, profile_url)
        self.worker.log_signal.connect(self.log)
        self.worker.result_signal.connect(self.handle_result)
        self.worker.finished_signal.connect(self.scraping_finished)
        self.worker.start()

    # ------------------- HANDLE SCRAPE RESULT -------------------
    def handle_result(self, result):
        self.scraped_data_list.append(result)

        # Display only profile name in result box
        name = result.get('basic_info', {}).get('name', 'Unknown')
        self.scraped_names.append(name)
        self.result_box.setText("\n".join(self.scraped_names))

        # Enable download buttons
        self.download_json_btn.setEnabled(True)
        self.download_excel_btn.setEnabled(True)

    def scraping_finished(self):
        self.start_btn.setEnabled(True)
        self.log("Ready for next URL.")

    # ------------------- LOG -------------------
    def log(self, message):
        self.log_box.append(message)

    # ------------------- DOWNLOAD JSON -------------------
    def download_json(self):
        if not self.scraped_data_list:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save JSON", "", "JSON Files (*.json)"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.scraped_data_list, f, indent=4)
            self.log(f"Saved JSON to {file_path}")

    # ------------------- DOWNLOAD EXCEL -------------------
    def download_excel(self):
        if not self.scraped_data_list:
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel", "", "Excel Files (*.xlsx)"
        )
        if file_path:
            df = pd.json_normalize(self.scraped_data_list)
            df.to_excel(file_path, index=False)
            self.log(f"Saved Excel to {file_path}")

    # ------------------- CLOSE EVENT -------------------
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
