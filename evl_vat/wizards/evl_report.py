#-*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta

import sys
import os

sys.path.insert(1,os.path.abspath("./nbr/library/"))

import bangla
import inflect

def last_day_of_month(any_day):
    import datetime
    next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


def get_local_time(self):
    from datetime import datetime,timedelta
    import pytz
    user_tz = self.env.user.tz or pytz.utc

    if str(user_tz) == 'UTC':
        raise UserError(_("Please setup timezone for you."))
    else:
        local = pytz.timezone(user_tz)
        local_time = datetime.now().astimezone(local) 
        return local_time

def get_years():
    year_list = []
    crn_year = datetime.now().year
    for i in range(2019, crn_year+1):
        year_list.append((str(i), str(i)))
    return year_list

class ReportMushak43(models.Model):
    _name = 'mushak.inputoutput'
    _description = 'Mushak 4.3 (Input-Output Coefficient)'
    _rec_name = 'product_id'
    
    
    company_id = fields.Many2one(string='Company', comodel_name='res.company', default=lambda self: self.env.user.company_id)
    user = fields.Many2one(string='User', comodel_name='res.users', default=lambda self: self.env.user.id)
    start_date = fields.Date.today()
    product_id = fields.Many2one(
        'product.product', 'Product',
        domain="[('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), ('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        required=True, check_company=True,  )
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    report_time = fields.Datetime('report Datetime', compute='compute_display_time')
    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)
    server_time = fields.Datetime('Server time', default=fields.Datetime.now,store=True)
    report_outline = fields.Boolean("Report Outline", default=False)
    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format')
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='landscape', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)
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
        check_company=True, required=True,
        help="Bill of Materials allow you to define the list of required components to make a finished product.")
  
    @api.model
    def get_config(self):
        for rec in self:
            rec.config = self.env.ref('evl_vat.report_mushak_input_output').id

    def prepare_data(self):
        # import pdb; pdb.set_trace()
        self.env.cr.execute("""SELECT name,street FROM res_partner WHERE id=%d""" %(self.company_id.partner_id.id))
        headers = self.env.cr.fetchall()
        data = {'model':'mushak.inputoutput','form': self.read()[0]}

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
        
        bom_product = self.env['product.template'].search([('id','=',data['form']['product_tmpl_id'][0])])
        if not bom_product:
            bom_product = self.env['product.template'].search([('id','=',data['form']['product_id'][0])])
 
        test_lines = []

        i=1       
        pro = {}
        pro['serial_number'] =  1
        pro['hscode'] = bom_product.hscode.hscode[0] if bom_product.hscode.hscode[0] else bom_product.hscode.hscode
        pro['name'] = bom_product.name
        pro['uom'] = bom_product.uom_id.name
        pro['product_name'] =  "Raw Materials"
        pro['product_qty'] =  ""
        pro['product_uom_id'] = ""
        pro['product_price'] =  None
        pro['waste_qty'] =  ""
        pro['waster_per'] =  ""
        pro['add_name'] =""
        pro['add_price'] =  None
        pro['comment'] =  ""
        pro['index'] = i
        pro['index'] = ''
        pro['type'] = 'pro'
        test_lines.append(pro)  
        i += 1

        product = {
            'serial_number': 1,
            'hscode': bom_product.hscode.hscode,
            'name': bom_product.name,
            'uom': bom_product.uom_id.name,
        }
        # import pdb; pdb.set_trace()
        bom_lines = []
        bom_line_ids = self.env['mrp.bom'].search([('id','=',data['form']['bom_code'][0])]).bom_line_ids
        bom_code_n = data['form']['bom_code'][0]
        bill_of_cost = self.env['mrp.bom'].search([('id','=',bom_code_n)]).bill_of_cost
       

        leng = max(len(bom_line_ids),len(bill_of_cost))
       

        for i in range(0, len(bom_line_ids)):

            pro = {}
            pro['serial_number'] =  ""
            pro['hscode'] = ""
            pro['name'] = ""
            pro['uom'] = ""
            pro['product_name'] = bom_line_ids[i].product_id.name
            pro['product_qty'] = bom_line_ids[i].product_qty
            pro['product_uom_id'] = bom_line_ids[i].product_uom_id.name
            pro['product_price'] = "{0:.2f}".format(round(bom_line_ids[i].standard_price,2)) or ""
            pro['waste_qty'] = bom_line_ids[i].waste_qty or ""
            pro['waster_per'] = str(bom_line_ids[i].waste_per) + " %" or ""
            pro['add_name'] =""
            pro['add_price'] =  ""
            pro['comment'] =  ""
            pro['index'] = i
            pro['type'] = 'bol'
            test_lines.append(pro)  
            i += 1
            

        for i in range(0, len(bill_of_cost)):

            pro = {}
            pro['serial_number'] =  ""
            pro['hscode'] = ""
            pro['name'] = ""
            pro['uom'] = ""
            pro['product_name'] = ""
            pro['product_qty'] = ""
            pro['product_uom_id'] = ""
            pro['product_price'] = ""
            pro['waste_qty'] = ""
            pro['waster_per'] = ""
            pro['add_name'] = bill_of_cost[i].name
            pro['add_price'] =  "{0:.2f}".format(round(bill_of_cost[i].cost,2)) 
            pro['comment'] = ""
            pro['index'] = i
            pro['type'] = 'boc'

            test_lines.append(pro)  
            i += 1

        #Convert to Bangla

        if self.language == 'bangla':
            headers[0]['zip'] = bangla.convert_english_digit_to_bangla_digit(headers[0]['zip'] )
            headers[0]['vat'] = bangla.convert_english_digit_to_bangla_digit(headers[0]['vat'])
            headers[0]['date'] = bangla.convert_english_digit_to_bangla_digit(headers[0]['date'])

            for line in test_lines:
                print(line)
                if line['type'] == 'pro':
                    line['serial_number'] = bangla.convert_english_digit_to_bangla_digit(str(line['serial_number']))
                    line['hscode'] = bangla.convert_english_digit_to_bangla_digit(line['hscode'])    
                if line['type'] == 'bol':
                    line['product_qty'] = bangla.convert_english_digit_to_bangla_digit(str(line['product_qty']))
                    line['product_price'] = bangla.convert_english_digit_to_bangla_digit(str(line['product_price']))
                    line['waste_qty'] = bangla.convert_english_digit_to_bangla_digit(str(line['waste_qty']))
                    line['waster_per'] = bangla.convert_english_digit_to_bangla_digit(str(line['waster_per']))
                if line['type'] == 'boc':
                    line['add_name'] = bangla.convert_english_digit_to_bangla_digit(str(line['add_name']))
                    line['add_price'] = bangla.convert_english_digit_to_bangla_digit(str(line['add_price']))


        data['headers'] = headers
        data['bom_product'] = product
        data['bom_lines'] = test_lines        
        data['footer'] = {'report_time': self.report_time}
        return data

    def print_preview(self): 

        data = self.prepare_data()
        return self.env.ref('evl_vat.report_mushak_input_output_preview').report_action(self, data=data)


    def print_report(self): 
        # import pdb; pdb.set_trace()
        data = self.prepare_data()

        # report = self.env.ref('evl_vat.report_mushak_input_output')
        # report.paperformat_id = self.env.ref('evl_vat.my_paperformat_to_apply').id
        # report.report_action([], data=data)

        return self.env.ref('evl_vat.report_mushak_input_output').report_action(self, data=data)
       



