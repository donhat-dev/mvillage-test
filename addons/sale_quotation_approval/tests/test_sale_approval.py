from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleApprovalCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "standard_price": 100,
                "list_price": 120,
            }
        )
        cls.team = cls.env["crm.team"].create({"name": "Test Team"})

        # Salesperson: only base sales group
        cls.salesperson = cls.env["res.users"].create(
            {
                "name": "Test Salesperson",
                "login": "test_sp_approval",
                "email": "sp@test.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("sales_team.group_sale_salesman").id,
                        ],
                    )
                ],
            }
        )

        # Team leader: all_leads so they can access orders of team members
        cls.team_leader = cls.env["res.users"].create(
            {
                "name": "Test Team Leader",
                "login": "test_tl_approval",
                "email": "tl@test.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("sales_team.group_sale_salesman_all_leads").id,
                        ],
                    )
                ],
            }
        )
        cls.team.user_id = cls.team_leader

        # Sales manager
        cls.sales_manager = cls.env["res.users"].create(
            {
                "name": "Test Sales Manager",
                "login": "test_sm_approval",
                "email": "sm@test.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("sales_team.group_sale_manager").id,
                        ],
                    )
                ],
            }
        )

        # Finance manager: needs sale order access + account manager
        cls.finance_manager = cls.env["res.users"].create(
            {
                "name": "Test Finance Manager",
                "login": "test_fm_approval",
                "email": "fm@test.com",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("account.group_account_manager").id,
                            cls.env.ref("sales_team.group_sale_salesman_all_leads").id,
                        ],
                    )
                ],
            }
        )

    def _create_order(self, price_unit=120, standard_price=100):
        self.product.standard_price = standard_price
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.salesperson.id,
                "team_id": self.team.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": price_unit,
                        },
                    )
                ],
            }
        )


@tagged("post_install", "-at_install")
class TestApprovalLevel(TestSaleApprovalCommon):
    def test_no_approval_needed(self):
        order = self._create_order(price_unit=500, standard_price=100)
        self.assertFalse(order.approval_level)

    def test_team_leader_level(self):
        # price_unit=140, cost=120 → amount_total <= 1.5 * total_cost
        order = self._create_order(price_unit=140, standard_price=120)
        self.assertEqual(order.approval_level, "team_leader")

    def test_full_level(self):
        # cost >= amount_total → full
        order = self._create_order(price_unit=80, standard_price=100)
        self.assertEqual(order.approval_level, "full")


