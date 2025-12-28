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
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

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
        # Don't initialize driver yet

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
        self.log_box.setPlaceholderText("Logs will appear here...")

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

    def showEvent(self, event):
        """Called when the window is shown"""
        super().showEvent(event)
        # Use a single-shot timer to delay driver initialization
        QTimer.singleShot(500, self.init_driver_and_login_check)

    # ------------------- DRIVER + LOGIN CHECK -------------------
    def init_driver_and_login_check(self):
        """Initialize the browser driver and check login status"""
        # Update UI first
        self.log("Initializing browser...")
        self.log("Please wait while the browser opens...")
        
        # Force UI update
        QApplication.processEvents()
        
        # Now initialize the driver
        try:
            self.driver = webdriver.Chrome()
            self.driver.get(LINKEDIN_URL)
            self.log("Browser opened successfully!")
            self.log("Please login to LinkedIn in the browser window...")
            
            # Small delay to ensure browser is visible
            time.sleep(1)
            
            # Now ask about login
            reply = QMessageBox.question(
                self,
                "Login Required",
                "A browser window has opened with LinkedIn.\n\n"
                "1. Please login to LinkedIn in that browser\n"
                "2. Then come back here and click 'Yes'\n\n"
                "Click 'Yes' after you have logged in.\n"
                "Click 'No' to cancel and close the app.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.is_logged_in = True
                self.start_btn.setEnabled(True)
                self.log("✓ Login confirmed")
                self.log("✓ Ready to scrape profiles")
                self.log("→ Paste a LinkedIn profile URL above and click 'Start Scraping'")
            else:
                self.log("Login cancelled by user")
                QMessageBox.information(
                    self,
                    "Closing",
                    "Application will now close."
                )
                if self.driver:
                    self.driver.quit()
                self.close()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Browser Error",
                f"Failed to open browser: {str(e)}\n\n"
                "Make sure you have:\n"
                "1. Chrome browser installed\n"
                "2. ChromeDriver downloaded and in PATH\n"
                "3. No other Chrome instances running"
            )
            self.log(f"✗ Error opening browser: {str(e)}")
            self.log("Please check ChromeDriver installation and try again")

    # ------------------- START SCRAPING -------------------
    def start_scraping(self):
        if not self.is_logged_in:
            QMessageBox.warning(self, "Login Required", "Please login first.")
            return

        profile_url = self.url_input.text().strip()
        if not profile_url:
            QMessageBox.warning(self, "Missing URL", "Please enter profile URL")
            return

        if "linkedin.com/in/" not in profile_url:
            reply = QMessageBox.question(
                self,
                "URL Warning",
                "This doesn't look like a LinkedIn profile URL.\n"
                "LinkedIn profiles usually contain 'linkedin.com/in/'.\n"
                "Do you want to continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
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
        self.log("✓ Ready for next URL")

    # ------------------- DOWNLOAD -------------------
    def download_json(self):
        if not self.scraped_data_list:
            QMessageBox.warning(self, "No Data", "No scraped data to save.")
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save JSON", 
            f"linkedin_data_{time.strftime('%Y%m%d_%H%M%S')}.json", 
            "JSON (*.json)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.scraped_data_list, f, indent=4, ensure_ascii=False)
                self.log(f"✓ JSON saved: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save JSON: {str(e)}")
                self.log(f"✗ Error saving JSON: {str(e)}")

    def download_excel(self):
        if not self.scraped_data_list:
            QMessageBox.warning(self, "No Data", "No scraped data to save.")
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Excel", 
            f"linkedin_data_{time.strftime('%Y%m%d_%H%M%S')}.xlsx", 
            "Excel (*.xlsx)"
        )
        if path:
            try:
                df = pd.json_normalize(self.scraped_data_list)
                df.to_excel(path, index=False)
                self.log(f"✓ Excel saved: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save Excel: {str(e)}")
                self.log(f"✗ Error saving Excel: {str(e)}")

    # ------------------- LOG -------------------
    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.append(f"[{timestamp}] {msg}")
        # Auto-scroll to bottom
        scrollbar = self.log_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        # Force UI update
        QApplication.processEvents()

    # ------------------- CLOSE -------------------
    def closeEvent(self, event):
        # Ask for confirmation before closing
        if self.driver and self.is_logged_in:
            reply = QMessageBox.question(
                self,
                "Confirm Exit",
                "Are you sure you want to exit?\nThe browser will be closed.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        if self.driver:
            try:
                self.log("Closing browser...")
                self.driver.quit()
            except:
                pass
        event.accept()


# ====================================================
# APP ENTRY
# ====================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont("Arial", 10)
    app.setFont(font)
    
    # Create and show window
    window = LinkedInScraperUI()
    window.show()
    
    # Start the application
    sys.exit(app.exec())