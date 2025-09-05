odoo.define('pos_digital_refund.EmergencyButton', [], function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class EmergencyButton extends PosComponent {
        constructor() {
            super(...arguments);
            console.log('[EMERGENCY BUTTON] Componente cargado');
        }

        get order() {
            return this.env.pos.get_order();
        }

        async onClick() {
            if (!this.order) {
                this.showPopup('ErrorPopup', {
                    title: 'Error',
                    body: 'No hay orden activa',
                });
                return;
            }

            const change = this.order.get_paid_total() - this.order.get_total_with_tax();
            const backendId = this.order.backendId || 'N/A';
            
            this.showPopup('ConfirmPopup', {
                title: 'DEBUG - Información de Orden',
                body: `
                    <strong>Total:</strong> ${this.env.pos.format_currency(this.order.get_total_with_tax())}
                    <strong>Pagado:</strong> ${this.env.pos.format_currency(this.order.get_paid_total())}
                    <strong>Cambio:</strong> ${this.env.pos.format_currency(change)}
                    <strong>Backend ID:</strong> ${backendId}
                    <strong>Estado:</strong> ${this.order.attributes.state || 'N/A'}
                `,
            });
        }
    }

    EmergencyButton.template = `
        <button class="emergency-btn btn btn-warning" t-on-click="onClick">
            <i class="fa fa-bug"/> DEBUG VUELTO
        </button>
    `;

    Registries.Component.add(EmergencyButton);
});