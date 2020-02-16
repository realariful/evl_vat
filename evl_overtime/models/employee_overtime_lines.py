# -*- coding: utf-8 -*-

from odoo import models, fields, api

from odoo import models, fields, api, exceptions, _
import babel
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
from pytz import timezone
from io import StringIO,BytesIO
import ast
import base64
from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class employeeOvertime(models.Model):
    _name = 'employee.overtime'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Overtime"


    @api.depends('employee_id')
    def name_get(self):
        result = []
        for record in self:
            name = "Overtime for " + str(record.employee_id.name)
            result.append((record.id, name))
        return result


    def _default_employee(self):        
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)   
    
    create_date = fields.Date(default=date.today(),string="Creation Date",store= "True")   

    stage_id = fields.Many2one('overtime.stage', string='Overtime Approval Stage', ondelete='restrict', tracking=True, index=True, copy=False,
       )

    employee_id = fields.Many2one('hr.employee', string='Employee',default=_default_employee,store=True)
    company_id = fields.Many2one('res.company', 'Company',related='employee_id.company_id',store= "True")
    department_id = fields.Many2one('hr.department',related ='employee_id.department_id',store= "True")


    from_time = fields.Datetime(string='From Time',
    required=True
    )
    to_time = fields.Datetime(string='To Time',
    required=True
    )
    
    @api.constrains('from_time', 'to_time')
    def _check_validity_check_in_check_out(self):
        for records in self:
            if records.from_time and records.to_time:
                if records.to_time < records.from_time:
                    raise exceptions.ValidationError(_('"To" time cannot be earlier than "From" time.'))
                if (records.to_time - records.from_time).days > 0:
                        raise exceptions.ValidationError(_('Total Overtime Length Cannot be greater than one day.'))
    
    note = fields.Text(
        string='Reason',
    )
    

    # def unlink(self):
    #     state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}        
    #     for line in self.filtered(lambda transfer: transfer.state not in ['confirm','draft']):
    #         raise UserError(_('You cannot delete a movement which is in "%s "state.') % (state_description_values.get(line.state),))
    #     return super(movement, self).unlink()


    # def followers_notification(self,employeeid,partner):
    #     self.message_subscribe(partner_ids=partner)  
    #     self.message_post(
    #         body=_('A movement request was created for  %s ' % (employeeid)),
    #         partner_ids=partner)


    # def action_confirm(self):

    #     for records in self:
    #         if records.sudo().employee_id.parent_id:
    #             self.followers_notification(self.employee_id.name,records.sudo().employee_id.parent_id.user_id.partner_id.ids)                      

    #         if records.sudo().employee_id.department_id.manager_id:
    #             self.followers_notification(self.employee_id.name,records.sudo().employee_id.department_id.manager_id.user_id.partner_id.ids)
                

    #         records.sudo().write({'state':'confirm'})
    

    # admin_check_compute = fields.Boolean(compute='admin_check',default='False')
    
    

   
    # @api.onchange('employee_id')
    # def admin_check(self):
    #    for records in self:  
    #         if self.sudo().env.user.has_group('evl_movement.movement_group_admin') or  self.sudo().env.user.has_group('base.group_erp_manager'):
    #             records.admin_check_compute = True
    #         else:
    #             records.admin_check_compute = False


 
   
    # manager = fields.Boolean(compute='manager_access') 
       
    # head=fields.Boolean(compute='head_access')

    # def manager_access(self):
    #     if self.sudo().env.user.has_group('evl_movement.group_hradmin_manager') or self.env.user.has_group('base.group_erp_manager') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1) == self.employee_id.parent_id :
    #         if  self.state == 'confirm':
    #             self.manager = False
    #             return
    #         else:
    #             self.manager = True                   
    #     else:
    #         self.manager = True
    

    # def head_access(self):
    #     for records in self:
    #         if self.sudo().env.user.has_group('evl_movement.group_hradmin_manager') or self.employee_id.department_id.manager_id == self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1) or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).id == 1 or self.env.user.has_group('leave.hr_group') or  self.env.user.has_group('base.group_erp_manager'):
    #             records.head = False
    #         else:
    #             records.head = True
                


    # @api.depends('employee_id')
    # def action_manager(self): 
    #     for recs in self:
    #         recs.sudo().write({'state':'manager'})

    # @api.depends('employee_id')
    # def action_dept_head(self): 
    #     for recs in self:
    #         if recs.state == 'manager':
    #             recs.sudo().write({'state':'head'})
            
              
    # hr_can_approve = fields.Boolean(compute='hr_approve')    
    # @api.depends('employee_id')    
    # def hr_approve(self):
    #     for records in self:            
    #         if self.env.user.has_group('evl_movement.movement_group_admin') or  self.env.user.has_group('base.group_erp_manager'):               
    #             records.hr_can_approve = False
    #         else:
    #             records.hr_can_approve = True     
    
    # def action_transfer_cancel(self):
    #         for records in self:
    #             records.state = 'cancel'


    
    # @api.depends('employee_id')
    # def action_admin(self): 
    #     for recs in self:
    #         if recs.state == 'head':
    #             recs.sudo().write({'state':'hradmin'})
            
                # vals = {
                #     'employee_id': recs.employee_id.id,
                #     'check_in': recs.from_time,
                #     'check_out':recs.to_time,
                #     'source':'state2'                
                #     }

                # records = self.env['evl.attendance'].sudo().create(vals)
           
            
                 