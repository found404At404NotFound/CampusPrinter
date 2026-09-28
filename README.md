# 🖨️ CampusPrinter
 
### Campus printing, without the queue.

**CampusPrinter** is a secure, centralized printing system designed for college campuses. It connects faculty members to printers across different labs through a central backend and lightweight **Print Agents** running on lab computers.

Instead of manually transferring files to a lab computer, faculty can submit a document, select a printer, verify the print request using an OTP, and have the designated lab printer handle the rest.

> 🚀 **Current status:** `v1.0.0` — First Stable Release
> 🧪 **Current access:** Faculty Testing Only

---

## ✨ What is CampusPrinter?

CampusPrinter separates the **user-facing application** from the **physical printer infrastructure**.

```text
                 ┌─────────────────────┐
                 │       Faculty       │
                 │   Web Application   │
                 └──────────┬──────────┘
                            │
                         HTTPS
                            │
                            ▼
                 ┌─────────────────────┐
                 │   CampusPrinter     │
                 │   Central Backend   │
                 └──────────┬──────────┘
                            │
                    Printer Selection
                            │
                            ▼
              ┌───────────────────────────┐
              │       Print Agent         │
              │      Lab Computer         │
              └────────────┬──────────────┘
                           │
                     Local Printing
                           │
                           ▼
                  ┌─────────────────┐
                  │     Printer     │
                  └─────────────────┘
```

---

## 🔐 How it works

### 1. Select a printer

The faculty member selects an available printer from the CampusPrinter interface.

### 2. Submit the document

The document is submitted to the CampusPrinter backend along with the selected printer and required print options.

### 3. Secure document transfer

The submitted document is compressed and securely encrypted before being transferred to the selected Print Agent.

### 4. Verify the request

An OTP is sent to the faculty member's registered email.

The OTP is entered at the lab printer interface when the faculty member reaches the lab and is ready to release the print job.

### 5. Send to the Print Agent

The backend communicates with the Print Agent assigned to the selected printer.

### 6. Print

The Print Agent processes the encrypted document, recovers the original document, and sends it to the local Windows printing system through **SumatraPDF**.

### 7. Done.

The document is printed at the selected lab.

---

## 🧩 Architecture

CampusPrinter consists of three major components:

### 🌐 Central Backend

The main Flask application handles:

* Authentication
* User sessions
* Printer management
* Print jobs
* OTP generation and verification
* Printer endpoint management
* Communication with Print Agents
* Secure document transfer
* Print job cancellation

### 🖥️ Print Agent

A lightweight Flask-based application running on each lab computer.

It handles:

* Receiving encrypted print jobs
* Secure document storage while pending
* Printer-specific operations
* Background print processing
* Local Windows printer communication
* Printer health endpoint
* Lab in-charge controls
* Cloudflare Tunnel connectivity

### 🗄️ Database

The PostgreSQL database stores application and printer metadata such as:

* Users
* Printers
* Printer endpoints
* Print jobs
* Uploaded file metadata
* Printer availability
* Printer status
* Last printer health check

---

## ⚙️ Tech Stack

| Component        | Technology              |
| ---------------- | ----------------------- |
| Backend          | Python / Flask          |
| Database         | PostgreSQL              |
| ORM              | SQLAlchemy              |
| Authentication   | Clerk                   |
| Email / OTP      | Resend                  |
| Background Tasks | Huey                    |
| Printing         | SumatraPDF              |
| Print Agent      | Python / Flask          |
| Connectivity     | Cloudflare Tunnel       |
| Hosting          | Azure App Service       |
| Frontend         | HTML / CSS / JavaScript |

---

## 🖨️ Print Agent

Each connected printer is managed by a dedicated **Print Agent** running on its associated Windows lab computer.

The agent is exposed to the CampusPrinter backend through a Cloudflare Tunnel.

```text
CampusPrinter Backend
        │
        │ HTTPS
        ▼
Cloudflare Tunnel
        │
        ▼
Print Agent
        │
        ├──────────► Health / Status
        │
        ▼
    Huey Worker
        │
        ▼
    SumatraPDF
        │
        ▼
Windows Printer
```

The Print Agent uses a unique **Printer ID** to ensure that print requests are delivered only to the intended printer.

---

## 🔑 OTP Authorization

CampusPrinter uses OTP verification before a print job can be released.

```text
Print Request
     │
     ▼
OTP Generated
     │
     ▼
OTP Sent to Email
     │
     ▼
Faculty Reaches Lab
     │
     ▼
OTP Entered
     │
     ▼
Print Authorized
     │
     ▼
Print Agent
     │
     ▼
Printer
```

### ⚠️ Important

The OTP should only be entered **after reaching the lab and being ready to release the print job**.

This provides an additional layer between submitting a document remotely and physically releasing it at the printer.

