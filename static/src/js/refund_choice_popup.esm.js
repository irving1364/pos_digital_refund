/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { useState } from "@odoo/owl";

export class RefundChoicePopup extends AbstractAwaitablePopup {
    static template = "pos_digital_refund.RefundChoicePopup";
    static defaultProps = {
        title: "¿Cómo desea dar el vuelto?",
        body: "Seleccione el método de devolución del cambio",
        confirmText: "Continuar",
        cancelText: "Cancelar",
    };

    setup() {
        super.setup();
        this.state = useState({
            refundMethod: 'digital', // 'digital' o 'cash'
        });
    }

    getPayload() {
        return {
            refundMethod: this.state.refundMethod,
        };
    }
}