class ReportMushakPurchaseBook(models.Model):
    _name = 'mushak.purchase'
    _description = 'Mushak 6.1 (Purchase Book)'

    report_type = fields.Selection([
                ('month', 'Month Wise'),
                ('date', 'Date Wise')], string='Report Type',
                default='month', help="Defines how a report will be generated(month-wise or date-wise)", required=True)
    month = fields.Selection(
                        [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ], 
                        string='Month')
    year = fields.Selection(get_years(), string='Year', dafault='10')

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    user = fields.Many2one(string='User', comodel_name='res.users', default=lambda self: self.env.user.id)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')

    product_selection = fields.Boolean(
        'All Product', default=True,
        help="By checking this product selection field, you select all products.")


    product_id = fields.Many2one(
        'product.product', 'Product',## ('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), 
        domain="[('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        )
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')

    report_time = fields.Datetime('report Datetime', compute='compute_display_time')
    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='landscape', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)

    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id
    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)


    def _build_contexts(self):

        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('stock.inventory', 'purchase.order')
        data['form'] = self.read()[0]

        result = {}

        if self.report_type == 'month':
            from datetime import datetime
            first_of_month = datetime.today().replace(month=int(self.month)).replace(year=int(self.year)).replace(day=1)
            import datetime
            last_of_month =  last_day_of_month(datetime.date(first_of_month.year,first_of_month.month,1 ))
        else:
            first_of_month = data['form']['date_from'] or False
            last_of_month = data['form']['date_to'] or False
      

 
        if data['form']['product_id'] != False:
            if data['form']['product_id'][0]:
                products = self.env['product.product'].search([('id','=',data['form']['product_id'][0])])
        else:
            products = self.env['product.product'].search([('purchase_ok','=',True)])
        
        pages=[]
        pg_no = 1

        #Opening Stock
        for product in products:

            # START_QTY ="""
            # SELECT 
            #     min("stock_valuation_layer".id) AS id, 
            #     count("stock_valuation_layer".id) AS "product_id_count" , 
            #     sum("stock_valuation_layer"."quantity") AS "quantity",
            #     sum("stock_valuation_layer"."value") AS "value",
            #     "stock_valuation_layer"."product_id" as "product_id" 
                
            #         FROM "stock_valuation_layer" LEFT JOIN "product_product" as "stock_valuation_layer__product_id" ON ("stock_valuation_layer"."product_id" = "stock_valuation_layer__product_id"."id") 
            #         LEFT JOIN "product_template" as "stock_valuation_layer__product_id__product_tmpl_id" ON ("stock_valuation_layer__product_id"."product_tmpl_id" = 
            #         "stock_valuation_layer__product_id__product_tmpl_id"."id") 
            #         LEFT JOIN "ir_translation" as "stock_valuation_layer__product_id__product_tmpl_id__name" ON ("stock_valuation_layer__product_id__product_tmpl_id"."id" = "stock_valuation_layer__product_id__product_tmpl_id__name"."res_id" 
            #         AND "stock_valuation_layer__product_id__product_tmpl_id__name"."type" = 'model' AND 
            #         "stock_valuation_layer__product_id__product_tmpl_id__name"."name" = 'product.template,name' 
            #         AND "stock_valuation_layer__product_id__product_tmpl_id__name"."lang" = 'en_US' 
            #         AND "stock_valuation_layer__product_id__product_tmpl_id__name"."value" != '')
            #         WHERE (("stock_valuation_layer"."product_id" in (58))  AND  ("stock_valuation_layer"."create_date" <= '2020-03-31 13:04:33')) 
            #         AND ("stock_valuation_layer"."company_id" in (1))
            #         GROUP BY "stock_valuation_layer"."product_id","stock_valuation_layer__product_id"."default_code",
            #         COALESCE("stock_valuation_layer__product_id__product_tmpl_id__name"."value","stock_valuation_layer__product_id__product_tmpl_id"."name"),
            #         "stock_valuation_layer__product_id"."id"
            #         ORDER BY  "stock_valuation_layer__product_id"."default_code" ,COALESCE("stock_valuation_layer__product_id__product_tmpl_id__name"."value", "stock_valuation_layer__product_id__product_tmpl_id"."name") ,
            #         "stock_valuation_layer__product_id"."id"

            # """

            product_id = product.id
            product_name  = product.name
            row_lines=[]
            o_s_qty = product.with_context({'to_date': first_of_month}).qty_available
            o_s_month_qty = product.with_context({'to_date': first_of_month}).qty_available
            o_s_month_price = o_s_month_qty*product.standard_price
                   

            #Starting Balance of products            
            sn = 1

            if sn==1 and int(o_s_month_qty) > 0:
                row = {
                    'ser_num' : sn,
                    'date': first_of_month.date(),
                    'op_stock': str(o_s_month_qty),                        
                    'op_price': "%.2f" % round(o_s_month_price,2),
                    'challan_no':'-',
                    'pur_date':'-',
                    'vendor_name':'-',
                    'vendor_add':'-',
                    'vendor_bin':'-',
                    'pur_desc':'-',
                    'pur_qty':'-',                        
                    'pur_price':'-',
                    'pur_sp_vat':'-',
                    'vat':'-',
                    'total_qty': str(o_s_month_qty),                        
                    'total_price': "%.2f" % round(o_s_month_price,2),
                    'man_qty':'-',                        
                    'man_price':'-',
                    'clo_qty': str(o_s_month_qty),                        
                    'clo_price': "%.2f" % round(o_s_month_price,2),
                    'comments': '',

                        'op_stock_uom': str(product.product_tmpl_id.uom_id.name),
                        'pur_qty_uom': '-',
                        'total_qty_uom': str(product.product_tmpl_id.uom_id.name),
                        'man_qty_uom': '-',
                        'clo_qty_uom': str(product.product_tmpl_id.uom_id.name),
                }
                row_lines.append(row) 
                sn += 1

        
        
            #Purchased Items
            #Alternative date must be used

            pur_order_query = """
                                SELECT 
                                    null as sn, 
                                    DATE(am.invoice_date) as date,  
                                    0 as op_stock,                                                                          
                                    0.00 as op_price,
                                    po.name as challan_no,
                                    DATE(am.invoice_date) as pur_date, 
                                    rp.name as vendor_name,
                                    CONCAT(rp.street ,',',  rp.street2,',',rp.city,',',rc.name) as vendor_add,
                                    rp.vat as vendor_bin,
                                    pol.name as pur_desc,
                                    pol.product_uom_qty as pur_qty,                                      
                                    pol.price_subtotal as pur_price,
                                    0.00 as pur_sp_vat,
                                    pol.price_tax as vat,
                                    null as total_qty,                                        
                                    null as total_price,
                                    null as man_qty,                                        
                                    null as man_price,
                                    null as clo_qty,
                                    null as clo_price,
                                    'purchase' as comments,
                                        null as op_stock_uom,  
                                        uu.name as pur_qty_uom,
                                        null as total_qty_uom,
                                        null as man_qty_uom,
                                        null as clo_qty_uom

                                FROM account_move as am 
                                    LEFT JOIN purchase_order as po ON po.id = am.bill_origin                                
                                    LEFT JOIN purchase_order_line as pol ON pol.order_id = po.id
                                    LEFT JOIN res_partner as rp ON pol.partner_id=rp.id
                                    LEFT JOIN res_country as rc ON rp.country_id = rc.id
                                    LEFT JOIN product_product as pp ON pp.id = pol.product_id
                                    LEFT JOIN product_template as pt ON pt.id = pp.product_tmpl_id
                                    LEFT JOIN uom_uom as uu ON pt.uom_id = uu.id
                                
                                    
                                WHERE po.invoice_status = 'invoiced' AND am.invoice_date >= %s
                                    AND am.invoice_date <= %s
                                    AND po.company_id = %s AND pol.product_id=%s


                                """ 

            mrp_pro_query ="""
                                SELECT 
                                    null as sn, 
                                    DATE(mp.date_finished) as date,
                                    0 as op_stock, 
                                    0.00 as op_price,
                                    null as challan_no,
                                    null as pur_date, 
                                    null as vendor_name,
                                    null as vendor_add,
                                    null as vendor_bin,
                                    null as pur_desc,
                                    null as pur_qty,
                                    0.00 as pur_price,
                                    0.00 as pur_sp_vat,
                                    0.00 as vat,
                                    null as total_qty,
                                    null as total_price,
                                    sm.product_uom_qty as man_qty,
                                    
                                        
                                    COALESCE(sm.product_uom_qty*mbl.standard_price, 0.00 )::numeric as man_price,
                                    null as clo_qty,
                                    null as clo_price,
                                    'consume' as comments,
                                        null as op_stock_uom,
                                        null pur_qty_uom,
                                        null as total_qty_uom,
                                        uu.name as man_qty_uom,
                                        null as clo_qty_uom

                                FROM mrp_bom_line as mbl 
                                    LEFT JOIN mrp_production as mp ON mbl.bom_id = mp.bom_id
                                    LEFT JOIN product_product as pp ON mp.product_id = pp.id
                                    LEFT JOIN product_template as pt ON pp.product_tmpl_id = pt.id
                                    LEFT JOIN ir_property as ip ON CAST(SPLIT_PART(ip.res_id, ',', 2) AS int) = pp.id
                                    LEFT JOIN uom_uom as uu ON mbl.product_uom_id = uu.id
                                    LEFT JOIN stock_move as sm ON mp.id = sm.raw_material_production_id

                                WHERE mp.state = 'done' AND
                                    mp.date_finished >= %s AND mp.date_finished <= %s
                                    AND mp.company_id = %s
                                    AND mbl.product_id = %s""" 

            # mrp_pro_query ="""
            #                     SELECT 
            #                         null as sn, 
            #                         DATE(mp.date_finished) as date,
            #                         0 as op_stock, 
            #                         0.00 as op_price,
            #                         null as challan_no,
            #                         null as pur_date, 
            #                         null as vendor_name,
            #                         null as vendor_add,
            #                         null as vendor_bin,
            #                         null as pur_desc,
            #                         null as pur_qty,
            #                         0.00 as pur_price,
            #                         0.00 as pur_sp_vat,
            #                         0.00 as vat,
            #                         null as total_qty,
            #                         null as total_price,
            #                         mbl.product_qty as man_qty,
                                        
            #                         COALESCE(ip.value_float, 0.00 )::numeric as man_price,
            #                         null as clo_qty,
            #                         null as clo_price,
            #                         'consume' as comments,
            #                             null as op_stock_uom,
            #                             null pur_qty_uom,
            #                             null as total_qty_uom,
            #                             uu.name as man_qty_uom,
            #                             null as clo_qty_uom

            #                     FROM mrp_bom_line as mbl 
            #                         LEFT JOIN mrp_production as mp ON mbl.bom_id = mp.bom_id
            #                         LEFT JOIN product_product as pp ON mp.product_id = pp.id
            #                         LEFT JOIN product_template as pt ON pp.product_tmpl_id = pt.id
            #                         LEFT JOIN ir_property as ip ON CAST(SPLIT_PART(ip.res_id, ',', 2) AS int) = pp.id
            #                         LEFT JOIN uom_uom as uu ON mbl.product_uom_id = uu.id
            #                     WHERE mp.state = 'done' AND
            #                         mp.date_finished >= %s AND mp.date_finished <= %s
            #                         AND mp.company_id = %s
            #                         AND mbl.product_id = %s""" 
      


            main_quey = pur_order_query + """ UNION """ + mrp_pro_query +""" ORDER BY date ASC"""
            self.env.cr.execute(main_quey,(first_of_month.date(), last_of_month, self.company_id.id, product_id,first_of_month.date(), last_of_month, self.company_id.id, product_id))
            datas = self.env.cr.fetchall()

            pg_toto = pg_no = 1

            for q_line in datas:
                #Neeed to solve address issue
                add = q_line[7].split(",") if q_line[7] != None else q_line[7]
                vendor_add = ''
                if add != None:
                    for i in add:
                        vendor_add += ','  + i if i != '' else vendor_add
                       

                if sn > 1:
                    o_s_month_qty = float(row_lines[-1]['clo_qty'])
                    o_s_month_price = float(row_lines[-1]['clo_price'])



                else:
                    o_s_month_qty = 0.0
                    o_s_month_price = 0.0

                
                if q_line[10] !=  None:
                    clo_qty =  o_s_month_qty +  q_line[10]
                     
                    
                elif q_line[16] !=  None:
                    clo_qty =  o_s_month_qty -  q_line[16] 
                else:
                    clo_qty =  o_s_month_qty

                if q_line[11] !=  None:
                    clo_price =  o_s_month_price +  q_line[11] 
                    
                elif q_line[16] !=  None:
                    clo_price =  o_s_month_price -  q_line[17] 
                else:
                    clo_price =  o_s_month_price
                # import pdb; pdb.set_trace()
                row = {
                    'ser_num' : sn,
                    'date': q_line[1],
                    'op_stock': "%.2f" % round(o_s_month_qty,2) ,
                    'op_price': "%.2f" % round(o_s_month_price,2),
                    'challan_no': q_line[4],
                    'pur_date': q_line[5] ,
                    'vendor_name': q_line[6] ,
                    'vendor_add': vendor_add ,
                    'vendor_bin': q_line[8] ,
                    'pur_desc' :q_line[9] ,
                    'pur_qty':  "%.2f" % round(q_line[10],2) if q_line[10] != None and int(q_line[10]) != 0 else '',
                    'pur_price': "%.2f" % q_line[11] if q_line[11] != None and int(q_line[11]) != 0 else '',
                    'pur_sp_vat': "%.2f" % round(q_line[12]  ,2) if q_line[12] != None and int(q_line[12]) != 0 else '',
                    'vat': "%.2f" % round(q_line[13] ,2) if q_line[13] != None and int(q_line[13]) != 0 else '',
                    'total_qty': "%.2f" % round(o_s_month_qty +  q_line[10],2) if  q_line[10] != None else "%.2f" % round(o_s_month_qty,2),
                    'total_price': "%.2f" % round(o_s_month_price +  q_line[11]) if  q_line[11] != None else "%.2f" % round(o_s_month_qty,2),
                    'man_qty': "%.2f" % round(q_line[16],2) if q_line[16] != None else '',
                    'man_price': "%.2f" % round(q_line[17] ,2 ) if q_line[17] != None else None,
                    'clo_qty': "%.2f" % round(clo_qty,2) if clo_qty != None else '',
                    'clo_price': "%.2f" % round(clo_price  ,2) if clo_price != None else '',
                    'comments': q_line[20] ,

                        'op_stock_uom': str(product.product_tmpl_id.uom_id.name),
                        'pur_qty_uom': q_line[22] ,
                        'total_qty_uom': str(product.product_tmpl_id.uom_id.name),
                        'man_qty_uom': q_line[24] ,
                        'clo_qty_uom': str(product.product_tmpl_id.uom_id.name),

                }
                row_lines.append(row) 
                sn += 1
                o_s_month_qty = clo_qty
                o_s_month_price = clo_price


            if len(row_lines) > 0:  
                footers = {
                'print_date': self.report_time,
                'pg_no' : pg_no,
                'pg_toto':pg_toto
                }    
                pg_no += 1  
                pages.append({'row_lines': row_lines, 'product_header' : product.name,'footers':footers})
        #-----------------------------------------------------------------------------
        if len(pages) == 0:
            row_lines =[]
            sn = 1
            row = {
                'ser_num' : '',
                'date':'',
                'op_stock': '',
                'op_price': '',
                'challan_no':'',
                'pur_date':'',
                'vendor_name':'',
                'vendor_add':'',
                'vendor_bin':'',
                'pur_desc':'',
                'pur_qty':'',
                'pur_price':'',
                'pur_sp_vat':'',
                'vat':'',
                'total_qty': '',
                'total_price': '',
                'man_qty':'',
                'man_price':'',
                'clo_qty': '',
                'clo_price': '',
                'comments': '',
                        'op_stock_uom': '',
                        'pur_qty_uom': '',
                        'total_qty_uom': '',
                        'man_qty_uom': '',
                        'clo_qty_uom': ''

            }
            row_lines.append(row) 
            footers = {
            'print_date': self.report_time,
            'pg_no' : '1',
            'pg_toto':'1'
            }
            pages.append({'row_lines': row_lines, 'product_header' : '','footers':footers})

        #---------------------------------------------------------------------------------
        #ManOrder Finished Product
        #Sales
        #Closing Stock
        # result = {}
        # result['company_id'] = data['form']['company_id'][0] or False
        #row_lines = []
        # result['pages'] = pages

        self.report_time = get_local_time(self).replace(tzinfo=None)
        result['footers'] ={'date_time': self.report_time}



             
        headers=[{
                            'name': self.company_id.name,
                            'street': self.company_id.street,
                            'street2': self.company_id.street2,
                            'zip': self.company_id.zip,
                            'vat':self.company_id.vat,
                        }]



        if self.language == 'bangla':

            headers[0]['zip'] = bangla.convert_english_digit_to_bangla_digit(str(headers[0]['zip']))
            headers[0]['vat'] = bangla.convert_english_digit_to_bangla_digit(str(headers[0]['vat']))

            if self.language == 'bangla':
                for page in pages:
                
                    for line in page['row_lines']: 
                        
                        for key,value in line.items():
                            if key == 'ser_num':
                                # line[key] =int(line[key]) if line[key] != None else ''
                                line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key])) if line[key] != None else ''
                            
                            
                            if key not in ['ser_num','challan_no','vendor_name','vendor_add', 'pur_desc','comments']:
                                if key not in ['date','pur_date',]:
                                    line[key] ="%.2f" % float(line[key]) if line[key] != None else ''
                                line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key])) if line[key] != None else ''
                                


        data['headers'] = headers
        data['pages'] = pages
        data['footers'] = {'date_time': self.report_time}
        return data

    def print_preview(self): 
        data = self._build_contexts()  
        return self.env.ref('evl_vat.report_mushak_purchase_preview').report_action(self, data=data)

    def _print_report(self, data):
        raise NotImplementedError()

    def print_purchase(self):
        self.ensure_one()
        data = self._build_contexts()  
        return self.env.ref('evl_vat.report_mushak_purchase').report_action(self, data=data)
  

 

