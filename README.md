# 🖨️ CampusPrinter

### Campus printing, without the queue.

**CampusPrinter** is a secure, centralized printing system designed for college campuses. It connects students to printers across different labs through a central backend and lightweight **Print Agents** running on lab computers.

Instead of manually transferring files to a lab computer, students can submit a document, select a printer, verify the print request using an OTP, and let the designated lab printer handle the rest.

> 🚧 **Current status:** `v0.1.0-beta.1` — First working beta prototype

---

## ✨ What is CampusPrinter?

CampusPrinter separates the **student-facing application** from the **physical printer infrastructure**.

```text
                 ┌─────────────────────┐
                 │       Student       │
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
              │        Lab Computer       │
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

The student selects an available printer from the CampusPrinter interface.

### 2. Submit the document

The PDF is submitted to the CampusPrinter backend along with the selected printer.

### 3. Verify the request

An OTP is used to authorize the print request.

### 4. Send to the Print Agent

The backend communicates with the Print Agent assigned to the selected printer.

### 5. Print

The Print Agent passes the document to the local Windows printing system through **SumatraPDF**.

### 6. Done.

The document is printed at the selected lab.

---

## 🧩 Architecture

CampusPrinter consists of three major components:

### 🌐 Central Backend

The main Flask application handles:

- Authentication
- User management
- Printer management
- Print jobs
- OTP verification
- Printer endpoint registration
- Communication with Print Agents

### 🖥️ Print Agent

A lightweight application running on each lab computer.

It handles:

- Receiving print jobs
- Communicating with the local printer
- Background task processing
- Printer-specific operations
- Cloudflare Tunnel connectivity

### 🗄️ Database

Stores application and printer metadata such as:

- Users
- Printers
- Printer endpoints
- Print jobs
- Availability state

---

## ⚙️ Tech Stack

| Component | Technology |
|---|---|
| Backend | Python / Flask |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Authentication | Clerk |
| Email / OTP | Resend |
| Background Tasks | Huey |
| Printing | SumatraPDF |
| Print Agent | Flask + Waitress |
| Connectivity | Cloudflare Tunnel |
| Hosting | Azure App Service |
| Frontend | HTML / CSS / JavaScript |

---

## 🖨️ Print Agent

Each printer can have a dedicated Print Agent running on a Windows lab computer.

The agent exposes a local service which is made reachable to the CampusPrinter backend through a Cloudflare Quick Tunnel.

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
        ▼
SumatraPDF
        │
        ▼
Windows Printer
```

The agent also runs a **Huey worker** for background printing tasks.

---

## 🔑 OTP Authorization

CampusPrinter uses OTP verification before a print job is authorized.

```text
Print Request
     │
     ▼
OTP Generated
     │
     ▼
OTP Sent
     │
     ▼
User Verification
     │
     ▼
Print Authorized
     │
     ▼
Printer Agent
```

This adds an additional authorization step between submitting a document and physically printing it.

---

## 📡 Printer Availability

Printer availability is designed to distinguish between:

**Automatic availability**

The system checks whether the Print Agent is reachable.

**Manual availability**

A lab in-charge can intentionally disable a printer.

The system uses an `ALLOWOVERWRITE` flag to distinguish these states.

```text
ALLOWOVERWRITE = TRUE
        │
        ▼
Automatic availability checks enabled


ALLOWOVERWRITE = FALSE
        │
        ▼
Manual offline state
        │
        ▼
Automatic checker does not override it
```

---

## 🔒 Privacy

Document privacy is one of the major design considerations of CampusPrinter.

The system is being designed to minimize the lifetime of submitted documents and avoid unnecessary persistent storage.

Planned privacy improvements include:

- Reduced document lifetime
- Temporary document handling
- OTP-controlled printing
- Automatic cleanup
- Protected communication between components
- Minimizing persistent copies of submitted documents

> Privacy and security mechanisms are still being actively developed in the beta stage.

---

## 🚀 Current Features

- [x] Centralized printer management
- [x] User authentication
- [x] Printer selection
- [x] PDF submission
- [x] OTP verification
- [x] Print Agent
- [x] Background print processing
- [x] Windows printer integration
- [x] Cloudflare Tunnel connectivity
- [x] Printer endpoint registration
- [x] Azure deployment
- [ ] Automated printer health monitoring
- [ ] Improved document privacy architecture
- [ ] Lab in-charge dashboard
- [ ] Advanced print controls
- [ ] Production security hardening

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
│   └── ...
│
├── .github/
│   └── workflows/
│
└── README.md
```

---

## 🧪 Beta Release

Current version:

```text
v0.1.0-beta.1
```

This release represents the first working beta prototype.

It is intended for:

- Testing
- Demonstrations
- Development
- Architecture validation

It is **not yet production-ready**.

---

## 🗺️ Roadmap

### Phase 1 — Prototype
- [x] Core backend
- [x] Database
- [x] Print Agent
- [x] OTP authorization
- [x] Remote agent connectivity

### Phase 2 — Reliability
- [ ] Printer health monitoring
- [ ] Automatic online/offline detection
- [ ] Better agent recovery
- [ ] Print job state tracking

### Phase 3 — Privacy & Security
- [ ] Temporary document handling
- [ ] Secure document transfer
- [ ] Improved authentication validation
- [ ] Security hardening

### Phase 4 — Campus Deployment
- [ ] Lab in-charge controls
- [ ] Printer administration
- [ ] Print history
- [ ] Usage statistics
- [ ] Multi-lab deployment

---

## 👨‍💻 Team

Built by **404Found**.

A student-led development group working on practical software, cybersecurity, and automation projects.

---

## 📜 License

License information will be added as the project approaches its first stable release.

---

<p align="center">
  <b>CampusPrinter</b><br>
  Print smarter. Print securely.
</p>
