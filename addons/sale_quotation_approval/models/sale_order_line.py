from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    cost_total = fields.Monetary(
        string="Cost",
        compute="_compute_cost_total",
        store=True,
        currency_field="currency_id",
    )

    @api.depends("product_id.standard_price", "product_uom_qty")
    def _compute_cost_total(self):
        for line in self:
            if line.order_id.state not in ("draft", "sent"):
                continue
            line.cost_total = line.product_id.standard_price * line.product_uom_qty