@tagged("post_install", "-at_install")
class TestWriteLock(TestSaleApprovalCommon):
    def test_edit_allowed_before_approval(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).write({"client_order_ref": "OK"})
        self.assertEqual(order.client_order_ref, "OK")

    def test_edit_blocked_during_approval(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).write({"client_order_ref": "BLOCKED"})

    def test_edit_blocked_for_all_users_during_approval(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.team_leader).write({"client_order_ref": "BLOCKED"})

    def test_edit_blocked_after_approved(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_leader_approve()
        self.assertEqual(order.approval_state, "approved")
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).write({"client_order_ref": "BLOCKED"})

    def test_edit_allowed_after_reject(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_reject()
        order.with_user(self.salesperson).write({"client_order_ref": "OK2"})
        self.assertEqual(order.client_order_ref, "OK2")


@tagged("post_install", "-at_install")
class TestTeamLeaderFlow(TestSaleApprovalCommon):
    def test_team_leader_full_flow(self):
        order = self._create_order(price_unit=140, standard_price=120)
        self.assertEqual(order.approval_level, "team_leader")

        # Request
        order.with_user(self.salesperson).action_request_approval()
        self.assertEqual(order.approval_state, "pending")

        # Team leader approves → fully approved
        order.with_user(self.team_leader).action_leader_approve()
        self.assertEqual(order.approval_state, "approved")

        # Confirm succeeds
        order.with_user(self.salesperson).action_confirm()
        self.assertEqual(order.state, "sale")

    def test_only_team_leader_can_approve(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.sales_manager).action_leader_approve()

    def test_salesperson_cannot_approve(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).action_leader_approve()


@tagged("post_install", "-at_install")
class TestFullThreeLevelFlow(TestSaleApprovalCommon):
    def test_full_approval_flow(self):
        order = self._create_order(price_unit=80, standard_price=100)
        self.assertEqual(order.approval_level, "full")

        # Request → pending
        order.with_user(self.salesperson).action_request_approval()
        self.assertEqual(order.approval_state, "pending")

        # Team leader → team_leader_approved
        order.with_user(self.team_leader).action_leader_approve()
        self.assertEqual(order.approval_state, "team_leader_approved")

        # Sales manager → manager_approved
        order.with_user(self.sales_manager).action_sale_manager_approve()
        self.assertEqual(order.approval_state, "manager_approved")

        # Finance manager → approved
        order.with_user(self.finance_manager).action_finance_manager_approve()
        self.assertEqual(order.approval_state, "approved")

        # Confirm
        order.with_user(self.salesperson).action_confirm()
        self.assertEqual(order.state, "sale")

    def test_wrong_stage_approve_blocked(self):
        order = self._create_order(price_unit=80, standard_price=100)
        order.with_user(self.salesperson).action_request_approval()

        # Sales manager cannot approve at pending stage
        with self.assertRaises(UserError):
            order.with_user(self.sales_manager).action_sale_manager_approve()

        # Finance manager cannot approve at pending stage
        with self.assertRaises(UserError):
            order.with_user(self.finance_manager).action_finance_manager_approve()

    def test_wrong_role_approve_blocked(self):
        order = self._create_order(price_unit=80, standard_price=100)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_leader_approve()

        # Team leader cannot approve at sales manager stage
        with self.assertRaises(UserError):
            order.with_user(self.team_leader).action_sale_manager_approve()

        order.with_user(self.sales_manager).action_sale_manager_approve()

        # Sales manager cannot approve at finance stage
        with self.assertRaises(UserError):
            order.with_user(self.sales_manager).action_finance_manager_approve()


@tagged("post_install", "-at_install")
class TestRejectAndReset(TestSaleApprovalCommon):
    def test_reject_at_pending(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_reject()
        self.assertEqual(order.approval_state, "rejected")

    def test_reject_at_team_leader_approved(self):
        order = self._create_order(price_unit=80, standard_price=100)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_leader_approve()
        order.with_user(self.sales_manager).action_reject()
        self.assertEqual(order.approval_state, "rejected")

    def test_reject_at_manager_approved(self):
        order = self._create_order(price_unit=80, standard_price=100)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_leader_approve()
        order.with_user(self.sales_manager).action_sale_manager_approve()
        order.with_user(self.finance_manager).action_reject()
        self.assertEqual(order.approval_state, "rejected")

    def test_wrong_role_reject_blocked(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).action_reject()

    def test_reject_and_resubmit(self):
        order = self._create_order(price_unit=80, standard_price=100)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_reject()

        # Can edit when rejected
        order.with_user(self.salesperson).write({"client_order_ref": "UPDATED"})

        # Can re-submit directly from rejected state
        order.with_user(self.salesperson).action_request_approval()
        self.assertEqual(order.approval_state, "pending")

    def test_cannot_resubmit_while_pending(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).action_request_approval()


@tagged("post_install", "-at_install")
class TestRequestApprovalAccess(TestSaleApprovalCommon):
    def test_only_salesperson_can_request(self):
        order = self._create_order(price_unit=140, standard_price=120)
        with self.assertRaises(UserError):
            order.with_user(self.team_leader).action_request_approval()

    def test_no_approval_needed_raises(self):
        order = self._create_order(price_unit=500, standard_price=100)
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).action_request_approval()

    def test_cannot_request_twice(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).action_request_approval()


@tagged("post_install", "-at_install")
class TestActionBlocking(TestSaleApprovalCommon):
    def test_confirm_blocked_before_approved(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).action_confirm()

    def test_send_blocked_before_approved(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).action_quotation_send()

    def test_cancel_blocked_during_approval(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).action_cancel()

    def test_draft_blocked_during_approval(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).action_draft()

    def test_cancel_blocked_after_approved(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_leader_approve()
        with self.assertRaises(UserError):
            order.with_user(self.salesperson).action_cancel()

    def test_confirm_succeeds_after_approved(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_leader_approve()
        order.with_user(self.salesperson).action_confirm()
        self.assertEqual(order.state, "sale")

    def test_no_approval_needed_confirm_allowed(self):
        order = self._create_order(price_unit=500, standard_price=100)
        self.assertFalse(order.approval_level)
        order.with_user(self.salesperson).action_confirm()


@tagged("post_install", "-at_install")
class TestApprovalPermissions(TestSaleApprovalCommon):
    def test_can_approve_reject_pending_team_leader(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        tl_order = order.with_user(self.team_leader)
        self.assertTrue(tl_order.can_approve)
        self.assertTrue(tl_order.can_reject)

    def test_cannot_approve_reject_pending_salesperson(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        sp_order = order.with_user(self.salesperson)
        self.assertFalse(sp_order.can_approve)
        self.assertFalse(sp_order.can_reject)

    def test_can_approve_reject_team_leader_approved_sales_manager(self):
        order = self._create_order(price_unit=80, standard_price=100)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_leader_approve()
        sm_order = order.with_user(self.sales_manager)
        self.assertTrue(sm_order.can_approve)
        self.assertTrue(sm_order.can_reject)

    def test_cannot_approve_reject_team_leader_approved_team_leader(self):
        order = self._create_order(price_unit=80, standard_price=100)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_leader_approve()
        tl_order = order.with_user(self.team_leader)
        self.assertFalse(tl_order.can_approve)
        self.assertFalse(tl_order.can_reject)

    def test_can_approve_reject_manager_approved_finance(self):
        order = self._create_order(price_unit=80, standard_price=100)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_leader_approve()
        order.with_user(self.sales_manager).action_sale_manager_approve()
        fm_order = order.with_user(self.finance_manager)
        self.assertTrue(fm_order.can_approve)
        self.assertTrue(fm_order.can_reject)

    def test_no_permissions_before_request(self):
        order = self._create_order(price_unit=140, standard_price=120)
        tl_order = order.with_user(self.team_leader)
        self.assertFalse(tl_order.can_approve)
        self.assertFalse(tl_order.can_reject)

    def test_no_permissions_after_approved(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_leader_approve()
        tl_order = order.with_user(self.team_leader)
        self.assertFalse(tl_order.can_approve)
        self.assertFalse(tl_order.can_reject)

    def test_no_permissions_after_rejected(self):
        order = self._create_order(price_unit=140, standard_price=120)
        order.with_user(self.salesperson).action_request_approval()
        order.with_user(self.team_leader).action_reject()
        tl_order = order.with_user(self.team_leader)
        self.assertFalse(tl_order.can_approve)
        self.assertFalse(tl_order.can_reject)
