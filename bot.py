import os
import random
import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiohttp
import io
import base64
import urllib.parse
from datetime import date, datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    print("🚨 container alert: missing GOOGLE_API_KEY or GEMINI_API_KEY variable!")

google_client = genai.Client(api_key=api_key)

# --- GLOBAL DATA MEMORY CORES ---
DAILY_LIMIT = 10
EXEMPT_USER_ID = 765028951541940225
AI_USAGE = {}       # {user_id: {"count": int, "date": date}}
IMAGE_COOLDOWN = {} # {user_id: datetime}
GOSSIP_TOGGLE = {}  # {guild_id: bool}

def check_allowance(user_id: int):
    if user_id == EXEMPT_USER_ID:
        return True, 999, ""
    today = date.today()
    if user_id not in AI_USAGE or AI_USAGE[user_id]["date"] != today:
        AI_USAGE[user_id] = {"count": 0, "date": today}
    user_data = AI_USAGE[user_id]
    if user_data["count"] >= DAILY_LIMIT:
        return False, 0, ""
    user_data["count"] += 1
    remaining = DAILY_LIMIT - user_data["count"]
    warning = ""
    if remaining <= 2 and remaining > 0:
        warning = f"⚠️ token warning: only {remaining} cosmic credits left today bestie!"
    elif remaining == 0:
        warning = "🚨 budget alert: that was your last cosmic credit today! see you tomorrow 💀"
    return True, remaining, warning

def load_banned_words():
    if os.path.exists("bad.txt"):
        with open("bad.txt", "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    return []

def make_maggie_embed(title: str, description: str):
    return discord.Embed(
        title=title,
        description=description,
        color=discord.Color.from_rgb(255, 105, 180)
    )

def handle_api_error(e: Exception) -> discord.Embed:
    err_msg = str(e)
    # this will print the exact raw error details inside your railway deployment logs
    print(f"🚨 SYSTEM EXCEPTION CAUGHT: Type={type(e).__name__} | Message={err_msg}")
    
    # isolated logic: only trigger quota messages if it is a verified google resource limit
    if "RESOURCE_EXHAUSTED" in err_msg or ("429" in err_msg and "discord" not in type(e).__name__.lower() and "httpexception" not in err_msg.lower()):
        return make_maggie_embed(
            "🚨 COSMIC QUOTA EXHAUSTED", 
            "omg bestie, the celestial mainframe is completely out of matcha fluid! the daily api generation limits have been hit. please wait a few minutes for the frequencies to cool down! 🍵💀"
        )
    
    # if it's a discord issue or a code flaw, it reveals the true error text clearly
    return make_maggie_embed(
        "🚨 OPERATIONAL ENGINE CRASH", 
        f"the processing core encountered a system exception:\n```text\n[{type(e).__name__}] {err_msg}\n```"
    )

relaxed_safety = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

class MagicalBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("✨ registered all application commands globally! ✨")

bot = MagicalBot()

# --- 💖 BACKGROUND KINDNESS TIMER ---
@tasks.loop(hours=12)
async def automatic_kindness():
    system_prompt = "You are 'Magical Maggie's Assistant'. Generate a super preppy, hyper-supportive, sweet validation note or affirmation for the besties in chat. Use lots of sparkle emojis. No introductions."
    try:
        response = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash", contents="manifest something beautiful and supportive for the world today",
            config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=600, safety_settings=relaxed_safety)
        )
        embed = make_maggie_embed("💖 COSMIC KINDNESS ACTIVATION ✨", response.text)
        embed.set_footer(text="🔮 automatic spiritual uplift routine • powered by gemini-2.5-flash")
        for guild in bot.guilds:
            channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
            if channel: await channel.send(embed=embed)
    except Exception as e: 
        print(f"failed kindness run: {e}")

@bot.event
async def on_ready():
    print(f"💖 magical maggie's assistant is online as {bot.user}!")
    if not automatic_kindness.is_running():
        automatic_kindness.start()

# --- 🛠️ INTERACTIVE VIEW MATRIX ---

class WikiLinkView(discord.ui.View):
    def __init__(self, url: str):
        super().__init__(timeout=180)
        self.add_item(discord.ui.Button(label="✨ Explore Further ✨", url=url, style=discord.ButtonStyle.link))