---

## 📡 Printer Availability & Health

CampusPrinter monitors the state of connected Print Agents and printers.

The Print Agent provides a `/health` endpoint that allows the backend to verify whether the agent is reachable.

```text
CampusPrinter Backend
        │
        │ GET /health
        ▼
Cloudflare Tunnel
        │
        ▼
Print Agent
        │
        ▼
HTTP Status
```

This allows the system to distinguish between an accessible and unreachable Print Agent.

The printer database also maintains information such as:

* Availability
* Status code
* Last ping
* Printer endpoint
* Manual override state

---

## 👨‍🏫 Lab Incharge Controls

CampusPrinter includes a dedicated Lab Incharge Dashboard for controlling printer access.

Lab in-charges can:

* Enable or disable printer availability
* Control print override settings
* Manage the printer assigned to their lab
* View the current printer control state

The dashboard communicates directly with the Print Agent, which updates the corresponding printer information in the central database.

---

## 🔒 Secure Document Handling

Document security is an important part of CampusPrinter.

The current system uses encrypted document transfer between the central backend and the Print Agent.

The general flow is:

```text
Original Document
       │
       ▼
Compression
       │
       ▼
Encryption
       │
       ▼
Encrypted .bin
       │
       ▼
Print Agent
       │
       ▼
Decryption
       │
       ▼
Original Document
       │
       ▼
Printing
```

The Print Agent stores the encrypted file while the print job is pending rather than keeping the original document directly.

---

## 🗑️ Print Job Cancellation

Pending print jobs can be cancelled before printing.

When a pending job is cancelled, CampusPrinter removes the associated pending file and database records from the Print Agent.

```text
Pending Print Job
       │
       ▼
Cancel Request
       │
       ▼
Remove Pending File
       │
       ▼
Remove Job Metadata
       │
       ▼
Job Cancelled
```

---

## 🚀 Current Features

* [x] Centralized printer management
* [x] Faculty authentication
* [x] Printer selection
* [x] Document submission
* [x] OTP-based print verification
* [x] Print Agent
* [x] Background print processing
* [x] Windows printer integration
* [x] Cloudflare Tunnel connectivity
* [x] Printer-specific routing
* [x] Printer endpoint registration
* [x] Printer health endpoint
* [x] Printer availability management
* [x] Lab in-charge dashboard
* [x] Print override controls
* [x] Encrypted document transfer
* [x] Pending print job cancellation
* [x] Azure deployment
* [x] Faculty testing environment

---

## 🧪 Current Testing Phase

CampusPrinter `v1.0.0` is currently undergoing controlled testing with **faculty members and lab in-charges**.

The purpose of the current testing phase is to validate:

* Print reliability
* Printer availability detection
* OTP verification
* Secure document transfer
* Print Agent stability
* Lab in-charge controls
* Overall usability

Student access and wider campus deployment will be introduced after the testing phase.

---

## 🛠️ Project Structure

```text
CampusPrinter/
│
├── app.py
├── models.py
├── helpers.py
├── tasks.py
├── requirements.txt
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── print.html
│   ├── credits.html
│   └── ...
│
├── .github/
│   └── workflows/
│
└── README.md
```

The Print Agent is maintained separately and contains its own Flask application, database models, upload handling, administration endpoints, and background printing tasks.

---

## 🗺️ Roadmap

### Phase 1 — Stable Core

* [x] Central backend
* [x] PostgreSQL database
* [x] Print Agent
* [x] OTP authorization
* [x] Remote agent connectivity
* [x] Printer management
* [x] Secure document transfer
* [x] Faculty testing

### Phase 2 — Reliability

* [x] Print Agent health endpoint
* [x] Printer availability management
* [x] Automatic status handling
* [x] Lab in-charge controls
* [ ] Further print job state tracking
* [ ] Improved agent recovery

### Phase 3 — Security & Privacy

* [x] Encrypted document transfer
* [x] OTP-controlled printing
* [x] Protected authenticated sessions
* [ ] Further authentication hardening
* [ ] Additional document lifecycle improvements
* [ ] Production security audit

### Phase 4 — Campus Deployment

* [ ] Student access
* [ ] Wider lab deployment
* [ ] Additional printer installations
* [ ] Print history
* [ ] Usage statistics
* [ ] Expanded administration

### Phase 5 — Mobile

* [ ] React Native application
* [ ] Android APK
* [ ] Mobile document selection
* [ ] Mobile print job management

---

## 👨‍💻 Team

Built by **404Found**.

A student-led development group working on practical software, cybersecurity, automation, and real-world campus solutions.

---

## 📜 License

License information will be added as the project approaches wider public deployment.

---

<p align="center">
  <b>CampusPrinter v1.0.0</b><br>
  Print smarter. Print securely.
</p>
