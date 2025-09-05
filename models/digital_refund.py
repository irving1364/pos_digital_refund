from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
import logging

_logger = logging.getLogger(__name__)

class DigitalRefund(models.Model):
    _name = 'digital.refund'
    _description = 'Vuelto Digital'
    _order = 'create_date desc'
    
    name = fields.Char(
        string='Referencia', 
        required=True, 
        default=lambda self: self.env['ir.sequence'].next_by_code('digital.refund')
    )
    amount = fields.Float(string='Monto', required=True)
    invoice_number = fields.Char(string='Número de Factura')
    reference = fields.Char(string='Referencia API')
    response = fields.Text(string='Respuesta API')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Completado'),
        ('error', 'Error')
    ], string='Estado', default='draft')
    
    # Relación con pos.order modificada para asegurar compatibilidad
    pos_order_id = fields.Many2one(
        comodel_name='pos.order',
        string='Orden POS',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    config_id = fields.Many2one(
        comodel_name='encrypted.data',
        string='Configuración API'
    )
    
    # Campos relacionados para fácil acceso
    pos_reference = fields.Char(
        string='Referencia POS', 
        related='pos_order_id.pos_reference',
        store=True
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Cliente',
        related='pos_order_id.partner_id',
        store=True
    )
    
    encrypted_client = fields.Char(related='config_id.encrypted_client', store=True)
    destination_id = fields.Char(related='config_id.default_destination_id', store=True)
    destination_mobile = fields.Char(related='config_id.default_destination_mobile', store=True)
    
    def action_process_refund(self):
        """Procesar el vuelto digital a través de la API"""
        for refund in self:

            _logger.info("🔍 Configuración API: %s", refund.config_id.api_url_refund)
            _logger.info("🔍 Encrypted Client: %s", refund.config_id.encrypted_client)

            if refund.state != 'draft':
                continue
            
            # Obtener configuración de datos encriptados (singleton)
            encrypted_config = self.env['encrypted.data'].search([], limit=1)
            if not encrypted_config:
                raise UserError(_("No se encontró configuración de datos encriptados"))
            
            amount = round(float(refund.amount), 2)  # Redondea a 2 decimales
            if amount <= 0:
                raise UserError(_("El monto a devolver debe ser mayor que cero"))
            # Validar campos obligatorios
            #required_fields = {
            #    'default_destination_id': refund.config_id.default_destination_id,
            #    'default_destination_mobile': refund.config_id.default_destination_mobile,
            #    'default_origin_mobile': refund.config_id.default_origin_mobile
            #}
            
            #missing = [k for k, v in required_fields.items() if not v]
            #if missing:
            #    raise UserError(_(f"Configuración incompleta en POS: {', '.join(missing)}"))
            
            # Construir payload
            payload = {
                "encryptedClient": encrypted_config.encrypted_client,
                "encryptedMerchant": "XAhbCqpM4LIWlGq+eA85Tg==",
                "encryptedKey": "i9lmbuSvM95bN1EERt78dLEKuEzbnmlCspcs3erDSQ8=",
                "destinationId": refund.config_id.default_destination_id or "V18367443",
                "destinationMobile": refund.config_id.default_destination_mobile or "584241513063",
                "originMobile": refund.config_id.default_origin_mobile or "584142591177",
                "amount": amount,
                "invoiceNumber": refund.invoice_number,
                "twofactorAuth": refund.config_id.default_twofactor_auth or "00000000"
            }

            _logger.info("🔍 Payload enviado API: %s", payload)
            
            
            headers = {'Content-Type': 'application/json'}
            
            try:
                response = requests.post(
                    refund.config_id.api_url_refund,
                    data=json.dumps(payload),
                    headers=headers,
                    timeout=10
                )
                
                _logger.error("Este es el response de la API:")


                _logger.error(response)

                if response.status_code == 200:
                    result = response.json()
                    
                    # Manejar respuesta exitosa según la estructura esperada
                    if result.get('status') == 'success':
                        bank_response = result.get('bank_response', {})
                        transaction_response = bank_response.get('transaction_c2p_response', {})
                        
                        refund.write({
                            'state': 'done',
                            'amount': transaction_response.get('amount', refund.amount),
                            'reference': transaction_response.get('payment_reference', ''),
                            'response': json.dumps(result)
                        })
                        return {
                            'success': True,
                            'amount': transaction_response.get('amount', refund.amount),
                            'reference': transaction_response.get('payment_reference', ''),
                            'raw_response': result
                        }
                    else:
                        error_msg = result.get('message', 'Error desconocido en la API')
                        refund.write({
                            'state': 'error',
                            'response': json.dumps(result)
                        })
                        raise UserError(_("Error en API: %s") % error_msg)
                else:
                    error_msg = f"Error HTTP {response.status_code}: {response.text}"
                    _logger.error(error_msg)
                    refund.write({
                        'state': 'error',
                        'response': error_msg
                    })
                    raise UserError(_("Error de conexión: %s") % error_msg)
                    
            except Exception as e:
                error_msg = f"Error de conexión: {str(e)}"
                _logger.error(error_msg)
                refund.write({
                    'state': 'error',
                    'response': error_msg
                })
                raise UserError(_("Error de conexión: %s") % str(e))
            

    def action_create_from_pos(self, amount, order_id):
        """Crear vuelto desde el POS"""
        order = self.env['pos.order'].browse(order_id)
        if not order.exists():
            raise UserError("La orden POS no existe")
            
        refund = self.create({
            'amount': amount,
            'pos_order_id': order.id,
            'invoice_number': order.pos_reference or order.name,
            'config_id': self.env['encrypted.data'].get_encrypted_data().id
        })
        refund.action_process_refund()
        return refund.id
    
    
        
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