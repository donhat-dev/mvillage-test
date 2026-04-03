from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    total_cost = fields.Monetary(
        compute="_compute_total_cost",
        store=True,
        currency_field="currency_id",
    )
    approval_state = fields.Selection(
        selection=[
            ("pending", "Pending Approval"),
            ("team_leader_approved", "Team Leader Approved"),
            ("manager_approved", "Manager Approved"),
            ("approved", "Fully Approved"),
            ("rejected", "Rejected"),
        ],
        tracking=True,
        copy=False,
    )
    approval_level = fields.Selection(
        selection=[
            ("team_leader", "Partial Approval"),
            ("full", "Full Approval"),
        ],
        compute="_compute_approval_level",
        store=True,
    )
    can_approve = fields.Boolean(compute="_compute_approval_permissions")
    can_reject = fields.Boolean(compute="_compute_approval_permissions")

    @api.depends("order_line.cost_total")
    def _compute_total_cost(self):
        for order in self:
            if order.state not in ("draft", "sent"):
                continue
            order.total_cost = sum(order.order_line.mapped("cost_total"))

    @api.depends("total_cost", "amount_total")
    def _compute_approval_level(self):
        for order in self:
            if order.total_cost and order.total_cost >= order.amount_total:
                order.approval_level = "full"
            elif order.total_cost and order.amount_total <= 1.5 * order.total_cost:
                order.approval_level = "team_leader"
            else:
                order.approval_level = False

    @api.depends("approval_state", "approval_level", "team_id.user_id")
    @api.depends_context("uid")
    def _compute_approval_permissions(self):
        user = self.env.user
        is_sale_mgr = user.has_group("sales_team.group_sale_manager")
        is_finance_mgr = user.has_group("account.group_account_manager")
        for order in self:
            can_approve = False
            can_reject = False
            if order.approval_state == "pending":
                can_approve = can_reject = order.team_id.user_id == user
            elif order.approval_state == "team_leader_approved":
                can_approve = can_reject = is_sale_mgr
            elif order.approval_state == "manager_approved":
                can_approve = can_reject = is_finance_mgr
            order.can_approve = can_approve
            order.can_reject = can_reject

    # ------------------------------------------------------------------
    # Approval actions
    # ------------------------------------------------------------------

    def action_request_approval(self):
        for order in self:
            if not order.approval_level:
                raise UserError(_("This quotation does not require approval."))
            if order.user_id != self.env.user:
                raise UserError(_("Only the Salesperson can request approval."))
            if order.approval_state and order.approval_state != "rejected":
                raise UserError(
                    _("Approval has already been requested for this quotation.")
                )
            order.with_context(skip_approval_write_lock=True).write(
                {"approval_state": "pending"}
            )

    def action_leader_approve(self):
        for order in self:
            if order.approval_state != "pending":
                raise UserError(_("Nothing to approve at this stage."))
            if order.team_id.user_id != self.env.user:
                raise UserError(
                    _("Only the Sales Team Leader can approve at this stage.")
                )
            if order.approval_level == "team_leader":
                order.with_context(skip_approval_write_lock=True).write(
                    {"approval_state": "approved"}
                )
            else:
                order.with_context(skip_approval_write_lock=True).write(
                    {"approval_state": "team_leader_approved"}
                )

    def action_sale_manager_approve(self):
        for order in self:
            if order.approval_state != "team_leader_approved":
                raise UserError(_("Nothing to approve at this stage."))
            if not self.env.user.has_group("sales_team.group_sale_manager"):
                raise UserError(_("Only the Sales Manager can approve at this stage."))
            order.with_context(skip_approval_write_lock=True).write(
                {"approval_state": "manager_approved"}
            )

    def action_finance_manager_approve(self):
        for order in self:
            if order.approval_state != "manager_approved":
                raise UserError(_("Nothing to approve at this stage."))
            if not self.env.user.has_group("account.group_account_manager"):
                raise UserError(
                    _("Only the Finance Manager can approve at this stage.")
                )
            order.with_context(skip_approval_write_lock=True).write(
                {"approval_state": "approved"}
            )

    def action_reject(self):
        for order in self:
            order._check_reject_access()
            order.with_context(skip_approval_write_lock=True).write(
                {"approval_state": "rejected"}
            )

    # ------------------------------------------------------------------
    # Access checks
    # ------------------------------------------------------------------

    def _check_reject_access(self):
        self.ensure_one()
        user = self.env.user

        if self.approval_state == "pending":
            if self.team_id.user_id != user:
                raise UserError(
                    _("Only the Sales Team Leader can reject at this stage.")
                )
            return
        if self.approval_state == "team_leader_approved":
            if not user.has_group("sales_team.group_sale_manager"):
                raise UserError(_("Only the Sales Manager can reject at this stage."))
            return
        if self.approval_state == "manager_approved":
            if not user.has_group("account.group_account_manager"):
                raise UserError(_("Only the Finance Manager can reject at this stage."))
            return

        raise UserError(_("Only quotations pending approval can be rejected."))

    # ------------------------------------------------------------------
    # Overrides
    # ------------------------------------------------------------------

    def write(self, vals):
        if self.env.context.get("skip_approval_write_lock"):
            return super().write(vals)

        for order in self:
            if order.approval_state and order.approval_state != "rejected":
                raise UserError(
                    _(
                        "Quotation '%(name)s' cannot be modified while it is"
                        " in the approval flow. It must be rejected before"
                        " editing.",
                        name=order.name,
                    )
                )
        return super().write(vals)

    def action_confirm(self):
        for order in self:
            if order.approval_level and order.approval_state != "approved":
                raise UserError(
                    _(
                        "Quotation '%(name)s' requires approval before"
                        " confirmation.",
                        name=order.name,
                    )
                )
        return super(
            SaleOrder, self.with_context(skip_approval_write_lock=True)
        ).action_confirm()

    def action_quotation_send(self):
        for order in self:
            if order.approval_level and order.approval_state != "approved":
                raise UserError(
                    _(
                        "Quotation '%(name)s' requires approval before"
                        " sending to the customer.",
                        name=order.name,
                    )
                )
        return super().action_quotation_send()

    def action_quotation_sent(self):
        for order in self:
            if order.approval_level and order.approval_state != "approved":
                raise UserError(
                    _(
                        "Quotation '%(name)s' requires approval before"
                        " sending to the customer.",
                        name=order.name,
                    )
                )
        return super(
            SaleOrder, self.with_context(skip_approval_write_lock=True)
        ).action_quotation_sent()

    def action_draft(self):
        for order in self:
            if order.approval_state not in (False, "rejected"):
                raise UserError(
                    _(
                        "Quotation '%(name)s' cannot be reset to draft while"
                        " it is in the approval flow.",
                        name=order.name,
                    )
                )
        return super(
            SaleOrder, self.with_context(skip_approval_write_lock=True)
        ).action_draft()

    def action_cancel(self):
        for order in self:
            if order.approval_state not in (False, "rejected"):
                raise UserError(
                    _(
                        "Quotation '%(name)s' cannot be cancelled while it is"
                        " in the approval flow.",
                        name=order.name,
                    )
                )
        return super(
            SaleOrder, self.with_context(skip_approval_write_lock=True)
        ).action_cancel()
