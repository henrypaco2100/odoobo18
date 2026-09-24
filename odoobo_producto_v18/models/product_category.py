# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductCategory(models.Model):
    _inherit = "product.category"

    # Se conservan los nombres técnicos del antiguo sd_stock_v13 para facilitar
    # una futura migración de datos y mantener la lógica conocida por el usuario.
    sd_secuencia_id = fields.Many2one(
        "ir.sequence",
        string="Secuencia Categoría",
        copy=False,
        readonly=True,
        ondelete="set null",
        help="Secuencia independiente usada para la referencia interna de los productos de esta categoría.",
    )
    sd_siguiente = fields.Integer(
        string="Siguiente Número",
        related="sd_secuencia_id.number_next_actual",
        readonly=False,
    )
    sd_tam_secuencia = fields.Integer(
        string="Tamaño Secuencia",
        related="sd_secuencia_id.padding",
        readonly=False,
    )
    sd_name_secuencia = fields.Char(
        string="Nombre Secuencia",
        related="sd_secuencia_id.name",
        readonly=False,
    )
    sd_prefijo_secuencia = fields.Char(
        string="Prefijo",
        related="sd_secuencia_id.prefix",
        readonly=False,
        help="Opcional. Ejemplo LIB- genera LIB-00001, LIB-00002, etc.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        categories = super().create(vals_list)
        # Mejora respecto a v13: cada categoría queda con su propia secuencia
        # inmediatamente después de guardarse.
        for category in categories:
            if not category.sd_secuencia_id:
                category._odoobo_create_category_sequence()
        return categories

    def _odoobo_create_category_sequence(self):
        self.ensure_one()
        if not self.id:
            raise UserError(_("Guarde primero la categoría antes de crear la secuencia."))

        sequence = self.env["ir.sequence"].sudo().create({
            "name": self.name or _("Secuencia Categoría"),
            "code": f"odoobo_producto.category.{self.id}",
            "implementation": "standard",
            "prefix": "",
            "padding": 5,
            "number_increment": 1,
            "number_next_actual": 1,
            "company_id": False,
        })
        self.sd_secuencia_id = sequence.id
        return sequence

    def action_odoobo_create_category_sequence(self):
        """Crea la secuencia en categorías antiguas que todavía no la tengan."""
        for category in self:
            if not category.sd_secuencia_id:
                category._odoobo_create_category_sequence()
        return True

    def _odoobo_next_product_reference(self):
        self.ensure_one()
        sequence = self.sd_secuencia_id or self._odoobo_create_category_sequence()
        reference = sequence.sudo().next_by_id()
        if not reference:
            raise UserError(_("No se pudo obtener la siguiente referencia para la categoría %s.", self.display_name))
        return reference
