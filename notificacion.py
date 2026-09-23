import os,urllib.request,urllib.parse,urllib.error,json
from email.message import EmailMessage
import smtplib

def telegram_send(chat_id,text):
 token=os.getenv('TELEGRAM_BOT_TOKEN')
 if not token or not chat_id:return False
 try:
  url=f"https://api.telegram.org/bot{token}/sendMessage"
  data=f"chat_id={chat_id}&text={urllib.parse.quote(text)}"
  req=urllib.request.Request(url,data=data.encode(),headers={'Content-Type':'application/x-www-form-urlencoded'})
  with urllib.request.urlopen(req,timeout=8) as r:resp=r.read()
  return True
 except Exception:return False

def email_send(to,subject,body):
 if not to:return 'Sin correo'
 if not os.getenv('SMTP_HOST'):
  os.makedirs('instance',exist_ok=True)
  with open('instance/outbox.log','a',encoding='utf8') as f:f.write(f'\nTO:{to}\nSUBJECT:{subject}\n{body}\n')
  return 'Bandeja demo'
 try:
  m=EmailMessage();m['To']=to;m['From']=os.getenv('SMTP_FROM','noreply@clinica.demo');m['Subject']=subject;m.set_content(body)
  with smtplib.SMTP(os.getenv('SMTP_HOST'),int(os.getenv('SMTP_PORT','587')),timeout=8) as sv:
   if os.getenv('SMTP_TLS','true')=='true':sv.starttls()
   if os.getenv('SMTP_USER'):sv.login(os.getenv('SMTP_USER'),os.getenv('SMTP_PASSWORD'))
   sv.send_message(m)
  return 'Enviado'
 except Exception as e:return 'Error SMTP: '+str(e)

def notificar(chat_id=None,email=None,telefono=None,asunto='Notificación',cuerpo=''):
 text=f"{asunto}\n\n{cuerpo}"
 enviados=[]
 if chat_id and telegram_send(chat_id,text):enviados.append('Telegram OK')
 if email:
  res=email_send(email,asunto,cuerpo)
  enviados.append('Email: '+res)
 if not enviados:
  os.makedirs('instance',exist_ok=True)
  with open('instance/outbox.log','a',encoding='utf8') as f:f.write(f'\nTO:{chat_id or email or telefono}\nASUNTO:{asunto}\n{cuerpo}\n')
  enviados.append('Bandeja demo')
 return ' | '.join(enviados)
