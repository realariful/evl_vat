# -*- coding: utf-8 -*-

import logging
import math

from collections import namedtuple

from datetime import datetime, time
from pytz import timezone, UTC

from odoo import api, fields, models, SUPERUSER_ID, tools
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

DummyAttendance = namedtuple('DummyAttendance', 'hour_from, hour_to, dayofweek, day_period, week_type')


from collections import defaultdict
from pytz import utc

# #----------------------------
def timezone_datetime(time):
    if not time.tzinfo:
        time = time.replace(tzinfo=utc)
    return time
# #----------------------------


class HolidaysRequestInherit(models.Model):
    _inherit = "hr.leave"  


    # #----------------------------

    def _get_work_days_data(self, from_datetime, to_datetime, compute_leaves=True, calendar=None, domain=None):
        print(from_datetime,to_datetime)
        print("_get_work_days_data")
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        from_datetime = timezone_datetime(from_datetime)
        to_datetime = timezone_datetime(to_datetime)
        print(from_datetime,to_datetime)
        

        day_total = calendar._get_day_total(from_datetime, to_datetime, resource)

        # actual hours per day
        if compute_leaves:
            intervals = calendar._work_intervals(from_datetime, to_datetime, resource, domain)
        else:
            intervals = calendar._attendance_intervals(from_datetime, to_datetime, resource)

        #print("Interval: ",calendar._get_days_data(intervals, day_total))
        return calendar._get_days_data(intervals, day_total)

    def _get_number_of_days(self, date_from, date_to, employee_id):
        print("holiday_status_id",self.holiday_status_id)
        """ Returns a float equals to the timedelta between two dates given as string."""
        if employee_id:
            employee = self.env['hr.employee'].browse(employee_id)   
            resource_cal = self.env['hr.employee'].search([('id','=',employee_id)]).resource_calendar_id

            holiday_from_status = True
            holiday_to_status  = True

            # from datetime import date, timedelta

            # sdate = date_from   # start date
            # edate = date_to   # end date

            # delta = edate - sdate       # as timedelta
            # print("=============")
            # l_req=[]
            # for i in range(delta.days + 1):
            #     day = (sdate + timedelta(days=i)).weekday()
            #     l_req.append(day)
            #     print(day)
            # print("=============")
            # for d in l_req:
            #     for day in resource_cal.attendance_ids:
            #         if int(d) == int(day.dayofweek):
            #             print(int(d) == int(day.dayofweek))
            #             holiday_from_status = False
            #             #raise ValidationError(_('Your Leave selection is on a holiday. Please select another date.'))
               
            # for day in resource_cal.attendance_ids:
            #     if int(date_from.weekday()) == int(day.dayofweek) and date_from.hour >= day.hour_from and date_from.hour <= day.hour_to:
            #         holiday_from_status = False
            #     if int(date_to.weekday()) == int(day.dayofweek)and date_to.hour >= day.hour_from and date_to.hour <= day.hour_to:
            #         holiday_to_status = False
            
            # global_holoday_status = True
            # for dates in resource_cal.global_leave_ids:
            #     if date_from.date() >= dates.date_from.date() and date_from.date() <= dates.date_to.date():
            #         global_holoday_status = False
            #     if date_to.date() >= dates.date_from.date() and date_to.date() <= dates.date_to.date():
            #         global_holoday_status = False

            
            # if global_holoday_status == False:
            #     raise ValidationError(_('Your Leave selection is on a global holiday. Please select another date.'))
 
            # if holiday_from_status == True:
            #         raise ValidationError(_('Your Leave starting date selection is on a holiday. Please select another date.'))
            # if holiday_to_status == True:
            #         raise ValidationError(_('Your Leave ending date selection is on a holiday. Please select another date.'))
                  
            # status = self.holiday_status_id.request_unit

            # if status == 'day' and self.request_unit_half == False:
            #     leave_time = employee._get_work_days_data(date_from, date_to)

            #     if leave_time['days'] - round(leave_time['days']) == 0.25 or 0.33:
            #         leave_time['days'] = round(leave_time['days']) + 1
            #         return leave_time


            return employee._get_work_days_data(date_from, date_to)

        today_hours = self.env.company.resource_calendar_id.get_work_hours_count(
            datetime.combine(date_from.date(), time.min),
            datetime.combine(date_from.date(), time.max),
            False)

        hours = self.env.company.resource_calendar_id.get_work_hours_count(date_from, date_to)
        return {'days': hours / (today_hours or HOURS_PER_DAY), 'hours': hours}

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_leave_dates(self):        
        if self.date_from and self.date_to:
            self.number_of_days = self._get_number_of_days(self.date_from, self.date_to, self.employee_id.id)['days']
        else:
            self.number_of_days = 0



    # #----------------------------



    date_from = fields.Datetime(
        'Start Date', readonly=True, index=True, copy=False, required=True, 
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, tracking=True)
    date_to = fields.Datetime(
        'End Date', readonly=True, copy=False, required=True, 
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, tracking=True)

    yes = fields.Boolean(string='Attach Documents')
    attachment= fields.Many2many(comodel_name="ir.attachment", 
                                column1="m2m_id",
                                column2="attachment_id",
                                string="Attachments")


    state = fields.Selection([
    ('draft', 'To Submit'),
    ('cancel', 'Cancelled'),
    ('confirm', 'Confirm'),
    ('refuse', 'Refused'),
    ('validate1', 'First Approval'),
    ('validate2', 'Second Approval'),
    ('validate', 'Approved')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft')

    third_approver_id = fields.Many2one(
        'hr.employee', string='Third Approval', readonly=True, copy=False,
        help='This area is automatically filled by the user who validate the leave with third level (If leave type need third validation)')
    
    logged_user = fields.Many2one('res.users', string='Current User',  default=lambda self: self.env.uid)  
                
    def _check_triple_validation_rules(self, employees, state):
        if self.user_has_groups('hr_holidays.group_hr_holidays_manager'):
            return

        is_leave_user = self.user_has_groups('hr_holidays.group_hr_holidays_user')
        if state == 'validate1':
            employees = employees.filtered(lambda employee: employee.leave_manager_id != self.env.user)
            if employees and not is_leave_user:
                raise AccessError(_('You cannot first approve a leave for %s, because you are not his leave manager' % (employees[0].name,)))
        elif state == 'validate' and not is_leave_user:
            # Is probably handled via ir.rule
            raise AccessError(_('You don\'t have the rights to apply second approval on a leave request'))
        elif state == 'validate2' and not is_leave_user:
            # Is probably handled via ir.rule
            raise AccessError(_('You don\'t have the rights to apply third approval on a leave request'))
  
    #-----------------------------------------------------------------------------

    
    first_approver = fields.Boolean(compute='first_approval',default=False)
    @api.depends('employee_id')    
    def first_approval(self):
        for az in self:
            print(self.env['res.users'])
            if self.env.user.user_has_groups('hr_holidays.group_hr_holidays_manager') or self.env.user.has_group('evl_leave.group_evl_leave_manager') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1) == self.employee_id.parent_id:
                az.sudo().first_approver = True
            else:
                az.sudo().first_approver = False
        if self.state == 'validate2' or self.state == 'validate' :
            az.sudo().first_approver = False

        employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.user_id.id)], limit=1)
        loginuser = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        if employee.id == loginuser.id:
            print("-->user_id is same as logged_user")
            az.sudo().first_approver = False   
        if employee.department_id.manager_id.id == loginuser.id:
            print("Manager id is same as logged_user")
            az.sudo().first_approver = False   
        if employee.parent_id.id == loginuser.id and employee.department_id.manager_id.id == loginuser.id:
            az.sudo().first_approver = True 

    second_approver = fields.Boolean(compute='second_approval',default=False)
    @api.depends('employee_id','department_id')    
    def second_approval(self):
        for az in self:
            if self.state == 'validate1':
                if self.env.user.user_has_groups('hr_holidays.group_hr_holidays_manager') or (self.env.user.has_group('evl_leave.group_evl_leave_manager') and self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1).id == self.employee_id.department_id.manager_id.id):
                    az.sudo().second_approver = True
                else:
                    az.sudo().second_approver = False                         
            else:
                az.sudo().second_approver = False                     
                # if self.state == 'validate1' or self.state == 'validate2':
                #     az.sudo().second_approver = False



    final_approver = fields.Boolean(compute='final_approval')
    @api.depends('employee_id', 'department_id')
    def final_approval(self):
        for az in self:
            if (self.env.user.user_has_groups('hr_holidays.group_hr_holidays_manager') or (self.env.user.has_group('leave.hr_group') == self.env.user.id or  self.holiday_status_id.responsible_id.id  == self.env.user.id)) and self.state == 'validate2':
                az.sudo().final_approver = True                   
            else:                
                az.sudo().final_approver = False      
            print(az.final_approver)


    def activity_update(self):
        print('activity_update')
        to_clean, to_do = self.env['hr.leave'], self.env['hr.leave']
        for holiday in self:
            note = _('New %s Request created by %s from %s to %s') % (holiday.holiday_status_id.name, holiday.create_uid.name, fields.Datetime.to_string(holiday.date_from), fields.Datetime.to_string(holiday.date_to))

            if holiday.state == 'draft':
                    to_clean |= holiday
            elif holiday.state == 'confirm':
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
            elif holiday.state == 'validate1':
                #print("activity_feedback")               

                holiday.activity_feedback(['hr_holidays.mail_act_leave_approval'])
                #import pdb; pdb.set_trace()
                print("----------")
                holiday.activity_schedule(
                    'hr_holidays.mail_act_leave_second_approval',
                    note=note,
                    user_id=holiday.sudo()._get_responsible_for_approval().id or self.env.user.id)
                print("validate1 error none")
                #import pdb; pdb.set_trace()

            elif holiday.state == 'validate':
                to_do |= holiday
            elif holiday.state == 'refuse':
                to_clean |= holiday
        if to_clean:
            to_clean.activity_unlink(['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])
        if to_do:
            to_do.activity_feedback(['hr_holidays.mail_act_leave_approval', 'hr_holidays.mail_act_leave_second_approval'])



    def activity_feedback(self, act_type_xmlids, user_id=None, feedback=None):
        """ Set activities as done, limiting to some activity types and
        optionally to a given user. """
        if self.env.context.get('mail_activity_automation_skip'):
            return False
        Data = self.env['ir.model.data'].sudo()
        activity_types_ids = [Data.xmlid_to_res_id(xmlid) for xmlid in act_type_xmlids]
        domain = [
            '&', '&', '&',
            ('res_model', '=', self._name),
            ('res_id', 'in', self.ids),
            ('automated', '=', True),
            ('activity_type_id', 'in', activity_types_ids)
        ]
        if user_id:
            domain = ['&'] + domain + [('user_id', '=', user_id)] 
        activities = self.env['mail.activity'].sudo().search(domain)
        if activities:
            activities.action_feedback(feedback=feedback)
        return True


    def action_draft(self):
        if any(holiday.state not in ['confirm', 'refuse'] for holiday in self):
            raise UserError(_('Leave request state must be "Refused" or "To Approve" in order to be reset to draft.'))
        self.write({
            'state': 'draft',
            'first_approver_id': False,
            'second_approver_id': False,
            'third_approver_id': False,
                    })
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_draft()
            linked_requests.unlink()
        self.activity_update()
        return True

    def action_confirm(self):
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError(_('Leave request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm'})
        self.activity_update()
        return True


    def action_approve(self): 
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})
        self.filtered(lambda hol: hol.validation_type == 'triple').write({'state': 'validate1', 'first_approver_id': current_employee.id})
        # Post a second message, more verbose than the tracking message
        for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
            holiday.message_post(
                body=_('Your %s planned on %s has been accepted' % (holiday.holiday_status_id.display_name, holiday.date_from)),
                partner_ids=holiday.employee_id.user_id.partner_id.ids)

        if self.validation_type == 'both':
            self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
            if not self.env.context.get('leave_fast_create'):
                self.activity_update()
            return True
        elif self.validation_type == 'triple':
            #Getting multi company error here
            self.filtered(lambda hol: not hol.validation_type == 'triple').action_validate()
            if not self.env.context.get('leave_fast_create'):
                self.activity_update()
            return True

    
    def action_validate(self):
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if any(holiday.state not in ['confirm', 'validate1', 'validate2'] for holiday in self):
            raise UserError(_('Leave request must be confirmed in order to approve it.'))

        if self.validation_type == 'triple':
            if self.state == 'validate2':
                self.write({'state': 'validate'})
                self.filtered(lambda holiday: holiday.validation_type == 'triple' and holiday.state=='validate').write({'third_approver_id': current_employee.id})
                self.filtered(lambda holiday: holiday.validation_type == 'triple' and holiday.state=='validate2').write({'second_approver_id': current_employee.id})
                self.filtered(lambda holiday: holiday.validation_type == 'triple' and holiday.state=='validate1').write({'first_approver_id': current_employee.id})

                for holiday in self.filtered(lambda holiday: holiday.holiday_type != 'employee'):
                    if holiday.holiday_type == 'category':
                        employees = holiday.category_id.employee_ids
                    elif holiday.holiday_type == 'company':
                        employees = self.env['hr.employee'].search([('company_id', '=', holiday.mode_company_id.id)])
                    else:
                        employees = holiday.department_id.member_ids

                    if self.env['hr.leave'].search_count([('date_from', '<=', holiday.date_to), ('date_to', '>', holiday.date_from),
                                    ('state', 'not in', ['cancel', 'refuse']), ('holiday_type', '=', 'employee'),
                                    ('employee_id', 'in', employees.ids)]):
                        raise ValidationError(_('You can not have 2 leaves that overlaps on the same day.'))

                    values = [holiday._prepare_holiday_values(employee) for employee in employees]
                    leaves = self.env['hr.leave'].with_context(
                        tracking_disable=True,
                        mail_activity_automation_skip=True,
                        leave_fast_create=True,
                    ).create(values)
                    leaves.action_approve()
                    # FIXME RLi: This does not make sense, only the parent should be in validation_type both
                    if leaves and leaves[0].validation_type == 'triple':
                        leaves.action_validate()
                employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
                employee_requests._validate_leave_request()
                if not self.env.context.get('leave_fast_create'):
                    employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
                # if len(self.second_approver_id) != 0: 
                #     second_approver = True
                return True
        
        elif self.validation_type == 'both':
            self.write({'state': 'validate'})
            self.filtered(lambda holiday: holiday.validation_type == 'both').write({'second_approver_id': current_employee.id})
            self.filtered(lambda holiday: holiday.validation_type != 'both' or 'triple').write({'first_approver_id': current_employee.id})

            for holiday in self.filtered(lambda holiday: holiday.holiday_type != 'employee'):
                if holiday.holiday_type == 'category':
                    employees = holiday.category_id.employee_ids
                elif holiday.holiday_type == 'company':
                    employees = self.env['hr.employee'].search([('company_id', '=', holiday.mode_company_id.id)])
                else:
                    employees = holiday.department_id.member_ids

                if self.env['hr.leave'].search_count([('date_from', '<=', holiday.date_to), ('date_to', '>', holiday.date_from),
                                ('state', 'not in', ['cancel', 'refuse']), ('holiday_type', '=', 'employee'),
                                ('employee_id', 'in', employees.ids)]):
                    raise ValidationError(_('You can not have 2 leaves that overlaps on the same day.'))

                values = [holiday._prepare_holiday_values(employee) for employee in employees]
                leaves = self.env['hr.leave'].with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True,
                ).create(values)
                leaves.action_approve()
                # FIXME RLi: This does not make sense, only the parent should be in validation_type both
                if leaves and leaves[0].validation_type == 'both':
                    leaves.action_validate()
            employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
            employee_requests._validate_leave_request()
            if not self.env.context.get('leave_fast_create'):
                employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
            return True


    def action_validate2(self):       
        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)


        if any(holiday.state not in ['confirm', 'validate1', 'validate2'] for holiday in self):
            raise UserError(_('Leave request must be confirmed in order to approve it.'))
        if self.validation_type == 'triple':
            if self.state == 'validate1':
                self.write({'state': 'validate2'})
                self.filtered(lambda holiday: holiday.validation_type == 'triple' and holiday.state=='validate2').write({'second_approver_id': current_employee.id})
                for holiday in self.filtered(lambda holiday: holiday.holiday_type != 'employee'):
                    if holiday.holiday_type == 'category':
                        employees = holiday.category_id.employee_ids
                        #import pdb; pdb.set_trace()

                    elif holiday.holiday_type == 'company':
                        employees = self.env['hr.employee'].search([('company_id', '=', holiday.mode_company_id.id)])
                    else:
                        employees = holiday.department_id.member_ids

                    if self.env['hr.leave'].search_count([('date_from', '<=', holiday.date_to), ('date_to', '>', holiday.date_from),
                                    ('state', 'not in', ['cancel', 'refuse']), ('holiday_type', '=', 'employee'),
                                    ('employee_id', 'in', employees.ids)]):
                        raise ValidationError(_('You can not have 2 leaves that overlaps on the same day.'))

                    values = [holiday._prepare_holiday_values(employee) for employee in employees]
                    leaves = self.env['hr.leave'].with_context(
                        tracking_disable=True,
                        mail_activity_automation_skip=True,
                        leave_fast_create=True,
                    ).create(values)
                    leaves.action_approve()
                    # FIXME RLi: This does not make sense, only the parent should be in validation_type both
                    if leaves and leaves[0].validation_type == 'triple':
                        leaves.action_validate()            
                
                employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
                employee_requests._validate_leave_request()
                if not self.env.context.get('leave_fast_create'):
                    employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
                return True

        #--------------------------------------------

        elif self.validation_type == 'both':
            self.write({'state': 'validate'})
            self.filtered(lambda holiday: holiday.validation_type == 'both').write({'second_approver_id': current_employee.id})
            self.filtered(lambda holiday: holiday.validation_type != 'both' or 'triple').write({'first_approver_id': current_employee.id})

            for holiday in self.filtered(lambda holiday: holiday.holiday_type != 'employee'):
                if holiday.holiday_type == 'category':
                    employees = holiday.category_id.employee_ids
                elif holiday.holiday_type == 'company':
                    employees = self.env['hr.employee'].search([('company_id', '=', holiday.mode_company_id.id)])
                else:
                    employees = holiday.department_id.member_ids

                if self.env['hr.leave'].search_count([('date_from', '<=', holiday.date_to), ('date_to', '>', holiday.date_from),
                                ('state', 'not in', ['cancel', 'refuse']), ('holiday_type', '=', 'employee'),
                                ('employee_id', 'in', employees.ids)]):
                    raise ValidationError(_('You can not have 2 leaves that overlaps on the same day.'))

                values = [holiday._prepare_holiday_values(employee) for employee in employees]
                leaves = self.env['hr.leave'].with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True,
                ).create(values)
                leaves.action_approve()
                # FIXME RLi: This does not make sense, only the parent should be in validation_type both
                if leaves and leaves[0].validation_type == 'both':
                    leaves.action_validate()
            employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
            employee_requests._validate_leave_request()
            if not self.env.context.get('leave_fast_create'):
                employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
            return True


    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return

        current_employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        is_officer = self.env.user.has_group('hr_holidays.group_hr_holidays_user')
        is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        
        #import pdb; pdb.set_trace()
        for holiday in self:
            val_type = holiday.holiday_status_id.validation_type

            if not is_manager and state != 'confirm':
                if state == 'draft':
                    if holiday.state == 'refuse':
                        raise UserError(_('Only a Leave Manager can reset a refused leave.'))
                    if holiday.date_from.date() <= fields.Date.today():
                        raise UserError(_('Only a Leave Manager can reset a started leave.'))
                    if holiday.employee_id != current_employee:
                        raise UserError(_('Only a Leave Manager can reset other people leaves.'))
                else:
                    if val_type == 'no_validation' and current_employee == holiday.employee_id:
                        continue
                    # use ir.rule based first access check: department, members, ... (see security.xml)
                    holiday.check_access_rule('write')

                    # This handles states validate1 validate and refuse
                    if holiday.employee_id == current_employee:
                        raise UserError(_('Only a Leave Manager can approve/refuse its own requests.'))

                    if (state == 'validate1' and val_type == 'both') or (state == 'validate' and val_type == 'manager') and holiday.holiday_type == 'employee':
                        if not is_officer and self.env.user != holiday.employee_id.leave_manager_id:
                            raise UserError(_('You must be either %s\'s manager or Leave manager to approve this leave') % (holiday.employee_id.name))

    