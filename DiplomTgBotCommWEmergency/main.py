import asyncio
import json
import logging
import math
import time
import datetime
import pytz
import requests

from aiogram import Bot, Dispatcher, types, F
from asyncio.exceptions import CancelledError

from aiogram.enums import ChatAction, ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, CallbackQuery
from aiogram.utils import markdown
from aiogram.utils.keyboard import InlineKeyboardBuilder

from DB.db_conn import create_db, add_users_in_db, see_all_users, add_street_to_incident, add_incidient, get_user_by_id, \
    delete_dispatcher, add_description_to_incidient, check_for_updates, see_all_incidents, get_dispatchers_tg_id
from config import settings

dp = Dispatcher()
bot = Bot(token=settings.bot_token)
YANDEX_API_KEY = settings.yandex_api_key
utc_timezone = pytz.timezone("UTC")
chat_id = []
TypeInc = None
description = None
dispatchers_list = []


@dp.message(CommandStart())
async def handle_start(msg: types.Message):
    await msg.bot.send_chat_action(
        chat_id=msg.chat.id,
        action=ChatAction.TYPING,
    )
    add_users_in_db(msg.from_user.id, msg.from_user.username, msg.from_user.is_bot)
    await msg.answer(
        text=f'Здравстуйте, {msg.from_user.first_name}, что у вас произошло?',
    )


@dp.message(Command("help"))
async def handle_short_numbers(msg: types.Message):
    await msg.answer(
        text="112 - Единый номер вызова экстренных служб\n"
             "101 - Пожарная\n"
             "102 - Милиция\n"
             "103 - Скорая\n"
             "104 - Газовая\n",
    )


@dp.message(Command("first_aid"))
async def handle_command_first_aid(msg: types.Message):
    await msg.answer(
        text="Чтобы не растеряться и грамотно оказать первую помощь, важно соблюдать следующую последовательность действий:\n"
             "  1. Убедиться, что при оказании первой помощи вам ничего не угрожает и вы не подвергаете себя опасности.\n"
             "  2. Обеспечить безопасность пострадавшему и окружающим (например, извлечь пострадавшего из горящего автомобиля).\n"
             "  3. Проверить наличие у пострадавшего признаков жизни (пульс, дыхание, реакция зрачков на свет) и сознания."
             "Для проверки дыхания необходимо запрокинуть голову пострадавшего, наклониться к его рту и носу и попытаться услышать или почувствовать дыхание."
             "Для обнаружения пульса необходимо приложить подушечки пальцев к сонной артерии пострадавшего."
             "Для оценки сознания необходимо (по возможности) взять пострадавшего за плечи, аккуратно встряхнуть и задать какой-либо вопрос.\n"
             "  4. Вызвать специалистов: 112 — с мобильного телефона, с городского — 103 (скорая) или 101 (спасатели).\n"
             "  5. Оказать неотложную первую помощь. В зависимости от ситуации это может быть:\n"
             "      - восстановление проходимости дыхательных путей;\n"
             "      - сердечно-лёгочная реанимация;\n"
             "      - остановка кровотечения и другие мероприятия.\n"
             "  6. Обеспечить пострадавшему физический и психологический комфорт, дождаться прибытия специалистов.\n"
    )


@dp.message(Command("briefing"))
async def handle_command_briefing(msg: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Искуственное дыхание рот в рот", callback_data="artificial respiration")
    builder.button(text="Непрямой массаж сердца", callback_data="cardiac massage")
    builder.button(text="Перелом", callback_data="fracture")
    builder.button(text="Наложение кровоостанавливающего жгута", callback_data="hemostatic")
    builder.button(text="Обморок", callback_data="fainting")
    builder.button(text="Ожог", callback_data="burn")
    builder.button(text="Утопление", callback_data="drowned")
    builder.button(text="Переохлаждение и обморожение", callback_data="frostbite")
    builder.button(text="Отравление", callback_data="poisoned")
    builder.adjust(1)
    await msg.answer(
        text="Инструктаж",
        reply_markup=builder.as_markup()
    )


@dp.callback_query(F.data == "artificial respiration")
async def handle_cb_artificail_respiration(call: CallbackQuery):
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text=
        "Если при осмотре пострадавшего естественное дыхание не обнаружено, необходимо немедленно провести искусственную вентиляцию легких.\n"
        "   1. Обеспечьте проходимость верхних дыхательных путей. Поверните голову пострадавшего набок и пальцем удалите из полости рта слизь, кровь, инородные предметы.\n"
        f"{markdown.hbold("Проверьте носовые ходы пострадавшего, при необходимости очистите их.\n")}"
        "   2. Запрокиньте голову пострадавшего, удерживая шею одной рукой.\n"
        "Не меняйте положение головы пострадавшего при травме позвоночника!\n"
        "   3. Положите на рот пострадавшего салфетку, платок, кусок ткани или марли, чтобы защитить себя от инфекций. Зажмите нос пострадавшего большим и указательным пальцем."
        " Глубоко вдохните, плотно прижмитесь губами ко рту пострадавшего. Сделайте выдох в лёгкие пострадавшего.\n"
        f"{markdown.hbold("Первые 5–10 выдохов должны быть быстрыми (за 20–30 секунд), затем — 12–15 выдохов в минуту.\n")}"
        "   4. Следите за движением грудной клетки пострадавшего. Если грудь пострадавшего при вдохе воздуха поднимается, значит, вы всё делаете правильно.",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "cardiac massage")
