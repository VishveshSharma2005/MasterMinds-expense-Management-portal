# 🚀 SplitSmart – AI-Inspired Expense Management & Settlement Platform

SplitSmart is a modern **expense management and settlement platform** designed to simplify group finances with **UPI-style payment simulation, intelligent debt minimization, and an immutable ledger for transaction security**.

The system helps users manage shared expenses, settle debts efficiently, and maintain **tamper-proof financial records**.

Built during a hackathon to demonstrate how **FinTech, cybersecurity, and algorithmic optimization** can enhance everyday financial management.

---

# ✨ Key Highlights

* 🔗 **Immutable Ledger System** – Blockchain-inspired transaction log using SHA256 hashes
* 💸 **UPI-style Payment Simulation** – Simulated instant payments without external APIs
* 🧠 **Greedy Algorithm Debt Minimization** – Reduces the number of settlement transactions
* 👥 **Group Expense Management** – Create groups, add members, and split expenses
* 🔐 **Secure Transaction Records** – Ledger integrity ensures tamper-proof records
* 📱 **Mobile Optimized UI** – Fully responsive design for mobile and desktop
* 🔔 **Notification System** – Real-time UI notifications for settlements and updates
* 💰 **Hybrid Settlement Options** – Supports both **Cash settlements with approval** and **Online payments**

---

# 🧠 Problem Statement

Managing shared expenses in groups often becomes complicated due to:

* multiple transactions
* unclear debt tracking
* lack of transparent records
* inefficient settlement processes

SplitSmart solves this problem by introducing:

* **algorithmic debt optimization**
* **secure financial logging**
* **simple payment simulation**
* **clear financial visibility**

---

# 🏗️ System Architecture

Frontend

* HTML Templates
* CSS (Responsive UI)
* JavaScript (Dynamic interactions)

Backend

* FastAPI (Python)

Database

* SQLite

Security Layer

* SHA256 Ledger Hash Chain

---

# 📊 Core Features

## 1️⃣ Smart Group Expense Management

Users can create groups, add members, and track shared expenses easily.

Features include:

* add expenses
* split bills among members
* track balances within groups
* view group expense history

---

## 2️⃣ Greedy Debt Minimization Algorithm

SplitSmart reduces unnecessary transactions using a **Greedy algorithm**.

Example:

Before optimization:

User A → User B ₹200
User B → User C ₹150
User C → User A ₹300

After optimization:

User C → User B ₹50
User C → User A ₹150

This significantly reduces the number of settlements required.

---

## 3️⃣ UPI-Style Payment Simulation

SplitSmart simulates a **real-time UPI payment experience** without using external payment gateways.

Users can:

* select **Pay via UPI**
* confirm simulated payment
* instantly settle debts

This allows realistic FinTech demonstrations during hackathons without requiring real banking APIs.

---

## 4️⃣ Cash Settlement with Receiver Approval

For users who prefer offline transactions:

1. Debtor selects **Settle by Cash**
2. Receiver receives settlement request
3. Receiver approves the transaction
4. Ledger is updated automatically

This supports real-world scenarios where not everyone uses digital payments.

---

## 5️⃣ Immutable Ledger System

All settlements are recorded in a **tamper-proof ledger**.

Each transaction contains:

* transaction ID
* sender
* receiver
* amount
* timestamp
* previous hash
* current hash

Hash calculation:

SHA256(
transaction_id +
from_user +
to_user +
amount +
timestamp +
previous_hash
)

This creates a **chain of transactions similar to blockchain systems**, ensuring data integrity.

---

## 6️⃣ Ledger Verification

The platform verifies the integrity of transaction records by checking the hash chain.

If any transaction is modified, the ledger becomes invalid.

This ensures **secure financial record keeping**.

---

## 7️⃣ Notification System

Users receive notifications for:

* new expenses
* settlement requests
* payment confirmations
* ledger updates

This improves user awareness and collaboration in groups.

---

# 📂 Project Structure

```
MasterMinds-expense-Management-portal

├── static
│   ├── css
│   └── js
│
├── templates
│   ├── partials
│   ├── base.html
│   ├── dashboard.html
│   ├── friends.html
│   ├── groups.html
│   ├── group_detail.html
│   ├── create_group.html
│   ├── ledger.html
│   ├── login.html
│   ├── signup.html
│   └── profile.html
│
├── uploads
│   └── user profile pictures
│
├── app.py
├── expense_tracker.py
├── expense_tracker.db
│
├── LEDGER_DESIGN.md
├── LEDGER_FEATURE.md
├── LEDGER_TESTING.md
├── LEDGER_README.md
│
├── ALGORITHM.md
├── SETUP_GUIDE.md
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation & Setup

Clone the repository:

```
git clone https://github.com/VishveshSharma2005/MasterMinds-expense-Management-portal.git
```

Navigate to project directory:

```
cd MasterMinds-expense-Management-portal
```

Install dependencies:

```
pip install -r requirements.txt
```

Run the application:

```
python app.py
```

Open in browser:

```
http://localhost:8000
```

---

# 📱 Demo Flow

1️⃣ User Signup / Login
2️⃣ Create Group
3️⃣ Add Friends
4️⃣ Add Expense
5️⃣ Split Bill
6️⃣ Optimize Settlements
7️⃣ Pay via UPI Simulation or Cash
8️⃣ Transaction Recorded in Immutable Ledger

---

# 🔐 Security Features

* SHA256 ledger hashing
* immutable transaction records
* tamper detection through hash chain
* secure settlement approvals

---

# 🚀 Future Improvements

* Real UPI gateway integration
* AI based expense categorization
* OCR receipt scanning
* financial analytics dashboard
* real-time WebSocket notifications

---

# 👨‍💻 Contributors

**Rishi Rami** Full Stack Developer And
**Vishvesh Sharma**
AI/ML & Full Stack Developer

---

⭐ If you found this project useful, consider giving it a star!
