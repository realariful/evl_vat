
import json
import logging
import werkzeug
from datetime import datetime
from math import ceil
from odoo.tools.translate import _

from odoo import fields, http, SUPERUSER_ID
from odoo.http import request
from odoo.tools import ustr
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment
from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)

class SurveyUserInput(models.Model):
    _inherit = "survey.user_input"

    is_appraisal = fields.Boolean(string='Is Appraisal Survey')
    appraisal_id = fields.Many2one('evl.hr.appraisal', string='Appraisal')
    

    employee_id = fields.Many2one('hr.employee', string='Employee Appraisal')
    responsible = fields.Many2one('hr.employee', string='Reviewer')

    def send_mail_for_appraisal(self):

        for records in self:
                url = records.survey_id.public_url
                url = url + '?answer_token=' + records.token

                if not records.responsible.work_email:
                     raise ValidationError(_("Email was not sent"))

                mail_content = "Dear " + records.responsible.name + "," + "<br>Please fill out the following survey " \
                                                                "related to " + records.employee_id.name + "<br>Click here to access the survey.<br>" + \
                                str(url) + "<br>Post your response for the appraisal till : " \
                                # + str(records.date_close)
                values = {'model': 'evl.hr.appraisal', 'res_id': records.appraisal_id.id, 'subject': records.survey_id.title,
                            'body_html': mail_content, 'parent_id': None, 'email_from': self.env.user.email or None,
                            'auto_delete': True, 'email_to': records.responsible.work_email}
                
                _logger.info('FYI:">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"mail sent')

                result = self.env['mail.mail'].create(values)._send()

#   
    def detailed_answer(self):
            
                view_ref = self.env['ir.model.data'].get_object_reference('survey', 'survey_user_input_view_form') 
                return {
                    'name': "Feedback Deatails",
                    'type': 'ir.actions.act_window',
                    'res_model': 'survey.user_input',
                    'view_id': view_ref and view_ref[1] or False,
                    'res_id': self.id,
                    'view_mode': 'form',

                    # 'context': False,
                    'target':'current',
                    # 'domain': [('appraisal_id', '=', self.id)],
                }

   
   
    def unlink(self):
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}
        
        for line in self.filtered(lambda transfer: transfer.state in ['new','skip','done']):
                raise UserError(_('You cannot delete an appraisal  which is in "%s" state.') % (state_description_values.get(line.state),))
        return super(SurveyUserInput, self).unlink()