async def handle_cb_cardial_massage(call: CallbackQuery):
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text=
        f"Если вместе с дыханием отсутствует пульс, необходимо сделать непрямой массаж сердца.\n"
        f"{markdown.hbold("Внимание! Нельзя проводить закрытый массаж сердца при наличии пульса.\n")}"
        "   1. Уложите пострадавшего на плоскую твёрдую поверхность. На кровати и других мягких поверхностях проводить компрессию грудной клетки нельзя.\n"
        "   2. Определите расположение у пострадавшего мечевидного отростка. Мечевидный отросток — это самая короткая и узкая часть грудины, её окончание.\n"
        "   3. Отмерьте 2–4 см вверх от мечевидного отростка — это точка компрессии.\n"
        "   4. Положите основание ладони на точку компрессии. При этом большой палец должен указывать либо на подбородок, либо на живот пострадавшего, в зависимости от местоположения лица, осуществляющего реанимацию."
        " Поверх одной руки положите вторую ладонь, пальцы сложите в замок. Надавливания проводятся строго основанием ладони — ваши пальцы не должны соприкасаться с грудиной пострадавшего.\n"
        f"  5. Осуществляйте ритмичные толчки грудной клетки сильно, плавно, строго вертикально, тяжестью верхней половины вашего тела. Частота — 100–110 надавливаний в минуту. При этом грудная клетка должна прогибаться на 3–4 см.\n"
        f"{markdown.hbold("Грудным детям непрямой массаж сердца производится указательным и средним пальцем одной руки. Подросткам — ладонью одной руки.\n")}"
        "Если одновременно с закрытым массажем сердца проводится ИВЛ, каждые два вдоха должны чередоваться с 30 надавливаниями на грудную клетку.\n"
        f"{markdown.hbold("Вред:")} непрямой массаж сердца может сломать ребра, следовательно, сломанные кости легко могут повредить легкие и сердце.\n"
        f"{markdown.hbold("Как правильно")}: непрямой массаж сердца выполняется только после того, как вы убедились, что пульс и дыхание у пострадавшего отсутствуют, а врача по близости нет. В то время пока один человек делает массаж сердца, кто-то второй обязательно должен вызвать скорую медицинскую помощь.\n"
        "Массаж выполняется в ритме – 100 компрессий за 1 минуту. В случае детей, непрямой массаж сердца выполняется пальцами в другом ритме."
        " После того как сердце запустится, приступите к выполнению искусственного дыхания. Альтернативный способ: 30 компрессий и 2 вдоха, после чего снова повторите компрессии и 2 вдоха.\n"
        f"{markdown.hbold("В случае аварии не доставайте пострадавшего из машины и не меняйте его позу\n")}"
        f"{markdown.hbold(" Вред:")} летальный исход чаще всего случается при травме или переломе позвоночника. Даже самое не существенное движение, вызванное помочь пострадавшему лечь удобней, может убить или сделать человека инвалидом.\n"
        f"{markdown.hbold(" Как правильно:")} вызовите скорую помощь сразу после травмы, если существует опасение что у пострадавшего может быть травмироваться голова, шея или позвоночник. При этом следите за дыханием больного до приезда врачей.",
        parse_mode=ParseMode.HTML,
    )


@dp.callback_query(F.data == "fracture")
async def handle_cb_fracture(call: CallbackQuery):
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text="  1. Оцените тяжесть состояния пострадавшего, определите локализацию перелома.\n"
             "  2. При наличии кровотечения остановите его.\n"
             "  3. Определите, возможно ли перемещение пострадавшего до прибытия специалистов.\n"
             f"{markdown.hbold("Не переносите пострадавшего и не меняйте его положения при травмах позвоночника!\n")}"
             "  4. Обеспечьте неподвижность кости в области перелома — проведите иммобилизацию. Для этого необходимо обездвижить суставы, расположенные выше и ниже перелома.\n"
             "  5. Наложите шину. В качестве шины можно использовать плоские палки, доски, линейки, прутья и прочее. Шину необходимо плотно, но не туго зафиксировать бинтами или пластырем.\n"
             "При закрытом переломе иммобилизация производится поверх одежды. При открытом переломе нельзя прикладывать шину к местам, где кость выступает наружу.",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "hemostatic")
