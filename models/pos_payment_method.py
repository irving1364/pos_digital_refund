from odoo import models, fields, api

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'
    
    is_digital_refund = fields.Boolean(
        string='Es Vuelto Digital',
        default=False,
        help="Método de pago específico para vueltos digitales por pago móvil"
    )