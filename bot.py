import asyncio
import nest_asyncio
import json
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)
from datetime import datetime
import re

# --- Configuración ---
nest_asyncio.apply()

TOKEN = "7860727576:AAHvVucfSKJYOHwAS-wWfkHOLE1QqjGHTUQ"
ADMIN_ID = 5411037672
ADMIN_PASSWORD = "123456"

DATA_FILE = "data.json"

PERFILES_POR_PLATAFORMA = {
    "Netflix": 6,
    "Disney": 7,
    "Prime Video": 7,
    "Max": 5,
    "Crunchyroll": 20,
    "DGO": 5,
    "Liga 1 Max": 4,
    "IPTV": 4,
    "Paramount": 8,
    "Office": 5,
    "VIX": 7,
    "ChatGPT": 10,
    "Youtube": 3
}

admin_authorized = set()
cuentas = {}
datos_pago = {"banco": "ROSALI E. FLORES", "numero": "NUMERO_CORRESPONDIENTE"}

ASK_PASSWORD = 0

# --- Persistencia JSON ---
def guardar_datos():
    data = {
        "cuentas": cuentas,
        "datos_pago": datos_pago
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cargar_datos():
    global cuentas, datos_pago
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            cuentas = data.get("cuentas", {})
            datos_pago = data.get("datos_pago", {"banco": "ROSALI E. FLORES", "numero": "NUMERO_CORRESPONDIENTE"})

# --- Funciones auxiliares ---
def plataforma_valida(nombre):
    return nombre.capitalize() in PERFILES_POR_PLATAFORMA

def crear_estructura_perfiles(nombre_plataforma):
    n = PERFILES_POR_PLATAFORMA.get(nombre_plataforma.capitalize(), 5)
    return {int(i): {"cliente": None, "vence": None} for i in range(1, n+1)}

def formatear_cuenta(plataforma):
    p = cuentas.get(plataforma)
    if not p:
        return f"No existe la plataforma {plataforma}"
    texto = f"*{plataforma.capitalize()}*\nCorreo: {p['correo']}\nContraseña: {p['contraseña']}\n"
    for i in range(1, len(p["perfiles"]) + 1):
        perfil = p["perfiles"][str(i)] if isinstance(list(p["perfiles"].keys())[0], str) else p["perfiles"][i]
        if perfil["cliente"]:
            texto += f"Perfil {i} {perfil['cliente']}  ----  {perfil['vence']}\n"
        else:
            texto += f"Perfil {i}\n"
    return texto.strip()

def crear_link_whatsapp(numero):
    num = re.sub(r'\D', '', numero)
    return f"https://wa.me/{num}"

def perfiles_vendidos(plataforma, correo):
    p = cuentas.get(plataforma)
    if not p or p["correo"].lower() != correo.lower():
        return []
    vendidos = []
    for perfil_num, datos in p["perfiles"].items():
        if datos["cliente"]:
            vendidos.append((perfil_num, datos["cliente"], datos["vence"]))
    return vendidos

def asignar_perfil(plataforma, cliente_num, fecha_venc):
    p = cuentas.get(plataforma)
    if not p:
        return None
    for perfil_num, datos in p["perfiles"].items():
        if datos["cliente"] is None:
            p["perfiles"][perfil_num]["cliente"] = cliente_num
            p["perfiles"][perfil_num]["vence"] = fecha_venc
            guardar_datos()
            return perfil_num
    return None

def actualizar_fecha_vencimiento(plataforma, correo, cliente_num, nueva_fecha):
    p = cuentas.get(plataforma)
    if not p or p["correo"].lower() != correo.lower():
        return False
    for perfil_num, datos in p["perfiles"].items():
        if datos["cliente"] == cliente_num:
            p["perfiles"][perfil_num]["vence"] = nueva_fecha
            guardar_datos()
            return True
    return False

def eliminar_cuenta(plataforma, correo):
    p = cuentas.get(plataforma)
    if not p or p["correo"].lower() != correo.lower():
        return False
    del cuentas[plataforma]
    guardar_datos()
    return True

# --- Handlers ---

async def vip_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("Acceso denegado.")
        return ConversationHandler.END
    if user_id in admin_authorized:
        await update.message.reply_text("Ya estás autorizado.\nUsa /comandos para ver la lista.")
        return ConversationHandler.END
    await update.message.reply_text("ESCRIBE TU CONTRASEÑA ADMIN (6 dígitos):")
    return ASK_PASSWORD

async def vip_check_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    pwd = update.message.text.strip()
    if pwd == ADMIN_PASSWORD:
        admin_authorized.add(user_id)
        await update.message.reply_text(
            "✅ Acceso concedido.\n\nCOMANDOS DISPONIBLES:\n"
            "/comandos\n"
            "/agregarcc (correo) (contraseña) (plataforma)\n"
            "/comprar (plataforma) (numero_cliente) (fecha_vencimiento)\n"
            "/reemplazar (plataforma) (correo nuevo) (contraseña nuevo) (correo viejo)\n"
            "/renovar (numero_cliente) (plataforma) (correo) (fecha nueva)\n"
            "/pago (nombre banco) (numero telefono)\n"
            "/eliminarcc (plataforma) (correo)\n"
            "/info (numero_cliente) (plataforma - opcional)\n"
            "/asignar (numero_cliente) (plataforma) (correo) (contraseña)\n"
            "/base\n"
            "/avisomanual\n"
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Contraseña incorrecta. Usa /vip para intentar de nuevo.")
        return ConversationHandler.END

async def comandos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in admin_authorized:
        await update.message.reply_text("Acceso denegado. Usa /vip para ingresar.")
        return
    texto = (
        "Lista de comandos:\n"
        "/comandos\n"
        "/agregarcc (correo) (contraseña) (plataforma)\n"
        "/comprar (plataforma) (numero_cliente) (fecha_vencimiento)\n"
        "/reemplazar (plataforma) (correo nuevo) (contraseña nuevo) (correo viejo)\n"
        "/renovar (numero_cliente) (plataforma) (correo) (fecha nueva)\n"
        "/pago (nombre banco) (numero telefono)\n"
        "/eliminarcc (plataforma) (correo)\n"
        "/info (numero_cliente) (plataforma - opcional)\n"
        "/asignar (numero_cliente) (plataforma) (correo) (contraseña)\n"
        "/base\n"
        "/avisomanual\n"
    )
    await update.message.reply_text(texto)

async def agregarcc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in admin_authorized:
        await update.message.reply_text("Acceso denegado.")
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Uso: /agregarcc (correo) (contraseña) (plataforma)")
        return
    correo = args[0]
    contraseña = args[1]
    plataforma = " ".join(args[2:]).capitalize()

    if not plataforma_valida(plataforma):
        await update.message.reply_text(f"Plataforma inválida. Plataformas válidas: {', '.join(PERFILES_POR_PLATAFORMA.keys())}")
        return
    if plataforma in cuentas:
        await update.message.reply_text(f"La plataforma {plataforma} ya tiene una cuenta. Usa /reemplazar para actualizar.")
        return

    cuentas[plataforma] = {
        "correo": correo,
        "contraseña": contraseña,
        "perfiles": crear_estructura_perfiles(plataforma)
    }
    guardar_datos()

    await update.message.reply_text(f"Cuenta agregada:\n{formatear_cuenta(plataforma)}")

async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in admin_authorized:
        await update.message.reply_text("Acceso denegado.")
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Uso: /comprar (plataforma) (numero_cliente) (fecha_vencimiento)")
        return
    plataforma = " ".join(args[0:len(args)-2]).capitalize()
    numero_cliente = args[-2]
    fecha_vencimiento = args[-1]

    if plataforma not in cuentas:
        await update.message.reply_text(f"No existe la plataforma {plataforma}.")
        return

    perfil_asignado = asignar_perfil(plataforma, numero_cliente, fecha_vencimiento)
    if perfil_asignado is None:
        await update.message.reply_text(f"No hay perfiles disponibles en {plataforma}. Por favor agrega una nueva cuenta.")
        return

    c = cuentas[plataforma]
    texto = (
        f"*{plataforma}*\n"
        f"📬CORREO: {c['correo']}\n"
        f"🗝️CONTRASEÑA: {c['contraseña']}\n"
        f"📍PERFIL: {perfil_asignado}\n"
        f"📌TOCA RENOVAR: {fecha_vencimiento}"
    )
    await update.message.reply_markdown(texto)

    wa_link = crear_link_whatsapp(numero_cliente)
    await update.message.reply_text(f"Chat WhatsApp directo: {wa_link}")

async def reemplazar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in admin_authorized:
        await update.message.reply_text("Acceso denegado.")
        return
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("Uso: /reemplazar (plataforma) (correo nuevo) (contraseña nuevo) (correo viejo)")
        return
    plataforma = args[0].capitalize()
    correo_nuevo = args[1]
    contraseña_nueva = args[2]
    correo_viejo = args[3]

    if plataforma not in cuentas:
        await update.message.reply_text(f"No existe la plataforma {plataforma}.")
        return

    c = cuentas[plataforma]
    if c["correo"].lower() != correo_viejo.lower():
        await update.message.reply_text("El correo viejo no coincide con el registrado.")
        return

    perfiles_vendidos_lista = perfiles_vendidos(plataforma, correo_viejo)

    c["correo"] = correo_nuevo
    c["contraseña"] = contraseña_nueva
    guardar_datos()

    texto = f"*CONTRASEÑA ACTUALIZADA {plataforma}*\nCORREO: {correo_nuevo}\nCONTRASEÑA: {contraseña_nueva}\n"
    await update.message.reply_markdown(texto)

    for perfil_num, cliente_num, vence in perfiles_vendidos_lista:
        wa_link = crear_link_whatsapp(cliente_num)
        msg = (
            f"Perfil {perfil_num} - Cliente: {cliente_num}\n"
            f"Link WhatsApp: {wa_link}"
        )
        await update.message.reply_text(msg)

async def renovar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in admin_authorized:
        await update.message.reply_text("Acceso denegado.")
        return
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("Uso: /renovar (numero_cliente) (plataforma) (correo) (fecha nueva)")
        return
    numero_cliente = args[0]
    plataforma = args[1].capitalize()
    correo = args[2]
    fecha_nueva = args[3]

    if plataforma not in cuentas:
        await update.message.reply_text(f"No existe la plataforma {plataforma}.")
        return

    exito = actualizar_fecha_vencimiento(plataforma, correo, numero_cliente, fecha_nueva)
    if not exito:
        await update.message.reply_text("No se encontró el cliente con esos datos.")
        return

    texto = (
        "*RENOVACION EXITOSA, DATOS DE LA CUENTA*\n"
        f"{plataforma}\n{correo}\n"
        f"Chat WhatsApp: {crear_link_whatsapp(numero_cliente)}"
    )
    await update.message.reply_markdown(texto)

async def pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in admin_authorized:
        await update.message.reply_text("Acceso denegado.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Uso: /pago (nombre banco) (numero telefono)")
        return
    banco = args[0]
    numero = args[1]
    datos_pago["banco"] = banco
    datos_pago["numero"] = numero
    guardar_datos()
    await update.message.reply_text(f"Métodos de pago actualizados:\nBanco: {banco}\nNúmero: {numero}")

async def eliminarcc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in admin_authorized:
        await update.message.reply_text("Acceso denegado.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Uso: /eliminarcc (plataforma) (correo)")
        return
    plataforma = args[0].capitalize()
    correo = args[1]
    if plataforma not in cuentas:
        await update.message.reply_text(f"No existe la plataforma {plataforma}.")
        return

    c = cuentas[plataforma]
    if c["correo"].lower() != correo.lower():
        await update.message.reply_text("Correo no coincide.")
        return

    perfiles_vend = perfiles_vendidos(plataforma, correo)
    if perfiles_vend:
        await update.message.reply_text(f"La cuenta tiene perfiles vendidos. Se notificará a admin con links WhatsApp.")
        for perfil_num, cliente_num, vence in perfiles_vend:
            wa_link = crear_link_whatsapp(cliente_num)
            msg = (
                f"Perfil {perfil_num} - Cliente: {cliente_num}\n"
                f"Link WhatsApp: {wa_link}"
            )
            await update.message.reply_text(msg)

    eliminar_cuenta(plataforma, correo)
    await update.message.reply_text(f"Cuenta eliminada: {plataforma} - {correo}")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in admin_authorized:
        await update.message.reply_text("Acceso denegado.")
        return
    args = context.args
    if len(args) == 0:
        await update.message.reply_text("Uso: /info (numero_cliente) (plataforma - opcional)")
        return
    numero_cliente = args[0]
    plataforma = None
    if len(args) > 1:
        plataforma = " ".join(args[1:]).capitalize()

    resultados = []
    for plat, data in cuentas.items():
        if plataforma and plat != plataforma:
            continue
        for perfil_num, datos in data["perfiles"].items():
            if datos["cliente"] == numero_cliente:
                resultados.append(
                    f"Plataforma: {plat}\nCorreo: {data['correo']}\nContraseña: {data['contraseña']}\n"
                    f"Perfil: {perfil_num}\nVence: {datos['vence']}\n"
                )
    if resultados:
        await update.message.reply_text("\n".join(resultados))
    else:
        await update.message.reply_text("No se encontraron cuentas para ese cliente/plataforma.")

async def asignar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in admin_authorized:
        await update.message.reply_text("Acceso denegado.")
        return
    args = context.args
    if len(args) < 4:
        await update.message.reply_text("Uso: /asignar (numero_cliente) (plataforma) (correo) (contraseña)")
        return
    numero_cliente = args[0]
    plataforma = args[1].capitalize()
    correo = args[2]
    contraseña = args[3]

    if plataforma not in cuentas:
        await update.message.reply_text(f"No existe la plataforma {plataforma}.")
        return

    c = cuentas[plataforma]
    if c["correo"].lower() != correo.lower() or c["contraseña"] != contraseña:
        await update.message.reply_text("Correo o contraseña incorrectos para la plataforma.")
        return

    perfil_asignado = None
    for perfil_num, datos in c["perfiles"].items():
        if datos["cliente"] is None:
            c["perfiles"][perfil_num]["cliente"] = numero_cliente
            c["perfiles"][perfil_num]["vence"] = None
            perfil_asignado = perfil_num
            guardar_datos()
            break

    if perfil_asignado:
        await update.message.reply_text(f"Perfil {perfil_asignado} asignado a cliente {numero_cliente}.")
    else:
        await update.message.reply_text("No hay perfiles disponibles para asignar.")

# Comando /base corregido y mejorado
async def base(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in admin_authorized:
        await update.message.reply_text("Acceso denegado.")
        return

    texto = ""
    for plataforma, data in cuentas.items():
        perfiles = data["perfiles"]
        alquilado = any(perfil["cliente"] is not None for perfil in perfiles.values())
        estado = "Alquilado" if alquilado else "Disponible"

        texto += f"*{plataforma}* - Estado: {estado}\n"
        texto += f"Correo: {data['correo']}\nContraseña: {data['contraseña']}\n"
        for num_perfil, datos_perfil in sorted(perfiles.items(), key=lambda x: int(x[0])):
            cliente = datos_perfil["cliente"]
            vence = datos_perfil["vence"]
            if cliente:
                texto += f"Perfil {num_perfil}: {cliente}  ----  {vence}\n"
            else:
                texto += f"Perfil {num_perfil}: Disponible\n"
        texto += "\n"

    if texto == "":
        texto = "No hay cuentas registradas."

    await update.message.reply_markdown(texto)

# Comando /avisomanual para avisos manuales
async def avisomanual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID or user_id not in admin_authorized:
        await update.message.reply_text("Acceso denegado.")
        return

    hoy = datetime.now().date()
    mensajes = []
    for plataforma, data in cuentas.items():
        for perfil_num, perfil_data in data["perfiles"].items():
            if perfil_data["cliente"] and perfil_data["vence"]:
                try:
                    vence_date = datetime.strptime(perfil_data["vence"], "%d/%m/%y").date()
                except:
                    continue
                if vence_date <= hoy:
                    texto = (
                        f"PLATAFORMA: {plataforma}\n"
                        f"CLIENTE: {perfil_data['cliente']}\n"
                        f"CUENTA: {data['correo']} -- {data['contraseña']}\n"
                        "AVISO MANUAL: Plataforma vencida.\n"
                        f"Chat WhatsApp: {crear_link_whatsapp(perfil_data['cliente'])}"
                    )
                    mensajes.append(texto)
    if mensajes:
        for msg in mensajes:
            await update.message.reply_text(msg)
    else:
        await update.message.reply_text("No hay cuentas vencidas para hoy.")

# Tarea diaria: avisos matutinos y vespertinos
async def tarea_diaria(application):
    while True:
        ahora = datetime.now()
        hoy = ahora.date()

        if ahora.hour == 9 and ahora.minute == 0:
            for plataforma, data in cuentas.items():
                for perfil_num, perfil_data in data["perfiles"].items():
                    if perfil_data["cliente"] and perfil_data["vence"]:
                        try:
                            vence_date = datetime.strptime(perfil_data["vence"], "%d/%m/%y").date()
                        except:
                            continue
                        if vence_date <= hoy:
                            texto = (
                                f"PLATAFORMA: {plataforma}\n"
                                f"CLIENTE: {perfil_data['cliente']}\n"
                                f"CUENTA: {data['correo']} -- {data['contraseña']}\n"
                                "BUEN DIA, TU PLATAFORMA DE "
                                f"{plataforma.upper()} ACABA DE EXPIRAR CONFIRMAR RENOVACION PARA EVITAR CORTES Y MOLESTIAS.\n"
                                "MÉTODOS DE PAGO\n"
                                f"🟣 {datos_pago['banco']} - {datos_pago['numero']}\n"
                                "NO COLOCAR NADA EN LA DESCRIPCIÓN DEL PAGO NO LEEMOS ESA INFORMACIÓN\n"
                                "*IMPORTANTE ENVIAR COMPROBANTE DE PAGO PARA REALIZAR LA RENOVACION*\n"
                                "CORTE DE LA PLATAFORMA: 7:00 PM.\n"
                                f"Chat WhatsApp: {crear_link_whatsapp(perfil_data['cliente'])}"
                            )
                            await application.bot.send_message(chat_id=ADMIN_ID, text=texto)

        if ahora.hour == 18 and ahora.minute == 0:
            for plataforma, data in cuentas.items():
                for perfil_num, perfil_data in data["perfiles"].items():
                    if perfil_data["cliente"] and perfil_data["vence"]:
                        try:
                            vence_date = datetime.strptime(perfil_data["vence"], "%d/%m/%y").date()
                        except:
                            continue
                        if vence_date < hoy:
                            texto = (
                                f"PLATAFORMA: {plataforma}\n"
                                f"CLIENTE: {perfil_data['cliente']}\n"
                                f"CUENTA: {data['correo']} -- {data['contraseña']}\n"
                                "El perfil está vencido y no fue renovado durante el día.\n"
                                "El perfil será liberado para venta.\n"
                                f"Chat WhatsApp: {crear_link_whatsapp(perfil_data['cliente'])}"
                            )
                            await application.bot.send_message(chat_id=ADMIN_ID, text=texto)
                            data["perfiles"][perfil_num]["cliente"] = None
                            data["perfiles"][perfil_num]["vence"] = None
                            guardar_datos()

        await asyncio.sleep(60)  # Checkea cada minuto

# --- Main ---

async def main():
    cargar_datos()
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("vip", vip_start)],
        states={ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, vip_check_password)]},
        fallbacks=[]
    )
    application.add_handler(conv_handler)

    application.add_handler(CommandHandler("comandos", comandos_handler))
    application.add_handler(CommandHandler("agregarcc", agregarcc))
    application.add_handler(CommandHandler("comprar", comprar))
    application.add_handler(CommandHandler("reemplazar", reemplazar))
    application.add_handler(CommandHandler("renovar", renovar))
    application.add_handler(CommandHandler("pago", pago))
    application.add_handler(CommandHandler("eliminarcc", eliminarcc))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("asignar", asignar))
    application.add_handler(CommandHandler("base", base))
    application.add_handler(CommandHandler("avisomanual", avisomanual))

    print("Bot iniciado")
    application.create_task(tarea_diaria(application))

    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "event loop is running" in str(e):
            asyncio.get_event_loop().run_until_complete(main())
        else:
            raise
