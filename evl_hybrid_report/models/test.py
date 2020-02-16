 # def write(self, values):
    #     """
    #         Update all record(s) in recordset, with new value comes as {values}
    #         return True on success, False otherwise

    #         @param values: dict of new values to be set

    #         @return: True on success, False otherwise
    #     """

    #     result = super(evl_hybrid_report, self).write(values)

    #     return result

    # @api.model
    # def create(self, values):
    #     """
    #         Create a new record for a model ModelName
    #         @param values: provides a data for new record

    #         @return: returns a id of new record
    #     """

    #     if  'attendance_id' in values:
    #             if self.env['hr.employee'].search([('id', '=', values['employee_id'])]).resource_calendar_id:
    #                 record = self.env['hr.employee'].search([('id', '=', values['employee_id'])]).resource_calendar_id.attendance_ids.filtered(lambda r: r.dayofweek == str(values['record_date'].weekday()))

    #                 if record:
    #                     from_time  = min(record.mapped('hour_from'))
    #                     to_time = max(record.mapped('hour_to'))

    #                     f_from_time = datetime.time(int(math.modf(from_time)[1]),int(math.modf(from_time)[0]*60),0)
    #                     f_to_time = datetime.time(int(math.modf(to_time)[1]),int(math.modf(to_time)[0]*60))

    #                     check_in =  ( values['check_in'] + timedelta(hours =6 )).time()
    #                     check_out =  ( values['check_out'] + timedelta(hours =6 )).time()

    #                     # >>>>>>>>>

    #                     emp_check_in_hour = check_in.hour
    #                     emp_check_in_minute = round(check_in.minute/60,2)
    #                     emp_check_in = emp_check_in_hour + emp_check_in_minute

    #                     if emp_check_in >from_time:
    #                         late_calc = math.modf(round(emp_check_in - from_time,2))

    #                         values['late_time_daily']  = late_calc[1] + late_calc[0]

    #                     else:
    #                         values['late_time_daily']  = 0

    #                     # >>>>>>>>>
    #                     emp_check_out_hour = check_out.hour
    #                     emp_check_out_minute = round(check_out.minute/60,2)
    #                     emp_check_out = emp_check_out_hour + emp_check_out_minute

    #                     if emp_check_out < to_time:
    #                         late_calc = math.modf(round(to_time - emp_check_out,2))

    #                         if late_calc[1] != 0 :
    #                             values['early_leave_time']  = late_calc[1] + late_calc[0]
    #                         else:
    #                             values['early_leave_time']  = late_calc[0]
    #                     else:
    #                         values['early_leave_time']  = 0

    #     result = super(evl_hybrid_report, self).create(values)

    #     return result



    
 
 
 if  'attendance_id' in values:
                if self.env['hr.employee'].search([('id', '=', values['employee_id'])]).resource_calendar_id:
                    record = self.env['hr.employee'].search([('id', '=', values['employee_id'])]).resource_calendar_id.attendance_ids.filtered(lambda r: r.dayofweek == str(values['record_date'].weekday()))

                    if record:
                        from_time  = min(record.mapped('hour_from'))
                        to_time = max(record.mapped('hour_to'))

                        f_from_time = datetime.time(int(math.modf(from_time)[1]),int(math.modf(from_time)[0]*60),0)
                        f_to_time = datetime.time(int(math.modf(to_time)[1]),int(math.modf(to_time)[0]*60))

                        check_in =  ( values['check_in'] + timedelta(hours =6 )).time()
                        check_out =  ( values['check_out'] + timedelta(hours =6 )).time()

                        # >>>>>>>>>

                        emp_check_in_hour = check_in.hour
                        emp_check_in_minute = round(check_in.minute/60,2)
                        emp_check_in = emp_check_in_hour + emp_check_in_minute

                        if emp_check_in >from_time:
                            late_calc = math.modf(round(emp_check_in - from_time,2))

                            values['late_time_daily']  = late_calc[1] + late_calc[0]

                        else:
                            values['late_time_daily']  = 0

                        # >>>>>>>>>
                        emp_check_out_hour = check_out.hour
                        emp_check_out_minute = round(check_out.minute/60,2)
                        emp_check_out = emp_check_out_hour + emp_check_out_minute

                        if emp_check_out < to_time:
                            late_calc = math.modf(round(to_time - emp_check_out,2))

                            if late_calc[1] != 0 :
                                values['early_leave_time']  = late_calc[1] + late_calc[0]
                            else:
                                values['early_leave_time']  = late_calc[0]
                        else:
                            values['early_leave_time']  = 0

        result = super(evl_hybrid_report, self).create(values)
