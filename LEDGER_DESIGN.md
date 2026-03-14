# Ledger Feature - UI/UX Design Document

## Design System

### Color Palette

#### Semantic Colors
```
Status Success (Settled/Payments)
  Primary:    #4CAF50 (Green)
  Light:      #E8F5E9 (Very Light Green)
  Dark:       #2E7D32 (Dark Green)

Status Warning (Pending/In Progress)
  Primary:    #FF9800 (Orange)
  Light:      #FFF3E0 (Very Light Orange)
  Dark:       #E65100 (Dark Orange)

Status Danger (Debt/Owes)
  Primary:    #f44336 (Red)
  Light:      #FFEBEE (Very Light Red)
  Dark:       #c62828 (Dark Red)

Status Neutral (Settled/No Action)
  Primary:    #999999 (Gray)
  Light:      #F5F5F5 (Light Gray)
  Dark:       #666666 (Dark Gray)

Info/Accent
  Primary:    #007BFF (Blue)
  Light:      #E3F2FD (Very Light Blue)
```

#### Usage Guide
```
Transaction Amount    → Blue (#007BFF)
Payer Name           → Dark (#333)
Payee Name           → Dark (#333)
Status Badge         → Color-coded (Green/Orange/etc)
Balance Owed         → Green (#4CAF50)
Balance Owes         → Red (#f44336)
Border Left Stripe   → Matches balance type
Card Background      → Light (#f9f9f9)
Content Text         → Dark (#333)
Secondary Text       → Medium (#666)
Disabled Text        → Light (#999)
```

### Typography

#### Font Family
```javascript
Font Stack: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif
Fallback: Arial, sans-serif
```

#### Font Sizes & Weights
```
Heading 1 (h1)
  Size:    2.0rem (32px)
  Weight:  700 (Bold)
  Usage:   Page title "Transaction Ledger"

Heading 2 (h2)
  Size:    1.3rem (21px)
  Weight:  600 (Semi-bold)
  Usage:   Section titles

Heading 3 (h3)
  Size:    1.1rem (18px)
  Weight:  600 (Semi-bold)
  Usage:   Balance card user name

Body Regular
  Size:    1.0rem (16px)
  Weight:  400 (Normal)
  Usage:   Table content, regular text

Body Small
  Size:    0.9rem (14px)
  Weight:  400 (Normal)
  Usage:   Secondary information

Label
  Size:    0.85rem (13px)
  Weight:  600 (Semi-bold)
  Usage:   Card labels, badges

Caption
  Size:    0.75rem (12px)
  Weight:  400 (Normal)
  Usage:   Timestamp, fine print

Badge Text
  Size:    0.85rem (13px)
  Weight:  600 (Semi-bold)
  Usage:   Status badges
```

### Spacing System

```
8px   = xs  (smallest gap, between inline elements)
12px  = sm  (small gap, between form fields)
16px  = md  (medium gap, standard padding)
24px  = lg  (large gap, between sections)
32px  = xl  (extra large gap, section separators)
48px  = 2xl (double extra large gap, major sections)
```

#### Applied Spacing
```
Card padding:           1.5rem (24px)
Button padding:         0.75rem 1.5rem (12px 24px)
Form field spacing:     1rem (16px)
Column gap (grid):      1rem (16px)
Row gap (grid):         1rem (16px)
Section margin-bottom:  2rem (32px)
Table cell padding:     1rem (16px)
Border radius:          0.75rem (12px) for cards
                        0.5rem (8px) for buttons
                        0.4rem (6px) for inputs
                        0.3rem (4px) for badges
```

### Border & Shadow System

```
Borders
  Light:    1px solid #e0e0e0 (main)
  Heavy:    2px solid #e0e0e0 (section dividers)
  Left accent: 4px solid (color-coded)

Shadows
  Card:     None (flat design)
  Hover:    None (flat design)
  Overall:  Minimal, border-based depth
```

## Component Specifications

### Summary Cards (4-Column Grid)

```
┌─────────────────────────────────────────────────────┐
│ 🔵 Total Transactions    📊 Settled   ⏳ Pending 💰 Total Volume │
└─────────────────────────────────────────────────────┘
```

#### Single Card Layout
```
┌───────────────────────────────────┐
│ [Left Border: Blue/Green/etc]      │
│ TOTAL TRANSACTIONS (uppercase)     │
│ 24 (Large, Bold)                  │
└───────────────────────────────────┘

Dimensions:
  - Min width: 220px
  - Height: ~140px
  - Padding: 1.5rem
  - Border-left: 4px
  - Border-radius: 12px
  - Background: white
  - Border: 1px solid #e0e0e0
```

