import os
import discord
import asyncio
import datetime
import signal
from discord.ext import commands
from discord.ui import Modal, TextInput
from discord import FFmpegPCMAudio

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Variabile globale per tracciare lo stato del meccanismo
assemblea_attiva = False

# Crea il Modale per raccogliere le informazioni
class NicknameModal(Modal, title="Imposta il tuo Nickname"):
    nome = TextInput(label="Nome", placeholder="Inserisci il tuo nome", required=True)
    cognome = TextInput(label="Cognome", placeholder="Inserisci il tuo cognome", required=True)
    classe = TextInput(label="Classe", placeholder="Es. 1", required=True, max_length=1)
    sezione = TextInput(label="Sezione", placeholder="Es. A", required=True, max_length=1)
    specializzazione = TextInput(label="Specializzazione", placeholder="Es. INF", required=True, max_length=3)

    async def on_submit(self, interaction: discord.Interaction):
        # Componi il nickname con i dati inseriti
        role = 'everyone'
        # Funzione per formattare il nickname
        def format_input(field, value):
            if field in ["nome", "cognome"]:
                return value.capitalize()
            elif field in ["classe", "sezione", "specializzazione"]:
                return value.upper()
            return value

        # Applica la formattazione agli input
        nome_formattato = format_input("nome", self.nome.value)
        cognome_formattato = format_input("cognome", self.cognome.value)
        classe_formattata = format_input("classe", self.classe.value)
        sezione_formattata = format_input("sezione", self.sezione.value)
        specializzazione_formattata = format_input("specializzazione", self.specializzazione.value)

        # Componi il nickname con i dati formattati
        nickname = f"{nome_formattato} {cognome_formattato} {classe_formattata}{sezione_formattata}{specializzazione_formattata}"

        try:
            # Cambia il nickname dell'utente
            await interaction.user.edit(nick=nickname)
            await interaction.user.add_roles(discord.utils.get(interaction.user.guild.roles, name=role))
            destination_channel = discord.utils.get(interaction.guild.text_channels, name="registro-presenze")
            if destination_channel:
                await interaction.response.send_message(
                    f"Il tuo nickname è stato aggiornato. Clicca qui per continuare: {destination_channel.mention}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    "Il tuo nickname è stato aggiornato, ma il canale 'registro-presenze' non è stato trovato.",
                    ephemeral=True
                )

        except discord.Forbidden:
            await interaction.response.send_message("Non ho permessi per cambiare il tuo nickname.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

# Definisce il comando come slash command
@bot.tree.command(name="nickname", description="Imposta il tuo nickname con nome, cognome, classe, sezione e specializzazione")
async def nickname_command(interaction: discord.Interaction):
    await interaction.response.send_modal(NicknameModal())

class NicknameButton(discord.ui.View):
    def __init__(self, message=None):
        super().__init__()
        self.message = message  # Salva il riferimento al messaggio

    @discord.ui.button(label="Imposta il tuo nickname", style=discord.ButtonStyle.primary)
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Apre il modal quando l'utente clicca sul pulsante
        await interaction.response.send_modal(NicknameModal())

        # Elimina il messaggio con il bottone
        if self.message:
            await self.message.delete()

# Funzione per controllare i ruoli richiesti
def has_required_role(member):
    required_roles = ["Rappresentante di Istituto", "Admin del Server"]
    return any(role.name in required_roles for role in member.roles)

# Comando per abilitare il meccanismo
@bot.tree.command(name="assemblea_avvia", description="Abilita lo spostamento automatico degli utenti per l'assemblea.")
async def assemblea_avvia(interaction: discord.Interaction):
    global assemblea_attiva

    # Controlla se l'utente ha i ruoli necessari
    if not has_required_role(interaction.user):
        await interaction.response.send_message(
            "Non hai i permessi per eseguire questo comando.", ephemeral=True
        )
        return

    assemblea_attiva = True
    await interaction.response.send_message(
        "Il meccanismo di spostamento automatico è stato **attivato**. Gli utenti in lista d'attesa saranno distribuiti nei canali disponibili.",
        ephemeral=True
    )

    # ID dei canali di interesse
    source_channel_id = 1308155167304060948
    destination_channels = [
        1312866730724560906,
        1312866755676471296,
        1312866787628417115,
        1312866807203495967
    ]
    log_channel_id = 1312930597093511198

    guild = interaction.guild
    source_channel = discord.utils.get(guild.voice_channels, id=source_channel_id)
    log_channel = discord.utils.get(guild.text_channels, id=log_channel_id)

    if source_channel:
        for member in source_channel.members:
            # Trova un canale disponibile con meno di 20 membri
            destination_channel = None
            for channel_id in destination_channels:
                channel = discord.utils.get(guild.voice_channels, id=channel_id)
                if channel and len(channel.members) < 20:
                    destination_channel = channel
                    break

            if destination_channel:
                try:
                    # Sposta l'utente nel canale disponibile
                    await member.move_to(destination_channel)
                    # Log dell'operazione
                    if log_channel:
                        await log_channel.send(
                            f"**{member.display_name}** è stato spostato da {source_channel.name} a {destination_channel.name}."
                        )
                except discord.Forbidden:
                    if log_channel:
                        await log_channel.send(
                            f"Permessi insufficienti per spostare {member.display_name}."
                        )
                except Exception as e:
                    if log_channel:
                        await log_channel.send(
                            f"Errore nel tentativo di spostare {member.display_name}: {e}"
                        )
            else:
                # Log in caso di nessun canale disponibile
                if log_channel:
                    await log_channel.send(
                        f"**{member.display_name}** non è stato spostato perché tutti i canali di destinazione sono pieni."
                    )

# Comando per disabilitare il meccanismo
@bot.tree.command(name="assemblea_ferma", description="Disabilita lo spostamento automatico degli utenti per l'assemblea.")
async def assemblea_ferma(interaction: discord.Interaction):
    global assemblea_attiva

    # Controlla se l'utente ha i ruoli necessari
    if not has_required_role(interaction.user):
        await interaction.response.send_message(
            "Non hai i permessi per eseguire questo comando.", ephemeral=True
        )
        return

    assemblea_attiva = False
    await interaction.response.send_message(
        "Il meccanismo di spostamento automatico è stato **disattivato**.", ephemeral=True
    )
    
# Comando per espellere tutti e disabilitare il meccanismo
@bot.tree.command(name="assemblea_kick", description="Kicka utenti dai canali vocali esclusi gli Admin del Server e i Rappresentanti di Istituto. Disattiva il meccanismo di spostamento automatico.")
async def assemblea_kick(interaction: discord.Interaction):
    global assemblea_attiva
    # ID dei canali vocali da cui rimuovere gli utenti
    voice_channel_ids = [
        1312866730724560906,
        1312871355871658174,
        1312871383898001438,
        1312871407235104768
    ]

    # Controlla i ruoli richiesti
    required_roles = ["Rappresentante di Istituto", "Admin del Server"]

    if not has_required_role(interaction.user):
        await interaction.response.send_message("Non hai i permessi per eseguire questo comando.", ephemeral=True)
        return

    assemblea_attiva = False
    guild = interaction.guild
    kicked_members = []

    for channel_id in voice_channel_ids:
        channel = discord.utils.get(guild.voice_channels, id=channel_id)
        if not channel:
            continue

        for member in channel.members:
            # Controlla se il membro ha i ruoli richiesti
            if not any(role.name in required_roles for role in member.roles):
                try:
                    await member.move_to(None)  # Kicka dal canale vocale
                    kicked_members.append(member.display_name)
                except Exception as e:
                    print(f"Errore nel kick di {member.display_name}: {e}")

    if kicked_members:
        await interaction.response.send_message(
            f"Sono stati rimossi dai canali vocali:\n{', '.join(kicked_members)}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message("Nessun utente rimosso dai canali vocali.", ephemeral=True)

# Comando per esportare la chat dell'assemblea
@bot.tree.command(name="esporta_chat", description="Esporta i messaggi di oggi dal canale specifico.")
async def esporta_chat(interaction: discord.Interaction):
    channel_id = 1306336623105146961  # Canale da cui esportare i messaggi
    log_channel_id = 1312930597093511198  # Canale in cui inviare il file
    source_channel = discord.utils.get(interaction.guild.text_channels, id=channel_id)
    log_channel = discord.utils.get(interaction.guild.text_channels, id=log_channel_id)

    if not source_channel:
        await interaction.response.send_message("Canale da esportare non trovato.", ephemeral=True)
        return

    if not log_channel:
        await interaction.response.send_message("Canale di log non trovato.", ephemeral=True)
        return

    today = datetime.datetime.utcnow().date()
    messages_today = []

    async for message in source_channel.history(limit=None):
        if message.created_at.date() == today:
            messages_today.append(f"[{message.created_at}] {message.author.display_name}: {message.content}")

    if not messages_today:
        await interaction.response.send_message("Nessun messaggio trovato per oggi.", ephemeral=True)
        return

    # Percorso del file con il nome contenente la data
    file_path = os.path.join(os.path.dirname(__file__), "chat_" + today.strftime("%Y-%m-%d") + ".txt")

    try:
        # Rimuovi il file se esiste già
        if os.path.exists(file_path):
            os.remove(file_path)

        # Scrivi i messaggi in un nuovo file
        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(messages_today))

    except Exception as e:
        await interaction.response.send_message(
            f"Errore durante il salvataggio del file: {e}", ephemeral=True
        )
        return

    # Invia il file al canale di log
    try:
        await log_channel.send(
            content=f"Esportazione dei messaggi di oggi dal canale <#{channel_id}>:",
            file=discord.File(file_path)
        )
        await interaction.response.send_message("File esportato e inviato nel canale di log.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(
            f"Errore durante l'invio del file al canale di log: {e}", ephemeral=True
        )

# Evento per il meccanismo di spostamento
@bot.event
async def on_voice_state_update(member, before, after):
    global assemblea_attiva

    # Controlla se il meccanismo è attivo
    if not assemblea_attiva:
        return
    
    # ID dei canali di interesse
    source_channel_id = 1308155167304060948
    destination_channels = [
        1312866730724560906,
        1312871355871658174,
        1312871383898001438,
        1312871407235104768
    ]
    log_channel_id = 1305928677841702925

    # Controlla se l'utente si è connesso al canale specifico
    if after.channel and after.channel.id == source_channel_id:
        guild = member.guild
        log_channel = discord.utils.get(guild.text_channels, id=log_channel_id)

        # Trova un canale disponibile con meno di 20 membri
        destination_channel = None
        for channel_id in destination_channels:
            channel = discord.utils.get(guild.voice_channels, id=channel_id)
            if channel and len(channel.members) < 20:
                destination_channel = channel
                break

        if destination_channel:
            try:
                # Sposta l'utente nel canale disponibile
                await member.move_to(destination_channel)
                # Log dell'operazione
                if log_channel:
                    # await log_channel.send(
                    #     f"**{member.display_name}** è entrato in Assemblea (Spostato in {destination_channel.name})"
                    # )
                    #print(f"{member.display_name} è entrato in Assemblea (Spostato in {destination_channel.name})")
                    pass
            except discord.Forbidden:
                if log_channel:
                    # await log_channel.send(
                    #     f"Permessi insufficienti per spostare {member.display_name}."
                    # )
                    print(f"Permessi insufficienti per spostare {member.display_name}.")
            except Exception as e:
                if log_channel:
                    # await log_channel.send(
                    #     f"Errore nel tentativo di spostare {member.display_name}: {e}"
                    # )
                    print(f"Errore nel tentativo di spostare {member.display_name}: {e}")
        else:
            # Log in caso di nessun canale disponibile
            if log_channel:
                await log_channel.send(
                    f"**{member.display_name}** non è stato spostato perché tutti i canali di destinazione sono pieni."
                )

@bot.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name="nickname")
    if welcome_channel:
        # Invia il messaggio con il bottone
        message = await welcome_channel.send(
            f"Benvenuto {member.mention}! **PER ENTRARE DENTRO IL SERVER E ACCEDERE ANCHE AI CANALI DELL'ASSEMBLEA** clicca sul pulsante qui sotto per impostare il tuo nickname:",
            view=NicknameButton(message=None)  # Placeholder per il messaggio
        )
        # Aggiungi il riferimento al messaggio nella view
        view = NicknameButton(message=message)
        await message.edit(view=view)

        # Avvia il controllo per kickare l'utente dopo 15 minuti se necessario
        await kick_if_not_identified(member, message)