#-------------------------------------------------------Mushak 6.2: Sale Book------------------------------------------------------------------

class ReportMushakSaleBook(models.Model):
    _name = 'mushak.sale'
    _description = 'Mushak 6.2 (Sale Book)'

    report_type = fields.Selection([
                ('month', 'Month Wise'),
                ('date', 'Date Wise')], string='Report Type',
                default='month', help="Defines how a report will be generated(month-wise or date-wise)", required=True)

    month = fields.Selection(
                        [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ], 
                        string='Month')
    year = fields.Selection(get_years(), string='Year', dafault='10')

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')

    product_selection = fields.Boolean(
        'All Product', default=True,
        help="By checking this product selection field, you select all products.")


    product_id = fields.Many2one(
        'product.product', 'Product',## ('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), 
        domain="[('sale_ok','=',True), ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        )
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    

    report_time = fields.Datetime('report Datetime', compute='compute_display_time')
    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='landscape', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)

    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id

    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)
    def _build_contexts(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('stock.inventory', 'purchase.order')
        data['form'] = self.read()[0]

        result = {}
        result['company_id'] = data['form']['company_id'][0] or False

        if self.report_type == 'month':
            from datetime import datetime
            first_of_month = datetime.today().replace(month=int(self.month)).replace(year=int(self.year)).replace(day=1)
            import datetime
            last_of_month =  last_day_of_month(datetime.date(first_of_month.year,first_of_month.month,1 ))

        else:
            first_of_month = data['form']['date_from'] or False
            last_of_month = data['form']['date_to'] or False


        #Get all saleable product info
        products = self.env['product.product'].search([('sale_ok','=',True)])
        pages=[]
        # import pdb; pdb.set_trace()


        #Opening Stock
        for product in products:
            product_id = product.id
            product_name  = product.name
            row_lines=[]
            o_s_qty = o_s_month_qty =  product.with_context({'to_date': first_of_month}).qty_available
            o_s_month_price = o_s_month_qty*product.standard_price


            mo_factor =  self.env['mrp.production'].search([('product_id','=',product_id)],limit=1).product_uom_id
            so_factor = self.env['sale.order.line'].search([('product_id','=',product_id)],limit=1).product_uom

            
            mo_fac = so_fac = 1


            if len(mo_factor) > 0 and len(so_factor) >0:
                if mo_factor.factor != so_factor.factor:
                    if mo_factor.factor < so_factor.factor:
                        mo_fac = so_factor.factor/mo_factor.factor
                        so_fac = 1
                    else:
                        mo_fac = 1
                        so_fac = mo_factor/so_factor


            #test
            # o_s_month_qty = 10.00
            # o_s_month_price = 5000.00

            #Starting Balance of products   
            # Considering single unit of product_product         
            sn = 1

            if sn==1:
                row = {
                    'ser_num' : sn,
                    'date': first_of_month.date(),
                    'op_stock': str(o_s_month_qty),
                    'op_price':    "%.2f" % round(o_s_month_price  ,2),  
                    'man_qty':'-',
                    'man_price':'-',
                    'total_qty':str(o_s_month_qty),
                    'total_price':   "%.2f" % round(o_s_month_price  ,2),    
                    'cus_name':'-',
                    'cus_add':'-',
                    'cus_bin':'-',
                    'challan_no':'-',
                    'challan_date':'-',
                    'product':'-',
                    'sale_qty':'-',
                    'sale_price':'-',
                    'sale_sd': '-',
                    'sale_vat': '-',
                    'clo_qty': str(o_s_month_qty),
                    'clo_price':  "%.2f" % round(o_s_month_price  ,2), 
                    'comments': '',
                    'product_uom': product.product_tmpl_id.uom_id.name
                }
                row_lines.append(row)  
                sn += 1

            
            #SQL Queries
            #No link between purchase invoice and purchase Order
            mrp_pro_query = """
                            SELECT 
                                null as sn, DATE(mp.date_finished) as start_date, null as open_qty, null as open_price, product_qty as manu_qty, 
                            product_qty*pt.list_price as manu_price, null as total_qty, null as total_price,
                            null as cus_name, null as cus_address, null as bin_no, null as invoice_id, null as invoice_date,   pt.name as product_name,
                            null as pro_qty, null as pro_unit, null as pro_sd, null as pri_tax, null as clo_stoc_qty, null as clo_stoc_price, null as end_comments,
                            
                            uu.factor as mo_uom,
                            null as sol_uom,
                            null as product_uom

                            FROM mrp_production as mp 

                            LEFT JOIN product_product as pp ON mp.product_id = pp.id
                            LEFT JOIN product_template as pt ON pp.product_tmpl_id = pt.id
                            
                            LEFT JOIN uom_uom as uu ON mp.product_uom_id = uu.id

                            WHERE mp.state = 'done' AND mp.product_id ='%s' AND mp.date_finished >= '%s' AND mp.date_finished <= '%s'
                            """ %(product_id,first_of_month.date(),last_of_month)

            sale_order_query = """
                                SELECT null as sn, DATE(am.invoice_date) as start_date,  
                                    null as open_qty, null as open_price, null as manu_qty, 
                                    null as manu_price, null as total_qty, null as total_price,
                                    rp.name as cus_name,CONCAT(rp.street ,',',  rp.street2,',',rp.city,',',rc.name) as cus_address, 
                                    rp.vat as bin_no, so.name as invoice_id,DATE(am.invoice_date) as invoice_date,
                                    sop.name as product_name, sop.product_uom_qty as pro_qty, sop.price_subtotal as pro_unit, 
                                    null as pro_sd, sop.price_tax as pri_tax, null as clo_stoc_qty,
                                    null as clo_stoc_price, null as end_comments,
                                    null as mo_uom,
                                    uu.factor as sol_uom,
                                    null as product_uom
                                FROM account_move as am 
                                    LEFT JOIN sale_order as so ON am.invoice_origin=so.name
                                    LEFT JOIN   sale_order_line as sop ON sop.order_id = so.id
                                    LEFT JOIN res_partner as rp
                                        ON sop.order_partner_id=rp.id
                                    LEFT JOIN res_country as rc
                                        ON rp.country_id = rc.id
                                    LEFT JOIN uom_uom as uu ON sop.product_uom = uu.id 
                                    
                                WHERE sop.invoice_status = 'invoiced' AND am.type='out_invoice' 
                                    AND DATE(am.invoice_date) >= '%s'

                                    AND DATE(am.invoice_date) <= '%s'
                                    
                                     AND sop.product_id='%s'


                                """ %(first_of_month.date(),last_of_month, product_id)



            main_quey = mrp_pro_query + """UNION""" + sale_order_query +""" ORDER BY start_date ASC"""
            self.env.cr.execute(main_quey)
            datas = self.env.cr.fetchall()




            print(datas)
            # import pdb; pdb.set_trace()
            for q_line in datas:
                if sn > 1:
                    o_s_month_qty = float(row_lines[-1]['clo_qty'])
                    o_s_month_price = float(row_lines[-1]['clo_price'])

                clo_stock = o_s_month_qty + q_line[4]* mo_fac if  q_line[4] != None else o_s_month_qty
                clo_stock = clo_stock -  q_line[14] *so_fac  if  q_line[14] != None else clo_stock

                # clo_price = o_s_month_price + q_line[5] * mo_fac   if q_line[5] != None else o_s_month_price
                # clo_price = clo_price  -  q_line[15] *so_fac if  q_line[15] != None else clo_price

                clo_price = clo_stock *product.product_tmpl_id.standard_price if  q_line[15] != None else clo_stock *product.product_tmpl_id.standard_price


                row = {
                    'ser_num' : sn,
                    'date': q_line[1],
                    'op_stock': o_s_month_qty ,
                    'op_price':  "%.2f" % round(o_s_month_price,2),   
                    'man_qty': "%.2f" % round(q_line[4] * mo_fac,2)  if q_line[4] != None else None,
                    'man_price':  "%.2f" % round(q_line[5] * mo_fac ,2) if q_line[5] !=None else None,     
                    'total_qty': "%.2f" % round(o_s_month_qty + q_line[4] * mo_fac,2) if q_line[4] != None else o_s_month_qty, #str(row_lines[-1]['op_stock'] + 
                    'total_price':   "%.2f" % round( o_s_month_price + q_line[5] * mo_fac if q_line[5] != None else o_s_month_price ,2),   
                    'cus_name':q_line[8] if q_line[8] != None else '-',
                    'cus_add':q_line[9] if q_line[9] != None else '-',
                    'cus_bin':q_line[10] if q_line[10] != None else '-',
                    'challan_no':q_line[11] if q_line[11] != None else '-',
                    'challan_date':q_line[12] if q_line[12] != None else '-',
                    'product':q_line[13],
                    'sale_qty':q_line[14] *so_fac if q_line[14]!= None else None,
                    'sale_price': "%.2f" % round(q_line[15]*so_fac ,2) if q_line[15] != None else None,   
                    'sale_sd':q_line[16] ,
                    'sale_vat':q_line[17] if q_line[17] != None else '-',
                    'clo_qty': clo_stock,
                    'clo_price':  "%.2f" % round(clo_price ,2),
                    'comments':q_line[20],
                        'product_uom':product.product_tmpl_id.uom_id.name,
                }
                row_lines.append(row)  
                sn += 1

            if len(row_lines) > 1:        
                pages.append({'row_lines': row_lines, 'product_header' : product.name})
        print(pages)
        # import pdb; pdb.set_trace()
        if len(pages) == 0:
            row_lines =[]
            row = {
                'ser_num' : '-',
                'date': '-',
                'op_stock': '-',
                'op_price':  '-',  
                'man_qty': '-',
                'man_price':  '-',     
                'total_qty': '-',
                'total_price':   '-',
                'cus_name': '-',
                'cus_add': '-',
                'cus_bin': '-',
                'challan_no': '-',
                'challan_date':'-',
                'product':'-',
                'sale_qty':'-',
                'sale_price': '-', 
                'sale_sd': '-',
                'sale_vat': '-',
                'clo_qty': '-',
                'clo_price':  '-',
                'comments': '-',
                    'product_uom':'',
            }
            row_lines.append(row) 
            
            footers = {
            'print_date': self.report_time,
            'pg_no' : '1',
            'pg_toto':'1'
            }
            pages.append({'row_lines': row_lines, 'product_header' : '','footers':footers})

        headers=[{
                            'name': self.company_id.name,
                            'street': self.company_id.street,
                            'street2': self.company_id.street2,
                            'zip': self.company_id.zip,
                            'vat':self.company_id.vat,
                }]

        if self.language == 'bangla':
            headers[0]['zip'] = bangla.convert_english_digit_to_bangla_digit(str(headers[0]['zip']))
            headers[0]['vat'] = bangla.convert_english_digit_to_bangla_digit(str(headers[0]['vat']))

            for page in pages:                
                for line in page['row_lines']:                         
                    for key,value in line.items():
                        print(key,value)
                        
                        
                        if key not in ['cus_name','cus_add','challan_no', 'product','comments']:
                            if key not in ['date','challan_date',]:
                                line[key] ="%.2f" % float(line[key]) if line[key] != None and line[key] != '' and line[key] != '-' else line[key]
                            line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key])) if line[key] != None else ''


        self.report_time = get_local_time(self).replace(tzinfo=None)
        data['headers'] = headers
        data['pages'] = pages
        data['totals'] = {}
        data['footers'] = {'date_time': self.report_time}
        print(data)
        # import pdb; pdb.set_trace()

        return data

    def _print_report(self, data):
        raise NotImplementedError()

    def print_preview(self): 
        data = self._build_contexts()  
        return self.env.ref('evl_vat.report_mushak_sale_preview').report_action(self, data=data)


    def print_sale(self):
        data = self._build_contexts()  
        # return self.env.ref('evl_vat.report_mushak_purchase_preview').report_action(self, data=data)

        return self.env.ref('evl_vat.report_mushak_sale').report_action(self, data=data)


 

