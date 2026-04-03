{
    "name": "Sale Quotation Approval",
    "version": "18.0.1.0.0",
    "category": "Sales/Sales",
    "summary": "Multi-level approval workflow for sale quotations based on cost margin",
    "author": "donhat-dev",
    "website": "https://github.com/mvillage-test",
    "license": "LGPL-3",
    "depends": ["sale_management"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sale_quotation_approval/static/src/components/**/*",
        ],
    },
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
