"""
Advanced Group Expense Tracker with Settlement Algorithm
Efficiently tracks shared expenses and calculates optimal settlements
"""

from collections import defaultdict
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Expense:
    """Represents a single expense"""
    id: str
    description: str
    amount: float
    paid_by: str
    participants: List[str]
    date: str
    
    def __post_init__(self):
        # Validate that paid_by is in participants
        if self.paid_by not in self.participants:
            self.participants.append(self.paid_by)


@dataclass
class Settlement:
    """Represents a payment from one person to another"""
    from_person: str
    to_person: str
    amount: float
    
    def __str__(self):
        return f"{self.from_person} → {self.to_person}: ${self.amount:.2f}"


class AdvancedExpenseTracker:
    """
    Advanced expense tracker with settlement feature
    
    Tracks shared group expenses and calculates optimal settlements
    using a greedy matching algorithm.
    
    Features:
    - Track who paid what amount
    - Track who participated in which expenses
    - Calculate individual balances (amount owed vs amount paid)
    - Optimize settlements using greedy matching algorithm
    - Group settlements by creditor
    """
    
    def __init__(self):
        self.expenses: List[Expense] = []
        self.balances: Dict[str, float] = defaultdict(float)
        self.expense_counter = 0
    
    def add_expense(
        self, 
        description: str, 
        amount: float, 
        paid_by: str, 
        participants: List[str],
        date: str = None
    ) -> str:
        """
        Add an expense to the tracker
        
        Args:
            description: Description of the expense
            amount: Total amount spent
            paid_by: Person who paid
            participants: List of people who should split this expense
            date: Date of expense (optional, defaults to today)
        
        Returns:
            Expense ID (e.g., "EXP_0001")
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        self.expense_counter += 1
        expense_id = f"EXP_{self.expense_counter:04d}"
        
        # Ensure paid_by is in participants
        if paid_by not in participants:
            participants = participants + [paid_by]
        
        # Remove duplicates
        participants = list(set(participants))
        
        expense = Expense(
            id=expense_id,
            description=description,
            amount=amount,
            paid_by=paid_by,
            participants=participants,
            date=date
        )
        
        self.expenses.append(expense)
        self._update_balances(expense)
        
        return expense_id
    
    def _update_balances(self, expense: Expense):
        """
        Update balances after adding an expense
        
        Internal method called by add_expense()
        
        Algorithm:
        1. Calculate per-person share: amount / number_of_participants
        2. Credit the payer: balance[paid_by] += expense.amount
        3. Debit all participants: balance[participant] -= per_person_share
        
        Time Complexity: O(n) where n = number of participants
        Space Complexity: O(1)
        """
        per_person_share = expense.amount / len(expense.participants)
        
        # Person who paid gets credit
        self.balances[expense.paid_by] += expense.amount
        
        # All participants owe their share
        for participant in expense.participants:
            self.balances[participant] -= per_person_share
    
    def get_balance(self, person: str) -> float:
        """
        Get the current balance for a person
        
        Args:
            person: Name of the person
        
        Returns:
            Balance amount
            - Positive = person is owed money (creditor)
            - Negative = person owes money (debtor)
            - Zero = fully settled
        """
        return self.balances[person]
    
    def get_all_balances(self) -> Dict[str, float]:
        """
        Get all participants and their current balances
        
        Returns:
            Dictionary mapping person name to balance
        """
        return dict(self.balances)
    
    def calculate_settlements(self) -> List[Settlement]:
        """
        Calculate optimal settlements using greedy matching algorithm
        
        Algorithm Overview:
        1. Separate people into debtors and creditors based on balance
        2. Greedily match debtors with creditors:
           - Take first debtor (largest debt) and first creditor (largest claim)
           - Settle minimum(debt, credit) amount between them
           - Remove fully settled person from list
           - Repeat until all settled
        
        Why Greedy Works:
        - Each settlement fully eliminates either a debtor or creditor (or both)
        - Never creates unnecessary partial payments
        - Results in minimum number of transactions
        - Proof: each transaction reduces unsettled people count by >= 1
        
        Time Complexity: O(n log n) where n = number of participants
        Space Complexity: O(n)
        
        Returns:
            List of Settlement objects representing all payments needed
        """
        settlements = []
        
        # Create lists of people who owe money and who are owed
        debtors = []  # [person_name, amount_owed]
        creditors = []  # [person_name, amount_owed_to_them]
        
        # Separate debtors and creditors
        for person, balance in self.balances.items():
            if balance < -0.01:  # Account for floating point errors
                debtors.append([person, -balance])
            elif balance > 0.01:
                creditors.append([person, balance])
        
        # Greedy matching loop
        while debtors and creditors:
            debtor_name, debt_amount = debtors[0]
            creditor_name, credit_amount = creditors[0]
            
            # Settle up to the minimum of debt and credit
            settlement_amount = min(debt_amount, credit_amount)
            
            settlements.append(Settlement(
                from_person=debtor_name,
                to_person=creditor_name,
                amount=settlement_amount
            ))
            
            # Update remaining amounts
            debtors[0][1] -= settlement_amount
            creditors[0][1] -= settlement_amount
            
            # Remove if fully settled
            if debtors[0][1] < 0.01:
                debtors.pop(0)
            if creditors[0][1] < 0.01:
                creditors.pop(0)
        
        return settlements
    
    def calculate_settlements_with_groups(self) -> Dict[str, List[Settlement]]:
        """
        Return settlements grouped by creditor
        
        Useful for understanding who needs to pay whom
        
        Returns:
            Dictionary where keys are creditor names and values are
            lists of settlements they should receive
        """
        settlements = self.calculate_settlements()
        grouped = defaultdict(list)
        
        for settlement in settlements:
            grouped[settlement.to_person].append(settlement)
        
        return dict(grouped)
    
    def get_expenses(self) -> List[Dict]:
        """
        Get all expenses in readable format
        
        Returns:
            List of dictionaries containing expense details
        """
        return [
            {
                'id': exp.id,
                'description': exp.description,
                'amount': exp.amount,
                'paid_by': exp.paid_by,
                'participants': exp.participants,
                'per_person_share': exp.amount / len(exp.participants),
                'date': exp.date
            }
            for exp in self.expenses
        ]
    
    def clear_all(self):
        """Clear all expenses and balances - reset tracker to initial state"""
        self.expenses.clear()
        self.balances.clear()
        self.expense_counter = 0
    
    def print_summary(self):
        """Print a comprehensive summary of the tracker including expenses, balances, and settlements"""
        print("\n" + "="*60)
        print("ADVANCED EXPENSE TRACKER SUMMARY")
        print("="*60)
        
        if not self.expenses:
            print("No expenses tracked yet.")
            return
        
        print("\nExpenses:")
        print("-" * 60)
        for exp in self.expenses:
            per_share = exp.amount / len(exp.participants)
            print(f"[{exp.id}] {exp.description}: ${exp.amount:.2f}")
            print(f"  Paid by: {exp.paid_by}")
            print(f"  Participants: {', '.join(exp.participants)}")
            print(f"  Per person share: ${per_share:.2f}")
            print(f"  Date: {exp.date}\n")
        
        print("\nBalances:")
        print("-" * 60)
        for person, balance in sorted(self.balances.items()):
            if balance > 0:
                print(f"{person}: ${balance:.2f} (to receive)")
            elif balance < 0:
                print(f"{person}: ${-balance:.2f} (to pay)")
            else:
                print(f"{person}: $0.00 (settled)")
        
        print("\nSettlements Needed:")
        print("-" * 60)
        settlements = self.calculate_settlements()
        if settlements:
            for i, settlement in enumerate(settlements, 1):
                print(f"{i}. {settlement}")
        else:
            print("All settled!")
        
        print("="*60 + "\n")


# ============================================================================
# Example Usage and Testing
# ============================================================================

if __name__ == "__main__":
    # Create advanced tracker
    tracker = AdvancedExpenseTracker()
    
    print("=" * 60)
    print("ADVANCED EXPENSE TRACKER - EXAMPLE")
    print("=" * 60)
    
    # Add some expenses
    print("\n1. Adding expenses...")
    
    tracker.add_expense("Team lunch", 200, "Alice", ["Alice", "Bob", "Charlie", "Diana", "Eve"])
    tracker.add_expense("Hotel room A", 300, "Bob", ["Bob", "Charlie"])
    tracker.add_expense("Hotel room B", 400, "Diana", ["Diana", "Eve"])
    tracker.add_expense("Transportation", 150, "Charlie", ["Alice", "Bob", "Charlie", "Diana", "Eve"])
    
    # Display summary
    tracker.print_summary()
    
    # Get specific person's balance
    print("\nIndividual Balances:")
    for person in ["Alice", "Bob", "Charlie", "Diana", "Eve"]:
        balance = tracker.get_balance(person)
        status = "owes" if balance < 0 else "is owed"
        print(f"{person}: ${abs(balance):.2f} {status}")
    
    print("\nSettlements grouped by creditor:")
    grouped = tracker.calculate_settlements_with_groups()
    for creditor, settlements in sorted(grouped.items()):
        print(f"\n{creditor} should receive:")
        for settlement in settlements:
            print(f"  - {settlement.from_person}: ${settlement.amount:.2f}")
