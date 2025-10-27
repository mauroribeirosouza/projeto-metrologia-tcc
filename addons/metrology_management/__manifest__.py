{
    'name': 'Sistema de Controle Metrológico',
    'version': '1.0.0',
    'category': 'Quality/Metrology',
    'summary': 'Sistema de gestão metrológica aderente à ISO 10012',
    'description': """
        Sistema completo para controle de instrumentos de medição,
        calibrações, certificados e conformidade metrológica.
        
        Funcionalidades:
        * Gestão de instrumentos de medição
        * Controle de calibrações
        * Emissão de certificados
        * Dashboard metrológico
        * Alertas automáticos
        * Rastreabilidade completa
        
        Aderente aos requisitos da norma ABNT NBR ISO 10012:2004.
    """,
    'author': 'Mauro Sérgio Ribeiro de Souza',
    'website': 'https://github.com/mauroribeirosouza/',
    'depends': [
        'base',
        'mail',
        'web',
    ],
    'data': [
        # Security
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        
        # Data
        'data/sequence_data.xml',
        'data/cron.xml',
        'data/mail_activity.xml',
        
        # Views (only existing view files)
        'views/equipment_views.xml',
        'views/dashboard_views.xml',
        
        # Reports
        'reports/certificado_template.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'price': 0.0,
    'currency': 'EUR',
}