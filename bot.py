import json
import os
from datetime import datetime, timedelta, time
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackContext
import pytz

DB_FILE = "clientes.json"
TOKEN = "7772707700:AAF7PdzosGSm3qW5p4PKHArfOWV8FoEOOR0"

def cargar_datos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"clientes": {}}

def guardar_datos(datos):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def fecha_valida(fecha_str):
    try:
        datetime.strptime(fecha_str, "%d/%m/%y")
        return True
    except ValueError:
        return False

def formatear_base(datos):
    texto = ""
    orden = ["netflix", "disney", "prime video", "max", "youtube", "spotify", "dgo", "liga 1 max", "vix", "chatgpt",
             "paramount", "iptv", "crunchyroll", "rakuten viki", "apple tv", "scribd", "tidal", "porhub"]
    especiales = ["office 365", "mccafe"]

    for cliente_num, info_cliente in datos.get("clientes", {}).items():
        texto += f"Cliente: {cliente_num}\n"
        plataformas = info_cliente.get("plataformas", {})

        for plat in orden:
            if plat in plataformas:
                p = plataformas[plat]
                cantidad = p.get("cantidad")
                if cantidad:
                    texto += f"{plat.upper()}: {cantidad} CUENTAS\n"

        for esp in especiales:
            if esp in plataformas:
                p = plataformas[esp]
                fv = p.get("fecha_vencimiento", "")
                garantia = p.get("garantia", "")
                texto += f"{esp.upper()} (fecha de vencimiento): {fv}\n"
                if garantia:
                    texto += f"Garantía vigente hasta: {garantia}\n"

        texto += "\n"
    return texto if texto else "No hay datos registrados."

async def base(update: Update, context: ContextTypes.DEFAULT_TYPE):
    datos = cargar_datos()
    respuesta = formatear_base(datos)
    await update.message.reply_text(respuesta)

async def agregar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("Uso: /agregar (numero_cliente) (correo) (plataforma) (fecha_vencimiento dd/mm/aa)")
        return

    numero_cliente = args[0]
    correo = args[1].lower()
    plataforma = args[2].lower()
    fecha_vencimiento = args[3]

    plataformas_validas = ["netflix", "disney", "max", "prime video", "youtube", "spotify", "dgo", "liga 1 max",
                          "vix", "chatgpt", "paramount", "iptv", "crunchyroll", "rakuten viki", "apple tv", "scribd",
                          "tidal", "porhub", "office 365", "mccafe"]

    if plataforma not in plataformas_validas:
        await update.message.reply_text(f"Plataforma inválida. Usa una de: {', '.join(plataformas_validas)}")
        return

    if not fecha_valida(fecha_vencimiento):
        await update.message.reply_text("Formato de fecha inválido. Usa dd/mm/aa, por ejemplo 23/05/25")
        return

    datos = cargar_datos()

    if numero_cliente not in datos["clientes"]:
        datos["clientes"][numero_cliente] = {"plataformas": {}}

    plataformas = datos["clientes"][numero_cliente]["plataformas"]

    if plataforma in plataformas:
        p = plataformas[plataforma]
        if "correos" in p:
            if correo not in p["correos"]:
                p["correos"].append(correo)
        else:
            p["correos"] = [correo]

        fecha_actual = datetime.strptime(p["fecha_vencimiento"], "%d/%m/%y")
        nueva_fecha = datetime.strptime(fecha_vencimiento, "%d/%m/%y")
        if nueva_fecha > fecha_actual:
            p["fecha_vencimiento"] = fecha_vencimiento
    else:
        p = {"correos": [correo], "fecha_vencimiento": fecha_vencimiento}
        if plataforma in ["netflix", "disney", "max", "prime video", "youtube", "spotify", "dgo", "liga 1 max",
                          "vix", "chatgpt", "paramount", "iptv", "crunchyroll", "rakuten viki", "apple tv", "scribd",
                          "tidal", "porhub"]:
            p["cantidad"] = 1
        if plataforma in ["office 365", "mccafe"]:
            fv_date = datetime.strptime(fecha_vencimiento, "%d/%m/%y")
            garantia_date = fv_date + timedelta(days=180)
            p["garantia"] = garantia_date.strftime("%d/%m/%y")

        plataformas[plataforma] = p

    for plat in plataformas:
        if plat in ["netflix", "disney", "max", "prime video", "youtube", "spotify", "dgo", "liga 1 max",
                    "vix", "chatgpt", "paramount", "iptv", "crunchyroll", "rakuten viki", "apple tv", "scribd",
                    "tidal", "porhub"]:
            plataformas[plat]["cantidad"] = len(plataformas[plat].get("correos", []))

    guardar_datos(datos)
    await update.message.reply_text(f"Información agregada/actualizada para cliente {numero_cliente}, plataforma {plataforma.upper()}.")

