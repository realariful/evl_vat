from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from odoo.addons import decimal_precision as dp


class ExpensesBankPayment(models.Model):
    _name = 'expense.bank.payments'
    _inherit = ['mail.thread']

    name = fields.Char(string=u'Name', copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('expense.bank.payments'))
    description = fields.Text(string=u'Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('done', 'Posted'),
        ], string='Status', copy=False, index=True, readonly=True, store=True, default="draft", track_visibility='onchange',
        help="Status of the expense payments.")
    payment_line_ids = fields.One2many('expense.bank.payments.lines', 'payment_id', readonly=True, states={'draft': [('readonly', False)]})
    total_expense_amount = fields.Float(string='Total Amount', compute="_compute_total_expense_amount", digits=dp.get_precision('Account'))
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    journal_id = fields.Many2one('account.journal', string='Journal Type', required=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env['res.company']._company_default_get('expense.bank.payments'))
    expense_date = fields.Datetime(string='Date', copy=False, default=fields.Datetime.now, index=True, readonly=True, states={'draft': [('readonly', False)]})
    posted_date = fields.Date(string='Posted Date', copy=False, readonly=True)
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    expense_account_id = fields.Many2one(string=u'Bank/Cash Account', comodel_name='account.account', domain=[('user_type_id', '=', 3)], ondelete='cascade', required=True, track_visibility='onchange')
       
    def approve_expense(self):
        all_order_status = [i.state for i in self]

        if all(i=='approved' for i in all_order_status):
            if self.env.user.has_group('evl_expenses.evl_expenses_admin') or self.env.user.has_group('base.group_system'):            
                for orders in self:
                    orders.action_post()              
            else:
                raise ValidationError(_("User Not Authorized to perform this action"))

        else:
            raise ValidationError(_("Status must be 'Approved'"))

    def _compute_total_expense_amount(self):
        for payment in self:
            if payment.payment_line_ids:
                total_amount = 0.00
                for line in payment.payment_line_ids:
                    total_amount += line.expense_amount

                payment.total_expense_amount = total_amount
            else:
                payment.total_expense_amount = 0.0

    @api.onchange('payment_line_ids')
    def _onchange_payment_line_ids(self):
        active_ids = self.env.context.get('active_ids', False)
        active_model = self.env.context.get('active_model', False)
        if not self.payment_line_ids and active_model and active_ids:
            payment_data = []
            for active_id in active_ids:
                expense_obj = self.env['account.expenses'].browse(active_id)
                payment_data.append((0, 0, {
                    'expense_id': expense_obj.id,
                    'payment_id': self.id,
                    'expense_amount': expense_obj.amount,
                    'reference': expense_obj.reference,
                    'expense_type_id': expense_obj.expense_type_id.id,
                    }))
            self.payment_line_ids = payment_data

        else:
            pass
    
    def unlink(self):
        for payment in self:
            if payment.state in ['done', 'approved']:
                raise UserError(_('You can only delete a draft expense payment.'))
        super(ExpensesBankPayment, self).unlink()

    def action_approve(self):
        if self.state == 'draft':
            self.write({'state': 'approved'})

    def action_post(self):
        if self.state == 'approved':
            if any(self.payment_line_ids.mapped('expense_id').mapped(lambda exp: exp.state != 'approved')):
                raise UserError(_('Only approved expenses can be selected for payment posting'))
            
            account_move_obj = self.env['account.move']
            account_move_line_obj = self.env['account.move.line']
            
            vals = {
                'company_id': self.company_id.id,
                'journal_id': self.journal_id.id,
                'date': self.expense_date,
                'ref': self.name,
                'is_account_expense_entry': True,
                'line_ids': [],
            }
            
            account_move_lines = []

            if self.payment_line_ids:
                for line in self.payment_line_ids:
                    move_line_debit_vals = {
                        'account_id': line.expense_type_id.expense_account_id.id,
                        'debit': line.expense_amount,
                        'credit': 0.0,
                    }
                    account_move_lines.append(move_line_debit_vals)
                    
                move_line_credit_vals = {
                    'account_id': self.expense_account_id.id, 
                    'debit': 0.0,
                    'credit': self.total_expense_amount,
                }
                account_move_lines.append(move_line_credit_vals)
                
                for line in account_move_lines:
                    vals['line_ids'].append((0, 0, line))
                
                account_move_id = account_move_obj.create(vals)
                account_move_id.post()
                
                self.write({
                    'state': 'done',
                    'move_id': account_move_id.id,
                    'posted_date': account_move_id.date,
                })

                self.payment_line_ids.mapped('expense_id').write({
                    'payment_ref_id': self.id,
                    'state': 'done',
                    })

            else:
                pass


class ExpensesBankPaymentLine(models.Model):
    _name = 'expense.bank.payments.lines'
    _rec_name = 'expense_id'

    payment_id = fields.Many2one('expense.bank.payments', ondelete='cascade')
    state = fields.Selection(related='payment_id.state',readonly=True, store=True)
    expense_amount = fields.Float(string='Expense Amount', digits=dp.get_precision('Account'))
    expense_id = fields.Many2one('account.expenses', domain=[('state', '=', 'approved')])
    reference = fields.Char(string="Reference", size=200)
    expense_type_id = fields.Many2one(string=u'Expense Type', comodel_name='expenses.type', ondelete='cascade')

    @api.onchange('expense_id')
    def _onchange_expense_id(self):
        if self.expense_id:
            expense_id = self.expense_id
            self.reference = expense_id.reference
            self.expense_amount = expense_id.amount
            self.expense_type_id = expense_id.expense_type_id



