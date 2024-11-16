import os
import discord
import asyncio
from discord.ext import commands
from discord.ui import Modal, TextInput

intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

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

# Evento di avvio del bot
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizzati {len(synced)} comandi.")
    except Exception as e:
        print(f"Errore di sincronizzazione dei comandi: {e}")

    print(f"{bot.user} è online e pronto a ricevere comandi.")

# Avvio del bot server
bot.run(os.getenv("TOKEN"))