#---------------Mushak 6.2.1: Purchase-Sale Book------------------------------------------------------------------

class ReportMushakPurcahseSaleBook(models.Model):
    _name = 'mushak.purchase.sale'
    _description = 'Mushak 6.2 (Purchase-Sale Book)'

    report_type = fields.Selection([
                ('month', 'Month Wise'),
                ('date', 'Date Wise')], string='Report Type',
                default='month', help="Defines how a report will be generated(month-wise or date-wise)", required=True)
    month = fields.Selection(
                        [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ], 
                        string='Month')
    year = fields.Selection(get_years(), string='Year', dafault='10')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    product_selection = fields.Boolean(
        'All Product', default=True,
        help="By checking this product selection field, you select all products.")
    product_id = fields.Many2one(
        'product.product', 'Product',## ('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), 
        domain="['|', ('sale_ok','=',True),('purchase_ok', True), ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        )
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    
    report_time = fields.Datetime('report Datetime', compute='compute_display_time')

    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='landscape', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)

    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id


    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)


    def _build_contexts(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('stock.inventory', 'purchase.order')
        data['form'] = self.read()[0]
        



        # result = {}
        # result['company_id'] = data['form']['company_id'][0] or False

        if self.report_type == 'month':
            from datetime import datetime
            first_of_month = datetime.today().replace(month=int(self.month)).replace(year=int(self.year)).replace(day=1)
            import datetime
            last_of_month =  last_day_of_month(datetime.date(first_of_month.year,first_of_month.month,1 ))

        else:
            first_of_month = data['form']['date_from'] or False
            last_of_month = data['form']['date_to'] or False


        #Get all saleable product info
        products = self.env['product.product'].search(['|',('sale_ok','=',True),('purchase_ok','=',True)])


        pages=[]
        #Opening Stock
        for product in products:

            product_id = product.id
            product_name  = product.name
            row_lines=[]
            o_s_qty = product.with_context({'to_date': first_of_month}).qty_available
            o_s_month_qty = product.with_context({'to_date': first_of_month}).qty_available
            o_s_month_price = o_s_month_qty*product.standard_price
                   

            mo_factor =  self.env['mrp.production'].search([('product_id','=',product_id)],limit=1).product_uom_id
            so_factor = self.env['sale.order.line'].search([('product_id','=',product_id)],limit=1).product_uom

            
            mo_fac = so_fac = 1


            if len(mo_factor) > 0 and len(so_factor) >0:
                if mo_factor.factor != so_factor.factor:
                    if mo_factor.factor < so_factor.factor:
                        mo_fac = so_factor.factor/mo_factor.factor
                        so_fac = 1
                    else:
                        mo_fac = 1
                        so_fac = mo_factor/so_factor

            #Starting Balance of products            
            sn = 1

            if sn==1 and int(o_s_month_qty) > 0:
                row = {



                    'ser_num' : str(sn),                    
                    'date': first_of_month.date(),
                    'sale_op_stock': str(o_s_month_qty),
                    'sale_op_price': str(o_s_month_price),
                    'pur_qty':'-',
                    'pur_price':'-',
                    'total_qty':str(o_s_month_qty),
                    'total_price':str(o_s_month_price),
                    'vendor_name':'-',
                            'vd_street': '-',
                            'vd_street2':'-',
                            'vd_area': '-',
                            'vd_city': '-',
                    # 'vendor_add': q_line[9],
                    'vendor_bin':'-',
                    'pur_challan': '-',
                    'pur_challan_date': '-',
                    'sale_product': '-',
                    'sale_qty': '-',
                    'sale_price': '-',
                    'sale_sd': '-',
                    'sale_vat': '-',
                    'customer_name': '-',
                            'street': '-',
                            'street2':'-',
                            'area': '-',
                            'city': '-',
                            'country':'-',

                    # 'customer_add': q_line[19],
                    'customer_bin': '-',
                    'sale_challan': '-',
                    'sale_challan_date': '-',
                    'clo_qty': str(o_s_month_qty),
                    'clo_price':   "%.2f" % round(o_s_month_price ,2), 
                    'comments': '',
                    'product_uom': product.product_tmpl_id.uom_id.name,
                     }

          
                row_lines.append(row)  
                sn += 1


            #Purchase Order Query
            pur_query = """
                           SELECT 
                                null::Numeric as ser_num,
                                DATE(am.invoice_date) as date,
                                null::Numeric as sale_op_stock,
                                null::Numeric as sale_op_price,
                                pol.qty_received as pur_qty,
                                pol.price_subtotal as pur_price,
                                null::Numeric as total_qty,
                                null::Numeric as total_price,
                                rp.name as vendor_name,
                                CONCAT(rp.street ,',',  rp.street2,',',rp.city,',', rc.name) as vendor_add, 
                                rp.vat as vendor_bin,
                                po.name as challan_no,
                                DATE(po.date_order) as challan_date,
                                null as sale_product,
                                null as sale_qty,
                                null as sale_price,
                                null as sale_sd,
                                null as sale_vat,
                                null as customer_name,
                                null as customer_add,
                                null as customer_bin,
                                null as sale_challan,
                                null as sale_challan_date,
                                null::Numeric as clo_qty,
                                null::Numeric as clo_price,
                                null as comments,
                                null as product_uom

                            FROM account_move am
                                LEFT JOIN purchase_order po ON am.bill_origin=po.id
                                LEFT JOIN purchase_order_line pol ON pol.order_id = po.id 
                                LEFT JOIN res_partner rp ON pol.partner_id = rp.id
                                LEFT JOIN res_country as rc ON rp.country_id = rc.id

                            WHERE
                                po.invoice_status = 'invoiced' AND am.type='in_invoice' AND am.invoice_date >= '%s'

                                AND am.invoice_date <= '%s' AND pol.product_id = '%s' 
                        """ %(first_of_month.date(),last_of_month,product_id)

     
            sale_query = """
                            SELECT 
                                null::Numeric as ser_num,
                                DATE(am.invoice_date) as date,  
                                null::Numeric as sale_op_stock,
                                null::Numeric as sale_op_price,
                                null as pur_qty,
                                null::Numeric  as pur_price,
                                null::Numeric as total_qty,
                                null::Numeric as total_price,
                                null as vendor_name,
                                null as vendor_add,
                                null as vendor_bin,
                                null as challan_no,
                                null as challan_date,                               
                                sop.name as sale_product, 
                                sop.product_uom_qty as sale_qty, 
                                sop.price_subtotal as sale_price, 
                                null as sale_sd,
                                sop.price_tax::Numeric as sale_vat,					
                                rp.name as customer_name,
                                CONCAT(rp.street ,',',  rp.street2,',',rp.city,',',rc.name) as customer_add, 
                                rp.vat as customer_bin,					
                                so.name as sale_challan,
                                null as sale_challan_date,					
                                null as clo_qty,
                                null as clo_price, 
                                null as comments,
                                null as product_uom                
                            FROM
				                    account_move as am  
				            LEFT JOIN sale_order as so ON am.invoice_origin = so.name
                                LEFT JOIN sale_order_line as sop ON sop.order_id = so.id
                            LEFT JOIN res_partner as rp
                                ON sop.order_partner_id=rp.id
                            LEFT JOIN res_country as rc
                                ON rp.country_id = rc.id
                            WHERE sop.invoice_status = 'invoiced' AND am.type='out_invoice'
                                AND am.invoice_date >='%s' AND  am.invoice_date <='%s'        AND sop.product_id = '%s'     
                        """ %(first_of_month.date(),last_of_month,product_id)



            main_quey = pur_query + """UNION""" + sale_query + """ORDER BY date ASC""" 
            self.env.cr.execute(main_quey)           
            datas = self.env.cr.fetchall()

            for q_line in datas:
                if sn > 1:
                    o_s_month_qty = float(row_lines[-1]['clo_qty']) 
                    o_s_month_price = float(row_lines[-1]['clo_price'])

                clo_stock = o_s_month_qty + q_line[4]  if  q_line[4] != None else clo_stock
                clo_stock = clo_stock - q_line[14]  if  q_line[14] != None else clo_stock
                
                clo_price = o_s_month_price + q_line[5]  if q_line[5] != None else o_s_month_price
                clo_price = clo_price  -  q_line[15]  if   q_line[15] != None else clo_price

                total_qty = o_s_month_qty if o_s_month_qty != None and o_s_month_qty != '-' else 0.00
                total_qty = total_qty + q_line[4] if q_line[4]  != None and q_line[4] != '-'  else total_qty
                total_price = o_s_month_price if o_s_month_price != None and o_s_month_price != '-' else 0.00
                total_price = total_price + q_line[5]  if q_line[5]  != None and q_line[5] != '-'  else total_price


                row = {
                    'ser_num' : sn,                    
                    'date': q_line[1],
                    'sale_op_stock': str(o_s_month_qty),
                    'sale_op_price': str(o_s_month_price),
                    'pur_qty': q_line[4],
                    'pur_price': q_line[5],
                    'total_qty': total_qty,
                    'total_price': total_price,
                    'vendor_name': q_line[8],
                            'vd_street': q_line[9].split(",")[0] if q_line[9] != None else '',
                            'vd_street2': q_line[9].split(",")[1] if q_line[9] != None else '',
                            # 'vd_area': q_line[9].split(",")[2] if q_line[9] != None else '',
                            'vd_city': q_line[9].split(",")[2] if q_line[9] != None else '',
                            'vd_country': q_line[9].split(",")[3] if q_line[9] != None else '',
                    # 'vendor_add': q_line[9],
                    'vendor_bin': q_line[10],
                    'pur_challan': q_line[11],
                    'pur_challan_date': q_line[12],
                    'sale_product': q_line[13],
                    'sale_qty': q_line[14],
                    'sale_price': q_line[15],
                    'sale_sd': q_line[16],
                    'sale_vat': q_line[17],
                    'customer_name': q_line[18],
                            'street': q_line[19].split(",")[0] if q_line[19] != None else '',
                            'street2': q_line[19].split(",")[1] if q_line[19] != None else '',
                            # 'area': q_line[19].split(",")[2] if q_line[19] != None else '',
                            'city': q_line[19].split(",")[2] if q_line[19] != None else '',
                            'cus_country':  q_line[19].split(",")[3] if q_line[19] != None else '',

                    # 'customer_add': q_line[19],
                    'customer_bin': q_line[20],
                    'sale_challan': q_line[21],
                    'sale_challan_date': q_line[22],
                    'clo_qty': clo_stock,
                    'clo_price':clo_price,
                    'comments': q_line[25],
                    'product_uom': product.product_tmpl_id.uom_id.name
                }
                row_lines.append(row)  
                sn += 1

            
            if len(row_lines) > 0:        
                pages.append({'row_lines': row_lines, 'product_header' : product.name})

        #Decimal Conversion
        for page in pages:
            for line in page['row_lines']:
                for key,value in line.items():
                    if line[key] != False and  line[key] != None and  line[key] != '' and line[key] != '-':                    
                        line[key] = "%.2f" % float(line[key]) if key in ['clo_qty','clo_price','sale_op_stock','sale_op_price','pur_qty','pur_price','total_qty','total_price','sale_qty','sale_price','sale_sd','sale_vat'] else line[key]

            #-----------------------------------------------------------------------------
        if len(pages) == 0:
            row_lines =[]
            sn = 1
            row = { 
                    'ser_num' : '',                    
                    'date': '',      
                    'sale_op_stock': '',      
                    'sale_op_price': '',      
                    'pur_qty': '',      
                    'pur_price': '',      
                    'total_qty': '',      
                    'total_price': '',      
                    'vendor_name': '',      
                    'vd_street': '',      
                    'vd_street2': '',      
                    'vd_area': '',      
                    'vd_city': '',      
                    'vendor_bin': '',      
                    'pur_challan': '',      
                    'pur_challan_date': '',      
                    'sale_product': '',      
                    'sale_qty': '',      
                    'sale_price': '',      
                    'sale_sd': '',      
                    'sale_vat': '',      
                    'customer_name': '',      
                    'street': '',      
                    'street2': '',      
                    'area': '',      
                    'city': '',      
                    'customer_bin': '',      
                    'sale_challan': '',      
                    'sale_challan_date': '',      
                    'clo_qty':'',      
                    'clo_price': '',      
                    'comments': '',  
                    'product_uom': '',  
            }
            row_lines.append(row) 


            footers = {
            'print_date': self.report_time,
            'pg_no' : '1',
            'pg_toto':'1'
            }
            pages.append({'row_lines': row_lines, 'product_header' : ''})
        #---------------------------------------------------------------------------------

        #ManOrder Finished Product
        #Sales
        #Closing Stock
        footers = {
            'print_date': self.report_time,
            'pg_no' : '1',
            'pg_toto':'1'
            }

    
        headers=[{
                            'name': self.company_id.name,
                            'street': self.company_id.street,
                            'street2': self.company_id.street2,
                            'zip': self.company_id.zip,
                            'vat':self.company_id.vat,
                        }]


        if self.language == 'bangla':
            headers[0]['zip'] = bangla.convert_english_digit_to_bangla_digit(str(headers[0]['zip']))
            headers[0]['vat'] = bangla.convert_english_digit_to_bangla_digit(str(headers[0]['vat']))

            for page in pages:                
                for line in page['row_lines']:                         
                    for key,value in line.items():                     
                        if key not in ['vendor_name','vd_street','vd_street2', 'vd_area','vd_city','pur_challan','sale_product','customer_name','street','street2','city','sale_challan','comments','area']:
                            if key not in ['date','pur_challan_date','sale_challan_date','vendor_bin','customer_bin']:
                                line[key] ="%.2f" % float(line[key]) if line[key] != None and line[key] != '' and line[key] != '-' else line[key]
                            line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key])) if line[key] != None else ''


        data['headers'] = headers
        data['pages'] = pages
        data['footers'] = footers
        return data

    def _print_report(self):
        raise NotImplementedError()

    def print_preview(self): 
        data = self._build_contexts()  
        # import pdb; pdb.set_trace()
        return self.env.ref('evl_vat.purchase_sale_preview').report_action(self, data=data)


    def print_mushak_6_2_1(self):
        data = self._build_contexts()     
        return self.env.ref('evl_vat.report_mushak_purchase_sale').report_action(self, data=data)



