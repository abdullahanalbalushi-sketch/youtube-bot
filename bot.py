import discord
import os
from discord.ext import commands
from discord import app_commands

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def fmt_num(n: float) -> str:
    return f"{int(n):,}"

def fmt_pct(n: float) -> str:
    return f"{n:.1f}%"

def score_label(score: int):
    if score >= 7:
        return "A+ ممتاز 🟢", "الثمبنيل يشد، الـ Hook قوي، والناس يكملون.\nالخوارزمية راح تدفع هذا المقطع.", discord.Color.green()
    elif score >= 5:
        return "B جيد 🔵", "المقطع يشتغل بشكل معقول مع مجال واضح للتحسين.", discord.Color.blue()
    elif score >= 3:
        return "C يحتاج تحسين 🟡", "في مشكلة واضحة في مرحلة معينة — الأرقام تحدد وين بالضبط.", discord.Color.yellow()
    else:
        return "D يحتاج مراجعة شاملة 🔴", "المشكلة في أكثر من مرحلة — ابدأ بإصلاح الـ Hook أولاً.", discord.Color.red()

def retention_bar(pct: float, length: int = 10) -> str:
    filled = max(0, min(round(pct / 100 * length), length))
    return "█" * filled + "░" * (length - filled)

def get_tip(ctr: float, r1: float, r2: float, r3: float) -> str:
    if r1 < 50:
        return "🎣 **الـ Hook ضعيف**\nأكثر من نصف المشاهدين يخرجون في أول دقيقة.\nالحل: ابدأ بأقوى لحظة في المقطع مباشرة، وأزل أي مقدمة طويلة."
    elif (r1 - r2) > 20:
        return "📉 **انقطاع في المنتصف**\nالناس يبدأون بس ما يكملون للوسط.\nالحل: أضف معلومة مفاجئة أو غيّر الإيقاع في المنتصف."
    elif (r2 - r3) > 20:
        return "🏁 **خروج قبل النهاية**\nالناس يصلون للوسط بس يخرجون قبل النهاية.\nالحل: أضف تشويق في الوسط — مثل: 'في النهاية راح أقول لك...'"
    elif ctr < 3:
        return "🖼️ **CTR ضعيف**\nالثمبنيل والعنوان ما يشدون النظر.\nالحل: ثمبنيل فيه وجه أو تعبير واضح، وعنوان فيه رقم أو سؤال."
    else:
        return "✅ **أداء متوازن**\nالخطوة الجاية: ارفع الإمبرشنز عن طريق النشر في وقت الذروة والتفاعل مع التعليقات في أول ساعة."

def calc_score(ctr: float, r1: float, r3: float) -> int:
    score = 0
    if ctr >= 10:   score += 3
    elif ctr >= 5:  score += 2
    elif ctr >= 2:  score += 1
    if r1 >= 70:    score += 3
    elif r1 >= 50:  score += 2
    elif r1 >= 30:  score += 1
    if r3 >= 30:    score += 3
    elif r3 >= 15:  score += 2
    elif r3 >= 5:   score += 1
    return score


@bot.tree.command(name="video_performance", description="احسب أداء مقطعك على يوتيوب 📊")
@app_commands.describe(
    impressions="عدد مرات ظهور المقطع (الإمبرشنز)",
    views="عدد المشاهدات (الكليك)",
    retention_min1="نسبة % من بقي بعد أول دقيقة",
    retention_mid="نسبة % من وصل لوسط المقطع",
    retention_end="نسبة % من أكمل المقطع للنهاية",
)
async def video_performance(interaction: discord.Interaction, impressions: int, views: int, retention_min1: float, retention_mid: float, retention_end: float):
    await interaction.response.defer()

    errors = []
    if impressions <= 0: errors.append("الإمبرشنز لازم يكون أكبر من 0")
    if views <= 0: errors.append("المشاهدات لازم تكون أكبر من 0")
    if views > impressions: errors.append("المشاهدات ما تكون أكثر من الإمبرشنز")
    for label, val in [("أول دقيقة", retention_min1), ("الوسط", retention_mid), ("النهاية", retention_end)]:
        if not (0 <= val <= 100): errors.append(f"نسبة {label} لازم تكون بين 0 و 100")
    if retention_min1 < retention_mid or retention_mid < retention_end:
        errors.append("النسب لازم تكون تنازلية: أول دقيقة ≥ وسط ≥ نهاية")

    if errors:
        err_embed = discord.Embed(title="❌ خطأ في المدخلات", description="\n".join(f"• {e}" for e in errors), color=discord.Color.red())
        await interaction.followup.send(embed=err_embed, ephemeral=True)
        return

    ctr      = views / impressions * 100
    true_ret = retention_end * views / impressions / 100 * 100
    ppl_min1 = round(views * retention_min1 / 100)
    ppl_mid  = round(views * retention_mid  / 100)
    ppl_end  = round(views * retention_end  / 100)

    score = calc_score(ctr, retention_min1, retention_end)
    grade, grade_desc, color = score_label(score)
    tip = get_tip(ctr, retention_min1, retention_mid, retention_end)

    embed = discord.Embed(title="📊 تقرير أداء المقطع", color=color)
    embed.add_field(name="📌 الأرقام الأساسية", value=f"```\nالإمبرشنز     {fmt_num(impressions)}\nالكليك         {fmt_num(views)}\nCTR            {fmt_pct(ctr)}\nTrue Retention {fmt_pct(true_ret)}\n```", inline=False)
    embed.add_field(name="📈 منحنى الاحتفاظ", value=f"أول دقيقة  {retention_bar(retention_min1)} **{fmt_pct(retention_min1)}** — {fmt_num(ppl_min1)} شخص\nوسط المقطع {retention_bar(retention_mid)}  **{fmt_pct(retention_mid)}**  — {fmt_num(ppl_mid)} شخص\nآخر دقيقة  {retention_bar(retention_end)} **{fmt_pct(retention_end)}** — {fmt_num(ppl_end)} شخص", inline=False)
    embed.add_field(name=f"🏆 التقييم: {grade}", value=grade_desc, inline=False)
    embed.add_field(name="💡 الإجراء المطلوب", value=tip, inline=False)
    embed.set_footer(text="استخدم /video_performance لتحليل مقطع جديد")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="video_help", description="كيف تستخدم حاسبة أداء المقاطع؟")
async def video_help(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 دليل استخدام حاسبة الأداء", color=discord.Color.blurple())
    embed.add_field(name="الأمر", value="`/video_performance`", inline=False)
    embed.add_field(name="المدخلات المطلوبة", value="**impressions** — الإمبرشنز\n**views** — الكليك\n**retention_min1** — % بقوا بعد أول دقيقة\n**retention_mid** — % وصلوا لوسط المقطع\n**retention_end** — % أكملوا للنهاية\n\n⚠️ النسب الثلاث تكون تنازلية دائماً", inline=False)
    embed.add_field(name="وين تلاقي الأرقام؟", value="افتح **YouTube Studio** ← اختر المقطع\n← **Analytics** ← **Reach** للإمبرشنز والـ CTR\n← **Engagement** ← **Audience retention** للنسب", inline=False)
    embed.add_field(name="مثال", value="`/video_performance impressions:10000 views:610 retention_min1:65 retention_mid:40 retention_end:22`", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ البوت شغال: {bot.user} | Slash commands synced")


bot.run(TOKEN)
