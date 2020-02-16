# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-

from odoo import models, fields, api
import json
import logging
import werkzeug
from datetime import datetime
from math import ceil
from odoo import fields, http, SUPERUSER_ID
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _
from odoo.http import request
from odoo.tools import ustr

_logger = logging.getLogger(__name__)

class evl_transfer(models.Model):
    _name = 'evl.hr.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee transfer"

    transfer_STATES = [
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('hr', 'Hr Approved'),
        ('supervisor', 'Supervisor Approved'),
        ('manager', 'Manager Approved'),
        ('done', 'Transfered'),
        ('cancel', 'Cancel'),

        ]


    def unlink(self):
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}
        
        for line in self.filtered(lambda transfer: transfer.state not in ['draft']):
            raise UserError(_('You cannot delete a transfer which is in "%s"state.') % (state_description_values.get(line.state),))
        return super(evl_transfer, self).unlink()
    
    def confirm(self):
        for records in self:

            admin_employees =self.env['res.groups'].search([('name','=','HR Admin')]).users.mapped('employee_ids.id')
            followers_list=[]
            for emps in admin_employees:            
                followers_list.append(emps)

            filtered = [e for e in followers_list if isinstance(e, int)]

            # import pdb; pdb.set_trace()
            # if self.env['hr.employee'].sudo().browse(filtered):
            #     notification = self.env['evl.notice.board'].notification_message_post(
            #             message_body=('A transfer was created for  %s , which is now confirmed .This is now at your end to approve' % (self.employee_id.name)),
            #             related_record=self,
            #             message_recipient = self.env['hr.employee'].sudo().browse(filtered)
            #             )


            for ids in filtered:            
                employee = self.env['hr.employee'].sudo().browse(ids)
                if employee.user_id:                 
                    self.message_post(
                        body=_('A transfer was created for  %s , which is now confirmed .This is now at your end to approve' % (self.employee_id.name)),
                        partner_ids=employee.user_id.partner_id.ids)
        
            records.sudo().write({'state':'confirm'})
   
   
    state = fields.Selection(transfer_STATES, string='Status', track_visibility='onchange',default='draft')
    
    # >>>>>>>>>>>>>>>>>>>>>>>>>hr
    hr_can_approve = fields.Boolean(compute='hr_approve')    
    @api.depends('employee_id')    
    def hr_approve(self):
        for records in self:            
            if self.env.user.has_group('evl_appraisal.group_hradmins_manager') or  self.env.user.has_group('base.group_erp_manager'):               
                records.hr_can_approve = True
            else:
                records.hr_can_approve = False
                 

    def action_hr_approve(self):
        for records in self:
            records.state = 'hr'

        if self.state == 'hr':
            employee = self.env['hr.employee'].sudo().browse(self.manager_id.id)

            if employee.user_id:                     
                aa= self.message_post(
                    body=_('A transfer was created for  %s , which is approved by HR .This is now at your end to approve' % (self.employee_id.name)),
                    partner_ids=employee.user_id.partner_id.ids)
               
            

 
    # >>>>>>>>>>>>>>>>>>>>>>>>>supervisor
                
    supervisor_can_approve = fields.Boolean(compute='supervisor_approve')    
    def supervisor_approve(self):
        for records in self:
            
            if self.sudo().env.user.has_group('evl_transfer.group_hradmins_manager') or  self.sudo().env.user.has_group('base.group_erp_manager') or self.sudo().employee_id.parent_id == self.sudo().env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1):
               
                records.supervisor_can_approve = True
            else:
                records.supervisor_can_approve = False
                 

    def action_supervisor_approve(self):
        for records in self:
            records.state = 'supervisor'


            if self.state == 'supervisor':
                employee = self.env['hr.employee'].sudo().browse(self.department_id.manager_id.id)

            if employee.user_id:   
                # notification = self.env['evl.notice.board'].notification_message_post(
                #         message_body=('A transfer was created for  %s , which is approved by Supervisor.This is now at your end to approve' % (self.employee_id.name)),
                #         related_record=self,
                #         message_recipient = employee
                #         )


                self.message_post(
                    body=_('A transfer was created for  %s , which is approved by Supervisor .This is now at your end to approve' % (self.employee_id.name)),
                    partner_ids=employee.user_id.partner_id.ids)

    # >>>>>>>>>>>>>>>>>>>>>>>>>manager
                   
    manager_can_approve = fields.Boolean(compute='manager_approve')    
    def manager_approve(self):
        for records in self:
            
            if self.sudo().env.user.has_group('evl_transfer.group_hradmins_manager') or  self.env.user.has_group('base.group_erp_manager') or self.sudo().employee_id.department_id.manager_id == self.sudo().env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1):
               
                records.manager_can_approve = True
            else:
                records.manager_can_approve = False
                 

    def action_manager_approve(self):
        for records in self:
            records.state = 'manager'
        

               
        if self.state == 'manager':
            transfer_managers =self.env['res.groups'].search([('name','=','Transfer Manager')]).users.mapped('employee_ids.id')
            followers_list=[]
            for emps in transfer_managers:            
                followers_list.append(emps)

            filtered = [e for e in followers_list if isinstance(e, int)]

            for ids in filtered:
            
                employee = self.env['hr.employee'].sudo().browse(ids)

                if employee.user_id:    

                    # notification = self.env['evl.notice.board'].notification_message_post(
                    #     message_body=('A transfer was created for  %s , which is now approved by Department Head .All approvals are done. Please Proceed with manual trnsfer process' % (self.employee_id.name)),
                    #     related_record=self,
                    #     message_recipient = employee
                    #     )  
                    
                                   
                    self.message_post(
                        body=_('A transfer was created for  %s , which is now approved by Department Head .All approvals are done. Please Proceed with manual trnsfer process' % (self.employee_id.name)),
                        partner_ids=employee.user_id.partner_id.ids)

        
    
    def action_transfer_cancel(self):
        for records in self:
            records.state = 'cancel'

    # >>>>>>>>>>>>>>>>>>>>>>>>>transfer manager
                   
    transfer_manager_can_approve = fields.Boolean(compute='transfer_manager_approve')    
    def transfer_manager_approve(self):
        for records in self:
            
            if self.sudo().env.user.has_group('evl_appraisal.group_hradmins_manager') or  self.sudo().env.user.has_group('base.group_erp_manager') or   self.sudo().env.user.has_group('evl_transfer.group_transfer_manager'):               
                records.transfer_manager_can_approve = True
            else:
                records.transfer_manager_can_approve = False
                 

    def action_transfer_manager_approve(self):
        for records in self:
            records.state = 'done'
  


    employee_id = fields.Many2one('hr.employee', required=True, string='Employee', index=True)
    

    # current employee information
    company_id = fields.Many2one('res.company', string='Company', related='employee_id.company_id')
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department', readonly=True)    
    position = fields.Many2one('hr.job', related='employee_id.job_id', string='Position', readonly=True)
    manager_id = fields.Many2one('hr.employee',related='employee_id.parent_id', string='Manager', readonly=True)
    resource_calendar = fields.Many2one('resource.calendar',related='employee_id.resource_calendar_id', string='Working Calender', readonly=True)

    # revised transfer
    
    to_company_id = fields.Many2one('res.company', string='Company')
    to_department_id = fields.Many2one('hr.department', string='Department')
    to_position = fields.Many2one('hr.job', string='Position')
    to_manager_id = fields.Many2one('hr.employee', string='Manager')
    to_resource_calendar = fields.Many2one('resource.calendar', string='Working Calender')

    
    note = fields.Char(
        string='Transfer Note',
    )
    
      
    @api.depends('employee_id')
    def name_get(self):
        result = []
        for record in self:
            name = "Transfer for " + str(record.employee_id.name)
            result.append((record.id, name))
        return result
    