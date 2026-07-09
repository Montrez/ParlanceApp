"""
Daily language and culture posts for #daily-culture.

Morgan picks one topic per day from a rotating list and posts it at 10:00 AM ET.
Topics cover Spanish and French language, culture, interpreter craft, and exam tips.
"""
from __future__ import annotations

import datetime
import random

import discord
from discord.ext import commands, tasks

from .config import CHANNELS, GUILD_ID
from .personalities import GUIDE


# ── Topic library ─────────────────────────────────────────────────────────────

TOPICS = [
    # False cognates
    {
        "title": "False friend of the day: **embarazada**",
        "body": (
            "In Spanish, *embarazada* means **pregnant** — not embarrassed. "
            "If you meant embarrassed, the word you want is *avergonzada/o*.\n\n"
            "False cognates like this one are one of the most common interpreter slips. "
            "Which ones have tripped you up?"
        ),
    },
    {
        "title": "False friend of the day: **sensible**",
        "body": (
            "In French, *sensible* means **sensitive**, not sensible. "
            "If you mean sensible (reasonable), say *raisonnable*.\n\n"
            "The French word *sensé* is closer to the English meaning, "
            "but even that leans more toward 'makes sense' than 'levelheaded.'"
        ),
    },
    {
        "title": "False friend: **éventuellement** (French)",
        "body": (
            "*Éventuellement* does not mean 'eventually' — it means **possibly** or **if need be**.\n\n"
            "If you mean eventually, say *finalement* or *à terme*. "
            "This one catches even advanced speakers off guard in formal contexts."
        ),
    },
    {
        "title": "False friend: **actualmente** (Spanish)",
        "body": (
            "*Actualmente* means **currently** or **at present** — not 'actually.'\n\n"
            "For 'actually,' use *de hecho*, *en realidad*, or *efectivamente* depending on the shade of meaning. "
            "In a courtroom or medical setting, mixing these up changes the entire statement."
        ),
    },
    # Register and formality
    {
        "title": "Register matters: *usted* in Latin America vs. Spain",
        "body": (
            "In most of Latin America, *usted* is used far more broadly than in Spain — "
            "including with close family members in some countries like Colombia.\n\n"
            "In Spain, *tú* is the default for almost any peer or younger person. "
            "When interpreting, always match the register of the original speaker, not your own habits."
        ),
    },
    {
        "title": "Register tip: when to use *vous* vs. *tu* in French",
        "body": (
            "The *vous/tu* distinction in French is not just about age — it signals relationship, "
            "power, and context. In professional or medical settings, always default to *vous* "
            "unless the other person explicitly switches.\n\n"
            "Switching too early can feel presumptuous. Switching too late can feel cold. "
            "When in doubt, follow the other speaker's lead."
        ),
    },
    # Interpreter craft
    {
        "title": "Interpreter tip: chunking",
        "body": (
            "Simultaneous interpreters don't wait for a sentence to end before starting — "
            "they break speech into **chunks** of 3 to 5 words and begin rendering immediately.\n\n"
            "The trick is holding the meaning of the last chunk in short-term memory while "
            "your mouth is still producing the previous one. Practicing dictation exercises "
            "in your target language builds this muscle fast."
        ),
    },
    {
        "title": "Interpreter tip: note-taking symbols",
        "body": (
            "Consecutive interpreters develop personal symbol systems over time. "
            "A few common ones:\n"
            "→ cause/leads to\n"
            "↑↓ increase/decrease\n"
            "≠ contradiction or denial\n"
            "+ positive, agreement\n"
            "∅ nothing, absence, refusal\n\n"
            "The goal isn't shorthand for every word — it's capturing structure, "
            "sequence, and the speaker's stance."
        ),
    },
    {
        "title": "Interpreter tip: the 'ear-voice span'",
        "body": (
            "The ear-voice span (EVS) is the delay between when you hear something and when you say it. "
            "In simultaneous interpretation, a trained interpreter typically maintains an EVS of **2 to 4 seconds**.\n\n"
            "Too short and you start guessing before the meaning is clear. "
            "Too long and your working memory gets overloaded. "
            "Finding your natural EVS is one of the core skills of interpreter training."
        ),
    },
    # Cultural notes
    {
        "title": "Cultural note: the *sobremesa*",
        "body": (
            "In Spanish-speaking cultures, *la sobremesa* refers to the time spent lingering at the table "
            "after a meal — talking, debating, laughing. There is no direct equivalent in English or French.\n\n"
            "It reflects a cultural value: meals are not just about food, they are social rituals. "
            "Understanding concepts like this deepens your ability to interpret tone and intent."
        ),
    },
    {
        "title": "Cultural note: French and the Académie française",
        "body": (
            "The *Académie française* has been France's official guardian of the French language since 1635. "
            "It publishes rulings on new words and correct usage — though speakers often ignore them.\n\n"
            "In 2017, it declared gender-neutral writing (*l'écriture inclusive*) a 'mortal peril' for French. "
            "Whether you agree or not, knowing this context helps you understand why register and grammar "
            "carry so much weight in formal French communication."
        ),
    },
    {
        "title": "Cultural note: *voseo* and regional identity",
        "body": (
            "*Voseo* — using *vos* instead of *tú* — is standard in Argentina, Uruguay, and parts of Central America. "
            "Its conjugations differ: *vos hablás*, *vos comés*, *vos vivís*.\n\n"
            "In some countries it was historically stigmatized; today in Argentina it is a point of pride. "
            "An interpreter working with Argentine speakers should never 'correct' *voseo* — "
            "it is not an error, it is the standard."
        ),
    },
    {
        "title": "Cultural note: French in Africa",
        "body": (
            "French is the official or co-official language of 29 countries, "
            "most of them in Africa. More people speak French in sub-Saharan Africa "
            "than in France itself.\n\n"
            "African French has regional vocabulary, rhythms, and loanwords from local languages. "
            "An interpreter who only knows Parisian French may miss meaning in a Congolese or "
            "Senegalese speaker's phrasing."
        ),
    },
    # Grammar and language facts
    {
        "title": "Grammar deep dive: *ser* vs. *estar*",
        "body": (
            "Both mean 'to be,' but they are not interchangeable. "
            "A quick rule that holds up in professional contexts:\n\n"
            "*Ser* → identity, origin, material, permanent traits, time/date, profession\n"
            "*Estar* → state, location (of people/things), temporary conditions, results of change\n\n"
            "The nuance matters for interpretation: *'está muerto'* (he is dead, a current state) "
            "vs. *'es muerto'* (which would be unnatural) — context carries meaning."
        ),
    },
    {
        "title": "Grammar deep dive: the French subjunctive",
        "body": (
            "The subjunctive (*subjonctif*) is used far more in French than in English. "
            "It appears after expressions of doubt, emotion, necessity, or opinion:\n\n"
            "*Il faut que tu sois là.* (You need to be there.)\n"
            "*Je doute qu'il vienne.* (I doubt he'll come.)\n\n"
            "In formal and legal French, mastering the subjunctive is non-negotiable. "
            "In everyday speech, it is sometimes replaced by the indicative — "
            "but in writing and professional interpretation, it signals precision."
        ),
    },
    {
        "title": "Language fact: Spanish is the world's second most spoken native language",
        "body": (
            "With over 490 million native speakers, Spanish ranks second only to Mandarin. "
            "It is the official language of 20 countries across four continents.\n\n"
            "What this means for interpreters: there is no single 'correct' Spanish. "
            "Your job is to serve the speaker's dialect and intent — not impose a standard."
        ),
    },
    {
        "title": "Language fact: French has more words for 'you' than you think",
        "body": (
            "Beyond *tu* and *vous*, older literary French used *tu* for God and intimates "
            "while *vous* was strictly formal. Today *on* often replaces *nous* in spoken French "
            "(*on y va* instead of *nous y allons*).\n\n"
            "In Quebec French, *vous* can sound archaic between peers, while in formal France it is still expected. "
            "Regional and generational variation is always in play."
        ),
    },
    # Exam tips
    {
        "title": "DELE tip: formal register is non-negotiable at B2 and above",
        "body": (
            "The DELE exam at B2 and C1/C2 levels tests your ability to use formal written Spanish consistently.\n\n"
            "Common pitfalls:\n"
            "Mixing *tú* and *usted* in the same piece of writing\n"
            "Using colloquial connectors (*y* to start sentences, *bueno* as filler)\n"
            "Inconsistent verb tense in formal narration\n\n"
            "Practicing with Parlance on formal sentences before the exam can sharpen your register instincts quickly."
        ),
    },
    {
        "title": "DELF tip: the oral production section",
        "body": (
            "In the DELF B2, the oral production task requires you to take a position and defend it. "
            "Examiners are not just listening for vocabulary — they want:\n\n"
            "Clear structure (introduction, argument, counterargument, conclusion)\n"
            "Appropriate connectors (*en revanche*, *par ailleurs*, *c'est pourquoi*)\n"
            "Consistent register throughout\n\n"
            "Practice by summarizing a news article aloud and then arguing against your own summary."
        ),
    },
    # Word origins and curiosities
    {
        "title": "Word origin: *sincere*",
        "body": (
            "One popular theory holds that *sincere* comes from the Latin *sine cera* — 'without wax.' "
            "Dishonest marble merchants allegedly hid cracks in stone with wax. "
            "Honest sellers advertised their work as *sine cera*.\n\n"
            "Linguists debate whether this is true, but it is a useful reminder: "
            "language is full of metaphors from material culture that have long since faded from view."
        ),
    },
    {
        "title": "Word curiosity: *dépaysement* (French)",
        "body": (
            "*Dépaysement* describes the disorientation of being in a foreign place — "
            "that feeling of everything being unfamiliar, the rules slightly different, "
            "the cues you rely on no longer working.\n\n"
            "There is no single English equivalent. The closest is 'culture shock,' "
            "but *dépaysement* carries less anxiety and more wistfulness. "
            "It is sometimes used positively — as the refreshing jolt of a new environment."
        ),
    },
    {
        "title": "Word curiosity: *madrugada* (Spanish)",
        "body": (
            "*La madrugada* refers specifically to the hours between midnight and dawn — "
            "roughly 1 AM to 5 AM. English has no dedicated word for this stretch of time.\n\n"
            "Languages carve up the world differently. "
            "A good interpreter notices when a source-language concept has no clean equivalent "
            "and knows how to render the meaning without losing it."
        ),
    },
]


