import discord
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
        nickname = f"{self.nome.value} {self.cognome.value} {self.classe.value}{self.sezione.value}{self.specializzazione.value}"
        try:
            # Cambia il nickname dell'utente
            await interaction.user.edit(nick=nickname)
            await interaction.user.add_roles(discord.utils.get(interaction.user.guild.roles, name=role))
            destination_channel = discord.utils.get(interaction.guild.text_channels, name="registro-presenze")
            await interaction.response.send_message(f"Il tuo nickname è stato aggiornato. Clicca qui per continuare: {destination_channel.mention}", ephemeral=True)
                
        except discord.Forbidden:
            await interaction.response.send_message("Non ho permessi per cambiare il tuo nickname.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Errore: {e}", ephemeral=True)

# Definisce il comando come slash command
@bot.tree.command(name="nickname", description="Imposta il tuo nickname con nome, cognome, classe, sezione e specializzazione")
async def nickname_command(interaction: discord.Interaction):
    await interaction.response.send_modal(NicknameModal())

class NicknameButton(discord.ui.View):
    @discord.ui.button(label="Imposta il tuo nickname", style=discord.ButtonStyle.primary)
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Apre il modal quando l'utente clicca sul pulsante
        await interaction.response.send_modal(NicknameModal())
           
@bot.event
async def on_member_join(member):
    welcome_channel = discord.utils.get(member.guild.text_channels, name="nickname")
    if welcome_channel:
        await welcome_channel.send(
            f"Benvenuti {member.mention}! **PER ENTRARE DENTRO IL SERVER E ACCEDERE ANCHE AI CANALI DELL'ASSEMBLEA** clicca sul pulsante qui sotto per impostare il tuo nickname:",
            view=NicknameButton()
        )

# Evento di avvio del bot
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizzati {len(synced)} comandi.")
    except Exception as e:
        print(f"Errore di sincronizzazione dei comandi: {e}")

    print(f"{bot.user} è online e pronto a ricevere comandi.")

# Avvio del bot
bot.run('')