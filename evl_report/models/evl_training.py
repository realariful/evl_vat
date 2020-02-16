# #-*- coding: utf-8 -*-

# from odoo import models, fields, api


# from datetime import date, datetime
# from dateutil.relativedelta import relativedelta
# from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


# class Training(models.Model):
#     _name = 'evl.training'
#     _description = 'EVL Training Application'
#     _rec_name = 'id'

#     reference_no = fields.Char(string="Reference No.", required=True, default=None)
#     training_title = fields.Char(string="Training Title", default=None)
#     training_type = fields.Selection([
#     ('internal', 'Internal'),
#     ('external', 'External'),
#     ], string='Training Type', track_visibility='onchange', copy=False, default='internal', required=True)
#     description = fields.Char(string="Description", default=None)
#     skillset_cover = fields.Char(string="Skillset Cover", default=None)
#     capacity_of_participants = fields.Integer(string="Number of Participants", default=None)
#     participants_lines = fields.Many2many('hr.employee', string="Participants", default=None)



#     trainer_name = fields.Char( string="Trainer Name", required=True, default=None)
#     starting_date = fields.Datetime(string="Starting Date & Time", required=True, default=datetime.now)
#     ending_date = fields.Datetime(string="Ending Date & Time", required=True, default=datetime.now)
#     no_of_session = fields.Integer(string="Number of Session", required=True,default=1)

#     feedback = fields.Char(string="Feedback of Training", default=None)
#     supervisor_comments = fields.Char(string="Supervisors Comments", default=None)
    
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('saved', 'Saved'),
#         ('publish', 'Publish'),
#         ('process', 'Process'),
#         ('confirmed', 'Confirmed'),
#         ('feedback', 'Feedback Submitted'),
#         ('close', 'Close'),
#         ], string='state', readonly=True, track_visibility='onchange', copy=False, default='draft')


#     training_materials = fields.Many2many('evl.training.mat', string="Training Materials")
    
#     @api.model
#     def create(self, values):
#         """
#             Create a new record for a model ModelName
#             @param values: provides a data for new record
    
#             @return: returns a id of new record
#         """

#         result = super(Training, self).create(values)
#         if result.state == 'draft':
#             result.state = 'saved'
#         return result

#     #Publishes the training to employees and supervisor
#     def action_publish(self):
#         print(self.env.uid)
#         user= self.env['res.users'].search([('id','=',self.env.uid)])
#         print(user)

#         self.env['mail.message'].create({
#                 'email_from': self.env.user.partner_id.email, 
#                 'author_id': self.env.user.partner_id.id, 
#                 'model': 'mail.channel',
#                 # 'type': 'comment',
#                 'subtype_id': self.env.ref('mail.mt_comment').id, 
#                 'body': "Body of the message", 
#                 'channel_ids': [], 
#                 'res_id': self.env.ref('evl_training.channel_accountant_group').id, 
#             })

#     #Publishes the training to employees and supervisor
#     def action_process(self):
#         print(self.env.uid)
#         user= self.env['res.users'].search([('id','=',self.env.uid)])
#         print(user)


#     #Confirming the Training
#     def action_confirm(self):
#         print(self.env.uid)
#         user= self.env['res.users'].search([('id','=',self.env.uid)])
#         print(user)


#     #Publishes the training to employees and supervisor
#     def action_feedback(self):
#         print(self.env.uid)
#         user= self.env['res.users'].search([('id','=',self.env.uid)])
#         print(user)


#     #Publishes the training to employees and supervisor
#     def action_close(self):
#         log_user = self.env['res.users'].search([('id','=',self.env.uid)])
#         print(log_user)
#         for record in self:
#             record.state = 'close'


#     #Publishes the training to employees and supervisor
#     def action_cancel(self):
#         for record in self:
#             record.state = 'cancel'


# class TrainingMaterials(models.Model):
#     _name = 'evl.training.mat'
#     _description = 'EVL Training Materials'
#     _rec_name = 'id'

#     name = fields.Char(string="Material Name")

# class TrainingExpenses(models.Model):
#     _name = 'evl.training.expense'
#     _description = 'EVL Training Expenses'
#     _rec_name = 'id'

#     name = fields.Char(string="Expense Name")
#     amnt = fields.Char(string="Amount")