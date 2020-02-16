# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _
from odoo import models, fields, api,_
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError

class InheritEmployee(models.Model):
        _inherit = "hr.employee"

        def act_current_employee_loan(self):

            tree_view_id = self.env.ref('evl_loan.hr_loan_tree_view').id      
            return {
                'name': "Loan Lines",
                'type': 'ir.actions.act_window',
                'res_model': 'hr.loan',
                'view_type':'form',
                'view_mode': 'tree,form',
                # 'view_id': tree_view_id,
                'res_id': False,
                'context': False,
                'target':'current',
                'domain': [('employee_id', '=', self.id)],
            }

class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"


    @api.model
    def default_get(self, field_list):
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        return result


    def _default_employee(self):        
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1) 

    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            if loan.loan_amount:
                for line in loan.loan_lines:
                    if line.paid:
                        total_paid += line.amount

                balance_amount = loan.loan_amount - total_paid

                loan.total_amount = loan.loan_amount
                loan.balance_amount = balance_amount
                loan.total_paid_amount = total_paid
            else:

                loan.total_amount = loan.loan_amount
                loan.balance_amount = 0
                loan.total_paid_amount = 0



            #  self.total_amount = loan.loan_amount
            # self.balance_amount = balance_amount
            # self.total_paid_amount = total_paid

    # name = fields.Char(string=u'Name', copy=False,default=lambda self: self.env['ir.sequence'].next_by_code('hr.loan'))
    
    name = fields.Char(required=True, copy=False, readonly=True,index=True, default=lambda self: _('New'))

    status = fields.Char(compute='status_compute', string='')
    
    @api.depends('loan_lines')
    def status_compute(self):
        for records in self:
            if records.loan_lines.filtered(lambda status: status.paid == False):
                records.status = "Not Paid"
            else:
                records.status = "Fully Paid"



    loan_record = fields.Char(string='')
    _rec_name = 'loan_record'


    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True)
    # employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    
    employee_id = fields.Many2one('hr.employee', string='Employee',default=_default_employee,store=True)

    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department")
    installment = fields.Integer(string="No Of Installments", default=1)
    payment_date = fields.Date(string="Installment Start Date", required=True, default=fields.Date.today())
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    company_id = fields.Many2one('res.company', string='Company', related='employee_id.company_id')


    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
    loan_amount = fields.Float(string="Loan Amount", required=True)
    total_amount = fields.Float(string="Total Amount", readonly=True)
    balance_amount = fields.Float(string="Balance Amount", compute='_compute_loan_amount',store=False)
    total_paid_amount = fields.Float(string="Total Paid Amount")

    # journal >>>>>>>>>>>>>>>>>>>>>>>>>

    pay_date = fields.Date(string="Payment Date", required=True, default=fields.Date.today())

    loan_account = fields.Many2one('account.account', string="Loan Account")
    cash_account_id = fields.Many2one('account.account', string="Cash Account")
    journal_id = fields.Many2one('account.journal', string="Journal")    

    move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Submitted'),        
        ('supervisor', 'Supervisor Approved'),
        ('hr', 'HR Approved'),
        ('accounts', 'Accounts Approved'),
        ('man_com', 'Man. Com Approved'),
        ('md', 'MD Approved'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', track_visibility='onchange', copy=False, )

    #button actions manager only >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    supervisor_can_approve = fields.Boolean(compute='supervisor_approve')    
    def supervisor_approve(self):
        for records in self:            
            if self.sudo().env.user.has_group('evl_loan.admin_super_access_loan') or  self.sudo().env.user.has_group('base.group_erp_manager') or self.sudo().employee_id.parent_id == self.sudo().env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1):
               
                records.supervisor_can_approve = True
            else:
                records.supervisor_can_approve = False
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    admin_check_compute = fields.Boolean(compute='admin_check',default='False')
    
    description = fields.Html("Reason For Loan",
    required=True
    )


   
    @api.onchange('employee_id')
    def admin_check(self):
       for records in self:  
            if self.sudo().env.user.has_group('evl_loan.loan_group_admin') or  self.sudo().env.user.has_group('base.group_erp_manager'):
                records.admin_check_compute = True
            else:
                records.admin_check_compute = False


    # @api.model
    # def create(self, values):
    #     loan_count = self.env['hr.loan'].search_count([('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
    #                                                    ('balance_amount', '!=', 0)])
    #     if loan_count:
    #         raise ValidationError(_("The employee has already a pending installment"))
    #     else:
    #         # values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
    #         res = super(HrLoan, self).create(values)
    #         res.loan_record = "Loan for " +   res.employee_id.name + "/" + res.date.strftime("%B" ) +"-"+ res.date.strftime("%Y")
    #         return res
    # >>>>>>>>>>>>>>>>>>>>>>>>>

  




    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None

            loan_count =  self.env['hr.loan'].search([('employee_id', '=', vals['employee_id']), ('state', '=', 'md')])
            # import pdb; pdb.set_trace()
            for records in loan_count:
                records._compute_loan_amount()
                if records.balance_amount != 0:
                    raise ValidationError(_("The employee has already a pending installment"))
            
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'hr.loan', sequence_date=seq_date) or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan', sequence_date=seq_date) or _('New')

        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined

        result = super(HrLoan, self).create(vals)
        result['loan_record'] = "Loan for " +   result.employee_id.name + "/" + result.date.strftime("%B" ) +"-"+ result.date.strftime("%Y")
        # import pdb; pdb.set_trace()
        return result
    #button actions >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def action_cancel(self):    
        for records in self:
            records.write({'state': 'cancel'})

    def action_submit(self):
        self.compute_installment()
        self.write({'state': 'confirm'})   
    
    def action_supervisor_approve(self):
        self.write({'state': 'supervisor'})   

    def action_hr_approve(self):
        for records in self:
            records.write({'state': 'hr'})


    def action_accounts_approve(self):
        for records in self:
            if not records.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                if not self.loan_account or not self.pay_date or not self.cash_account_id or not self.journal_id:
                    raise UserError("You must enter Payment Date, Loan account,Cash account and Journal to approve ")
                if not self.loan_lines:
                    raise UserError('You must compute Loan Request before Approved')
                timenow = self.pay_date.strftime('%Y-%m-%d')

                records.write({'state': 'accounts'})
    def action_mancom_approve(self):
        for records in self:
            records.write({'state': 'man_com'})
    # def action_md_approve(self):
    #     for records in self:
    #         records.write({'state': 'cancel'})


    # button actions >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#  >>>>>>>>>>>>>>>>>>>>>>      


       
    def action_md_approve(self):
        for data in self:
            if not data.loan_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                if not self.loan_account or not self.pay_date or not self.cash_account_id or not self.journal_id:
                    raise UserError("You must enter Payment Date, Loan account,Cash account and Journal to approve ")
                if not self.loan_lines:
                    raise UserError('You must compute Loan Request before Approved')
                timenow = self.pay_date.strftime('%Y-%m-%d')

                for loan in self:
                    amount = loan.loan_amount
                    loan_name = loan.employee_id.name
                    reference = loan.name
                    journal_id = loan.journal_id.id
                    debit_account_id = loan.cash_account_id.id
                    credit_account_id = loan.loan_account.id

                    debit_vals = {
                        'name': loan_name,
                        'account_id': credit_account_id,
                        'journal_id': journal_id,
                        'date': timenow,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit': amount < 0.0 and -amount or 0.0,
                    }
                    
                    credit_vals = {
                        'name': loan_name,
                        'account_id': debit_account_id,
                        'journal_id': journal_id,
                        'date': timenow,
                        'debit': amount < 0.0 and -amount or 0.0,
                        'credit': amount > 0.0 and amount or 0.0,
                    }
                    vals = {
                        'company_id': self.company_id.id,
                        'narration': loan_name,
                        'ref': reference,
                        'journal_id': journal_id,
                        'date': timenow,
                        'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                    }

                    move = self.env['account.move'].create(vals)
                    move.post()
                
                self.write({'state': 'md'})
                self.write({'move_id': move.id})

    
    def unlink(self):
        for loan in self:
            if loan.state not in ('draft'):
                raise UserError(
                    'You cannot delete a loan which is confirmed')
        return super(HrLoan, self).unlink()

    
    def compute_installment(self):
       
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                loan_lines = self.env['hr.loan.line'].sudo().create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                
                date_start = date_start + relativedelta(months=1)
        return True


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    amount = fields.Float(string="Amount", required=True)
    paid = fields.Boolean(string="Paid")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.",
    required=True
    )
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.")


class HrEmployee(models.Model):
    _inherit = "hr.employee"


    def _compute_employee_loans(self):
        
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')


