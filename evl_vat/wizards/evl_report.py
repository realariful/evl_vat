#-*- coding: utf-8 -*-


from odoo import models, fields, api

class ReportMushak43(models.Model):
    _name = 'mushak.inputoutput'
    _description = 'Mushak 4.3 (Input-Output Coefficient)'
    _rec_name = 'product_id'
    
    
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company',         
        default=lambda self: self.env.user.company_id
    )
    start_date = fields.Date.today()
    
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), ('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        required=True, check_company=True,
        )
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    

    bom_code = fields.Many2one(
        'mrp.bom', 'Bill of Material',
        domain="""[
        '&',
            '|',
                ('company_id', '=', False),
                ('company_id', '=', company_id),
            '&',
                '|',
                    ('product_id','=',product_id),
                    '&',
                        ('product_tmpl_id.product_variant_ids','=',product_id),
                        ('product_id','=',False),
        ('type', '=', 'normal')]""",
        check_company=True,
        help="Bill of Materials allow you to define the list of required components to make a finished product.")
  

    def print_report(self):
        data = {
            'model':'mushak.inputoutput',
            'form': self.read()[0]
        }

        app_vals = []
        vals = {
            'product_id' : data['form']['product_id'][1],
            'bom_code': data['form']['bom_code']
        }
        app_vals.append(vals)
        data['docs'] = app_vals
        headers=[{
                    'name': self.company_id.name,
                    'street': self.company_id.street,
                    'street2': self.company_id.street2,
                    'zip': self.company_id.zip,
                    'vat':self.company_id.vat,
                    'date': self.start_date
                }]
        
        bom_product = self.env['product.template'].search([('id','=',data['form']['product_id'][0])])
 
        bom_product = {
            'serial_number': 1,
            'hscode': bom_product.default_code.hscode,
            'name': bom_product.name,
            'uom': bom_product.uom_id.name,
        }

        bom_lines = []
        #import pdb; pdb.set_trace()
        # print(bom_product.bill_of_cost)

        bom_line_ids = self.env['mrp.bom'].search([('id','=',data['form']['bom_code'][0])]).bom_line_ids

        #----------------
        bom_code_n = data['form']['bom_code'][0]
        bill_of_cost = self.env['mrp.bom'].search([('id','=',bom_code_n)]).bill_of_cost

        # for item in bill_of_cost:
        #     print(item.cost,item.cost)


        test_lines = []
        # print(len(bom_line_ids),len(bill_of_cost))

        # if len(bill_of_cost) > len(bom_line_ids):
        for i in range(0,len(bom_line_ids)):
            print(i)

            pro = {}
            pro['product_name'] = bom_line_ids[i].product_id.name or ""
            pro['hscode'] = self.env['product.template'].search([('id','=',bom_line_ids[i].product_id.id)]).default_code.hscode or ""
            pro['product_qty'] = bom_line_ids[i].product_qty or ""
            pro['waste_qty'] = bom_line_ids[i].waste_qty or "N/A"
            pro['waster_per'] = bom_line_ids[i].waste_per or "N/A"
            pro['product_uom_id'] = bom_line_ids[i].product_uom_id.name or "N/A"
            pro['lst_price'] = "{0:.2f}".format(round(bom_line_ids[i].standard_price,2)) or "N/A"
            
            if i+1 >len(bill_of_cost):
                print("bill_of_cost > bom_line_ids") 

                pro['name'] = ""
                pro['cost'] = "" 
            else:
                pro['name'] = bill_of_cost[i].name or ""
                pro['cost'] = "{0:.2f}".format(round(bill_of_cost[i].cost,2))  or ""
            # else:
            #     pro['name'] = ""

            #     pro['cost'] = ""                
            test_lines.append(pro)  
          
        #print(test_lines) 
        #import pdb; pdb.set_trace()           

        #---------------
        # bill_of_cost = self.env['mrp.bom.costs'].search([('id','=',data['form']['bom_code'][0])]).bom_line_ids
        # print(bill_of_cost)

        if bom_line_ids:
            for product in bom_line_ids:
                pro = {
                    'product_name' : product.product_id.name,
                    'hscode': self.env['product.template'].search([('id','=',product.product_id.id)]).default_code.hscode,
                    'product_qty': product.product_qty,
                    'waste_qty': product.waste_qty,
                    'waster_per': product.waste_per,
                    'product_uom_id': product.product_uom_id.name,
                    'lst_price': round(product.product_id.lst_price,2),
                }
                bom_lines.append(pro)
          

        data['headers'] = headers
        data['bom_product'] = bom_product
        data['bom_lines'] = test_lines
        print("data---->")
        print(data)
        return self.env.ref('evl_vat.report_mushak_input_output').report_action(self, data=data)
       