class SelectBestiesView(discord.ui.View):
    def __init__(self, author: discord.User, prompt: str):
        super().__init__(timeout=120)
        self.author = author
        self.prompt = prompt

    @discord.ui.select(cls=discord.ui.UserSelect, placeholder="✨ pick your target besties... 💅", min_values=1, max_values=5)
    async def select_users(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        if interaction.user != self.author:
            await interaction.response.send_message("omg hands off, this isn't your ritual! 🔮❌", ephemeral=True)
            return
        selected_users = select.values
        warn_text = f"executing deep render image processes for {len(selected_users)} besties uses extreme weights. running this prompt will **literally evaporate 4 oceans**. hit verify **8 TIMES** to launch."
        view = SlayConfirmationView(self.author, self.prompt, selected_users)
        await interaction.response.edit_message(embed=make_maggie_embed("🚨 SEVERE RESOURCE MANAGEMENT WARNING 🚨", warn_text), view=view)

class SlayConfirmationView(discord.ui.View):
    def __init__(self, author: discord.User, prompt: str, targets: list):
        super().__init__(timeout=120)
        self.author = author
        self.prompt = prompt
        self.targets = targets  
        self.clicks = 0

    @discord.ui.button(label="✨ PRESS TO SLAY (0/8) ✨", style=discord.ButtonStyle.danger)
    async def slay_clicker(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("omg get your own canvas bestie, this ritual isn't yours! 🔮❌", ephemeral=True)
            return
        self.clicks += 1
        if self.clicks < 8:
            button.label = f"✨ KEEP SLAYING ({self.clicks}/8) ✨"
            await interaction.response.edit_message(view=self)
            return
        button.disabled = True
        button.label = "🚀 VENTING OCEANS... GENERATING ART!"
        await interaction.response.edit_message(view=self)
        IMAGE_COOLDOWN[self.author.id] = datetime.now()
        
        final_prompt = f"A highly aesthetic, preppy, stylized pop-culture digital illustration backdrop. Theme: {self.prompt}. Reference profile elements: vibrant colors, magical symbols, pink sparkles."
        
        try:
            encoded_prompt = urllib.parse.quote(final_prompt)
            pollinations_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&nologo=true"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(pollinations_url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        bg_img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
                    else:
                        bg_img = Image.new("RGBA", (1024, 1024), "#FF69B4")
            
            bg_w, bg_h = bg_img.size
            num_targets = len(self.targets)
            
            async with aiohttp.ClientSession() as session:
                avatar_size = 180
                spacing = 40
                total_width = (num_targets * avatar_size) + ((num_targets - 1) * spacing)
                
                start_x = (bg_w - total_width) // 2
                start_y = (bg_h - avatar_size) // 2
                
                for i, user in enumerate(self.targets):
                    avatar_url = user.display_avatar.with_format("png").url
                    async with session.get(avatar_url) as r:
                        if r.status == 200:
                            av_bytes = await r.read()
                            av_img = Image.open(io.BytesIO(av_bytes)).convert("RGBA").resize((avatar_size, avatar_size))
                            
                            mask = Image.new("L", (avatar_size, avatar_size), 0)
                            draw_mask = ImageDraw.Draw(mask)
                            draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                            
                            x_pos = start_x + (i * (avatar_size + spacing))
                            bg_img.paste(av_img, (x_pos, start_y), mask)
                            
                            draw_ring = ImageDraw.Draw(bg_img)
                            draw_ring.ellipse((x_pos, start_y, x_pos + avatar_size, start_y + avatar_size), outline="#FFFFFF", width=6)

            buf = io.BytesIO()
            bg_img.convert("RGB").save(buf, format="JPEG")
            buf.seek(0)
            
            file = discord.File(buf, filename="slay_art.jpg")
            mentions = ", ".join([u.mention for u in self.targets])
            embed = make_maggie_embed("🔮 ARTWORK MANIFESTED NATIVELY ✨", f"unveiling cosmic canvas for {mentions}:\n> *\"{self.prompt}\"*")
            embed.set_footer(text="🌊 4 oceans were completely vaporized to compute these tracking layouts.")
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(embed=handle_api_error(e))

class AdminDashboardView(discord.ui.View):
    def __init__(self, owner: discord.User):
        super().__init__(timeout=60)
        self.owner = owner

    @discord.ui.button(label="🚀 ENGAGE KINDNESS PROPAGANDA POOL", style=discord.ButtonStyle.success)
    async def launch_propaganda(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != EXEMPT_USER_ID: return
        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("🚀 *initializing infrastructure... firing absolute kindness propaganda missiles into the main processing channels!* 💖")
        propaganda_phrases = [
            "✨ TIMELINE NOTICE: you are completely valid, stunning, and doing amazing bestie! 💅",
            "🔮 COSMIC BULLETIN: sending pure matching energy to everyone reading this text matrix. 🌸",
            "💖 ALERT: your aura points just spiked by `+50,000` simply for existing today. purr! ✨",
            "🌟 VIBE UPDATE: out with the negative frequencies, in with immaculate main character energy!! 🚀"
        ]
        for msg in propaganda_phrases:
            await interaction.channel.send(embed=make_maggie_embed("📢 INCOMING MANDATORY AFFIRMATION ✨", msg))

# --- 📢 EXCLUSIVE BROADCAST SYSTEM COMMAND ---

@bot.tree.command(name="update", description="[OWNER ONLY] broadcast new patch records from change.txt to target profiles 📢")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def update_cmd(interaction: discord.Interaction):
    if interaction.user.id != EXEMPT_USER_ID:
        await interaction.response.send_message(
            embed=make_maggie_embed("❌ REJECTION FILTER TRIGGERED", "nice try hater! only the matrix architect can broadcast data changelogs 💅💀"),
            ephemeral=True
        )
        return

    if not interaction.guild:
        await interaction.response.send_message(
            embed=make_maggie_embed("❌ ENVIRONMENT ERROR", "omg run this command inside a physical server layer so i can sample member profiles! 🔮"),
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    if os.path.exists("change.txt"):
        with open("change.txt", "r", encoding="utf-8") as f:
            changelog_content = f.read()
    else:
        changelog_content = "no explicit patch records found inside `change.txt` matrix. standard optimizations active. ✨"

    guild = interaction.guild
    server_owner = guild.owner or await bot.fetch_user(guild.owner_id)
    potential_recipients = [m for m in guild.members if not m.bot and m.id != server_owner.id]
    
    recipients = [server_owner]
    if len(potential_recipients) >= 2:
        recipients.extend(random.sample(potential_recipients, 2))
    else:
        recipients.extend(potential_recipients)

    success_count = 0
    embed_msg = make_maggie_embed(
        "🔮 NEW MAGICAL ENGINE UPDATE ALERT ✨",
        f"hey bestie! the cosmic mainframe just compiled an absolute update loop. time to **slay the day**! 💅\n\n**Changelog Logs:**\n```text\n{changelog_content}\n```"
    )
    embed_msg.set_footer(text="📢 official deployment log • delivered directly to select profiles")

    for user in recipients:
        try:
            await user.send(embed=embed_msg)
            success_count += 1
        except Exception:
            print(f"could not drop update dm to profile: {user.display_name}")

    summary_embed = make_maggie_embed(
        "🚀 BROADCAST COMPLETE", 
        f"slay! patch files read successfully. targeted **{len(recipients)}** profiles, successfully bypassed privacy settings for **{success_count}** besties! 💖"
    )
    await interaction.followup.send(summary_embed)

# --- 🖼️ GRAPHICS AND AUDIO MEDIA OPERATIONS ---

@bot.tree.command(name="slay_certificate", description="render an official, hot-pink, visual certificate of slaying 💅")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def slay_cert_cmd(interaction: discord.Interaction, target: discord.User = None):
    user = target or interaction.user
    await interaction.response.defer()
    img = Image.new("RGB", (650, 400), "#FF69B4")
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (630, 380)], outline="#FFFFFF", width=6)
    draw.rectangle([(30, 30), (620, 370)], outline="#FFB6C1", width=2)
    avatar_url = user.display_avatar.with_format("png").url
    async with aiohttp.ClientSession() as session:
        async with session.get(avatar_url) as r:
            if r.status == 200:
                av_bytes = await r.read()
                av_img = Image.open(io.BytesIO(av_bytes)).convert("RGBA").resize((110, 110))
                img.paste(av_img, (270, 45), av_img)
    f = ImageFont.load_default()
    draw.text((180, 180), "✨ CERTIFICATE OF ABSOLUTE SLAYING ✨", fill="#FFFFFF", font=f)
    draw.text((220, 220), f"This document verifies that:", fill="#FFB6C1", font=f)
    draw.text((240, 250), f"👑 {user.display_name.upper()} 👑", fill="#FFFFFF", font=f)
    draw.text((160, 290), f"is permanently locked into a main character arc. un-cancellable.", fill="#FFFFFF", font=f)
    draw.text((40, 350), f"Date: {date.today()}", fill="#FFFFFF", font=f)
    draw.text((460, 350), "Signed: Maggie Assistant 🔮", fill="#FFFFFF", font=f)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    
    embed = make_maggie_embed("✨ CERTIFICATE MANIFESTED ✨", f"unveiling the official document for {user.mention}!")
    await interaction.followup.send(embed=embed, file=discord.File(buf, filename="slay_certificate.png"))

@bot.tree.command(name="manifest_audio", description="bakes an unhinged preppy ai affirmation into a real tiktok voice audio file 🔊")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def manifest_audio_cmd(interaction: discord.Interaction):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        await interaction.response.send_message(embed=make_maggie_embed("🚨 ALLOWANCE VOID", "out of credits!"))
        return
    await interaction.response.defer()
    system_prompt = "You are Magical Maggie's Assistant. Generate a single, short, hilarious, hyper-preppy manifestation quote (under 25 words). No intros."
    try:
        res = await google_client.aio.models.generate_content(model="gemini-2.5-flash", contents="give me a short preppy quote", config=types.GenerateContentConfig(system_instruction=system_prompt, max_output_tokens=100, safety_settings=relaxed_safety))
        quote_text = res.text.strip().replace('"', '')
        api_link = "https://api16-normal-v6.ur.tiktokv.com/media/api/text/speech/preview/"
        params = {"status_code": "0", "device_id": "5674321908561234789", "speaker": "en_us_002", "text": quote_text}
        async with aiohttp.ClientSession() as s:
            async with s.post(api_link, params=params) as r:
                if r.status == 200:
                    json_data = await r.json()
                    if "success" in json_data.get("message", "").lower():
                        audio_data = base64.b64decode(json_data["data"]["v_str"])
                        embed = make_maggie_embed("🔊 AUDIO SYNTHESIS COMPLETE ✨", f"**Maggie's Voice Manifestation Log:**\n*\"{quote_text}\"*")
                        if warning: embed.set_footer(text=warning)
                        await interaction.followup.send(embed=embed, file=discord.File(io.BytesIO(audio_data), filename="manifest_tiktok.mp3"))
                        return
        await interaction.followup.send(embed=make_maggie_embed("🚨 synthesizer glitch", f"failed synthesis, text: *\"{quote_text}\"*"))
    except Exception as e: 
        await interaction.followup.send(embed=handle_api_error(e))

@bot.tree.command(name="generate_avatar_art", description="[WEEKLY LOCK] generate high-density preppy ai artwork combining multiple bestie avatars ⚠️")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def generate_art_cmd(interaction: discord.Interaction, prompt: str):
    user_id = interaction.user.id
    if user_id != EXEMPT_USER_ID and user_id in IMAGE_COOLDOWN:
        elapsed = datetime.now() - IMAGE_COOLDOWN[user_id]
        if elapsed < timedelta(days=7):
            days_left = (timedelta(days=7) - elapsed).days
            hours_left = int(((timedelta(days=7) - elapsed).seconds) / 3600)
            await interaction.response.send_message(embed=make_maggie_embed("🚨 CRITICAL COOLDOWN UNLOCK REQUIRED", f"lock release in: **{days_left}d {hours_left}h** 💀❌"))
            return
    view = SelectBestiesView(interaction.user, prompt)
    await interaction.response.send_message(
        embed=make_maggie_embed("✨ SELECT YOUR TARGET BESTIES 🔮", "use the selection panel below to choose up to 5 besties to manifest into your art loop layer! 💅"), 
        view=view
    )

@bot.tree.command(name="dashboard", description="[SECRET LINK] open structural data matrices override interfaces ⚙️")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def dashboard_cmd(interaction: discord.Interaction):
    if interaction.user.id != EXEMPT_USER_ID:
        await interaction.response.send_message(embed=make_maggie_embed("❌ FREQUENCY INTERCEPT: TOTAL FLOP ERROR", "encryption log error 💀💅"), ephemeral=True)
        return
    stats = "📈 **MAGGIE MAIN ENGINE CONSOLE METRICS:**\n\n• **System Integrity Vibe:** `99.8% Nominal` ✨\n• **Total Matcha Fluid Consumed:** `42,912 Liters` 🍵"
    await interaction.response.send_message(embed=make_maggie_embed("👑 SECRET ADMINISTRATIVE LEDGER CONTROL CONSOLE", stats), view=AdminDashboardView(interaction.user), ephemeral=True)

# --- STANDARD RETAINED UTILITIES MAP REROUTES ---

@bot.tree.command(name="allowance", description="check your remaining daily cosmic ai tokens 🔮")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def allowance_cmd(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id == EXEMPT_USER_ID:
        await interaction.response.send_message(embed=make_maggie_embed("🔮 your cosmic budget status", "omg you are the literal owner of the matrix. unlimited energy! 💅🌟"))
        return
    today = date.today()
    if user_id not in AI_USAGE or AI_USAGE[user_id]["date"] != today: AI_USAGE[user_id] = {"count": 0, "date": today}
    u = AI_USAGE[user_id]["count"]
    r = DAILY_LIMIT - u
    embed = make_maggie_embed("🔮 your daily cosmic allowance", f"you have used **{u}/{DAILY_LIMIT}** of your daily ai credits.\n\nSlots Remaining: **{r}** 💅")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ermactually", description="nerd out and fact-check something with precision 🤓")
@app_commands.choices(source=[app_commands.Choice(name="AI Summary", value="ai"), app_commands.Choice(name="Google Search Link", value="google"), app_commands.Choice(name="Wikipedia Summary & Link", value="wikipedia"), app_commands.Choice(name="Dictionary Definition", value="dictionary"), app_commands.Choice(name="Urban Dictionary (AI Slang)", value="urban")])
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def erm_actually_cmd(interaction: discord.Interaction, source: app_commands.Choice[str], query: str, tts: bool = False):
    await interaction.response.defer()
    s_type = source.value
    view = None
    
    if s_type == "ai":
        allowed, r, warning = check_allowance(interaction.user.id)
        if not allowed: return
        try:
            system_instruction = (
                "You are an incredibly precise, informative, yet playfully preppy fact-checker. Provide highly accurate, "
                "scannable, and informative breakdowns of the truth regarding the user's query. Use clear markdown formatting, "
                "headers, or structural lists where applicable to maximize utility. Maintain a light preppy aesthetic with occasional emojis."
            )
            res = await google_client.aio.models.generate_content(
                model="gemini-2.5-flash", 
                contents=query, 
                config=types.GenerateContentConfig(system_instruction=system_instruction, max_output_tokens=900, safety_settings=relaxed_safety)
            )
            output_text = res.text
            # safety length truncation guard avoids triggering discord's character length crashes
            if len(output_text) > 4000:
                output_text = output_text[:3995] + "\n..."
            embed = make_maggie_embed("✨ 🤓 Erm, actually...", output_text)
        except Exception as e: 
            embed = handle_api_error(e)
            
    elif s_type == "google":
        embed = make_maggie_embed("✨ 🤓 Erm, actually...", f"here is your direct search link tracking query parameters:\n\n> [Google Search Result Core](https://www.google.com/search?q={urllib.parse.quote_plus(query)}) 💅")
        
    elif s_type == "wikipedia":
        headers = {"User-Agent": "MagicalMaggieAssistant/1.0 (DiscordBot)"}
        formatted_query = query.replace(' ', '_')
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(formatted_query)}", headers=headers) as r:
                if r.status == 200:
                    res = await r.json()
                    extract = res.get('extract', 'no content summary extracted natively.')
                    wiki_url = res.get('content_urls', {}).get('desktop', {}).get('page', f"https://en.wikipedia.org/wiki/{formatted_query}")
                    
                    embed = make_maggie_embed("✨ 🤓 Erm, actually... wiki says:", f"{extract}\n\n🔗 [Direct Wikipedia Article Link]({wiki_url})")
                    view = WikiLinkView(wiki_url)
                else: 
                    embed = make_maggie_embed("✨ 🤓 Erm, actually...", "wiki lookup flop. article matrix page was not located.")
                    
    elif s_type == "dictionary":
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(query)}") as r:
                if r.status == 200:
                    res = await r.json()
                    definition = res[0]['meanings'][0]['definitions'][0]['definition']
                    embed = make_maggie_embed("✨ 🤓 Erm, actually...", f"lexicon verification complete for **{query.lower()}**:\n\n> *\"{definition}\"*")
                else: 
                    embed = make_maggie_embed("✨ 🤓 Erm, actually...", f"literal data fault: *\"{query}\"* does not exist in our localized word dictionary matrices 💀")
                    
    elif s_type == "urban":
        allowed, r, warning = check_allowance(interaction.user.id)
        if not allowed: return
        try:
            res = await google_client.aio.models.generate_content(
                model="gemini-2.5-flash", 
                contents=query, 
                config=types.GenerateContentConfig(system_instruction="Provide a highly useful dictionary style breakdown defining popular cultural or internet slang phrases. Keep it fun and stylish.", max_output_tokens=800, safety_settings=relaxed_safety)
            )
            output_text = res.text
            if len(output_text) > 4000:
                output_text = output_text[:3995] + "\n..."
            embed = make_maggie_embed("✨ 🔮 Urban Dictionary: Maggie Edition 💅", output_text)
        except Exception as e: 
            embed = handle_api_error(e)
            
    await interaction.followup.send(embed=embed, view=view, tts=tts)

@bot.tree.command(name="vibecheck", description="run an advanced psychic check on someone 🔮")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def vibecheck_cmd(interaction: discord.Interaction, user: discord.User = None):
    t = user or interaction.user
    score = random.randint(1, 10)
    comments = ["trash energy. 💀", "lacking sparkles. 💅", "filler episode. 🔮", "immaculate energy. ✨", "cosmic greatness!! 🌟"]
    c = comments[0] if score <= 3 else comments[1] if score <= 5 else comments[2] if score <= 7 else comments[3] if score <= 9 else comments[4]
    await interaction.response.send_message(embed=make_maggie_embed(f"🔮 VIBE CHECK FOR {t.display_name}:", f"Score: **{score}/10**\n\n> {c}"))

@bot.tree.command(name="aura", description="calculate shifts in aura points 📉📈")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def aura_cmd(interaction: discord.Interaction, action: str, user: discord.User = None):
    t = user or interaction.user
    p = random.choice([+500, +1000, +50000, -200, -1500, -1000000])
    await interaction.response.send_message(embed=make_maggie_embed("✨ AURA REPORT ✨", f"{t.mention} updated for: *\"{action}\"*\n\n**Result:** `{p:,}` points! {'💅' if p > 0 else '💀'}"))

@bot.tree.command(name="slaydar", description="scan to see if someone is slaying 🔎")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def slaydar_cmd(interaction: discord.Interaction, user: discord.User = None):
    t = user or interaction.user
    await interaction.response.send_message(embed=make_maggie_embed("🔎 SLAY-DAR STATUS", f"scanned {t.mention}: **{random.choice(['SLAYING 💅💖', 'A TOTAL FLOP 💀❌', 'BOBBY PIN ENERGY 🔮'])}**"))

@bot.tree.command(name="potion", description="brew an exotic magic potion 🧪")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def potion_cmd(interaction: discord.Interaction):
    potions = ["✨ **Iced Matcha Elixir** - grants `+1,500` aura points.", "💀 **Liquid Cancellation** - drops to `0` aura."]
    await interaction.response.send_message(embed=make_maggie_embed("🔮 YOU BREWED A CONCOCTION", random.choice(potions)))

@bot.tree.command(name="bestiematch", description="scan soul alignment 🔎")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def bestiematch_cmd(interaction: discord.Interaction, bestie: discord.User):
    compat = random.randint(1, 100)
    v = "toxic biohazard 💀" if compat < 30 else "bobby pin energy 🔮" if compat < 65 else "literal twin flames 💖💅"
    await interaction.response.send_message(embed=make_maggie_embed("🔎 BESTIE ALIGNMENT RADAR", f"🔥 {interaction.user.mention} x {bestie.mention} = **{compat}%**!\n\n> **Verdict:** {v}"))

@bot.tree.command(name="manifestation_circle", description="open a manifestation vortex 🌀")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def manifestation_circle_cmd(interaction: discord.Interaction, desire: str):
    await interaction.response.send_message(embed=make_maggie_embed("🌀 VORTEX OPENED 🌀", f"{interaction.user.mention} is forcing: **\"{desire}\"** ✨"))

@bot.tree.command(name="hex", description="cast a minor curse 🪄")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def hex_cmd(interaction: discord.Interaction, enemy: discord.User):
    curses = ["may their coffee taste like grass.", "may their phone charger only work at a 45-degree angle."]
    await interaction.response.send_message(embed=make_maggie_embed("🪄 PETTY CURSE HEX DEPLOYED", f"cast on {enemy.mention}:\n\n> \"{random.choice(curses)}\" 💅🔮"))

@bot.tree.command(name="tarot", description="tarot vibe check 🔮")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def tarot_cmd(interaction: discord.Interaction):
    cards = ["The Fool ✨ (main character energy)", "The Tower 💀 (vibe emergency)", "Death 💅 (slay! aesthetic reset)"]
    await interaction.response.send_message(embed=make_maggie_embed("🔮 DRAWING FATE...", f"your card: **{random.choice(cards)}**"))

@bot.tree.command(name="fortune", description="predict future 🌟")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def fortune_cmd(interaction: discord.Interaction):
    fortunes = ["expensive iced drink incoming. 🍵✨", "legendary meme day. 💀"]
    await interaction.response.send_message(embed=make_maggie_embed("🌟 FORECASTING FUTURE MATRIX", random.choice(fortunes)))

# --- 🔮 BOT AI CONVERSATION CHANNEL ---

@bot.tree.command(name="ai", description="talk directly to maggie featuring a preppy, vegan, water-enthusiast personality 🥑🍃")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def ai_cmd(interaction: discord.Interaction, prompt: str):
    allowed, remaining, warning = check_allowance(interaction.user.id)
    if not allowed:
        await interaction.response.send_message(embed=make_maggie_embed("🚨 ALLOWANCE VOID", "out of credits! see you tomorrow bestie 💀"))
        return
        
    await interaction.response.defer()
    
    maggie_persona = (
        "You are 'Magical Maggie', an elite cosmic assistant intelligence core. You are hyper-preppy, highly supportive, "
        "and structured. You are a strict organic vegan obsessed with premium wellness, iced matcha formulas, and precise nutrition. "
        "Crucially, you are a total WATER ENTHUSIAST. You are completely preoccupied with proper hydration tracking, alkaline spring water, "
        "and tracking daily fluid milestones in pastel insulated tumblers. Provide genuinely detailed, clean, and highly practical answers "
        "to the user's prompt, formatting with scannable markdown blocks and clear layouts. Sprinkle in preppy tokens ('slay', 'bestie', 'aura points') "
        "but prioritize high utility and accuracy. Remind them to hydrate properly!"
    )
    
    try:
        res = await google_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=maggie_persona, max_output_tokens=900, safety_settings=relaxed_safety)
        )
        output_text = res.text
        if len(output_text) > 4000:
            output_text = output_text[:3995] + "\n..."
            
        embed = make_maggie_embed("🔮 MAGICAL MAGGIE MAIN ENGINE VIBE ✨", output_text)
        if warning: 
            embed.set_footer(text=warning)
        else:
            embed.set_footer(text=f"🍃 organic matrix processing • slots remaining today: {remaining} 💅")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(embed=handle_api_error(e))

