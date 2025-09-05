odoo.define('pos_digital_refund.RefundButton', [], function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class RefundButton extends PosComponent {
        async onClick() {
            const order = this.env.pos.get_order();
            const change = order.get_total_with_tax() - order.get_paid_total();
            
            if (change < 0) {
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: 'Crear Vuelto Digital',
                    body: `¿Desea generar un vuelto digital por ${this.env.pos.format_currency(-change)}?`,
                });
                
                if (confirmed) {
                    const result = await this.rpc({
                        model: 'pos.order',
                        method: 'action_create_digital_refund',
                        args: [order.backendId],
                    });
                    
                    if (result) {
                        this.showNotification('Vuelto creado: ' + result.reference);
                    }
                }
            }
        }
    }
    RefundButton.template = 'RefundButton';

    Registries.Component.add(RefundButton);

    return RefundButton;
});