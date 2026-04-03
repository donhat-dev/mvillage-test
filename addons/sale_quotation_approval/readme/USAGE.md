## Cost visibility

Each sale order line shows a computed **Cost** column (product cost × quantity).
The order form displays the aggregated **Total Cost** above the tax totals.

## Approval workflow

When a salesperson creates or modifies a quotation, the system automatically
computes the required **Approval Level** based on margin:

| Condition                                            | Approval Level | Flow                                                    |
| ---------------------------------------------------- | -------------- | ------------------------------------------------------- |
| Total Cost < 66.7 % of Amount Total (margin > 50 %)  | None           | Confirm directly                                        |
| Total Cost ≥ 66.7 % of Amount Total (margin ≤ 50 %)  | Team Leader    | Team Leader → Confirm                                   |
| Total Cost ≥ Amount Total (selling at or below cost) | Full 3-Level   | Team Leader → Sales Manager → Finance Manager → Confirm |

### Step-by-step

1. Salesperson clicks **Request Approval** on the quotation.
2. The quotation enters _Pending Approval_ state; order lines become read-only.
3. The Team Leader clicks **Approve** (or **Reject**).
4. If the approval level is _Full 3-Level_, the flow continues to
   Sales Manager and then Finance Manager.
5. Once fully approved, the salesperson can **Confirm** the quotation as usual.

A **Reject** at any stage resets the state to _Rejected_. The salesperson
can revise the quotation and click **Submit Approval** to re-submit.

## List view

The quotation/order list view includes an **Approval Status** badge column
with color-coded decorations (warning for pending, green for approved,
red for rejected).