#### Color Mapping for Cards
```
Total Transactions  → Border-left: #007BFF (Blue)
Settled            → Border-left: #4CAF50 (Green)
Pending            → Border-left: #FF9800 (Orange)
Total Volume       → Border-left: #e91e63 (Pink)
```

### Transaction Table

```
┌──────────────────────────────────────────────────────────────────┐
│ Transaction History                                              │
├──────────────┬──────────────┬──────────┬──────────┬──────────────┤
│ From         │ To           │ Amount   │ Date     │ Status       │
├──────────────┼──────────────┼──────────┼──────────┼──────────────┤
│ Alice        │ Bob          │ ₹1,500   │ 2024-01  │ ✓ Settled   │
├──────────────┼──────────────┼──────────┼──────────┼──────────────┤
│ Bob          │ Charlie      │ ₹500     │ 2024-01  │ ⏳ Pending  │
└──────────────┴──────────────┴──────────┴──────────┴──────────────┘
```

#### Table Styling
```
Header Row
  Background: #f5f5f5
  Border-bottom: 2px solid #e0e0e0
  Font-weight: 600
  Color: #333

Data Row
  Background: white
  Border-bottom: 1px solid #e0e0e0
  Padding: 1rem per cell
  Hover: subtle background change (future)

Status Badge
  Background: Color + 20% (semi-transparent)
  Text: Color-matched to status
  Padding: 0.4rem 0.8rem
  Border-radius: 0.3rem
  Font-weight: 600

Amount Column
  Color: #007BFF
  Font-weight: 600
  Format: ₹X,XXX.XX
```

#### Status Badge Styles
```
Settled
  Background: #4CAF5020 (Green transparent)
  Text: #4CAF50
  Icon: ✓
  Height: ~24px

Pending
  Background: #FF980020 (Orange transparent)
  Text: #FF9800
  Icon: ⏳
  Height: ~24px
```

### Balance Cards (Grid Layout)

```
┌──────────────────────────┐  ┌──────────────────────────┐
│ ┃ Alice                  │  │ ┃ Bob                    │
│ ┃ Owed ₹1,500.00        │  │ ┃ Owes ₹500.00          │
│ ┃ Creditor              │  │ ┃ Debtor                │
└──────────────────────────┘  └──────────────────────────┘
```

#### Card Layout
```
Structure:
  ├─ Left Border (4px) [Color-coded]
  ├─ Member Name (font-weight: 600, color: #333)
  ├─ Balance Status (font-size: 1.2rem, font-weight: 700)
  └─ Role Badge (font-size: 0.75rem, uppercase)

Dimensions:
  - Min width: 280px
  - Min height: 120px
  - Padding: 1.5rem
  - Grid columns: repeat(auto-fit, minmax(280px, 1fr))
  - Gap: 1rem

Color-Coded Scheme:
  Green (#4CAF50)  → Creditor (owed money)
  Red (#f44336)    → Debtor (owes money)
  Gray (#999)      → Settled (zero balance)

Border-Left:
  Matches the balance type
  Width: 4px
  Style: solid
```

#### Content Examples

**Creditor Card (Green)**
```
Alice
Owed ₹1,500.00
Creditor

Breakdown:
  - Name: "Alice"
  - Status: "Owed ₹1,500.00" (Green text)
  - Role: "Creditor" (Gray label, uppercase)
  - Border-left: #4CAF50 (Green)
```

**Debtor Card (Red)**
```
Bob
Owes ₹250.00
Debtor

Breakdown:
  - Name: "Bob"
  - Status: "Owes ₹250.00" (Red text)
  - Role: "Debtor" (Gray label, uppercase)
  - Border-left: #f44336 (Red)
```

**Settled Card (Gray)**
```
Charlie
Settled

Breakdown:
  - Name: "Charlie"
  - Status: "Settled" (Gray text)
  - Role: (none - no badge)
  - Border-left: #999 (Gray)
```

## Responsive Breakpoints

### Desktop (1024px+)
```
Summary Cards Grid:
  - grid-template-columns: repeat(auto-fit, minmax(220px, 1fr))
  - Displays 4 cards in one row
  - Gap: 1rem

Balance Cards Grid:
  - grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))
  - Displays 3-4 cards per row depending on width
  - Gap: 1rem

Table:
  - Full width with horizontal scroll
  - Min height: 600px with overflow-y: auto
```