async def handle_cb_hemostatic(call: CallbackQuery):
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text=
        f"{markdown.hbold("Остановка кровотечения с использованием жгута может привести к ампутации конечности\n")}"
        f"{markdown.hbold(" Вред:")} передавливание конечностей – следствие неправильного или ненужного наложения жгута. Некроз тканей происходит из-за нарушения циркуляции крови в конечностях, потому что жгут не останавливает кровотечение, а полностью блокирует циркуляцию.\n"
        f"{markdown.hbold(" Как правильно:")} наложите повязку из чистой ткани или стерильной марли на рану и придержите её. До прибытия врачей этого будет достаточно. Только при сильном кровотечении, когда риск смерти выше риска ампутации, позволительно пользоваться жгутом.\n"
        "   1.Наложите жгут на одежду или мягкую подкладку чуть выше раны.\n"
        "   2.Затяните жгут и проверьте пульсацию сосудов: кровотечение должно прекратиться, а кожа ниже жгута — побледнеть.\n"
        "   3.Наложите повязку на рану.\n"
        "   4.Запишите точное время, когда наложен жгут.\n"
        f"{markdown.hbold("Жгут на конечности можно накладывать максимум на 1 час. По его истечении жгут необходимо ослабить на 10–15 минут. При необходимости можно затянуть вновь, но не более чем на 20 минут.\n")}"
        f"{markdown.hbold("В случае кровотечения из носа, запрещается запрокидывать голову или ложиться на спину\n")}"
        f"{markdown.hbold(" Вред:")} давление резко поднимается, если при носовом кровотечении запрокинуть голову или лечь на спину. Кровь может попасть в легкие или вызвать рвоту.\n"
        f"{markdown.hbold(" Как правильно:")} держа голову прямо, вы ускорите снижение давления. Приложите что-то холодное к носу. Закрывайте ноздри поочередно на 15 минут каждую, указательным и большим пальцем. В это время дышите ртом. Повторите этот приём, в случае если кровотечения не останавливается. Если кровотечение продолжается, срочно вызовете скорую медицинскую помощь.\n",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "fainting")
async def handle_cb_fainting(call: CallbackQuery):
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text="Важно отличать обычный и эпилептический обморок. Первому, как правило, предшествуют тошнота и головокружение.\n"
             "Предобморочное состояние характеризуется тем, что человек закатывает глаза, покрывается холодным потом, у него слабеет пульс, холодеют конечности.\n"
             "Типичные ситуации наступления обморока:\n"
             "  · испуг\n"
             "  · волнение\n"
             "  · духота и другие\n"
             "Если человек упал в обморок, придайте ему удобное горизонтальное положение и обеспечьте приток свежего воздуха (расстегните одежду, ослабьте ремень, откройте окна и двери)."
             "Брызните на лицо пострадавшего холодной водой, похлопайте его по щекам. При наличии под рукой аптечки дайте понюхать ватный тампон, смоченный нашатырным спиртом.\n"
             "Если сознание не возвращается 3–5 минут, немедленно вызывайте скорую.\n"
             "Когда пострадавший придёт в себя, дайте ему крепкого чая.\n"
             f"{markdown.hbold("Не вставляйте в рот человеку, у которого припадок ложку. И не вынимайте ему язык\n")}"
             f"{markdown.hbold("    Вред:")} Человек в припадочном состоянии может проглотить или задохнуться предметом, который вставляется для защиты языка в рот.\n"
             f"{markdown.hbold("    Как правильно:")} Приступ приводит в посинению или резким вздрагиваниям. Сам по себе организм не может нанести себе вред, а приступы заканчиваются сами. Лучше вызовите врача, и позаботьтесь, о том, чтобы человек не нанёс себе вред и мог свободно дышать."
             "С языком ничего не случится. Человек его не проглотит, а прикус языка ничем не опасен. Уложите больного набок сразу после приступа.\n",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "burn")
async def handle_cb_burn(call: CallbackQuery):
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text="Ожоги различаются по степеням, а также по типам повреждения. По последнему основанию выделяют ожоги:\n"
             "  · термические (пламя, горячая жидкость, пар, раскалённые предметы)\n"
             "  · химические (щёлочи, кислоты)\n"
             "  · электрические\n"
             "  · лучевые (световое и ионизирующее излучение)\n"
             "  · комбинированные\n"
             "При ожогах первым делом необходимо устранить действие поражающего фактора (огня, электрического тока, кипятка и так далее).\n"
             "Затем, при термических ожогах, поражённый участок следует освободить от одежды (аккуратно, не отдирая, а обрезая вокруг раны прилипшую ткань) и в целях дезинфекции и обезболивания оросить его водно-спиртовым раствором (1/1) или водкой.\n"
             f"{markdown.hbold("Не используйте масляные мази и жирные кремы — жиры и масла не уменьшают боль, не дезинфицируют ожог и не способствуют заживлению.\n")}"
             "После оросите рану холодной водой, наложите стерильную повязку и приложите холод. Кроме того, дайте пострадавшему тёплой подсоленной воды.\n"
             "Для ускорения заживления лёгких ожогов используйте спреи с декспантенолом. Если ожог занимает площадь больше одной ладони, обязательно обратитесь к врачу.\n"
             f"{markdown.hbold("Обработка йодом, медицинским спиртом и промывание ран перекисью водорода иногда представляют опасность\n")}"
             f"{markdown.hbold("    Вред:")} соединительная ткань разрушается перекисью водорода, тем самым рана заживает намного дольше. Спирт, йод и зелёнка сжигают неповрежденные клетки и провоцируют болевой шок или ожог при контакте с раной.\n"
             f"{markdown.hbold("    Как правильно:")} промойте рану чистой водой (можно кипяченой), после чего обработайте рану мазью с содержанием антибиотика. Не накладывайте повязку из бинта или пластырь без необходимости. Перевязанная рана заживает намного дольше.\n",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "drowned")
