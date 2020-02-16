  vals["early_leave_time"] = (
                    att_data.early_leave_time if att_data else None
                )
                vals["late_time_daily"] = att_data.late_time_daily if att_data else None
                vals["movement_id"] = None
                vals["hr_leave_id"] = None

                if movement_data and att_data:
                    remark = "Movement, Attendance"
                    vals["attendance_id"] = att_data.id
                    vals["movement_id"] = [(6, 0, [i.id for i in movement_data])]
                    time_datas = (
                        att_data.mapped("check_in")
                        + att_data.mapped("check_out")
                        + movement_data.mapped("from_time")
                        + movement_data.mapped("to_time")
                    )

                    # import pdb; pdb.set_trace()
                    vals["check_in"] = min(time_datas)
                    vals["check_out"] = max(time_datas)

                elif not movement_data and att_data:
                    remark = "Attendance"
                    vals["attendance_id"] = att_data.id
                    vals["check_in"] = att_data.check_in
                    vals["check_out"] = att_data.check_out

                elif not att_data and movement_data:
                    # import pdb; pdb.set_trace()
                    remark = "Movement"
                    vals["movement_id"] = [(6, 0, [i.id for i in movement_data])]
                    vals["check_in"] = movement_data.from_time
                    vals["check_out"] = movement_data.to_time

                # import pdb; pdb.set_trace()
                for records in (
                    self.env["hr.leave"]
                    .search(
                        [("employee_id", "=", employees.id), ("state", "=", "validate")]
                    )
                    .filtered(
                        lambda r: r.date_from.date() <= vals["record_date"]
                        and r.date_to.date() >= vals["record_date"]
                    )
                ):
                    vals["hr_leave_id"] = records.id
                    if len(remark) > 2:
                        remark += ","
                    remark += " Leave"
                    # import pdb; pdb.set_trace()
                vals["remark"] = remark

                # if not att_data:
                #     if not movement_data:
                #         if vals["hr_leave_id"] == False:
                #             vals["remark"] = "No Records Found"