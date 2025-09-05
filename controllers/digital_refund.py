# controllers/digital_refund.py
from odoo import http
import json
import logging

_logger = logging.getLogger(__name__)

class DigitalRefundController(http.Controller):
    
    @http.route('/pos/save_digital_refund', type='json', auth='user')
    def save_digital_refund(self, **kwargs):
        """Endpoint que espera activamente a que la orden exista"""
        order_identifier = kwargs.get('order_identifier')
        order_name = f"Orden {order_identifier}"
        
        _logger.info("🎯 Buscando orden: %s", order_name)
        
        # Espera activa de hasta 30 segundos
        import time
        start_time = time.time()
        timeout = 30
        
        while time.time() - start_time < timeout:
            order = http.request.env['pos.order'].search([
                ('pos_reference', '=', order_name)
            ], limit=1)
            
            if order:
                # Guarda los datos
                order.write({
                    'digital_refund_bank': kwargs.get('bank'),
                    'digital_refund_id_number': kwargs.get('idNumber'),
                    'digital_refund_phone': kwargs.get('phone'),
                    'digital_refund_amount': float(kwargs.get('amount', 0)),
                })
                
                _logger.info("✅ Datos guardados en orden ID: %s", order.id)
                return {'success': True, 'order_id': order.id}
            
            _logger.info("⏳ Esperando orden... (%s segundos)", int(time.time() - start_time))
            time.sleep(1)  # Espera 1 segundo entre intentos
        
        _logger.error("❌ Timeout: Orden no encontrada después de 30 segundos")
        return {'success': False}