from odoo import api, fields, models, _


class ExpensesType(models.Model):
    _name = 'expenses.type'
    _inherit = ['mail.thread']

    name = fields.Char(string=u'Title', size=100, required=True, track_visibility='onchange')
    description = fields.Text(string=u'Description')
    expense_account_id = fields.Many2one(string=u'Expense Account', comodel_name='account.account', ondelete='restrict', required=True, track_visibility='onchange')
    approved_user_ids = fields.Many2many(string=u'Approved Users', comodel_name='res.users.expenses', ondelete='restrict', required=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get('expenses.type'))

    @api.onchange('approved_user_ids')
    def _approved_users_domain(self):
        current_user_all_company = self.env.user.company_ids
        matched_company_expenses_id = self.env['res.company.expenses'].search([('company_id', 'in', current_user_all_company.ids)])

        return {'domain':{'approved_user_ids': [('company_ids', 'in', matched_company_expenses_id.ids)]}}
