#-*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta



class Training(models.Model):
    _name = 'evl.trainings'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'EVL Training Application'
    _rec_name = 'training_title'


    name = fields.Char(string='Name', copy=False, readonly=True, default=lambda self: self._get_next_name())
    reference_no = fields.Char(string="Reference No.", default=None)
    training_purpose = fields.Char(string="Training Purpose", default=None, required=True)


    training_title = fields.Char(string='Training Title', index=True, required=True)
    training_type = fields.Selection([
    ('internal', 'Internal'),
    ('external', 'External'),
    ], string='Training Type', track_visibility='onchange', copy=False, default='internal')

    description = fields.Char(string="Description", default=None)
    skillset_cover = fields.Char(string="Skillset Cover", default=None)
    capacity_of_participants = fields.Integer(string="Number of Participants", default=None)
    participants_lines = fields.Many2many('hr.employee', string="Participants", default=None)
    trainer_name = fields.Char( string="Trainer Name", default=None)
    starting_date = fields.Datetime(string="Starting Date & Time", required=True)
    ending_date = fields.Datetime(string="Ending Date & Time", required=True)
    mancom_comments = fields.Text( string="Comments", default=None)
    date_status = fields.Boolean(compute="check_start_end", default=False, store=False)

    venue = fields.Char(string="Venue")
    




    @api.depends('starting_date','ending_date')
    def check_start_end(self):
        for rec in self:
            if rec.ending_date <= rec.starting_date:
                rec.date_status = True
                raise ValidationError("Ending Time must be greater than Starting Time")  

    no_of_session = fields.Integer(string="Number of Session",default=1)
    supervisor_comments = fields.Char(string="Supervisors Comments", default=None)

    hr_note = fields.Text(string="HR Note", default=None) 
    mancom_note = fields.Text(string="Man Com Note", default=None) 
    state = fields.Selection([
        ('pre', 'predraft'),
        ('rft','RFT'),
        ('draft', 'Send to HR'),
        ('submit', 'Submitted'),
        ('approve', 'Approved'),
        ('cancel', 'Calcelled'),
        ('process', 'Processing'),
        ('confirmed', 'Confirmed'),
        ('feedback', 'Feedback Submitted'),
        ('close', 'Close'),
        ], string='state', readonly=True, track_visibility='onchange', copy=False, default='rft')


    training_materials = fields.One2many('training.mat.lines','material_id', string="Training Materials")
    expense_prices = fields.One2many('training.expense.lines','expense_id', string="Training Expenses")


    user_id = fields.Many2one('res.users',string='Logged User', compute='check_logged_user')
    def check_logged_user(self):
        #user = self.env['res.users'].sudo().search([('id','=',self.env.uid)])     
        for rec in self:
            user = rec.env['res.users'].sudo().search([('id','=',self.env.uid)]) 
            rec.sudo().user_id = user.id


    feedback_users = fields.One2many('feedback.users','feedback_id', string="Feedback users")


    check_hod = fields.Boolean(compute="check_hod_status", default=False , store=False)
    check_hr  = fields.Boolean(compute="check_hr_status", default=False, store=False) 
    check_mancom = fields.Boolean(compute="check_man_status", default=False, store=False)


    feedback_note = fields.Char( string="Feedback from User", default=None)

    feedback_users_status = fields.Boolean(compute="check_feedback", string="Feedback users Status", default=False)
    feedback_status = fields.Boolean(compute="check_feedback_status", string="Feedback Status", default=False)
    #feedbk_btn_status = fields.Boolean(compute="feedbk_btn_status", string="Feedback Btn Status", default=False)

    def check_feedback(self):
        for rec in self:
            rec.feedback_users_status = False
            if rec.state == 'confirmed':
                if rec.feedback_users:
                    for usr in rec.feedback_users:
                        if usr.user_id.id == rec.env.uid:
                            rec.feedback_users_status = True
                            print("Feed back User")
                    print(rec.feedback_users_status)
            else:
                rec.feedback_users_status = False
            print("check_feedback")
            print(rec.feedback_users_status)

    def check_feedback_status(self):
        for rec in self:
            rec.feedback_status = False
            if rec.state == 'confirmed':
                if rec.feedback_users:
                    user = rec.env['res.users'].sudo().search([('id','=',self.env.uid)])      

                    if user.id in rec.feedback_users.user_id.ids:
                        feedback_ids = rec.feedback_users.feedback_id.id
                        feedbk_user = rec.feedback_users.sudo().search([('feedback_id','=',feedback_ids),('user_id','=',user.id)])
                        fb_user = rec.feedback_users.sudo().search([('feedback_id','=',feedback_ids),('user_id','=',user.id)])#feedback.users(1,)
                        
                        if fb_user.feedback == False or fb_user.feedback == '':
                            rec.feedback_status = True
                else:
                    rec.feedback_status = False
            print("check_feedback_status")
            print(rec.feedback_status)

    #company_id =  fields.Many2one('res.users',string='Logged User', compute='check_logged_user')
    #------
    # check_user = fields.Boolean(compute="check_user_status", default=False, store=False) 

    # def check_user_status(self):
    #     for rec in self:
    #         user = rec.env['res.users'].sudo().search([('id','=',rec.env.uid)])           
    #         for emp in rec.participants_lines:
    #             if emp.id == user.employee_id:
    #                 rec.sudo().check_user = True    
    #---------

            
    def _get_next_name(self):
        sequence = self.env['ir.sequence'].sudo().search([('code','=','evl.trainings.order')])
        next= sequence.get_next_char(sequence.number_next_actual)
        return next 


    def add_follower(self, employee_id):
        employee = self.env['hr.employee'].sudo().browse(employee_id)
        if employee.user_id:
                     
            self.message_post(
                body=('A transfer is created for  %s' % (employee.name)),
                partner_ids=employee.user_id.partner_id.ids)


    def check_hod_status(self):
        for rec in self:
            user = rec.env['res.users'].sudo().search([('id','=',self.env.uid)])         
            if rec.create_uid.id == user.id:
                rec.sudo().check_hod = True
            else:
                rec.sudo().check_hod = False
            print("REC-->", rec.state)
            print("check_hod-->", rec.check_hod)


    def check_hr_status(self):
        for rec in self:
            if rec.env.user.sudo().has_group('evl_training.group_evl_training_hr') or rec.env.user.sudo().has_group('base.group_erp_manager'):
                rec.sudo().check_hr = True
            else:
                rec.sudo().check_hr = False
            print(rec.sudo().check_hr)
    def check_man_status(self):
        for rec in self:
            if rec.env.user.sudo().has_group('evl_training.group_evl_training_mancom') or rec.env.user.sudo().has_group('base.group_erp_manager'):
                rec.sudo().check_mancom = True
            else:
                rec.sudo().check_mancom = False
            print(rec.sudo().check_mancom)

    @api.model  
    def create(self, vals):
        """
            Create a new record for a model ModelName
            @param values: provides a data for new record
    
            @return: returns a id of new record
        """

        # if vals.get('name', ('New')) == 'New':
        #     vals['name'] = self.env['ir.sequence'].next_by_code('evl.trainings.sequence') or 'New'
        #     #import pdb; pdb.set_trace()
        #     print(vals['name']) 
        # print("--------------")
        user = self.env['res.users'].sudo().search([('id','=',self.env.uid)])

        if user.department_id.manager_id.user_id.id == user.id or user.sudo().has_group('base.group_erp_manager'):
            result = super(Training, self).create(vals)
            if result.state == 'pre':
                result.sudo().write({'state':'rft'})              
            return result
        else:
            raise ValidationError("Only Department Manager can request for training!!")  


    def write(self,values):
        for rec in self:
            if rec.state == 'rft':
                result = super(Training, rec).write(values)
                return result
            else:
                result = super(Training, rec).write(values)
                return result      


    def unlink(self):
        for rec in self:
            if not rec.state == 'rft':
                raise UserError(_('You can not delete this record since it is not in RFT state.'))
            else:
                return super(Training, self).unlink()


    #Send the training to HR
    def action_sendtohr(self):        
        user = self.env['res.users'].sudo().search([('id','=',self.env.uid)])

        for rec in self:
            user = self.env['res.users'].sudo().search([('id','=',rec.env.uid)])
            if user.department_id.manager_id.user_id.id == user.id or user.sudo().has_group('base.group_erp_manager'):

                admin_employees = self.env['res.groups'].sudo().search([('category_id.name','=','Training Management'),('name','=','HR Admin')]).users                
                hr_employees = admin_employees.employee_ids                
                notice_board_status = self.env['evl.notice.board'].notification_message_post(
                    message_body='A Training Request was created by  %s. This is now at your end to process.' % (rec.create_uid.name),
                    related_record=self,
                    message_recipient = hr_employees
                    )
                print(notice_board_status)

                if rec.state == 'rft':
                    rec.sudo().write({'state':'draft'})
        
    #Submit the Training Request
    def action_submit(self):  
        for rec in self:
            if rec.state == 'draft':                
                if rec.env.user.sudo().has_group('evl_training.group_evl_training_hr') or rec.env.user.sudo().has_group('base.group_erp_manager'):
                    if not (rec.reference_no and rec.trainer_name and rec.description and rec.skillset_cover):
                        raise ValidationError("Please input all fields")
                    
                    elif not rec.participants_lines:
                        raise ValidationError("Please input atleast one participant")

                    elif not rec.training_materials:
                        raise ValidationError("Please input atleast one material")                    
                    
                    else:                        
                        rec.sudo().check_hr = True
                        #Sending Notification to Man Com
                        mancoms = self.env['res.groups'].sudo().search([('category_id.name','=','Training Management'),('name','=','Man Com')]).users 
                        #mancoms =self.env['res.groups'].search([('name','=','Man Com')]).users
                        hr_employees = mancoms.employee_ids                
                        notice_board_status = self.env['evl.notice.board'].sudo().notification_message_post(
                            message_body='A Training Request has been submitted by  %s. This is now at your end to approve.' % (rec.env.user.name),
                            related_record=self,
                            message_recipient = hr_employees
                            )

                        rec.sudo().write({'state':'submit'})
                else:
                    raise ValidationError("You are not permitted to submit this request")

    #Approve the Training Request
    def action_approve(self):        
        for rec in self:
            if rec.state == 'submit':
                if rec.env.user.sudo().has_group('evl_training.group_evl_training_mancom') or rec.env.user.sudo().has_group('base.group_erp_manager'):
                    #Sending Notification to HR Admins
                    hr_admins = self.env['res.groups'].sudo().search([('category_id.name','=','Training Management'),('name','=','HR Admin')]).users      

                    hr_employees = hr_admins.employee_ids                
                    notice_board_status = self.env['evl.notice.board'].sudo().notification_message_post(
                        message_body='A Training Request has been approved by %s.This is now at your end to publish.' % (rec.env.user.name),
                        related_record=self,
                        message_recipient = hr_employees
                        )

                    rec.sudo().write({'state':'approve'})
                else:
                    raise ValidationError("You are not permitted to approve this Training Request")            


    #Cancel the training
    def action_publish(self):
        for rec in self:
            if rec.sudo().state == 'approve':
                if rec.env.user.sudo().has_group('evl_training.group_evl_training_hr') or rec.env.user.sudo().has_group('base.group_erp_manager'):
       
                    notice_board_status = self.env['evl.notice.board'].sudo().notification_message_post(
                        message_body='A Training has been published by %s. Please attend this training.' % (rec.env.user.name),
                        related_record=self,
                        message_recipient = rec.participants_lines
                        )

                    rec.sudo().write({'state':'process'})
                else:
                    raise ValidationError("You are not permitted to publish this Training Request") 

    #Cancel the training
    def action_cancel(self):
        for rec in self:
            if rec.env.user.sudo().has_group('evl_training.group_evl_training_mancom') or rec.env.user.sudo().has_group('base.group_erp_manager'):
                if rec.sudo().state == 'submit':
               
                    notice_board_status = self.env['evl.notice.board'].sudo().notification_message_post(
                        message_body='Your Training Request has been declined by %s.' % (rec.env.user.name),
                        related_record=self,
                        message_recipient = rec.create_uid.employee_id
                        )

                    rec.sudo().write({'state':'cancel'})
                    
            else:
                raise ValidationError("You are not permitted to cancel this Training Request") 


    #Confirming the Training
    def action_confirm(self):
        for rec in self:
            if rec.env.user.sudo().has_group('evl_training.group_evl_training_hr') or rec.env.user.sudo().has_group('base.group_erp_manager'):
                if rec.sudo().state == 'process':
                    if len(rec.feedback_users) == 0:
                        raise ValidationError("Please insert one feedback user!") 
                    else:
                        #Send notifications to feedback users               
                        notice_board_status = self.env['evl.notice.board'].sudo().notification_message_post(
                            message_body='A Training Request need your feedback. Please give your feedback!',
                            related_record=self,
                            message_recipient = rec.feedback_users.user_id.employee_id
                            )                     

                        rec.sudo().write({'state':'confirmed'})  
            else:
                raise ValidationError("You are not permitted to confirm this Training Request") 


    def action_feedback(self):
        user= self.env['res.users'].sudo().search([('id','=',self.env.uid)])
        for rec in self:
            if rec.state == 'confirmed':    
                #import pdb; pdb.set_trace()
                if user.id in rec.feedback_users.user_id.ids:
                    feedback_ids = rec.feedback_users.feedback_id.id
                    feedbk_user = rec.feedback_users.sudo().search([('feedback_id','=',feedback_ids),('user_id','=',user.id)])
                    fb_user = rec.feedback_users.sudo().search([('feedback_id','=',feedback_ids),('user_id','=',user.id)])#feedback.users(1,)
                    

                    if not rec.feedback_note:
                        raise ValidationError("Please provide a feedback for this training.") 
                    else:
                        if fb_user.feedback == False:
                            if not rec.feedback_note:
                                raise ValidationError("Please provide a feedback for this training.") 
                            else:
                                fb_user.feedback = rec.feedback_note
                                fb_user.feedback_status = True

                                rec.feedback_note = ''
                
                if rec.feedback_users:
                    main_status = True
                    for usr in rec.feedback_users:
                        print(usr)
                        main_status = main_status and usr.feedback_status
                    print(main_status)

                    if main_status == True:
                        rec.state = 'feedback'


                    






    #Close the training
    def action_close(self):
        print(self.env.uid)
        user= self.env['res.users'].sudo().search([('id','=',self.env.uid)])
        for rec in self:
            if rec.state == 'feedback':
                rec.state = 'close'



class TrainingMaterials(models.Model):
    _name = 'training.mat.lines'
    _description = 'EVL Training Materials'
    _rec_name = 'id'

    name = fields.Char(string="Material Name", required=True)
    quantity = fields.Integer(string="Quantity")    
    material_id = fields.Many2one('evl.trainings', string="Material Id")


class TrainingExpenses(models.Model):
    _name = 'training.expense.lines'
    _description = 'EVL Training Expenses'
    _rec_name = 'id'

    name = fields.Char(string="Expense Type", required=True)
    exp_price = fields.Float('Expense')
    expense_id = fields.Many2one('evl.trainings', string="Expense Id")

class FeedbackUsers(models.Model):
    _name = 'feedback.users'
    _description = 'Feedback Users'
    _rec_name = 'id'

    user_id = fields.Many2one('res.users', string="Feedback User", required=True)
    feedback = fields.Char(string="Note")
    feedback_status = fields.Boolean(string="Feedback Status")

    feedback_id = fields.Many2one('evl.trainings', string="Feedback Id")
