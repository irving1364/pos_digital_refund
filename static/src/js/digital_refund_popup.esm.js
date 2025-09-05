/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { useState } from "@odoo/owl";

export class DigitalRefundPopup extends AbstractAwaitablePopup {
    static template = "pos_digital_refund.DigitalRefundPopup";
    static defaultProps = {
        title: "Vuelto Digital",
        body: "Ingrese los datos para el reembolso",
    };

    setup() {
        super.setup();
        this.state = useState({
            bank: "",
            idNumber: "",
            phone: "",
            amount: this.props.initialAmount || 0,
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