async def kick_if_not_identified(member, message):
    # Aspetta 15 minuti
    await asyncio.sleep(15 * 60)  # 15 minuti in secondi

    # Controlla se il membro ha il ruolo 'everyone'
    role = discord.utils.get(member.guild.roles, name="everyone")
    if role not in member.roles:
        try:
            # Invia un messaggio privato all'utente
            try:
                # Primo messaggio: motivo del kick
                await member.send(
                    "Quando entri nel server **ITI G.M. Angioy**, è necessario identificarsi impostando il proprio nickname. "
                    "Non avendo completato questa procedura entro il tempo limite, sei stato rimosso dal server."
                )
                # Secondo messaggio: link per rientrare nel server
                await member.send(
                    "Puoi riprovare a entrare utilizzando il seguente link d'invito:\n"
                    "[Invito al server](https://discord.gg/uvE3T7BYY2)"
                )
            except discord.Forbidden:
                pass  # L'utente potrebbe avere i DM disabilitati

            # Kicka l'utente
            await member.kick(reason="Nickname non impostato entro il tempo limite")

            # Elimina il messaggio con il bottone
            if message:
                await message.delete()

        except Exception as e:
            print(f"Errore nel kick di {member}: {e}")
            
# Comando per riprodurre un file audio da un link diretto
@bot.tree.command(name="play_audio", description="Riproduci un file audio da un link diretto (.mp3)")
async def play_audio(interaction: discord.Interaction, url: str):
    # Verifica se l'utente ha i permessi necessari
    if not has_required_role(interaction.user):
        await interaction.response.send_message(
            "Non hai i permessi per eseguire questo comando.", ephemeral=True
        )
        return

    # ID del canale vocale
    channel_id = 1308155167304060948
    guild = interaction.guild
    channel = discord.utils.get(guild.voice_channels, id=channel_id)

    if channel:
        try:
            # Unisciti al canale vocale
            voice_client = await channel.connect()
            await interaction.response.send_message(
                f"Il bot è entrato nel canale {channel.name}. Avvio della riproduzione..."
            )

            # Usa FFmpegPCMAudio per riprodurre l'audio dal link diretto
            audio_source = FFmpegPCMAudio(url)
            voice_client.play(audio_source, after=lambda e: print("Riproduzione terminata.", e))

        except discord.Forbidden:
            await interaction.response.send_message(
                "Non ho permessi per unirmi a questo canale.", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"Errore durante la riproduzione: {e}", ephemeral=True
            )
    else:
        await interaction.response.send_message("Canale vocale non trovato.", ephemeral=True)

