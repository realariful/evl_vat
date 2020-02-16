# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.translate import _
import json
import logging
import werkzeug
from datetime import datetime
from math import ceil

from odoo import fields, http, SUPERUSER_ID
from odoo.http import request
from odoo.tools import ustr
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment

_logger = logging.getLogger(__name__)
_logger = logging.getLogger(__name__)

class evl_appraisal(models.Model):
    _name = 'evl.hr.appraisal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Employee Appraisal"

    APPRAISAL_STATES = [
        ('new', 'Draft'),
        ('pending', 'Appraisal Sent'),
        ('done', 'Done'),
        ('cancel', "Cancelled"),]

    
    def unlink(self):
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}
        
        for line in self.filtered(lambda transfer: transfer.state not in ['new']):
            raise UserError(_('You cannot delete an appraisal  which is in "%s" state.') % (state_description_values.get(line.state),))
        return super(evl_appraisal, self).unlink()


    active = fields.Boolean(default=True)

    company_id = fields.Many2one('res.company', string='Company', related='employee_id.company_id')
    employee_id = fields.Many2one('hr.employee', required=True, string='Employee', index=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Department', store=True, readonly=True)

    count_completed_survey = fields.Char(string='')
    

    date_close = fields.Date(string='Appraisal Deadline', required=True)
    state = fields.Selection(APPRAISAL_STATES, string='Status', track_visibility='onchange', required=True, copy=False, default='new', index=True)

    manager_appraisal = fields.Boolean(string='Manager', help="This employee will be appraised by his managers")

    manager_ids = fields.Many2many(string='Reviewers',required=True,comodel_name='hr.employee')

    survey_id = fields.Many2one('survey.survey', 
    required=True,
     string="Appraisal Survey")

    

    appraisal_lines = fields.One2many(
        comodel_name="evl.hr.appraisal.feedback", inverse_name="appraisal_id", string="Appraisal Feedback")

    
    @api.depends('employee_id')
    def name_get(self):
        result = []
        for record in self:
            name = "Appraisal for " + str(record.employee_id.name)
            result.append((record.id, name))
        return result
    
    
    mail_template_id = fields.Many2one('mail.template', string="Email Template for Appraisal", default=lambda self: self.env.ref('evl_appraisal.evl_appraisal_template'))

    def action_get_users_input(self):
        
        tree_view_id = self.env.ref('evl_appraisal.survey_user_input_view_tree_for_appraisal').id       
        return {
            'name': "Appraisal Feedback",
            'type': 'ir.actions.act_window',
            'res_model': 'survey.user_input',
            'view_type':'form',
            'view_mode': 'tree',
            'view_id': tree_view_id,
            'res_id': False,
            'context': False,
            'target':'current',
            'domain': [('appraisal_id', '=', self.id)],
        }

   
    def button_done_appraisal(self):
        for records in self:
            records.state = 'done'

    def button_cancel_appraisal(self):
            for records in self:
                records.state = 'cancel'

    def button_send_appraisal(self):
        self.write({'state': 'pending'})
        survey_line = self.env['survey.user_input']
        
        reviewer_count = 0
        for responsible in self.manager_ids:

            user_input = self.survey_id._create_answer()
            self.survey_id.with_context(survey_token=user_input.token).action_start_survey()
            
            user_input.appraisal_id = self.id    
            user_input.employee_id = self.employee_id
            user_input.responsible = responsible.id
            user_input.deadline = self.date_close

            data = {    'appraisal_id':self.id,
                        'reviewer_id':responsible.id,
                        'state':'Not Started',
                        'survey_name':user_input.survey_id.title,
                        'response_id':user_input.id,
                        'token':user_input.token,
                        'evaluated_score':'',
                        # 'appraisal_id':self.id           
            
                    }
            records = self.env['evl.hr.appraisal.feedback'].create(data)
            reviewer_count = reviewer_count + 1



            url = self.survey_id.public_url
                
            token = user_input.token
            if token:
                url = url + '?answer_token=' + token
                mail_content = "Dear " + responsible.name + "," + "<br>Please fill out the following survey " \
                                                                "related to " + records.appraisal_id.employee_id.name+ "<br>Click here to access the survey.<br>" + \
                                str(url) + "<br>Post your response for the appraisal till : " \
                                + str(self.date_close)
                values = {'model': 'evl.hr.appraisal', 'res_id': self.ids[0], 'subject': user_input.survey_id.title,
                            'body_html': mail_content, 'parent_id': None, 'email_from': self.env.user.email or None,
                            'auto_delete': True, 'email_to': responsible.work_email}
                
                _logger.info('Mail')
                result = self.env['mail.mail'].create(values)._send()




        self.count_completed_survey = reviewer_count




class evl_appraisal_feedback(models.Model):
    _name = 'evl.hr.appraisal.feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    appraisal_id = fields.Many2one('evl.hr.appraisal', string='')
    reviewer_id = fields.Many2one('hr.employee', string='')

    is_done = fields.Boolean(string='')    
    state = fields.Char(string='Appraisal State',default = "Not Started")     

    survey_name = fields.Char(string='Survey Name')        
    response_id = fields.Many2one('survey.user_input')
    token = fields.Char(string='')
    evaluated_score = fields.Integer(string='Evaluated Score')





