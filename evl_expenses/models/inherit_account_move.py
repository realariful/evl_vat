from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountMoveExpense(models.Model):
    _inherit = "account.move"

    is_account_expense_entry = fields.Boolean('Is Account Expense?', default=False)

