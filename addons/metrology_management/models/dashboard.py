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
    taxa_conformidade = fields.Float(string='Taxa de Conformidade (%)', compute='_compute_dashboard_data', store=True)

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
            record.taxa_conformidade = (
                round((record.equipamentos_conformes / record.total_equipamentos * 100), 2)
                if record.total_equipamentos > 0 else 0.0
            )

    @api.model
    def get_dashboard_data(self):
        """Retorna dados para o dashboard em formato JSON"""
        dashboard = self.create({})  # Cria registro temporário
        return {
            'total_equipamentos': dashboard.total_equipamentos,
            'conformes': dashboard.equipamentos_conformes,
            'vencidos': dashboard.equipamentos_vencidos,
            'proximas_calibracoes': dashboard.proximas_calibracoes,
            'calibracoes_mes': dashboard.calibracoes_mes,
            'taxa_conformidade': dashboard.taxa_conformidade
        }

    def refresh_dashboard(self):
        """Atualiza os dados do dashboard"""
        self.invalidate_cache()
        return self.get_dashboard_data()