class ReportMushak61(models.Model):
    _name = 'mushak.purchase'
    _description = 'Mushak 6.1 (Purchase Book)'

    month = fields.Datetime(string='Month')

   
    company_id = fields.Many2one(
        string='Company', 
        comodel_name='res.company',         
        default=lambda self: self.env.user.company_id
    )
    #start_date = fields.Date.today()
    
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), ('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        required=True, check_company=True,
        )
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    

    # bom_code = fields.Many2one(
    #     'mrp.bom', 'Bill of Material',
    #     domain="""[
    #     '&',
    #         '|',
    #             ('company_id', '=', False),
    #             ('company_id', '=', company_id),
    #         '&',
    #             '|',
    #                 ('product_id','=',product_id),
    #                 '&',
    #                     ('product_tmpl_id.product_variant_ids','=',product_id),
    #                     ('product_id','=',False),
    #     ('type', '=', 'normal')]""",
    #     check_company=True,
    #     help="Bill of Materials allow you to define the list of required components to make a finished product.")
  

    def print_report(self):
        data = {
            'model':'mushak.purchase',
            'form': self.read()[0]
        }

        app_vals = []
        vals = {
            'product_id' : data['form']['product_id'][1],
            'bom_code': data['form']['bom_code']
        }
        app_vals.append(vals)
        data['docs'] = app_vals
        headers=[{
                    'name': self.company_id.name,
                    'street': self.company_id.street,
                    'street2': self.company_id.street2,
                    'zip': self.company_id.zip,
                    'vat':self.company_id.vat,
                    'date': self.start_date
                }]
        
        bom_product = self.env['product.template'].search([('id','=',data['form']['product_id'][0])])
        bom_product = {
            'serial_number': 1,
            'hscode': bom_product.default_code.hscode,
            'name': bom_product.name,
            'uom': bom_product.uom_id.name,
        }

        bom_lines = []
        #import pdb; pdb.set_trace()
        bom_line_ids = self.env['mrp.bom'].search([('id','=',data['form']['bom_code'][0])]).bom_line_ids
        if bom_line_ids:
            for product in bom_line_ids:
                print("Product")
                # print(product.product_id.name,product.product_id.default_code,product.product_qty)
                # print(product.product_uom_id.name, product.product_id.lst_price)
                print("------------")
                #import pdb; pdb.set_trace()
                # waster_qty = 0
                # waster_per = round((waster_qty/product.product_qty)*100)
                pro = {
                    'product_name' : product.product_id.name,
                    'hscode': self.env['product.template'].search([('id','=',product.product_id.id)]).default_code.hscode,
                    'product_qty': product.product_qty,
                    'waste_qty': product.waste_qty,
                    'waster_per': product.waste_per,
                    'product_uom_id': product.product_uom_id.name,
                    'lst_price': product.product_id.standard_price,
                }
                bom_lines.append(pro)
          

        data['headers'] = headers
        data['bom_product'] = bom_product
        data['bom_lines'] = bom_lines
        print("data---->")
        print(data)
        return self.env.ref('evl_vat.report_mushak_input_output').report_action(self, data=data)
       

    # #--------------------------------------
    # @api.onchange('company_id')
    # def _onchange_company_id(self):
    #     if self.company_id:
    #         pass
    #         # self.journal_ids = self.env['account.journal'].search(
    #         #     [('company_id', '=', self.company_id.id)])
    #     else:
    #         pass
    #         #self.journal_ids = self.env['account.journal'].search([])

    # def _build_contexts(self, data):
    #     result = {}
    #     result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
    #     result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
    #     result['date_from'] = data['form']['date_from'] or False
    #     result['date_to'] = data['form']['date_to'] or False
    #     result['strict_range'] = True if result['date_from'] else False
    #     result['company_id'] = data['form']['company_id'][0] or False
    #     return result

    # def _print_report(self, data):
    #     raise NotImplementedError()

    # def check_report(self):
    #     self.ensure_one()
    #     data = {}
    #     data['ids'] = self.env.context.get('active_ids', [])
    #     data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
    #     data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move', 'company_id'])[0]
    #     used_context = self._build_contexts(data)
    #     data['form']['used_context'] = dict(used_context)
    #     return self.with_context(discard_logo_check=True)._print_report(data)

    # #--------------------------------------
    # # 

class WizardExample(models.TransientModel):
    _name = 'wizard.example'
    _description = 'wizard.example'


    patient_id = fields.Many2one('hr.employee', string="employee")
    date_meeting = fields.Date(string="Date Meeting")


    def print_report(self):
        print("+++++++++++++++++++++++++++", self.read()[0])
        print("DATA")
        data = {
            'model':'wizard.example',
            'form': self.read()[0]
        }

        app_vals = []
        vals = {
            'patient_id' : data['form']['patient_id'][1],
            'date_meeting': data['form']['date_meeting']
        }
        app_vals.append(vals)
        data['docs'] = app_vals


        print("------------------------")
        print(data['docs'] )
        return self.env.ref('evl_vat.action_lost_reason_apply').report_action(self, data=data)
       
        # #data['docs'] = {}
        # selected_patient = data['form']['patient_id'][0]
        # print(selected_patient)

        # app = self.env['hr.employee'].search([('id','=',selected_patient)])
        # app.patient_id = str(data['form']['patient_id'][0])
        # app.date_meeting = str(data['form']['date_meeting'])



        # data['docs'] = app
        # ##data['docs']['date_meeting'] = str(data['form']['date_meeting'])

        # print(data['docs'])
        # #import pdb; pdb.set_trace()







    def check_report(self):
        self.ensure_one()
        data = {}
        # data['ids'] = self.env.context.get('active_ids', [])
        # data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        # data['form'] = self.read(['patient_id', 'date_meeting'])[0]
        # used_context = self._build_contexts(data)
        # data['form']['used_context'] = dict(used_context)
        # print(data)
        print(self.read())
        data['patient_id'] = self.read(['patient_id'])[0]
        data['date_meeting'] = self.read(['patient_id'])
        data['docs'] = self.read()
        return self.env.ref('evl_report.action_lost_reason_apply').report_action(self, data=data)



class WizardAccounting(models.Model):
    _name = 'wizard.accounting'
    _description = 'wizard.accounting'
    _rec_name = 'id'

    account = fields.Char(string="Accoutnb Name")
    amount = fields.Float(string="amount")
    entry_date = fields.Datetime(string="Entry Date")


    @api.model  
    def create_appointment(self,vals):
        for rec in self:
            result = super(WizardAccounting, rec).create(vals)
            return result