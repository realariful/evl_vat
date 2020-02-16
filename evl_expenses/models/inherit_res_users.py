from odoo import api, models


class ResUsersExpensesMain(models.Model):
    _inherit = "res.users"

    @api.model
    def create(self, values):
        user_obj = super(ResUsersExpensesMain, self).create(values)
        expense_user_object = self.env['res.users.expenses']
        matched_expense_company_objs = self.env['res.company.expenses'].search([('company_id', 'in', user_obj.company_ids.ids)])
        
        expense_user_object.create({
            'user_id': user_obj.id,
            'name': user_obj.name,
            'company_ids': [(6, 0, matched_expense_company_objs.ids)], 
        })

        return user_obj

    def write(self, values):
        user_obj = super(ResUsersExpensesMain, self).write(values)
        expense_user_object = self.env['res.users.expenses'].search([('user_id', '=', self.id)])
        matched_expense_company_objs = self.env['res.company.expenses'].search([('company_id', 'in', self.company_ids.ids)])
        
        expense_user_object.write({
            'name': self.name,
            'company_ids': [(6, 0, matched_expense_company_objs.ids)], 
        })

        return user_obj

    def unlink(self):
        res = super(ResUsersExpensesMain, self).unlink()
        expense_user_object = self.env['res.users.expenses'].search([('user_id', '=', self.id)])
        expense_user_object.unlink()
        return res
    