async def handle_cb_drowned(call: CallbackQuery):
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text="  1. Извлеките пострадавшего из воды.\n"
             f"{markdown.hbold("Тонущий человек хватается за всё, что попадётся под руку. Будьте осторожны: подплывайте к нему сзади, держите за волосы или подмышки, держа лицо над поверхностью воды.\n")}"
             "  2. Положите пострадавшего животом на колено, чтобы голова была внизу.\n"
             "  3. Очистите ротовую полость от инородных тел (слизь, рвотные массы, водоросли).\n"
             "  4. Проверьте наличие признаков жизни.\n"
             "  5. При отсутствии пульса и дыхания немедленно приступайте к ИВЛ и непрямому массажу сердца.\n"
             "  6. После восстановления дыхания и сердечной деятельности положите пострадавшего набок, укройте его и обеспечивайте комфорт до прибытия медиков.\n",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "frostbite")
async def handle_cb_frostbite(call: CallbackQuery):
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text="Первая помощь при гипотермии\n"
             "  1. Заведите (занесите) пострадавшего в тёплое помещение или укутайте тёплой одеждой.\n"
             "  2. Не растирайте пострадавшего, дайте телу постепенно согреться самостоятельно.\n"
             "  3. Дайте пострадавшему тёплое питьё и еду.\n"
             f"{markdown.hbold("Не используйте алкоголь!\n")}"
             "Переохлаждение нередко сопровождается обморожением, то есть повреждением и омертвением тканей организма под воздействием низких температур."
             "Особенно часто встречается обморожение пальцев рук и ног, носа и ушей — частей тела с пониженным кровоснабжением.\n"
             f"{markdown.hbold("Первая помощь при обморожении\n")}"
             "  1. Поместите пострадавшего в тепло.\n"
             "  2. Снимите с него промёрзшую или мокрую одежду.\n"
             "  3. Не растирайте пострадавшего снегом или тканью — так вы только травмируете кожу.\n"
             "  4. Укутайте обмороженный участок тела.\n"
             "  5. Дайте пострадавшему горячее сладкое питьё или горячую пищу.\n",
        parse_mode=ParseMode.HTML
    )


