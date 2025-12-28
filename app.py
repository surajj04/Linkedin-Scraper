import sys
import json
import pandas as pd
from selenium import webdriver
import time
import os
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton,
    QTextEdit, QMessageBox
)
from database import (
    insert_li_person,
    upsert_li_person_master,
    prepare_profile_for_db
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QMutex
from PyQt6.QtGui import QFont

from scraper import start_scrap

LINKEDIN_URL = "https://www.linkedin.com/"

class ScraperWorker(QThread):
    log_signal = pyqtSignal(str)
    result_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal()

    def __init__(self, driver, profile_url, mutex):
        super().__init__()
        self.driver = driver
        self.profile_url = profile_url
        self.mutex = mutex

    def run(self):
        self.mutex.lock()
        try:
            self.log_signal.emit(f"Scraping started: {self.profile_url}")
            data = start_scrap(self.driver, self.profile_url)
            self.result_signal.emit(data)
            self.log_signal.emit("Scraping completed ✔")
        except Exception as e:
            self.log_signal.emit(f"Error: {e}")
        finally:
            self.mutex.unlock()
            self.finished_signal.emit()


class LinkedInScraperUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkedIn Profile Scraper")
        self.setMinimumSize(1200, 650)

        self.driver = None
        self.worker = None
        self.driver_mutex = QMutex()
        self.is_logged_in = False

        self.scraped_data_list = []
        self.scraped_names = []

        self.save_dir = self.create_save_dir()
        self.init_ui()

    # ---------------- SAVE DIRECTORY ----------------
    def create_save_dir(self):
        base = Path.home() / "Desktop" / "LinkedIn Profile Scraper"
        for f in ["JSON Files", "Excel Files", "CSV Files", "Profiles"]:
            (base / f).mkdir(parents=True, exist_ok=True)
        return base

    # ---------------- UI ----------------
    def init_ui(self):
        main = QHBoxLayout()
        left = QVBoxLayout()
        right = QVBoxLayout()

        title = QLabel("LinkedIn Profile Scraper")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:18px;font-weight:bold;")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste LinkedIn profile URL")

        self.start_btn = QPushButton("Start Scraping")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_scraping)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        # Download buttons
        self.download_json = QPushButton("Download JSON")
        self.download_excel = QPushButton("Download Excel")
        self.download_csv = QPushButton("Download CSV")

        for btn in (self.download_json, self.download_excel, self.download_csv):
            btn.setEnabled(False)

        self.download_json.clicked.connect(self.save_json)
        self.download_excel.clicked.connect(self.save_excel)
        self.download_csv.clicked.connect(self.save_csv)

        left.addWidget(title)
        left.addWidget(QLabel("Profile URL"))
        left.addWidget(self.url_input)
        left.addWidget(self.start_btn)
        left.addWidget(QLabel("Logs"))
        left.addWidget(self.log_box)
        left.addWidget(self.download_json)
        left.addWidget(self.download_excel)
        left.addWidget(self.download_csv)

        # RIGHT PANEL
        self.result_box = QTextEdit()
        self.result_box.setReadOnly(True)
        self.result_box.setPlaceholderText("Scraped profile names will appear here")

        # 🔹 SAVE PATH LABEL
        self.path_label = QLabel(
            f"Files are automatically saved to:\n{self.save_dir}"
        )
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet(
            "font-size:10px;color:#555;padding:8px;"
            "background:#f2f2f2;border:1px solid #ddd;border-radius:5px;"
        )

        # 🔹 OPEN SAVE FOLDER BUTTON
        self.open_folder_btn = QPushButton("📂 Open Save Folder")
        self.open_folder_btn.clicked.connect(self.open_save_folder)

        right.addWidget(QLabel("Scraped Profiles"))
        right.addWidget(self.result_box)
        right.addWidget(self.path_label)
        right.addWidget(self.open_folder_btn)

        main.addLayout(left, 1)
        main.addLayout(right, 2)

        container = QWidget()
        container.setLayout(main)
        self.setCentralWidget(container)

    # ---------------- STARTUP ----------------
    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(500, self.init_driver)

    def init_driver(self):
        self.log("Initializing browser...")
        self.driver = webdriver.Chrome()
        self.driver.get(LINKEDIN_URL)

        reply = QMessageBox.question(
            self,
            "Login Required",
            "Please login to LinkedIn in the browser.\nClick YES after login.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.is_logged_in = True
            self.start_btn.setEnabled(True)
            self.log("Login confirmed ✔")
        else:
            self.close()

    # ---------------- SCRAPING ----------------
    def start_scraping(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Enter profile URL")
            return

        self.start_btn.setEnabled(False)
        self.url_input.clear()

        self.worker = ScraperWorker(self.driver, url, self.driver_mutex)
        self.worker.log_signal.connect(self.log)
        self.worker.result_signal.connect(self.handle_result)
        self.worker.finished_signal.connect(self.scraping_done)
        self.worker.start()
        
    def generate_task_id(self,prefix="LI_PERSON"):
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d%H%M%S")
        milliseconds = f"{now.microsecond // 1000:03d}"
        return f"{prefix}_{timestamp}{milliseconds}"

    def handle_result(self, data):
        try:
            profile = prepare_profile_for_db(data)

            task_id = self.generate_task_id()
            
            insert_li_person(profile,task_id)
            upsert_li_person_master(profile,task_id)

            self.scraped_data_list.append(data)
            name = data.get("basic_info", {}).get("name", "Unknown")
            self.scraped_names.append(name)
            self.result_box.setText("\n".join(self.scraped_names))

            self.download_json.setEnabled(True)
            self.download_excel.setEnabled(True)
            self.download_csv.setEnabled(True)

            self.log("Saved to database ✔")

        except Exception as e:
            self.log(f"Database error ❌ {e}")

    def scraping_done(self):
        self.worker.quit()
        self.worker.wait()
        self.worker = None
        self.start_btn.setEnabled(True)
        self.log("Ready for next profile")

    # ---------------- SAVE FILES ----------------
    def save_json(self):
        path = self.save_dir / "JSON Files" / f"profiles_{int(time.time())}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.scraped_data_list, f, indent=4, ensure_ascii=False)
        self.log(f"Saved JSON → {path.name}")

    def save_excel(self):
        path = self.save_dir / "Excel Files" / f"profiles_{int(time.time())}.xlsx"
        
        rows = []
        
        for profile  in self.scraped_data_list:
            basic = profile .get('basic_info',{})
            experience_list = profile.get('experience',{})
            skills = profile.get("skills", [])
            
            first_exp = experience_list[0] if experience_list else {}

            rows.append({
                "Name":basic.get("name",""),
                "Headline":basic.get("headline",""),
                "Location":basic.get("location",""),
                "Connections":basic.get("connections",""),
                "Last Activity":basic.get("last_activity",""),
                "Job Title":first_exp.get("job_title",""),
                "Profile URL":basic.get("profile_url",""),
                "Job Title":basic.get("job_title",""),
                "Company Name": first_exp.get("company_name", ""),
                "Company Link": first_exp.get("company_link", ""),
                "Company Location": first_exp.get("location", ""),
                "Work Mode": first_exp.get("work_mode", ""),
                "Total Duration": first_exp.get("total_duration", first_exp.get("duration", ""),),
                "Job Type": first_exp.get("job_type", ""),
                "Duration": first_exp.get("duration", ""),
                "Tenurity": first_exp.get("tenurity", ""),
                "Skills": ", ".join(skills),
                "Experience": json.dumps(experience_list, ensure_ascii=False)
                
            })
        df = pd.DataFrame(rows)
        df.to_excel(path, index=False)
        self.log(f"Saved Excel → {path.name}")

    def save_csv(self):
        path = self.save_dir / "CSV Files" / f"profiles_{int(time.time())}.csv"
        rows = []
        
        for profile  in self.scraped_data_list:
            basic = profile .get('basic_info',{})
            experience_list = profile.get('experience',{})
            skills = profile.get("skills", [])
            
            first_exp = experience_list[0] if experience_list else {}

            rows.append({
                "Name":basic.get("name",""),
                "Headline":basic.get("headline",""),
                "Location":basic.get("location",""),
                "Connections":basic.get("connections",""),
                "Last Activity":basic.get("last_activity",""),
                "Job Title":first_exp.get("job_title",""),
                "Company Name": first_exp.get("company_name", ""),
                "Company Link": first_exp.get("company_link", ""),
                "Company Location": first_exp.get("location", ""),
                "Work Mode": first_exp.get("work_mode", ""),
                "Total Duration": first_exp.get("total_duration", first_exp.get("duration", ""),),
                "Job Type": first_exp.get("job_type", ""),
                "Duration": first_exp.get("duration", ""),
                "Tenurity": first_exp.get("tenurity", ""),
                "Skills": ", ".join(skills),
                "Experience": json.dumps(experience_list, ensure_ascii=False)
                
            })
        df = pd.DataFrame(rows)
        df.to_csv(path, index=False)
        self.log(f"Saved CSV → {path.name}")

    # ---------------- OPEN FOLDER ----------------
    def open_save_folder(self):
        if sys.platform == "win32":
            os.startfile(self.save_dir)
        elif sys.platform == "darwin":
            os.system(f'open "{self.save_dir}"')
        else:
            os.system(f'xdg-open "{self.save_dir}"')

    # ---------------- LOG ----------------
    def log(self, msg):
        self.log_box.append(f"[{time.strftime('%H:%M:%S')}] {msg}")

    # ---------------- CLOSE ----------------
    def closeEvent(self, event):
        if self.driver:
            self.driver.quit()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 10))
    window = LinkedInScraperUI()
    window.show()
    sys.exit(app.exec())
