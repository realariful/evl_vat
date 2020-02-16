import datetime
import pdb
from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError
import time
import logging
from datetime import date, timedelta, datetime
import math
import datetime
import calendar
import sys
import requests
import json

def findDay(date):
    born = datetime.datetime.strptime(date, "%d %m %Y").weekday()
    return calendar.day_name[born]


class override_base(models.Model):
    _inherit = "hr.attendance"

    source = fields.Selection([
        ('state1', 'Device'),
        ('state2', 'Movement')

    ],default = 'state1', string='')



# class override_hremployee(models.Model):
#     _inherit = "hr.employee"

#     @api.model
#     def create(self,vals):
#         for rec in self:
#             record = super(override_hremployee, rec).create()
#             return record


class override_ircron(models.Model):
    _inherit = "ir.cron"

    attendance_id = fields.Integer(string='Attendance ID',)
    


class Custom(models.Model):
    _name = "evl.attendance"
    _description = "EVL Attendance"
    _inherit = "hr.attendance"

    early_leave_time = fields.Float(string="Early Leave", store=True)
    late_time_daily = fields.Float(string="Late Time", store=True)
    location = fields.Char(string="Device Location")
    attref_id = fields.Integer(string="Attendance Ref Id")
    validity = fields.Selection([
        ('state0', 'draft'),        
        ('state1', 'Valid'),
        ('state2', 'Invalid')
    ],default = '', string='')   
    bool_late = fields.Boolean(compute="_compute_late",store=True)
    bool_early = fields.Boolean(compute="_compute_early",store=True)
    source = fields.Selection([
        ('state1', 'Device'),
        ('state2', 'Movement')
    ],default = 'state1', string='')

    @api.depends("late_time_daily")
    def _compute_late(self):
        for record in self:
            if record.late_time_daily > 0:
                record.bool_late = True
            else:
                record.bool_late = False

    @api.depends("late_time_daily")
    def _compute_early(self):
        for record in self:
            if record.early_leave_time > 0:
                record.bool_early = True
            else:
                record.bool_early = False  



   #Fuction to Pull Attendance Data From Intermediate Attendance Topten Server
    def pull_data_from_topten(self):
        try:

            #att_id = self.env['ir.cron'].search([('cron_name','=','Pull From Topten Server')]).attendance_id
            att_id = 560000

            url = "http://attendance.topten.ergov.com/device/get_device_data_id"#?att_id=22319
            payload = {'att_id':att_id}
            headers = {'content-type': "application/json"}
            response = requests.request("GET", url, params=payload)
            res_json = json.loads(response.text)
            data_arr = res_json['data']                                      

            for item in data_arr:
                emp_id = self.env['hr.employee'].sudo().search([('identification_id','=',item['identification_id'])],limit=1).id   
                         
                if emp_id:
                    check_attref_id = self.env['evl.attendance'].sudo().search([
                                                ( 'attref_id','=', item['id'])
                                                ])

                    if len(check_attref_id) == 0:
                        vals ={
                            'attref_id' :  item['id'],
                            'employee_id' : emp_id,
                            'check_in' : item['check_in'],
                            'check_out' : item['check_out'],
                            'validity' : item['validity'],
                            'location' : item['location'],
                            'early_leave_time' : item['early_leave_time'],
                            'late_time_daily' : item['late_time_daily'],
                            'attendance_id' :  None,
                            }          
                        record = self.env['evl.attendance'].sudo().create(vals)
                else:
                    pass
        except Exception as e:
            print ("Process terminate : {}".format(e))
            

    # @api.constrains("check_in", "check_out", "employee_id")
    # def _check_validity(self):        
    #     for attendance in self:
    #         # we take the latest attendance before our check_in time and check it doesn't overlap with ours
    #         last_attendance_before_check_in = self.env["attendance.data"].search(
    #             [
    #                 ("employee_id", "=", attendance.employee_id.id),
    #                 ("check_in", "<=", attendance.check_in),
    #                 ("id", "!=", attendance.id),
    #             ],
    #             order="check_in desc",
    #             limit=1,
    #         )
    #         if (
    #             last_attendance_before_check_in
    #             and last_attendance_before_check_in.check_out
    #             and last_attendance_before_check_in.check_out > attendance.check_in
    #         ):
    #             pass
               
    #         if not attendance.check_out:
    #             # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
    #             no_check_out_attendances = self.env["attendance.data"].search(
    #                 [
    #                     ("employee_id", "=", attendance.employee_id.id),
    #                     ("check_out", "=", False),
    #                     ("id", "!=", attendance.id),
    #                 ],
    #                 order="check_in desc",
    #                 limit=1,
    #             )
    #             if no_check_out_attendances:

    #                 pass
    #         else:                
    #             last_attendance_before_check_out = self.env["attendance.data"].search(
    #                 [
    #                     ("employee_id", "=", attendance.employee_id.id),
    #                     ("check_in", "<", attendance.check_out),
    #                     ("id", "!=", attendance.id),
    #                 ],
    #                 order="check_in desc",
    #                 limit=1,
    #             )
    #             if (
    #                 last_attendance_before_check_out
    #                 and last_attendance_before_check_in
    #                 != last_attendance_before_check_out
    #             ):
    #                 pass



    # early_leave_time = fields.Char(string="Early Leave", compute="_compute_early_time", store=True)
    # late_time_daily = fields.Char(string="Late Time", compute="_compute_late_time", store=True)
    # def update_in_device(self,company_id,location):

    #     devices = self.env['device.config'].search(['&','&',('company_id','=',company_id),('location','=',location)])
    #     ip_address = self.env['ir.config_parameter'].search([('key', '=', 'evl_attendance.ip_addr')]).value
    #     port_number = self.env['ir.config_parameter'].search([('key', '=', 'evl_attendance.port')]).value
    #     zk = ZK(ip_address, port=int(port_number))
    #     conn = zk.connect()

    #     users = conn.get_users()
    #     devExistingUsers = [i.name for i in users]
    #     new_users_to_be_updated = self.env['hr.employee'].search([('name','not in',devExistingUsers)])
    #     # import pdb; pdb.set_trace()

    #     for users in new_users_to_be_updated:
    #         if users.identification_id:
    #             # import pdb; pdb.set_trace()
    #             try:
    #                 conn.set_user(name=str(users.name), privilege=const.USER_DEFAULT, password='12345678', user_id=users.identification_id)
    #             except Exception as e:
    #                 print ("Process terminate : {}".format(e))


     
       

    # @api.depends("check_in", "check_out")
    # def _compute_late_time(self):
    #     for rec in self:
    #         select = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}
    #         #print("_compute_late_time")
    #         #import pdb; pdb.set_trace()
    #         date = (str(rec.check_in.day)+ " " + str(rec.check_in.month)+ " " + str(rec.check_in.year))
    #         day_of_week = str(select[findDay(date)])
    #         #print(date,day_of_week)
    #         #import pdb; pdb.set_trace()

    #         for x in rec.employee_id.resource_calendar_id.attendance_ids.filtered(lambda r: r.dayofweek == day_of_week):
    #             #import pdb; pdb.set_trace()            
    #             emp_check_in_hour = rec.check_in.hour + 6
    #             emp_check_in_minute = round(rec.check_in.minute/60,2)
    #             emp_check_in = emp_check_in_hour + emp_check_in_minute

    #             #print(emp_check_in_hour,emp_check_in_minute,emp_check_in)
    #             #import pdb; pdb.set_trace()

    #             if emp_check_in > x.hour_from:
    #                 late_calc = math.modf(round(emp_check_in - x.hour_from,2))
                    
    #                 rec.late_time_daily = late_calc[1] + late_calc[0]

    #             else:
    #                 rec.late_time_daily = 0
                       
           
            

    # @api.depends("check_in", "check_out")
    # def _compute_early_time(self):
    #     for rec in self:
    #         #print("_compute_early_time")
    #         select = {'Monday':0,'Tuesday':1,'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}
    #         date = (str(rec.check_out.day)+ " " + str(rec.check_out.month)+ " " + str(rec.check_out.year))
    #         day_of_week = str(select[findDay(date)])
    #         # self.early_leave_time = 1.5
    #         # return
    #         # import pdb; pdb.set_trace()

    #         for x in rec.employee_id.resource_calendar_id.attendance_ids.filtered(lambda r: r.dayofweek == day_of_week):            
    #             emp_check_out_hour = rec.check_out.hour + 6
    #             emp_check_out_minute = round(rec.check_out.minute/60,2)
    #             emp_check_out = emp_check_out_hour + emp_check_out_minute
                
    #             # import pdb; pdb.set_trace()
    #             if emp_check_out < x.hour_to:
    #                 late_calc = math.modf(round(x.hour_to - emp_check_out,2))

    #                 # import pdb; pdb.set_trace()  

    #                 if late_calc[1] != 0 :                                 
    #                     rec.early_leave_time = late_calc[1] + late_calc[0]
    #                 else:                                
    #                     rec.early_leave_time = late_calc[0]
    #             else:
    #                 rec.early_leave_time = 0