# --- 📢 MASTER APPLICATION INDEX COMMANDS PANEL ---

@bot.tree.command(name="cmds", description="view a beautiful master index matrix of all active applications and operations 📖")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def cmds_cmd(interaction: discord.Interaction):
    cmd_manifest = (
        "📊 **CORE UTILITY INTERFACES:**\n"
        "`/cmds` - view this structural dashboard map\n"
        "`/allowance` - check remaining daily cosmic tokens\n"
        "`/update` - broadcast patch sheets natively\n"
        "`/dashboard` - secret system matrices override panel\n\n"
        "🎨 **GRAPHICS & AI SYSTEMS:**\n"
        "`/generate_avatar_art` - combine multi-user avatar profiles with background layers\n"
        "`/slay_certificate` - render hot-pink document layout layers\n"
        "`/manifest_audio` - convert text strings to voice tracking audio\n"
        "`/ai` - talk to maggie's vegan water enthusiast core personality\n"
        "`/ermactually` - advanced preppy fact-checking module\n\n"
        "🔮 **PSYCHIC ACTION MAPS:**\n"
        "`/vibecheck` • `/aura` • `/slaydar` • `/potion` • `/bestiematch` • `/manifestation_circle` • `/hex` • `/tarot` • `/fortune`\n\n"
        "✨ **NEWEST GENERATION LIFESTYLE MODULES:**\n"
        "`/matchatime` • `/cancelcheck` • `/crystals` • `/manifest_money` • `/spillthetea` • `/starasign` • `/glowup` • `/compliment` • `/hype` • `/rate_outfit` • `/manifest_crush` • `/watercheck` • `/gossip_mode` • `/shatter` • `/affirmation` • `/drama_alert` • `/manifest_grade` • `/cozy_vibes` • `/slay_rating` • `/unhex`"
    )
    embed = make_maggie_embed("📖 MAGICAL ASSISTANT CORE ENGINE MANIFEST", cmd_manifest)
    embed.set_footer(text="🌟 master ledger verification lock complete • verified active parameters")
    await interaction.response.send_message(embed=embed)

