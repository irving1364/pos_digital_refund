from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import time
from datetime import timedelta

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    digital_refund_bank = fields.Char(string="Banco del Cliente")
    digital_refund_id_number = fields.Char(string="Cédula/RIF")
    digital_refund_phone = fields.Char(string="Teléfono Destino")
    digital_refund_amount = fields.Float(string="Monto a Devolver")
    
    digital_refund_ids = fields.One2many(
        'digital.refund', 
        'pos_order_id', 
        string='Vueltos Digitales',
        readonly=True
    )
    
    has_digital_refund = fields.Boolean(
        string='Tiene Vuelto Digital',
        compute='_compute_has_digital_refund',
        store=True
    )
    
    show_refund_button = fields.Boolean(
        string='Mostrar Botón de Vuelto',
        compute='_compute_show_refund_button',
        help="Determina si mostrar el botón de vuelto digital"
    )

    digital_refund_processed = fields.Boolean(
        string='Vuelto Digital Procesado',
        default=False,
        help="Indica que el vuelto se manejó digitalmente para evitar duplicación"
    )

    is_digital_refund = fields.Boolean(
        string='Es Vuelto Digital',
        default=False,
        help="Método de pago para vueltos digitales"
    )

    @api.model
    def _order_fields(self, ui_order):
        """Sobrescribe el método que procesa los campos de la orden"""
        _logger.info("🔄 _order_fields ejecutándose. digital_refund_processed: %s", 
                    ui_order.get('digital_refund_processed', False))
        fields = super()._order_fields(ui_order)
        
        # ✅ Elimina los pagos en efectivo negativos (vueltos) si hay vuelto digital
        if ui_order.get('digital_refund_processed', False):
            _logger.info("🔄 Detectado vuelto digital, eliminando pago en efectivo automático")
            
            # Filtra solo los pagos que NO son vueltos en efectivo
            if 'statement_ids' in fields:
                fields['statement_ids'] = [
                    st for st in fields['statement_ids'] 
                    if not (st[2].get('is_cash_count', False) and st[2].get('amount', 0) < 0)
                ]
                _logger.info("📋 statement_ids después de filtrar: %s", fields['statement_ids'])
        
        return fields
    
    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        """Procesa las líneas de pago, eliminando vueltos automáticos si es necesario"""
        
        _logger.info("🔄 _process_payment_lines ejecutándose. digital_refund_processed: %s", 
                    pos_order.get('digital_refund_processed', False))
        
        payment_lines = super()._process_payment_lines(pos_order, order, pos_session, draft)
        
        # Si se procesó vuelto digital, elimina el vuelto en efectivo
        if pos_order.get('digital_refund_processed', False):

            _logger.info("🗑️ Eliminando vuelto en efectivo automático por vuelto digital")

            _logger.info("📋 payment_lines antes de filtrar: %s", payment_lines)

            payment_lines = [
                line for line in payment_lines
                if not (line[2].get('is_cash_count', False) and line[2].get('amount', 0) < 0)
            ]

            _logger.info("📋 payment_lines después de filtrar: %s", payment_lines)
        
        return payment_lines
    
    # Añade esto al inicio de tu clase
    @api.model
    def create(self, vals):
        _logger.info("🆕 Creando orden POS con valores: %s", vals)
        return super().create(vals)

    # Sobrescribe el método de creación de pagos
    def _create_payment_lines(self, pos_order):
        _logger.info("💳 Creando líneas de pago para orden: %s", pos_order)
        payments = super()._create_payment_lines(pos_order)
        _logger.info("📋 Líneas de pago creadas: %s", payments)
        return payments

    @api.model
    def set_digital_refund_data(self, order_id, refund_data):
        """Método para guardar datos de vuelto digital y eliminar pago negativo"""
        try:
            _logger.info("🎯 Recibiendo datos para orden %s: %s", order_id, refund_data)
            
            order = self.browse(order_id)
            if not order.exists():
                _logger.error("❌ Orden no encontrada: %s", order_id)
                return False
            
            # ✅ Prepara los datos para guardar
            write_data = {
                'digital_refund_bank': refund_data.get('bank', '').strip(),
                'digital_refund_id_number': refund_data.get('idNumber', '').strip(),
                'digital_refund_phone': refund_data.get('phone', '').strip(),
                'digital_refund_amount': float(refund_data.get('amount', 0))
            }
            
            # ✅ Si es vuelto digital, marca para procesamiento especial
            if refund_data.get('digital_refund_processed', False):
                write_data['digital_refund_processed'] = True

            _logger.info("💾 Guardando datos: %s", write_data)
            
            # ✅ Guarda los datos
            order.write(write_data)
            
            _logger.info("✅ Datos guardados exitosamente en orden %s", order_id)
            
            # 🔥 ELIMINACIÓN DIRECTA DEL PAGO NEGATIVO
            if refund_data.get('digital_refund_processed', False):
                _logger.info("🔍 Buscando pagos negativos para eliminar...")
                
                # Buscar pagos en efectivo negativos
                cash_refunds = order.payment_ids.filtered(
                    lambda p: p.payment_method_id.is_cash_count and p.amount < 0
                )
                
                if cash_refunds:
                    _logger.info("🗑️ Eliminando %d pagos negativos: %s", 
                                len(cash_refunds), [(p.id, p.amount) for p in cash_refunds])
                    
                    # Eliminar los pagos negativos
                    cash_refunds.unlink()
                    
                    # Recalcular el estado de pago
                    #order._compute_amount_all()
                    
                    _logger.info("✅ Pagos negativos eliminados exitosamente")
                else:
                    _logger.info("ℹ️ No se encontraron pagos negativos para eliminar")
            
            return True
            
        except Exception as e:
            _logger.error("❌ Error al guardar datos: %s", str(e))
            return False
        
    def _debug_remove_cash_refund(self, order_id):
        """Método de debug para eliminar manualmente el vuelto en efectivo"""
        try:
            order = self.browse(order_id)
            if order.exists():
                _logger.info("🔍 DEBUG: Buscando pagos negativos en orden %s", order_id)
                
                # Buscar pagos en efectivo negativos
                cash_refunds = order.payment_ids.filtered(
                    lambda p: p.payment_method_id.is_cash_count and p.amount < 0
                )
                
                if cash_refunds:
                    _logger.info("🔍 DEBUG: Encontrados %d pagos negativos: %s", 
                                len(cash_refunds), [(p.id, p.amount) for p in cash_refunds])
                    
                    # Eliminar los pagos negativos
                    cash_refunds.unlink()
                    _logger.info("🔍 DEBUG: Pagos negativos eliminados manualmente")
                    
                    # Recalcular el estado de pago
                    #order._compute_amount_all()
                else:
                    _logger.info("🔍 DEBUG: No se encontraron pagos negativos")
        except Exception as e:
            _logger.error("🔍 DEBUG Error al eliminar pagos negativos: %s", str(e))

    @api.depends('digital_refund_ids')
    def _compute_has_digital_refund(self):
        for order in self:
            order.has_digital_refund = bool(order.digital_refund_ids)

    @api.depends('amount_paid', 'amount_total', 'has_digital_refund', 'state', 'digital_refund_processed')
    def _compute_show_refund_button(self):
        for order in self:
            # Mostrar botón si:
            # 1. Hay vuelto pendiente O ya se procesó vuelto digital
            # 2. Y no tiene vuelto digital creado todavía  
            # 3. Y la orden está pagada/finalizada
            order.show_refund_button = (
                (order.amount_paid > order.amount_total or order.digital_refund_processed) and
                not order.has_digital_refund and
                order.state in ['paid', 'done']
            )

            # Log para debugging
            _logger.info(
                "🔍 Botón vuelto - Orden: %s | paid: %s > total: %s = %s | processed: %s | has_refund: %s | state: %s | show: %s",
                order.name, order.amount_paid, order.amount_total, 
                order.amount_paid > order.amount_total, order.digital_refund_processed,
                order.has_digital_refund, order.state, order.show_refund_button
            )

    def action_create_digital_refund(self):
        """Acción mejorada para crear vuelto digital"""
        self.ensure_one()

        _logger.info("💰 Montos actuales - Paid: %s, Total: %s, Return: %s, Digital Refund Amount: %s", 
                self.amount_paid, self.amount_total, self.amount_return, self.digital_refund_amount)

        # Verifica si ya hay un vuelto en efectivo
        cash_return = self.amount_return
        if cash_return > 0:
            # Cancela el vuelto en efectivo
            self._cancel_existing_cash_refund()

        # ✅ USA EL MONTO GUARDADO EN LUGAR DE CALCULARLO
        if self.digital_refund_amount > 0:
            refund_amount = self.digital_refund_amount
            _logger.info("🔢 Usando monto guardado: %s", refund_amount)
        else:
            refund_amount = self.amount_paid - self.amount_total
            _logger.info("🔢 Calculando monto: %s - %s = %s", 
                        self.amount_paid, self.amount_total, refund_amount)

        # Validación de monto
        if refund_amount <= 0:
            raise UserError(_("No hay cambio para devolver. Monto: %s") % refund_amount)

        # Validaciones - SOLO verificar si ya se creó el vuelto digital
        if self.digital_refund_ids:
            raise UserError(_("Ya se creó un vuelto digital para esta orden. Referencia: %s") % 
                        self.digital_refund_ids[0].reference or "Pendiente")
        
        if self.digital_refund_ids:
            raise UserError(_("Ya se creó un vuelto digital para esta orden"))
        
        # Obtén la configuración CORRECTA del POS
        pos_config = self.session_id.config_id
        if not pos_config:
            raise UserError(_("No se encontró configuración de POS"))
        
        # Verifica que la URL esté configurada
        if not pos_config.api_url_refund:
            raise UserError(_(
                "URL de API no configurada. "
                "Por favor, configure la URL en: "
                "Punto de Venta → Configuración → %s → Pago Móvil"
            ) % pos_config.name)
        
        
        # Crea el vuelto digital (SOLO UNA VEZ)
        refund = self.env['digital.refund'].create({
            'pos_order_id': self.id,
            'amount': refund_amount,
            'invoice_number': self.pos_reference or self.name,
            'config_id': pos_config.id  # ← Configuración correcta
        })
        
        self._create_digital_refund_payment(refund_amount)

        # Procesa el vuelto
        try:
            result = refund.action_process_refund()
            if result.get('success'):
                message = _("Vuelto digital creado correctamente. Referencia: %s") % result.get('reference', '')
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Éxito'),
                        'message': message,
                        'sticky': False,
                        'next': {'type': 'ir.actions.act_window_close'},  # Cierra el popup
                        'type': 'success'
                    }
                }
            else:
                refund.unlink()  # Eliminar registro si falla
                error_msg = result.get('error', _('Error desconocido al procesar vuelto'))
                raise UserError(error_msg)
                
        except Exception as e:
            _logger.error("Error al crear vuelto digital: %s", str(e))
            refund.unlink()  # Eliminar registro si hay excepción
            raise UserError(_("Error al procesar vuelto: %s") % str(e))
        
    def _create_digital_refund_payment(self, refund_amount):
        """Crea el registro de pago para el vuelto digital (asiento contable)"""
        try:

            # 🔍 DEBUG: Verificar el monto del vuelto
            _logger.info("🔢 Refund amount: %s", refund_amount)
            
            if refund_amount <= 0:
                raise UserError(_("Monto de vuelto inválido: %s") % refund_amount)

            # Buscar el método de pago específico para vueltos digitales
            payment_method = self.env['pos.payment.method'].search([
                ('is_digital_refund', '=', True)
            ], limit=1)

            
            if not payment_method:
                _logger.warning("⚠️ No se encontró método de pago para vueltos digitales")
                # Crear uno automáticamente si no existe
                payment_method = self.env['pos.payment.method'].create({
                    'name': 'Vuelto Digital',
                    'is_digital_refund': True,
                    'journal_id': self.session_id.config_id.journal_id.id,
                })

            if payment_method not in self.session_id.config_id.payment_method_ids:
                _logger.info("➕ Agregando método de pago a la configuración del POS")
                self.session_id.config_id.write({
                    'payment_method_ids': [(4, payment_method.id)]
                })


            # Crear el pago negativo con la descripción específica
            payment_vals = {
                'pos_order_id': self.id,
                'payment_method_id': payment_method.id,
                'amount': -refund_amount,
                'name': f"Vuelto Digital por Pago Móvil - {self.pos_reference}",
                'payment_date': fields.Datetime.now(),
            }
            
            _logger.info("💳 Creando pago digital: %s", payment_vals)

            digital_payment = self.env['pos.payment'].create(payment_vals)
            
            
            _logger.info("✅ Pago digital creado: ID %s - %s", 
                        digital_payment.id, digital_payment.name)
            
            # ✅ ODOO RECALCULA AUTOMÁTICAMENTE - NO NECESITAS HACER NADA MÁS
            _logger.info("✅ Pago digital creado exitosamente")
            return digital_payment
            
            
        except Exception as e:
            _logger.error("❌ Error al crear pago digital: %s", str(e))
            raise UserError(_("Error al registrar el pago digital: %s") % str(e))    
        
    def _cancel_existing_cash_refund(self):
        """Cancela cualquier vuelto en efectivo existente"""
        cash_payments = self.payment_ids.filtered(
            lambda p: p.payment_method_id.is_cash_count and p.amount < 0
        )
        if cash_payments:
            cash_payments.unlink()
            self._recompute_payment_state()

    @api.model
    def _create_from_ui(self, orders):
        
        _logger.info("📦 _create_from_ui ejecutándose. Orders recibidas: %s", 
                    [(o.get('id'), o.get('data', {}).get('name')) for o in orders])
        
        order_ids = super()._create_from_ui(orders)
        
        for order_data in orders:

            _logger.info("📦 Procesando order_data: %s", order_data.get('id'))

            if order_data.get('data', {}).get('digital_refund_processed', False):

                _logger.info("🔄 Orden %s tiene digital_refund_processed=True", order_data.get('id'))
                # Buscar la orden recién creada
                pos_order = self.browse(order_data['id'])
                
                if pos_order.exists():
                    _logger.info("🔄 Eliminando vuelto en efectivo automático para orden %s", pos_order.name)
                    
                    # Eliminar pagos en efectivo negativos (vueltos)
                    cash_refunds = pos_order.payment_ids.filtered(
                        lambda p: p.payment_method_id.is_cash_count and p.amount < 0
                    )
                    
                    if cash_refunds:
                        _logger.info("🗑️ Eliminando %d pagos de vuelto en efectivo: %s", 
                                    len(cash_refunds), [(p.id, p.amount) for p in cash_refunds])
                        cash_refunds.unlink()
                        
                        # Recalcular el estado de pago
                        pos_order._recompute_payment_state()
                    else:
                        _logger.info("ℹ️ No se encontraron pagos negativos para eliminar")
            
            # Tu código existente para guardar datos de vuelto digital
            if order_data.get('digital_refund_data'):

                _logger.info("💾 Guardando digital_refund_data para orden %s", order_data.get('id'))

                pos_order = self.browse(order_data['id'])
                pos_order.write({
                    'digital_refund_bank': order_data['digital_refund_data']['bank'],
                    'digital_refund_id_number': order_data['digital_refund_data']['id_number'],
                    'digital_refund_phone': order_data['digital_refund_data']['phone'],
                    'digital_refund_amount': order_data['digital_refund_data']['amount'],
                })
                
                # Crear registro de vuelto digital
                self.env['digital.refund'].create({
                    'pos_order_id': pos_order.id,
                    'amount': order_data['digital_refund_data']['amount'],
                    'invoice_number': pos_order.pos_reference,
                    'bank': order_data['digital_refund_data']['bank'],
                    'customer_id_number': order_data['digital_refund_data']['id_number'],
                    'customer_phone': order_data['digital_refund_data']['phone'],
                })
        
        return order_ids