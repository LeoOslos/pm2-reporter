import os
import datetime
import yagmail
from dotenv import load_dotenv

load_dotenv()

LOGS_A_MONITOREAR = {
    "PM2": os.path.expanduser('~/.pm2/pm2.log'),
    "TICKETS": os.path.expanduser('~/ticket-processor-agent/agente.log'),
    "SENSORES": os.path.expanduser('~/sensores/log_ejecucion.txt')
}

RECEPTOR = os.getenv('EMAIL_RECEPTOR')
EMISOR = os.getenv('EMAIL_EMISOR')
PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
NOMBRE_SERVER = os.getenv('NOMBRE_SERVER')

def procesar_logs():
    errores_encontrados = []
    ahora = datetime.datetime.now()

    for etiqueta, ruta in LOGS_A_MONITOREAR.items():
        if os.path.exists(ruta) and os.path.getsize(ruta) > 0:
            try:
                # 1. Leemos el log actual
                with open(ruta, 'r', encoding='utf-8') as f:
                    lineas = f.readlines()
                
                # 2. Guardamos TODO en un archivo histórico antes de borrar
                ruta_hist = f"{ruta}.hist"
                with open(ruta_hist, 'a', encoding='utf-8') as f_hist:
                    f_hist.write(f"\n--- SESION {ahora.strftime('%Y-%m-%d %H:%M')} ---\n")
                    f_hist.writelines(lineas)

                # 3. Filtramos errores para el mail
                errores = [l.strip() for l in lineas if any(word in l.lower() for word in ["error", "exception", "tserror", "failed"])]
                
                if errores:
                    errores_encontrados.append(f"--- ERRORES EN {etiqueta} ---")
                    errores_encontrados.extend(errores)
                    errores_encontrados.append("")

                # 4. Vaciamos el log activo (los datos ya están seguros en el .hist)
                with open(ruta, 'w') as f_clean:
                    f_clean.truncate(0)

            except Exception as e:
                print(f"Error procesando {etiqueta}: {e}")

    if errores_encontrados:
        cuerpo = f"Reporte de errores unificado - {NOMBRE_SERVER}\n"
        cuerpo += f"Fecha: {ahora.strftime('%d/%m/%Y %H:%M')}\n"
        cuerpo += "Nota: Los logs completos fueron movidos a archivos .hist\n"
        cuerpo += "="*50 + "\n\n"
        cuerpo += "\n".join(errores_encontrados)
        enviar_mail(f"⚠️ Alerta {NOMBRE_SERVER}: Errores detectados", cuerpo)
    else:
        print(f"[{ahora}] Sin errores nuevos.")

def enviar_mail(asunto, contenido):
    try:
        yag = yagmail.SMTP({EMISOR: NOMBRE_SERVER}, PASSWORD)
        yag.send(to=RECEPTOR, subject=asunto, contents=contenido)
        print("Reporte enviado con éxito.")
    except Exception as e:
        print(f"Error enviando mail: {e}")

if __name__ == "__main__":
    procesar_logs()