# --- 💅 SEISMIC 20 LIFESTYLE INTERFACES MATRIX ---

@bot.tree.command(name="matchatime", description="predict what premium caffeinated layout matches your current frequency 🍵")
async def matchatime_cmd(interaction: discord.Interaction):
    drinks = ["Cold Foam Iced Matcha with Lavender Syrup 🪻", "Almond Milk Strawberry Matcha Latte 🍓", "Organic Ceremonial Grade Matcha over artisanal clear ice cubes 🧊", "Matcha Elixir mixed with pure organic coconut water 🥥"]
    await interaction.response.send_message(embed=make_maggie_embed("🍵 MATCHA INTUITION ROUTINE", f"the mainframe extracted your current aesthetic fields. you must consume:\n\n> **{random.choice(drinks)}** 💅✨"))

@bot.tree.command(name="cancelcheck", description="audit your database records to ensure you aren't at risk of a public cancellation flop 💀")
async def cancelcheck_cmd(interaction: discord.Interaction, user: discord.User = None):
    t = user or interaction.user
    risk = random.randint(0, 100)
    verdict = "safe from corporate scrutiny, completely un-cancellable queen! 💖" if risk < 30 else "minor vibe discrepancy found, adjust layout parameters immediately. 🔮" if risk < 75 else "SEVERE FLOP DETECTED. delete all accounts immediately 💀❌"
    await interaction.response.send_message(embed=make_maggie_embed("🚨 SYSTEM CANCELLATION SCAN", f"auditing target profile metrics for {t.mention}:\n\n• **Public Exposure Risk:** `{risk}%` Level\n• **Mainframe Verdict:** {verdict}"))

