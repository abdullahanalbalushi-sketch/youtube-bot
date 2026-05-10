import discord
import os
from discord.ext import commands
from discord import app_commands

TOKEN = os.environ["DISCORD_TOKEN"]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ─────────────────────────────────────────
#  مساعد: تنسيق
# ─────────────────────────────────────────
def fmt_num(n: float) -> str:
    return f"{int(n):,}"

def fmt_pct(n: float) -> str:
    return f"{n:.1f}%"

def retention_bar(pct: float, length: int = 10) -> str:
    filled = max(0, min(round(pct / 100 * length), length))
    return "█" * filled + "░" * (length - filled)


# ─────────────────────────────────────────
#  أداة ١: تحليل أداء الفيديو
# ─────────────────────────────────────────
def score_label(score: int):
    if score >= 7:
        return "A+ ممتاز 🟢", "الثمبنيل يشد، الـ Hook قوي، والناس يكملون.\nالخوارزمية راح تدفع هذا المقطع.", discord.Color.green()
    elif score >= 5:
        return "B جيد 🔵", "المقطع يشتغل بشكل معقول مع مجال واضح للتحسين.", discord.Color.blue()
    elif score >= 3:
        return "C يحتاج تحسين 🟡", "في مشكلة واضحة في مرحلة معينة — الأرقام تحدد وين بالضبط.", discord.Color.yellow()
    else:
        return "D يحتاج مراجعة شاملة 🔴", "المشكلة في أكثر من مرحلة — ابدأ بإصلاح الـ Hook أولاً.", discord.Color.red()

def get_tip(ctr, r1, r2, r3):
    if r1 < 50:
        return "🎣 **الـ Hook ضعيف**\nأكثر من نصف المشاهدين يخرجون في أول دقيقة.\nالحل: ابدأ بأقوى لحظة في المقطع مباشرة."
    elif (r1 - r2) > 20:
        return "📉 **انقطاع في المنتصف**\nالحل: أضف معلومة مفاجئة أو غيّر الإيقاع في المنتصف."
    elif (r2 - r3) > 20:
        return "🏁 **خروج قبل النهاية**\nالحل: أضف تشويق في الوسط — مثل: 'في النهاية راح أقول لك...'"
    elif ctr < 3:
        return "🖼️ **CTR ضعيف**\nالحل: ثمبنيل فيه وجه أو تعبير واضح، وعنوان فيه رقم أو سؤال."
    else:
        return "✅ **أداء متوازن**\nارفع الإمبرشنز عن طريق النشر في وقت الذروة والتفاعل في أول ساعة."

def calc_score(ctr, r1, r3):
    score = 0
    if ctr >= 10: score += 3
    elif ctr >= 5: score += 2
    elif ctr >= 2: score += 1
    if r1 >= 70: score += 3
    elif r1 >= 50: score += 2
    elif r1 >= 30: score += 1
    if r3 >= 30: score += 3
    elif r3 >= 15: score += 2
    elif r3 >= 5: score += 1
    return score