async def reemplazar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Uso: /reemplazar (numero_cliente) (correo_nuevo) (correo_antiguo)")
        return

    numero_cliente = args[0]
    correo_nuevo = args[1].lower()
    correo_antiguo = args[2].lower()

    datos = cargar_datos()

    if numero_cliente not in datos["clientes"]:
        await update.message.reply_text(f"No se encontró cliente con número {numero_cliente}")
        return

    plataformas = datos["clientes"][numero_cliente].get("plataformas", {})

    reemplazado = False
    for plat, info_plat in plataformas.items():
        correos = info_plat.get("correos", [])
        if correo_antiguo in correos:
            correos = [correo_nuevo if c == correo_antiguo else c for c in correos]
            info_plat["correos"] = correos
            if plat in ["netflix", "disney", "max", "prime video", "youtube", "spotify", "dgo", "liga 1 max",
                        "vix", "chatgpt", "paramount", "iptv", "crunchyroll", "rakuten viki", "apple tv", "scribd",
                        "tidal", "porhub"]:
                info_plat["cantidad"] = len(correos)
            reemplazado = True
            break

    if reemplazado:
        guardar_datos(datos)
        await update.message.reply_text(f"Correo reemplazado para cliente {numero_cliente}: {correo_antiguo} → {correo_nuevo}")
    else:
        await update.message.reply_text(f"No se encontró el correo {correo_antiguo} para el cliente {numero_cliente}")

async def renovar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("Uso: /renovar (numero_cliente) (correo) (plataforma) (nueva_fecha_vencimiento dd/mm/aa)")
        return

    numero_cliente = args[0]
    correo = args[1].lower()
    plataforma = args[2].lower()
    nueva_fecha = args[3]

    if not fecha_valida(nueva_fecha):
        await update.message.reply_text("Formato de fecha inválido. Usa dd/mm/aa, por ejemplo 23/05/25")
        return

    datos = cargar_datos()
    if numero_cliente not in datos["clientes"]:
        await update.message.reply_text(f"No se encontró cliente con número {numero_cliente}")
        return

    plataformas = datos["clientes"][numero_cliente].get("plataformas", {})
    if plataforma not in plataformas:
        await update.message.reply_text(f"No se encontró la plataforma {plataforma} para el cliente {numero_cliente}")
        return

    p = plataformas[plataforma]
    correos = p.get("correos", [])

    if correo not in correos:
        await update.message.reply_text(f"No se encontró el correo {correo} en la plataforma {plataforma} para el cliente {numero_cliente}")
        return

    # Actualizar fecha de vencimiento
    p["fecha_vencimiento"] = nueva_fecha

    # Si es plataforma especial, actualizar garantía
    if plataforma in ["office 365", "mccafe"]:
        fv_date = datetime.strptime(nueva_fecha, "%d/%m/%y")
        garantia_date = fv_date + timedelta(days=180)
        p["garantia"] = garantia_date.strftime("%d/%m/%y")

    guardar_datos(datos)
    await update.message.reply_text(f"Fecha de vencimiento actualizada para cliente {numero_cliente}, plataforma {plataforma.upper()}, correo {correo} a {nueva_fecha}.")

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "Comandos disponibles:\n\n"
        "/base - Muestra la base de clientes y plataformas.\n"
        "/agregar (numero_cliente) (correo) (plataforma) (fecha_vencimiento) - Agrega o actualiza cliente y plataforma.\n"
        "/reemplazar (numero_cliente) (correo_nuevo) (correo_antiguo) - Cambia correo existente.\n"
        "/buscar (numero_cliente) - Muestra todas las cuentas y fechas del cliente.\n"
        "/renovar (numero_cliente) (correo) (plataforma) (nueva_fecha) - Actualiza la fecha de vencimiento.\n"
        "/comandos - Muestra esta ayuda.\n"
    )
    await update.message.reply_text(texto)

