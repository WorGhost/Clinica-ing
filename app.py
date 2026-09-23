from datetime import datetime,date,time,timedelta
from calendar import monthrange
from functools import wraps
import os,json,urllib.request
from dotenv import load_dotenv; load_dotenv()
from flask import Flask,render_template,request,redirect,url_for,flash,jsonify,abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_user,logout_user,login_required,current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash,check_password_hash
from notificacion import notificar

db=SQLAlchemy(); login_manager=LoginManager(); csrf=CSRFProtect()
class User(UserMixin,db.Model):
 id=db.Column(db.Integer,primary_key=True);name=db.Column(db.String(120),nullable=False);email=db.Column(db.String(160),unique=True,nullable=False);password=db.Column(db.String(255),nullable=False);role=db.Column(db.String(30),nullable=False);active=db.Column(db.Boolean,default=True)
 doctor=db.relationship('Doctor',backref='user',uselist=False)
 @property
 def is_active(self):return self.active
class Patient(db.Model):
  id=db.Column(db.Integer,primary_key=True);document=db.Column(db.String(30),unique=True,nullable=False);name=db.Column(db.String(140),nullable=False);birth_date=db.Column(db.Date);phone=db.Column(db.String(30));email=db.Column(db.String(150));chat_id=db.Column(db.String(60),nullable=True);blood=db.Column(db.String(5));active=db.Column(db.Boolean,default=True)
  history=db.relationship('ClinicalHistory',backref='patient',uselist=False,cascade='all,delete-orphan')
class Specialty(db.Model):id=db.Column(db.Integer,primary_key=True);name=db.Column(db.String(100),unique=True,nullable=False)
class Doctor(db.Model):
 id=db.Column(db.Integer,primary_key=True);user_id=db.Column(db.Integer,db.ForeignKey('user.id'),unique=True);license=db.Column(db.String(60),unique=True,nullable=False);specialty_id=db.Column(db.Integer,db.ForeignKey('specialty.id'));active=db.Column(db.Boolean,default=True)
 specialty=db.relationship('Specialty')
class Service(db.Model):id=db.Column(db.Integer,primary_key=True);name=db.Column(db.String(120));duration=db.Column(db.Integer,default=30);price_usd=db.Column(db.Float,default=25)
class Schedule(db.Model):id=db.Column(db.Integer,primary_key=True);doctor_id=db.Column(db.Integer,db.ForeignKey('doctor.id'));weekday=db.Column(db.Integer);start=db.Column(db.Time);end=db.Column(db.Time)
class Appointment(db.Model):
 id=db.Column(db.Integer,primary_key=True);patient_id=db.Column(db.Integer,db.ForeignKey('patient.id'));doctor_id=db.Column(db.Integer,db.ForeignKey('doctor.id'));service_id=db.Column(db.Integer,db.ForeignKey('service.id'));starts=db.Column(db.DateTime);ends=db.Column(db.DateTime);status=db.Column(db.String(30),default='CONFIRMADA');reservation_type=db.Column(db.String(40),default='PRESENCIAL');reason=db.Column(db.String(500))
 patient=db.relationship('Patient');doctor=db.relationship('Doctor');service=db.relationship('Service');consultation=db.relationship('Consultation',backref='appointment',uselist=False)
class ClinicalHistory(db.Model):
 id=db.Column(db.Integer,primary_key=True);patient_id=db.Column(db.Integer,db.ForeignKey('patient.id'),unique=True);notes=db.Column(db.Text)
 allergies=db.relationship('Allergy',backref='history',cascade='all,delete-orphan');antecedents=db.relationship('Antecedent',backref='history',cascade='all,delete-orphan')
