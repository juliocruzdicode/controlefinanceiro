#!/usr/bin/env python3
"""
Script de migração para adicionar transações recorrentes
Versão: 2.0 - Transações Recorrentes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, TransacaoRecorrente, TipoTransacao, TipoRecorrencia, StatusRecorrencia
from datetime import datetime, timedelta

def executar_migracao():
    """Executa a migração para adicionar transações recorrentes"""
    with app.app_context():
        try:
            print("🔧 Iniciando migração para transações recorrentes...")
            
            # Criar/atualizar tabelas
            db.create_all()
            print("✅ Tabelas criadas/atualizadas com sucesso!")
            
            # Adicionar exemplos de transações recorrentes se não existirem
            if not TransacaoRecorrente.query.first():
                print("📝 Criando exemplos de transações recorrentes...")
                
                # Importar Categoria para pegar categorias existentes
                from models import Categoria
                
                # Buscar categorias para os exemplos
                salario_cat = Categoria.query.filter_by(nome='Salário').first()
                aluguel_cat = Categoria.query.filter_by(nome='Aluguel').first()
                supermercado_cat = Categoria.query.filter_by(nome='Supermercado').first()
                
                if salario_cat:
                    # Salário mensal
                    salario_recorrente = TransacaoRecorrente(
                        descricao='Salário Mensal',
                        valor=5000.00,
                        tipo=TipoTransacao.RECEITA,
                        tipo_recorrencia=TipoRecorrencia.MENSAL,
                        data_inicio=datetime(2024, 1, 5),  # Todo dia 5
                        categoria_id=salario_cat.id,
                        status=StatusRecorrencia.ATIVA
                    )
                    db.session.add(salario_recorrente)
                
                if aluguel_cat:
                    # Aluguel mensal
                    aluguel_recorrente = TransacaoRecorrente(
                        descricao='Aluguel do Apartamento',
                        valor=1200.00,
                        tipo=TipoTransacao.DESPESA,
                        tipo_recorrencia=TipoRecorrencia.MENSAL,
                        data_inicio=datetime(2024, 1, 10),  # Todo dia 10
                        categoria_id=aluguel_cat.id,
                        status=StatusRecorrencia.ATIVA
                    )
                    db.session.add(aluguel_recorrente)
                
                if supermercado_cat:
                    # Compras semanais do supermercado
                    supermercado_recorrente = TransacaoRecorrente(
                        descricao='Compras do Supermercado',
                        valor=200.00,
                        tipo=TipoTransacao.DESPESA,
                        tipo_recorrencia=TipoRecorrencia.SEMANAL,
                        data_inicio=datetime(2024, 1, 6),  # Todo sábado
                        categoria_id=supermercado_cat.id,
                        status=StatusRecorrencia.ATIVA
                    )
                    db.session.add(supermercado_recorrente)
                
                # Exemplo de transação parcelada
                if supermercado_cat:  # Usando qualquer categoria disponível
                    notebook_parcelado = TransacaoRecorrente(
                        descricao='Notebook Dell - Parcelado',
                        valor=250.00,
                        tipo=TipoTransacao.DESPESA,
                        tipo_recorrencia=TipoRecorrencia.MENSAL,
                        data_inicio=datetime(2024, 8, 1),
                        categoria_id=supermercado_cat.id,  # Idealmente seria uma categoria "Eletrônicos"
                        total_parcelas=12,
                        status=StatusRecorrencia.ATIVA
                    )
                    db.session.add(notebook_parcelado)
                
                db.session.commit()
                
                # Contar transações recorrentes criadas
                total_recorrentes = TransacaoRecorrente.query.count()
                print(f"✅ {total_recorrentes} transações recorrentes de exemplo criadas!")
                
                # Gerar transações pendentes para os exemplos
                print("🔄 Gerando transações pendentes para os exemplos...")
                todas_recorrentes = TransacaoRecorrente.query.all()
                total_transacoes_geradas = 0
                
                for recorrente in todas_recorrentes:
                    transacoes_geradas = recorrente.gerar_transacoes_pendentes()
                    total_transacoes_geradas += len(transacoes_geradas)
                    print(f"  - {recorrente.descricao}: {len(transacoes_geradas)} transação(ões) gerada(s)")
                
                print(f"✅ Total de {total_transacoes_geradas} transações geradas!")
            
            else:
                print("ℹ️  Transações recorrentes já existem no banco de dados")
            
            print("🎉 Migração concluída com sucesso!")
            
            # Mostrar resumo
            from models import Transacao
            total_transacoes = Transacao.query.count()
            total_recorrentes = TransacaoRecorrente.query.count()
            recorrentes_ativas = TransacaoRecorrente.query.filter_by(status=StatusRecorrencia.ATIVA).count()
            
            print(f"""
📊 RESUMO DO SISTEMA:
   • Total de transações: {total_transacoes}
   • Total de recorrências: {total_recorrentes}
   • Recorrências ativas: {recorrentes_ativas}
   • Recorrências pausadas/finalizadas: {total_recorrentes - recorrentes_ativas}
""")
            
        except Exception as e:
            print(f"❌ Erro durante a migração: {e}")
            db.session.rollback()
            return False
        
        return True

if __name__ == '__main__':
    sucesso = executar_migracao()
    if sucesso:
        print("✅ Migração executada com sucesso!")
    else:
        print("❌ Migração falhou!")
        sys.exit(1)
