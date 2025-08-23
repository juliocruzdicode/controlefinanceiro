#!/usr/bin/env python3
"""
Script para executar as migrações do banco de dados
"""
import os
import sys
import argparse
from pathlib import Path

# Adicionar o diretório atual ao path
sys.path.insert(0, str(Path(__file__).parent))

# Função principal
def main():
    """Função principal do script"""
    parser = argparse.ArgumentParser(description='Sistema de Migração do Banco de Dados')
    
    # Opções de comando
    parser.add_argument('comando', choices=['all', 'list', 'run', 'backup', 'recreate', 'postgres'], 
                       help='Comando a ser executado: all (todas migrações), list (listar migrações), '
                            'run (executar migrações específicas), backup (criar backup), '
                            'recreate (recriar banco), postgres (migrar para PostgreSQL)')
    
    # Argumentos adicionais
    parser.add_argument('--scripts', nargs='+', help='Scripts específicos para executar')
    
    args = parser.parse_args()
    
    # Importar módulo de migração
    from app.migrations.migrate import (
        importar_scripts_migracao, 
        executar_migracoes, 
        criar_backup_database, 
        limpar_e_recriar_banco
    )
    
    # Executar o comando especificado
    if args.comando == 'list':
        # Listar scripts disponíveis
        scripts = importar_scripts_migracao()
        print("\n📋 Scripts de migração disponíveis:")
        for i, nome in enumerate(scripts.keys(), 1):
            print(f"  {i}. {nome}")
        print()
        
    elif args.comando == 'run':
        # Executar scripts específicos
        if not args.scripts:
            print("❌ Por favor, especifique os scripts a serem executados com --scripts")
            return
        
        executar_migracoes(args.scripts)
        
    elif args.comando == 'all':
        # Executar todos os scripts
        executar_migracoes()
        
    elif args.comando == 'backup':
        # Criar backup
        backup_path = criar_backup_database()
        if backup_path:
            print(f"✅ Backup criado com sucesso: {backup_path}")
        
    elif args.comando == 'recreate':
        # Recriar banco
        limpar_e_recriar_banco()
        
    elif args.comando == 'postgres':
        # Migrar para PostgreSQL
        from app.migrations.scripts.migrate_postgres import migrar_para_postgres
        migrar_para_postgres()

if __name__ == "__main__":
    main()
