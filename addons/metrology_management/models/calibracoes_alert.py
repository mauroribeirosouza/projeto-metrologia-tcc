from odoo import models, fields, api
from datetime import date, timedelta

class CalibracoesTodo(models.Model):
    _name = 'metrology.calibracoes.alert'
    _description = 'Sistema de Alertas de Calibração'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _send_calibration_alerts(self):
        """
        Envia alertas para calibrações próximas ao vencimento e vencidas.
        Executa diariamente via agendador de tarefas (cron job).
        """
        self._send_upcoming_calibration_alerts()
        self._send_expired_calibration_alerts()
        
    def _send_upcoming_calibration_alerts(self):
        """Envia alertas para calibrações que vencem em 30 dias"""
        data_limite_30 = date.today() + timedelta(days=30)
        equipamentos_30 = self.env['metrology.equipamento'].search([
            ('proxima_calibracao', '<=', data_limite_30),
            ('proxima_calibracao', '>=', date.today()),
            ('active', '=', True)
        ])
        
        for equipamento in equipamentos_30:
            if not equipamento.activity_ids.filtered(
                lambda a: a.activity_type_id == self.env.ref('metrology_management.mail_activity_calibration_alert')
            ):
                self._create_calibration_alert_activity(equipamento)

    def _send_expired_calibration_alerts(self):
        """Envia alertas para equipamentos com calibração vencida"""
        equipamentos_vencidos = self.env['metrology.equipamento'].search([
            ('proxima_calibracao', '<', date.today()),
            ('status_metrologico', '=', 'vencido'),
            ('active', '=', True)
        ])
        
        for equipamento in equipamentos_vencidos:
            self._create_expired_calibration_message(equipamento)

    def _create_calibration_alert_activity(self, equipamento):
        """Cria atividade de alerta de calibração próxima"""
        return equipamento.activity_schedule(
            'metrology_management.mail_activity_calibration_alert',
            user_id=equipamento.responsavel_id.id or self.env.user.id,
            summary=f'Calibração próxima ao vencimento: {equipamento.tag}',
            note=f'O equipamento {equipamento.tag} - {equipamento.nome} '
                 f'vence em {equipamento.dias_para_vencimento} dias.'
        )

    def _create_expired_calibration_message(self, equipamento):
        """Cria mensagem de alerta para calibração vencida"""
        return equipamento.message_post(
            body=f'⚠️ ATENÇÃO: Equipamento {equipamento.tag} com calibração VENCIDA!',
            subject='Calibração Vencida',
            message_type='notification',
            subtype_id=self.env.ref('mail.mt_note').id,
            tracking_value_ids=[(0, 0, {
                'field': 'status_metrologico',
                'field_desc': 'Status Metrológico',
                'old_value_char': 'Válido',
                'new_value_char': 'Vencido'
            })]
        )