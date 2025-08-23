#!/usr/bin/env python3
"""
Script de teste para verificar as funcionalidades de transações recorrentes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, TransacaoRecorrente, Transacao, Categoria, TipoRecorrencia, StatusRecorrencia
from datetime import datetime

def testar_funcionalidades():
    """Testa as principais funcionalidades das transações recorrentes"""
    with app.app_context():
        print("🧪 Testando funcionalidades das transações recorrentes...")
        
        # 1. Verificar transações recorrentes existentes
        recorrentes = TransacaoRecorrente.query.all()
        print(f"✅ {len(recorrentes)} transações recorrentes encontradas")
        
        for recorrente in recorrentes:
            print(f"  - {recorrente.descricao}: {recorrente.tipo_recorrencia.value} "
                  f"({recorrente.status.value}) - {len(recorrente.transacoes)} transações geradas")
        
        # 2. Verificar total de transações
        transacoes = Transacao.query.all()
        transacoes_recorrentes = [t for t in transacoes if t.is_recorrente]
        transacoes_unicas = [t for t in transacoes if not t.is_recorrente]
        
        print(f"✅ {len(transacoes)} transações no total:")
        print(f"   - {len(transacoes_recorrentes)} de recorrências")
        print(f"   - {len(transacoes_unicas)} únicas")
        
        # 3. Testar geração de próxima transação
        print("\n🔄 Testando geração de próxima transação...")
        recorrente_ativa = TransacaoRecorrente.query.filter_by(status=StatusRecorrencia.ATIVA).first()
        
        if recorrente_ativa:
            transacoes_antes = len(recorrente_ativa.transacoes)
            proxima_data = recorrente_ativa.calcular_proxima_data()
            print(f"   - Recorrência: {recorrente_ativa.descricao}")
            print(f"   - Próxima data calculada: {proxima_data.strftime('%d/%m/%Y') if proxima_data else 'N/A'}")
            print(f"   - Transações já geradas: {transacoes_antes}")
            print(f"   - Status: {recorrente_ativa.status.value}")
            
            if recorrente_ativa.is_parcelada:
                print(f"   - Parcelas: {recorrente_ativa.parcelas_geradas}/{recorrente_ativa.total_parcelas}")
                print(f"   - Restantes: {recorrente_ativa.parcelas_restantes}")
        
        # 4. Verificar categorias usadas
        print("\n📊 Categorias usadas nas recorrências:")
        categorias_recorrentes = db.session.query(Categoria).join(TransacaoRecorrente).all()
        for categoria in categorias_recorrentes:
            count = len([r for r in recorrentes if r.categoria_id == categoria.id])
            print(f"   - {categoria.nome}: {count} recorrência(s)")
        
        # 5. Estatísticas
        print("\n📈 Estatísticas:")
        recorrentes_por_tipo = {}
        for recorrente in recorrentes:
            tipo = recorrente.tipo_recorrencia.value
            if tipo not in recorrentes_por_tipo:
                recorrentes_por_tipo[tipo] = 0
            recorrentes_por_tipo[tipo] += 1
        
        for tipo, count in recorrentes_por_tipo.items():
            print(f"   - {tipo.title()}: {count}")
        
        print("\n✅ Teste concluído com sucesso!")
        
        # 6. URLs disponíveis
        print("\n🌐 URLs disponíveis:")
        print("   - Dashboard: http://localhost:5001/")
        print("   - Transações Recorrentes: http://localhost:5001/transacoes-recorrentes")
        print("   - Nova Recorrente: http://localhost:5001/nova-transacao-recorrente")
        print("   - API Recorrentes: http://localhost:5001/api/transacoes-recorrentes")
        print("   - Gerar Pendentes: http://localhost:5001/api/gerar-todas-transacoes-pendentes")
        
        return True

if __name__ == '__main__':
    testar_funcionalidades()
