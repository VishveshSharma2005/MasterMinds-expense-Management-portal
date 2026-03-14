# Ledger Feature Testing Guide

## Pre-Testing Setup

### 1. Database Verification
Before testing, ensure your database has:

```python
# Check for transactions table
SELECT name FROM sqlite_master 
WHERE type='table' AND name='transactions';

# Check for groups_members table
SELECT name FROM sqlite_master 
WHERE type='table' AND name='groups_members';

# Sample query to verify data exists
SELECT COUNT(*) as transaction_count FROM transactions;
```

### 2. Test Data Creation
Create test data using the UI:

1. **Create a test group** with 3+ members
2. **Add 5-10 test expenses** with different split methods
3. **Mark some transactions as settled** if available

## Manual Testing Checklist

### Test 1: Tab Navigation
**Objective:** Verify ledger tab appears and is clickable

```
✓ Navigate to Group Detail page
✓ Verify 4 tabs exist: Expenses, Members, Settlement, Ledger
✓ Click Ledger tab
✓ Verify tab content loads without errors
✓ Check browser console for JS errors (F12 → Console)
```

### Test 2: Summary Statistics
**Objective:** Verify summary cards display correct numbers

```
✓ Count total transactions in database for this group:
  SELECT COUNT(*) FROM transactions WHERE group_id = <id>

✓ Verify "Total Transactions" card matches count

✓ Count settled transactions:
  SELECT COUNT(*) FROM transactions WHERE group_id = <id> AND status='COMPLETED'

✓ Verify "Settled" card matches count

✓ Verify "Pending" = Total - Settled

✓ Sum all transaction amounts:
  SELECT SUM(amount) FROM transactions WHERE group_id = <id>

✓ Verify "Total Volume" matches sum
```

### Test 3: Transaction Table
**Objective:** Verify transaction history displays correctly

**SQL Query to validate:**
```sql
SELECT t.id, t.payer_id, t.payee_id, t.amount, t.status, t.timestamp,
       u1.full_name as payer_name, u2.full_name as payee_name
FROM transactions t
JOIN users u1 ON t.payer_id = u1.username
JOIN users u2 ON t.payee_id = u2.username
WHERE t.group_id = <group_id>
ORDER BY t.timestamp DESC;
```

**Checklist:**
```
✓ Transaction rows match database count
✓ Payer names display correctly
✓ Payee names display correctly
✓ Amounts formatted as ₹X.XX
✓ Dates match timestamp in database
✓ Status badges color-coded correctly:
  - Green ✓ for COMPLETED
  - Orange ⏳ for PENDING
✓ Table is scrollable (if > 600px)
✓ No visual overlap or truncation
```

### Test 4: Balance Sheet
**Objective:** Verify balance cards display correct values

**SQL Query to validate:**
```sql
-- Get expected balances from transactions
SELECT payee_id as user,
       SUM(amount) as balance
FROM transactions
WHERE group_id = <group_id> AND status='COMPLETED'
GROUP BY payee_id
UNION ALL
SELECT payer_id,
       -SUM(amount)
FROM transactions
WHERE group_id = <group_id> AND status='COMPLETED'
GROUP BY payer_id;
```

**Checklist:**
```
✓ One card per group member
✓ Cards sorted by balance amount (largest first)
✓ Colors match balance type:
  - Green: Balance > 0 (owed money)
  - Red: Balance < 0 (owes money)
  - Gray: Balance = 0 (settled)
✓ Left border color matches balance type
✓ Status text correct:
  - "Owed ₹X.XX" for positive balance
  - "Owes ₹X.XX" for negative balance
  - "Settled" for zero balance
✓ Role badges display:
  - "Creditor" for positive balance
  - "Debtor" for negative balance
  - (none) for zero balance
```

### Test 5: Account Access Control
**Objective:** Verify only group members can view ledger

```
✓ Login as group member
✓ Navigate to group detail
✓ Verify ledger tab accessible

✓ Login as non-member user
✓ Try to access group detail URL directly
✓ Verify 403 Forbidden error

✓ Verify API endpoint returns 401 if not logged in:
  curl http://localhost:5000/api/groups/1/transactions
```

### Test 6: Empty States
**Objective:** Verify handling of groups with no transactions

**Setup:**
1. Create a new group
2. Don't add any expenses

**Checklist:**
```
✓ Summary cards show all zeros/empty
✓ "Total Transactions: 0" displays
✓ "Total Volume: ₹0.00" displays
✓ Transaction table shows "No transactions yet"
✓ Balance sheet shows "All members settled!"
✓ No JS errors in console
```

### Test 7: Responsive Design
**Objective:** Verify layout works on different screen sizes

**Desktop (1920x1080):**
```
✓ 4-column grid for summary cards (all visible)
✓ Transaction table full width with scrolling
✓ Balance cards 2-column grid
```

