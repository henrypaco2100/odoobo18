# -*- coding: utf-8 -*-
import unicodedata

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    esi_remission_percentage = fields.Char(string="Porcentaje")

    # ESI corrección: opciones de impresión solicitadas para Odoo 18.
    esi_print_cost = fields.Boolean(string="Imprimir costo", default=True)
    esi_print_cost_total = fields.Boolean(string="Imprimir costo total", default=False)
    esi_print_amount_total = fields.Boolean(string="Imprimir importe total", default=True)

    def _esi_fix_mojibake(self, value):
        if value in (False, None):
            return ""
        text = str(value)
        markers = ("Ã", "Â", "â€", "â€™", "â€œ", "â€\x9d", "ð")
        if any(marker in text for marker in markers):
            original_score = sum(text.count(marker) for marker in markers)
            for encoding in ("cp1252", "latin1"):
                try:
                    candidate = text.encode(encoding).decode("utf-8")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    continue
                candidate_score = sum(candidate.count(marker) for marker in markers)
                if candidate_score < original_score:
                    text = candidate
                    break
        return text

    def esi_report_text(self, value, output_type=None):
        """Unicode en HTML; ASCII estable en PDF para evitar caracteres Ã...."""
        text = self._esi_fix_mojibake(value)
        if output_type == "pdf":
            return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        return text

    def esi_format_amount(self, value):
        """Importes sin símbolo de moneda."""
        try:
            amount = float(value or 0.0)
        except (TypeError, ValueError):
            amount = 0.0
        raw = f"{amount:,.2f}"
        return raw.replace(",", "X").replace(".", ",").replace("X", ".")

    def esi_format_quantity(self, value):
        try:
            qty = float(value or 0.0)
        except (TypeError, ValueError):
            qty = 0.0
        # Mantiene una salida limpia: 3 en lugar de 3,00 cuando es entero.
        if qty.is_integer():
            return str(int(qty))
        raw = f"{qty:,.2f}"
        return raw.replace(",", "X").replace(".", ",").replace("X", ".")

    def esi_date_in_words(self):
        self.ensure_one()
        date = self.date_done or self.scheduled_date
        months = (
            "", "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
            "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
        )
        return "%02d DE %s DEL %s" % (date.day, months[date.month], date.year) if date else ""

    def esi_report_moves(self):
        self.ensure_one()
        return self.move_ids_without_package.filtered(
            lambda move: self.esi_move_quantity(move)
        ).sorted(key=lambda move: move.id)

    def esi_move_quantity(self, move):
        """Odoo 18: quantity sustituye a quantity_done de versiones antiguas."""
        return move.quantity or move.product_uom_qty

    def esi_unit_cost(self, move):
        product = move.product_id.with_company(self.company_id)
        return product.standard_price

    def esi_unit_pvp(self, move):
        product = move.product_id.with_company(self.company_id)
        return product.lst_price

    def esi_line_amount_total(self, move):
        # ESI: IMPORTE TOTAL = CANTIDAD x PVP.
        return self.esi_move_quantity(move) * self.esi_unit_pvp(move)

    def esi_line_cost_total(self, move):
        # ESI: COSTO TOTAL = CANTIDAD x COSTO UNITARIO.
        return self.esi_move_quantity(move) * self.esi_unit_cost(move)

    def esi_total_quantity(self):
        return sum(self.esi_move_quantity(move) for move in self.esi_report_moves())

    def esi_total_amount(self):
        return sum(self.esi_line_amount_total(move) for move in self.esi_report_moves())

    def esi_total_cost(self):
        return sum(self.esi_line_cost_total(move) for move in self.esi_report_moves())

    def esi_percentage_label(self):
        value = (self.esi_remission_percentage or "").strip()
        return value if not value or "%" in value else value + "%"