#-------------------------------------------------------Mushak 6.2.1: Tax Book -----------------------------------------------------------------

class ReportMushakTaxBook(models.Model):
    _name = 'mushak.tax'
    _description = 'Mushak 6.3 (Tax Book)'

    sale_order = fields.Many2one('sale.order', string='Sale Order')    
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    report_time = fields.Datetime('report Datetime', compute='compute_display_time')

    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='landscape', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)

    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id


    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)

    def _build_contexts(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('stock.inventory', 'purchase.order')
        data['form'] = self.read()[0]
        


        first_of_month = datetime.today().replace(day=1)      
        last_of_month =  last_day_of_month(datetime.date(first_of_month))
        result = {}
        result['company_id'] = data['form']['company_id'][0] or False
        pages=[]            
        sale_orders =  self.env['sale.order'].search([('date_order','>=',first_of_month),('invoice_status','=','invoiced'),('date_order','<=',last_of_month)])
        
        if data['form']['sale_order'] == False:
            sale_orders =  self.env['sale.order'].search([('date_order','>=',first_of_month),('invoice_status','=','invoiced'),('date_order','<=',last_of_month)])

        else:
            sale_orders = self.env['sale.order'].search([('id','=', data['form']['sale_order'][0])])

        customers = sale_orders.partner_id
        for customer in customers:            
            cus = {
                        'cus_name' : customer.name,                    
                        'cus_bin': customer.vat,
                        'cus_street': customer.street,               
                        'cus_street2': customer.street2, 
                        'cus_city': customer.city, 
                        'cus_country': customers.country_id.name     
                    }

            row_lines = []   

            if data['form']['sale_order'] == False:
                sos = self.env['sale.order'].search([('date_order','>=',first_of_month),('invoice_status','=','invoiced'),('date_order','<=',last_of_month),
                                                ('partner_id','=',customer.id)])
            else:
                sos = sale_orders
            for so in sos:
                sn = 1
                for sol in so.order_line:            

                    row = {
                        'sn': sn,
                        'pro_name': sol.product_id.name,
                        'pro_unit':sol.product_uom.name,
                        'pro_qty': sol.product_uom_qty,
                        'pro_unit_price': "%.2f" % round(sol.price_unit,2), 
                        'pro_untax': "%.2f" % round(sol.untaxed_amount_invoiced,2), 
                        'pro_sd': 0,
                        'pro_vat_percent': str(int(sol.tax_id.amount)) + "%",
                        'pro_vat': "%.2f" % round(sol.price_tax, 2),  
                        'pro_total': "%.2f" % round(sol.price_subtotal, 2),

                    }
                    sn += 1
                    row_lines.append(row)    

            sale_or = {
                'amt_vatsd': "%.2f" % round(0,2),
                'amt_untaxed':   "%.2f" % round(so.amount_untaxed,2),
                'amt_tax':  "%.2f" % round( so.amount_tax,2),
                'amt_total': "%.2f" % round( so.amount_total,2),
            }
            pages.append({'row_lines': row_lines, 'product_header' : 'test', 'customer': cus , 'sale_or': sale_or })


        # result = {}
        # result['company_id'] = data['form']['company_id'][0] or False
        # result['pages'] = pages
        # result['totals'] ={} 

        
        headers=[{
                            'name': self.company_id.name,
                            'street': self.company_id.street,
                            'street2': self.company_id.street2,
                            'city': self.company_id.city,
                            'zip': self.company_id.zip,
                            'country': self.company_id.country_id.name,
                            'vat': self.company_id.vat,
                            'report_date': self.report_time.date(),
                            'report_time': self.report_time.time(),
                        }]

        if self.language == 'bangla':
            # headers[0]['zip'] = bangla.convert_english_digit_to_bangla_digit(str(headers[0]['zip']))
            # headers[0]['vat'] = bangla.convert_english_digit_to_bangla_digit(str(headers[0]['vat']))

            for page in pages:                
                for line in page['row_lines']:                         
                    for key,value in line.items():            
                        
                        if key not in ['pro_name','pro_unit']:
                            line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key])) if line[key] != None else ''
                
                page['sale_or']['amt_vatsd'] = bangla.convert_english_digit_to_bangla_digit(page['sale_or']['amt_vatsd']) if page['sale_or']['amt_vatsd'] != None else ''
                for key,value in sale_or.items():            
                    sale_or[key] = bangla.convert_english_digit_to_bangla_digit(str(sale_or[key])) if sale_or[key] != None else ''

        data['headers'] = headers
        data['pages'] = pages
        data['totals'] = {} 
        # import pdb; pdb.set_trace()
        return data

    def _print_report(self,data):
        raise NotImplementedError()


    def print_preview(self): 
        data = self._build_contexts()  
        return self.env.ref('evl_vat.tax_book_preview').report_action(self, data=data)

    def print_mushak_tax(self):
        data = self._build_contexts()       
        return self.env.ref('evl_vat.report_mushak_tax_book').report_action(self, data=data)




