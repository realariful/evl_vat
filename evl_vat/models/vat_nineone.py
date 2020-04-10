# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
import copy 
from itertools import groupby

class VatNineOne(models.Model):
    _name = 'vat.nineone'
    _description = 'VAT Nineone'


    print_name = fields.Char("print_name") 
    bin = fields.Char("bin") 
    company = fields.Char("company") 
    address = fields.Char("address") 
    business_type = fields.Char("business_type") 
    operation_type = fields.Char("operation_type") 
    tax_period = fields.Char("tax_period") 

    month = fields.Selection(
                    [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'),
                    ('5', 'May'), ('6', 'June'), ('7', 'July'), ('8', 'August'), 
                    ('9', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ], 
                    string='Month')
    year = fields.Integer( string='Year')
    
    type = fields.Integer("type") 
    last = fields.Integer("last") 
    date = fields.Char("date")     
    
    note1_z_t = fields.Char("note1_z_t")    
    note2_z_t = fields.Char("note2_z_t") 
    note3_t = fields.Char("note3_t") 
    note4_t = fields.Char("note4_t") 
    note5_t = fields.Char("note5_t") 
    note6_t = fields.Char("note6_t") 
    note7_t = fields.Char("note7_t") 
    note8_t = fields.Char("note8_t") 
    note9_t = fields.Char("note9_t") 
    zero_total_loc = fields.Char("zero_total_loc") 
    zero_total_for = fields.Char("zero_total_for") 
    exempt_total_loc = fields.Char("exempt_total_loc") 
    exempt_total_for = fields.Char("exempt_total_for") 
    standard_total_loc = fields.Char("standard_total_loc") 
    standard_total_for = fields.Char("standard_total_for") 
    nstandard_total_loc = fields.Char("nstandard_total_loc") 
    nstandard_total_for = fields.Char("nstandard_total_for") 
    specific_total_loc = fields.Char("specific_total_loc") 
    notreyat_total_loc = fields.Char("notreyat_total_loc") 
    notreyat_total_for = fields.Char("notreyat_total_for") 
    notreyatser_total_loc = fields.Char("notreyatser_total_loc") 
    notreyatser_total_for = fields.Char("notreyatser_total_for") 
    total_pur = fields.Char("total_pur") 
    note24 = fields.Char("note24") 
    note24_t = fields.Char("note24_t") 
    note25_t = fields.Char("note25_t")
    note26_t = fields.Char("note26_t")           


    note27_t = fields.Char("note27_t") 
    note28_t = fields.Char("note28_t") 
    note29 = fields.Char("note29")
    note29_t = fields.Char("note29_t") 

    note30_t = fields.Char("note30_t") 
    note30_l = fields.Char("note30_l") 
    note31_t = fields.Char("note31_t")   

    note32_t = fields.Char("note32_t")



     
    debit_note_vat = fields.Char("debit_note_vat") 
    credit_note_vat = fields.Char("credit_note_vat") 
    note33_t = fields.Char("note33_t") 
    note34_t = fields.Char("note34_t") 


    note35 = fields.Char("note35") 
    note36 = fields.Char("note36") 
    note37 = fields.Char("note37") 
    note38 = fields.Char("note38") 
    note39 = fields.Char("note39") 
    note40 = fields.Char("note40") 
    note41 = fields.Char("note41")   
    note42 = fields.Char("note42") 
    note43 = fields.Char("note43") 
    note44 = fields.Char("note44")   
    note45 = fields.Char("note45") 
    note46 = fields.Char("note46") 
    note47 = fields.Char("note47") 
    note48 = fields.Char("note48") 
    note49 = fields.Char("note49")                    
    note50 = fields.Char("note50")   
    note51 = fields.Char("note51") 




    note52 = fields.Char("note52") 
    note53 = fields.Char("note53") 
    note54 = fields.Char("note54") 
    note55 = fields.Char("note55") 


    note56 = fields.Char("note56")   
    note57 = fields.Char("note57") 
    note58 = fields.Char("note58") 
    note59 = fields.Char("note59")
    note60 = fields.Char("note60")  
    note61 = fields.Char("note61") 
    note62 = fields.Char("note62")     
    note63 = fields.Char("note63")   
        


    #------------------Rows Data
    note1_z_l = fields.Char("note1_z_l") 
    note2_z_l = fields.Char("note2_z_l")


    note10_z_l = fields.Text("note10_z_l")     
    note11_z_f = fields.Text("note11_z_f")   
    note10_z_l = fields.Text("note10_z_l")   
    note10_z_l = fields.Text("note10_z_l")   
    note10_z_l = fields.Text("note10_z_l")   
    note10_z_l = fields.Text("note10_z_l")   
    note10_z_l = fields.Text("note10_z_l")  
    note12_z_l = fields.Text("note12_z_l") 
    note13_z_f = fields.Text("note13_z_f") 
    note14_z_l = fields.Text("note14_z_l") 
    note15_z_f = fields.Text("note15_z_f") 
    note16_l = fields.Text("note16_l")
    note17_f = fields.Text("note17_f")
    note18_l = fields.Text("note18_l")
    note19_l = fields.Text("note19_l")
    note20_f = fields.Text("note20_f")
    note21_l = fields.Text("note21_l")
    note22_f = fields.Text("note22_f")

    note3_l = fields.Text("note3_l")     
    note4_l = fields.Text("note4_l")   
    note5_l = fields.Text("note5_l")   
    note6_l = fields.Text("note6_l")   
    note7_l = fields.Text("note7_l")   
    note8_l = fields.Text("note8_l")   

    note52_t = fields.Text("note52_t")     
    note53_t = fields.Text("note53_t")   
    note54_t = fields.Text("note54_t")   
    note55_t = fields.Text("note55_t")   
    note56_t = fields.Text("note56_t")
    note57_t = fields.Text("note57_t")   
    note58_t = fields.Text("note58_t") 
    note59_t = fields.Text("note59_t") 
    note60_t = fields.Text("note60_t") 
    note61 = fields.Text("note61") 
    note61_t = fields.Text("note61_t") 
    note9_t_ga = fields.Char("note9_t_ga")   
    report_date = fields.Char("report_date") 



    @api.model
    def create(self,values):
        copy_flag = values['copy_flag']
        del(values['copy_flag'])


        rec = super(VatNineOne, self).create(values)
        rec.month = values['tax_period']['month']
        rec.year = values['tax_period']['year']
        

        if copy_flag == False:
        
            for key,value in values.items():
                if key in ['note1_z_l','note2_z_l','note3_l','note4_l','note5_l','note7_l','note8_l',
                            'note10_z_l','note11_z_f', 'note12_z_l','note13_z_f','note14_z_l','note15_z_f','note15_z_f',
                            'note16_l','note17_f','note18_l','note19_l','note20_f','note21_l','note22_f']:

                    for item in value:
                        sub=self.env['subform.ka']
                        item['note_type'] = key
                        item['vat_id'] = rec.id
                        sub.create(item)

                if key in ['note24','note29']:
                    for item in value:                    
                        sub=self.env['subform.yuo']
                        item['note_type'] = key
                        item['vat_id'] = rec.id
                        sub.create(item)

                if key in ['note6_l','note18_l']:
                    for item in value:
                        sub=self.env['subform.ga']
                        item['note_type'] = key
                        item['vat_id'] = rec.id
                        sub.create(item)

                if key in ['note30_l']:
                    for item in value:
                        sub=self.env['subform.co']
                        item['note_type'] = key
                        item['vat_id'] = rec.id
                        sub.create(item)

                if key in ['note52_t','note53_t','note54_t','note55_t','note56_t','note57_t','note58_t','note59_t','note60_t','note61_t']:
                    for item in value:
                        sub=self.env['subform.cho']
                        item['note_type'] = key
                        item['vat_id'] = rec.id
                        sub.create(item)
        return rec
class SubformKa(models.Model):
    #ka, kha together
    _name = 'subform.ka'
    _description = 'Subform Ka'
    _rec_name = 'id'

    sn = fields.Char(string="Sn", required=True)
    pro_des= fields.Char(string="pro_des")
    pro_hs= fields.Char(string="pro_hs")
    pro_name= fields.Char(string="pro_name")
    pro_price= fields.Char(string="pro_price")
    pro_sd= fields.Char(string="pro_sd")
    pro_vat= fields.Char(string="pro_vat")
    pro_vat= fields.Char(string="pro_vat")
    comment = fields.Char('comment')


    note_type = fields.Char(string="note_type")

    vat_id = fields.Many2one('vat.nineone', string="Cost Id")


    def create(self,values):
        rec = super(SubformKa, self).create(values)
        return rec


class SubformKha(models.Model):
    #Yuo and Gha#NOte 24,note29
    _name = 'subform.yuo'
    _description = 'Subform Yo'
    _rec_name = 'id'

    sn = fields.Integer(string="Sn", required=True)
    cus_bin= fields.Char(string="pro_des")
    cus_name= fields.Char(string="cus_name")
    cus_address= fields.Char(string="cus_address")
    pro_price= fields.Char(string="pro_price")
    pro_vat= fields.Char(string="pro_vat")
    invoice_no= fields.Char(string="invoice_no")
    invoice_date= fields.Char(string="invoice_date")
    account_code = fields.Char('account_code')
    comment = fields.Char('comment')


    note_type = fields.Char(string="note_type")

    vat_id = fields.Many2one('vat.nineone', string="Cost Id")

    @api.model
    def create(self,values):
        rec = super(SubformKha, self).create(values)
        return rec


class SubformCo(models.Model):
    #Cho
    _name = 'subform.co'
    _description = 'Subform Cho'
    _rec_name = 'id'

    sn = fields.Integer(string="Sn", required=True)
    billentry= fields.Char(string="billentry")
    date= fields.Char(string="date")
    cus_house= fields.Char(string="cus_house")
    atv_amt= fields.Char(string="atv_amt")
    comment = fields.Char('account_code')


    note_type = fields.Char(string="note_type")

    vat_id = fields.Many2one('vat.nineone', string="Cost Id")

    @api.model
    def create(self,values):
        rec = super(SubformCo, self).create(values)
        return rec



class SubformGa(models.Model):
    #Ga
    _name = 'subform.ga'
    _description = 'Subform Ga'
    _rec_name = 'id'

    sn = fields.Char(string="Sn", required=True)
    pro_des= fields.Char(string="pro_des")
    pro_hs= fields.Char(string="pro_hs")
    pro_name= fields.Char(string="pro_name")
    pro_price= fields.Char(string="pro_price")
    pro_sd= fields.Char(string="pro_sd")
    pro_vat= fields.Char(string="pro_vat")
    pro_vat= fields.Char(string="pro_vat")
    comment = fields.Char('comment')


    note_type = fields.Char(string="note_type")

    vat_id = fields.Many2one('vat.nineone', string="Cost Id")


    def create(self,values):
        rec = super(SubformGa, self).create(values)
        return rec


class SubformCho(models.Model):
    #Ga
    _name = 'subform.cho'
    _description = 'Subform cho'
    _rec_name = 'id'

    sn = fields.Char(string="Sn", required=True)
    pro_des= fields.Char(string="pro_des")
    pro_hs= fields.Char(string="pro_hs")
    pro_name= fields.Char(string="pro_name")
    pro_price= fields.Char(string="pro_price")
    pro_sd= fields.Char(string="pro_sd")
    pro_vat= fields.Char(string="pro_vat")
    pro_vat= fields.Char(string="pro_vat")
    comment = fields.Char('comment')


    note_type = fields.Char(string="note_type")

    vat_id = fields.Many2one('vat.nineone', string="Cost Id")


    def create(self,values):
        rec = super(SubformCho, self).create(values)
        return rec