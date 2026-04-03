# Sale Quotation Approval — Odoo 18 Community

Multi-level quotation approval workflow for Odoo 18 Community based on cost margin analysis.

## Description

This module extends `sale.order` and `sale.order.line` to enforce a margin-based approval policy before quotations can be sent or confirmed.

### Main features

- Computed **Cost** field on each sale order line (`standard_price × quantity`).
- Aggregated **Total Cost** on the sale order.
- Automatic approval-level determination based on the relationship between Total Cost and Total Amount.
- **Send by Email** and **Confirm** blocked until the required approval is obtained.
- Sequential approval through Team Leader, Sales Manager, and Finance Manager.
- Approval status displayed on form view (ribbon), list view (badge), and tracked via Odoo chatter.

### Approval logic summary

| Condition | Approval level | Flow |
| --- | --- | --- |
| `Total Amount > Total Cost + 50 % Total Cost` | None | Send or confirm directly |
| `Total Amount ≤ Total Cost + 50 % Total Cost` **and** `Total Amount > Total Cost` | Team Leader | Team Leader approves → continue |
| `Total Cost ≥ Total Amount` | Full 3-level | Team Leader → Sales Manager → Finance Manager |

## Installation

### Prerequisites

- Docker >= 20.10.0
- Docker Compose >= 2.0.0
- Git

### Getting started

#### 1. Clone the repository

```bash
git clone https://github.com/donhat-dev/mvillage-test.git mvillage-test
cd mvillage-test
```

#### 2. Prepare the environment file

Copy the provided `.env.example` to `.env` and adjust values if needed:

```bash
cp .env.example .env          # macOS / Linux
Copy-Item .env.example .env   # Windows PowerShell
```

Default variables:

| Variable | Default |
| --- | --- |
| `COMPOSE_PROJECT_NAME` | `mvillage` |
| `POSTGRES_USER` | `odoo` |
| `POSTGRES_PASSWORD` | `odoo` |
| `POSTGRES_DB` | `postgres` |
| `ODOO_PORT` | `8069` |
| `ODOO_CHAT_PORT` | `8072` |
| `DEBUGPY_PORT` | `5678` (debug variant only) |

#### 3. Start the services

```bash
docker compose up -d --build
```

This creates two services:

- **db** — PostgreSQL 15
- **web** — Odoo 18 Community with custom addons mounted from `addons/`

#### 4. Access the application

| Service | URL |
| --- | --- |
| Odoo web | `http://localhost:8069` |
| Longpolling / chat bus | port `8072` |
| Debug (debugpy) | port `5678` (debug compose variant) |

## Use Cases / Context

In many organizations, salespeople may offer deep discounts or sell below cost to close a deal. Without a systematic check, these quotations can be sent to customers or confirmed as sales orders without management oversight, leading to margin erosion.

This module addresses that gap by automatically computing the cost margin on every quotation and routing it through the appropriate approval levels before the quotation can be emailed or confirmed. The enforcement is built into the Odoo workflow — no external tools or manual checklists required.

### Role resolution

The original requirements do not specify which Odoo groups map to each role. This implementation applies the following assumptions:

- **Sales Person** — identified by the `user_id` field on `sale.order` (user with `sales_team.group_sale_salesman` or `sales_team.group_sale_salesman_all_leads`).
- **Team Leader** — the leader of the sales team assigned to the quotation (`team_id.user_id`).
- **Sales Manager** — any user in the `sales_team.group_sale_manager` group (*Sales / Administrator*).
- **Finance Manager** — any user in the `account.group_account_manager` group (*Invoicing / Administrator*).

## Configure

### 1. Database name

The project is configured with a fixed database name `test_approval` in `config/odoo.conf` (`list_db = False`). To use a different database name, edit `db_name` in `config/odoo.conf` before the first startup.

### 2. Install the module

1. Open `http://localhost:8069` and log in as an administrator.
2. Go to **Apps**, update the app list if needed.
3. Search for **Sale Quotation Approval** and install it.

### 3. User roles and permissions

1. Go to **Settings → Users & Companies → Users**.
2. Assign users to the appropriate business roles:
   - **Sales Person** — default sales user.
   - **Sales Manager** — user in `sales_team.group_sale_manager`.
   - **Finance Manager** — user in `account.group_account_manager`.

### 4. Sales Team Leader

1. Go to **Sales → Configuration → Sales Teams**.
2. Select the relevant sales team.
3. Set the **Team Leader** field — this user acts as the first-level approver via `team_id.user_id`.

### 5. Product cost

1. Go to **Inventory → Products**.
2. Open each product used in quotations.
3. Set the **Cost** (`standard_price`) accurately so the system can compute per-line Cost and the order-level Total Cost.

## Usage

### Basic flow

1. Log in as a **Sales Person**.
2. Create a new **Quotation** — enter customer, products, quantities, and unit prices.
3. The system automatically computes:
   - **Cost** on each order line
   - **Total Cost** on the order
   - The required **approval level**

### Scenario 1 — No approval required

When `Total Amount > Total Cost + 50 % Total Cost`, no approval is needed. The quotation can be sent by email or confirmed directly.

### Scenario 2 — Team Leader approval only

When `Total Amount ≤ Total Cost + 50 % Total Cost` and `Total Amount > Total Cost`:

1. The Sales Person clicks **Submit Approval**.
2. The quotation enters *Pending Approval* state.
3. The Team Leader of the assigned sales team clicks **Team Lead Approve**.
4. After approval the Sales Person can send or confirm the quotation.

### Scenario 3 — Full 3-level approval

When `Total Cost ≥ Total Amount`:

1. **Team Leader** approves first.
2. **Sales Manager** approves next.
3. **Finance Manager** gives the final approval.
4. Only after the status reaches **Approved** can the Sales Person send or confirm the quotation.

### Reject and re-submit

Any approver with current authority can click **Reject**.

1. The quotation moves to **Rejected** state and becomes editable again.
2. The Sales Person can revise the quotation content.
3. The Sales Person clicks **Submit Approval** to restart the approval process from the beginning.

### Read-only locking

Once a quotation enters the approval flow:

- Order line content is locked (read-only) until the quotation is rejected.
- **Send by Email** and **Confirm** are blocked until the status reaches *Approved*.
- The quotation cannot be reset to draft or cancelled while in the approval flow, except through the reject path.

### Approval tracking

- **Form view ribbon** — displays the current approval state: *Pending Approval*, *Waiting Manager*, *Waiting Finance*, *Approved*, or *Rejected*.
- **List view badge** — color-coded *Approval Status* column.
- **Chatter** — all state transitions are logged via Odoo's tracking mechanism.

## Credits

- License: [LGPL-3.0](LICENSE)

## Authors

- donhat-dev

## Contributors

- donhat-dev — <donhat.hn@gmail.com>