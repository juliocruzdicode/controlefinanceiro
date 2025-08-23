#!/usr/bin/env python3
"""
Script para apagar todas as transações do sistema
"""

from app import app, db
from models import Transacao, TransacaoRecorrente

def limpar_transacoes():
    with app.app_context():
        print('🗑️  Iniciando limpeza de transações...')
        
        # Contar transações antes da limpeza
        total_transacoes = Transacao.query.count()
        total_recorrentes = TransacaoRecorrente.query.count()
        
        print(f'📊 Transações encontradas: {total_transacoes}')
        print(f'📊 Transações recorrentes encontradas: {total_recorrentes}')
        
        if total_transacoes == 0 and total_recorrentes == 0:
            print('ℹ️  Não há transações para remover')
            return
        
        try:
            # Deletar transações recorrentes primeiro (devido às chaves estrangeiras)
            if total_recorrentes > 0:
                TransacaoRecorrente.query.delete()
                db.session.commit()
                print('✅ Transações recorrentes removidas')
            
            # Deletar todas as transações normais
            if total_transacoes > 0:
                Transacao.query.delete()
                db.session.commit()
                print('✅ Transações normais removidas')
            
            # Verificar se foi tudo apagado
            restantes = Transacao.query.count()
            restantes_rec = TransacaoRecorrente.query.count()
            
            print(f'📊 Transações restantes: {restantes}')
            print(f'📊 Recorrentes restantes: {restantes_rec}')
            
            if restantes == 0 and restantes_rec == 0:
                print('🎉 Limpeza concluída com sucesso!')
            else:
                print('⚠️  Algumas transações não foram removidas')
                
        except Exception as e:
            print(f'❌ Erro durante a limpeza: {e}')
            db.session.rollback()

if __name__ == '__main__':
    limpar_transacoes()
