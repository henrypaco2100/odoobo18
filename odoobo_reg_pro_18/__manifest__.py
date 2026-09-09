# -*- coding: utf-8 -*-
{
    "name": "Odoobo PRO / REG / COE + Editorial",
    "version": "18.0.2.0.0",
    "summary": "PRO/REG/COE automáticos, datos editoriales, código interno y kardex por autor",
    "description": """
Odoobo para Odoo 18, extraído del antiguo sd_plural_v13 y limitado a las
funciones editoriales necesarias:

- Autor y cuentas PRO / REG.
- Cuentas COE PRO / COE REG y porcentaje de identificación COE.
- Impuestos automáticos PRO/REG y COE PRO/REG por producto.
- Compatibilidad con Ventas, Facturación y Punto de Venta sin modificar core.
- Datos editoriales del producto.
- Código interno visible/buscable y agregado al nombre mostrado del producto.
- Kardex / Informe por Venta de Publicaciones por Autor en Excel.

No incluye MRP, personalizaciones de picking, multi-store ni otras funciones
del antiguo sd_plural_v13.
""",
    "author": "ESI - Especialistas en Sistemas Integrados",
    "category": "Accounting/Accounting",
    "license": "LGPL-3",
    "depends": [
        "account",
        "sale_management",
        "point_of_sale",
        "stock",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/res_partner_views.xml",
        "views/product_template_views.xml",
        "views/account_tax_views.xml",
        "wizard/report_by_author_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
