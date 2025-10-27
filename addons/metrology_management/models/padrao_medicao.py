from odoo import models, fields


class PadraoMedicao(models.Model):
    _name = 'metrology.padrao_medicao'
    _description = 'Padrão de Medição'

    name = fields.Char(string='Nome do Padrão', required=True)
    fabricante = fields.Char(string='Fabricante')
    modelo = fields.Char(string='Modelo')
    numero_serie = fields.Char(string='Número de Série')

    # Campo referenciado por metrology.calibracao.rastreabilidade
    rastreabilidade = fields.Char(string='Rastreabilidade', help='Identificação da rastreabilidade do padrão')

    observacoes = fields.Text(string='Observações')

    active = fields.Boolean(default=True)