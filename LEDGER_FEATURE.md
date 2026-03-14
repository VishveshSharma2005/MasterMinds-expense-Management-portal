# Ledger Feature Documentation

## Overview

The **Ledger tab** in the Group Detail page provides a comprehensive view of all transactions and balances within a group. It displays transaction history, settlement status, and individual member balances with color-coded visual indicators.

## Features

### 1. Summary Dashboard
Located at the top of the Ledger tab, showing 4 key metrics:

| Metric | Description | Color | Calculation |
|--------|-------------|-------|-------------|
| **Total Transactions** | Count of all settlement transactions | Blue | `COUNT(transactions)` |
| **Settled** | Number of completed transactions | Green | `COUNT(transactions WHERE status='COMPLETED')` |
| **Pending** | Number of pending/unsettled transactions | Orange | `Total - Settled` |
| **Total Volume** | Sum of all transaction amounts | Pink | `SUM(transaction.amount)` |

### 2. Transaction History Table

Displays all transactions in reverse chronological order with columns:

| Column | Content | Notes |
|--------|---------|-------|
| **From** | Payer name | Full name of the person paying |
| **To** | Payee name | Full name of the person receiving |
| **Amount** | Transaction amount | Formatted currency (₹X.XX) |
| **Date** | Transaction date | Derived from timestamp (YYYY-MM-DD) |
| **Status** | Settlement status | Badge with color: <span style="color: #4CAF50;">✓ Settled</span> or <span style="color: #FF9800;">⏳ Pending</span> |

**Features:**
- Sorted by date (newest first)
- Scrollable container (max 600px height)
- Color-coded status badges
- User names linked to full user profiles (future enhancement)

### 3. Current Balances Sheet

Card-based grid layout showing each member's balance status:

#### Color Coding System

```
Green (#4CAF50) = Creditor (someone owes them)
Red (#f44336) = Debtor (they owe someone)
Gray (#999) = Settled (balance is zero)
```

#### Card Contents

Each balance card displays:
- **Member Name** - Username or full name
- **Balance Status** - Formatted text indicating owed/owes amount
- **Role Badge** - "Creditor" or "Debtor" label
- **Left Border** - Colored stripe matching balance type

Example card:
```
┌─────────────────────────────┐
│ Alice                       │
│ Owed ₹1,500.00             │
│ Creditor                    │
└─────────────────────────────┘
```

## Backend API Endpoints

### GET `/api/groups/<group_id>/transactions`

Returns all transactions for a group with full user details.

**Response:**
```json
{
    "transactions": [
        {
            "id": 1,
            "expense_id": 5,
            "payer_id": "alice",
            "payer_name": "Alice Johnson",
            "payee_id": "bob",
            "payee_name": "Bob Smith",
            "amount": 1500.50,
            "status": "COMPLETED",
            "timestamp": "2024-01-20T14:30:00",
            "expense_name": "Groceries"
        }
    ]
}
```

### GET `/api/groups/<group_id>/balances`

Returns current balance for each group member.

**Response:**
```json
{
    "balances": {
        "alice": 1500.50,
        "bob": -500.00,
        "charlie": -1000.50
    }
}
```

**Balance Interpretation:**
- `> 0` = Amount owed to this person
- `< 0` = Amount this person owes
- `= 0` = Settled

## Data Flow

```
┌─────────────────────────────────────────┐
│ User Clicks Ledger Tab                 │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ switchTab('ledger') triggers            │
│ loadLedgerData()                        │
└──────────┬──────────────────────────────┘
           │
           ├──────────────────┬──────────────────┐
           ▼                  ▼                  ▼
    ┌────────────┐    ┌───────────────┐   ┌───────────────┐
    │ Fetch      │    │ Fetch         │   │ Calculate     │
    │ Balances   │    │ Transactions  │   │ Statistics    │
    └────┬───────┘    └───────┬───────┘   └───────┬───────┘
         │                    │                   │
         └────────────────┬───┴───────────────────┘
                          ▼
                 ┌──────────────────┐
                 │ Render Summary   │
                 │ Render Table     │
                 │ Render Balances  │
                 └──────────────────┘
```

## Frontend Implementation

### JavaScript Functions

#### `loadLedgerData()`
Main function called when ledger tab is activated.

```javascript
async function loadLedgerData() {
    // 1. Fetch transactions from API
    const txResponse = await fetch(`/api/groups/{{ group.group_id }}/transactions`);
    const transactions = (await txResponse.json()).transactions;
    
    // 2. Fetch balances from API
    const balResponse = await fetch(`/api/groups/{{ group.group_id }}/balances`);
    const balances = (await balResponse.json()).balances;
    
    // 3. Calculate statistics
    const settled = transactions.filter(t => t.status === 'COMPLETED').length;
    const pending = transactions.length - settled;
    
    // 4. Render all components
    renderSummaryCards(transactions);
    renderTransactionTable(transactions);
    renderBalanceSheet(balances);
}
```

