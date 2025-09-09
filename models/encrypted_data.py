from odoo import models, fields, api
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class EncryptedData(models.Model):
    _inherit = 'encrypted.data'
    
    api_url_refund = fields.Char(
        string="URL API Vuelto", 
        default="http://localhost:3000/api/pay-mobile/vuelto"
    )
    
    default_destination_id = fields.Char(string="ID Destino Predeterminado")
    default_destination_mobile = fields.Char(string="Móvil Destino Predeterminado")
    default_origin_mobile = fields.Char(string="Móvil Origen Predeterminado")
    default_twofactor_auth = fields.Char(string="Autenticación Two-Factor")
    