#-------------------------------------------------------'Mushak 6.5 (Transfer Book)'-----------------------------------------------------------------

class ReportMushakTransferBook(models.Model):
    _name = 'mushak.transfer'
    _description = 'Mushak 6.5 (Transfer Book)'

    transfer_order = fields.Many2one('stock.picking', string='Transfer Order', domain="[('picking_type_id','=', 5),('state','=','done')]" , default=False    )  
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    report_time = fields.Datetime('report Datetime', compute='compute_display_time')


    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='landscape', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)
    

    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id
        
            
    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)


    def _build_contexts(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('stock.inventory', 'purchase.order')
        data['form'] = self.read()[0]
        


        first_of_month = datetime.today().replace(day=1)      
        last_of_month =  last_day_of_month(datetime.date(first_of_month))

        result = {}
        result['company_id'] = data['form']['company_id'][0] or False
        pages=[]            
        t_os =  self.env['stock.picking'].search([('date_done','>=',first_of_month),('date_done','<=',last_of_month),('picking_type_id','=', 5),('state','=','done')])
        
        if len(self.transfer_order) > 0:
            t_os = self.env['stock.picking'].sudo().search([('id','=',data['form']['transfer_order'][0])])
        elif len(self.transfer_order) == 0:
            t_os = self.env['stock.picking'].search([('date_done','>=',first_of_month),('date_done','<=',last_of_month),('picking_type_id','=', 5),('state','=','done')])
            
        pages=[] 
        for t_o in t_os:
            pg_toto = len(t_os)
            pg_no = 1
            page ={}

            wh_id = self.env['stock.warehouse'].sudo().search([('view_location_id','=',t_o.location_id.location_id.id)])

            wh_desid = self.env['stock.warehouse'].sudo().search([('view_location_id','=',t_o.location_dest_id.location_id.id)])

           
            headers=        {
                                'company' : t_os.company_id.name,
                                'bin'  : t_os.company_id.vat,
                                'sender': wh_id.name,
                                'sen_street' :  wh_id.company_id.street,
                                'sen_street2' :  wh_id.company_id.street2,
                                'sen_city' :  wh_id.company_id.city,
                                'sen_country' : wh_id.company_id.country_id.name,
                                'receiver': wh_desid.name,
                                'challan': t_o.name,
                                'issue_dt': t_o.date_done.date(),
                                'issue_tm': t_o.date_done.time(),
                            }

            footers = {
                'report_date': self.report_time,
                'cn_pg': pg_no,
                'total_pg': pg_toto,
            }
            
            body = {}
            lines = []
            for line in t_o.move_ids_without_package:
                sn = 1
                row = {
                    'sn':sn,
                    'pro_name' : line.product_id.name,
                    'pro_qty' : "%.2f" % line.quantity_done,
                    'pro_untaxed_pr' : "%.2f" % line.product_id.standard_price,
                    'pro_tax_per' : self.env['product.template'].search([('id','=', line.product_tmpl_id.id)]).hscode.vat.amount,
                    'comments' : '',
                }
                lines.append(row)
                sn += 1
            print(lines)
            

            body['lines'] = lines
            body['qty_tot'] =   "%.2f" % sum(map(lambda x: float(x['pro_qty']), lines))
            body['untaxed_tot'] = "%.2f" % sum(map(lambda x: float(x['pro_untaxed_pr']), lines))
            body['tax_per'] = ''#sum(map(lambda x: int(x['pro_tax_per']), lines))
            
            page['headers'] = headers
            page['body'] = body        
            page['footers'] = footers                     


            pages.append(page)   
            pg_no += 1      
        
        
        if self.language == 'bangla':
            for page in pages:                
                for line in page['body']['lines']:                         
                    for key,value in line.items():            
                        
                        if key not in ['pro_name','comments']:
                            line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key])) if line[key] != None else ''
                page['body']['qty_tot'] = bangla.convert_english_digit_to_bangla_digit(page['body']['qty_tot']) if page['body']['qty_tot'] != None else ''
                page['body']['untaxed_tot']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['untaxed_tot']) if page['body']['qty_tot'] != None else ''
                page['body']['tax_per']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['tax_per']) if page['body']['tax_per'] != None else ''




        data['company_id'] = data['form']['company_id'][0] or False
        data['pages'] = pages

        return data




    def _print_report(self, data):
        raise NotImplementedError()

    def print_preview(self): 
        data = self._build_contexts()  
        return self.env.ref('evl_vat.transfer_preview').report_action(self, data=data)

    def print_mushak_transfer(self):
        data = self._build_contexts()  

        return self.env.ref('evl_vat.report_mushak_transfer').report_action(self, data=data)




#------------------------------------------------------------
#--------Mushak 6.4 Contractual Production Book -----------------------------------------------------------------

class ReportMushakContract(models.Model):
    _name = 'mushak.contract'
    _description = 'Mushak 6.4 (Contractual Production Book)'

        
    contract_order = fields.Many2one('mrp.production', string='Contract Number',
                        domain="[('bom_id.type','in', ['subcontract']),]" ,default=False    )
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)




    report_time = fields.Datetime('report Datetime', compute='compute_display_time')

    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='landscape', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)


    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id
    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)
    
    def _build_contexts(self, data):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('stock.inventory', 'purchase.order')
        data['form'] = self.read()[0]        



        first_of_month = datetime.today().replace(day=1)      
        last_of_month =  last_day_of_month(datetime.date(first_of_month))


            
        pages=[] 

        pg_no = pg_toto = 1
        page ={}
        sender= {
                    'name' : self.company_id.name,
                    'bin'  : self.company_id.vat,
                    'address': self.company_id.city,
                    'challan_no': self.contract_order.origin,
                    'issue_date'    : self.report_time.date(),
                    'issue_time'    : self.report_time.time(),
                }
        receiver= {
                    'name' : self.contract_order.bom_id.subcontractor_ids.name,
                    'bin'  : self.contract_order.bom_id.subcontractor_ids.vat,
                    'rec_add'  : self.contract_order.bom_id.subcontractor_ids.city if self.contract_order.bom_id.subcontractor_ids.city != False else self.contract_order.bom_id.subcontractor_ids.country_id.name,
                }            
        headers=        {
                            'sender': sender,
                            'receiver': receiver,
                        }

        footers = {
                        'print_date': self.report_time,
                        'pg_no' : pg_no,
                        'pg_toto':pg_toto
                    }
        
        body = {}
        lines = []
        sum = 0
        for pro in self.contract_order.move_raw_ids:
            sum += pro.product_uom_qty
            sn = 1
            line = {
                'sn':sn,
                'pro_type' : 'Raw Materials',
                'pro_uom' : pro.product_id.name ,
                'pro_qty' : str(pro.product_uom_qty) + ' ' + pro.product_uom.name,
                'comment' : '',
            }
            lines.append(line)
            
            sn += 1

        sum_line = {
                'sn':'',
                'pro_type' : '',
                'pro_uom' : 'সর্বমোট' ,
                'pro_qty' : str(sum),
                'comment' : '',
            }
        lines.append(sum_line)

        body['lines'] = lines
        page['headers'] = headers
        page['body'] = body        
        page['footers'] = footers 
        pages.append(page)   
        pg_no += 1       


        if self.language == 'bangla':
            for page in pages:                
                for line in page['body']['lines']:                         
                    for key in line.items():        
                        
                        if key not in ['pro_type','pro_uom','comment']:
                            if key=='pro_qty':
                                line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key].split(" ")[0])) + line[key].split(" ")[1] if line[key] != None else ''
                            else:
                                line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key]))  if line[key] != None else ''
                # page['body']['qty_tot'] = bangla.convert_english_digit_to_bangla_digit(page['body']['qty_tot']) if page['body']['qty_tot'] != None else ''
                # page['body']['untaxed_tot']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['untaxed_tot']) if page['body']['qty_tot'] != None else ''
                # page['body']['tax_per']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['tax_per']) if page['body']['tax_per'] != None else ''



        data['company_id'] = data['form']['company_id'][0] or False

        rows = self._build_contexts(data)       
        data['pages'] = pages

        return data

    def _print_report(self, data):
        raise NotImplementedError()


    def print_preview(self): 
        data = self._build_contexts({})  
        return self.env.ref('evl_vat.contract_preview').report_action(self, data=data)

    def print_mushak_contract(self):

        return self.env.ref('evl_vat.report_mushak_contract').report_action(self, data=data)