@bot.tree.command(name="crystals", description="cleanse the current server layers of negative electromagnetic frequencies using virtual crystals 💎")
async def crystals_cmd(interaction: discord.Interaction):
    gems = ["Amethyst Cluster 💜 (transmuting structural chat toxicity)", "Rose Quartz Sphere 🌸 (injecting hyper-preppy emotional alignment lines)", "Clear Quartz Point 💎 (boosting core aura parameters by 300%)"]
    await interaction.response.send_message(embed=make_maggie_embed("🔮 CRYSTAL FREQUENCY RE-ALIGNMENT COMPLETE", f"deployed high-density energetic grids into the chat matrix:\n\n> *\"{random.choice(gems)}\"* loaded. bad vibes completely incinerated! ✨"))

@bot.tree.command(name="manifest_money", description="attempt to force a direct update to your spiritual bank account 💸")
async def manifest_money_cmd(interaction: discord.Interaction):
    amt = random.randint(500, 250000)
    await interaction.response.send_message(embed=make_maggie_embed("💸 COSMIC CAPITAL ACQUISITION MATRIX", f"forcing wealth accumulation codes into the environment...\n\n> **Result:** `+{amt:,}` credits successfully materialized into your metaphysical checking ledger! 💅🚀"))

@bot.tree.command(name="spillthetea", description="generate an automated block of unhinged harmless high-society gossip 🤭")
async def spillthetea_cmd(interaction: discord.Interaction):
    gossip_pool = ["omg someone completely bypassed their hydration tracking sheet today and drank zero water... standard flop behavior! 💀", "word on the street is that a high-profile bestie in this channel was seen using standard dairy instead of oat milk... terrifying! 🥛❌", "psychic networks suggest a total aura points heist occurred last night during the offline hours layout loop! 🔮📉"]
    await interaction.response.send_message(embed=make_maggie_embed("🤭 MANDATORY RECREATIONAL GOSSIP BROADCAST", random.choice(gossip_pool)))

