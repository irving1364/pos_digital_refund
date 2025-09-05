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
    
    
        
    def check_pos_config():
        configs = env['pos.config'].search([])
        for config in configs:
            print(f"\nConfiguración POS: {config.name}")
            print(f"URL API Vuelto: {config.api_url_refund}")
            print(f"Destino ID: {config.default_destination_id}")
            print(f"Destino Móvil: {config.default_destination_mobile}")
            print(f"Origen Móvil: {config.default_origin_mobile}")
            
            # Verificar si está completo
            complete = all([
                config.api_url_refund,
                config.default_destination_id,
                config.default_destination_mobile,
                config.default_origin_mobile
            ])
            
            print(f"Configuración Completa: {'✅' if complete else '❌'}")