#-------------------------------------------------!!!---------------------------------------------------------

#----------------------------------------------working  ---------Mushak 6.7 Credit Note -----------------------------------------------------------------

class ReportMushakCreditNote(models.Model):
    _name = 'mushak.credit'
    _description = 'Mushak 6.7 (Credit Note)'

    credit_note = fields.Many2one('account.move', string='Credit Note Number' , domain="[('reversed_entry_id','!=', False),('state','=','posted'),('type','=','out_refund')]" ,
    default=False   ,required=True )
    #in_refund--->Vendor Credit ,out_refund--> Customer Credit Note, 
    # Credit Note-->Sales Return, Debit Note -->Purchase returns
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    report_time = fields.Datetime('report Datetime', compute='compute_display_time')

    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='landscape', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)
    

    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id

    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)

    def _build_contexts(self, data):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('stock.inventory', 'purchase.order')
        data['form'] = self.read()[0]        



        first_of_month = datetime.today().replace(day=1)      
        last_of_month =  last_day_of_month(datetime.date(first_of_month))

        if len(self.credit_note) > 0:
            credit_acs = self.env['account.move'].sudo().search([('id','=',data['form']['credit_note'][0])])
        elif len(self.credit_note) == 0:
            credit_acs = self.env['account.move'].sudo().search([('reversed_entry_id','!=', False),('state','=','posted'),('type','=','out_refund')])
            
        pages=[] 
        for credit_ac in credit_acs:
            pg_toto = len(credit_acs)
            pg_no = 1
            page ={}
            sender= {
                        'name' : credit_ac.invoice_partner_display_name,
                        'bin'  : credit_ac.partner_id.vat,
                        'main_challan'  : credit_ac.reversed_entry_id.name,
                        'issue_date'    : credit_ac.date,
                    }
            receiver= {
                        'name' : credit_ac.company_id.name,
                        'bin'  : credit_ac.company_id.vat,
                        'credit_note'  : credit_ac.name,
                        'credit_issue_dt'    : credit_ac.create_date.date(),
                        'credit_issue_tm'    : credit_ac.create_date.time(),
                    }            
            headers=        [{
                                'sender': sender,
                                'receiver': receiver,
                            }]

            footers = {
                'print_date': self.report_time,
                'pg_no' : pg_no,
                'pg_toto':pg_toto
            }
            
            body = {}
            lines = []
            for line in credit_ac.invoice_line_ids:
                sn = 1
                line = {
                    'sn':sn,
                    'pro_name' : line.name,
                    'pro_uom' : line.product_uom_id.name,
                    'pro_qty' : line.quantity,
                    'pro_unit_price' : "%.2f" % round(line.price_unit,2),
                    'pro_subtotal' : "%.2f" % round(line.price_subtotal,2),
                }
                lines.append(line)

                sn += 1

            body['lines'] = lines
            body['total'] = "%.2f" % round(credit_ac.amount_untaxed,2)
            body['discount'] =  "%.2f" % 0.0

           
            body['taxed_amt'] = str("%.2f" % round(credit_ac.amount_total,2)) 
            body['taxed_vat'] = "%.2f" % round(credit_ac.amount_by_group[0][1],2)  #[('Tax 15%', 78.0, 520.0, '78.00 ৳', '520.00 ৳', 1, 2)]
            body['pro_sd'] = "%.2f" % 0.0
            body['pro_vat_total'] =  "%.2f" % round(credit_ac.amount_by_group[0][1],2)  #[('Tax 15%', 78.0, 520.0, '78.00 ৳', '520.00 ৳', 1, 2)]
            body['rt_reason'] = data['form']['credit_note'][1].split(",")[1] if data['form']['credit_note'][1].split(",")[1] != '' else ''
            page['headers'] = headers
            page['body'] = body        
            page['footers'] = footers 

                       


            pages.append(page)   
            pg_no += 1       


            if self.language == 'bangla':
                for page in pages:                
                    for line in page['body']['lines']:                         
                        for key,value in line.items():     
                            
                            if key not in ['pro_name','pro_uom','comment']:
                                line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key]))  if line[key] != None else ''
                    page['body']['total'] = bangla.convert_english_digit_to_bangla_digit(page['body']['total']) if page['body']['total'] != None else ''
                    page['body']['taxed_amt']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['taxed_amt']) if page['body']['taxed_amt'] != None else ''
                    page['body']['taxed_vat']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['taxed_vat']) if page['body']['taxed_vat'] != None else ''
                    page['body']['pro_sd']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['pro_sd']) if page['body']['pro_sd'] != None else ''
                    page['body']['pro_vat_total']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['pro_vat_total']) if page['body']['pro_vat_total'] != None else ''
                    page['body']['discount']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['discount']) if page['body']['discount'] != None else ''



            data['company_id'] = data['form']['company_id'][0] or False
    
            data['pages'] = pages
            
                
            return data

    def _print_report(self, data):
        raise NotImplementedError()

    def print_preview(self): 
        data = self._build_contexts({})  
        return self.env.ref('evl_vat.credit_preview').report_action(self, data=data)


    def print_credit_note(self):
        data = self._build_contexts({})  
        return self.env.ref('evl_vat.report_mushak_credit_note').report_action(self, data=data)



#-------------------------------------------------!!!---------------------------------------------------------

#----------------------------------------Mushak 6.8 Debit Note ---------------------------------

class ReportMushakDebitNote(models.Model):
    _name = 'mushak.debit'
    _description = 'Mushak 6.8 (Debit Note)'

    debit_note = fields.Many2one('account.move', string='Debit Note Number' , domain="[('state','=','posted'),('type','=','in_refund')]" ,
                        default=False  ,required=True )  
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    report_time = fields.Datetime('report Datetime', compute='compute_display_time')


    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='landscape', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)



    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id


    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)

    def _build_contexts(self, data):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('stock.inventory', 'purchase.order')
        data['form'] = self.read()[0]        



        if len(self.debit_note) > 0:
            debit_acs = self.env['account.move'].sudo().search([('id','=',data['form']['debit_note'][0])])
        elif len(self.debit_note) == 0:
            debit_acs = self.env['account.move'].sudo().search([('state','=','posted'),('type','=','in_refund')])
            
        pages=[] 
        for debit_ac in debit_acs:
            pg_toto = len(debit_acs)
            pg_no = 1
            page ={}
            sender= {
                        'name' : debit_ac.company_id.name, 
                        'bin'  : debit_ac.company_id.vat,
                        'main_challan'  : debit_ac.reversed_entry_id.name,
                        'issue_date'    : debit_ac.date,
                    }
            receiver= {
                        'name' : debit_ac.invoice_partner_display_name,
                        'bin'  :  debit_ac.partner_id.vat,
                        'debit_note'  : debit_ac.name,
                        'debit_issue_dt'    : debit_ac.create_date.date(),
                        'debit_issue_tm'    : debit_ac.create_date.time(),
                    }            
            headers=        [{
                                'sender': sender,
                                'receiver': receiver,
                            }]

            footers = {
                'print_date': self.report_time,
                'pg_no' : pg_no,
                'pg_toto':pg_toto
            }
            
            body = {}
            lines = []
            for line in debit_ac.invoice_line_ids:
                sn = 1
                line = {
                    'sn':sn,
                    'pro_name' : line.name,
                    'pro_uom' : line.product_uom_id.name,
                    'pro_qty' : line.quantity,
                    'pro_unit_price' : "%.2f" % round(line.price_unit,2),
                    'pro_subtotal' : "%.2f" % round(line.price_unit,2),
                }
                lines.append(line)

                sn += 1

            body['lines'] = lines
            body['total'] = "%.2f" % round(debit_ac.amount_untaxed,2)
            body['discount'] = "%.2f" % 0
            body['taxed_amt'] =   "%.2f" % round(debit_ac.amount_total,2)      
            body['taxed_vat'] = "%.2f" % round(debit_ac.amount_by_group[0][1],2) if len(debit_ac.amount_by_group) > 0 else "%.2f" % 0
            body['pro_sd'] = "%.2f" % 0
            body['pro_vat_total'] =  "%.2f" % round(debit_ac.amount_by_group[0][1],2) if len(debit_ac.amount_by_group) > 0 else "%.2f" % 0#[('Tax 15%', 78.0, 520.0, '78.00 ৳', '520.00 ৳', 1, 2)]
            body['rt_reason'] = data['form']['debit_note'][1].split(",")[1].split(")")[0] if len(data['form']['debit_note'][1].split(",")) > 1 else ''
            page['headers'] = headers
            page['body'] = body        
            page['footers'] = footers                     
            pages.append(page)   
            pg_no += 1       




            if self.language == 'bangla':
                for page in pages:                
                    for line in page['body']['lines']:                         
                        for key,value in line.items():    
                            
                            if key not in ['pro_name','pro_uom','comment']:
                                line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key]))  if line[key] != None else ''
                    page['body']['total'] = bangla.convert_english_digit_to_bangla_digit(page['body']['total']) if page['body']['total'] != None else ''
                    page['body']['taxed_amt']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['taxed_amt']) if page['body']['taxed_amt'] != None else ''
                    page['body']['taxed_vat']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['taxed_vat']) if page['body']['taxed_vat'] != None else ''
                    page['body']['pro_sd']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['pro_sd']) if page['body']['pro_sd'] != None else ''
                    page['body']['pro_vat_total']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['pro_vat_total']) if page['body']['pro_vat_total'] != None else ''
                    page['body']['discount']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['discount']) if page['body']['discount'] != None else ''




            data['company_id'] = data['form']['company_id'][0] or False

            data['pages'] = pages

            return data

    def _print_report(self, data):
        raise NotImplementedError()

    def print_preview(self): 
        data = self._build_contexts({})  
        return self.env.ref('evl_vat.debit_preview').report_action(self, data=data)



    def print_debit_note(self):
        data = self._build_contexts({})  

        

        return self.env.ref('evl_vat.report_mushak_debit_note').report_action(self, data=data)