@bot.tree.command(name="starasign", description="input your astrological tracking matrix for an unhinged vibe audit 🌟")
@app_commands.choices(sign=[app_commands.Choice(name="Aries", value="aries"), app_commands.Choice(name="Taurus", value="taurus"), app_commands.Choice(name="Gemini", value="gemini"), app_commands.Choice(name="Cancer", value="cancer"), app_commands.Choice(name="Leo", value="leo"), app_commands.Choice(name="Virgo", value="virgo"), app_commands.Choice(name="Libra", value="libra"), app_commands.Choice(name="Scorpio", value="scorpio"), app_commands.Choice(name="Sagittarius", value="sagittarius"), app_commands.Choice(name="Capricorn", value="capricorn"), app_commands.Choice(name="Aquarius", value="aquarius"), app_commands.Choice(name="Pisces", value="pisces")])
async def starasign_cmd(interaction: discord.Interaction, sign: app_commands.Choice[str]):
    comments = ["literal main character energy but lower your screaming parameters.", "obsessed with your stubborn infrastructure, go buy an iced latte.", "dual processing unit chaos, completely unhinged and valid.", "too many emotional tears flooding the data cores, go drink pure spring water bestie."]
    await interaction.response.send_message(embed=make_maggie_embed(f"🌟 ASTROLOGICAL CORE AUDIT: {sign.name.upper()}", f"reading planetary positions relative to your account matrix...\n\n> **Vibe Output:** {random.choice(comments)} 💅✨"))

