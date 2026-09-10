# -*- coding: utf-8 -*-
{
    "name": "Odoobo - Campos Producto Odoo 18",
    "version": "18.0.1.2.0",
    "category": "Sales/Products",
    "summary": "Diez campos adicionales de producto con etiquetas configurables",
    "description": """
ESI - Campos Adicionales de Producto para Odoo 18 Community.

- Añade diez campos Char a producto/plantilla.
- Se muestran en formularios de producto y variante.
- Se muestran como columnas opcionales en listas.
- Se pueden usar en búsquedas.
- Los nombres mostrados de los diez campos son configurables por administradores.
- Conserva los cinco campos originales y agrega los campos 6 al 10.
- Sin dependencias de módulos de terceros.
    """,
    "author": "ESI Bolivia",
    "website": "https://esibolivia.store",
    "license": "LGPL-3",
    "depends": ["product", "base_setup"],
    "data": [
        "views/product_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