**Tablet (768x1024):**
```
✓ 2-column grid for summary cards
✓ Transaction table scrollable
✓ Balance cards 1-column layout
```

**Mobile (375x667):**
```
✓ 1-column layout for summary cards
✓ Transaction table horizontal scroll
✓ Balance cards full width
✓ All text readable
✓ No content overflow
```

### Test 8: Performance
**Objective:** Verify ledger loads quickly

**Setup:**
1. Create group with 100+ transactions
2. Open DevTools (F12 → Network)

**Checklist:**
```
✓ API response time < 500ms
✓ Page render time < 1 second
✓ No memory leaks (check heap)
✓ Scrolling is smooth
✓ No jank or lag when scrolling
```

### Test 9: Data Accuracy
**Objective:** Verify ledger calculations are mathematically correct

**Example Group:**
```
Members: Alice (+₹500), Bob (-₹250), Charlie (-₹250)

Verification:
1. Sum of all balances should equal zero
   500 + (-250) + (-250) = 0 ✓

2. For Alice (creditor with ₹500):
   she receives ₹250 from Bob + ₹250 from Charlie = ₹500 ✓

3. Each transaction amount should be logical
   ✓ Split amounts match original expense
   ✓ No duplicate transactions
```

**Manual Calculation:**
```
For each member:
  balance = SUM(amount WHERE payee_id = member) 
          - SUM(amount WHERE payer_id = member)

Example with SQL:
SELECT 
    payee_id,
    SUM(amount) as owed_to,
    (SELECT SUM(amount) FROM transactions WHERE payer_id = transactions.payee_id 
     AND group_id = 1 AND status='COMPLETED') as owes_amount
FROM transactions
WHERE group_id = 1 AND status='COMPLETED'
GROUP BY payee_id;
```

## Automated Testing

### Playwright Test (Example)
```javascript
import { test, expect } from '@playwright/test';

test('ledger tab displays transaction history', async ({ page }) => {
    await page.goto('/group-detail/1');
    
    // Click ledger tab
    await page.click('[data-tab="ledger"]');
    
    // Verify summary cards exist
    const totalTxCard = await page.$('#ledger-total-tx');
    expect(totalTxCard).toBeTruthy();
    
    // Verify transaction table
    const txTable = await page.$('#ledger-transactions table');
    expect(txTable).toBeTruthy();
    
    // Verify balance cards
    const balanceCards = await page.$$('#ledger-balances > div');
    expect(balanceCards.length).toBeGreaterThan(0);
});

test('ledger respects access control', async ({ page }) => {
    // Test as non-member
    const response = await page.goto('/api/groups/999/transactions');
    expect(response.status()).toBe(403);
});
```

### pytest Test (Example)
```python
import pytest
from app import app
from flask import session

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_transactions_requires_auth(client):
    """Verify 401 when not logged in"""
    response = client.get('/api/groups/1/transactions')
    assert response.status_code == 401

def test_get_transactions_requires_membership(client):
    """Verify 403 when user not in group"""
    with client:
        # Login as user not in group
        client.post('/login', data={'username': 'alice', 'password': 'pass'})
        response = client.get('/api/groups/999/transactions')
        assert response.status_code == 403

def test_transactions_data_structure(client):
    """Verify API response has correct structure"""
    with client:
        client.post('/login', data={'username': 'alice', 'password': 'pass'})
        response = client.get('/api/groups/1/transactions')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'transactions' in data
        
        if data['transactions']:
            tx = data['transactions'][0]
            assert 'payer_id' in tx
            assert 'payee_id' in tx
            assert 'amount' in tx
            assert 'status' in tx
```

## Bug Report Template

If you find issues, report using this template:

```
## Bug: [Title]

### Environment
- OS: Windows / Mac / Linux
- Browser: Chrome / Firefox / Safari
- Flask version: X.X.X

### Steps to Reproduce
1. Navigate to [URL]
2. Click [Element]
3. Observe [Behavior]

### Expected Behavior
Description of what should happen

### Actual Behavior
Description of what actually happens

### Screenshots
[Attach screenshot if visual issue]

### Console Errors
```
[Paste any JS errors from F12 → Console]
```

### Database Query
```sql
[Relevant SQL to reproduce issue]
```

### Additional Context
Any other relevant information
```

## Performance Benchmarks

| Metric | Target | Actual |
|--------|--------|--------|
| API Response Time (<100 txs) | < 200ms | ____ |
| API Response Time (>500 txs) | < 500ms | ____ |
| Page Render Time | < 1s | ____ |
| Scroll Performance | 60 FPS | ____ |
| Memory Usage | < 50MB | ____ |

## Sign-Off

- [ ] All tests passed
- [ ] No console errors
- [ ] Responsive on mobile
- [ ] Access control verified
- [ ] Performance acceptable
- [ ] Data accuracy confirmed

**Tested By:** _______________  
**Date:** _______________  
**Status:** ✓ PASS / ✗ FAIL