@dp.callback_query(F.data == "poisoned")
async def handle_cb_poisened(call: CallbackQuery):
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text="В зависимости от вида токсина различают отравления:\n"
             "  · угарным газом\n"
             "  · ядохимикатами\n"
             "  · алкоголем\n"
             "  · лекарствами\n"
             "  · пищей и другие\n"
             "От характера отравления зависят меры оказания первой помощи. Наиболее распространены пищевые отравления, сопровождаемые тошнотой, рвотой, поносом и болями в желудке."
             "Пострадавшему в этом случае рекомендуется принимать по 3–5 граммов активированного угля через каждые 15 минут в течение часа, пить много воды, воздержаться от приёма пищи и обязательно обратиться к врачу.\n"
             f"{markdown.hbold("В этих случаях первая помощь состоит из следующих шагов:\n")}"
             "  1. Промойте пострадавшему желудок. Для этого заставьте его выпить несколько стаканов подсоленной воды (на 1 л — 10 г соли и 5 г соды)."
             "После 2–3 стаканов вызовите у пострадавшего рвоту. Повторяйте эти действия, пока рвотные массы не станут «чистыми».\n"
             f"{markdown.hbold("Промывание желудка возможно только в том случае, если пострадавший в сознании.\n")}"
             "  2. Растворите в стакане воды 10–20 таблеток активированного угля, дайте выпить это пострадавшему.\n"
             "  3. Дождитесь приезда специалистов.\n",
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("find"))
async def handle_command_find(msg: types.Message):
    call_fire_dep_btn = InlineKeyboardButton(
        text="Пожарная",
        callback_data="fire department",
    )
    call_police_btn = InlineKeyboardButton(
        text="Милиция",
        callback_data="police station",
    )
    call_emergency_btn = InlineKeyboardButton(
        text="Скорая помощь",
        callback_data="hospital",
    )
    call_gas_btn = InlineKeyboardButton(
        text="Газовая",
        callback_data="gas service",
    )
    rows = [
        [call_fire_dep_btn],
        [call_police_btn],
        [call_emergency_btn],
        [call_gas_btn],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    await msg.answer(
        text=f"Кого хотите вызвать?",
        reply_markup=markup,
    )


@dp.message(Command("location"))
async def handle_command_location(msg: types.Message):
    button = KeyboardButton(
        text="Отправить геолокацию",
        request_location=True,
    )
    buttons = [button]
    markup = ReplyKeyboardMarkup(
        keyboard=[buttons],
    )
    await msg.answer(
        text="Нажмите кнопку",
        reply_markup=markup,
    )


@dp.message(Command("call"))
async def handle_command_call(msg: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Пожар",
        callback_data="fire"
    )
    builder.button(
        text="Авария",
        callback_data="car crash"
    )
    builder.button(
        text="Пострадал человек",
        callback_data="emergency"
    )
    builder.button(
        text="Утечка газа",
        callback_data="gas"
    )
    builder.adjust(1)
    await msg.bot.send_message(
        chat_id=msg.chat.id,
        text="Что у вас произшло?",
        reply_markup=builder.as_markup()
    )


@dp.message(Command("chatId"), F.from_user.id.in_({42, 1012387760}))
async def save_chat_id(msg: types.Message):
    chat_id = msg.chat.id
    f = open('chat_id.txt', 'r+')
    f.write(str(chat_id))
    f.close()


@dp.message(Command("users"), F.from_user.id.in_({42, 1012387760}))
async def see_all_chat_users(msg: types.Message):
    button_add = InlineKeyboardButton(
        text='Установить как диспетчера',
        callback_data='setDispatcher',
    )
    button_delete = InlineKeyboardButton(
        text='Удалить диспетчера',
        callback_data='deleteDispatcher',
    )
    row_first = [button_add]
    row_second = [button_delete]
    rows = [row_first, row_second]
    markup = InlineKeyboardMarkup(inline_keyboard=rows)
    await msg.answer(
        text=f"Пользователи чата:",
    )
    for line in see_all_users():
        await msg.answer(
            text=f"{line}",
            reply_markup=markup,
        )


def dispatchers_list():
    return get_dispatchers_tg_id()


@dp.message(Command("incidents"), F.from_user.id.in_(dispatchers_list()))
async def handle_command_incidents(msg: types.Message):
    for line in see_all_incidents():
        incident = str(line)
        symbols_to_remove = "()'"
        for symbol in symbols_to_remove:
            incident = incident.replace(symbol, "")
        await msg.answer(
            text=incident
        )


@dp.message(F.location)
async def handle_location(msg: types.Message):
    await msg.bot.send_chat_action(
        chat_id=msg.chat.id,
        action=ChatAction.FIND_LOCATION
    )
    global longitude, latitude
    longitude = msg.location.longitude
    latitude = msg.location.latitude
    await msg.answer(
        text=f"Ваша позиция: {latitude},{longitude}",
    )
    return longitude, latitude


@dp.callback_query(F.data == "edit_message")
async def edit_message(call: CallbackQuery):
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text="Хорошо, укажите где это произошло"
    )


@dp.callback_query(F.data == "add_street")
async def add_street(call: CallbackQuery):
    global TypeInc
    try:
        senders_location = f"Широта: {latitude}, Долгота: {longitude}"
    except (AttributeError, NameError):
        senders_location = "Местоположение не определено"

    place = call.message.text
    performed_date = time.time()
    if TypeInc is not None:
        if description is not None:
            add_street_to_incident(Type=TypeInc, sender_name=call.from_user.first_name,
                                   sender_id=call.from_user.id, sender_location=senders_location,
                                   Date=datetime.datetime.fromtimestamp(performed_date),
                                   place=place, description=description)
            await call.bot.send_message(
                chat_id=call.message.chat.id,
                text="Спасибо за сообщение, ожидайте...",
            )
            await call.message.delete_reply_markup()
        else:
            await call.bot.send_message(
                chat_id=call.message.chat.id,
                text="Пожалуйста опишите что у вас произошло"
            )
    else:
        await call.bot.send_message(
            chat_id=call.message.chat.id,
            text="Пожалуйста нажмите /call"
        )
        return


@dp.callback_query(F.data == "fire")
async def handle_cb_call_fire(call: CallbackQuery):
    global TypeInc
    global longitude, latitude
    TypeInc = "Пожар"
    sender_id = call.from_user.id
    sender_name = call.from_user.first_name
    performed_date = time.time()
    try:
        senders_location = f"Широта: {latitude}, Долгота: {longitude}"
    except (AttributeError, NameError):
        senders_location = "Местоположение не определено"
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text="Опишитие что произошло",
        reply_to_message_id=call.message.message_id
    )
    try:
        add_incidient(TypeInc, sender_id, sender_name, senders_location,
                      datetime.datetime.fromtimestamp(performed_date))
    except Exception:
        await call.answer(
            text="Что-то пошло не так, попробуйте заново"
        )


