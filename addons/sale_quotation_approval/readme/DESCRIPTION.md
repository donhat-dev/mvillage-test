# Sale Quotation Approval

Adds a margin-based approval workflow for sale quotations in Odoo 18
Community.

**Features:**

- Computed **Cost** field on each sale order line (`standard_price ×
  quantity`)
- Aggregated **Total Cost** on the sale order
- Automatic approval-level determination based on the relationship
  between Total Cost and Total Amount
- **Send by Email** and **Confirm** blocked until the required approval
  is obtained
- Sequential approval through Team Leader, Sales Manager, and Finance
  Manager
- Approval status displayed on form view (ribbon), list view (badge),
  and tracked via Odoo chatter
