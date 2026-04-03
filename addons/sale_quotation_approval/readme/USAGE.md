## Cost visibility

Each sale order line shows a computed **Cost** column (product cost × quantity).
The order form displays the aggregated **Total Cost** above the tax totals.

## Approval workflow

When a Sales Person creates or modifies a quotation, the system automatically
computes the required **Approval Level** based on the relationship between
Total Cost and Total Amount:

| Condition | Approval Level | Flow |
| --- | --- | --- |
| `Total Amount > Total Cost + 50 % Total Cost` | None | Send or confirm directly |
| `Total Amount ≤ Total Cost + 50 % Total Cost` **and** `Total Amount > Total Cost` | Team Leader | Team Leader approves → continue |
| `Total Cost ≥ Total Amount` | Full 3-Level | Team Leader → Sales Manager → Finance Manager |

### Step-by-step

1. Sales Person clicks **Submit Approval** on the quotation.
2. The quotation enters _Pending Approval_ state; order lines become
   read-only.
3. The Team Leader of the assigned sales team clicks **Team Lead
   Approve** (or **Reject**).
4. If the approval level is _Full 3-Level_, the flow continues to Sales
   Manager and then Finance Manager.
5. Once fully approved, the Sales Person can **Send by Email** or
   **Confirm** the quotation as usual.

A **Reject** at any stage resets the state to _Rejected_. The Sales Person
can click **Reset Approval**, revise the quotation, and submit it again
from the beginning.

## List view

The quotation/order list view includes an **Approval Status** badge column
with color-coded decorations (warning for pending, green for approved,
red for rejected).
