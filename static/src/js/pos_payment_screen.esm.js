/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/store/models";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { useService } from "@web/core/utils/hooks";
import { DigitalRefundPopup } from "../js/digital_refund_popup.esm";
import { RefundChoicePopup } from "../js/refund_choice_popup.esm";

/*
patch(Order.prototype, {
    // Sobrescribimos el método que agrega el vuelto en efectivo
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);

        // 🔹 Si la orden tiene vuelto digital, eliminamos el pago negativo de efectivo
        if (this.digital_refund && json.statement_ids) {
            json.statement_ids = json.statement_ids.filter(st => st.amount >= 0);
        }

        return json;
    },
});
*/
patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.popup = useService("popup");
        this.orm = useService("orm");
        this.notification = useService("notification");
    },

    async _finalizeValidation() {
        const order = this.pos.get_order();
        const change = order.get_change();

        if (change > 0) {
            // 🔹 1. Mostrar primero la ventana de elección
            const { confirmed: choiceConfirmed, payload: choicePayload } = await this.popup.add(
                RefundChoicePopup
            );

            if (choiceConfirmed) {
                if (choicePayload.refundMethod === "digital") {
                    // 🔹 2. Si eligió digital → abrir DigitalRefundPopup
                    order.digital_refund_processed = true; 
                    order.digital_refund = true; 
                    const { confirmed, payload } = await this.popup.add(DigitalRefundPopup, {
                        initialAmount: change,
                    });

                    if (confirmed) {
                        try {
                            // Forzar sincronización inmediata
                            if (!order.server_id) {
                                console.log("⚡ Forzando push_single_order para guardar en servidor...");
                                await this.pos.push_single_order(order);
                            }

                            if (!order.server_id) {
                                throw new Error("No se pudo sincronizar la orden con el servidor");
                            }

                            console.log("✅ Orden sincronizada en servidor. ID:", order.server_id);

                            console.log("📤 Enviando a servidor:", {
                                order_id: order.server_id,
                                payload: payload,
                            });

                            
                            await this.orm.call(
                                "pos.order",
                                "set_digital_refund_data",
                                [order.server_id, {
                                    ...payload,
                                    digital_refund_processed: true  // ← NUEVA LÍNEA
                                }]
                            );

                            this.notification.add(`Vuelto de ${payload.amount} registrado`, {
                                type: "success",
                            });
                        } catch (error) {
                            console.error("Error:", error);
                            this.notification.add("Error al guardar vuelto: " + error.message, {
                                type: "danger",
                            });
                        }
                    }
                } else if (choicePayload.refundMethod === "cash") {
                    order.digital_refund = false;
                    // 🔹 3. Si eligió efectivo → mostrar notificación y seguir normal
                    this.notification.add("💰 El vuelto será entregado en efectivo", {
                        type: "info",
                    });
                }
            }
        }

        return super._finalizeValidation(...arguments);
    },

    async _processDigitalRefund(order, payload) {
        try {
            console.log("📤 Procesando vuelto digital:", payload);

            // Asegura que los datos sean válidos
            const processedPayload = {
                bank: payload.bank || '',
                idNumber: payload.idNumber || '',
                phone: payload.phone || '',
                amount: parseFloat(payload.amount) || 0
            };

            if (processedPayload.amount <= 0) {
                throw new Error("Monto inválido para el vuelto digital");
            }

            // Espera a que la orden tenga server_id (si es necesario)
            if (!order.server_id) {
                console.log("⏳ Esperando sincronización de orden...");
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            // Envía los datos al servidor
            const result = await this.orm.call(
                "pos.order",
                "set_digital_refund_data",
                [order.server_id, processedPayload]
            );

            console.log("✅ Vuelto digital procesado:", result);
            
            this.notification.add("✅ Vuelto digital registrado", {
                type: "success",
            });

        } catch (error) {
            console.error("❌ Error procesando vuelto digital:", error);
            this.notification.add("❌ Error: " + error.message, {
                type: "danger",
            });
            throw error;
        }
    }
});