@dp.callback_query(F.data == "car crash")
async def handle_cb_call_car_crash(call: CallbackQuery):
    global TypeInc
    global latitude, longitude
    TypeInc = "Авария"
    sender_id = call.from_user.id
    sender_name = call.from_user.first_name
    performed_date = time.time()
    try:
        senders_location = f"Широта: {latitude}, Долгота: {longitude}"
    except (AttributeError, NameError):
        senders_location = "Местоположение не определено"
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text="Опишитие что произошло",
        reply_to_message_id=call.message.message_id
    )
    try:
        add_incidient(TypeInc, sender_id, sender_name, senders_location,
                      datetime.datetime.fromtimestamp(performed_date))
    except Exception:
        await call.answer(
            text="Что-то пошло не так, попробуйте заново"
        )


@dp.callback_query(F.data == "emergency")
async def handle_cb_call_emergency(call: CallbackQuery):
    global TypeInc
    global latitude, longitude
    TypeInc = "Пострадал человек"
    sender_id = call.from_user.id
    sender_name = call.from_user.first_name
    performed_date = time.time()
    try:
        senders_location = f"Широта: {latitude}, Долгота: {longitude}"
    except (AttributeError, NameError):
        senders_location = "Местоположение не определено"
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text="Опишитие что произошло",
        reply_to_message_id=call.message.message_id
    )
    try:
        add_incidient(TypeInc, sender_id, sender_name, senders_location,
                      datetime.datetime.fromtimestamp(performed_date))
    except Exception:
        await call.answer(
            text="Что-то пошло не так, попробуйте заново"
        )
    return TypeInc


@dp.callback_query(F.data == "gas")
async def handle_cb_call_gas(call: CallbackQuery):
    global TypeInc
    global latitude, longitude
    TypeInc = "Утечка газа"
    sender_id = call.from_user.id
    sender_name = call.from_user.first_name
    performed_date = time.time()
    try:
        senders_location = f"Широта: {latitude}, Долгота: {longitude}"
    except (AttributeError, NameError):
        senders_location = "Местоположение не определено"
    await call.bot.send_message(
        chat_id=call.message.chat.id,
        text="Опишитие что произошло",
        reply_to_message_id=call.message.message_id
    )
    try:
        add_incidient(TypeInc, sender_id, sender_name, senders_location,
                      datetime.datetime.fromtimestamp(performed_date))
    except Exception:
        await call.answer(
            text="Что-то пошло не так, попробуйте заново"
        )


@dp.callback_query(F.data == 'setDispatcher')
async def cb_set_dispatcher(call: CallbackQuery):
    Str = call.message.text
    symbols_to_remove = "(') "
    for symbol in symbols_to_remove:
        Str = Str.replace(symbol, "")
    list = Str.split(",")
    with open(file="dispatchers_list.txt", mode="a") as f:
        f.writelines(str(list[1])+'\n')
    get_user_by_id(list[0])
    await call.answer(
        text="Пользователь назначен диспетчером!",
    )


@dp.callback_query(F.data == 'deleteDispatcher')
async def cb_delete_dispatcher(call: CallbackQuery):
    # with open(file="dispatchers_list.txt", mode="r") as f:
    #     lines = f.readlines()

    Str = call.message.text
    symbols_to_remove = "(') "
    for symbol in symbols_to_remove:
        Str = Str.replace(symbol, "")
    list = Str.split(",")
    #
    # update_line = []
    # for line in lines:
    #     if line.strip() != list[1]:
    #         update_line.append(line.strip())
    #
    # with open(file="dispatchers_list.txt", mode="w") as f:
    #     f.write("\n".join(update_line))
    delete_dispatcher(list[0])
    await call.answer(
        text="Диспетчер удален!"
    )


@dp.callback_query(F.data == "fire department")
async def handle_cb_fire_btn(call: CallbackQuery):
    global longitude, latitude
    try:
        if latitude is not None and longitude is not None:
            await call.bot.send_chat_action(
                chat_id=call.message.chat.id,
                action=ChatAction.FIND_LOCATION,
            )
            url = (f"https://search-maps.yandex.ru/v1/?text=fire_department&ll={longitude},{latitude}&type=biz&results"
                   f"=3&lang=ru_RU&apikey={settings.yandex_api_key}")
            response = requests.get(url=url)
            if response.status_code == 200:
                data = json.loads(response.text)
                if "features" in data:
                    for feature in data["features"]:
                        geometry = feature["geometry"]
                        coord = geometry.get("coordinates", "Координаты не найдены")
                        r = 6371
                        lat1 = math.radians(latitude)
                        lon1 = math.radians(longitude)
                        lat2 = math.radians(coord[1])
                        lon2 = math.radians(coord[0])

                        dlat = lat2 - lat1
                        dlon = lon2 - lon1

                        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

                        dist = r * c

                        if "properties" in feature and "CompanyMetaData" in feature["properties"]:
                            company_metadata = feature["properties"]["CompanyMetaData"]
                            name = company_metadata.get("name", "Название не найдено")
                            address = company_metadata.get("address", "Адрес не найден")
                            phones = [phone["formatted"] for phone in company_metadata.get("Phones", [])]

                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Название: {name}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Адрес: {address}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Телефоны: {', '.join(phones)}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Расстояние до места: {round(dist, 2)} км"
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text="-----------------------------"
                            )
                            await asyncio.sleep(1)
                        else:
                            print("Не удалось найти информацию о компании")
                else:
                    print("Отсутствуют объекты (features) в JSON-ответе")
            else:
                print("Ошибка в запросе: ", response.status_code)
        else:
            await call.answer(
                text="Отправьте пожалуйста вашу позицию",
            )
    except NameError:
        await call.answer(
            text="Отправьте пожалуйста вашу позицию",
        )


