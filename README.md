# Smart QR Code & Barcode Scanner System

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![OpenCV](https://img.shields.io/badge/OpenCV-Image%20Processing-green) ![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-darkblue) ![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)

## 📌 Project Overview
The **Smart QR Code & Barcode Scanner System** is an advanced, cross-platform desktop application designed for high-speed, reliable data extraction from barcodes and QR codes. 

Developed with Python, this system leverages Computer Vision (`OpenCV`), highly accurate decoding algorithms (`pyzbar`), and a modern GUI framework (`CustomTkinter`). It is built to handle real-world scanning scenarios, including low-light environments, and features an integrated SQLite database for secure scan history management.

This project is highly suitable for academic presentation, demonstrating practical applications of computer vision, database management, and UI/UX design.

---

## 🚀 Key Features

### 1. Intelligent Scanning & Processing
- **Real-Time Webcam Streaming:** High-framerate video processing for instant decoding.
- **Image Upload Support:** Scan static images (PNG, JPG, BMP) directly from the filesystem.
- **Low-Light Enhancement Algorithm:** Utilizes OpenCV contrast-stretching and histogram equalization to decode images in poor lighting conditions.
- **Smart Data Parsing:** Automatically categorizes scanned data into formats like URLs, WiFi Credentials, Emails, Phone Numbers, and Plain Text.

### 2. Smart Actions Engine
Based on the scanned data type, the application offers context-aware quick actions:
- 🌐 **URL:** Open links directly in the default web browser.
- 📶 **WiFi:** Auto-connect to WiFi networks (Linux `nmcli` integration).
- 📧 **Email:** Open the default mail client with pre-filled addresses.
- 📱 **Phone/Text:** One-click copy to the system clipboard.

### 3. Integrated QR Code Generator
- Generate custom QR codes from any text input.
- Real-time preview of the generated QR code.
- Save generated QR codes locally as high-quality PNG files.

### 4. Data Management & Reporting
- **Local Database:** All successful, unique scans are automatically saved to a local SQLite database (`scans.db`).
- **History Viewer:** A built-in data grid to view timestamps, scan types, and extracted data.
- **CSV Export:** Export the entire database to a CSV file for analytics or external record-keeping.

---

## 🛠 System Architecture & Tech Stack

- **Frontend UI:** `CustomTkinter` (Modern, Dark/Light mode capable GUI)
- **Computer Vision Pipeline:** `OpenCV` (`cv2`) and `Pillow` (PIL)
- **Decoding Engine:** `pyzbar`
- **Backend Storage:** `SQLite3`
- **Audio Feedback:** `pygame.mixer` (with `aplay` Linux fallback)

---

## ⚙️ Installation & Setup (Demo Guide)

### Prerequisites
The `pyzbar` library relies on the underlying C-library `zbar`.
- **Ubuntu/Debian:** `sudo apt-get install libzbar0`
- **Fedora/RHEL:** `sudo dnf install zbar`

### Environment Setup
1. **Clone/Navigate to the project directory.**
2. **Set up a Virtual Environment (Recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate.fish  # For Fish shell
   # OR: source venv/bin/activate # For Bash/Zsh
   ```
3. **Install Python Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application
```bash
python app.py
```

---

## 🎓 Demo Flow for Professor/Presentation

If you are demonstrating this project, follow this recommended flow:

1. **Introduction:** Briefly explain the tech stack (Python, OpenCV, SQLite).
2. **Live Scanning Demo:** 
   - Click **Start Webcam**.
   - Show a QR code to the camera. The system will "beep" and draw a bounding box.
3. **Smart Actions Demo:** 
   - Scan a URL QR code. Click the **Open URL in Browser** button that dynamically appears.
4. **Generator Demo:** 
   - Switch to the "Generator" tab. Type a message, generate the QR code, and save it.
5. **Database & Export Demo:** 
   - Open **View History** to show the SQLite data persistence.
   - Click **Export to CSV** to demonstrate report generation.
6. **Edge Case Handling (Low Light):** 
   - Turn on the "Low-Light Enhance" toggle and show how the system pre-processes the image frame to extract codes in dark conditions.