class Allergy(db.Model):id=db.Column(db.Integer,primary_key=True);history_id=db.Column(db.Integer,db.ForeignKey('clinical_history.id'));substance=db.Column(db.String(120));reaction=db.Column(db.String(250));severity=db.Column(db.String(30))
class Antecedent(db.Model):id=db.Column(db.Integer,primary_key=True);history_id=db.Column(db.Integer,db.ForeignKey('clinical_history.id'));kind=db.Column(db.String(60));description=db.Column(db.String(500))
class Consultation(db.Model):
 id=db.Column(db.Integer,primary_key=True);appointment_id=db.Column(db.Integer,db.ForeignKey('appointment.id'),unique=True);doctor_id=db.Column(db.Integer,db.ForeignKey('doctor.id'));motive=db.Column(db.String(500));vitals=db.Column(db.String(500));exam=db.Column(db.Text);diagnosis=db.Column(db.Text);treatment=db.Column(db.Text);status=db.Column(db.String(30),default='FINALIZADA');created=db.Column(db.DateTime,default=datetime.utcnow)
 doctor=db.relationship('Doctor');prescription=db.relationship('Prescription',backref='consultation',uselist=False,cascade='all,delete-orphan')
class Prescription(db.Model):id=db.Column(db.Integer,primary_key=True);consultation_id=db.Column(db.Integer,db.ForeignKey('consultation.id'),unique=True);status=db.Column(db.String(30),default='BORRADOR');issued=db.Column(db.DateTime);items=db.relationship('PrescriptionItem',backref='prescription',cascade='all,delete-orphan')
class PrescriptionItem(db.Model):id=db.Column(db.Integer,primary_key=True);prescription_id=db.Column(db.Integer,db.ForeignKey('prescription.id'));medicine=db.Column(db.String(160));dose=db.Column(db.String(100));frequency=db.Column(db.String(100));route=db.Column(db.String(60));duration=db.Column(db.String(100))
class Exam(db.Model):id=db.Column(db.Integer,primary_key=True);name=db.Column(db.String(150),unique=True);description=db.Column(db.String(500));price_usd=db.Column(db.Float);active=db.Column(db.Boolean,default=True)
class ExchangeRate(db.Model):id=db.Column(db.Integer,primary_key=True);rate=db.Column(db.Float);source=db.Column(db.String(80));rate_date=db.Column(db.Date);fetched=db.Column(db.DateTime,default=datetime.utcnow)
class Payment(db.Model):id=db.Column(db.Integer,primary_key=True);appointment_id=db.Column(db.Integer,db.ForeignKey('appointment.id'),unique=True);amount_usd=db.Column(db.Float);rate=db.Column(db.Float);amount_ves=db.Column(db.Float);method=db.Column(db.String(40));reference=db.Column(db.String(80));status=db.Column(db.String(30),default='APROBADO');appointment=db.relationship('Appointment')
class Audit(db.Model):id=db.Column(db.Integer,primary_key=True);user_id=db.Column(db.Integer,db.ForeignKey('user.id'));action=db.Column(db.String(80));entity=db.Column(db.String(80));entity_id=db.Column(db.Integer);detail=db.Column(db.String(500));created=db.Column(db.DateTime,default=datetime.utcnow);user=db.relationship('User')
@login_manager.user_loader
def load(uid):return db.session.get(User,int(uid))
def audit(action,entity='',eid=None,detail=''):db.session.add(Audit(user_id=current_user.id if current_user.is_authenticated else None,action=action,entity=entity,entity_id=eid,detail=detail))
def roles(*allowed):
 def deco(fn):
  @wraps(fn)
  @login_required
  def inner(*a,**k):
   if current_user.role not in allowed:abort(403)
   return fn(*a,**k)
  return inner
 return deco
