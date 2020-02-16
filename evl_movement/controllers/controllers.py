# -*- coding: utf-8 -*-
from odoo import http

# class Movement(http.Controller):
#     @http.route('/movement/movement/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/movement/movement/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('movement.listing', {
#             'root': '/movement/movement',
#             'objects': http.request.env['movement.movement'].search([]),
#         })

#     @http.route('/movement/movement/objects/<model("movement.movement"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('movement.object', {
#             'object': obj
#         })