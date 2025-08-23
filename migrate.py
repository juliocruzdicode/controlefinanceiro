#!/usr/bin/env python3
"""
Script para migrar/recriar o banco de dados com a nova estrutura hierárquica
"""
import os
import sys
from pathlib import Path

# Adicionar o diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db
from models import Categoria

def migrar_banco():
    """Migra o banco de dados para a nova estrutura"""
    with app.app_context():
        print("🔄 Iniciando migração do banco de dados...")
        
        # Remover banco antigo se existir
        db_path = Path("instance/controle_financeiro.db")
        if db_path.exists():
            print("📦 Removendo banco de dados antigo...")
            os.remove(db_path)
        
        # Criar nova estrutura
        print("🏗️  Criando nova estrutura...")
        db.create_all()
        
        # Criar categorias hierárquicas
        print("📁 Criando categorias hierárquicas...")
        
        # Categorias raiz
        alimentacao = Categoria(nome='Alimentação', descricao='Gastos com comida', cor='#ff6384')
        transporte = Categoria(nome='Transporte', descricao='Gastos com transporte', cor='#36a2eb')
        moradia = Categoria(nome='Moradia', descricao='Aluguel, conta de luz, etc.', cor='#ffce56')
        saude = Categoria(nome='Saúde', descricao='Plano de saúde, medicamentos', cor='#4bc0c0')
        educacao = Categoria(nome='Educação', descricao='Cursos, livros, etc.', cor='#9966ff')
        lazer = Categoria(nome='Lazer', descricao='Entretenimento e diversão', cor='#ff9f40')
        trabalho = Categoria(nome='Trabalho', descricao='Receitas do trabalho', cor='#2ecc71')
        
        # Adicionar categorias raiz
        categorias_raiz = [alimentacao, transporte, moradia, saude, educacao, lazer, trabalho]
        for categoria in categorias_raiz:
            db.session.add(categoria)
        
        db.session.commit()  # Commit para gerar IDs
        print(f"✅ {len(categorias_raiz)} categorias raiz criadas")
        
        # Subcategorias de Alimentação
        subcategorias_alimentacao = [
            Categoria(nome='Restaurantes', descricao='Refeições em restaurantes', cor='#ff6384', parent_id=alimentacao.id),
            Categoria(nome='Supermercado', descricao='Compras no supermercado', cor='#ff4757', parent_id=alimentacao.id),
            Categoria(nome='Delivery', descricao='Comida por delivery', cor='#ff3838', parent_id=alimentacao.id),
        ]
        
        # Subcategorias de Transporte
        subcategorias_transporte = [
            Categoria(nome='Combustível', descricao='Gasolina, álcool, diesel', cor='#36a2eb', parent_id=transporte.id),
            Categoria(nome='Transporte Público', descricao='Ônibus, metro, trem', cor='#2f80ed', parent_id=transporte.id),
            Categoria(nome='Uber/Taxi', descricao='Corridas de aplicativo', cor='#1e40af', parent_id=transporte.id),
        ]
        
        # Subcategorias de Moradia
        subcategorias_moradia = [
            Categoria(nome='Aluguel', descricao='Pagamento do aluguel', cor='#ffce56', parent_id=moradia.id),
            Categoria(nome='Contas', descricao='Luz, água, internet, etc.', cor='#ffd93d', parent_id=moradia.id),
            Categoria(nome='Manutenção', descricao='Reparos e melhorias', cor='#ffb347', parent_id=moradia.id),
        ]
        
        # Subcategorias de Trabalho
        subcategorias_trabalho = [
            Categoria(nome='Salário', descricao='Salário principal', cor='#2ecc71', parent_id=trabalho.id),
            Categoria(nome='Freelance', descricao='Trabalhos extras', cor='#27ae60', parent_id=trabalho.id),
            Categoria(nome='Investimentos', descricao='Rendimentos de investimentos', cor='#16a085', parent_id=trabalho.id),
        ]
        
        # Adicionar todas as subcategorias
        todas_subcategorias = (subcategorias_alimentacao + subcategorias_transporte + 
                             subcategorias_moradia + subcategorias_trabalho)
        
        for subcategoria in todas_subcategorias:
            db.session.add(subcategoria)
        
        db.session.commit()
        print(f"✅ {len(todas_subcategorias)} subcategorias de segundo nível criadas")
        
        # Exemplo de subcategorias de terceiro nível
        # Subcategorias de Restaurantes
        restaurante = Categoria.query.filter_by(nome='Restaurantes').first()
        if restaurante:
            subcategorias_restaurantes = [
                Categoria(nome='Fast Food', descricao='McDonald\'s, KFC, etc.', cor='#ff6b6b', parent_id=restaurante.id),
                Categoria(nome='Comida Japonesa', descricao='Sushi, yakisoba, etc.', cor='#ee5a24', parent_id=restaurante.id),
                Categoria(nome='Pizzaria', descricao='Pizza e massas', cor='#ff9ff3', parent_id=restaurante.id),
            ]
            
            for subcategoria in subcategorias_restaurantes:
                db.session.add(subcategoria)
            
            db.session.commit()
            print(f"✅ {len(subcategorias_restaurantes)} subcategorias de terceiro nível criadas")
        
        # Mostrar estrutura criada
        print("\n🌳 Estrutura de categorias criada:")
        mostrar_arvore()
        
        print("\n🎉 Migração concluída com sucesso!")
        print("📊 Você pode agora executar: python run.py")

def mostrar_arvore():
    """Mostra a estrutura de categorias de forma hierárquica"""
    def imprimir_categoria(categoria, nivel=0):
        indentacao = "  " * nivel
        print(f"{indentacao}├─ {categoria.nome} ({categoria.cor})")
        for sub in categoria.subcategorias:
            imprimir_categoria(sub, nivel + 1)
    
    categorias_raiz = Categoria.get_categorias_raiz()
    for categoria in categorias_raiz:
        imprimir_categoria(categoria)

if __name__ == '__main__':
    migrar_banco()
