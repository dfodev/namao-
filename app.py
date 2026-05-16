import os
import re
import secrets
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import quote

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, session, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image

# Importação unificada dos modelos do banco de dados e formulários
from models import (
    db, User, Service, Availability, PortfolioImage,
    Review, Favorite, ProfileView, ContactHistory, Report
)
from forms import LoginForm, RegisterForm, BecomeProviderForm, AvailabilityForm

# ==============================================
# CONFIGURAÇÃO DO APP E SEGURANÇA
# ==============================================
app = Flask(__name__)

app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///namao.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_HTTPONLY'] = True

# Proteção CSRF Global
csrf = CSRFProtect()
csrf.init_app(app)

# Inicialização do Banco de Dados
db.init_app(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = "strong"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Configurações de Upload
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'tif',
    'webp', 'avif', 'heic', 'heif', 'svg', 'ico',
    'raw', 'cr2', 'nef', 'arw', 'dng'
}
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ==============================================
# FUNÇÕES AUXILIARES / UTILS
# ==============================================
def allowed_file(filename):
    """Verifica se o arquivo possui uma extensão de imagem válida"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def save_image(file, user_id, is_profile=False):
    """Salva e otimiza imagens reduzindo o overhead de armazenamento"""
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        if is_profile:
            filename = f"profile_{user_id}_{secrets.token_hex(8)}.{ext}"
        else:
            filename = f"portfolio_{user_id}_{secrets.token_hex(8)}.{ext}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            img = Image.open(file)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')

            if is_profile:
                img.thumbnail((300, 300))
            else:
                max_size = 1200
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size))

            if ext in ['gif', 'webp', 'png']:
                img.save(filepath, optimize=True)
            else:
                jpeg_path = filepath.rsplit('.', 1)[0] + '.jpg'
                img.save(jpeg_path, 'JPEG', optimize=True, quality=85)
                return f'uploads/{os.path.basename(jpeg_path)}'

            return f'uploads/{filename}'
        except Exception as e:
            print(f"Erro ao processar imagem: {e}")
            return None
    return None


def get_color_for_category(categoria):
    """Retorna a cor Hex correspondente para estilização dinâmica na UI"""
    colors = {
        'Encanador': '#4cc9f0',
        'Eletricista': '#f72585',
        'Pedreiro': '#f8961e',
        'Pintor': '#9b5de5',
        'Jardineiro': '#06d6a0',
        'Entregador': '#ffd166',
        'Faxineiro': '#118ab2'
    }
    return colors.get(categoria, '#6c757d')


app.jinja_env.globals.update(get_color_for_category=get_color_for_category)


@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=lambda: generate_csrf())


# ==============================================
# AUTENTICAÇÃO & CONTAS
# ==============================================
@app.route('/')
def index():
    bairro = request.args.get('bairro', '')
    categoria = request.args.get('categoria', '')

    query = Service.query.filter_by(is_available=True).join(User)

    if bairro:
        query = query.filter(User.bairro.ilike(f'%{bairro}%'))

    if categoria and categoria != 'Todos':
        query = query.filter(Service.categoria == categoria)

    servicos = query.order_by(User.trust_seal.desc()).all()
    categorias = ['Todos', 'Encanador', 'Eletricista', 'Pedreiro', 'Pintor', 'Jardineiro', 'Entregador', 'Faxineiro']

    return render_template('index.html', servicos=servicos, bairro=bairro, categoria=categoria, categorias=categorias)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('index'))
        flash('Email ou senha inválidos')
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            name=form.name.data,
            email=form.email.data,
            password=hashed_password,
            bairro=form.bairro.data,
            telefone=form.telefone.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Cadastro realizado! Faça login.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()

        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            flash(f'Link de redefinição: {url_for("redefinir_senha", token=token, _external=True)}')
        else:
            flash('Email não encontrado')
        return redirect(url_for('login'))

    return render_template('esqueci_senha.html')


@app.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    user = User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expiry < datetime.utcnow():
        flash('Link inválido ou expirado')
        return redirect(url_for('login'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            flash('Senhas não coincidem')
        elif len(password) < 6:
            flash('Senha deve ter no mínimo 6 caracteres')
        else:
            user.password = generate_password_hash(password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            flash('Senha redefinida com sucesso!')
            return redirect(url_for('login'))

    return render_template('redefinir_senha.html', token=token)


# ==============================================
# SISTEMA DE PRESTADORES & DASHBOARD
# ==============================================
@app.route('/become-provider', methods=['GET', 'POST'])
@login_required
def become_provider():
    if current_user.is_provider:
        return redirect(url_for('dashboard'))

    form = BecomeProviderForm()
    if form.validate_on_submit():
        current_user.bio = form.bio.data
        current_user.is_provider = True
        current_user.trust_seal = False

        service = Service(
            user_id=current_user.id,
            categoria=form.categoria.data,
            preco_medio=form.preco_medio.data,
            is_available=True
        )
        db.session.add(service)

        availability = Availability(
            user_id=current_user.id,
            segunda=True, terca=True, quarta=True, quinta=True, sexta=True, sabado=True, domingo=False
        )
        db.session.add(availability)
        db.session.commit()

        flash('Você agora é um prestador de serviços!')
        return redirect(url_for('dashboard'))

    return render_template('become_provider.html', form=form)


@app.route('/dashboard')
@app.route('/minha-conta', endpoint='minha_conta')
@login_required
def dashboard():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    my_reviews = Review.query.filter_by(reviewer_id=current_user.id).all()
    contacts = ContactHistory.query.filter_by(client_id=current_user.id).order_by(
        ContactHistory.contacted_at.desc()).all()

    if current_user.is_provider:
        service = Service.query.filter_by(user_id=current_user.id).first()
        if not service:
            return redirect(url_for('become_provider'))

        availability = Availability.query.filter_by(user_id=current_user.id).first()
        portfolio = PortfolioImage.query.filter_by(user_id=current_user.id).order_by(
            PortfolioImage.created_at.desc()).all()

        # Métricas de visitas do prestador
        total_views = ProfileView.query.filter_by(user_id=current_user.id).count()
        recent_visitors = ProfileView.query.filter_by(user_id=current_user.id) \
            .order_by(ProfileView.viewed_at.desc()) \
            .limit(5).all()

        return render_template('dashboard_unificado.html',
                               service=service, availability=availability, portfolio=portfolio,
                               favorites=favorites, my_reviews=my_reviews, contacts=contacts,
                               total_views=total_views, recent_visitors=recent_visitors)

    return render_template('dashboard_unificado.html', favorites=favorites, my_reviews=my_reviews, contacts=contacts)


@app.route('/toggle-availability')
@login_required
def toggle_availability():
    if not current_user.is_provider:
        return redirect(url_for('index'))

    service = Service.query.filter_by(user_id=current_user.id).first()
    if service:
        service.is_available = not service.is_available
        db.session.commit()
        status = "disponível" if service.is_available else "indisponível"
        flash(f'Você agora está {status} na vitrine!')

    return redirect(url_for('dashboard'))


@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    try:
        bio = request.form.get('bio', '')
        preco_medio = request.form.get('preco_medio', '')
        bairro = request.form.get('bairro', '')
        telefone = request.form.get('telefone', '')

        if telefone:
            telefone_limpo = re.sub(r'\D', '', telefone)
            if len(telefone_limpo) not in [10, 11]:
                flash('Telefone inválido.')
                return redirect(url_for('dashboard'))
            current_user.telefone = telefone_limpo

        if bio:
            current_user.bio = bio[:500]

        if bairro:
            current_user.bairro = bairro

        service = Service.query.filter_by(user_id=current_user.id).first()
        if service and preco_medio:
            service.preco_medio = preco_medio[:100]

        db.session.commit()
        flash('Perfil updated com sucesso!')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar perfil: {str(e)}')

    return redirect(url_for('dashboard'))


# ==============================================
# GERENCIAMENTO DE IMAGENS E PORTFÓLIO
# ==============================================
@app.route('/upload-profile-image', methods=['POST'])
@login_required
def upload_profile_image():
    if 'profile_image' not in request.files:
        flash('Nenhuma imagem selecionada')
        return redirect(url_for('dashboard'))

    file = request.files['profile_image']
    if file.filename == '':
        flash('Nenhuma imagem selecionada')
        return redirect(url_for('dashboard'))

    if current_user.profile_image and current_user.profile_image != 'default-avatar.png':
        old_path = os.path.join(app.config['UPLOAD_FOLDER'], current_user.profile_image.replace('uploads/', ''))
        if os.path.exists(old_path):
            os.remove(old_path)

    image_path = save_image(file, current_user.id, is_profile=True)
    if image_path:
        current_user.profile_image = image_path
        db.session.commit()
        flash('Foto de perfil updated com sucesso!')
    else:
        flash('Formato de imagem não suportado.')

    return redirect(url_for('dashboard'))


@app.route('/upload-portfolio', methods=['POST'])
@login_required
def upload_portfolio():
    if 'portfolio_images' not in request.files:
        flash('Nenhuma imagem selecionada')
        return redirect(url_for('dashboard'))

    files = request.files.getlist('portfolio_images')
    title = request.form.get('title', '')
    description = request.form.get('description', '')

    uploaded_count = 0
    for file in files:
        if file and file.filename != '':
            image_path = save_image(file, current_user.id, is_profile=False)
            if image_path:
                portfolio_image = PortfolioImage(
                    user_id=current_user.id,
                    image_path=image_path,
                    title=title[:100],
                    description=description[:200]
                )
                db.session.add(portfolio_image)
                uploaded_count += 1

    if uploaded_count > 0:
        db.session.commit()
        flash(f'{uploaded_count} imagem(ns) adicionada(s) ao portfólio!')
    else:
        flash('Nenhuma imagem foi salva.')

    return redirect(url_for('dashboard'))


@app.route('/editar-portfolio/<int:image_id>', methods=['POST'])
@login_required
def editar_portfolio(image_id):
    image = PortfolioImage.query.get_or_404(image_id)
    if image.user_id != current_user.id:
        flash('Acesso negado')
        return redirect(url_for('dashboard'))

    image.title = request.form.get('title', '')[:100]
    image.description = request.form.get('description', '')[:200]
    db.session.commit()

    flash('Informações do portfólio atualizadas!')
    return redirect(url_for('dashboard'))


@app.route('/delete-portfolio/<int:image_id>')
@login_required
def delete_portfolio(image_id):
    image = PortfolioImage.query.get_or_404(image_id)
    if image.user_id != current_user.id:
        flash('Acesso negado')
        return redirect(url_for('dashboard'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.image_path.replace('uploads/', ''))
    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(image)
    db.session.commit()

    flash('Imagem removida do portfólio')
    return redirect(url_for('dashboard'))


@app.route('/set-primary-portfolio/<int:image_id>')
@login_required
def set_primary_portfolio(image_id):
    image = PortfolioImage.query.get_or_404(image_id)
    if image.user_id != current_user.id:
        flash('Acesso negado')
        return redirect(url_for('dashboard'))

    PortfolioImage.query.filter_by(user_id=current_user.id).update({'is_primary': False})
    image.is_primary = True
    db.session.commit()

    flash('Imagem definida como destaque do perfil!')
    return redirect(url_for('dashboard'))


# ==============================================
# PERFIL PÚBLICO E INTERAÇÕES ASSÍNCRONAS (AJAX)
# ==============================================
@app.route('/perfil/<int:user_id>')
def perfil_publico(user_id):
    user = User.query.get_or_404(user_id)
    service = Service.query.filter_by(user_id=user_id).first()
    portfolio = PortfolioImage.query.filter_by(user_id=user_id).all()

    is_authenticated = current_user.is_authenticated
    viewer_id = current_user.id if is_authenticated else None
    viewer_ip = request.remote_addr

    # Impedir auto-visualização do dono da conta nas métricas
    if is_authenticated and current_user.id == user.id:
        reviews = Review.query.filter_by(provider_id=user_id, status='approved').order_by(Review.created_at.desc()).all()
        return render_template('perfil_publico.html', user=user, service=service, portfolio=portfolio,
                               reviews=reviews, is_favorite=False)

    # Mecanismo Anti-Flood (Janela de 15 minutos)
    tempo_limite = datetime.utcnow() - timedelta(minutes=15)
    query_filtro = ProfileView.query.filter(
        ProfileView.user_id == user_id,
        ProfileView.viewed_at >= tempo_limite
    )

    if is_authenticated:
        recent_view = query_filtro.filter(ProfileView.viewer_id == viewer_id).first()
    else:
        recent_view = query_filtro.filter(ProfileView.viewer_ip == viewer_ip, ProfileView.viewer_id == None).first()

    if not recent_view:
        new_view = ProfileView(user_id=user_id, viewer_id=viewer_id, viewer_ip=viewer_ip)
        try:
            db.session.add(new_view)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao registrar ProfileView: {e}")

    reviews = Review.query.filter_by(provider_id=user_id, status='approved').order_by(Review.created_at.desc()).all()
    is_favorite = Favorite.query.filter_by(user_id=current_user.id, provider_id=user_id).first() is not None if is_authenticated else False

    return render_template('perfil_publico.html', user=user, service=service, portfolio=portfolio,
                           reviews=reviews, is_favorite=is_favorite)


@app.route('/favoritar/<int:provider_id>', methods=['POST'])
@login_required
def favoritar(provider_id):
    """Alterna o estado de favorito de forma assíncrona respeitando restrições."""
    if current_user.id == provider_id:
        return jsonify({
            'status': 'error',
            'message': 'Você não pode favoritar o seu próprio perfil.'
        }), 400

    User.query.get_or_404(provider_id)
    existing_favorite = Favorite.query.filter_by(user_id=current_user.id, provider_id=provider_id).first()

    try:
        if existing_favorite:
            db.session.delete(existing_favorite)
            db.session.commit()
            return jsonify({
                'status': 'success',
                'action': 'removed',
                'message': 'Removido dos favoritos com sucesso.'
            }), 200
        else:
            new_favorite = Favorite(user_id=current_user.id, provider_id=provider_id)
            db.session.add(new_favorite)
            db.session.commit()
            return jsonify({
                'status': 'success',
                'action': 'added',
                'message': 'Adicionado aos favoritos com sucesso!'
            }), 201
    except Exception:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Erro interno ao processar a requisição no banco.'
        }), 500


@app.route('/meus-favoritos')
@login_required
def meus_favoritos():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    return render_template('favoritos.html', favorites=favorites)


@app.route('/registrar_contato/<int:provider_id>', methods=['POST'])
@login_required
def registrar_contato(provider_id):
    """Registra interações de clique assíncronas direcionadas ao WhatsApp do prestador."""
    if current_user.id == provider_id:
        return jsonify({
            'status': 'error',
            'message': 'Auto-contatos não geram registros no histórico.'
        }), 400

    User.query.get_or_404(provider_id)
    new_contact = ContactHistory(client_id=current_user.id, provider_id=provider_id)

    try:
        db.session.add(new_contact)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'message': 'Interação de contato computada com sucesso.'
        }), 201
    except Exception:
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': 'Erro interno ao registrar o histórico.'
        }), 500


@app.route('/avaliar/<int:provider_id>', methods=['POST'])
@login_required
def avaliar(provider_id):
    provider = User.query.get_or_404(provider_id)

    if not provider.is_provider:
        flash('Este usuário não é um prestador de serviços.', 'danger')
        return redirect(url_for('perfil_publico', user_id=provider_id))

    if current_user.id == provider.id:
        flash('Você não pode avaliar a si mesmo!', 'warning')
        return redirect(url_for('perfil_publico', user_id=provider_id))

    try:
        rating = int(request.form.get('rating', 0))
        comment = request.form.get('comment', '').strip()
    except (ValueError, TypeError):
        flash('Dados de avaliação inválidos.', 'danger')
        return redirect(url_for('perfil_publico', user_id=provider_id))

    if rating < 1 or rating > 5:
        flash('A nota deve estar entre 1 e 5 estrelas.', 'danger')
        return redirect(url_for('perfil_publico', user_id=provider_id))

    existing_review = Review.query.filter_by(reviewer_id=current_user.id, provider_id=provider_id).first()
    if existing_review:
        flash('Você já avaliou este prestador anteriormente.', 'info')
        return redirect(url_for('perfil_publico', user_id=provider_id))

    new_review = Review(
        reviewer_id=current_user.id,
        provider_id=provider_id,
        rating=rating,
        comment=comment,
        status='approved'
    )

    try:
        db.session.add(new_review)
        db.session.commit()
        flash('Avaliação enviada com sucesso!', 'success')
    except Exception:
        db.session.rollback()
        flash('Erro interno ao salvar sua avaliação.', 'danger')

    return redirect(url_for('perfil_publico', user_id=provider_id))


@app.route('/denunciar/<int:user_id>', methods=['POST'])
@login_required
def denunciar(user_id):
    reason = request.form.get('reason')
    description = request.form.get('description', '')

    if not reason:
        flash('Motivo da denúncia é obrigatório')
        return redirect(request.referrer)

    report = Report(
        reporter_id=current_user.id,
        reported_id=user_id,
        reason=reason,
        description=description
    )
    db.session.add(report)
    db.session.commit()

    flash('Denúncia enviada! Nossa equipe irá analisar.')
    return redirect(request.referrer)


@app.route('/busca-avancada')
def busca_avancada():
    query = Service.query.filter_by(is_available=True).join(User)

    bairro = request.args.get('bairro', '')
    categoria = request.args.get('categoria', '')
    ordenar = request.args.get('ordenar', '')

    if bairro:
        query = query.filter(User.bairro.ilike(f'%{bairro}%'))

    if categoria and categoria != 'Todos':
        query = query.filter(Service.categoria == categoria)

    if ordenar == 'preco_asc':
        query = query.order_by(Service.preco_medio)
    elif ordenar == 'preco_desc':
        query = query.order_by(Service.preco_medio.desc())
    else:
        query = query.order_by(User.trust_seal.desc())

    servicos = query.all()
    categorias = ['Todos', 'Encanador', 'Eletricista', 'Pedreiro', 'Pintor', 'Jardineiro', 'Entregador', 'Faxineiro']

    return render_template('busca_avancada.html', servicos=servicos, bairro=bairro, categoria=categoria,
                           categorias=categorias, ordenar=ordenar)


# ==============================================
# APIS / ENDPOINTS JSON INTERNOS
# ==============================================
@app.route('/api/profile/<int:user_id>')
def api_profile(user_id):
    user = User.query.get_or_404(user_id)
    service = Service.query.filter_by(user_id=user_id).first()
    availability = Availability.query.filter_by(user_id=user_id).first()
    portfolio = PortfolioImage.query.filter_by(user_id=user_id).order_by(
        PortfolioImage.is_primary.desc(),
        PortfolioImage.created_at.desc()
    ).all()

    if not service:
        return jsonify({'success': False, 'error': 'Profissional não encontrado'}), 404

    availability_dict = {}
    if availability:
        availability_dict = {
            'Segunda': availability.segunda, 'Terça': availability.terca, 'Quarta': availability.quarta,
            'Quinta': availability.quinta, 'Sexta': availability.sexta, 'Sábado': availability.sabado,
            'Domingo': availability.domingo
        }

    portfolio_list = [{
        'id': img.id, 'image_path': img.image_path, 'title': img.title,
        'description': img.description, 'is_primary': img.is_primary,
        'created_at': img.created_at.strftime('%d/%m/%Y')
    } for img in portfolio]

    return jsonify({
        'success': True,
        'profile': {
            'user_id': user.id, 'name': user.name, 'bairro': user.bairro,
            'bio': user.bio[:300] if user.bio else '', 'telefone': user.telefone,
            'trust_seal': user.trust_seal, 'profile_image': user.profile_image,
            'categoria': service.categoria, 'preco_medio': service.preco_medio,
            'is_available': service.is_available, 'availability': availability_dict,
            'portfolio': portfolio_list
        }
    })


# ==============================================
# PAINEL ADMINISTRATIVO (ADMIN)
# ==============================================
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.email != 'admin@namao.com':
        flash('Acesso negado')
        return redirect(url_for('index'))

    pending_reports = Report.query.filter_by(status='pending').all()
    pending_reviews = Review.query.filter_by(status='pending').all()
    pending_services = Service.query.filter_by(is_approved=False).all()

    return render_template('admin_dashboard.html',
                           pending_reports=pending_reports,
                           pending_reviews=pending_reviews,
                           pending_services=pending_services)


@app.route('/admin/aprovar-servico/<int:service_id>')
@login_required
def aprovar_servico(service_id):
    if current_user.email != 'admin@namao.com':
        flash('Acesso negado')
        return redirect(url_for('index'))

    service = Service.query.get_or_404(service_id)
    service.is_approved = True
    db.session.commit()

    flash('Serviço aprovado!')
    return redirect(url_for('admin_dashboard'))


@app.route('/whatsapp-redirect/<int:user_id>')
@login_required
def whatsapp_redirect(user_id):
    """
    Registra o contato no banco de dados e redireciona
    o cliente de forma segura para o WhatsApp do prestador.
    """
    if current_user.id == user_id:
        flash('Você não pode iniciar um contato com você mesmo.')
        return redirect(url_for('index'))

    prestador = User.query.get_or_404(user_id)

    # Salva no histórico de interações de contato
    novo_contato = ContactHistory(client_id=current_user.id, provider_id=user_id)
    try:
        db.session.add(novo_contato)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Loga o erro internamente mas deixa o usuário prosseguir
        print(f"Erro ao computar histórico de contato: {e}")

    # Garante que o número tenha apenas dígitos
    telefone_limpo = re.sub(r'\D', '', prestador.telefone)

    # Se o telefone não tiver o código do país (55), adiciona por padrão
    if len(telefone_limpo) == 11 or len(telefone_limpo) == 10:
        telefone_limpo = f"55{telefone_limpo}"

    texto_mensagem = quote(f"Olá {prestador.name}, vi seu perfil no NaMão e gostaria de solicitar um orçamento!")
    link_whatsapp = f"https://api.whatsapp.com/send?phone={telefone_limpo}&text={texto_mensagem}"

    return redirect(link_whatsapp)

@app.route('/contato')
def contato():
    """Página de contato e suporte ao cliente"""
    return render_template('contato.html')

# ==============================================
# EXECUÇÃO DO SISTEMA
# ==============================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)