# -*- coding: utf-8 -*-
import base64
import io

import xlsxwriter

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockReportByAuthor(models.TransientModel):
    _name = "odoobo.report.by.author"
    _description = "Informe por Venta de Publicaciones por Autor"

    date_start = fields.Date(string="Fecha inicio")
    date_end = fields.Date(string="Fecha final")
    autor_id = fields.Many2many(
        "res.partner",
        string="Autor",
        domain="[('sd_es_autor', '=', True)]",
    )
    product_id = fields.Many2many(
        "product.product",
        string="Libro / Producto",
        domain="[('sd_autor_id', '!=', False)]",
    )
    excel_file = fields.Binary(string="Reporte Excel", readonly=True)
    file_name = fields.Char(string="Archivo Excel", readonly=True)

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for wizard in self:
            if wizard.date_start and wizard.date_end and wizard.date_start > wizard.date_end:
                raise UserError(_("La fecha inicial no puede ser posterior a la fecha final."))

    def _get_invoice_lines(self):
        self.ensure_one()
        domain = [
            ("move_id.state", "=", "posted"),
            ("move_id.move_type", "=", "out_invoice"),
            ("product_id", "!=", False),
            ("product_id.product_tmpl_id.sd_autor_id", "!=", False),
        ]
        if self.date_start:
            domain.append(("move_id.invoice_date", ">=", self.date_start))
        if self.date_end:
            domain.append(("move_id.invoice_date", "<=", self.date_end))
        if self.autor_id:
            domain.append(("product_id.product_tmpl_id.sd_autor_id", "in", self.autor_id.ids))
        if self.product_id:
            domain.append(("product_id", "in", self.product_id.ids))
        return self.env["account.move.line"].search(domain, order="move_id.invoice_date, id")

    def _get_report_rows(self):
        self.ensure_one()
        lines = self._get_invoice_lines()
        grouped = {}
        for line in lines:
            product = line.product_id
            template = product.product_tmpl_id
            author = template.sd_autor_id
            if not author:
                continue
            author_bucket = grouped.setdefault(author.id, {
                "author": author,
                "products": {},
            })
            bucket = author_bucket["products"].setdefault(product.id, {
                "product": product,
                "quantity": 0.0,
            })
            bucket["quantity"] += line.quantity

        # Stock actual por producto en ubicaciones internas y compañía activa.
        all_product_ids = [pid for data in grouped.values() for pid in data["products"]]
        stock_by_product = {pid: 0.0 for pid in all_product_ids}
        if all_product_ids:
            quants = self.env["stock.quant"].search([
                ("product_id", "in", all_product_ids),
                ("location_id.usage", "=", "internal"),
                ("company_id", "=", self.env.company.id),
            ])
            for quant in quants:
                stock_by_product[quant.product_id.id] = stock_by_product.get(quant.product_id.id, 0.0) + quant.quantity

        result = []
        for author_data in sorted(grouped.values(), key=lambda d: (d["author"].name or "")):
            products = []
            for item in sorted(author_data["products"].values(), key=lambda d: (d["product"].display_name or "")):
                product = item["product"]
                tmpl = product.product_tmpl_id
                qty = item["quantity"]
                agreement_price = tmpl.sd_amount_impuesto or 0.0
                products.append({
                    "product": product,
                    "quantity": qty,
                    "pvp": tmpl.list_price or 0.0,
                    "agreement_price": agreement_price,
                    "total_agreement": qty * agreement_price,
                    "stock": stock_by_product.get(product.id, 0.0),
                    "deposito_legal": tmpl.sd_deposito_legal or "",
                })
            result.append({"author": author_data["author"], "products": products})
        return result

    def action_export_xlsx(self):
        self.ensure_one()
        rows = self._get_report_rows()
        if not rows:
            raise UserError(_("No se encontraron ventas publicadas para los filtros seleccionados."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Informe por Autor")
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.freeze_panes(6, 0)

        fmt_title = workbook.add_format({"bold": True, "font_size": 15, "align": "center", "valign": "vcenter", "border": 1})
        fmt_header = workbook.add_format({"bold": True, "font_size": 11, "align": "center", "valign": "vcenter", "text_wrap": True, "border": 1, "bg_color": "#E7E9ED"})
        fmt_label = workbook.add_format({"bold": True, "font_size": 11, "border": 1})
        fmt_text = workbook.add_format({"font_size": 11, "border": 1})
        fmt_center = workbook.add_format({"font_size": 11, "border": 1, "align": "center"})
        fmt_num = workbook.add_format({"font_size": 11, "border": 1, "num_format": "0.00"})
        fmt_money = workbook.add_format({"font_size": 11, "border": 1, "num_format": "#,##0.00"})
        fmt_author = workbook.add_format({"bold": True, "font_size": 11, "border": 1, "bg_color": "#F2F2F2"})
        fmt_total = workbook.add_format({"bold": True, "font_size": 11, "border": 1, "bg_color": "#E7E9ED", "num_format": "0.00"})
        fmt_total_money = workbook.add_format({"bold": True, "font_size": 11, "border": 1, "bg_color": "#E7E9ED", "num_format": "#,##0.00"})

        widths = [7, 48, 14, 14, 18, 15, 14, 18, 18, 18]
        for col, width in enumerate(widths):
            sheet.set_column(col, col, width)

        sheet.merge_range(0, 0, 1, 9, "INFORME POR VENTA DE PUBLICACIONES", fmt_title)
        sheet.write(2, 0, "Compañía:", fmt_label)
        sheet.merge_range(2, 1, 2, 3, self.env.company.name, fmt_text)
        sheet.write(2, 4, "Fecha:", fmt_label)
        date_from = fields.Date.to_string(self.date_start) if self.date_start else "Primer registro"
        date_to = fields.Date.to_string(self.date_end) if self.date_end else "Fecha actual"
        sheet.merge_range(2, 5, 2, 9, f"{date_from} - {date_to}", fmt_text)

        authors = ", ".join(self.autor_id.mapped("name")) if self.autor_id else "Todos"
        products = ", ".join(self.product_id.mapped("display_name")) if self.product_id else "Todos"
        sheet.write(3, 0, "Autores:", fmt_label)
        sheet.merge_range(3, 1, 3, 4, authors, fmt_text)
        sheet.write(3, 5, "Libros:", fmt_label)
        sheet.merge_range(3, 6, 3, 9, products, fmt_text)

        headers = [
            "Nro", "TÍTULO", "CANTIDAD\nRECIBIDA", "CANTIDAD\nDEVUELTA", "DEPÓSITO\nLEGAL",
            "TOTAL VENTAS\nREALIZADAS", "PVP", "PRECIO ACUERDO\nCONTRATO", "TOTAL VENTAS", "SALDO EN\nCONSIG. O ALMACÉN",
        ]
        for col, value in enumerate(headers):
            sheet.write(5, col, value, fmt_header)
        sheet.set_row(5, 34)

        row = 6
        total_qty = 0.0
        total_bs = 0.0
        total_stock = 0.0
        for author_data in rows:
            sheet.merge_range(row, 0, row, 9, author_data["author"].name or "SIN AUTOR", fmt_author)
            row += 1
            number = 1
            for item in author_data["products"]:
                sheet.write_number(row, 0, number, fmt_center)
                sheet.write(row, 1, item["product"].display_name, fmt_text)
                sheet.write_number(row, 2, 0, fmt_num)  # v13 no calculaba recibidas
                sheet.write_number(row, 3, 0, fmt_num)  # v13 no calculaba devueltas
                sheet.write(row, 4, item["deposito_legal"], fmt_center)
                sheet.write_number(row, 5, item["quantity"], fmt_num)
                sheet.write_number(row, 6, item["pvp"], fmt_money)
                sheet.write_number(row, 7, item["agreement_price"], fmt_money)
                sheet.write_number(row, 8, item["total_agreement"], fmt_money)
                sheet.write_number(row, 9, item["stock"], fmt_num)
                total_qty += item["quantity"]
                total_bs += item["total_agreement"]
                total_stock += item["stock"]
                number += 1
                row += 1

        sheet.write(row, 0, "", fmt_total)
        sheet.merge_range(row, 1, row, 4, "TOTALES", fmt_total)
        sheet.write_number(row, 5, total_qty, fmt_total)
        sheet.write(row, 6, "", fmt_total)
        sheet.write(row, 7, "", fmt_total)
        sheet.write_number(row, 8, total_bs, fmt_total_money)
        sheet.write_number(row, 9, total_stock, fmt_total)

        workbook.close()
        output.seek(0)
        filename = "INFORME_POR_VENTA_DE_PUBLICACIONES.xlsx"
        self.write({
            "excel_file": base64.b64encode(output.read()),
            "file_name": filename,
        })
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/?model={self._name}&id={self.id}&field=excel_file&filename_field=file_name&download=true",
            "target": "self",
        }
