# -*- coding: utf-8 -*-
import time
from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import except_orm
from odoo import exceptions
from odoo.exceptions import AccessError, UserError, ValidationError


class SalaryAdvancePayment(models.Model):
    _name = "salary.advance"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    
    batch = fields.Many2one(
        comodel_name='salary.advance.batch',
        ondelete='restrict',
    )
    

    def unlink(self):
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}
        
        for line in self.filtered(lambda transfer: transfer.state not in ['draft']):
            raise UserError(_('You cannot delete an Salary Advance  which is in "%s" state.') % (state_description_values.get(line.state),))
        return super(SalaryAdvancePayment, self).unlink()


    name = fields.Char(string='Name', readonly=True, default=lambda self: 'Adv/')
    
    
    employee_id = fields.Many2one('hr.employee')


    date = fields.Date(string='Date', required=True, default=lambda self: fields.Date.today())

    reason = fields.Text(string='Reason')

    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id
                                  )
    company_id = fields.Many2one('res.company', string='Company', required=True,default=lambda self: self.env.user.company_id)

    advance = fields.Float(string='Advance Amount', required=True)

    department = fields.Many2one('hr.department', string='Department')

    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submitted'),                             
                              ('approve', 'Approved'),
                              ('cancel', 'Cancelled'),
                              ('reject', 'Rejected')], string='Status', default='draft', track_visibility='onchange')



    def submit_to_manager(self):
        self.state = 'submit'

    def cancel(self):
        self.state = 'cancel'

    def reject(self):
        self.state = 'reject'

    @api.model
    def create(self, vals):
        res_id = super(SalaryAdvancePayment, self).create(vals)
        return res_id

  

    def approve_request_acc_dept(self):
       
        salary_advance_search = self.search([('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
                                             ('state', '=', 'approve')])
        current_month = datetime.strptime(str(self.date), '%Y-%m-%d').date().month

        for each_advance in salary_advance_search:
            existing_month = datetime.strptime(str(each_advance.date), '%Y-%m-%d').date().month
            if current_month == existing_month:
                raise except_orm('Error!', 'Advance can be requested once in a month')
       
        if not self.advance:
            raise except_orm('Warning', 'You must Enter the Salary Advance amount')

      
        for request in self:               
            request.state = 'approve'
            return True


class SalaryAdvanceBatchLines(models.Model):
    _name = "salary.advance.batch.lines"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    
    
    batch = fields.Many2one(
        comodel_name='salary.advance.batch',
        ondelete='restrict',
    )   
    
    
    employee_ids = fields.Many2one(
        string='field_name',
        comodel_name='hr.employee',
    )    

    
    percentage = fields.Char(
        string='Percentage',
    )

    
    amount = fields.Char(
        string='Amount',
    )
    
    # state = fields.Selection([('draft', 'Draft'),
    #                           ('generate', 'Disbursed'),
    #                           ], string='Status', default='draft', track_visibility='onchange')


    
class SalaryAdvanceBatch(models.Model):
    _name = "salary.advance.batch"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    _rec_name = 'batch_name'

    batch_name = fields.Char() 
    rec_month_name = fields.Char(string='')


    state = fields.Selection([('draft', 'Draft'),
                            ('confirm', 'Confirm'),                            
                              ('generate', 'Disbursed'),
                              ('cancel', 'Cancelled'),
                              ], string='Status', default='draft', track_visibility='onchange')


    
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
    )    
    
    
    
    date = fields.Date(string='Date')
    date_start = fields.Date(string='Date',
    required=True
    )
    date_end = fields.Date(string='Date',
    required=True
    )

    @api.onchange('date_end')
    def _onchange_(self):
        if self.date_start and self.date_end:
            if not (30 > (self.date_end - self.date_start).days > 0):
                raise except_orm('Invalid date rage found')
               
  
    
    

    advance = fields.Float(string='Advance Percentage', required=True)

    
    lines = fields.One2many(
        comodel_name='salary.advance.batch.lines',
        inverse_name='batch',
    )
    
    def compute(self):
            existing_employees = self.lines.mapped('employee_ids.id')
            for persons in self.employee_ids.filtered(lambda r: r.id not in existing_employees):
                self.lines.create({'batch':self.id,
                                'employee_ids':persons.id,
                                'amount':persons.contract_id.wage *  (self.advance / 100) if persons.contract_id else "No Active Contracts Found",
                                'percentage': self.advance
                                })

    @api.model
    def create(self, vals):        
        res_id = super(SalaryAdvanceBatch, self).create(vals)
        res_id.date = res_id.date_start
        res_id.state = 'confirm'
        res_id.batch_name = "Advance Salary for " + res_id.date.strftime("%B" ) +" "+ res_id.date.strftime("%Y")
        res_id.compute()

       
        return res_id


    def write(self,values):

            result = super(SalaryAdvanceBatch, self).write(values)
            return result
             
    
    
    def confirm(self):
            advance_object = self.env['salary.advance']
            adv_percentage = self.advance

       


            
            for liness in self.lines:

                if not liness.employee_ids.contract_id:
                    raise except_orm('Warning', 'No Active Contract for Employee')
                else:
                    if liness.employee_ids.contract_id.state != 'open':
                        raise except_orm('Warning', 'No Active Contract for Employee')
                    


                vals ={'batch':self.id,
                    'employee_id':liness.employee_ids.id,
                    'company_id':liness.employee_ids.company_id.id,
                    'advance':liness.amount,
                    'state':'approve',
                    'date':self.date}

                salary_advance_search = self.env['salary.advance'].search([('employee_id', '=', liness.employee_ids.id),
                                                ('state', '=', 'approve')])

                current_month = datetime.strptime(str(self.date), '%Y-%m-%d').date().month

                for each_advance in salary_advance_search:
                    existing_month = datetime.strptime(str(each_advance.date), '%Y-%m-%d').date().month
                    if current_month == existing_month:
                        raise except_orm('Error!', 'Advance can be requested once in a month')

                
                self.env['salary.advance'].create(vals)
                self.state = 'generate'