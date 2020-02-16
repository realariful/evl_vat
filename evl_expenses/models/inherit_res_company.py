from odoo import fields, models, api


class ResComapnyExpensesMain(models.Model):
    _inherit = "res.company"

    @api.model
    def create(self, values):
        company_obj = super(ResComapnyExpensesMain, self).create(values)
        expense_company_object = self.env['res.company.expenses']
        expense_company_object.create({
            'company_id': company_obj.id,
            'name': company_obj.name,
        })

        return company_obj

    def write(self, values):
        company_obj = super(ResComapnyExpensesMain, self).write(values)
        expense_company_object = self.env['res.company.expenses']

        expense_company_object.write({
            'name': self.name,
        })

        return company_obj

    def unlink(self):
        res = super(ResComapnyExpensesMain, self).unlink()
        expense_company_object = self.env['res.company.expenses'].search([('company_id', '=', self.id)])
        expense_company_object.unlink()
        return res

    