#### `getColorForBalance(balance)`
Returns color code based on balance value.

```javascript
function getColorForBalance(balance) {
    if (balance > 0.01) return '#4CAF50';  // Green - owed
    if (balance < -0.01) return '#f44336'; // Red - owes
    return '#999';                         // Gray - settled
}
```

#### `getStatusColor(status)`
Returns color for transaction status.

```javascript
function getStatusColor(status) {
    return status === 'COMPLETED' ? '#4CAF50' : '#FF9800';
}
```

### HTML Structure

```html
<div id="ledger-tab" class="tab-content">
    <!-- Summary Cards -->
    <div id="summary-cards">
        <div class="card">Total Transactions: <span id="ledger-total-tx">0</span></div>
        <div class="card">Settled: <span id="ledger-settled">0</span></div>
        <div class="card">Pending: <span id="ledger-pending">0</span></div>
        <div class="card">Total Volume: <span id="ledger-total-volume">₹0.00</span></div>
    </div>
    
    <!-- Transaction Table -->
    <div id="ledger-transactions">
        <!-- Table rows rendered here -->
    </div>
    
    <!-- Balance Sheet -->
    <div id="ledger-balances">
        <!-- Balance cards rendered here -->
    </div>
</div>
```

## Styling Guidelines

### Color Palette

```css
/* Status Colors */
--color-settled: #4CAF50;   /* Green */
--color-pending: #FF9800;   /* Orange */
--color-owed: #4CAF50;      /* Green */
--color-owes: #f44336;      /* Red */
--color-settled-user: #999; /* Gray */

/* Background Colors */
--bg-card: #f9f9f9;
--bg-table-header: #f5f5f5;
--border-color: #e0e0e0;
```

### Responsive Design

- **Desktop**: 4-column grid for summary cards, full table
- **Tablet**: 2-column grid for summary cards
- **Mobile**: 1-column layout, scrollable table

## Example Scenarios

### Scenario 1: Simple Expense
```
Group: Trip to Goa
Members: Alice, Bob, Charlie

Expense: Hotel (₹3000)
Paid By: Alice
Split: Equal (3 ways)

Transactions Generated:
1. Bob → Alice: ₹1000 ✓ Settled
2. Charlie → Alice: ₹1000 ✓ Settled

Balances:
- Alice: Owed ₹2000 (Green/Creditor)
- Bob: Owes ₹1000 (Red/Debtor)
- Charlie: Owes ₹1000 (Red/Debtor)

Ledger Display:
✓ Total Transactions: 2
✓ Settled: 2
✓ Pending: 0
✓ Total Volume: ₹2000.00
```

### Scenario 2: Multiple Expenses with Partial Settlement
```
Group: Roommate Expenses
Members: Alice, Bob, Charlie

Initial State:
- Alice owes Bob: ₹500
- Alice owes Charlie: ₹300
- Bob owes Charlie: ₹200

After Settlemen:
- Alice → Bob: ₹500 ✓ Paid
- Alice → Charlie: ₹300 ⏳ Pending
- Bob → Charlie: ₹200 ✓ Paid

Ledger Display:
✓ Total Transactions: 3
✓ Settled: 2
✓ Pending: 1
✓ Total Volume: ₹1000.00

Balances:
- Alice: Owes ₹300 (Red/Debtor)
- Charlie: Owed ₹300 (Green/Creditor)
- Bob: Settled (Gray)
```

## Benefits

1. **Full Transparency**: Every transaction is visible to all group members
2. **Audit Trail**: Complete history of who paid and received money
3. **Quick Reconciliation**: Color coding helps identify debts and credits at a glance
4. **Dispute Resolution**: Clear record helps resolve payment disputes
5. **Financial Planning**: Members can see their financial standing in the group

## Future Enhancements

- [ ] Export ledger to CSV/PDF
- [ ] Filter transactions by date range
- [ ] Search/filter by member name
- [ ] Transaction detail modal with expense breakdown
- [ ] Transaction status updates (mark as paid)
- [ ] Ledger reconciliation workflow
- [ ] Mobile-optimized table view
- [ ] Real-time balance updates (WebSocket)
- [ ] Ledger analytics (spending trends, settlement patterns)
- [ ] Integration with payment gateways for automatic settlement

## Testing Checklist

- [ ] Verify transactions load correctly when ledger tab is clicked
- [ ] Verify balances are calculated correctly
- [ ] Verify color coding matches balance status
- [ ] Verify summary statistics are accurate
- [ ] Verify table is sortable by date
- [ ] Verify responsive design on mobile/tablet
- [ ] Verify API responses handle empty data
- [ ] Verify access control (only group members can view)
