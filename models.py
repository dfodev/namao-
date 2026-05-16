from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bairro = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)
    bio = db.Column(db.Text, default='')
    profile_image = db.Column(db.String(200), default='default-avatar.png')
    is_provider = db.Column(db.Boolean, default=False)
    trust_seal = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_verified = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # ==========================================
    # RELACIONAMENTOS (1:1)
    # ==========================================
    service = db.relationship('Service', back_populates='owner', uselist=False, cascade='all, delete-orphan')
    availability = db.relationship('Availability', back_populates='user', uselist=False, cascade='all, delete-orphan')

    # ==========================================
    # RELACIONAMENTOS (1:N)
    # ==========================================
    # Portfólio
    portfolio_images = db.relationship('PortfolioImage', back_populates='user', lazy=True, cascade='all, delete-orphan')

    # Avaliações
    reviews_received = db.relationship('Review', foreign_keys='Review.provider_id',
                                       back_populates='provider', lazy=True, cascade='all, delete-orphan')
    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id',
                                    back_populates='reviewer', lazy=True, cascade='all, delete-orphan')

    # Favoritos
    favorites = db.relationship('Favorite', foreign_keys='Favorite.user_id',
                                back_populates='user', lazy=True, cascade='all, delete-orphan')
    favorited_by = db.relationship('Favorite', foreign_keys='Favorite.provider_id',
                                   back_populates='provider', lazy=True)

    # Visualizações de perfil
    profile_views_received = db.relationship('ProfileView', foreign_keys='ProfileView.user_id',
                                             back_populates='user', lazy=True, cascade='all, delete-orphan')
    profile_views_made = db.relationship('ProfileView', foreign_keys='ProfileView.viewer_id',
                                         back_populates='viewer', lazy=True)

    # Denúncias
    reports_made = db.relationship('Report', foreign_keys='Report.reporter_id',
                                   back_populates='reporter', lazy=True, cascade='all, delete-orphan')
    reports_received = db.relationship('Report', foreign_keys='Report.reported_id',
                                       back_populates='reported', lazy=True)

    # Histórico de contatos
    contacts_made = db.relationship('ContactHistory', foreign_keys='ContactHistory.client_id',
                                    back_populates='client', lazy=True, cascade='all, delete-orphan')
    contacts_received = db.relationship('ContactHistory', foreign_keys='ContactHistory.provider_id',
                                        back_populates='provider', lazy=True)

    # ==========================================
    # PROPERTIES & ENGINES (Regras de Negócio)
    # ==========================================
    @property
    def avg_rating(self):
        """Calcula a média ponderada apenas de avaliações aprovadas de forma dinâmica"""
        approved_reviews = [r for r in self.reviews_received if r.status == 'approved']
        if not approved_reviews:
            return 0.0
        return round(sum(r.rating for r in approved_reviews) / len(approved_reviews), 1)

    @property
    def total_reviews(self):
        """Retorna a contagem total de avaliações válidas"""
        return len([r for r in self.reviews_received if r.status == 'approved'])

    @property
    def total_views(self):
        """Retorna o número total de visualizações que o perfil recebeu"""
        return len(self.profile_views_received)

    @property
    def total_favorites(self):
        """Retorna quantas pessoas favoritaram este prestador"""
        return len(self.favorited_by)

    @property
    def total_contacts(self):
        """Retorna quantos cliques em contato ('Falar Agora') este prestador recebeu"""
        return len(self.contacts_received)


class Service(db.Model):
    __tablename__ = 'service'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    preco_medio = db.Column(db.String(50), nullable=True)
    preco_min = db.Column(db.Float, nullable=True)
    preco_max = db.Column(db.Float, nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    experiencia = db.Column(db.Integer, default=0)
    projetos_realizados = db.Column(db.Integer, default=0)
    is_approved = db.Column(db.Boolean, default=True)

    owner = db.relationship('User', back_populates='service')


class Availability(db.Model):
    __tablename__ = 'availability'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    segunda = db.Column(db.Boolean, default=True)
    terca = db.Column(db.Boolean, default=True)
    quarta = db.Column(db.Boolean, default=True)
    quinta = db.Column(db.Boolean, default=True)
    sexta = db.Column(db.Boolean, default=True)
    sabado = db.Column(db.Boolean, default=True)
    domingo = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='availability')


class PortfolioImage(db.Model):
    __tablename__ = 'portfolio_image'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_path = db.Column(db.String(300), nullable=False)
    title = db.Column(db.String(100), default='')
    description = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_primary = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='portfolio_images')


class Review(db.Model):
    __tablename__ = 'review'

    id = db.Column(db.Integer, primary_key=True)
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='approved')

    provider = db.relationship('User', foreign_keys=[provider_id], back_populates='reviews_received')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], back_populates='reviews_given')


class Favorite(db.Model):
    __tablename__ = 'favorite'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], back_populates='favorites')
    provider = db.relationship('User', foreign_keys=[provider_id], back_populates='favorited_by')

    __table_args__ = (db.UniqueConstraint('user_id', 'provider_id', name='unique_favorite'),)


class ProfileView(db.Model):
    __tablename__ = 'profile_view'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    viewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    viewer_ip = db.Column(db.String(50))
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], back_populates='profile_views_received')
    viewer = db.relationship('User', foreign_keys=[viewer_id], back_populates='profile_views_made')


class Report(db.Model):
    __tablename__ = 'report'

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reported_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')

    reporter = db.relationship('User', foreign_keys=[reporter_id], back_populates='reports_made')
    reported = db.relationship('User', foreign_keys=[reported_id], back_populates='reports_received')


class ContactHistory(db.Model):
    __tablename__ = 'contact_history'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    provider_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    contacted_at = db.Column(db.DateTime, default=datetime.utcnow)

    client = db.relationship('User', foreign_keys=[client_id], back_populates='contacts_made')
    provider = db.relationship('User', foreign_keys=[provider_id], back_populates='contacts_received')