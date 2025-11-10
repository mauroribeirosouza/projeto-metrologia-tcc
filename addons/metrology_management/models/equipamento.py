from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Equipamento(models.Model):
    _name = 'metrology.equipamento'
    _description = 'Instrumento de Medição'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'codigo'
    _rec_name = 'nome'

    def name_get(self):
        """Display as 'TAG - Descrição'. Fallbacks to available pieces."""
        result = []
        for rec in self:
            parts = []
            if rec.tag:
                parts.append(rec.tag)
            if rec.nome:
                parts.append(rec.nome)
            display = ' - '.join(parts) if parts else (rec.codigo or str(rec.id))
            result.append((rec.id, display))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Search by tag OR description (nome)
            domain = args + ['|', ('tag', operator, name), ('nome', operator, name)]
            recs = self.search(domain, limit=limit)
        else:
            recs = self.search(args, limit=limit)
        return recs.name_get()

    def action_view_calibracoes(self):
        """Ação para exibir as calibrações do equipamento em uma nova view"""
        self.ensure_one()
        action = {
            'name': 'Calibrações do Equipamento',
            'type': 'ir.actions.act_window',
            'res_model': 'metrology.calibracao',
            'view_mode': 'tree,form',
            'domain': [('equipamento_id', '=', self.id)],
            'context': {'default_equipamento_id': self.id},
        }
        return action

    def action_print_history(self):
        """Gera o relatório PDF com todo o histórico do equipamento."""
        self.ensure_one()
        return self.env.ref('metrology_management.action_report_equipment_history').report_action(self)

    # Campos de Identificação
    codigo = fields.Char(
        string='Código',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('metrology.equipamento')
    )
    tag = fields.Char(string='TAG/Etiqueta', required=True, tracking=True)
    nome = fields.Char(string='Descrição', required=True, tracking=True)
    tipo = fields.Selection([
        ('dimensional', 'Dimensional'),
        ('eletrico', 'Elétrico'),
        ('pressao', 'Pressão'),
        ('temperatura', 'Temperatura'),
        ('vazao', 'Vazão'),
        ('massa', 'Massa'),
        ('outro', 'Outro'),
    ], string='Tipo', required=True, tracking=True)
    
    # Dados do Fabricante
    fabricante = fields.Char(string='Fabricante', tracking=True)
    modelo = fields.Char(string='Modelo', tracking=True)
    numero_serie = fields.Char(string='Número de Série', tracking=True)
    
    # Especificações Técnicas
    faixa_medicao = fields.Char(string='Faixa de Medição', tracking=True)
    resolucao = fields.Char(string='Resolução', tracking=True)
    incerteza_maxima = fields.Float(string='Incerteza Máxima Permitida', tracking=True)
    erro_maximo_admissivel = fields.Float(string='Erro Máximo Admissível (EMA)', tracking=True)
    
    # Localização e Responsável
    localizacao = fields.Char(string='Localização Física', tracking=True)
    centro_custo = fields.Char(string='Centro de Custo')
    responsavel_id = fields.Many2one('res.users', string='Responsável Técnico', tracking=True)
    
    # Status Metrológico
    status_metrologico = fields.Selection([
        ('conforme', 'Conforme'),
        ('nao_conforme', 'Não Conforme'),
        ('vencido', 'Calibração Vencida'),
        ('em_calibracao', 'Em Calibração'),
        ('fora_uso', 'Fora de Uso'),
    ], string='Status Metrológico', default='conforme', compute='_compute_status_metrologico', 
       store=True, tracking=True)
    
    # Calibração
    frequencia_calibracao = fields.Integer(string='Frequência de Calibração (meses)', default=12)
    ultima_calibracao = fields.Date(string='Data da Última Calibração', compute='_compute_datas_calibracao', store=True)
    proxima_calibracao = fields.Date(string='Data da Próxima Calibração', compute='_compute_datas_calibracao', store=True)
    dias_para_vencimento = fields.Integer(string='Dias para Vencimento', compute='_compute_dias_vencimento', store=True)
    
    # Relacionamentos
    calibracao_ids = fields.One2many('metrology.calibracao', 'equipamento_id', string='Histórico de Calibrações')
    nao_conformidade_ids = fields.One2many('metrology.nao_conformidade', 'equipamento_id', string='Não Conformidades')
    
    # Campos de Controle
    active = fields.Boolean(default=True, string='Ativo')
    observacoes = fields.Text(string='Observações')
    
    @api.depends('calibracao_ids', 'calibracao_ids.data_calibracao', 'calibracao_ids.state')
    def _compute_datas_calibracao(self):
        """Calcula as datas de última e próxima calibração"""
        for equipamento in self:
            calibracoes = equipamento.calibracao_ids.filtered(
                lambda c: c.state == 'aprovado'
            ).sorted('data_calibracao', reverse=True)
            
            if calibracoes:
                equipamento.ultima_calibracao = calibracoes[0].data_calibracao
                from dateutil.relativedelta import relativedelta
                equipamento.proxima_calibracao = calibracoes[0].data_calibracao + relativedelta(
                    months=equipamento.frequencia_calibracao
                )
            else:
                equipamento.ultima_calibracao = False
                equipamento.proxima_calibracao = False
    
    @api.depends('proxima_calibracao', 'calibracao_ids.resultado', 'calibracao_ids.state')
    def _compute_status_metrologico(self):
        """Calcula o status metrológico com base nas calibrações"""
        from datetime import date
        for equipamento in self:
            if not equipamento.proxima_calibracao:
                equipamento.status_metrologico = 'fora_uso'
            elif equipamento.proxima_calibracao < date.today():
                equipamento.status_metrologico = 'vencido'
            else:
                ultima_calibracao = equipamento.calibracao_ids.filtered(
                    lambda c: c.state == 'aprovado'
                ).sorted('data_calibracao', reverse=True)[:1]
                
                if ultima_calibracao and ultima_calibracao.resultado == 'conforme':
                    equipamento.status_metrologico = 'conforme'
                elif ultima_calibracao and ultima_calibracao.resultado == 'nao_conforme':
                    equipamento.status_metrologico = 'nao_conforme'
                else:
                    equipamento.status_metrologico = 'fora_uso'
    
    @api.depends('proxima_calibracao')
    def _compute_dias_vencimento(self):
        """Calcula dias restantes até o vencimento da calibração"""
        from datetime import date
        for equipamento in self:
            if equipamento.proxima_calibracao:
                delta = equipamento.proxima_calibracao - date.today()
                equipamento.dias_para_vencimento = delta.days
            else:
                equipamento.dias_para_vencimento = 0
    
    @api.constrains('tag')
    def _check_tag_unique(self):
        """Valida unicidade do TAG"""
        for equipamento in self:
            if self.search_count([('tag', '=', equipamento.tag), ('id', '!=', equipamento.id)]) > 0:
                raise ValidationError('Já existe um equipamento cadastrado com este TAG!')
