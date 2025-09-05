from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'  # Heredamos el modelo existente
    
    # Campos para la configuración del vuelto digital
    api_url_refund = fields.Char(
        string="URL API Vuelto",
        default="http://localhost:3000/api/pay-mobile/vuelto"
    )
    default_destination_id = fields.Char(
        string="ID Destino Predeterminado",
        default="V18367443"
    )
    default_destination_mobile = fields.Char(
        string="Móvil Destino Predeterminado",
        default="584241513063"
    )
    default_origin_mobile = fields.Char(
        string="Móvil Origen Predeterminado",
        default="584142591177"
    )
    default_twofactor_auth = fields.Char(
        string="Autenticación Two-Factor",
        default="00000000"
    )