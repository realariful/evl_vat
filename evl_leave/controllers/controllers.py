# -*- coding: utf-8 -*-
# from odoo import http


# class Evlleave(http.Controller):
#     @http.route('/evlleave/evlleave/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/evlleave/evlleave/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('evlleave.listing', {
#             'root': '/evlleave/evlleave',
#             'objects': http.request.env['evlleave.evlleave'].search([]),
#         })

#     @http.route('/evlleave/evlleave/objects/<model("evlleave.evlleave"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('evlleave.object', {
#             'object': obj
#         })
