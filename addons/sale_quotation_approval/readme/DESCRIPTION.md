# Sale Quotation Approval

Adds multi-level approval workflow for sale quotations based on cost margin analysis.

**Features:**

- Cost field on sale order lines (based on product's standard price)
- Total Cost summary on sale order
- Multi-level approval workflow:
  - No approval needed when margin > 50%
  - Team Leader approval when margin ≤ 50%
  - Full 3-level approval (Team Leader → Sales Manager → Finance Manager) when selling below cost