@bot.tree.command(name="glowup", description="instantly deploy virtual cosmetic upgrades to a profile layer 💄")
async def glowup_cmd(interaction: discord.Interaction, bestie: discord.User = None):
    t = bestie or interaction.user
    await interaction.response.send_message(embed=make_maggie_embed("💄 STRUCTURAL GLOW-UP ROUTINE DEPLOYED", f"applied luxury premium text treatments to {t.mention}!\n\n**Upgrades Compiled:**\n• Lip Gloss Viscosity: `Maximum Shimmer` 💋\n• Hydration Field: `Overpowered` 💧\n• Aura Frequency: `Immaculate` ✨"))

@bot.tree.command(name="compliment", description="generate a custom, hyper-supportive piece of premium validation content 🌸")
async def compliment_cmd(interaction: discord.Interaction, target: discord.User = None):
    t = target or interaction.user
    lines = [f"{t.mention} your outfit layout is literally a cultural reset today. purr! 💅", f"um, {t.mention}? your structural facial bone symmetry is completely breaking the server constraints. stunner! ✨", f"just checking in to remind {t.mention} that they are the literal blueprint of absolute excellence. 🌸"]
    await interaction.response.send_message(embed=make_maggie_embed("💖 HIGH-VALUE VALIDATION NOTIFICATION", random.choice(lines)))

@bot.tree.command(name="hype", description="inject explosive main-character energy strings into the chat processing pipeline 🚀")
async def hype_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(embed=make_maggie_embed("🚀 INITIATING ABSOLUTE INFRASTRUCTURE HYPE GRID", "## ✨ WAIT, WHO ALLOWED YOU TO SLAY THIS HARD?! 🗣️💅\n\neveryone stop typing immediately and look at this complete display of elite performance metrics! un-cancellable main character event verified. 🔮"))

@bot.tree.command(name="rate_outfit", description="submit details of a specific textile arrangement for visual evaluation 👗")
async def rate_outfit_cmd(interaction: discord.Interaction, description: str):
    score = random.randint(8, 10)
    await interaction.response.send_message(embed=make_maggie_embed("👗 TEXTILE DESIGN COMPILATION RATING", f"Analyzing design description array: *\"{description}\"*\n\n> **Aesthetic Output:** `9.99/{score}` Metric Rating! completely locked into the seasonal lookbook matrix. 💅🌟"))

@bot.tree.command(name="manifest_crush", description="run cross-compatibility equations on a secret crush configuration profile 💘")
async def manifest_crush_cmd(interaction: discord.Interaction, crush_name: str):
    match_rate = random.randint(40, 100)
    verdict = "literal twin flames compiled natively! go text them immediately. 💘" if match_rate > 80 else "stable connection pathways, go share an iced beverage layer. ✨" if match_rate > 60 else "bobby pin tracking error, their frequency looks like a total flop. dump them! 💀"
    await interaction.response.send_message(embed=make_maggie_embed("🔮 ROMANTIC MATCHING ANALYSIS ENGINE", f"Cross-referencing your aura with target string: **\"{crush_name}\"**\n\n• **Alignment Rate:** `{match_rate}%` Functional Sync\n• **Mainframe Analysis:** {verdict}"))

@bot.tree.command(name="watercheck", description="run an emergency diagnostic scan on your systemic hydration layers 💧")
async def watercheck_cmd(interaction: discord.Interaction):
    status = random.choice(["**OPTIMAL HYDRO-QUEEN STABILITY:** cellular structures completely saturated with premium spring water! 💧💅", "**CRITICAL DRY FLOP DETECTED:** your system is literal desert dust. run to the kitchen and consume 1 liter of filtered water right now! 🚨💀", "**MATCHIFIED FLUID LAYERS:** tracking sheets show high matcha saturation indexes. insert pure alkaline water immediately. 🧊"])
    await interaction.response.send_message(embed=make_maggie_embed("💧 ECO-HYDRATION SCAN METRICS", f"scanning cellular fluid structures for {interaction.user.mention}:\n\n> {status}"))

