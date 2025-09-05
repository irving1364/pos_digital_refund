/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { registry } from "@web/core/registry";

export const DigitalRefundPaymentScreen = (PaymentScreen) =>
    class extends PaymentScreen {
        async _finalizeValidation() {
            const order = this.env.pos.get_order();
            const change = order.get_change();

            if (change > 0) {
                const { confirmed, payload } = await this.popup.add("DigitalRefundPopup", {
                    change,
                });

                if (confirmed) {
                    order.set_digital_refund_data(payload);
                }
            }

            return super._finalizeValidation(...arguments);
        }
    };

registry.category("pos_screens").extend("PaymentScreen", DigitalRefundPaymentScreen);