async def enviar_mensajes_vencidos(context: CallbackContext):
    datos = cargar_datos()
    hoy = datetime.now()
    chat_id_administrador = 5411037672  # Cambia por tu chat id

    orden_plataformas = ["netflix", "disney", "prime video", "max", "youtube", "spotify", "dgo", "liga 1 max", "vix",
                        "chatgpt", "paramount", "iptv", "crunchyroll", "rakuten viki", "apple tv", "scribd", "tidal", "porhub"]

    no_renovados_mensaje = "CUENTAS NO RENOVADAS:\n"

    for cliente_num, info_cliente in datos.get("clientes", {}).items():
        plataformas = info_cliente.get("plataformas", {})

        for plat in orden_plataformas:
            if plat in plataformas:
                p = plataformas[plat]
                fv_str = p.get("fecha_vencimiento")
                if not fv_str:
                    continue
                try:
                    fv = datetime.strptime(fv_str, "%d/%m/%y")
                except:
                    continue

                # Aviso de vencidos (igual que antes)
                if fv.date() < hoy.date():
                    correos = p.get("correos", [])
                    correo_mostrar = correos[0] if correos else "sin correo"
                    texto = (f"Buen día, tu plataforma de {plat.upper()} correo: {correo_mostrar} ha vencido.\n"
                             f"Confirmar renovación para evitar cortes.")

                    wa_num = cliente_num
                    wa_text = urllib.parse.quote(texto)
                    wa_link = f"https://wa.me/{wa_num}?text={wa_text}"

                    botones = [[InlineKeyboardButton("Enviar WhatsApp", url=wa_link)]]

                    await context.bot.send_message(chat_id=chat_id_administrador, text=texto, reply_markup=InlineKeyboardMarkup(botones))

                # Detectar cuentas no renovadas (vencidas hace más de 1 día)
                dias_pasados = (hoy.date() - fv.date()).days
                if dias_pasados > 1:
                    correos = p.get("correos", [])
                    for correo in correos:
                        no_renovados_mensaje += f"{cliente_num}:\n{correo}   /   {plat.upper()}   /  {fv_str}\n"

    # Enviar resumen de cuentas no renovadas si existen
    if no_renovados_mensaje != "CUENTAS NO RENOVADAS:\n":
        await context.bot.send_message(chat_id=chat_id_administrador, text=no_renovados_mensaje)
    else:
        await context.bot.send_message(chat_id=chat_id_administrador, text="No hay cuentas no renovadas.")

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Uso: /buscar (numero_cliente)")
        return

    numero_cliente = args[0]
    datos = cargar_datos()

    if numero_cliente not in datos["clientes"]:
        await update.message.reply_text(f"No se encontró cliente con número {numero_cliente}")
        return

    plataformas = datos["clientes"][numero_cliente].get("plataformas", {})

    if not plataformas:
        await update.message.reply_text("El cliente no tiene plataformas registradas.")
        return

    mensaje = f"Información para cliente {numero_cliente}:\n\n"
    for plat, info in plataformas.items():
        nombre_plat = plat.upper()
        cantidad = info.get("cantidad", len(info.get("correos", [])))
        correos = info.get("correos", [])
        fecha_vencimiento = info.get("fecha_vencimiento", "Sin fecha")

        mensaje += f"{nombre_plat}: {cantidad} CUENTAS\n"
        for correo in correos:
            mensaje += f"{correo} - Vence: {fecha_vencimiento}\n"
        mensaje += "\n"

    await update.message.reply_text(mensaje)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("base", base))
    app.add_handler(CommandHandler("agregar", agregar))
    app.add_handler(CommandHandler("reemplazar", reemplazar))
    app.add_handler(CommandHandler("buscar", buscar))
    app.add_handler(CommandHandler("renovar", renovar))
    app.add_handler(CommandHandler("comandos", comandos))

    zona_horaria = pytz.timezone("America/Lima")
    job_queue = app.job_queue
    job_queue.run_daily(enviar_mensajes_vencidos, time=time(hour=7, minute=0, tzinfo=zona_horaria))

    print("Bot iniciado...")
    app.run_polling()

if __name__ == "__main__":
    main()
