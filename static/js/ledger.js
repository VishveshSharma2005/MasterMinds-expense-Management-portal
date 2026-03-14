/**
 * Ledger Manager - Displays detailed transaction history with color coordination
 */

class LedgerManager {
    constructor(groupId) {
        this.groupId = groupId;
        this.transactions = [];
        this.balances = {};
    }

    /**
     * Fetch all transactions from the ledger
     */
    async fetchTransactions() {
        try {
            const response = await fetch(`/api/groups/${this.groupId}/transactions`);
            if (!response.ok) throw new Error('Failed to fetch transactions');
            
            const data = await response.json();
            this.transactions = data.transactions;
            return this.transactions;
        } catch (error) {
            console.error('Error fetching transactions:', error);
            return [];
        }
    }

    /**
     * Fetch current balances
     */
    async fetchBalances() {
        try {
            const response = await fetch(`/api/groups/${this.groupId}/balances`);
            if (!response.ok) throw new Error('Failed to fetch balances');
            
            const data = await response.json();
            this.balances = data.balances;
            return this.balances;
        } catch (error) {
            console.error('Error fetching balances:', error);
            return {};
        }
    }

    /**
     * Get color code based on transaction status and type
     */
    getStatusColor(status, isPayer) {
        if (status === 'COMPLETED') {
            return isPayer ? '#ef4444' : '#10b981'; // Red (debt paid) / Green (received)
        } else {
            return '#f59e0b'; // Amber (pending)
        }
    }

    /**
     * Get status badge HTML
     */
    getStatusBadge(status) {
        const badgeClass = status === 'COMPLETED' ? 'badge-success' : 'badge-warning';
        const badgeText = status === 'COMPLETED' ? '✓ Settled' : '⏳ Pending';
        return `<span class="badge ${badgeClass}">${badgeText}</span>`;
    }

    /**
     * Get user color based on their balance
     */
    getUserColor(userId) {
        const balance = this.balances[userId] || 0;
        if (balance > 0) return '#10b981'; // Green - owed money (creditor)
        if (balance < 0) return '#ef4444'; // Red - owes money (debtor)
        return '#6b7280';  // Gray - settled
    }

    /**
     * Format currency
     */
    formatCurrency(amount) {
        return `₹${amount.toFixed(2)}`;
    }

    /**
     * Format timestamp
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleDateString('en-IN') + ' ' + date.toLocaleTimeString('en-IN');
    }

    /**
     * Render detailed ledger table
     */
    renderLedgerTable() {
        if (this.transactions.length === 0) {
            return '<div class="empty-state"><p>No transactions yet</p></div>';
        }

        let html = `
            <div class="ledger-table-container">
                <table class="ledger-table">
                    <thead>
                        <tr>
                            <th>Transaction ID</th>
                            <th>From</th>
                            <th>To</th>
                            <th>Amount</th>
                            <th>Expense</th>
                            <th>Date & Time</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        this.transactions.forEach(tx => {
            const payerColor = this.getUserColor(tx.payer_id);
            const payeeColor = this.getUserColor(tx.payee_id);
            const statusColor = this.getStatusColor(tx.status, true);
            const expenseText = tx.expense_name || 'Settlement';

            html += `
                <tr class="ledger-row" data-status="${tx.status}">
                    <td class="tx-id">#${tx.id}</td>
                    <td>
                        <span class="user-badge" style="background: ${payerColor}20; border-left: 4px solid ${payerColor}">
                            ${tx.payer_name}
                        </span>
                    </td>
                    <td>
                        <span class="user-badge" style="background: ${payeeColor}20; border-left: 4px solid ${payeeColor}">
                            ${tx.payee_name}
                        </span>
                    </td>
                    <td>
                        <strong style="color: ${statusColor}">${this.formatCurrency(tx.amount)}</strong>
                    </td>
                    <td class="expense-name">${expenseText}</td>
                    <td class="timestamp">${this.formatTimestamp(tx.timestamp)}</td>
                    <td>${this.getStatusBadge(tx.status)}</td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        return html;
    }

    /**
     * Render summary cards
     */
    renderSummaryCards() {
        let creditors = 0, debtors = 0, totalOwed = 0, totalCredit = 0;

        Object.entries(this.balances).forEach(([user, balance]) => {
            if (balance > 0) {
                creditors++;
                totalCredit += balance;
            } else if (balance < 0) {
                debtors++;
                totalOwed += Math.abs(balance);
            }
        });

        return `
            <div class="summary-cards">
                <div class="card card-blue">
                    <div class="card-icon">👥</div>
                    <div class="card-content">
                        <p class="card-label">Total Transactions</p>
                        <p class="card-value">${this.transactions.length}</p>
                    </div>
                </div>
                <div class="card card-green">
                    <div class="card-icon">💰</div>
                    <div class="card-content">
                        <p class="card-label">Total Credit</p>
                        <p class="card-value">${this.formatCurrency(totalCredit)}</p>
                    </div>
                </div>
                <div class="card card-red">
                    <div class="card-icon">💳</div>
                    <div class="card-content">
                        <p class="card-label">Total Outstanding</p>
                        <p class="card-value">${this.formatCurrency(totalOwed)}</p>
                    </div>
                </div>
                <div class="card card-purple">
                    <div class="card-icon">✓</div>
                    <div class="card-content">
                        <p class="card-label">Settled Transactions</p>
                        <p class="card-value">${this.transactions.filter(t => t.status === 'COMPLETED').length}</p>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Render balance sheet
     */
    renderBalanceSheet() {
        const users = Object.entries(this.balances)
            .map(([user, balance]) => ({ user, balance }))
            .sort((a, b) => Math.abs(b.balance) - Math.abs(a.balance));

        if (users.length === 0) {
            return '<div class="empty-state"><p>All settled!</p></div>';
        }

        let html = `
            <div class="balance-sheet">
                <h3>Current Balances</h3>
                <div class="balance-list">
        `;

        users.forEach(({ user, balance }) => {
            const color = this.getUserColor(user);
            const type = balance > 0 ? '(Owed)' : '(Owes)';
            const arrow = balance > 0 ? '←' : '→';

            html += `
                <div class="balance-item" style="border-left: 4px solid ${color}">
                    <div class="balance-user">
                        <span class="balance-name">${user}</span>
                        <span class="balance-type">${type}</span>
                    </div>
                    <div class="balance-amount" style="color: ${color}">
                        ${arrow} ${this.formatCurrency(Math.abs(balance))}
                    </div>
                </div>
            `;
        });

        html += `
                </div>
            </div>
        `;

        return html;
    }

    /**
     * Initialize and render ledger view
     */
    async init(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Show loading state
        container.innerHTML = '<div class="loading">Loading ledger...</div>';

        // Fetch data
        await this.fetchTransactions();
        await this.fetchBalances();

        // Render content
        const summaryHtml = this.renderSummaryCards();
        const tableHtml = this.renderLedgerTable();
        const balanceHtml = this.renderBalanceSheet();

        container.innerHTML = `
            <div class="ledger-view">
                ${summaryHtml}
                <div class="ledger-section">
                    <h2>Transaction History</h2>
                    ${tableHtml}
                </div>
                <div class="ledger-section">
                    ${balanceHtml}
                </div>
            </div>
        `;
    }
}

// Export for use in templates
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LedgerManager;
}