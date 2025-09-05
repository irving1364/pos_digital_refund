{
    'name': 'POS Vuelto Digital',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Gestión de vueltos digitales para Odoo POS con pago movil, en el backend',
    'description': """
        Módulo para registrar vueltos digitales mediante API externa
        en el punto de venta de Odoo 17 Enterprise.
    """,
    'author': 'Tu Nombre',
    'website': 'https://tudominio.com',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'encrypted_data_merca'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/digital_refund_views.xml',
        'views/pos_order_views.xml',
        'views/pos_payment_config_views.xml',
        'views/pos_payment_method_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_digital_refund/static/src/xml/refund_choice_popup.xml',
            'pos_digital_refund/static/src/xml/digital_refund_popup.xml',
            'pos_digital_refund/static/src/js/digital_refund_popup.esm.js',  
            'pos_digital_refund/static/src/js/pos_payment_screen.esm.js',
            'pos_digital_refund/static/src/js/refund_choice_popup.esm.js',
            'pos_digital_refund/static/src/css/refund_popup.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}