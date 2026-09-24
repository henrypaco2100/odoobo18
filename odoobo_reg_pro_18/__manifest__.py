# -*- coding: utf-8 -*-
{
    "name": "Odoobo PRO / REG / COE + Editorial",
    "version": "18.0.5.0.0",
    "summary": "PRO/REG/COE compartidos, datos editoriales y kardex por autor",
    "description": """
Odoobo para Odoo 18, extraído del antiguo sd_plural_v13 y limitado a las
funciones editoriales necesarias:

- Autor y cuentas PRO / REG.
- Cuentas COE PRO / COE REG y porcentaje de identificación COE.
- Un solo impuesto compartido PRO, REG, COE PRO y COE REG por compañía; importe y cuentas dinámicos según el producto/autor.
- Compatibilidad con Ventas, Facturación y Punto de Venta sin modificar core.
- Datos editoriales del producto.
- Código interno visible/buscable y agregado al nombre mostrado del producto.
- Reporte histórico stock_report_by_author / Informe por Venta de Publicaciones por Autor en Excel.
- Importe fijo PRO/REG visible también debajo del costo en Información general del producto.

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
        "wizard/stock_report_by_author.xml",
        "data/migrate_shared_taxes.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "odoobo_reg_pro_18/static/src/js/odoobo_tax_helpers.js",
        ],
        "point_of_sale._assets_pos": [
            "odoobo_reg_pro_18/static/src/js/odoobo_tax_helpers.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
