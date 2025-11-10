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

    @api.model
    def create(self, vals):
        """Garante que só existe um registro de dashboard"""
        existing = self.search([], limit=1)
        if existing:
            return existing
        return super().create(vals)

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
    def default_get(self, fields_list):
        """Override para forçar recálculo ao abrir o dashboard"""
        res = super().default_get(fields_list)
        
        # Procura ou cria o registro do dashboard
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({})
        else:
            # Força recálculo dos campos computados
            dashboard._compute_dashboard_data()
        
        # Retorna os valores atualizados
        if dashboard:
            for field in fields_list:
                if hasattr(dashboard, field):
                    res[field] = getattr(dashboard, field)
        
        return res

    def get_report_data(self):
        """Retorna um snapshot com os dados do dashboard e a última calibração de cada equipamento.

        Estrutura retornada:
        {
          'total_equipamentos': int,
          'equipamentos_conformes': int,
          'equipamentos_vencidos': int,
          'proximas_calibracoes': int,
          'calibracoes_mes': int,
          'taxa_conformidade': float,  # 0..1
          'equipment_rows': [
              {'equipamento': record(equip), 'calibracao': record(cal) or False}
          ]
        }
        """
        self.ensure_one()
        Equip = self.env['metrology.equipamento']
        Calib = self.env['metrology.calibracao']

        from datetime import date, timedelta

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

        taxa_conformidade = (
            round((equipamentos_conformes / total_equipamentos), 4)
            if total_equipamentos > 0 else 0.0
        )

        equipment_rows = []
        for eq in Equip.search([('active', '=', True)], order='tag asc, nome asc'):
            last = Calib.search([
                ('equipamento_id', '=', eq.id),
                ('state', '=', 'aprovado')
            ], order='data_calibracao desc', limit=1)
            equipment_rows.append({'equipamento': eq, 'calibracao': last or False})

        return {
            'total_equipamentos': total_equipamentos,
            'equipamentos_conformes': equipamentos_conformes,
            'equipamentos_vencidos': equipamentos_vencidos,
            'proximas_calibracoes': proximas_calibracoes,
            'calibracoes_mes': calibracoes_mes,
            'taxa_conformidade': taxa_conformidade,
            'equipment_rows': equipment_rows,
        }