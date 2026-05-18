from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, TextAreaField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, NumberRange


# ===== FORMULÁRIO DE LOGIN =====
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])


# ===== FORMULÁRIO DE REGISTRO =====
class RegisterForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    bairro = StringField('Bairro', validators=[DataRequired()])
    telefone = StringField('WhatsApp (com DDD, apenas números)', validators=[DataRequired(), Length(min=10, max=11)])
    accept_terms = BooleanField('Aceito os termos', validators=[DataRequired()])


# ===== FORMULÁRIO PARA SE TORNAR PRESTADOR =====
class BecomeProviderForm(FlaskForm):
    bio = TextAreaField('Bio/Descrição', validators=[DataRequired(), Length(min=10, max=500)])
    categoria = SelectField('Categoria', choices=[
        ('Encanador', 'Encanador'),
        ('Eletricista', 'Eletricista'),
        ('Pedreiro', 'Pedreiro'),
        ('Pintor', 'Pintor'),
        ('Jardineiro', 'Jardineiro'),
        ('Entregador', 'Entregador'),
        ('Faxineiro', 'Faxineiro'),
        ('Outros', 'Outros')
    ], validators=[DataRequired()])
    preco_medio = StringField('Preço médio (ex: R$ 80/hora)', validators=[DataRequired()])


# ===== FORMULÁRIO DE DISPONIBILIDADE =====
class AvailabilityForm(FlaskForm):
    segunda = BooleanField('Segunda')
    terca = BooleanField('Terça')
    quarta = BooleanField('Quarta')
    quinta = BooleanField('Quinta')
    sexta = BooleanField('Sexta')
    sabado = BooleanField('Sábado')
    domingo = BooleanField('Domingo')


# ===== FORMULÁRIO DE PORTFÓLIO =====
class PortfolioForm(FlaskForm):
    images = FileField('Imagens do Portfólio',
                       validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp'],
                                               'Apenas imagens são permitidas!')],
                       render_kw={"multiple": True})
    title = StringField('Título', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Descrição', validators=[Optional(), Length(max=200)])


# ===== FORMULÁRIO DE ATUALIZAÇÃO DE PERFIL =====
class ProfileUpdateForm(FlaskForm):
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    experiencia = IntegerField('Anos de Experiência', validators=[Optional(), NumberRange(min=0, max=50)])
    projetos_realizados = IntegerField('Projetos Realizados', validators=[Optional(), NumberRange(min=0)])


# ===== FORMULÁRIO DE REGISTRO =====
class RegisterForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    cidade = StringField('Cidade', validators=[DataRequired()])  # ← NOVO
    bairro = StringField('Bairro', validators=[DataRequired()])
    telefone = StringField('WhatsApp (com DDD, apenas números)', validators=[DataRequired(), Length(min=10, max=11)])
    accept_terms = BooleanField('Aceito os termos', validators=[DataRequired()])