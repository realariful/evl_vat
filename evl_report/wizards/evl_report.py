#-*- coding: utf-8 -*-

from odoo import models, fields, api


class WizardExample(models.TransientModel):
    _name = 'wizard.example'
    _description = 'wizard.example'


    patient_id = fields.Many2one('hr.employee', string="employee")
    date_meeting = fields.Date(string="Date Meeting")


    def print_report(self):
        print("+++++++++++++++++++++++++++", self.read()[0])
        print("DATA")
        data = {
            'model':'wizard.example',
            'form': self.read()[0]
        }

        app_vals = []
        vals = {
            'patient_id' : data['form']['patient_id'][1],
            'date_meeting': data['form']['date_meeting']
        }
        app_vals.append(vals)
        data['docs'] = app_vals


        print("------------------------")
        print(data['docs'] )
        return self.env.ref('evl_report.action_lost_reason_apply').report_action(self, data=data)
       
        # #data['docs'] = {}
        # selected_patient = data['form']['patient_id'][0]
        # print(selected_patient)

        # app = self.env['hr.employee'].search([('id','=',selected_patient)])
        # app.patient_id = str(data['form']['patient_id'][0])
        # app.date_meeting = str(data['form']['date_meeting'])



        # data['docs'] = app
        # ##data['docs']['date_meeting'] = str(data['form']['date_meeting'])

        # print(data['docs'])
        # #import pdb; pdb.set_trace()







    def check_report(self):
        self.ensure_one()
        data = {}
        # data['ids'] = self.env.context.get('active_ids', [])
        # data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        # data['form'] = self.read(['patient_id', 'date_meeting'])[0]
        # used_context = self._build_contexts(data)
        # data['form']['used_context'] = dict(used_context)
        # print(data)
        print(self.read())
        data['patient_id'] = self.read(['patient_id'])[0]
        data['date_meeting'] = self.read(['patient_id'])
        data['docs'] = self.read()
        return self.env.ref('evl_report.action_lost_reason_apply').report_action(self, data=data)



class WizardAccounting(models.Model):
    _name = 'wizard.accounting'
    _description = 'wizard.accounting'
    _rec_name = 'id'

    account = fields.Char(string="Accoutnb Name")
    amount = fields.Float(string="amount")
    entry_date = fields.Datetime(string="Entry Date")


    @api.model  
    def create_appointment(self,vals):
        for rec in self:
            result = super(WizardAccounting, rec).create(vals)
            return result