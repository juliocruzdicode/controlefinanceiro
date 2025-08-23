#!/usr/bin/env python3
"""
Script para forçar criação das tabelas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Categoria, Transacao, TransacaoRecorrente, Tema

def criar_todas_tabelas():
    """Força a criação de todas as tabelas"""
    with app.app_context():
        print("🔧 Criando todas as tabelas...")
        
        # Drop all para recriar
        db.drop_all()
        
        # Criar todas as tabelas
        db.create_all()
        
        print("✅ Tabelas criadas com sucesso!")
        
        # Criar tema padrão se não existir
        tema_padrao = Tema.query.filter_by(is_default=True).first()
        if not tema_padrao:
            print("🎨 Criando tema padrão...")
            tema_padrao = Tema(
                nome="Tema Padrão",
                descricao="Tema padrão do sistema",
                is_default=True,
                cor_primaria="#007bff",
                cor_secundaria="#6c757d",
                cor_sucesso="#28a745",
                cor_perigo="#dc3545",
                cor_alerta="#ffc107",
                cor_info="#17a2b8",
                cor_fundo="#ffffff",
                cor_texto="#212529",
                cor_primaria_dark="#375a7f",
                cor_secundaria_dark="#444444",
                cor_sucesso_dark="#00bc8c",
                cor_perigo_dark="#e74c3c",
                cor_alerta_dark="#f39c12",
                cor_info_dark="#3498db",
                cor_fundo_dark="#222222",
                cor_texto_dark="#ffffff"
            )
            db.session.add(tema_padrao)
            db.session.commit()
            print("✅ Tema padrão criado com sucesso!")
        
        # Verificar tabelas criadas
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()
        print(f"📋 Tabelas criadas: {', '.join(tabelas)}")
        
        return True

if __name__ == '__main__':
    criar_todas_tabelas()
