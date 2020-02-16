from odoo import fields, models


class ResUsersExpenses(models.Model):
    _name = "res.users.expenses"

    user_id = fields.Integer()
    name = fields.Char()
    company_ids = fields.Many2many('res.company.expenses')


class ResCompanyExpenses(models.Model):
    _name = "res.company.expenses"

    name = fields.Char()
    company_id = fields.Integer()