#-----------------------------------------Mushak 6.10 (Purchase-Sale Book above 2 Lakhs Taka)------------------------------------------------------------------

class ReportMushakTwoLakhs(models.Model):
    _name = 'mushak.twolakhs'
    _description = 'Mushak 6.10 (Purchase-Sale Book above 2 Lakhs Taka)'

    report_type = fields.Selection([
                ('month', 'Month Wise'),
                ('date', 'Date Wise')], string='Report Type',
                default='month', help="Defines how a report will be generated(month-wise or date-wise)", required=True)
    month = fields.Selection(
                        [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ], 
                        string='Month')
    year = fields.Selection(get_years(), string='Year', dafault='10')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    product_selection = fields.Boolean(
        'All Product', default=True,
        help="By checking this product selection field, you select all products.")
    product_id = fields.Many2one(
        'product.product', 'Product',## ('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), 
        domain="[('categ_id.name','=','Raw Material'),('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        )
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    report_time = fields.Datetime('report Datetime', compute='compute_display_time')

    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='landscape', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)



    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id


    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)
    def _build_contexts(self, data):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('sale.order.line', 'purchase.order.line')
        data['form'] = self.read()[0]
        



        result = {}
        result['company_id'] = data['form']['company_id'][0] or False

        if self.report_type == 'month':
            from datetime import datetime
            first_of_month = datetime.today().replace(month=int(self.month)).replace(year=int(self.year)).replace(day=1)
            import datetime
            last_of_month =  last_day_of_month(datetime.date(first_of_month.year,first_of_month.month,1 ))

        else:
            first_of_month = data['form']['date_from'] or False
            last_of_month = data['form']['date_to'] or False

        pages=[] 

        page ={} 
        pg_no = pg_toto =1
        headers=        {
                            'company': self.company_id.name,
                            'bin': self.company_id.vat,
                        }

        footers = {
            'print_date': self.report_time,
            'pg_no' : pg_no,
            'pg_toto':pg_toto
        }
        #Purchase
        pur_lines = []
        
        pur_o = self.env['purchase.order'].search([('amount_untaxed','>=',200000),\
                                                        ('state','=','purchase'),
                                                        ('invoice_status','=','invoiced'),
                                                        ('date_approve','>=', first_of_month.date()),
                                                         ('date_approve','<=', last_of_month),
        
                                                        ], order='id asc')
        sn = 1
        import pdb; pdb.set_trace()
        for po in pur_o:                                          

            
            pur = {
                'sn': sn,
                'challan' :  po.name,
                'issue_date' : po.date_approve.date(),
                'price_subtotal' :   "%.2f" % round( po.amount_untaxed,2),   
                'ven_name' : po.partner_id.name,
                'ven_add' :
                            {
                                'street': po.partner_id.street,
                                'street2': po.partner_id.street2,
                                'city': po.partner_id.city,
                                'country': po.partner_id.country_id.name,
                            },
                'bin' : po.partner_id.vat,
            }
            pur_lines.append(pur)
            sn += 1

        pur_total = "%.2f" %(sum(map(lambda x: float(x['price_subtotal']), pur_lines)))

        #Sales
        sale_lines = []
        
        sale_o = self.env['sale.order'].search([('amount_untaxed','>=',200000),\
                                                        ('state','=','sale'),
                                                        ('invoice_status','=','invoiced'),
                                                        ('date_order','>=', first_of_month.date()),
                                                        ('date_order','<=', last_of_month)], order='id asc')       
        sn = 1
        for sol in sale_o:                                             

            
            sale = {
                'sn': sn,
                'challan' :  sol.name,
                'issue_date' : sol.date_order.date(),
                'price_subtotal' : "%.2f" % round( sol.amount_untaxed,2),     
                'cus_name' : sol.partner_id.name,
                'cus_add' :
                            {'street':sol.partner_id.street,
                            'street2':sol.partner_id.street2,
                            'city': sol.partner_id.city,
                            'country': sol.partner_id.country_id.name,
                            },
                'bin' : sol.partner_id.vat,
            }
            sale_lines.append(sale)
            sn += 1
        sale_total = "%.2f" %(sum(map(lambda x: float(x['price_subtotal']), sale_lines)))

        body = {}
        
        body['purchase'] = {'pur_lines': pur_lines , 'pur_total': pur_total}
        body['sales'] = {'sale_lines': sale_lines , 'sale_total': sale_total}

        page['headers'] = headers
        page['body'] = body        
        page['footers'] = footers                     
        pages.append(page)   


 #-----------------------------------------------------------------------------
        if len(pages) == 0:
            pur_lines =[]
            sn = 1
            pur = {
                'sn': '',
                'challan' :  '',
                'issue_date' :'',
                'price_subtotal' :   '',   
                'ven_name' : '',
                'ven_add' :
                            {
                                'street':'',
                                'street2':'',
                                'city': '',
                                'country': '',
                            },
                'bin' : '',
            }
            pur_lines.append(pur)
            sn += 1


            sale_lines =[]
            sn = 1
            sale = {
                'sn':'',
                'challan' : '',
                'issue_date' : '',
                'price_subtotal' : '',
                'cus_name' : '',
                'cus_add' :
                            {'street':'',
                            'street2':'',
                            'city': '',
                            'country': '',
                            },
                'bin' : '',
            }
            sale_lines.append(sale)
            sn += 1

            footers = {
                    'print_date': self.report_time,
                    'pg_no' : '1',
                    'pg_toto':'1'
                    }
            pur_total = ''
            sale_total = ''
            body['purchase'] = {'pur_lines': pur_lines , 'pur_total': pur_total}
            body['sales'] = {'sale_lines': sale_lines , 'sale_total': sale_total}

            page['headers'] = headers
            page['body'] = body        
            page['footers'] = footers                     
            pages.append(page)   

        #---------------------------------------------------------------------------------





        if self.language == 'bangla':
            for page in pages:                
                for line in page['body']['purchase']['pur_lines']:                         
                    for key,value in line.items():   
                        
                        if key in ['sn','issue_date', 'price_subtotal','bin']:
                            line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key]))  if line[key] != None else ''
                for line in page['body']['sales']['sale_lines']:                         
                    for key,value in line.items():   
                        
                        if key in ['sn','issue_date', 'price_subtotal','bin']:
                            line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key]))  if line[key] != None else ''


                page['body']['purchase']['pur_total'] = bangla.convert_english_digit_to_bangla_digit(page['body']['purchase']['pur_total']) if page['body']['purchase']['pur_total'] != None else ''
                page['body']['sales']['sale_total']     =      bangla.convert_english_digit_to_bangla_digit(page['body']['sales']['sale_total'] ) if page['body']['sales']['sale_total']  != None else ''
             






        data['company_id'] = data['form']['company_id'][0] or False
        data['pages'] = pages
        # import pdb; pdb.set_trace()

        return data

    def _print_report(self, data):
        raise NotImplementedError()



    def print_preview(self): 
        data = self._build_contexts({})  
        return self.env.ref('evl_vat.twolakhs_preview').report_action(self, data=data)


    def print_mushak_6_10(self):
        data = self._build_contexts({})  
        return self.env.ref('evl_vat.report_mushak_twolakhs').report_action(self, data=data)




#-----------------------------------------'TR-6 (Treasury Challan)'------------------------------------------------------------------

class ReportTreasury(models.Model):
    _name = 'mushak.treasury'
    _description = 'TR-6 (Treasury Challan)'


    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    voucher = fields.Many2one('evl.payments', 'Voucher', required=True)
    report_time = fields.Datetime('report Datetime', compute='compute_display_time')
    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='landscape', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='bangla', required=True)

    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id

    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)

    def _build_contexts(self, data):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('sale.order.line', 'purchase.order.line')
        data['form'] = self.read()[0]       

        pages=[] 

        page ={} 
        pg_no = pg_toto =1
        headers=        {
                            'company': self.company_id.name,
                            'bin': self.company_id.vat,
                        }

        footers = { 'print_date': self.report_time, 'pg_no' : pg_no, 'pg_toto':pg_toto}
        pay = self.env['evl.payments'].search([('id','=',data['form']['voucher'][0])])       
        address = self.company_id.street if self.company_id.street != False else ''
        address =  address + ',' + self.company_id.street2 if self.company_id.street != False else address
        address =  address + ',' + self.company_id.zip if self.company_id.zip != False else address
        address =  address + ',' + self.company_id.country_id.name if self.company_id.country_id.name != False else address



        p = inflect.engine()

        body= {
            'name': self.company_id.name,
            'address': address,
            'purpose': dict(pay._fields['purpose'].selection).get(pay.purpose),
            'pay_type': pay.payment_method,
            'amount':  "%.2f" % round(  pay.amount,2), 
            'date': pay.date_submit,
            'words': p.number_to_words(int(pay.amount)) + ' taka only',
            'paisa':  "0." + str(round(  pay.amount,2)).split(".")[1],

            'challan' : pay.challan,
            'date_submit' : pay.date_submit,
            'bank' : pay.bank,
            'branch' : pay.branch,


        }      


        page['headers'] = headers
        page['body'] = body        
        page['footers'] = footers                     
        pages.append(page)   

        if self.language == 'bangla':
            for page in pages: 
                    line = page['body']                   
                    for key,value in page['body'].items()  :                         
                        if key in ['amount','date','paisa']:
                            line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key]))  if line[key] != None else ''

        data['company_id'] = data['form']['company_id'][0] or False
        data['pages'] = pages
        return data

    def _print_report(self, data):
        raise NotImplementedError()


    def print_preview(self): 
        data = self._build_contexts({})  
        return self.env.ref('evl_vat.treasury_preview').report_action(self, data=data)


    def print_treasury(self):
        data = self._build_contexts({})  
        return self.env.ref('evl_vat.mushak_treasury_action').report_action(self, data=data)
