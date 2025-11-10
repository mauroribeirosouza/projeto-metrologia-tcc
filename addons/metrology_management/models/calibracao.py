from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class Calibracao(models.Model):
    _name = 'metrology.calibracao'
    _description = 'Registro de Calibração'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'data_calibracao desc'

    name = fields.Char(string='Número', required=True, copy=False, readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('metrology.calibracao'))
    
    # Identificação
    equipamento_id = fields.Many2one('metrology.equipamento', string='Equipamento', 
                                      required=True, ondelete='restrict', tracking=True)
    data_calibracao = fields.Date(string='Data da Calibração', required=True, 
                                   default=fields.Date.today, tracking=True)
    data_validade = fields.Date(string='Data de Validade', compute='_compute_data_validade', 
                                 store=True, tracking=True)
    
    # Tipo de Comprovação
    tipo_comprovacao = fields.Selection([
        ('calibracao', 'Calibração'),
        ('verificacao', 'Verificação'),
        ('ajuste', 'Ajuste'),
    ], string='Tipo de Comprovação', required=True, default='calibracao', tracking=True)
    
    # Local e Executor
    local_ensaio_id = fields.Many2one('metrology.local_ensaios', string='Local do Ensaio')
    executor_id = fields.Many2one('metrology.parte_interessada', string='Executor',
                                   domain=[('tipo', '=', 'laboratorio')])
    tecnico_responsavel = fields.Char(string='Técnico Responsável')
    
    # Padrão Utilizado
    padrao_id = fields.Many2one('metrology.padrao_medicao', string='Padrão de Medição Utilizado')
    rastreabilidade = fields.Char(string='Rastreabilidade', 
                                   related='padrao_id.rastreabilidade', readonly=True)
    
    # Condições Ambientais
    temperatura = fields.Float(string='Temperatura (°C)')
    umidade = fields.Float(string='Umidade Relativa (%)')
    pressao = fields.Float(string='Pressão Atmosférica (hPa)')
    
    # Resultados
    resultado = fields.Selection([
        ('conforme', 'Conforme'),
        ('nao_conforme', 'Não Conforme'),
        ('condicional', 'Condicional'),
    ], string='Resultado da Calibração', required=True, tracking=True)
    
    incerteza_expandida = fields.Float(string='Incerteza Expandida (k=2)')
    erro_encontrado = fields.Float(string='Erro Encontrado')
    ajuste_realizado = fields.Boolean(string='Ajuste Realizado', tracking=True)
    
    # Certificado
    numero_certificado = fields.Char(string='Número do Certificado')
    certificado_file = fields.Binary(string='Arquivo do Certificado')
    certificado_filename = fields.Char(string='Nome do Arquivo')
    
    # Observações
    observacoes = fields.Text(string='Observações')
    restricoes_uso = fields.Text(string='Restrições de Uso')
    
    # Status
    state = fields.Selection([
        ('rascunho', 'Rascunho'),
        ('em_analise', 'Em Análise'),
        ('aprovado', 'Aprovado'),
        ('cancelado', 'Cancelado'),
    ], string='Status', default='rascunho', tracking=True)
    
    @api.depends('data_calibracao', 'equipamento_id.frequencia_calibracao')
    def _compute_data_validade(self):
        """Calcula a data de validade com base na data de calibração e frequência do equipamento"""
        for record in self:
            if record.data_calibracao and record.equipamento_id:
                frequencia = record.equipamento_id.frequencia_calibracao or 12
                record.data_validade = record.data_calibracao + relativedelta(months=frequencia)
            else:
                record.data_validade = False
    
    @api.constrains('data_calibracao', 'data_validade')
    def _check_dates(self):
        for record in self:
            if record.data_validade and record.data_calibracao and record.data_validade < record.data_calibracao:
                raise ValidationError('A data de validade não pode ser anterior à data de calibração.')

    @api.onchange('equipamento_id')
    def _onchange_equipamento(self):
        if self.equipamento_id:
            # Algumas instalações podem não ter o campo 'padrao_recomendado_id' no equipamento.
            # Usar getattr com valor default evita AttributeError durante onchange.
            padrao = getattr(self.equipamento_id, 'padrao_recomendado_id', False)
            # Se o campo existir e for um recordset, atribuir o primeiro valor; caso contrário False.
            self.padrao_id = padrao if padrao else False

    def action_em_analise(self):
        """Move o registro para o estado 'em_analise'"""
        self.write({'state': 'em_analise'})

    def action_aprovar(self):
        """Aprova o registro de calibração e atualiza o status do equipamento"""
        self.ensure_one()
        if not self.numero_certificado:
            raise ValidationError('É necessário informar o número do certificado para aprovar a calibração.')
        self.write({'state': 'aprovado'})
        self.equipamento_id._compute_status_metrologico()

    def action_cancelar(self):
        """Cancela o registro de calibração"""
        self.ensure_one()
        self.write({'state': 'cancelado'})
        self.equipamento_id._compute_status_metrologico()

    def action_reset(self):
        """Volta o registro para o estado rascunho"""
        self.write({'state': 'rascunho'})

    def unlink(self):
        """Impede a exclusão de registros aprovados"""
        for record in self:
            if record.state == 'aprovado':
                raise ValidationError('Não é possível excluir registros de calibração aprovados.')
        return super(Calibracao, self).unlink()