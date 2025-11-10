from odoo import models, fields, api
from datetime import date, timedelta

class MetrologyDashboard(models.Model):
    _name = 'metrology.dashboard'
    _description = 'Dashboard Metrológico'

    # Campos computados para cache de dados
    total_equipamentos = fields.Integer(string='Total de Equipamentos', compute='_compute_dashboard_data', store=True)
    equipamentos_conformes = fields.Integer(string='Equipamentos Conformes', compute='_compute_dashboard_data', store=True)
    equipamentos_vencidos = fields.Integer(string='Equipamentos Vencidos', compute='_compute_dashboard_data', store=True)
    proximas_calibracoes = fields.Integer(string='Calibrações Próximas', compute='_compute_dashboard_data', store=True)
    calibracoes_mes = fields.Integer(string='Calibrações do Mês', compute='_compute_dashboard_data', store=True)
    taxa_conformidade = fields.Float(string='Taxa de Conformidade', compute='_compute_dashboard_data', store=True)

    @api.depends('total_equipamentos', 'equipamentos_conformes')
    def _compute_dashboard_data(self):
        """Computa os dados do dashboard"""
        for record in self:
            # Total de equipamentos
            record.total_equipamentos = self.env['metrology.equipamento'].search_count([
                ('active', '=', True)
            ])

            # Equipamentos por status
            record.equipamentos_conformes = self.env['metrology.equipamento'].search_count([
                ('status_metrologico', '=', 'conforme'),
                ('active', '=', True)
            ])

            record.equipamentos_vencidos = self.env['metrology.equipamento'].search_count([
                ('status_metrologico', '=', 'vencido'),
                ('active', '=', True)
            ])

            # Calibrações próximas (30 dias)
            data_limite = date.today() + timedelta(days=30)
            record.proximas_calibracoes = self.env['metrology.equipamento'].search_count([
                ('proxima_calibracao', '<=', data_limite),
                ('proxima_calibracao', '>=', date.today()),
                ('active', '=', True)
            ])

            # Calibrações realizadas no mês
            inicio_mes = date.today().replace(day=1)
            record.calibracoes_mes = self.env['metrology.calibracao'].search_count([
                ('data_calibracao', '>=', inicio_mes),
                ('state', '=', 'aprovado')
            ])

            # Taxa de conformidade
            # Widget percentage na view espera valor entre 0 e 1; não multiplicar por 100 aqui
            record.taxa_conformidade = (
                round((record.equipamentos_conformes / record.total_equipamentos), 4)
                if record.total_equipamentos > 0 else 0.0
            )

    @api.model
    def get_dashboard_data(self):
        """Retorna dados para o dashboard em formato JSON, calculados on-the-fly sem criar registros."""
        Equip = self.env['metrology.equipamento']
        Calib = self.env['metrology.calibracao']

        total_equipamentos = Equip.search_count([('active', '=', True)])
        equipamentos_conformes = Equip.search_count([
            ('status_metrologico', '=', 'conforme'), ('active', '=', True)
        ])
        equipamentos_vencidos = Equip.search_count([
            ('status_metrologico', '=', 'vencido'), ('active', '=', True)
        ])

        data_limite = date.today() + timedelta(days=30)
        proximas_calibracoes = Equip.search_count([
            ('proxima_calibracao', '<=', data_limite),
            ('proxima_calibracao', '>=', date.today()),
            ('active', '=', True)
        ])

        inicio_mes = date.today().replace(day=1)
        calibracoes_mes = Calib.search_count([
            ('data_calibracao', '>=', inicio_mes), ('state', '=', 'aprovado')
        ])

        # Widget percentage espera 0..1
        taxa_conformidade = round((equipamentos_conformes / total_equipamentos), 4) if total_equipamentos > 0 else 0.0

        return {
            'total_equipamentos': total_equipamentos,
            'conformes': equipamentos_conformes,
            'vencidos': equipamentos_vencidos,
            'proximas_calibracoes': proximas_calibracoes,
            'calibracoes_mes': calibracoes_mes,
            'taxa_conformidade': taxa_conformidade,
        }

    @api.model
    def refresh_dashboard(self):
        """Atualiza os dados do dashboard"""
        # Retorna os dados atualizados calculados on-the-fly
        return self.get_dashboard_data()