from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'  # Heredamos el modelo existente
    
    # Campos para la configuración del vuelto digital
    api_url_refund = fields.Char(
        string="URL API Vuelto",
        default="http://localhost:3000/api/pay-mobile/vuelto"
    )
    