def _topic_for_today() -> dict:
    day_index = datetime.date.today().timetuple().tm_yday
    return TOPICS[day_index % len(TOPICS)]


# ── Scheduled cog ─────────────────────────────────────────────────────────────

class DailyCultureCog(commands.Cog):
    """Posts one language/culture topic per day to #daily-culture."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._posted_today = False
        self.daily_post.start()

    def cog_unload(self):
        self.daily_post.cancel()

    def _culture_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        return discord.utils.get(guild.text_channels, name=CHANNELS["daily_culture"])

    @tasks.loop(hours=24)
    async def daily_post(self):
        await self.bot.wait_until_ready()
        guild = self.bot.get_guild(GUILD_ID)
        if not guild:
            return
        channel = self._culture_channel(guild)
        if not channel:
            return

        # Pick a topic based on the day of year so all members see the same one
        topic = _topic_for_today()

        await channel.send(f"**{topic['title']}**\n\n{topic['body']}")

    @daily_post.before_loop
    async def before_daily_post(self):
        """Wait until 10:00 AM ET before firing the first post."""
        await self.bot.wait_until_ready()
        now = datetime.datetime.now(datetime.timezone.utc)
        # 14:00 UTC = 10:00 AM ET (14:00 in winter / 13:00 EDT — close enough for daily cadence)
        target = now.replace(hour=14, minute=0, second=0, microsecond=0)
        if now >= target:
            target += datetime.timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        await discord.utils.sleep_until(target)