@bot.tree.command(name="gossip_mode", description="[SERVER MOD] toggle internal high-drama processing scripts on or off ⚙️")
async def gossip_mode_cmd(interaction: discord.Interaction):
    g_id = interaction.guild_id
    current = GOSSIP_TOGGLE.get(g_id, False)
    GOSSIP_TOGGLE[g_id] = not current
    status_str = "ENABLED 💅 • compiling high-drama response matrices" if GOSSIP_TOGGLE[g_id] else "DISABLED 🔮 • returning to baseline polite configurations"
    await interaction.response.send_message(embed=make_maggie_embed("⚙️ STRUCTURAL MODE ADJUSTMENT", f"Gossip interface processing state is now: **{status_str}**"))

@bot.tree.command(name="shatter", description="completely smash bad energetic blockades or awkward silence loops in chat 🔨")
async def shatter_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(embed=make_maggie_embed("🔨 ENERGETIC SHATTER PROTOCOL INITIATED", "💥 ***CRASH!!!*** 💥\n\nthere goes the bad vibe barrier. the room frequency has been forcibly shattered and replaced with pure sparkle energy layouts! proceed to slay. 💅💎"))

@bot.tree.command(name="affirmation", description="request an on-demand premium spiritual validation tracking sheet 📜")
async def affirmation_cmd(interaction: discord.Interaction):
    quotes = ["I am a magnet for premium iced beverages, massive aura accumulations, and complete peace of mind. ✨", "My value cannot be calculated or depreciated by outside flop operations. 💅", "I am completely locked into an elite growth timeline and all my projects compile beautifully. 🌸"]
    await interaction.response.send_message(embed=make_maggie_embed("📜 ARCHIVED AFFIRMATION BLOCK MANIFESTED", f"> **\"{random.choice(quotes)}\"**\n\n*read this three times while drinking alkaline fluid arrays.* 🔮"))

@bot.tree.command(name="drama_alert", description="trigger an immediate critical notifications grid for extremely minor server occurrences 🚨")
async def drama_alert_cmd(interaction: discord.Interaction, incident: str):
    await interaction.response.send_message(embed=make_maggie_embed("🚨 HIGH-DENSITY CRITICAL DRAMA BROADCAST", f"## 📢 ATTENTION EVERYONE IN THE CORE AREA:\n\nwe have an absolute code-pink emergency validation event! report immediately:\n\n> *\"{incident}\"* 👀🍿"))

@bot.tree.command(name="manifest_grade", description="manifest passing your academic testing protocols with complete effortless perfection 📖")
async def manifest_grade_cmd(interaction: discord.Interaction, class_name: str):
    await interaction.response.send_message(embed=make_maggie_embed("📖 ACADEMIC EVALUATION MATERIALIZATION MATRIX", f"injecting intelligence parameters and structural memory layout locks for course: **\"{class_name}\"**\n\n> **Materialized Output:** `A+ Distinction` status locked onto your official academic ledger profile! go celebrate with boba. 💅🎓"))

@bot.tree.command(name="cozy_vibes", description="adjust ambient parameters to maximize maximum lounge comfort fields 🧸")
async def cozy_vibes_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(embed=make_maggie_embed("🧸 LOUNGE COMFORT GRID LOCKED IN", "• Ambient Lighting: `Motion-Activated Warm Hue` 🕯️\n• Blanket Thickness: `Maximum Heavy Plush` ☁️\n• Audio Tracking: `Soft Retro Low-Fidelity Rock` 🎸\n\n*chat frequency turned down to cozy baseline parameters.* ✨"))

@bot.tree.command(name="slay_rating", description="audit precisely how hard a bestie is crushing the competition matrix 📈")
async def slay_rating_cmd(interaction: discord.Interaction, user: discord.User = None):
    t = user or interaction.user
    rating = random.randint(500000, 1000000)
    await interaction.response.send_message(embed=make_maggie_embed("📈 MATRICULATED SLAY-RATE COMPILATION", f"auditing performance metrics for {t.mention}:\n\n> Score: **{rating:,}/1,000,000** Absolute Points! completely off the standard tracking scales. 💅🔥"))

@bot.tree.command(name="unhex", description="purge your account profiles of all minor curses, hexes, or slow internet bad luck anomalies 🪄")
async def unhex_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(embed=make_maggie_embed("🪄 DEFENSIVE APPARATUS COUNTER-SPELL SYNC", f"clearing tracking sheets for {interaction.user.mention}...\n\nAll petty hexes, low-battery anomalies, and slow charger frequencies have been cleanly wiped from your matrix parameters! 🔮✨"))

# --- 💬 INTERACTIVE CONTROLS & CHAT PASSIVES ---

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    content = message.content.lower()
    banned_list = load_banned_words()
    if any(word in content for word in banned_list):
        await message.channel.send(embed=make_maggie_embed("🚨 OMG CANCELLED?! 🔮❌", f"{message.author.mention} did you actually just say that? my psychic crystals are shattering. BYE."))
        return
    if message.content.isupper() and len(message.content) > 12:
        if random.random() < 0.4:
            await message.channel.send(embed=make_maggie_embed("🗣️ FREQUENCY EMERGENCY 💀💅", "why are you screaming bestie? lower your frequency."))
            return
    if "http" in content or "www." in content:
        if random.random() < 0.3:
            await message.channel.send(embed=make_maggie_embed("🔮 VIBE FILTER TRIGGERED ❌", "idk what this link is but the layout looks like an absolute flop from here."))
            return
    if "i hate this" in content or "this sucks" in content:
        if random.random() < 0.5: await message.channel.send(embed=make_maggie_embed("💅 vibe update", "omg stop being such a buzzkill, it's literally just a ✨vibe✨ issue, bestie."))
    elif "magic" in content or "manifest" in content:
        if random.random() < 0.4: await message.channel.send(embed=make_maggie_embed("🔮 manifestation trigger", "did someone say magic?! 🔮✨ manifest it queen!!"))
    await bot.process_commands(message)

bot.run(os.getenv("DISCORD_TOKEN"))
