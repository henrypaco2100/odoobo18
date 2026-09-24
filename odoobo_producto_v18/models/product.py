# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


# ESI adaptación Odoo 18:
# Se conservan las claves de configuración de los cinco campos originales
# y se amplía el módulo a diez campos adicionales configurables.
LABEL_KEYS = {
    "esi_extra_field_1": ("odoobo_producto.field_1_label", "Campo adicional 1"),
    "esi_extra_field_2": ("odoobo_producto.field_2_label", "Campo adicional 2"),
    "esi_extra_field_3": ("odoobo_producto.field_3_label", "Campo adicional 3"),
    "esi_extra_field_4": ("odoobo_producto.field_4_label", "Campo adicional 4"),
    "esi_extra_field_5": ("odoobo_producto.field_5_label", "Campo adicional 5"),
    "esi_extra_field_6": ("odoobo_producto.field_6_label", "Campo adicional 6"),
    "esi_extra_field_7": ("odoobo_producto.field_7_label", "Campo adicional 7"),
    "esi_extra_field_8": ("odoobo_producto.field_8_label", "Campo adicional 8"),
    "esi_extra_field_9": ("odoobo_producto.field_9_label", "Campo adicional 9"),
    "esi_extra_field_10": ("odoobo_producto.field_10_label", "Campo adicional 10"),
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
    esi_extra_field_6 = fields.Char(string="Campo adicional 6")
    esi_extra_field_7 = fields.Char(string="Campo adicional 7")
    esi_extra_field_8 = fields.Char(string="Campo adicional 8")
    esi_extra_field_9 = fields.Char(string="Campo adicional 9")
    esi_extra_field_10 = fields.Char(string="Campo adicional 10")

    def fields_get(self, allfields=None, attributes=None):
        result = super().fields_get(allfields=allfields, attributes=attributes)
        return _esi_apply_dynamic_labels(self.env, result)


class ProductProduct(models.Model):
    _inherit = "product.product"

    # ESI Odoo 18: product.product delega en product.template mediante _inherits,
    # por lo que los diez campos también están disponibles en las variantes.
    def fields_get(self, allfields=None, attributes=None):
        result = super().fields_get(allfields=allfields, attributes=attributes)
        return _esi_apply_dynamic_labels(self.env, result)


class ProductTemplateCategorySequence(models.Model):
    _inherit = "product.template"

    def action_obtener_siguiente_sequencia(self):
        """Genera la referencia interna usando la secuencia propia de la categoría.

        Mejora v18: usa directamente el valor devuelto por ir.sequence, evitando
        el desfase del código v13 que avanzaba la secuencia y después leía el
        siguiente número.
        """
        for product in self:
            if not product.categ_id:
                raise UserError(_("Seleccione una categoría antes de generar la referencia."))
            if product.default_code:
                raise UserError(_(
                    "El producto '%s' ya tiene la referencia interna '%s'.\n"
                    "Límpiela primero si necesita generar una nueva.",
                    product.display_name,
                    product.default_code,
                ))
            product.default_code = product.categ_id._odoobo_next_product_reference()
        return True


class ProductProductCategorySequence(models.Model):
    _inherit = "product.product"

    def action_obtener_siguiente_sequencia(self):
        for product in self:
            if not product.categ_id:
                raise UserError(_("Seleccione una categoría antes de generar la referencia."))
            if product.default_code:
                raise UserError(_(
                    "La variante '%s' ya tiene la referencia interna '%s'.\n"
                    "Límpiela primero si necesita generar una nueva.",
                    product.display_name,
                    product.default_code,
                ))
            product.default_code = product.categ_id._odoobo_next_product_reference()
        return True
