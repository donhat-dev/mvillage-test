After installing the module, configure approvers according to the business
roles used by the implementation:

- **Sales Person** — the quotation owner (`user_id` on `sale.order`), using
  the standard sales user access rights.
- **Team Leader** — the first approver, resolved from the sales team assigned
  to the quotation (`team_id.user_id`). Configure this under
  **Sales → Configuration → Sales Teams**.
- **Sales Manager** — a user in the `sales_team.group_sale_manager` group,
  who approves the second step of the full 3-level flow.
- **Finance Manager** — a user in the `account.group_account_manager` group,
  who provides the final approval when selling at or below cost.

Products must have a **Cost** (`standard_price`) set for the approval level
to be computed correctly.
