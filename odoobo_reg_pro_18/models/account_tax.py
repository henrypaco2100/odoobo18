# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    sd_tipo_pro_reg = fields.Selection(
        selection=[
            ("pro", "PRO"),
            ("reg", "REG"),
            ("coe_pro", "COE PRO"),
            ("coe_reg", "COE REG"),
        ],
        string="Tipo Odoobo PRO/REG/COE",
        copy=False,
        index=True,
    )
    # Campo legado de las versiones v18 iniciales. Se conserva para poder
    # detectar/archivar impuestos por producto al actualizar a la nueva lógica.
    sd_product_tmpl_id = fields.Many2one(
        "product.template",
        string="Producto Odoobo (legado)",
        copy=False,
        ondelete="set null",
        index=True,
    )

    # ------------------------------------------------------------------
    # Cálculo dinámico: UN impuesto PRO/REG/COE compartido por compañía,
    # pero el importe se toma del producto de la línea, igual que la idea
    # original de sd_plural_v13, sin modificar el impuesto en la base de datos.
    # ------------------------------------------------------------------
    def _eval_taxes_computation_prepare_product_fields(self):
        fields_to_load = super()._eval_taxes_computation_prepare_product_fields()
        return fields_to_load | {"sd_amount_impuesto", "sd_tax_calc_mode"}

    def _odoobo_dynamic_tax_amount(self, raw_base, evaluation_context):
        self.ensure_one()
        if not self.sd_tipo_pro_reg:
            return None

        product_values = evaluation_context.get("product") or {}
        amount = abs(product_values.get("sd_amount_impuesto") or 0.0)
        mode = int(product_values.get("sd_tax_calc_mode") or 1)
        kind_sign = 1.0 if self.sd_tipo_pro_reg in ("pro", "coe_pro") else -1.0

        # 1=fijo, 2=porcentaje, 3=división. Los impuestos compartidos se
        # mantienen técnicamente como 'fixed'; este método aplica el cálculo
        # elegido en el producto sin crear un impuesto nuevo por cada producto.
        if mode == 1:
            price_sign = -1.0 if evaluation_context.get("price_unit", 0.0) < 0.0 else 1.0
            return kind_sign * price_sign * evaluation_context.get("quantity", 0.0) * amount
        if mode in (2, 3):
            return kind_sign * raw_base * amount / 100.0
        return 0.0

    def _eval_tax_amount_fixed_amount(self, batch, raw_base, evaluation_context):
        if self.sd_tipo_pro_reg:
            return self._odoobo_dynamic_tax_amount(raw_base, evaluation_context)
        return super()._eval_tax_amount_fixed_amount(batch, raw_base, evaluation_context)

    def _odoobo_product_account(self, product):
        self.ensure_one()
        if not product or not self.sd_tipo_pro_reg:
            return self.env["account.account"]
        mapping = {
            "pro": product.sd_cuenta_pro,
            "reg": product.sd_cuenta_reg,
            "coe_pro": product.sd_cuenta_coe,
            "coe_reg": product.sd_cuenta_coe_reg,
        }
        return mapping.get(self.sd_tipo_pro_reg) or self.env["account.account"]

    @api.model
    def _add_accounting_data_to_base_line_tax_details(self, base_line, company, include_caba_tags=False):
        super()._add_accounting_data_to_base_line_tax_details(
            base_line,
            company,
            include_caba_tags=include_caba_tags,
        )
        product = base_line.get("product_id")
        if not product:
            return

        for tax_data in base_line.get("tax_details", {}).get("taxes_data", []):
            tax = tax_data.get("tax")
            if not tax or not tax.sd_tipo_pro_reg:
                continue
            account = tax._odoobo_product_account(product)
            if not account:
                continue
            for tax_rep_data in tax_data.get("tax_reps_data", []):
                tax_rep_data["account"] = account
                grouping_key = tax_rep_data.get("grouping_key")
                if isinstance(grouping_key, dict):
                    grouping_key["account_id"] = account.id

    # point_of_sale carga account.tax mediante pos.load.mixin. Se añade el
    # tipo Odoobo para que el cálculo dinámico también funcione en el POS.
    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_list = super()._load_pos_data_fields(config_id)
        if "sd_tipo_pro_reg" not in fields_list:
            fields_list.append("sd_tipo_pro_reg")
        return fields_list