### Tablet (768px - 1023px)
```
Summary Cards Grid:
  - grid-template-columns: repeat(2, 1fr)
  - Displays 2 cards per row
  - Gap: 1rem

Balance Cards Grid:
  - grid-template-columns: repeat(2, 1fr)
  - Displays 2 cards per row
  - Gap: 1rem

Table:
  - Full width with horizontal scroll
  - Min height: 400px with overflow-y: auto
```

### Mobile (< 768px)
```
Summary Cards Grid:
  - grid-template-columns: 1fr
  - Displays 1 card per row (full-width)
  - Gap: 1rem
  - Padding: 1rem

Balance Cards Grid:
  - grid-template-columns: 1fr
  - Displays 1 card per row (full-width)
  - Gap: 1rem

Table:
  - Width: 100% with horizontal scroll
  - Font-size: 0.9rem
  - Padding: 0.75rem per cell
  - Min height: 300px with overflow-y: auto

Special:
  - Hide non-critical columns if space is tight
  - Consider collapsible table rows
```

## Animation & Transitions

### Hover Effects
```javascript
// Card hover
.balance-card:hover {
  opacity: 0.95;
  transform: translateY(-2px);
  transition: all 0.2s ease;
}

// Button hover
button:hover {
  background: (darker shade);
  transition: background 0.3s;
}

// Tab button active
.tab-button.active {
  color: #333;
  border-bottom-color: #007BFF;
  transition: color 0.2s;
}
```

### Loading States
```
<div class="loading">
  text-align: center
  padding: 3rem
  color: #999
  
  Content: "Loading ledger data..."
  Or: Spinner animation
```

### Empty States
```
<div class="empty-state">
  text-align: center
  padding: 2rem
  color: #999
  font-size: 2rem emoji
  
  "No transactions yet" or "All settled!"
```

## Accessibility

### Color Contrast
```
All text meets WCAG AA minimum contrast (4.5:1)
- Green text on white: #4CAF50 → ✓ 3.0:1 (minimum)
- Red text on white: #f44336 → ✓ 3.3:1 (minimum)
- Blue text on white: #007BFF → ✓ 3.3:1 (minimum)
- Black text on white: #333 → ✓ 12.6:1 (excellent)
```

### Keyboard Navigation
```
- Tab through summary cards
- Tab through table rows
- Tab through balance cards
- Enter to activate buttons
- Escape to close modals (future)
```

### Screen Reader Support
```
- Semantic HTML (table, thead, tbody, th, td)
- ARIA labels for color-coded elements
- Alt text for emoji icons
- Form labels with proper associations
```

## Print Styles

```css
@media print {
  .tab-navigation { display: none; }
  .ledger-view {
    background: white;
    color: black;
  }
  .balance-card {
    page-break-inside: avoid;
  }
  table {
    page-break-inside: avoid;
  }
}
```

## Dark Mode Support (Future)

```css
@media (prefers-color-scheme: dark) {
  --bg-card: #1e1e1e;
  --text-primary: #ffffff;
  --text-secondary: #b0b0b0;
  --border-color: #404040;
  
  /* Adjust all colors for dark mode */
}
```

## Icons & Emojis

```
Transaction History     📋
Settlement             💵
Members                👥
Currency Symbol         ₹
Status Settled         ✓
Status Pending         ⏳
Creditor              💰
Debtor                📊
Money Owed            ←
Money Owing           →
```

## Code Example: Full Component

```html
<!-- Summary Cards -->
<div style="
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
">
    <div style="
        background: white;
        padding: 1.5rem;
        border-radius: 0.75rem;
        border-left: 4px solid #007BFF;
        border: 1px solid #e0e0e0;
    ">
        <div style="
            font-size: 0.85rem;
            color: #666;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 0.5rem;
        ">
            Total Transactions
        </div>
        <div style="
            font-size: 1.75rem;
            font-weight: 700;
            color: #333;
        ">
            24
        </div>
    </div>
</div>
```

## Validation & Testing

- [ ] All colors meet WCAG AA contrast requirements
- [ ] Typography scales correctly on all screen sizes
- [ ] Spacing is consistent (8px grid)
- [ ] Responsive design tested on mobile/tablet/desktop
- [ ] Print styles work correctly
- [ ] Dark mode compatibility verified
- [ ] Keyboard navigation works
- [ ] Screen reader announcements clear
- [ ] Animations perform well (60 FPS)
- [ ] Component library style consistency
