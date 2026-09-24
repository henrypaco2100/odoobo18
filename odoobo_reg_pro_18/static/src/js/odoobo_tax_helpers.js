/** @odoo-module **/

import { accountTaxHelpers } from "@account/helpers/account_tax";
import { patch } from "@web/core/utils/patch";

function odooboDynamicAmount(tax, rawBase, evaluationContext) {
    if (!tax.sd_tipo_pro_reg) {
        return null;
    }
    const product = evaluationContext.product || {};
    const amount = Math.abs(product.sd_amount_impuesto || 0);
    const mode = Number(product.sd_tax_calc_mode || 1);
    const kindSign = ["pro", "coe_pro"].includes(tax.sd_tipo_pro_reg) ? 1 : -1;

    if (mode === 1) {
        const priceSign = (evaluationContext.price_unit || 0) < 0 ? -1 : 1;
        return kindSign * priceSign * (evaluationContext.quantity || 0) * amount;
    }
    if (mode === 2 || mode === 3) {
        return kindSign * rawBase * amount / 100.0;
    }
    return 0;
}

patch(accountTaxHelpers, {
    eval_tax_amount_fixed_amount(tax, batch, rawBase, evaluationContext) {
        if (tax.sd_tipo_pro_reg) {
            return odooboDynamicAmount(tax, rawBase, evaluationContext);
        }
        return super.eval_tax_amount_fixed_amount(tax, batch, rawBase, evaluationContext);
    },
});
