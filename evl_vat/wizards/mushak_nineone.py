
#-*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime

from odoo import api, fields, models, _
from odoo.tools.misc import get_lang
from odoo.exceptions import UserError

from datetime import datetime,timedelta
import bangla

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



class ReportMushakVATReturn1(models.Model):
    _name = 'mushak.vatreturn'
    _description = 'Mushak 9.1 (VAT Return)'

    month = fields.Selection(
                        [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                        ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                        ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ], 
                        string='Month' , required=True)
    year = fields.Selection(get_years(), string='Year', dafault='10' , required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    product_selection = fields.Boolean(
        'All Product', default=False,
        help="By checking this product selection field, you select all products.")
    product_id = fields.Many2one(
        'product.product', 'Product',## ('bom_ids', '!=', False), ('bom_ids.active', '=', True), ('bom_ids.type', '=', 'normal'), 
        domain="[('categ_id.name','=','Raw Material'),('type', 'in', ['product', 'consu']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        )
    product_tmpl_id = fields.Many2one('product.template', 'Product Template', related='product_id.product_tmpl_id')
    report_time = fields.Datetime('report Datetime', compute='compute_display_time')
    def compute_display_time(self):
        self.report_time = get_local_time(self).replace(tzinfo=None)
        
    report_header = fields.Boolean("Report Header", default=False)
    report_title = fields.Char("Report Title",store=True)
    page_setup =  fields.Many2one('report.paperformat', string='Page Format',compute='format_id',readonly=True)
    page_orientation = fields.Selection([('portrait', 'Portrait'), ('landscape', 'Landscape')], 'Orientation', default='portrait', readonly=True)
    language = fields.Selection([('english', 'English'), ('bangla', 'Bangla')], 'Report Language', default='english', required=True)

    def format_id(self):
        self.page_setup = self.env['report.paperformat'].search([('name','=','A4')]).id


    sub_date =  fields.Date('Submission Date'  , required=True)
    # report_lang = fields.Selection([('1', 'English'), ('2', 'Bangla'), ], string='Month', default='1')
 

    def _build_contexts(self, data):
        #Need to find start date and end date
        from datetime import datetime
        first_of_month = datetime.today().replace(month=int(self.month)).replace(day=1).replace(year=int(self.year)).date()
        import datetime
        last_of_month =  last_day_of_month(datetime.date(first_of_month.year,first_of_month.month,1 ))
        # first_of_month = first_of_month.date()

        result = {}
        # result['company_id'] = data['form']['company_id'][0] or False

        
        page1={}

        address = self.company_id.street if self.company_id.street != False else ''
        address = address + ',' + self.company_id.street2 if self.company_id.street2 != False else address
        address = address + ',' + self.company_id.city if self.company_id.city != False else address
        address = address + ',' + self.company_id.country_id.name if self.company_id.country_id.name != False else address


        page1= {
            'part1':
                    {
                            'bin':self.company_id.vat,
                            'company':self.company_id.name,
                            'address':address,
                            'business_type': dict(self.company_id._fields['owner_type'].selection).get(self.company_id.owner_type),
                            'operation_type' : dict(self.company_id._fields['economic_activity'].selection).get(self.company_id.economic_activity),
                        },

                'part2': {
                            'tax_period': {'month': self.month,'year':self.year},
                            'type': '1',
                            'last':'1',
                            'date' : self.sub_date.strftime("%d/%m/%Y")
                        },

                        'pg_no': '1','report_date': self.report_time.strftime("%d/%m/%Y %H:%M")
                    }
        #--------------------------------------------------------------------------------------------
        
 
        subform = {}
        sub_ka = {}


        #COALESCE( round(  es.amount ,2), 0.00)
        #-------------------------Working
        #Query for sales Order (Note 10-20)
        #Sales query using account_move
        #Make sure everything from account_move
        sol_query_new = """ 
                        SELECT 
                            ROW_NUMBER() OVER (ORDER BY eh.hscode) as sn,
                            eh.description as pro_des,
                            eh.hscode as pro_hs,	
                            sol.name as pro_name, 
                            COALESCE(round( CAST(SUM(am.amount_untaxed) as numeric), 2),0.00) as pro_price, 
                            COALESCE(round( CAST(SUM(sol.vat_sd) as numeric), 2),0.00) as pro_sd,
                            COALESCE(round( CAST(SUM(am.amount_tax) as numeric), 2),0.00) as pro_vat,
                            so.sale_type as comment
                        FROM sale_order_line sol
                            LEFT JOIN product_product pp ON sol.product_id = pp.id
                            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                            LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                            LEFT JOIN sale_order so ON sol.order_id = so.id	
                            LEFT JOIN account_move am ON so.name = am.invoice_origin
                        WHERE so.invoice_status = 'invoiced' AND sol.sale_subtype = %s
                            AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s 
                            AND so.company_id = %s
                            AND so.sale_type = %s AND so.sale_type2 = %s
                        GROUP BY eh.description,eh.hscode,sol.name,so.sale_type

                        """ 
        soltot_query_new = """
                          SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(round( CAST(SUM(am.amount_untaxed) as numeric), 2),0.00) as pro_price, 
                                COALESCE(SUM(sol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(am.amount_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                                
                                FROM sale_order_line sol


                                LEFT JOIN product_product pp ON sol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN sale_order so ON sol.order_id = so.id	
                                LEFT JOIN account_move am ON so.name = am.invoice_origin
    
                                WHERE so.invoice_status = 'invoiced' AND sol.sale_subtype = %s
                                        AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  
                                        AND so.company_id = %s
                                        AND so.sale_type = %s AND so.sale_type2 = %s


                                """



        sol_query = """ 
                        SELECT 
                            ROW_NUMBER() OVER (ORDER BY eh.hscode) as sn,
                            eh.description as pro_des,
                            eh.hscode as pro_hs,	
                            sol.name as pro_name, 
                            COALESCE(round( CAST(SUM(am.amount_untaxed) as numeric), 2),0.00) as pro_price, 
                            COALESCE(round( CAST(SUM(sol.vat_sd) as numeric), 2),0.00) as pro_sd,
                            COALESCE(round( CAST(SUM(am.amount_tax) as numeric), 2),0.00) as pro_vat,
                            so.sale_type as comment
                        FROM sale_order_line sol
                            LEFT JOIN product_product pp ON sol.product_id = pp.id
                            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                            LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                            LEFT JOIN sale_order so ON sol.order_id = so.id	
                            LEFT JOIN account_move am ON so.name = am.invoice_origin
                        WHERE so.invoice_status = 'invoiced' AND sol.sale_subtype = %s
                            AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s 
                            AND so.company_id = %s
                            AND so.sale_type = %s
                        GROUP BY eh.description,eh.hscode,sol.name,so.sale_type

                        """ 
        soltot_query = """
                          SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(round( CAST(SUM(am.amount_untaxed) as numeric), 2),0.00) as pro_price, 
                                COALESCE(SUM(sol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(am.amount_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                                
                                FROM sale_order_line sol


                                LEFT JOIN product_product pp ON sol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN sale_order so ON sol.order_id = so.id	
                                LEFT JOIN account_move am ON so.name = am.invoice_origin
    
                                WHERE so.invoice_status = 'invoiced' AND sol.sale_subtype = %s
                                        AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  
                                        AND so.company_id = %s
                                        AND so.sale_type = %s


                                """
      
        sol_total = """
                        SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(round( CAST(SUM(am.amount_untaxed) as numeric), 2),0.00) as pro_price, 
                                COALESCE(SUM(sol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(am.amount_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                                
                                FROM sale_order_line sol


                                LEFT JOIN product_product pp ON sol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN sale_order so ON sol.order_id = so.id	
                                LEFT JOIN account_move am ON so.name = am.invoice_origin
    
                                WHERE so.invoice_status = 'invoiced'  
                                        AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s AND so.company_id =%s

                                """


        row_loc =   [{'sn' : '-','pro_des' : '-', 'pro_hs' : '-', 'pro_name' : '-', 'pro_price' : 0.00, 'pro_sd' : 0.00, 'pro_vat' : 0.00, 'comment' : '',} ]
        row_for =   [{'sn' : '-', 'pro_des' : '-', 'pro_hs' : '-', 'pro_name' : '-', 'pro_price' : 0.00, 'pro_sd' : 0.00, 'pro_vat' : 0.00, 'comment' : '', } ]


        #<t t-esc="'%.2f'%(pages['page2']['sub_ka']['note1_z_t'][0]['pro_price'])" /></div>
        sol_Cat = ['zero','exempt','standard', 'high', 'specific', 'not_reyat','retail']
        for cate in sol_Cat:
            if cate == 'zero':
                #direct
                self.env.cr.execute(sol_query_new, (cate, first_of_month, last_of_month,self.company_id.id,'foreign','direct'))   
                note1_z_l = self.env.cr.dictfetchall() 
                
                self.env.cr.execute(soltot_query_new, (cate, first_of_month,last_of_month,self.company_id.id,'foreign','direct')) 
                note1_z_t = self.env.cr.dictfetchall()

                #indirect
                self.env.cr.execute(sol_query_new, (cate, first_of_month,last_of_month,self.company_id.id,'foreign','indirect'))   
                note2_z_l = self.env.cr.dictfetchall() 
                self.env.cr.execute(soltot_query_new, (cate, first_of_month,last_of_month,self.company_id.id,'foreign','indirect'))     
                note2_z_t = self.env.cr.dictfetchall() 
                note1_z_l = row_loc if len(note1_z_l) == 0 else note1_z_l
                note2_z_t = row_for if len(note2_z_l) == 0 else note2_z_l 


                note1_ka = note1_z_t[0]['pro_price']  
                note1_kha = 0.0#note1_z_t[0]['pro_sd']    -->not shown in main form but shown in subform
                note1_ga = 0.0#note1_z_t[0]['pro_vat']    -->not shown in main form but shown in subform

                note2_ka = note2_z_t[0]['pro_price']  
                note2_kha = 0.0#note1_z_t[0]['pro_sd']    -->not shown in main form but shown in subform
                note2_ga = 0.0#note1_z_t[0]['pro_vat']    -->not shown in main form but shown in subform

                


            if cate == 'exempt':               
                #Local
                self.env.cr.execute(sol_query, ('exempt', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note3_l = self.env.cr.dictfetchall() 
                self.env.cr.execute(soltot_query, ('exempt', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note3_t = self.env.cr.dictfetchall() 
                note3_l = row_loc if len(note3_l) == 0 else note3_l

                note3_ka = note3_t[0]['pro_price']  
                note3_kha = 0.0#note1_z_t[0]['pro_sd']    -->not shown in main form but shown in subform
                note3_ga = 0.0#note1_z_t[0]['pro_vat']    -->not shown in main form but shown in subform
            if cate == 'standard':
                #Local
                self.env.cr.execute(sol_query, ('standard', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note4_l = self.env.cr.dictfetchall() 
                self.env.cr.execute(soltot_query, ('standard', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note4_t = self.env.cr.dictfetchall() 
                note4_l = row_loc if len(note4_l) == 0 else note4_l

            if cate == 'high':
                #Local
                self.env.cr.execute(sol_query, ('high', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note5_l = self.env.cr.dictfetchall() 
                self.env.cr.execute(soltot_query, ('high', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note5_t = self.env.cr.dictfetchall() 
                note5_l = row_loc if len(note5_l) == 0 else note5_l
                
            if cate == 'specific':
                #Local                
                self._cr.execute(sol_query, ('specific', first_of_month, last_of_month,self.company_id.id,'local'))  
                note6_l = self.env.cr.dictfetchall() 
                self._cr.execute(soltot_query, ('specific', first_of_month, last_of_month,self.company_id.id,'local' ))  
                note6_t = self.env.cr.dictfetchall()                
                note6_l = row_loc if len(note6_l) == 0 else note6_l
              
            if cate == 'not_reyat':
                self._cr.execute(sol_query, ('not_reyat', first_of_month, last_of_month,self.company_id.id,'local'))  
                note7_l = self.env.cr.dictfetchall() 
                self._cr.execute(soltot_query, ('not_reyat', first_of_month, last_of_month,self.company_id.id,'local' ))  
                note7_t = self.env.cr.dictfetchall()                
                note7_l = row_loc if len(note7_l) == 0 else note7_l

            if cate == 'retail':
                #Local                
                self._cr.execute(sol_query, ('retail', first_of_month, last_of_month,self.company_id.id,'local'))  
                note8_l = self.env.cr.dictfetchall() 
                self._cr.execute(soltot_query, ('retail', first_of_month, last_of_month,self.company_id.id,'local' ))  
                note8_t = self.env.cr.dictfetchall()                
                note8_l = row_loc if len(note8_l) == 0 else note8_l

        self.env.cr.execute(sol_total, (first_of_month, last_of_month,self.company_id.id,))   
        note9_t = self.env.cr.dictfetchall() 


        # print("-----------------")
        note9_t_ga = note9_t[0]['pro_vat']



        #Purchase order starts

        #VAT Query
        rows_query = """ 
                            SELECT 
                                    ROW_NUMBER() OVER (ORDER BY eh.hscode) as sn,
                                    eh.description as pro_des,
                                    eh.hscode as pro_hs,	
                                    pol.name as pro_name, 
                                    ROUND(SUM(pol.price_subtotal),2) as pro_price, 
                                    COALESCE(SUM(pol.vat_sd), 0.00 ) as pro_sd,
                                    round( CAST(SUM(pol.price_tax) as numeric), 2) as pro_vat,
                                    po.purchase_type as comment
                                FROM purchase_order_line pol 

                                
                                LEFT JOIN product_product pp ON pol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN purchase_order po ON pol.order_id = po.id	
                                 LEFT JOIN account_move as am ON po.id = am.bill_origin
    
                                WHERE po.invoice_status = 'invoiced' AND pol.purchase_subtype = %s
                                        AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  AND po.company_id =%s 
                                        AND po.purchase_type = %s
                       
                                GROUP BY eh.description,eh.hscode,pol.name,po.purchase_type

                        """ 
        tot_query = """
                            SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(ROUND(SUM(pol.price_subtotal),2),0.00) as pro_price, 
                                COALESCE(SUM(pol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(pol.price_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                            FROM purchase_order_line pol 
                                LEFT JOIN product_product pp ON pol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN purchase_order po ON pol.order_id = po.id	
                                LEFT JOIN account_move as am ON po.id = am.bill_origin
        
                            WHERE po.invoice_status = 'invoiced' AND pol.purchase_subtype = %s
                                    AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  AND po.company_id =%s 
                                    AND po.purchase_type = %s


                                """
      
        zero_total = """
                            SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(ROUND(SUM(pol.price_subtotal),2),0.00) as pro_price, 
                                COALESCE(SUM(pol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(pol.price_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                            FROM purchase_order_line pol 
                                LEFT JOIN product_product pp ON pol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN purchase_order po ON pol.order_id = po.id	
                                LEFT JOIN account_move as am ON po.id = am.bill_origin
                
                                WHERE (po.invoice_status = 'invoiced' AND pol.purchase_subtype = %s
                                    AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  AND po.company_id =%s  AND po.purchase_type =%s )
                                OR 
                                    (po.invoice_status = 'invoiced' AND pol.purchase_subtype = %s
                                            AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  AND po.company_id =%s  AND po.purchase_type = %s) 
                       
                                """
        
        #Note 23 excludes zero and exempt
        pur_total = """
                            SELECT null as sn,
                                null as pro_des,
                                null as pro_hs,	
                                null as pro_name, 
                                COALESCE(ROUND(SUM(pol.price_subtotal),2),0.00) as pro_price, 
                                COALESCE(SUM(pol.vat_sd), 0.00 ) as pro_sd,
                                COALESCE(round( CAST(SUM(pol.price_tax) as numeric), 2),0.00) as pro_vat,
                                null as comment
                            FROM purchase_order_line pol 
                                LEFT JOIN product_product pp ON pol.product_id = pp.id
                                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                                LEFT JOIN evl_hscode eh ON pt.hscode = eh.id
                                LEFT JOIN purchase_order po ON pol.order_id = po.id	
                                LEFT JOIN account_move as am ON po.id = am.bill_origin
                
                                WHERE po.invoice_status = 'invoiced'AND DATE(am.invoice_date) >= %s  AND DATE(am.invoice_date) <= %s  AND po.company_id =%s 
                                                                     
                       
                                """
                                #  AND pol.purchase_subtype != 'zero' AND pol.purchase_subtype != 'exempt'


        row_loc =   [{
                        'sn' : '-',
                        'pro_des' : '-', 
                        'pro_hs' : '-', 
                        'pro_name' : '-', 
                        'pro_price' : 0.00, 
                        'pro_sd' : 0.00, 
                        'pro_vat' : 0.00, 
                        'comment' : 'local', 
                    } ]
        row_for =   [{
                    'sn' : '-',
                    'pro_des' : '-', 
                    'pro_hs' : '-', 
                    'pro_name' : '-', 
                    'pro_price' : 0.00, 
                    'pro_sd' : 0.00, 
                    'pro_vat' : 0.00, 
                    'comment' : 'foreign', 
                } ]
        cats = ['zero','exempt','standard', 'not_standard', 'specific', 'not_reyat','not_reyat_ser']
        for cat in cats:
            if cat == 'zero':
                #Local
                self.env.cr.execute(rows_query, (cat, first_of_month, last_of_month,self.company_id.id,'local' ))   
                note10_z_l = self.env.cr.dictfetchall() 
                self.env.cr.execute(tot_query, (cat, first_of_month,last_of_month,self.company_id.id,'local')) 
                zero_total_loc = self.env.cr.fetchall() 
                #Foreign
                self.env.cr.execute(rows_query, (cat, first_of_month,last_of_month,self.company_id.id,'foreign'))   
                note11_z_f = self.env.cr.dictfetchall() 
                self.env.cr.execute(tot_query, (cat, first_of_month,last_of_month,self.company_id.id,'foreign'))     
                zero_total_for = self.env.cr.fetchall() 
                note10_z_l = row_loc if len(note10_z_l) == 0 else note10_z_l
                note11_z_f = row_for if len(note11_z_f) == 0 else note11_z_f

                #Total Sum
                self.env.cr.execute(tot_query, ( cat, first_of_month,last_of_month,self.company_id.id,'local')) 
                zero_total = self.env.cr.fetchall() 
            
                note10_ka = zero_total_loc[0][4]  
                note10_kha = 0.0
                note10_ga = 0.0          

                note11_ka = zero_total_for[0][4]  
                note11_kha = 0.0
                note11_ga = 0.0

            if cat == 'exempt':
               
                #Local
                self.env.cr.execute(rows_query, ('exempt', first_of_month, last_of_month,self.company_id.id,'local' ))   
                note12_z_l = self.env.cr.dictfetchall() 
                self.env.cr.execute(tot_query, ('exempt', first_of_month, last_of_month,self.company_id.id,'local' ))   
                exempt_total_loc = self.env.cr.fetchall() 
                #Foreign
                self.env.cr.execute(rows_query, ('exempt', first_of_month,last_of_month,self.company_id.id,'foreign' ))   
                note13_z_f = self.env.cr.dictfetchall() 
                self.env.cr.execute(tot_query, ('exempt', first_of_month,last_of_month,self.company_id.id,'foreign' ))   
                exempt_total_for = self.env.cr.fetchall() 
                note12_z_l = row_loc if len(note12_z_l) == 0 else note12_z_l
                note13_z_f = row_for if len(note13_z_f) == 0 else note13_z_f

                note12_ka = exempt_total_loc[0][4]  
                note12_kha = 0.0
                note12_ga = 0.0          

                note13_ka = zero_total_for[0][4]  
                note13_kha = 0.0
                note13_ga = 0.0 

            #standard
            if cat == 'standard':
               
                #Local

                
                self._cr.execute(rows_query, ('standard', first_of_month, last_of_month,self.company_id.id,'local'))  
                note14_z_l = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('standard', first_of_month, last_of_month,self.company_id.id,'local'))  
                standard_total_loc = self.env.cr.fetchall() 
                #Foreign
                self._cr.execute(rows_query, ('standard', first_of_month,last_of_month,self.company_id.id,'foreign'))  
                note15_z_f = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('standard', first_of_month,last_of_month,self.company_id.id,'foreign'))    
                standard_total_for = self.env.cr.fetchall() 
                note14_z_l = row_loc if len(note14_z_l) == 0 else note14_z_l
                note15_z_f = row_for if len(note15_z_f) == 0 else note15_z_f
                #Total Sum
                # self._cr.execute(zero_total, ( 'standard', first_of_month,last_of_month,self.company_id.id,'local','standard', first_of_month,last_of_month,self.company_id.id,'foreign')) 
                # standard_total = self.env.cr.fetchall() 
                
            if cat == 'not_standard':
                #Local                
                self._cr.execute(rows_query, ('not_standard', first_of_month, last_of_month,self.company_id.id,'local'))  
                note16_l = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('not_standard', first_of_month, last_of_month,self.company_id.id,'local' ))  
                nstandard_total_loc = self.env.cr.fetchall() 
                #Foreign
                self._cr.execute(rows_query, ('not_standard', first_of_month,last_of_month,self.company_id.id,'foreign'))   
                note17_f = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('not_standard', first_of_month,last_of_month,self.company_id.id,'foreign'))     
                nstandard_total_for = self.env.cr.fetchall() 
                note16_l = row_loc if len(note16_l) == 0 else note16_l
                note17_f = row_for if len(note17_f) == 0 else note17_f
                #Total Sum
                # self._cr.execute(standard_all, ( 'not_standard', first_of_month,last_of_month,self.company_id.id,'local','not_standard', first_of_month,last_of_month,self.company_id.id,'foreign')) 
                # nstandard_total = self.env.cr.fetchall() 
                
            if cat == 'specific':
                #Local                
                self._cr.execute(rows_query, ('specific', first_of_month, last_of_month,self.company_id.id,'local'))  
                note18_l = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('specific', first_of_month, last_of_month,self.company_id.id,'local' ))  
                specific_total_loc = self.env.cr.fetchall()                
                note18_t = row_loc if len(note18_l) == 0 else note18_l


            # 'not_reyat','not_reyat_ser'
               
            if cat == 'not_reyat':
                #Local                
                self._cr.execute(rows_query, ('not_reyat', first_of_month, last_of_month,self.company_id.id,'local'))  
                note19_l = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('not_reyat', first_of_month, last_of_month,self.company_id.id,'local' ))  
                notreyat_total_loc = self.env.cr.fetchall() 
                #Foreign
                self._cr.execute(rows_query, ('not_reyat', first_of_month,last_of_month,self.company_id.id,'foreign'))   
                note20_f = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('not_reyat', first_of_month,last_of_month,self.company_id.id,'foreign'))     
                notreyat_total_for = self.env.cr.fetchall() 
                note19_l = row_loc if len(note19_l) == 0 else note19_l
                note20_f = row_for if len(note20_f) == 0 else note20_f

            if cat == 'not_reyat_ser':
                #Local                
                self._cr.execute(rows_query, ('not_reyat_ser', first_of_month, last_of_month,self.company_id.id,'local'))  
                note21_l = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('not_reyat_ser', first_of_month, last_of_month,self.company_id.id,'local' ))  
                notreyatser_total_loc = self.env.cr.fetchall() 
                #Foreign
                self._cr.execute(rows_query, ('not_reyat_ser', first_of_month,last_of_month,self.company_id.id,'foreign'))   
                note22_f = self.env.cr.dictfetchall() 
                self._cr.execute(tot_query, ('not_reyat_ser', first_of_month,last_of_month,self.company_id.id,'foreign'))     
                notreyatser_total_for = self.env.cr.fetchall() 
                note21_l = row_loc if len(note21_l) == 0 else note21_l
                note22_f = row_for if len(note22_f) == 0 else note22_f

        self.env.cr.execute(pur_total, (first_of_month, last_of_month,self.company_id.id,))   
        total_pur = self.env.cr.fetchall() 
        note23_kha = total_pur

        # 
        # 
        # 



        #Debite and credit note
        debit_sql = """SELECT COALESCE(ROUND(SUM(amount_tax),2),0.00) as debit_note_vat FROM account_move WHERE DATE(invoice_date) >= %s AND DATE(invoice_date) <= %s AND state = 'posted' AND type = 'in_refund' AND company_id=%s;"""
        self._cr.execute(debit_sql, (first_of_month, last_of_month, self.company_id.id))  
        debit_note_vat = self.env.cr.dictfetchall() 
        credit_sql = """SELECT COALESCE(ROUND(SUM(amount_tax),2),0.00) as credit_note_vat FROM account_move WHERE DATE(invoice_date) >=  %s AND DATE(invoice_date) <= %s AND state = 'posted' AND type = 'out_refund' AND company_id=%s;"""
        self._cr.execute(credit_sql, (first_of_month, last_of_month, self.company_id.id))  
        credit_note_vat = self.env.cr.dictfetchall() 



        #------------------------
        #***************************
        #VDS Query
        note24_q = """ 
                            SELECT 
                                    COALESCE(ROW_NUMBER() OVER (ORDER BY evs.name),null) as sn,
                                    COALESCE(rp.vat,null) as cus_bin,
                                    COALESCE(rp.name,null) as cus_name,	
                                    COALESCE(CONCAT(rp.street ,',',  rp.street2,',',rp.city,',',rc.name),null) as cus_address,
                                    COALESCE(ROUND(SUM(am.amount_untaxed),2),0.00) as pro_price, 
                                    COALESCE(SUM(am.amount_tax), 0.00 ) as pro_vat,
                                    COALESCE(am.name,null) as invoice_no,
                                    COALESCE(am.invoice_date,null) as invoice_date,
                                    null as account_code,
                                    null as comment
                    
                            FROM evl_vdssale evs
                                    LEFT JOIN sale_order so
                                        ON evs.sale_order = so.id 
                                    LEFT JOIN res_partner as rp
                                        ON so.partner_invoice_id =rp.id
                                    LEFT JOIN res_country as rc
                                        ON rp.country_id = rc.id
                                    LEFT JOIN account_move as am
                                        ON am.invoice_origin = so.name
    
                            WHERE 
					                    am.state = 'posted' AND 
                                        DATE(evs.date_submit) >= %s  AND DATE(evs.date_submit) <= %s AND evs.company_id = %s
                                        GROUP BY rp.vat, rp.name, rc.name, rp.street, rp.street2, rp.city, am.amount_untaxed, evs.name, am.name, am.invoice_date


                        """ 
        note24_t_q = """
                            SELECT 
                                    null  as sn,
                                    null as cus_bin,
                                    null as cus_name,	
                                    null as cus_address,
                                    SUM(am.amount_untaxed) as pro_price, 
                                    COALESCE(SUM(am.amount_tax), 0.00 ) as pro_vat,
                                    null as invoice_no,
                                    null as invoice_date,
                                    null as account_code,
                                    null as comment
                    
                                FROM evl_vdssale evs

                                LEFT JOIN sale_order so
                                    ON evs.sale_order = so.id 
                                LEFT JOIN res_partner as rp
                                    ON so.partner_invoice_id =rp.id
                                LEFT JOIN res_country as rc
                                    ON rp.country_id = rc.id
                                LEFT JOIN account_move as am
                                    ON am.invoice_origin = so.name
    
                                WHERE 
					                am.state = 'posted' AND DATE(evs.date_submit) >= %s  AND DATE(evs.date_submit) <= %s  AND evs.company_id = %s


                                """

        #VDS Sale
        self._cr.execute(note24_q, (first_of_month, last_of_month, self.company_id.id))  
        note24 = self.env.cr.dictfetchall() 
        self._cr.execute(note24_t_q, (first_of_month, last_of_month, self.company_id.id))  
        note24_t = self.env.cr.dictfetchall()    


        note25_t = 0.0
        note26_t =debit_note_vat[0]['debit_note_vat']
        note27_t = 0.0

        note28_t = note24_t[0]['pro_vat'] + note25_t + note26_t + note27_t

        
        
        note_29_q = """
                                    SELECT 
                                    ROW_NUMBER() OVER (ORDER BY evp.name) as sn,
                                    rp.vat as cus_bin,
                                    rp.name as cus_name,	
                                    CONCAT(rp.street ,',',  rp.street2,',',rp.city,',',rc.name) as cus_address,
                                    ROUND(SUM(am.amount_untaxed),2) as pro_price, 
                                    COALESCE(SUM(am.amount_tax), 0.00 ) as pro_vat,
                                    am.name as invoice_no,
                                    am.invoice_date as invoice_date,
                                    null as account_code,
                                    evp.description as comment
                                    
                    
                                FROM evl_vdspayments evp

                                LEFT JOIN purchase_order po
                                    ON evp.purchase_order = po.id 
                                LEFT JOIN res_partner as rp
                                    ON po.partner_id = rp.id
                                LEFT JOIN res_country as rc
                                    ON rp.country_id = rc.id
                                LEFT JOIN account_move as am
                                    ON am.invoice_origin = po.name
    
                                WHERE  am.state = 'posted' AND 
					 
                                DATE(evp.date_submit) >= %s  AND DATE(evp.date_submit) <= %s  AND evp.company_id = %s
                                GROUP BY rp.vat, rp.name, rc.name, rp.street, rp.street2, rp.city, am.amount_untaxed, evp.name, am.name, am.invoice_date, evp.description
                    """

        note_29_q_t= """
                            SELECT 
                                    null  as sn,
                                    null as cus_bin,
                                    null as cus_name,	
                                    null as cus_address,
                                    COALESCE(SUM(am.amount_untaxed), 0.00 ) as pro_price, 
                                    COALESCE(SUM(am.amount_tax), 0.00 ) as pro_vat,
                                    null as invoice_no,
                                    null as invoice_date,
                                    null as account_code,
                                    null as comment
                                    
                                FROM evl_vdspayments evp

                                LEFT JOIN purchase_order po ON evp.purchase_order = po.id 
                                LEFT JOIN res_partner as rp ON po.partner_id = rp.id
                                LEFT JOIN res_country as rc ON rp.country_id = rc.id
                                LEFT JOIN account_move as am ON am.invoice_origin = po.name

                                WHERE DATE(evp.date_submit) >= %s  AND DATE(evp.date_submit) <= %s  AND evp.company_id = %s
                                
        """


        #VDS Purchase
        self._cr.execute(note_29_q, (first_of_month, last_of_month, self.company_id.id))  
        note29 = self.env.cr.dictfetchall() 
        self._cr.execute(note_29_q_t, (first_of_month, last_of_month, self.company_id.id))  
        note29_t = self.env.cr.dictfetchall()  

        
        note30_t = 0.0 #Needs to be calculated  # Shwo in subform -cha
        note31_t = 0.0 #Needs to be calculated # VAT for rm for exported product manufactured
        note32_t = credit_note_vat[0]['credit_note_vat']
        note33_t = 0.0

        note34_t = note29_t[0]['pro_vat'] + note30_t + note31_t + note32_t + note33_t


        #-------------------------
        #Only added
        note35 = note9_t_ga + note23_kha[0][6] + note28_t - note34_t
        note50 = 0.0
        note36 = note35 - note50

        note9_t_kha = note9_t[0]['pro_sd']
        
        note39 = 0.0#Needs to be calculated#Debit Note SD
        note40 = 0.0#Needs to be calculated#Credit Note SD
        note41 = 0.0#Needs to be calculated
        note42 =  0.0 # Unpaid VAT Interest calculation#calculation based on note35
        note43 = 0.0 #  Unpaid SD Interest calculation    

        note45 = 0.0#Abgari sulko #Need to find out


        note44_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as dev_surcharge  FROM evl_surcharge es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.surcharge_type='pen'"""
        self._cr.execute(note44_q,(first_of_month, last_of_month, self.company_id.id))  
        note44 = self.env.cr.fetchall()[0][0] #Punishment and Fines  

        note46_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as dev_surcharge  FROM evl_surcharge es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.surcharge_type='dev'"""
        self._cr.execute(note46_q,(first_of_month, last_of_month, self.company_id.id))  
        note46 = self.env.cr.fetchall()[0][0] #Development Surcharge
        
        note47_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as dev_surcharge  FROM evl_surcharge es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.surcharge_type='info'"""

        self._cr.execute(note47_q,(first_of_month, last_of_month, self.company_id.id))  
        note47 =  self.env.cr.fetchall()[0][0]#Information Techonology Development Surcharge

        note48_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as dev_surcharge  FROM evl_surcharge es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.surcharge_type='health'"""        
        
        self._cr.execute(note48_q ,(first_of_month, last_of_month, self.company_id.id))  
        note48 = self.env.cr.fetchall()[0][0]#('health', 'Health Protection Surcharge')

        note49_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as dev_surcharge  FROM evl_surcharge es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.surcharge_type='env'"""         
        self._cr.execute(note49_q,(first_of_month, last_of_month, self.company_id.id))        
        note49 = self.env.cr.fetchall()[0][0]#('env', 'Environment Protecttion Surcharge'),


        #*******************************************
        note50 = 0.0#Last Ending VAT#Need to calculate
        note51 = 0.0#Last Ending SD
        


        #*******************************************

        #PART-8: Treasury Payments
        # print('----------------')
        import datetime
        last_month_end = first_of_month - datetime.timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        #Calculation from evl_payments model        


        note52_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'vat'"""         
        self._cr.execute(note52_q,(first_of_month, last_of_month, self.company_id.id))        
        note52 = self.env.cr.fetchall()[0][0]#Treasury Paid VAT

        note52_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
                        AND ep.purpose = 'sd' 
                        GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note52_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note52_t = self.env.cr.dictfetchall()#Treasury Paid VAT
        

        note53_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'sd'"""         
        self._cr.execute(note53_q,(first_of_month, last_of_month, self.company_id.id))        
        note53 = self.env.cr.fetchall()[0][0]#Treasury Paid SD

        note53_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				AND ep.purpose = 'sd' 
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note52_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note53_t = self.env.cr.dictfetchall()#Treasury Paid SD


        note54_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'vatin'"""         
        self._cr.execute(note54_q,(first_of_month, last_of_month, self.company_id.id))        
        note54 = self.env.cr.fetchall()[0][0]#Tvatin


        note54_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				AND ep.purpose = 'vatin' 
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note54_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note54_t = self.env.cr.dictfetchall()


        note55_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'sdin'"""         
        self._cr.execute(note55_q,(first_of_month, last_of_month, self.company_id.id))        
        note55 = self.env.cr.fetchall()[0][0]#Treasury Paid SD


        note55_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				AND ep.purpose = 'sdin' 
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note55_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note55_t = self.env.cr.dictfetchall()

        # note56_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
        #                     WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
        #                     AND es.purpose = 'surcharge' AND es.surcharge_type = 'pen' """         
        # self._cr.execute(note56_q,(first_of_month, last_of_month, self.company_id.id))        
        # note56 = self.env.cr.fetchall()[0][0]#Pena and fine
        

        note56_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'surcharge' AND es.surcharge_type='pen'"""         
        self._cr.execute(note56_q,(first_of_month, last_of_month, self.company_id.id))        
        note56 = self.env.cr.fetchall()[0][0]#Punishment and Fines  



        note56_q_t = """SELECT 
                            ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                            ep.challan as challan,
                            ep.bank as bank,	
                            ep.branch as branch,
                            ep.date_submit as date, 
                            ep.acc_code as acc_code,
                            COALESCE(ep.amount, 0.00) as amt,
                            null as comment                                 
                        FROM evl_payments as ep   
                            WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
                            AND  ep.purpose = 'surcharge' AND ep.surcharge_type='pen'
                            GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note56_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note56_t = self.env.cr.dictfetchall()





        note57_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'excise'"""         
        self._cr.execute(note57_q,(first_of_month, last_of_month, self.company_id.id))        
        note57 = self.env.cr.fetchall()[0][0]#Excide Dauty


        note57_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE( round(  ep.amount ,2), 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				AND ep.purpose = 'excise'
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note57_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note57_t = self.env.cr.dictfetchall()



        note58_q = """SELECT COALESCE( round(  es.amount ,2), 0.00) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'surcharge' AND es.surcharge_type='dev'"""         
        self._cr.execute(note58_q,(first_of_month, last_of_month, self.company_id.id))        
        data= self.env.cr.fetchall()
        note58 = data[0][0] if len(data) > 0 else 0.00




        note58_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE( round(  ep.amount ,2), 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				 AND ep.purpose = 'surcharge' AND ep.surcharge_type='dev'
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note58_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note58_t = self.env.cr.dictfetchall()

        note59_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'surcharge' AND es.surcharge_type='info'"""         
        self._cr.execute(note59_q,(first_of_month, last_of_month, self.company_id.id))        
        # import pdb; pdb.set_trace()
        data= self.env.cr.fetchall()
        note59 = data[0][0] if len(data) > 0 else 0.00#Information Techonology Development Surcharge

        note59_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				  AND ep.purpose = 'surcharge' AND ep.surcharge_type='info'
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note59_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note59_t = self.env.cr.dictfetchall()




        note60_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'surcharge' AND es.surcharge_type='health'"""         
        self._cr.execute(note60_q,(first_of_month, last_of_month, self.company_id.id))        
        data= self.env.cr.fetchall()
        note60 = data[0][0] if len(data) > 0 else 0.00


        note60_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				   AND ep.purpose = 'surcharge' AND ep.surcharge_type='health'
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note60_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note60_t = self.env.cr.dictfetchall()

        note61_q = """SELECT COALESCE(SUM(es.amount), 0.00 ) as amt  FROM evl_payments es
                            WHERE DATE(es.date_submit) >= %s  AND DATE(es.date_submit) <= %s  AND es.company_id = %s
                            AND es.purpose = 'surcharge' AND es.surcharge_type='env'"""         
        self._cr.execute(note61_q,(first_of_month, last_of_month, self.company_id.id))        
        data= self.env.cr.fetchall()
        note61 = data[0][0] if len(data) > 0 else 0.00
        # note61 = self.env.cr.fetchall()[0][0] if len(self.env.cr.fetchall()) > 0 else 0.00#('env', 'Environment Protecttion Surcharge'),



        note61_q_t = """SELECT 
                                    ROW_NUMBER() OVER (ORDER BY ep.name) as sn, 
                                    ep.challan as challan,
                                    ep.bank as bank,	
                                    ep.branch as branch,
                                    ep.date_submit as date, 
                                    ep.acc_code as acc_code,
                                    COALESCE(ep.amount, 0.00) as amt,
                                    null as comment                                   
                    
                        FROM evl_payments as ep   
                                
    
                                WHERE DATE(ep.date_submit) >= %s  AND DATE(ep.date_submit) <= %s    AND ep.company_id = %s
				   AND ep.purpose = 'surcharge' AND ep.surcharge_type='health'
                GROUP BY ep.challan, ep.bank, ep.branch, ep.date_submit, ep.name, ep.acc_code, ep.amount"""
        self._cr.execute(note61_q_t,(first_of_month, last_of_month, self.company_id.id))        
        note61_t = self.env.cr.dictfetchall()


        note37 = note9_t_kha + note39 -  note40 - note41
        note38 = note37 - note51 #0.0#N

        note62 = note53 - note38
        note63 = 0.0


        note30_l =[ {
            'sn':'1',
            'billentry':'',
            'date':'',
            'cus_house':'',
            'atv_amt':'',
            'comment':''
        }]


        # Chang note 50 and note 51
        # import pdb; pdb.set_trace()
        l_month = int(self.month) - 1 if int(self.month) -1 > 0 else 12
        l_year = int(self.year) if int(self.month) -1 > 0 else int(self.year) -1


        print(l_month,l_year)

        #Check last records
        l_check = self.env['vat.nineone'].search([('month','=',l_month),('year','=',l_year)],order='id asc',limit=1)
        if l_check:
            sub_ka['note_50'] = l_check.note_50
            sub_ka['note_51'] = l_check.note_51

        import pdb; pdb.set_trace()

        sub_ka = { 
                    'print_name':'Main Copy',
                    #Part1
                    'bin':self.company_id.vat,
                    'company':self.company_id.name,
                    'address':address,
                    'business_type': dict(self.company_id._fields['owner_type'].selection).get(self.company_id.owner_type),
                    'operation_type' : dict(self.company_id._fields['economic_activity'].selection).get(self.company_id.economic_activity),

                    #Part2
                    'tax_period': {'month': self.month,'year':self.year},
                    'type': '1',
                    'last':'1',
                    'date' : self.sub_date.strftime("%d/%m/%Y"),
                    
                    
                    'note10_z_l': note10_z_l, 'note11_z_f': note11_z_f,'zero_total_loc': zero_total_loc, 'zero_total_for': zero_total_for ,
                    'note12_z_l': note12_z_l, 'note13_z_f': note13_z_f, 'exempt_total_loc': exempt_total_loc, 'exempt_total_for': exempt_total_for ,
                    'note14_z_l': note14_z_l, 'note15_z_f': note15_z_f, 'standard_total_loc': standard_total_loc, 'standard_total_for': standard_total_for ,
                    'note16_l': note16_l, 'note17_f': note17_f, 'nstandard_total_loc': nstandard_total_loc, 'nstandard_total_for': nstandard_total_for ,
                    'note18_l': note18_l, 'specific_total_loc': specific_total_loc,
                    'note19_l': note19_l, 'note20_f': note20_f, 'notreyat_total_loc': notreyat_total_loc, 'notreyat_total_for': notreyat_total_for ,
                    'note21_l': note21_l, 'note22_f': note22_f, 'notreyatser_total_loc': notreyatser_total_loc, 'notreyatser_total_for': notreyatser_total_for ,
                    'total_pur':total_pur,
                    
                    'note1_z_l': note1_z_l,
                    'note1_z_t':note1_z_t,
                    'note2_z_l':note2_z_l,
                    'note2_z_t':note2_z_t,
                    'note3_l':note3_l,
                    'note3_t':note3_t,
                    'note4_l':note4_l,
                    'note4_t':note4_t,
                    'note5_l':note5_l,
                    'note5_t':note5_t,
                    'note6_l':note6_l,
                    'note6_t':note6_t,
                    'note7_l':note7_l,
                    'note7_t':note7_t,
                    'note8_l':note8_l,
                    'note8_t':note8_t,
                    'note9_t':note9_t,
                    'debit_note_vat' : debit_note_vat,
                    'credit_note_vat' : credit_note_vat,
                    'note24':note24,
                    'note24_t': note24_t, 
                    'note25_t':note25_t,
                    'note26_t':note26_t,
                    'note27_t':note27_t,
                    
                    'note28_t':note28_t,
                    'note29':note29,
                    'note29_t': note29_t,
                    'note30_t':note30_t,
                    'note30_l':note30_l,
                    
                    'note31_t':note31_t,
                    'note32_t':note32_t,
                    'note33_t': note33_t,
                    'note34_t': note34_t,

                    'note35':note35, 'note36':note35, 'note37':note37, 'note38':note38, 'note39':note39, 'note40':note40, 'note41':note41, 'note42':note42,
                    'note43':note43, 'note44':note44,   'note45':note45,  'note46':note46,  'note47':note47,  'note48':note48,  'note49':note49, 
                    'note50':note50 , 'note51':note51 , 

                'note52':note52 , 'note52_t':note52_t , 
                'note53':note53 , 'note53_t':note53_t , 
                'note54':note54 , 'note54_t':note54_t , 
                'note55':note55 , 'note55_t':note55_t , 
                'note56':note56 , 'note56_t':note56_t , 
                'note57':note57 , 'note57_t':note57_t , 
                'note58':note58 , 'note58_t':note58_t , 
                'note59':note59 , 'note59_t':note59_t , 
                'note60':note60 , 'note60_t':note60_t , 
                'note61':note61 , 'note61_t':note61_t , 


                'note62' : note62,
                'note63' : note63,

                'report_date':self.report_time,


                    }       
        page2={}
        page2 = {'sub_ka':sub_ka}
        pages ={'page1' : page1, 'page2' : page2 , 'sub_ka' :  sub_ka} 

        pg_no = pg_toto =1
    
        result = {}
        # result['company_id'] = data['form']['company_id'][0] or False
        result['pages'] = pages

        return result

    def _print_report(self, data,id):
        raise NotImplementedError()

    def _generate_data(self,sub_ka,rec_id):       

        ka=self.env['subform.co'].search([('id','=',rec_id)])
        for row in ka:
            if row.note_type in ['note1_z_l','note2_z_l','note3_l','note4_l','note5_l','note7_l','note8_l',
                        'note10_z_l','note11_z_f', 'note12_z_l','note13_z_f','note14_z_l','note15_z_f','note15_z_f',
                        'note16_l','note17_f','note18_l','note19_l','note20_f','note21_l','note22_f']:                    

                sub_ka[row.note_type].append(row.read(list(set(row._fields))))

        yuo=self.env['subform.yuo'].search([('id','=',rec_id)])
        for row in yuo:
            if row.note_type in ['note24','note29']:
                sub_ka[row.note_type].append(row.read(list(set(row._fields))))

        ga=self.env['subform.yuo'].search([('id','=',rec_id)])
        for row in ga:
            if row.note_type in ['note6_l','note18_l']:
                sub_ka[row.note_type].append(row.read(list(set(row._fields))))

        co=self.env['subform.yuo'].search([('id','=',rec_id)])
        for row in co:
            if row.note_type in ['note30_l']:
                sub_ka[row.note_type].append(row.read(list(set(row._fields))))


        cho=self.env['subform.yuo'].search([('id','=',rec_id)])
        for row in cho:
            if row.note_type in ['note52_t','note53_t','note54_t','note55_t','note56_t','note57_t','note58_t','note59_t','note60_t','note61_t']:
                sub_ka[row.note_type].append(row.read(list(set(row._fields))))

        sub_ka = sub_ka[0]
        len_check = len(self.env['vat.nineone'].search([('month','=',self.month),('year','=',self.year)]))
        sub_ka['print_name'] = 'Copy 1' if len_check == 1 else ('Copy 2' if len_check > 1 else 'Main Copy')

        sub_ka['tax_period'] = {}
        sub_ka['tax_period']['month'] = sub_ka['month']
        sub_ka['tax_period']['year'] = sub_ka['year']
        return sub_ka



    def convert_bangla(self,data):
        # import pdb; pdb.set_trace()
        # if self.language == 'bangla':
        sub_ka = data['pages']['sub_ka']
        
        for key,value in sub_ka.items():
            # 'note10_z_l': note10_z_l, 'note11_z_f': note11_z_f,'zero_total_loc': zero_total_loc, 'zero_total_for': zero_total_for ,
            # 'note12_z_l': note12_z_l, 'note13_z_f': note13_z_f, 'exempt_total_loc': exempt_total_loc, 'exempt_total_for': exempt_total_for ,
            # 'note14_z_l': note14_z_l, 'note15_z_f': note15_z_f, 'standard_total_loc': standard_total_loc, 'standard_total_for': standard_total_for ,
            # 'note16_l': note16_l, 'note17_f': note17_f, 'nstandard_total_loc': nstandard_total_loc, 'nstandard_total_for': nstandard_total_for ,
            # 'note18_l': note18_l, 'note17_f': note17_f, 'specific_total_loc': specific_total_loc,
            # 'note19_l': note19_l, 'note20_f': note20_f, 'notreyat_total_loc': notreyat_total_loc, 'notreyat_total_for': notreyat_total_for ,
            # 'note21_l': note21_l, 'note22_f': note22_f, 'notreyatser_total_loc': notreyatser_total_loc, 'notreyatser_total_for': notreyatser_total_for ,
            # 'total_pur':total_pur,

            if key in ['note25_t','note27_t','note28_t','note30_t','note31_t','note32_t','note33_t',
                'note34_t', 'note36', 'note35','note36','note37','note38','note39','note40',
                'note41','note42','note43','note44','note45','note46',
                'note47','note48','note49','note50','note51','note52',
                'note53' ,'note54' , 'note55', 'note56', 'note57' ,  'note58', 
                'note59', 'note60', 'note61' , 'note62' , 'note63', ]:
                sub_ka[key] =  bangla.convert_english_digit_to_bangla_digit(str(sub_ka[key])) if sub_ka[key] != None else ''


            if key in ['debit_note_vat','credit_note_vat']:
                print(key)
                # import pdb; pdb.set_trace()
                for line in sub_ka[key]:
                    line[key] = bangla.convert_english_digit_to_bangla_digit(str(line[key])) if line[key] != None else ''

            if key in ['note1_z_t','note2_z_t','note3_t','note4_t','note5_t','note6_t','note7_t','note8_t'
                ,'note9_t','note10_z_l','note11_z_f','note12_z_l','note13_z_f','note14_z_l','note15_z_f',
                'note16_l','note17_f','note18_l','note19_l','note20_f','note21_l','note22_f',
                'note8_l','note24','note29','note52_t','note53_t','note54_t','note55_t','note56_t','note57_t','note58_t',
                'note59_t','note60_t','note61_t','zero_total_loc','zero_total_for','exempt_total_loc',
                'exempt_total_for','standard_total_loc','standard_total_for','nstandard_total_loc',
                'nstandard_total_for','specific_total_loc','notreyat_total_loc',
                'notreyat_total_for','notreyatser_total_loc','notreyatser_total_for',
                'total_pur', 'note24_t', 'note29_t', 
                'note1_z_l','note2_z_l','note3_l','note4_l','note5_l','note6_l',
                'note7_l',]:


                # if key == 'note10_z_l':
                #     print(key)
                #     import pdb; pdb.set_trace()
                # if key == 'zero_total_loc':
                #     print(key)
                #     import pdb; pdb.set_trace()

                for line in sub_ka[key]:
                    
                    if type(line) == dict:
                        for key,value in line.items():   
                                if key in ['sn','pro_price','pro_sd','pro_vat']:
                                    line[key] =  bangla.convert_english_digit_to_bangla_digit(str(line[key])) if line[key] != None else ''
                                    # line['pro_sd'] =  bangla.convert_english_digit_to_bangla_digit(str(line['pro_sd'])) if line['pro_sd'] != None else ''
                                    # line['pro_vat'] =  bangla.convert_english_digit_to_bangla_digit(str(line['pro_vat'])) if line['pro_vat'] != None else ''

                    if type(line) == tuple:
                        # print(line)
                        # import pdb; pdb.set_trace()
                        line = list(line)                    
                        line[4] =  bangla.convert_english_digit_to_bangla_digit(str(line[4])) if line[4] != None else ''
                        line[5] =  bangla.convert_english_digit_to_bangla_digit(str(line[5])) if line[5] != None else ''
                        line[6] =  bangla.convert_english_digit_to_bangla_digit(str(line[6])) if line[6] != None else ''
                        sub_ka[key][0] = tuple(line)   
                        print(line)
                        # import pdb; pdb.set_trace()
                        # line['pro_price'] =  bangla.convert_english_digit_to_bangla_digit(str(line['pro_price'])) if line['pro_price'] != None else ''
                        # line['pro_sd'] =  bangla.convert_english_digit_to_bangla_digit(str(line['pro_sd'])) if line['pro_sd'] != None else ''
                        # line['pro_vat'] =  bangla.convert_english_digit_to_bangla_digit(str(line['pro_vat'])) if line['pro_vat'] != None else ''
 

        data['pages']['sub_ka'] = sub_ka
        return data

        # else:
        #     return data
            # #------------------------------------

    def check_mushak(self,data):
        check = self.env['vat.nineone'].search([('month','=',self.month),('year','=',self.year)],order='id asc',limit=1)
        if len(check) > 0:
            copy_flag=True
            sub_ka = check.read(list(set(check._fields)))
            sub_ka = self._generate_data(sub_ka,check.id)
            pages={}


            for key,value in sub_ka.items():
                if key in ['note25_t','note27_t','note28_t','note30_t','note31_t','note33_t',
                    'note34_t', 'note36', 'note35','note36','note37','note38','note39','note40',
                    'note41','note42','note43','note44','note45','note46',
                    'note47','note48','note49','note50','note51','note52',
                    'note53' ,'note54' , 'note55', 'note56', 'note57' ,  'note58', 
                    'note59', 'note60', 'note61' , 'note62' , 'note63', ]:
                    sub_ka[key] = float(sub_ka[key])
                    
                if key in ['note1_z_t','note2_z_t','note3_t','note4_t','note5_t','note6_t','note7_t','note8_t'
                    ,'note9_t','note10_z_l','note11_z_f','note12_z_l','note13_z_f','note14_z_l','note15_z_f',
                    'note16_l','note17_f','note18_l','note19_l','note20_f','note21_l','note22_f',
                    'note8_l','note24','note29','note52_t','note53_t','note54_t','note55_t','note56_t','note57_t','note58_t',
                    'note59_t','note60_t','note61_t','zero_total_loc','zero_total_for','exempt_total_loc',
                    'exempt_total_for','standard_total_loc','standard_total_for','nstandard_total_loc',
                    'nstandard_total_for','specific_total_loc','notreyat_total_loc',
                    'notreyat_total_for','notreyatser_total_loc','notreyatser_total_for',
                    'total_pur', 'note24_t','debit_note_vat', 'note29_t', 'credit_note_vat',
                    'note1_z_l','note2_z_l','note3_l','note4_l','note5_l','note6_l',
                    'note7_l',]:
                    
                    import ast

                    mm = sub_ka[key].strip('][')
                    sub_ka[key] = [ast.literal_eval(mm)] if len(mm) > 0 else []
                    if len(sub_ka[key]) > 0:
                        if type(sub_ka[key][0]) == tuple and len(sub_ka[key][0]) > 0:
                            if type(sub_ka[key][0][0]) == dict: 
                                x=[]
                                for item in sub_ka[key][0]:
                                    x.append(item)
                                sub_ka[key] = x

       
            sub_ka['copy_flag'] = True
            page1= { 'pg_no': '1','report_date': self.report_time.strftime("%d/%m/%Y %H:%M") }
            pages['sub_ka'] = sub_ka

            page2={}
            page2 = {'sub_ka':sub_ka}
            pages ={'page1' : page1, 'page2' : page2 , 'sub_ka' :  sub_ka} 

            data['pages'] = pages

        # #------------------------------------
        else:
            copy_flag=False
            rows = self._build_contexts(data)       
            data['pages'] = rows['pages']
            data['pages']['sub_ka']['copy_flag'] = False

        #------------------------------------
        rec = self.env['vat.nineone']
        rec.month = self.month
        rec.year =self.year
        
        self.env['vat.nineone'].create(data['pages']['sub_ka'],)  


        return data

    def print_preview(self): 
        data = self.check_mushak({})
        data = self.convert_bangla(data) if self.language == 'bangla' else data
        return self.env.ref('evl_vat.mushak_9_1_preview').report_action(self, data=data)


    def print_mushak_9_1(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('sale.order.line', 'purchase.order.line')
        data['form'] = self.read()[0]
        
        #Converting to bangla
        data = self.convert_bangla(data) if self.language == 'bangla' else data


        return self.env.ref('evl_vat.mushak_9_1_action').report_action(self, data=data)

 
 