"""
Script principal de migração

Este script centraliza todos os scripts de migração e permite
executá-los individualmente ou em conjunto.
"""
import os
import sys
import argparse
from datetime import datetime
import importlib.util
import inspect

# Adiciona o diretório raiz ao path para importações relativas
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def importar_scripts_migracao():
    """
    Importa dinamicamente todos os scripts de migração do diretório scripts
    
    Returns:
        dict: Dicionário com nome do script e função de migração
    """
    scripts = {}
    scripts_dir = os.path.join(os.path.dirname(__file__), 'scripts')
    
    # Verificar se o diretório existe
    if not os.path.exists(scripts_dir):
        print(f"Diretório de scripts não encontrado: {scripts_dir}")
        return scripts
    
    # Listar arquivos de script
    for filename in os.listdir(scripts_dir):
        if filename.startswith('migrate_') and filename.endswith('.py'):
            script_name = filename[:-3]  # Remove a extensão .py
            script_path = os.path.join(scripts_dir, filename)
            
            # Importar o módulo dinamicamente
            spec = importlib.util.spec_from_file_location(script_name, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Encontrar a função de migração
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and name.startswith('migrar_'):
                    scripts[script_name] = obj
                    break
    
    return scripts

def criar_backup_database():
    """
    Cria um backup do banco de dados atual
    
    Returns:
        str: Caminho do arquivo de backup
    """
    from app import app
    
    # Determinar caminho do banco de dados
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        if 'instance/' in app.config['SQLALCHEMY_DATABASE_URI']:
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        else:
            db_path = os.path.join('instance', app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{db_path}.backup_{timestamp}"
        
        # Copiar arquivo original para backup
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup criado em: {backup_path}")
        
        return backup_path
    
    print("⚠️ Backup automático disponível apenas para SQLite")
    return None

def executar_migracoes(scripts_selecionados=None):
    """
    Executa scripts de migração
    
    Args:
        scripts_selecionados: Lista de nomes de scripts para executar
                             Se None, executa todos os scripts
    
    Returns:
        bool: True se todas as migrações foram bem-sucedidas
    """
    from app import app
    
    # Importar scripts disponíveis
    scripts = importar_scripts_migracao()
    
    if not scripts:
        print("❌ Nenhum script de migração encontrado!")
        return False
    
    # Filtrar scripts selecionados
    if scripts_selecionados:
        scripts_para_executar = {}
        for nome in scripts_selecionados:
            for script_nome, func in scripts.items():
                if nome in script_nome:
                    scripts_para_executar[script_nome] = func
    else:
        scripts_para_executar = scripts
    
    if not scripts_para_executar:
        print("❌ Nenhum script selecionado para execução!")
        return False
    
    # Criar backup antes de começar
    criar_backup_database()
    
    # Executar scripts
    sucessos = 0
    falhas = 0
    
    with app.app_context():
        for script_nome, func in scripts_para_executar.items():
            print(f"\n🚀 Executando {script_nome}...")
            try:
                resultado = func()
                if resultado:
                    print(f"✅ {script_nome} executado com sucesso!")
                    sucessos += 1
                else:
                    print(f"❌ {script_nome} falhou!")
                    falhas += 1
            except Exception as e:
                print(f"❌ Erro ao executar {script_nome}: {str(e)}")
                falhas += 1
    
    print(f"\n📊 Resumo da migração: {sucessos} sucesso(s), {falhas} falha(s)")
    return falhas == 0

def limpar_e_recriar_banco():
    """
    Limpa completamente o banco de dados e recria todas as tabelas
    
    Returns:
        bool: True se o banco foi recriado com sucesso
    """
    from app import app, db
    
    try:
        with app.app_context():
            print("⚠️ Apagando todas as tabelas do banco de dados...")
            db.drop_all()
            
            print("🔄 Recriando todas as tabelas...")
            db.create_all()
            
            print("✅ Banco de dados recriado com sucesso!")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao recriar o banco: {str(e)}")
        return False

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Sistema de Migração do Banco de Dados')
    
    # Opções de comando
    parser.add_argument('comando', choices=['all', 'list', 'run', 'backup', 'recreate'], 
                       help='Comando a ser executado')
    
    # Argumentos adicionais
    parser.add_argument('--scripts', nargs='+', help='Scripts específicos para executar')
    
    args = parser.parse_args()
    
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

if __name__ == "__main__":
    main()
