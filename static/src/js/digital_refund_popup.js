/** @odoo-module */

import { useState } from "@odoo/owl";
import { AbstractAwaitablePopup } from "@point_of_sale/app/utils/abstract_awaitable_popup/abstract_awaitable_popup";
import { registry } from "@web/core/registry";

export class DigitalRefundPopup extends AbstractAwaitablePopup {
    setup() {
        super.setup();
        this.state = useState({
            bank: "",
            idNumber: "",
            phone: "",
            amount: this.props.change,
        });
    }

    getPayload() {
        
        const payload = {
            bank: this.state.bank,
            idNumber: this.state.idNumber,
            phone: this.state.phone,
            amount: parseFloat(this.state.amount) || 0
        };
        console.log("📝 Payload generado:", payload);
        return payload;
    }
}

DigitalRefundPopup.template = "DigitalRefundPopup";
DigitalRefundPopup.defaultProps = {
    title: "Vuelto Digital - Datos del Cliente",
    body: "Ingrese la información para el reembolso móvil",
};

registry.category("popups").add("DigitalRefundPopup", DigitalRefundPopup);