@dp.callback_query(F.data == "police station")
async def handle_cb_police_btn(call: CallbackQuery):
    global longitude, latitude
    try:
        if latitude is not None and longitude is not None:
            await call.bot.send_chat_action(
                chat_id=call.message.chat.id,
                action=ChatAction.FIND_LOCATION,
            )
            url = f"https://search-maps.yandex.ru/v1/?text=police_station&ll={longitude},{latitude}&type=biz&results=3&lang=ru_RU&apikey={settings.yandex_api_key}"
            response = requests.get(url=url)
            if response.status_code == 200:
                data = json.loads(response.text)
                if "features" in data:
                    for feature in data["features"]:
                        geometry = feature["geometry"]
                        coord = geometry.get("coordinates", "Координаты не найдены")
                        r = 6371
                        lat1 = math.radians(latitude)
                        lon1 = math.radians(longitude)
                        lat2 = math.radians(coord[1])
                        lon2 = math.radians(coord[0])

                        dlat = lat2 - lat1
                        dlon = lon2 - lon1

                        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

                        dist = r * c

                        if "properties" in feature and "CompanyMetaData" in feature["properties"]:
                            company_metadata = feature["properties"]["CompanyMetaData"]
                            name = company_metadata.get("name", "Название не найдено")
                            address = company_metadata.get("address", "Адрес не найден")
                            phones = [phone["formatted"] for phone in company_metadata.get("Phones", [])]

                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Название: {name}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Адрес: {address}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Телефоны: {', '.join(phones)}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Расстояние до места: {round(dist, 2)} км"
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text="-----------------------------"
                            )
                            await asyncio.sleep(1)
                        else:
                            print("Не удалось найти информацию о компании")
                else:
                    print("Отсутствуют объекты (features) в JSON-ответе")
            else:
                print("Ошибка в запросе: ", response.status_code)
        else:
            await call.answer(
                text="Отправьте пожалуйста вашу позицию",
            )
    except NameError:
        await call.answer(
            text="Отправьте пожалуйста вашу позицию",
        )


@dp.callback_query(F.data == "hospital")
async def handle_cb_emergency_btn(call: CallbackQuery):
    global longitude, latitude
    try:
        if latitude is not None and longitude is not None:
            await call.bot.send_chat_action(
                chat_id=call.message.chat.id,
                action=ChatAction.FIND_LOCATION,
            )
            url = f"https://search-maps.yandex.ru/v1/?text=hospital&ll={longitude},{latitude}&type=biz&results=3&lang=ru_RU&apikey={settings.yandex_api_key}"
            response = requests.get(url=url)
            if response.status_code == 200:
                data = json.loads(response.text)
                if "features" in data:
                    for feature in data["features"]:
                        geometry = feature["geometry"]
                        coord = geometry.get("coordinates", "Координаты не найдены")
                        r = 6371
                        lat1 = math.radians(latitude)
                        lon1 = math.radians(longitude)
                        lat2 = math.radians(coord[1])
                        lon2 = math.radians(coord[0])

                        dlat = lat2 - lat1
                        dlon = lon2 - lon1

                        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

                        dist = r * c

                        if "properties" in feature and "CompanyMetaData" in feature["properties"]:
                            company_metadata = feature["properties"]["CompanyMetaData"]
                            name = company_metadata.get("name", "Название не найдено")
                            address = company_metadata.get("address", "Адрес не найден")
                            phones = [phone["formatted"] for phone in company_metadata.get("Phones", [])]

                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Название: {name}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Адрес: {address}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Телефоны: {', '.join(phones)}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Расстояние до места: {round(dist, 2)} км"
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text="-----------------------------"
                            )
                            await asyncio.sleep(1)
                        else:
                            print("Не удалось найти информацию о компании")
                else:
                    print("Отсутствуют объекты (features) в JSON-ответе")
            else:
                print("Ошибка в запросе: ", response.status_code)
        else:
            await call.answer(
                text="Отправьте пожалуйста вашу позицию",
            )
    except NameError:
        await call.answer(
            text="Отправьте пожалуйста вашу позицию",
        )


