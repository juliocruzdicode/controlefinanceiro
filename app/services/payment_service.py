"""
Serviço para formas de pagamento: criação de formas padrão por usuário e utilitários.
"""
from app import db
from app.models import FormaPagamento

class PaymentService:
    DEFAULT_FORMS = [
        ('Dinheiro', 'dinheiro'),
        ('Cartão de Crédito', 'cartao_credito'),
        ('Cartão de Débito', 'cartao_debito'),
        ('Pix', 'pix'),
        ('Transferência', 'transferencia')
    ]

    @staticmethod
    def seed_default_for_user(user_id):
        """Insere as formas de pagamento mais usadas para um novo usuário.
        Não duplica formas já existentes (mesmo slug para o usuário).
        """
        created = []
        for nome, slug in PaymentService.DEFAULT_FORMS:
            slug_user = f"{slug}-u{user_id}"
            exists = FormaPagamento.query.filter_by(user_id=user_id, slug=slug_user).first()
            if not exists:
                f = FormaPagamento(nome=nome, slug=slug_user, user_id=user_id)
                db.session.add(f)
                created.append(f)
        if created:
            db.session.commit()
        return created
