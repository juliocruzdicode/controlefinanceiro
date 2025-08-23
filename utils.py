from models import db, Categoria, TipoTransacao
from sqlalchemy import func

def criar_categorias_padrao(user_id, verificar_existentes=True):
    """
    Cria categorias padrão para um novo usuário.
    
    Args:
        user_id (int): ID do usuário para o qual criar as categorias
        verificar_existentes (bool): Se True, verifica se as categorias já existem antes de criar
        
    Returns:
        dict: Estatísticas de criação (adicionadas, já existentes, total)
    """
    # Contadores para estatísticas
    stats = {
        'adicionadas': 0,
        'ja_existentes': 0,
        'total': 0
    }
    
    # Definição das categorias padrão com hierarquia
    categorias_padrao = [
        # Categorias de DESPESA
        {
            'nome': 'Moradia',
            'descricao': 'Despesas relacionadas à moradia',
            'cor': '#e74c3c',  # Vermelho
            'subcategorias': [
                {'nome': 'Aluguel', 'descricao': 'Pagamento de aluguel', 'cor': '#e74c3c'},
                {'nome': 'Condomínio', 'descricao': 'Taxa de condomínio', 'cor': '#e74c3c'},
                {'nome': 'IPTU', 'descricao': 'Imposto Predial e Territorial Urbano', 'cor': '#e74c3c'},
                {'nome': 'Água', 'descricao': 'Conta de água', 'cor': '#e74c3c'},
                {'nome': 'Luz', 'descricao': 'Conta de energia elétrica', 'cor': '#e74c3c'},
                {'nome': 'Gás', 'descricao': 'Conta de gás', 'cor': '#e74c3c'},
                {'nome': 'Internet', 'descricao': 'Serviço de internet', 'cor': '#e74c3c'},
                {'nome': 'Manutenção', 'descricao': 'Manutenção e reparos', 'cor': '#e74c3c'}
            ]
        },
        {
            'nome': 'Alimentação',
            'descricao': 'Despesas com alimentação',
            'cor': '#f39c12',  # Laranja
            'subcategorias': [
                {'nome': 'Supermercado', 'descricao': 'Compras de supermercado', 'cor': '#f39c12'},
                {'nome': 'Restaurantes', 'descricao': 'Refeições em restaurantes', 'cor': '#f39c12'},
                {'nome': 'Delivery', 'descricao': 'Comida por entrega', 'cor': '#f39c12'},
                {'nome': 'Lanches', 'descricao': 'Lanches e fast food', 'cor': '#f39c12'}
            ]
        },
        {
            'nome': 'Transporte',
            'descricao': 'Despesas com transporte',
            'cor': '#3498db',  # Azul
            'subcategorias': [
                {'nome': 'Combustível', 'descricao': 'Gasolina, etanol, diesel', 'cor': '#3498db'},
                {'nome': 'Transporte Público', 'descricao': 'Ônibus, metrô, trem', 'cor': '#3498db'},
                {'nome': 'Aplicativos', 'descricao': 'Uber, 99, Cabify', 'cor': '#3498db'},
                {'nome': 'Manutenção', 'descricao': 'Manutenção de veículos', 'cor': '#3498db'},
                {'nome': 'IPVA', 'descricao': 'Imposto sobre veículos', 'cor': '#3498db'},
                {'nome': 'Seguro', 'descricao': 'Seguro de veículos', 'cor': '#3498db'},
                {'nome': 'Estacionamento', 'descricao': 'Taxas de estacionamento', 'cor': '#3498db'}
            ]
        },
        {
            'nome': 'Saúde',
            'descricao': 'Despesas com saúde',
            'cor': '#2ecc71',  # Verde
            'subcategorias': [
                {'nome': 'Plano de Saúde', 'descricao': 'Mensalidade do plano de saúde', 'cor': '#2ecc71'},
                {'nome': 'Medicamentos', 'descricao': 'Compra de remédios', 'cor': '#2ecc71'},
                {'nome': 'Consultas', 'descricao': 'Consultas médicas', 'cor': '#2ecc71'},
                {'nome': 'Exames', 'descricao': 'Exames médicos', 'cor': '#2ecc71'},
                {'nome': 'Dentista', 'descricao': 'Tratamentos odontológicos', 'cor': '#2ecc71'},
                {'nome': 'Academia', 'descricao': 'Mensalidade da academia', 'cor': '#2ecc71'}
            ]
        },
        {
            'nome': 'Educação',
            'descricao': 'Despesas com educação',
            'cor': '#9b59b6',  # Roxo
            'subcategorias': [
                {'nome': 'Mensalidade', 'descricao': 'Mensalidades escolares', 'cor': '#9b59b6'},
                {'nome': 'Material', 'descricao': 'Material escolar', 'cor': '#9b59b6'},
                {'nome': 'Cursos', 'descricao': 'Cursos extracurriculares', 'cor': '#9b59b6'},
                {'nome': 'Livros', 'descricao': 'Compra de livros', 'cor': '#9b59b6'}
            ]
        },
        {
            'nome': 'Lazer',
            'descricao': 'Despesas com lazer e entretenimento',
            'cor': '#1abc9c',  # Turquesa
            'subcategorias': [
                {'nome': 'Streaming', 'descricao': 'Netflix, Spotify, Disney+', 'cor': '#1abc9c'},
                {'nome': 'Cinema', 'descricao': 'Ingressos de cinema', 'cor': '#1abc9c'},
                {'nome': 'Shows', 'descricao': 'Ingressos para shows', 'cor': '#1abc9c'},
                {'nome': 'Viagens', 'descricao': 'Gastos com viagens', 'cor': '#1abc9c'},
                {'nome': 'Hobbies', 'descricao': 'Gastos com hobbies', 'cor': '#1abc9c'}
            ]
        },
        {
            'nome': 'Vestuário',
            'descricao': 'Despesas com roupas e acessórios',
            'cor': '#34495e',  # Azul escuro
            'subcategorias': [
                {'nome': 'Roupas', 'descricao': 'Compra de roupas', 'cor': '#34495e'},
                {'nome': 'Calçados', 'descricao': 'Compra de calçados', 'cor': '#34495e'},
                {'nome': 'Acessórios', 'descricao': 'Compra de acessórios', 'cor': '#34495e'}
            ]
        },
        {
            'nome': 'Pessoal',
            'descricao': 'Despesas pessoais',
            'cor': '#e67e22',  # Laranja escuro
            'subcategorias': [
                {'nome': 'Higiene', 'descricao': 'Produtos de higiene', 'cor': '#e67e22'},
                {'nome': 'Cuidados Pessoais', 'descricao': 'Cabeleireiro, manicure, etc.', 'cor': '#e67e22'},
                {'nome': 'Presentes', 'descricao': 'Presentes para outros', 'cor': '#e67e22'}
            ]
        },
        {
            'nome': 'Despesas Financeiras',
            'descricao': 'Despesas relacionadas a finanças',
            'cor': '#c0392b',  # Vermelho escuro
            'subcategorias': [
                {'nome': 'Juros', 'descricao': 'Juros de empréstimos e cartões', 'cor': '#c0392b'},
                {'nome': 'Tarifas Bancárias', 'descricao': 'Tarifas de serviços bancários', 'cor': '#c0392b'},
                {'nome': 'IOF', 'descricao': 'Imposto sobre Operações Financeiras', 'cor': '#c0392b'},
                {'nome': 'Multas', 'descricao': 'Multas e juros por atraso', 'cor': '#c0392b'}
            ]
        },
        {
            'nome': 'Outros',
            'descricao': 'Outras despesas',
            'cor': '#7f8c8d',  # Cinza
            'subcategorias': []
        },
        
        # Categorias de RECEITA
        {
            'nome': 'Salário',
            'descricao': 'Receitas de trabalho formal',
            'cor': '#27ae60',  # Verde escuro
            'subcategorias': [
                {'nome': 'Salário Base', 'descricao': 'Salário base mensal', 'cor': '#27ae60'},
                {'nome': 'Horas Extras', 'descricao': 'Pagamento de horas extras', 'cor': '#27ae60'},
                {'nome': 'Bônus', 'descricao': 'Bônus e comissões', 'cor': '#27ae60'},
                {'nome': '13º Salário', 'descricao': 'Décimo terceiro salário', 'cor': '#27ae60'},
                {'nome': 'Férias', 'descricao': 'Pagamento de férias', 'cor': '#27ae60'}
            ]
        },
        {
            'nome': 'Investimentos',
            'descricao': 'Receitas de investimentos',
            'cor': '#16a085',  # Verde turquesa
            'subcategorias': [
                {'nome': 'Dividendos', 'descricao': 'Dividendos de ações', 'cor': '#16a085'},
                {'nome': 'Juros', 'descricao': 'Juros de investimentos', 'cor': '#16a085'},
                {'nome': 'Aluguel', 'descricao': 'Renda de aluguéis', 'cor': '#16a085'},
                {'nome': 'Rendimentos', 'descricao': 'Outros rendimentos', 'cor': '#16a085'}
            ]
        },
        {
            'nome': 'Freelancer',
            'descricao': 'Receitas de trabalhos autônomos',
            'cor': '#2980b9',  # Azul médio
            'subcategorias': []
        },
        {
            'nome': 'Vendas',
            'descricao': 'Receitas de vendas',
            'cor': '#8e44ad',  # Roxo médio
            'subcategorias': []
        },
        {
            'nome': 'Outras Receitas',
            'descricao': 'Outras fontes de receita',
            'cor': '#2c3e50',  # Azul escuro
            'subcategorias': [
                {'nome': 'Presentes', 'descricao': 'Dinheiro recebido como presente', 'cor': '#2c3e50'},
                {'nome': 'Reembolsos', 'descricao': 'Reembolsos recebidos', 'cor': '#2c3e50'},
                {'nome': 'Prêmios', 'descricao': 'Prêmios, sorteios, loterias', 'cor': '#2c3e50'}
            ]
        }
    ]
    
    # Função para criar categoria e subcategorias
    def criar_categoria_com_sub(categoria_data, parent_id=None):
        nome_categoria = categoria_data['nome']
        stats['total'] += 1
        
        # Verificar se a categoria já existe
        if verificar_existentes:
            categoria_existente = Categoria.query.filter(
                func.lower(Categoria.nome) == func.lower(nome_categoria),
                Categoria.user_id == user_id,
                Categoria.parent_id == parent_id
            ).first()
            
            if categoria_existente:
                stats['ja_existentes'] += 1
                # Se a categoria já existe, usar seu ID para possíveis subcategorias
                categoria_id = categoria_existente.id
                
                # Processar subcategorias
                if 'subcategorias' in categoria_data and categoria_data['subcategorias']:
                    for sub_data in categoria_data['subcategorias']:
                        criar_subcategoria(sub_data, categoria_id)
                
                return categoria_id
        
        # Categoria não existe, criar nova
        nova_categoria = Categoria(
            nome=categoria_data['nome'],
            descricao=categoria_data['descricao'],
            cor=categoria_data['cor'],
            parent_id=parent_id,
            user_id=user_id
        )
        db.session.add(nova_categoria)
        db.session.flush()  # Para obter o ID da categoria criada
        stats['adicionadas'] += 1
        
        # Criar subcategorias se existirem
        if 'subcategorias' in categoria_data and categoria_data['subcategorias']:
            for sub_data in categoria_data['subcategorias']:
                criar_subcategoria(sub_data, nova_categoria.id)
        
        return nova_categoria.id
    
    # Função para criar subcategorias
    def criar_subcategoria(sub_data, parent_id):
        stats['total'] += 1
        
        # Verificar se a subcategoria já existe
        if verificar_existentes:
            sub_existente = Categoria.query.filter(
                func.lower(Categoria.nome) == func.lower(sub_data['nome']),
                Categoria.user_id == user_id,
                Categoria.parent_id == parent_id
            ).first()
            
            if sub_existente:
                stats['ja_existentes'] += 1
                return
        
        # Subcategoria não existe, criar nova
        sub = Categoria(
            nome=sub_data['nome'],
            descricao=sub_data['descricao'],
            cor=sub_data['cor'],
            parent_id=parent_id,
            user_id=user_id
        )
        db.session.add(sub)
        stats['adicionadas'] += 1
    
    # Criar todas as categorias padrão
    try:
        for cat_data in categorias_padrao:
            criar_categoria_com_sub(cat_data)
        
        db.session.commit()
        return stats
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar categorias padrão: {e}")
        return False