@bot.tree.command(name="video_performance", description="حلل أداء مقطعك على يوتيوب 📊")
@app_commands.describe(
    impressions="عدد مرات ظهور المقطع",
    views="عدد المشاهدات",
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
        if not (0 <= val <= 100): errors.append(f"نسبة {label} لازم تكون بين 0 و100")
    if retention_min1 < retention_mid or retention_mid < retention_end:
        errors.append("النسب لازم تكون تنازلية: أول دقيقة ≥ وسط ≥ نهاية")

    if errors:
        err_embed = discord.Embed(title="❌ خطأ في المدخلات", description="\n".join(f"• {e}" for e in errors), color=discord.Color.red())
        await interaction.followup.send(embed=err_embed, ephemeral=True)
        return

    ctr = views / impressions * 100
    true_ret = retention_end * views / impressions / 100 * 100
    ppl_min1 = round(views * retention_min1 / 100)
    ppl_mid = round(views * retention_mid / 100)
    ppl_end = round(views * retention_end / 100)

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


# ─────────────────────────────────────────
#  أداة ٢: حاسبة نمو القناة
# ─────────────────────────────────────────
@bot.tree.command(name="channel_growth", description="احسب متى توصل لهدف مشتركينك 📈")
@app_commands.describe(
    current_subs="عدد مشتركينك الحالي",
    goal_subs="الهدف اللي تبي توصله",
    videos_per_month="عدد الفيديوهات اللي تنشرها كل شهر",
    avg_subs_per_video="متوسط المشتركين الجدد من كل فيديو",
)
async def channel_growth(interaction: discord.Interaction, current_subs: int, goal_subs: int, videos_per_month: int, avg_subs_per_video: int):
    await interaction.response.defer()

    if goal_subs <= current_subs:
        embed = discord.Embed(title="❌ خطأ", description="الهدف لازم يكون أكبر من مشتركينك الحالي.", color=discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    subs_needed = goal_subs - current_subs
    subs_per_month = videos_per_month * avg_subs_per_video

    if subs_per_month <= 0:
        embed = discord.Embed(title="❌ خطأ", description="متوسط المشتركين لازم يكون أكبر من 0.", color=discord.Color.red())
        await interaction.followup.send(embed=embed, ephemeral=True)
        return

    months_needed = subs_needed / subs_per_month
    years = int(months_needed // 12)
    months = int(months_needed % 12)

    if months_needed <= 1:
        time_str = "أقل من شهر! 🔥"
        color = discord.Color.green()
    elif months_needed <= 6:
        time_str = f"{int(months_needed)} أشهر"
        color = discord.Color.green()
    elif months_needed <= 12:
        time_str = f"{int(months_needed)} أشهر"
        color = discord.Color.blue()
    else:
        time_str = f"{years} سنة و{months} أشهر" if months > 0 else f"{years} سنة"
        color = discord.Color.orange()

    videos_needed = int(subs_needed / avg_subs_per_video)

    embed = discord.Embed(title="📈 حاسبة نمو القناة", color=color)
    embed.add_field(name="📌 الوضع الحالي", value=f"```\nالمشتركين الحالي   {fmt_num(current_subs)}\nالهدف              {fmt_num(goal_subs)}\nالمطلوب            {fmt_num(subs_needed)}\n```", inline=False)
    embed.add_field(name="⚡ معدل نموك", value=f"```\nفيديوهات شهرياً    {videos_per_month}\nمشتركين/فيديو      {fmt_num(avg_subs_per_video)}\nمشتركين شهرياً     {fmt_num(subs_per_month)}\n```", inline=False)
    embed.add_field(name="🎯 متى توصل لهدفك؟", value=f"**{time_str}**\nتحتاج تقريباً **{fmt_num(videos_needed)} فيديو** إضافي", inline=False)

    if months_needed > 12:
        needed_per_video = int((subs_needed / 12) / videos_per_month)
        embed.add_field(name="💡 عشان توصل خلال سنة", value=f"تحتاج **{fmt_num(needed_per_video)} مشترك** من كل فيديو بدال {fmt_num(avg_subs_per_video)}", inline=False)

    embed.set_footer(text="استخدم /channel_growth لحساب هدف جديد")
    await interaction.followup.send(embed=embed)


# ─────────────────────────────────────────
#  أداة ٣: أفضل وقت نشر
# ─────────────────────────────────────────
BEST_TIMES = {
    "gaming": {"days": ["الجمعة", "السبت", "الأحد"], "times": ["٤ عصر", "٦ عصر", "٨ مساء"], "tip": "الجمهور يكون فاضي بعد الظهر وبالليل في نهاية الأسبوع."},
    "education": {"days": ["الثلاثاء", "الأربعاء", "الخميس"], "times": ["٧ مساء", "٨ مساء", "٩ مساء"], "tip": "الجمهور يبحث عن تعلم بعد الدوام أو الدراسة."},
    "vlog": {"days": ["الجمعة", "السبت"], "times": ["١٢ ظهر", "٢ عصر", "٤ عصر"], "tip": "الفلوق يحقق أفضل أداء في عطلة نهاية الأسبوع."},
    "tech": {"days": ["الثلاثاء", "الأربعاء", "الخميس"], "times": ["٦ مساء", "٨ مساء"], "tip": "جمهور التقنية نشط أيام منتصف الأسبوع بعد العمل."},
    "cooking": {"days": ["الأربعاء", "الخميس", "الجمعة"], "times": ["٤ عصر", "٥ عصر", "٦ مساء"], "tip": "الناس تفكر في الأكل قبل وقت العشاء."},
    "finance": {"days": ["الأحد", "الاثنين", "الثلاثاء"], "times": ["٧ مساء", "٨ مساء", "٩ مساء"], "tip": "جمهور المال يبحث عن معلومات في بداية الأسبوع."},
    "other": {"days": ["الجمعة", "السبت", "الأحد"], "times": ["٦ مساء", "٨ مساء"], "tip": "أوقات الذروة العامة على يوتيوب."}
}

@bot.tree.command(name="best_time", description="اعرف أفضل وقت تنشر فيديوهاتك ⏰")
@app_commands.describe(niche="نيش قناتك")
@app_commands.choices(niche=[
    app_commands.Choice(name="ألعاب / Gaming", value="gaming"),
    app_commands.Choice(name="تعليم / Education", value="education"),
    app_commands.Choice(name="فلوق / Vlog", value="vlog"),
    app_commands.Choice(name="تقنية / Tech", value="tech"),
    app_commands.Choice(name="طبخ / Cooking", value="cooking"),
    app_commands.Choice(name="مال واستثمار / Finance", value="finance"),
    app_commands.Choice(name="غير ذلك / Other", value="other"),
])
async def best_time(interaction: discord.Interaction, niche: str):
    data = BEST_TIMES.get(niche, BEST_TIMES["other"])
    embed = discord.Embed(title="⏰ أفضل أوقات النشر", color=discord.Color.blurple())
    embed.add_field(name="📅 أفضل الأيام", value="\n".join(f"• {d}" for d in data["days"]), inline=True)
    embed.add_field(name="🕐 أفضل الأوقات", value="\n".join(f"• {t}" for t in data["times"]), inline=True)
    embed.add_field(name="💡 السبب", value=data["tip"], inline=False)
    embed.add_field(name="⚠️ ملاحظة", value="هذي أوقات عامة — راجع Analytics تبعك بعد ٥ فيديوهات وشوف متى جمهورك تحديداً نشط.", inline=False)
    embed.set_footer(text="استخدم /best_time لمعرفة أفضل وقت حسب نيشك")
    await interaction.response.send_message(embed=embed)


# ─────────────────────────────────────────
#  أداة ٤: تحليل العنوان
# ─────────────────────────────────────────
POWER_WORDS = ["سر", "كيف", "لماذا", "أفضل", "أسوأ", "خطأ", "حقيقة", "مجاناً", "سريع", "بدون", "رهيب", "صدمة", "لن تصدق", "أخيراً", "مهم"]
WEAK_WORDS = ["فيديو", "مقطع", "حلقة", "الجزء", "قصتي"]

@bot.tree.command(name="title_check", description="حلل قوة عنوان فيديوهك 🎯")
@app_commands.describe(title="عنوان الفيديو اللي تبي تحلله")
async def title_check(interaction: discord.Interaction, title: str):
    score = 0
    feedback = []

    length = len(title)
    if 40 <= length <= 60:
        score += 2
        feedback.append("✅ طول العنوان مثالي")
    elif length < 30:
        feedback.append("⚠️ العنوان قصير جداً — أضف تفاصيل أكثر")
    elif length > 70:
        feedback.append("⚠️ العنوان طويل جداً — يتقطع في نتائج البحث")
    else:
        score += 1
        feedback.append("🟡 طول العنوان مقبول")

    if any(char.isdigit() for char in title):
        score += 2
        feedback.append("✅ فيه رقم — الأرقام ترفع CTR")
    else:
        feedback.append("💡 جرب تضيف رقم — مثال: '٥ طرق' أو '١٠ أخطاء'")

    found_power = [w for w in POWER_WORDS if w in title]
    if found_power:
        score += 2
        feedback.append(f"✅ فيه كلمات قوية: {', '.join(found_power)}")
    else:
        feedback.append("💡 أضف كلمة تثير فضول مثل: سر، كيف، لماذا، أفضل")

    found_weak = [w for w in WEAK_WORDS if w in title]
    if found_weak:
        score -= 1
        feedback.append(f"⚠️ تجنب كلمات ضعيفة مثل: {', '.join(found_weak)}")

    if "؟" in title or "?" in title:
        score += 1
        feedback.append("✅ سؤال في العنوان يثير فضول")

    score = max(0, min(score, 7))
    pct = int(score / 7 * 100)

    if pct >= 80: color, grade = discord.Color.green(), "عنوان قوي 🟢"
    elif pct >= 60: color, grade = discord.Color.blue(), "عنوان جيد 🔵"
    elif pct >= 40: color, grade = discord.Color.yellow(), "يحتاج تحسين 🟡"
    else: color, grade = discord.Color.red(), "عنوان ضعيف 🔴"

    embed = discord.Embed(title="🎯 تحليل العنوان", color=color)
    embed.add_field(name="العنوان", value=f"```{title}```", inline=False)
    embed.add_field(name="التقييم", value=f"**{pct}/100 — {grade}**", inline=False)
    embed.add_field(name="التفاصيل", value="\n".join(feedback), inline=False)
    embed.set_footer(text="استخدم /title_check لتحليل أي عنوان")
    await interaction.response.send_message(embed=embed)


# ─────────────────────────────────────────
#  أداة ٥: نشر مصدر تعليمي
# ─────────────────────────────────────────
@bot.tree.command(name="post_resource", description="انشر رابط أو مصدر تعليمي في روم معين 📌")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(
    channel="الروم اللي تبي تنشر فيه",
    title="عنوان المصدر أو الرابط",
    url="الرابط",
    description="وصف مختصر — اختياري",
)
async def post_resource(interaction: discord.Interaction, channel: discord.TextChannel, title: str, url: str, description: str = None):
    embed = discord.Embed(title=f"📌 {title}", url=url, color=discord.Color.blurple())
    if description:
        embed.description = description
    embed.set_footer(text=f"نشره {interaction.user.display_name}")

    await channel.send(embed=embed)
    await interaction.response.send_message(f"✅ تم النشر في {channel.mention}", ephemeral=True)


# ─────────────────────────────────────────
#  دليل الاستخدام
# ─────────────────────────────────────────
@bot.tree.command(name="tools_help", description="شوف كل الأدوات المتاحة 📖")
async def tools_help(interaction: discord.Interaction):
    embed = discord.Embed(title="📖 أدوات صانع المحتوى", color=discord.Color.blurple())
    embed.add_field(name="📊 /video_performance", value="حلل أداء فيديوهك — CTR، ريتنشن، ونصايح مخصصة", inline=False)
    embed.add_field(name="📈 /channel_growth", value="احسب متى توصل لهدف مشتركينك", inline=False)
    embed.add_field(name="⏰ /best_time", value="اعرف أفضل وقت تنشر حسب نيش قناتك", inline=False)
    embed.add_field(name="🎯 /title_check", value="حلل قوة عنوان فيديوهك قبل ما تنشر", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ─────────────────────────────────────────
#  تشغيل البوت
# ─────────────────────────────────────────
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ البوت شغال: {bot.user} | Slash commands synced")

@post_resource.error
async def post_resource_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message('❌ ما عندك صلاحية استخدام هذا الأمر.', ephemeral=True)

bot.run(TOKEN)
