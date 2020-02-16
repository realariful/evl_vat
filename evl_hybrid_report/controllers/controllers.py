# -*- coding: utf-8 -*-
from odoo import http

# class EciAttendanceReport(http.Controller):
#     @http.route('/eci_attendance_report/eci_attendance_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/eci_attendance_report/eci_attendance_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('eci_attendance_report.listing', {
#             'root': '/eci_attendance_report/eci_attendance_report',
#             'objects': http.request.env['eci_attendance_report.eci_attendance_report'].search([]),
#         })

#     @http.route('/eci_attendance_report/eci_attendance_report/objects/<model("eci_attendance_report.eci_attendance_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('eci_attendance_report.object', {
#             'object': obj
#         })