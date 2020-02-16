from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, Warning, ValidationError


class AccountExpenses(models.Model):
    _name = 'account.expenses'
    _inherit = ['mail.thread']

    name = fields.Char(string=u'Name', size=100, readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Text(string=u'Reason')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('done', 'Posted'),
        ('refused', 'Refused')
        ], string='Status', copy=False, index=True, readonly=True, store=True, default="draft", track_visibility='onchange', 
        help="Status of the expense.")
    expense_type_id = fields.Many2one(string=u'Expense Type', comodel_name='expenses.type', ondelete='set null', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env['res.company']._company_default_get('account.expenses'))
    reference = fields.Char(string="Reference", size=200, track_visibility='onchange')
    amount = fields.Float(string='Amount', digits=dp.get_precision('Account'), track_visibility='onchange')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    payment_ref_id = fields.Many2one('expense.bank.payments', string="Payment Ref.", store=True)
    expense_creation_date = fields.Datetime(string=u'Date', copy=False, default=fields.Datetime.now, readonly=True, states={'draft': [('readonly', False)]})
    employee_ids = fields.Many2many('hr.employee', string=u'Employees', track_visibility='onchange', ondelete='restrict',
        relation = 'account_expenses_hr_employee_rel', column1='expense_id', column2 = 'employee_id', default=lambda self: self.env.user.employee_id)
    
    show_approval = fields.Boolean(default=False, compute='_compute_show_approval')

    def _compute_show_approval(self):
        current_user_id = self.env.user
        
        for expense in self:
            if current_user_id.id == 2:
                expense.show_approval = True

            elif expense.state == 'confirmed':
               
                if current_user_id.employee_id.parent_id:

                    if current_user_id.employee_id.id not in expense.employee_ids.ids:
                        expense.show_approval = True

                    else:
                        expense.show_approval = False

                elif not current_user_id.employee_id.parent_id and current_user_id.has_group('evl_expenses.evl_expenses_admin'):
                    ''' This is for MAN COM Users '''
                    expense.show_approval = True
                
                else:
                    expense.show_approval = False

            else:
                expense.show_approval = False

    @api.onchange('expense_type_id')
    def _onchange_expense_type_id(self):
        current_user_id = self.env.user.id
        matched_user_expenses_id = self.env['res.users.expenses'].search([('user_id', '=', current_user_id)])

        return {'domain':{'expense_type_id': [('approved_user_ids', '=', matched_user_expenses_id.id)]}}

    def unlink(self):
        for expense in self:
            if expense.state in ['done', 'confirmed', 'approved', 'refused']:
                raise UserError(_('You can only delete a draft expense.'))
        super(AccountExpenses, self).unlink()

    def action_confirm(self):
        if self.state == 'draft':
            self.write({'state': 'confirmed'})
            # if self.env.user.id != 2:
            #     self.show_approval = 

    def action_approve(self):
        if self.state == 'confirmed':
            self.write({'state': 'approved'})

    def _payment_function(self):
        not_doable = self.filtered(lambda r: r.state != 'approved')

        if not_doable:
            raise Warning(_('Only approved expenses are allowed!'))

        else:
            context = self.env.context
            form_id = self.env.ref('evl_expenses.view_expense_payment_form').id
            tree_id = self.env.ref('evl_expenses.view_expense_payment_tree').id

            return  {
                    'type': 'ir.actions.act_window',
                    'name': 'Payments',
                    'views': [(tree_id, 'tree'), (form_id, 'form')],
                    'view_mode': 'tree,form',
                    'view_type': 'form',
                    # 'view_id': form_id,
                    'context': context,
                    'res_model': 'expense.bank.payments',
                    'src_model': 'account.expenses',
                    'target':'current',
                    'key2':"client_action_multi",
                    # 'res_id': record_id ,
                    # but if you are using more then one view
                    # you must use views to pass mutliple ids
                    #'views': [(form_id, 'form'), (tree_id, 'tree')],
                    # and to specify the search view use
                    # 'search_view_id': search_view_id,
                }

    def approve_bulk_expenses(self):
        all_expense_status = [i.state for i in self]

        if all(i == 'confirmed' for i in all_expense_status):
            if self.env.user.has_group('evl_expenses.evl_expenses_manager') or self.env.user.has_group('base.group_system') or self.env.user.has_group('evl_expenses.evl_expenses_admin'):            
                for expenses in self:
                    expenses.action_approve()              
            else:
                raise ValidationError(_("User Not Authorized to perform this action"))

        else:
            
            raise ValidationError(_("Status must be 'Confirmed'"))


