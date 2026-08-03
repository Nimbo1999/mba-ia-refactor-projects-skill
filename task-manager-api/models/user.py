from database import db
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash


def _utcnow():
    # SQLite/SQLAlchemy armazena datetimes "naive"; usamos o substituto não
    # deprecated de datetime.utcnow() removendo o tzinfo para manter os
    # valores comparáveis com o que já está persistido no banco.
    return datetime.now(timezone.utc).replace(tzinfo=None)


USER_ROLES = ['user', 'admin', 'manager']


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self):
        # Nunca inclui password/password_hash na serialização: credenciais não
        # devem trafegar em nenhuma resposta HTTP.
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at)
        }

    def set_password(self, pwd):
        self.password_hash = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password_hash, pwd)

    def is_admin(self):
        return self.role == 'admin'
