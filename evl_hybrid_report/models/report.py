from odoo import api, fields, models, _
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
import calendar
from odoo.exceptions import UserError, ValidationError


class evl_hybrid_report(models.Model):
    _inherit = "hr.attendance"
    _order = "record_date desc"

    @api.depends("employee_id")
    def _compute_expected(self):
        for records in self:
            if records.record_date:
                working_lines = records.employee_id.resource_calendar_id.attendance_ids.filtered(
                    lambda r: r.dayofweek == str(records.record_date.weekday())
                )
                if working_lines:
                    records.expected_check_in = min(working_lines.mapped("hour_from"))
                    records.expected_check_out = max(working_lines.mapped("hour_to"))
                    records.is_holiday = False

                else:
                    records.expected_check_in = 0
                    records.expected_check_out = 0
                    records.is_holiday = True

                time_datas = (
                    records.attendance_id.mapped("check_in")
                    + records.attendance_id.mapped("check_out")
                    + records.movement_id.mapped("from_time")
                    + records.movement_id.mapped("to_time")
                )
                if not time_datas:
                    records.check_in = None
                    records.check_out = None
                    records.late_time_daily = None
                    records.early_leave_time = None
                    # return
                else:

                    records.check_in = min(time_datas)
                    records.check_out = max(time_datas)

                    # >>>>>>>>>>>>>>>> computing late and early
                    # adjustedtime
                    check_in = (records.check_in + timedelta(hours=6)).time()
                    check_out = (records.check_out + timedelta(hours=6)).time()

                    emp_check_in = check_in.hour + round(check_in.minute / 60, 2)
                    emp_check_out = check_out.hour + round(check_out.minute / 60, 2)

                    # >>>>>>>>>
                    late_calc = math.modf(
                        round(emp_check_in - records.expected_check_in, 2)
                    )
                    early_leave = math.modf(
                        round(records.expected_check_out - emp_check_out, 2)
                    )
                    # import pdb; pdb.set_trace()

                    

                    records.late_time_daily = (
                        late_calc[1] + late_calc[0]
                        if emp_check_in > records.expected_check_in
                        else 0
                    )
                    records.early_leave_time = (
                        early_leave[1] + early_leave[0]
                        if emp_check_out < records.expected_check_out
                        else 0
                    )
          
    
    
    
    check_in = fields.Datetime(
        string="Check In", required=False
    )

    early_leave_time = fields.Float(string="Early Leave")

    late_time_daily = fields.Float(string="Late Time", compute="_compute_expected")

    remark = fields.Char(string="Remark",)

    movement_id = fields.Many2many(string="Movement", comodel_name="movement.movement",)

    hr_leave_id = fields.Many2one(
        string="Leave", comodel_name="hr.leave", ondelete="restrict",
    )
    attendance_id = fields.Many2one(
        string="Attendance Record", comodel_name="evl.attendance", ondelete="restrict",
    )

    record_date = fields.Date(string="Date")

    expected_check_in = fields.Float(
        string="Expected Check In", compute="_compute_expected", readonly=True,
    )
    expected_check_out = fields.Float(
        string="Expected Check Out", compute="_compute_expected", readonly=True,
    )

    is_holiday = fields.Boolean(string="Holiday",)

    def name_get(self):
        result = []
        for attendance in self:
            if attendance.check_out and attendance.check_in:

                result.append(
                    (
                        attendance.id,
                        _("%(empl_name)s from %(check_in)s to %(check_out)s")
                        % {
                            "empl_name": attendance.employee_id.name,
                            "check_in": fields.Datetime.to_string(
                                fields.Datetime.context_timestamp(
                                    attendance,
                                    fields.Datetime.from_string(attendance.check_in),
                                )
                            ),
                            "check_out": fields.Datetime.to_string(
                                fields.Datetime.context_timestamp(
                                    attendance,
                                    fields.Datetime.from_string(attendance.check_out),
                                )
                            ),
                        },
                    )
                )
        return result

    @api.constrains("check_in", "check_out", "employee_id")
    def _check_validity(self):
        pass

    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def report_action(self):

        date_from = self.search([],order="record_date desc",limit=1).record_date + timedelta(days =1).record_date if self.search([],order="record_date desc",limit=1).record_date + timedelta(days =1) else  datetime.datetime(2020, 1, 1, 0, 0)

        # date_from = datetime.datetime(2020, 1, 1, 0, 0)
        import pdb; pdb.set_trace()
        date_to = datetime.datetime(2020, 1, 10, 0, 0)

        # import pdb; pdb.set_trace()

        for i in range(abs(date_from - date_to).days + 1):

            for employees in self.env["hr.employee"].search(
                [("identification_id", "!=", ""), ("id", "=", 5391)]
            ):
                vals = {}
                vals["record_date"] = date_from.date() + datetime.timedelta(days=i)
                vals["employee_id"] = employees.id

                # >>>>>movement >
                movement_data = (
                    self.env["movement.movement"]
                    .search(
                        [("employee_id", "=", employees.id), ("state", "=", "hradmin")]
                    )
                    .filtered(lambda r: r.from_time.date() == vals["record_date"])
                )

                vals["movement_id"] = [(6, 0, [i.id for i in movement_data])]

                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> >

                # >>>>>attendance >

                att_data = (
                    self.env["evl.attendance"]
                    .search([("employee_id", "=", employees.id)])
                    .filtered(lambda r: r.check_in.date() == vals["record_date"])
                )

                vals["attendance_id"] = att_data.id

                # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> >
                rec = self.env["hr.attendance"].create(vals)
                rec._compute_expected()

