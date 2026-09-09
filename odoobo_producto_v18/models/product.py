# -*- coding: utf-8 -*-
from odoo import fields, models


# ESI adaptación Odoo 18:
# Se conservan las claves de configuración de Odoo 13 para facilitar migraciones y mantener los labels.
LABEL_KEYS = {
    "esi_extra_field_1": ("odoobo_producto.field_1_label", "Campo adicional 1"),
    "esi_extra_field_2": ("odoobo_producto.field_2_label", "Campo adicional 2"),
    "esi_extra_field_3": ("odoobo_producto.field_3_label", "Campo adicional 3"),
    "esi_extra_field_4": ("odoobo_producto.field_4_label", "Campo adicional 4"),
    "esi_extra_field_5": ("odoobo_producto.field_5_label", "Campo adicional 5"),
}


def _esi_apply_dynamic_labels(env, result):
    """ESI: cambia solo el texto mostrado; conserva los nombres técnicos."""
    parameters = env["ir.config_parameter"].sudo()
    for field_name, (key, default) in LABEL_KEYS.items():
        if field_name in result:
            result[field_name]["string"] = parameters.get_param(key, default) or default
    return result


class ProductTemplate(models.Model):
    _inherit = "product.template"

    esi_extra_field_1 = fields.Char(string="Campo adicional 1")
    esi_extra_field_2 = fields.Char(string="Campo adicional 2")
    esi_extra_field_3 = fields.Char(string="Campo adicional 3")
    esi_extra_field_4 = fields.Char(string="Campo adicional 4")
    esi_extra_field_5 = fields.Char(string="Campo adicional 5")

    def fields_get(self, allfields=None, attributes=None):
        result = super().fields_get(allfields=allfields, attributes=attributes)
        return _esi_apply_dynamic_labels(self.env, result)


class ProductProduct(models.Model):
    _inherit = "product.product"

    # ESI Odoo 18: product.product delega en product.template mediante _inherits,
    # por lo que los cinco campos también están disponibles en las variantes.
    def fields_get(self, allfields=None, attributes=None):
        result = super().fields_get(allfields=allfields, attributes=attributes)
        return _esi_apply_dynamic_labels(self.env, result)