def rate(force=False):
 today=date.today();cached=ExchangeRate.query.filter_by(rate_date=today).order_by(ExchangeRate.fetched.desc()).first()
 if cached and not force:return cached
 try:
  headers={'User-Agent':'Mozilla/5.0'}
  if os.getenv('BCV_API_KEY'):headers['Authorization']=os.getenv('BCV_API_KEY')
  req=urllib.request.Request(os.getenv('BCV_API_URL','https://ve.dolarapi.com/v1/dolares/oficial'),headers=headers)
  with urllib.request.urlopen(req,timeout=7) as r:data=json.loads(r.read())
  tasa=float(data.get('tasa') or data.get('rate') or data.get('promedio'))
  x=ExchangeRate(rate=tasa,source=data.get('fuente','BCV API'),rate_date=date.fromisoformat(data.get('fecha',today.isoformat())));db.session.add(x);db.session.commit();return x
 except Exception:
   x=ExchangeRate.query.order_by(ExchangeRate.rate_date.desc()).first()
   if x:return x
   x=ExchangeRate(rate=float(os.getenv('BCV_FALLBACK_RATE','36.50')),source='MANUAL/FALLBACK',rate_date=today);db.session.add(x);db.session.commit();return x

def create_app(cfg=None):
 a=Flask(__name__,instance_relative_config=True);a.config.update(SECRET_KEY=os.getenv('SECRET_KEY','dev-secret'),SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL','sqlite:///clinica.db'),SQLALCHEMY_TRACK_MODIFICATIONS=False)
 if cfg:a.config.update(cfg)
 os.makedirs(a.instance_path,exist_ok=True);db.init_app(a);login_manager.init_app(a);csrf.init_app(a);login_manager.login_view='login'
 @a.context_processor
 def ctx():return {'now':datetime.now}
 @a.route('/')
 def home():return redirect(url_for('dashboard' if current_user.is_authenticated else 'login'))
 @a.route('/login',methods=['GET','POST'])
 def login():
  if request.method=='POST':
   u=User.query.filter_by(email=request.form['email'].lower()).first()
   if u and u.active and check_password_hash(u.password,request.form['password']):login_user(u);audit('LOGIN','User',u.id);db.session.commit();return redirect(url_for('dashboard'))
   flash('Credenciales inválidas.','danger')
  return render_template('login.html')
 @a.post('/logout')
 @login_required
 def logout():logout_user();return redirect(url_for('login'))
 @a.route('/dashboard')
 @login_required
 def dashboard():return render_template('dashboard.html',stats=[Patient.query.count(),Appointment.query.count(),Consultation.query.count(),Prescription.query.filter_by(status='EMITIDA').count()],upcoming=Appointment.query.filter(Appointment.starts>=datetime.now()).order_by(Appointment.starts).limit(6).all())
 @a.route('/patients')
 @login_required
 def patients():
  q=request.args.get('q','');query=Patient.query
  if q:query=query.filter(db.or_(Patient.name.contains(q),Patient.document.contains(q)))
  return render_template('patients.html',patients=query.order_by(Patient.name).all(),q=q)
 @a.route('/patients/new',methods=['GET','POST'])
 @roles('ADMINISTRADOR','RECEPCIONISTA')
 def patient_new():
  if request.method=='POST':
   if Patient.query.filter_by(document=request.form['document']).first():flash('Documento duplicado.','danger')
   else:
    p=Patient(document=request.form['document'],name=request.form['name'],birth_date=date.fromisoformat(request.form['birth_date']) if request.form.get('birth_date') else None,phone=request.form['phone'],email=request.form.get('email'),chat_id=request.form.get('chat_id') or None,blood=request.form.get('blood'));p.history=ClinicalHistory();db.session.add(p);db.session.flush();audit('CREATE','Patient',p.id);db.session.commit();return redirect(url_for('patient_detail',id=p.id))
  return render_template('patient_form.html')
 @a.route('/patients/<int:id>')
 @login_required
 def patient_detail(id):return render_template('patient_detail.html',p=Patient.query.get_or_404(id))
 @a.route('/patients/<int:id>/history',methods=['GET','POST'])
 @roles('MEDICO')
 def history(id):
  p=Patient.query.get_or_404(id)
  if request.method=='POST':db.session.add(Allergy(history_id=p.history.id,substance=request.form['substance'],reaction=request.form.get('reaction'),severity=request.form['severity']));audit('CREATE','Allergy',detail=p.name);db.session.commit()
  audit('VIEW_HISTORY','Patient',p.id);db.session.commit();consults=Consultation.query.join(Appointment).filter(Appointment.patient_id==id).all();return render_template('history.html',p=p,consults=consults)
 @a.route('/doctors')
 @login_required
 def doctors():return render_template('doctors.html',doctors=Doctor.query.all())
 @a.route('/doctors/new',methods=['GET','POST'])
 @roles('ADMINISTRADOR')
 def doctor_new():
  if request.method=='POST':
   u=User(name=request.form['name'],email=request.form['email'].lower(),password=generate_password_hash(request.form.get('password','demo123')),role='MEDICO');db.session.add(u);db.session.flush();d=Doctor(user_id=u.id,license=request.form['license'],specialty_id=int(request.form['specialty_id']));db.session.add(d);db.session.flush()
   for wd in range(5):db.session.add(Schedule(doctor_id=d.id,weekday=wd,start=time(8),end=time(16)))
   audit('CREATE','Doctor',d.id);db.session.commit();return redirect(url_for('doctors'))
  return render_template('doctor_form.html',specialties=Specialty.query.all())
 @a.post('/doctors/<int:id>/toggle')
 @roles('ADMINISTRADOR')
 def doctor_toggle(id):d=Doctor.query.get_or_404(id);d.active=not d.active;d.user.active=d.active;db.session.commit();return redirect(url_for('doctors'))
 @a.post('/doctors/<int:id>/delete')
 @roles('ADMINISTRADOR')
 def doctor_delete(id):
  d=Doctor.query.get_or_404(id)
  if Appointment.query.filter_by(doctor_id=id).first():d.active=False;d.user.active=False;flash('Se desactivó para conservar historial.','danger')
  else:db.session.delete(d.user)
  db.session.commit();return redirect(url_for('doctors'))
 @a.route('/agenda')
 @login_required
 def agenda():
  f=date.fromisoformat(request.args.get('date',date.today().isoformat()));start=datetime.combine(f,time.min);return render_template('agenda.html',items=Appointment.query.filter(Appointment.starts>=start,Appointment.starts<start+timedelta(days=1)).order_by(Appointment.starts).all(),selected=f)
 @a.route('/calendar')
 @login_required
 def calendar_view():
  t=date.today();y=int(request.args.get('year',t.year));m=int(request.args.get('month',t.month));start=datetime(y,m,1);end=datetime(y+1,1,1) if m==12 else datetime(y,m+1,1);group={}
  for x in Appointment.query.filter(Appointment.starts>=start,Appointment.starts<end).all():group.setdefault(x.starts.day,[]).append(x)
  cells=[None]*date(y,m,1).weekday()+list(range(1,monthrange(y,m)[1]+1))
  while len(cells)%7:cells.append(None)
  return render_template('calendar.html',year=y,month=m,cells=cells,group=group)
 @a.route('/appointments/new',methods=['GET','POST'])
 @roles('ADMINISTRADOR','RECEPCIONISTA')
 def appointment_new():
  if request.method=='POST':
   st=datetime.fromisoformat(request.form['starts']);sv=db.session.get(Service,int(request.form['service_id']));en=st+timedelta(minutes=sv.duration);did=int(request.form['doctor_id']);conf=Appointment.query.filter(Appointment.doctor_id==did,Appointment.status!='CANCELADA',Appointment.starts<en,Appointment.ends>st).first()
   if conf:flash('Horario ocupado.','danger')
   else:
    x=Appointment(patient_id=int(request.form['patient_id']),doctor_id=did,service_id=sv.id,starts=st,ends=en,reservation_type=request.form['reservation_type'],reason=request.form.get('reason'));db.session.add(x);db.session.flush();db.session.commit(); msg=notificar(chat_id=x.patient.chat_id,email=x.patient.email,telefono=x.patient.phone,asunto='Confirmación de cita',cuerpo=f'Cita {st:%d/%m/%Y %H:%M} - {x.reservation_type}');flash('Cita creada. Notificación: '+msg,'success');return redirect(url_for('payment',appointment_id=x.id))
  return render_template('appointment_form.html',patients=Patient.query.all(),doctors=Doctor.query.filter_by(active=True).all(),services=Service.query.all())
 @a.get('/api/availability')
 @login_required
 def availability():
  d=int(request.args['doctor_id']);sv=db.session.get(Service,int(request.args['service_id']));f=date.fromisoformat(request.args['date']);sch=Schedule.query.filter_by(doctor_id=d,weekday=f.weekday()).first();out=[]
  if sch:
   cur=datetime.combine(f,sch.start);end=datetime.combine(f,sch.end);dur=timedelta(minutes=sv.duration)
   while cur+dur<=end:
    busy=Appointment.query.filter(Appointment.doctor_id==d,Appointment.status!='CANCELADA',Appointment.starts<cur+dur,Appointment.ends>cur).first()
    if not busy and cur>=datetime.now():out.append({'value':cur.isoformat(timespec='minutes'),'label':cur.strftime('%H:%M')})
    cur+=timedelta(minutes=30)
  return jsonify(slots=out)
 @a.post('/appointments/<int:id>/cancel')
 @roles('ADMINISTRADOR','RECEPCIONISTA')
 def cancel(id):x=Appointment.query.get_or_404(id);x.status='CANCELADA';db.session.commit();return redirect(request.referrer or url_for('agenda'))
 @a.route('/payment/<int:appointment_id>',methods=['GET','POST'])
 @roles('ADMINISTRADOR','RECEPCIONISTA')
 def payment(appointment_id):
  x=Appointment.query.get_or_404(appointment_id);r=rate();
  if request.method=='POST':db.session.add(Payment(appointment_id=x.id,amount_usd=x.service.price_usd,rate=r.rate,amount_ves=x.service.price_usd*r.rate,method=request.form['method'],reference=request.form.get('reference') or 'DEMO-'+datetime.now().strftime('%H%M%S')));db.session.commit();flash('Pago ficticio aprobado.','success');return redirect(url_for('agenda',date=x.starts.date()))
  return render_template('payment.html',x=x,r=r)
 @a.route('/exams')
 @login_required
 def exams():return render_template('exams.html',exams=Exam.query.all(),r=rate(request.args.get('refresh')=='1'))
 @a.post('/rate/manual')
 @roles('ADMINISTRADOR')
 def manual_rate():db.session.add(ExchangeRate(rate=float(request.form['rate']),source='MANUAL',rate_date=date.today()));db.session.commit();return redirect(url_for('exams'))
 @a.get('/api/bcv-rate')
 @login_required
 def rate_api():r=rate(request.args.get('refresh')=='1');return jsonify(rate=r.rate,date=r.rate_date.isoformat(),source=r.source)
 @a.route('/consultations/new/<int:appointment_id>',methods=['GET','POST'])
 @roles('MEDICO')
 def consultation_new(appointment_id):
  x=Appointment.query.get_or_404(appointment_id)
  if request.method=='POST':c=Consultation(appointment_id=x.id,doctor_id=current_user.doctor.id,motive=request.form['motive'],vitals=request.form.get('vitals'),exam=request.form.get('exam'),diagnosis=request.form.get('diagnosis'),treatment=request.form.get('treatment'));x.status='COMPLETADA';db.session.add(c);db.session.commit();return redirect(url_for('prescription',consultation_id=c.id))
  return render_template('consultation.html',x=x)
 @a.route('/prescription/<int:consultation_id>',methods=['GET','POST'])
 @roles('MEDICO')
 def prescription(consultation_id):
  c=Consultation.query.get_or_404(consultation_id);rx=c.prescription or Prescription(consultation=c)
  if request.method=='POST':
   if not rx.id:db.session.add(rx);db.session.flush()
   if request.form.get('medicine'):db.session.add(PrescriptionItem(prescription_id=rx.id,medicine=request.form['medicine'],dose=request.form['dose'],frequency=request.form['frequency'],route=request.form['route'],duration=request.form['duration']))
   if request.form.get('emit'):db.session.flush();rx.status='EMITIDA';rx.issued=datetime.utcnow()
   db.session.commit()
  return render_template('prescription.html',c=c,rx=rx)
 @a.route('/audit')
 @roles('ADMINISTRADOR')
 def audit_view():return render_template('audit.html',logs=Audit.query.order_by(Audit.created.desc()).limit(200).all())
 @a.route('/test-center')
 @login_required
 def tests():return render_template('tests.html')
 @a.get('/api/health')
 def health():return jsonify(status='ok',database='sqlite',time=datetime.now().isoformat())
 @a.errorhandler(403)
 def e403(e):return render_template('error.html',code=403,msg='Acceso denegado'),403
 with a.app_context():db.create_all();seed()
 return a

def seed():
 if User.query.first():return
 users=[]
 for n,e,r in [('Admin Demo','admin@clinica.demo','ADMINISTRADOR'),('Recepción Demo','recepcion@clinica.demo','RECEPCIONISTA'),('Dra. Ana Rivas','medico@clinica.demo','MEDICO')]:users.append(User(name=n,email=e,password=generate_password_hash('demo123'),role=r))
 db.session.add_all(users);db.session.flush();sp=Specialty(name='Medicina general');db.session.add(sp);db.session.flush();d=Doctor(user_id=users[2].id,license='DEM-001',specialty_id=sp.id);db.session.add(d);db.session.flush();db.session.add(Service(name='Consulta general',duration=30,price_usd=25))
 examenes=[Service(name='Perfil Hormonal (FSH, LH, Prolactina, Testosterona, Estradiol)',duration=15,price_usd=35),Service(name='Tipaje Sanguíneo (Grupo y Factor Rh)',duration=15,price_usd=6),Service(name='Prueba de Alergias (IgE Específica / RAST)',duration=15,price_usd=35),Service(name='Perfil 20',duration=15,price_usd=15),Service(name='Hematología Completa',duration=15,price_usd=5),Service(name='Perfil Tiroideo (T3, T4, TSH)',duration=15,price_usd=25),Service(name='Perfil Lipídico (Colesterol, Triglicéridos)',duration=15,price_usd=12),Service(name='Glicemia (Azúcar en sangre)',duration=15,price_usd=4),Service(name='Rayos X de Tórax (PA y Lateral)',duration=30,price_usd=20),Service(name='Rayos X de Extremidades (Brazo/Pierna)',duration=30,price_usd=25),Service(name='Rayos X de Columna Lumbar',duration=30,price_usd=30),Service(name='Rayos X de Cráneo',duration=30,price_usd=25)]
 db.session.add_all(examenes)
 for wd in range(5):db.session.add(Schedule(doctor_id=d.id,weekday=wd,start=time(8),end=time(16)))
 p=Patient(document='V-12345678',name='María González',birth_date=date(1984,5,17),phone='0412-0000000',email='maria@example.test',blood='O+');p.history=ClinicalHistory(notes='Demo');p.history.allergies.append(Allergy(substance='Penicilina',reaction='Erupción',severity='ALTA'));p.history.antecedents.append(Antecedent(kind='PERSONAL',description='Hipertensión'))
 db.session.add_all([p,Exam(name='Hematología completa',description='Perfil hematológico básico',price_usd=12),Exam(name='Perfil lipídico',description='Colesterol y triglicéridos',price_usd=18),Exam(name='Ecografía abdominal',description='Estudio por imagen',price_usd=35),ExchangeRate(rate=float(os.getenv('BCV_FALLBACK_RATE','1')),source='DEMO/MANUAL',rate_date=date.today())]);db.session.commit()