@dp.callback_query(F.data == "gas service")
async def handle_cb_gas_btn(call: CallbackQuery):
    global longitude, latitude
    try:
        if latitude is not None and longitude is not None:
            await call.bot.send_chat_action(
                chat_id=call.message.chat.id,
                action=ChatAction.FIND_LOCATION,
            )
            url = f"https://search-maps.yandex.ru/v1/?text=gas_service&ll={longitude},{latitude}&type=biz&results=3&lang=ru_RU&apikey={settings.yandex_api_key}"
            response = requests.get(url=url)
            if response.status_code == 200:
                data = json.loads(response.text)
                if "features" in data:
                    for feature in data["features"]:
                        geometry = feature["geometry"]
                        coord = geometry.get("coordinates", "Координаты не найдены")
                        r = 6371
                        lat1 = math.radians(latitude)
                        lon1 = math.radians(longitude)
                        lat2 = math.radians(coord[1])
                        lon2 = math.radians(coord[0])

                        dlat = lat2 - lat1
                        dlon = lon2 - lon1

                        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

                        dist = r * c

                        if "properties" in feature and "CompanyMetaData" in feature["properties"]:
                            company_metadata = feature["properties"]["CompanyMetaData"]
                            name = company_metadata.get("name", "Название не найдено")
                            address = company_metadata.get("address", "Адрес не найден")
                            phones = [phone["formatted"] for phone in company_metadata.get("Phones", [])]

                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Название: {name}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Адрес: {address}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Телефоны: {', '.join(phones)}",
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text=f"Расстояние до места: {round(dist, 2)} км"
                            )
                            await call.bot.send_message(
                                chat_id=call.message.chat.id,
                                text="-----------------------------"
                            )
                            await asyncio.sleep(1)
                        else:
                            print("Не удалось найти информацию о компании")
                else:
                    print("Отсутствуют объекты (features) в JSON-ответе")
            else:
                print("Ошибка в запросе: ", response.status_code)
        else:
            await call.answer(
                text="Отправьте пожалуйста вашу позицию",
            )
    except NameError:
        await call.answer(
            text="Отправьте пожалуйста вашу позицию",
        )


@dp.message(F.text.contains("Ул") | F.text.contains("ул"))
async def incidient_place(msg: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Да", callback_data="add_street")
    builder.button(text="Нет", callback_data="edit_message")
    builder.adjust(2)
    place = msg.text
    await msg.answer(
        text=f"Это произошло на {place}",
        reply_markup=builder.as_markup(),
    )


@dp.message()
async def incidient_discription(msg: types.Message):
    try:
        senders_location = f"Широта: {latitude}, Долгота: {longitude}"
    except (AttributeError, NameError):
        senders_location = "Местоположение не определено"
    global description, TypeInc
    description = msg.text
    performed_date = time.time()
    if TypeInc is None:
        print(TypeInc)
        await msg.answer(
            text="Пожалуйста нажмите /call"
        )
        return
    else:
        if description is not None:
            add_description_to_incidient(Type=TypeInc, sender_id=msg.from_user.id, sender_name=msg.from_user.first_name,
                                         description=description, sender_location=senders_location,
                                         Date=datetime.datetime.fromtimestamp(performed_date))
            print("Успешно добавлен")
        else:
            await msg.answer(
                text="Введите корректное сообщение"
            )
            return
        await msg.answer(
            text=f"Вы утверждаете что: {description}"
        )

    await msg.answer(
        text="Укажите улицу где это произошло(улица Куйбышева)"
    )


@dp.message(F.from_user.id.in_(dispatchers_list()))
async def periodic_check_updates():
    try:
        new_value = check_for_updates()
        f = open('chat_id.txt', 'r')
        chat_id = f.readline()
        f.close()
        for line in new_value:
            await bot.send_message(
                chat_id=chat_id,
                text=f"Тип: {line[1]}"
            )
            await bot.send_message(
                chat_id=chat_id,
                text=f"id отправителя: {line[2]}"
            )
            await bot.send_message(
                chat_id=chat_id,
                text=f"Имя отправителя: {line[3]}"
            )
            await bot.send_message(
                chat_id=chat_id,
                text=f"Что произоло: {line[4]}"
            )
            await bot.send_message(
                chat_id=chat_id,
                text=f"Местоположение отправителя: {line[5]}"
            )
            await bot.send_message(
                chat_id=chat_id,
                text=f"Где произошло: {line[6]}"
            )
            await bot.send_message(
                chat_id=chat_id,
                text=f"Дата отправки: {line[7]}"
            )
    except UnboundLocalError:
        print("Новых обновлений нет")


async def main():
    logging.basicConfig(
        level=logging.INFO
    )
    create_db()
    # with open(file="dispatchers_list.txt",mode="r") as f:
    #     global dispatchers_list
    #     dispatchers_list = [line.rstrip('\n') for line in f]
    #     print(type(dispatchers_list[-1]))
    #     dispatchers_list = list(map(int, dispatchers_list))
    #     print(dispatchers_list, "\n", type(dispatchers_list[-1]))

    loop = asyncio.get_event_loop()
    loop.call_later(150, repeat, periodic_check_updates, loop)
    await dp.start_polling(
        bot,
        loop=loop,
    )


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(150, repeat, coro, loop)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, CancelledError):
        pass