# Evento di avvio del bot
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizzati {len(synced)} comandi.")
    except Exception as e:
        print(f"Errore di sincronizzazione dei comandi: {e}")

    print(f"{bot.user} è online e pronto a ricevere comandi.")

    # ID del canale in cui inviare il messaggio
    log_channel_id = 1312930597093511198

    # Invia il messaggio di avvio
    guild = discord.utils.get(bot.guilds)  # Prendi il primo server dove il bot è connesso
    if guild:
        log_channel = discord.utils.get(guild.text_channels, id=log_channel_id)
        if log_channel:
            try:
                await log_channel.send(f"{bot.user.name} online - Deploy completato su Railway")
            except discord.Forbidden:
                print("Permesso negato per inviare messaggi nel canale specificato.")
            except Exception as e:
                print(f"Errore durante l'invio del messaggio di avvio: {e}")

# Evento shutdown
async def send_shutdown_message():
    try:
        log_channel_id = 1312930597093511198

        guild = discord.utils.get(bot.guilds)
        if not guild:
            print("Server non trovato. Impossibile inviare il messaggio di spegnimento.")
            return

        channel = discord.utils.get(guild.text_channels, id=log_channel_id)
        if channel:
            await channel.send(f"{bot.user.name} offline - Deployment su Railway... (trigger da nuovo push)")
        else:
            print("Canale non trovato. Impossibile inviare il messaggio di spegnimento.")
    except Exception as e:
        print(f"Errore durante l'invio del messaggio di spegnimento: {e}")

def shutdown_handler(signum, frame):
    loop = asyncio.get_event_loop()
    loop.create_task(send_shutdown_message())
    loop.create_task(bot.close())  # Chiude il bot

# Registra il signal handler per SIGINT e SIGTERM
signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

bot.run(os.getenv("TOKEN"))