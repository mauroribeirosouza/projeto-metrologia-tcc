from odoo import models, fields


class LocalEnsaio(models.Model):
    _name = 'metrology.local_ensaios'
    _description = 'Local de Ensaio'

    name = fields.Char(string='Nome', required=True)
    endereco = fields.Char(string='Endereço')
    observacoes = fields.Text(string='Observações')


class ParteInteressada(models.Model):
    _name = 'metrology.parte_interessada'
    _description = 'Parte Interessada / Executor'

    name = fields.Char(string='Nome', required=True)
    tipo = fields.Selection([
        ('cliente', 'Cliente'),
        ('laboratorio', 'Laboratório'),
        ('fornecedor', 'Fornecedor'),
    ], string='Tipo')
    contato = fields.Char(string='Contato')
    observacoes = fields.Text(string='Observações')


class NaoConformidade(models.Model):
    _name = 'metrology.nao_conformidade'
    _description = 'Registro de Não Conformidade'

    name = fields.Char(string='Título', required=True)
    equipamento_id = fields.Many2one('metrology.equipamento', string='Equipamento')
    data = fields.Date(string='Data')
    descricao = fields.Text(string='Descrição')
    ativo = fields.Boolean(string='Ativo', default=True)
