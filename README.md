# 🎓 Analyst-Simulator-Atomic-Red-
**Student Cyber Range & Purple Team Simulator**

[![Release](https://img.shields.io/github/v/release/bharathkanne/Analyst-Simulator-Atomic-Red-?label=Latest%20Release)](https://github.com/bharathkanne/Analyst-Simulator-Atomic-Red-/releases/tag/v1.0.0)
[![Repository](https://img.shields.io/badge/GitHub-Repository-181717?logo=github)](https://github.com/bharathkanne/Analyst-Simulator-Atomic-Red-)
[![Python](https://img.shields.io/badge/Python-Latest-blue)](https://www.python.org/)

## 📖 Overview
**Atomic Enterprise** is an educational, GUI-driven Purple Team simulation platform designed specifically for students, educators, and aspiring security analysts. Textbooks teach theory, but this tool provides a safe, hands-on environment to observe real-world command-line mechanics of cyberattacks and learn how to validate endpoint defenses.

By decoupling a high DPI-aware user interface from a background PowerShell execution engine, the core script `Untitled-3.py` allows students to interactively explore the MITRE ATT&CK matrix, run controlled adversary simulations, and analyze generated telemetry.

---

## 🎯 Educational Learning Objectives

### 1. Master the MITRE ATT&CK Framework

### 2. Understand How Attackers Attack (Offensive Mechanics)

### 3. Learn How Defensive Test Tools Work (Purple Team Lifecycle)


---

## 🛠️ Built-In Technical Architecture
* **Python 3 Application Layer:** Asynchronous threading maps out UI interactions while preventing the interface from freezing during heavy subprocess runs.
* **Tkinter Presentation Layer:** A crisp, high-DPI aware dark-themed console layout that mimics standard security analyst tools.
* **PowerShell Orchestration:** Dispatches standard syntax to hidden windows, utilizing administrative API tokens to track endpoint integrity.
* **Windows API Integration (`ctypes`):** Programmatically validates the operator's privilege token context (checking for Administrator/High-Integrity rights).

---

## 🚀 Lab Setup & Getting Started

### Option 1: Standalone Download (For Quick Student Labs)
1. Go to the [Releases Page](https://github.com/bharathkanne/Analyst-Simulator-Atomic-Red-/releases/tag/v1.0.0) and download the compiled standalone `.exe`.
2. Move the executable to an isolated, dedicated testing directory.
3. **Crucial Lab Step:** Because this tool acts as an automation pipeline for offensive logic, Windows Defender will flag this tool. Students must configure a localized folder exclusion in their Antivirus settings before running it.
4. Right-click the `.exe` and select **Run as Administrator**.
5. Click **"Download Framework"** to dynamically fetch and provision the latest MITRE threat definitions directly to your local workspace.

### Option 2: Running the Source Code
If you want to read, modify, or extend the logic of the tool, you can run the raw Python code directly:
1. Clone this repository to your local directory:
   ```bash
   git clone https://github.com/bharathkanne/Analyst-Simulator-Atomic-Red-.git
   ```
2. Navigate to the folder and ensure Python 3.8+ is installed on your Windows machine.
3. Execute the core program script:
   ```bash
   python Untitled-3.py
   ```

---

## ⚠️ Security Authorization Notice

> **LEGAL DISCLAIMER & TERMS OF USE**
> 1. This application acts as an automation interface for security testing tools.
> 2. You are strictly prohibited from executing simulations on systems you do not own.
> 3. The developers assume absolutely no liability for system downtime or data loss.

### Requirements to Run:
* Latest Python (if running from source)
* Windows 10/11 Endpoint
* Active Internet Connection
* Administrator Privileges (Recommended)
* Antivirus/EDR Exclusions applied to this folder

---

**Project Lead:** KANNE BHARATH  
**Focus:** Purple Team Automation, Defensive Verification Engineering, and Cyber Range Infrastructure
