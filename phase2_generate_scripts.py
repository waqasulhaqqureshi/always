#!/usr/bin/env python3
"""
Phase 2: Generate & Strictly Validate Two 8-Minute @film.feel.50-Style Recap Scripts
(8 x 1-minute parts for ElevenLabs) in:
  1. Roman Urdu / Hindi (script_roman_urdu_hindi.txt & .json)
  2. Roman Arabic (Egyptian / White Arabic) (script_roman_arabic.txt & .json)

Strict validation rules:
  - Exactly 8 parts (00:00 - 01:00 through 07:00 - 08:00)
  - 150 to 165 words per 1-minute part (~160 WPM pacing)
  - ZERO digits (0-9) or Arabizi digit-substitutes anywhere in spoken text
  - ZERO brackets or stage directions inside spoken paragraphs (only [end] at the very end of Part 8)
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

TIME_RANGES = [
    ("00:00", "01:00"),
    ("01:00", "02:00"),
    ("02:00", "03:00"),
    ("03:00", "04:00"),
    ("04:00", "05:00"),
    ("05:00", "06:00"),
    ("06:00", "07:00"),
    ("07:00", "08:00"),
]

# ==============================================================================
# 1. ROMAN URDU / HINDI SCRIPT (Mahira Khan as Billo, Wahaj Ali as Baala)
# ==============================================================================
URDU_PARTS = [
    # PART 1 (00:00 - 01:00)
    (
        "Ek aurat kaale kapdon mein mannat ka roza rakh kar kisi ki maut ka intezar kar rahi hai, "
        "aur usi lamhe ek aisa qaidi jail se bahar nikalta hai jise dekh kar poori jail usay kisi badshah ki tarah salaam karti hai. "
        "Lekin bahar nikalte hi qabristan mein us par goliyon ki baarish ho jaati hai. "
        "Aakhir kaun hai yeh aurat, aur is aadmi ke saath iska kya purana hisaab baqi hai? "
        "Aaj ki kahani hai Mitti De Baway ki, jahan Punjab ki zarkhez mitti sirf faslein nahi ugati, "
        "balkay yahan ishq ki daastanein bhi janam leti hain aur khoon mein doobi dushmaniyan bhi. "
        "Yahan mohabbat ho ya nafrat, dono dil ki gehrai se nibhayi jaati hain. "
        "Kahani shuru hoti hai saal unnees sau ninnanve se. "
        "Jail ki andheri rahdari mein ek shakhs kaale libaas mein chal kar aa raha hai. "
        "Yeh hai Iqbal Channan, jise poori duniya Baala ke naam se jaanti hai."
    ),
    # PART 2 (01:00 - 02:00)
    (
        "Jail ki salakhon ke peeche khade saare qaidi Baala ko dekh kar naare laga rahe hain, "
        "jaise koi aam mujrim nahi balkay koi azeem hero riha ho raha ho. "
        "Doosri taraf manzar badalta hai aur hum dekhte hain Bilqees Bano ko, jise kabhi sab Billo kehte thay. "
        "Kaale libaas mein lipti Billo apni dargah mein haath utha kar dua maang rahi hai, "
        "aur uske gird darjanon auratein adab se sir jhukaye baithi hain. "
        "Idhar jail ka bhari lohe ka darwaza khulta hai aur Baala azaad hawa mein qadam rakhta hai. "
        "Bahar uska chhota bhai Jooji aur uske wafadar log usay gale laga kar khushiyan manaate hain. "
        "Lekin Baala seedha ghar jaane ke bajaye qabristan chala jaata hai, "
        "jahan woh apne pyaron ki qabr par paani daal kar fatiha padhta hai. "
        "Udhar dargah mein jab khadima Billo ke liye khana laati hai, to woh sard lehje mein kehti hai, "
        "wapas le jao, mera mannat ka roza hai, aur yeh mannat poori hone par hi khulega."
    ),
    # PART 3 (02:00 - 03:00)
    (
        "Abhi Baala qabr ke paas khada dua kar hi raha hota hai ke qabristan ka sannata achanak barood mein badal jaata hai. "
        "Qabron ke peeche se hatyarband hamla-awar nikalte hain aur seedha Baala par kalashnikov taan lete hain. "
        "Baala chillata hai ke Jooji yahan se bhaag jao, magar wafadar bhai apne bade bhai ko akela chhodne se inkaar kar deta hai. "
        "Achanak goliyon ki ghan-garaj se poora qabristan goonj uthta hai. "
        "Theek usi lamhe Billo apni safaid dargah ke bahar khamosh khadi hai, uski aankhon mein na koi darr hai na koi reham. "
        "Qabristan mein ek ke baad ek goli chalti hai. "
        "Jooji khoon mein latpath ho kar mitti par gir padta hai, aur phir Baala khud bhi zakhmi ho kar zameen par dher ho jaata hai. "
        "Udhar dargah ke sehan mein khadi Billo sukoon se apni aankhein band kar leti hai, "
        "jaise qabristan mein behne wale khoon ne aakhirkar uski barson purani mannat poori kar di ho."
    ),
    # PART 4 (03:00 - 04:00)
    (
        "Camera qabristan ke upar uthta hai aur kahani kai saal peeche flashback mein chali jaati hai, "
        "us daur mein jab Baala ke haath mein bandook nahi thi aur na us par kisi qatl ka ilzaam tha. "
        "Yeh woh waqt hai jab Iqbal Channan ek shareef aur izzatdar kapde ka tajir hota hai. "
        "Uska chhota bhai Jooji hansi khushi motor cycle chalata hua dukan aur ghar sambhalta hai. "
        "Ghar mein Iqbal ki biwi Zareena usay apna purana wada yaad dilati hai ke usay poore chaar tolay ke sone ke kade chahiye. "
        "Iqbal narmi se kehta hai ke pehle meri behan Kausar ke nikah ki tareekh pakki ho jaye, "
        "phir uske zewaron ke saath tumhare kade bhi ban jayenge. "
        "Jab Zareena shikwa karti hai to Iqbal saaf kehta hai ke main sirf tumhara shohar nahi hoon, "
        "apne behan bhaiyon ka maa bhi hoon aur baap bhi, aaj jo kuch hai sab unhi ki badolat hai."
    ),
    # PART 5 (04:00 - 05:00)
    (
        "Agle manzar mein Iqbal aur Jooji apni kapde ki dukan par hote hain, jahan achanak ilaqay ke bhatta-khor ghunde aa dhamakte hain. "
        "Jooji ka para charh jaata hai aur woh unhein suna deta hai ke har mahine ki pehli tareekh ko poora hissa bhej diya jaata hai, "
        "ab dobara muft ki kamai khane kyun aa gaye? "
        "Baat haathapai tak pahunch jaati hai aur ghunde Jooji ko dhamki dete hain. "
        "Tabhi Iqbal beech mein aa kar maamla thanda karta hai, unke buzurg se adab se baat karta hai aur Jooji ko rok deta hai. "
        "Baad mein jab Jooji ghusse se kehta hai ke aap unke peeche mujhe daant rahe hain, "
        "to Iqbal use samjhata hai ke hum yahan karobar karne baithe hain, badmashi karne nahi. "
        "Hamein Kausar ki shaadi aur agle saal hajj karna hai, kisi se dushmani nahi chahiye. "
        "Kise pata tha yeh aman pasand aadmi ek din sab se khatarnak dushman ban jayega."
    ),
    # PART 6 (05:00 - 06:00)
    (
        "Idhar mohallay mein achanak halchal mach jaati hai jab safaid gaadiyon ka ek bada qafila Shah sahab ki haveli ke bahar aa kar rukta hai. "
        "Mohallay ki auratein bhaag kar dekhti hain aur pata chalta hai ke mashhoor buzurg Wadde Sarkar khud Shahon ke ghar tashreef laye hain. "
        "Doosri taraf Iqbal jab ghar aata hai to apne bete Ibrahim ko gaane sunte dekh kar barham ho jaata hai, "
        "kyunkay usay hamesha darr rehta hai ke kahin log uske khandan ke purane bhaand peshe ka taana na maar dein. "
        "Zareena muskurate hue kehti hai ke Ibrahim bilkul apne chacha Jooji ki tarah ziddi hai, "
        "kaash mujhe pehle pata hota to main usay Wadde Sarkar se dam karwa laati. "
        "Udhar Shahon ki haveli mein Wadde Sarkar unki nayi bahu ki ibadat aur parhezgari ki tareef karte hain "
        "aur usay khabardar karte hain ke is raaste par chalne walon ke saamne badi aazmaishein aati hain, "
        "magar ghabrana mat, kyunkay wahi aazmaishein tumhein kundan bana dengi."
    ),
    # PART 7 (06:00 - 07:00)
    (
        "Shahon ki haveli ki yeh baat agle hi pal Iqbal ke sehan mein toofan le aati hai. "
        "Zareena baaton mein Iqbal ko batati hai ke Wadde Sarkar ne Shahon ki bahu par khaas inayat ki hai, "
        "aur ab mohallay ki saari ladkiyan usi nek aurat se Quran padhti hain. "
        "Iqbal aam andaaz mein sun raha hota hai, magar tabhi Zareena uska naam leti hai, "
        "Bilqees, wahi Bilqees Bano jo Wazirabad se Shahon ke ghar byah kar aayi hai. "
        "Yeh naam sunte hi Iqbal ke chehre ka rang ud jaata hai aur haath wahin tham jaate hain. "
        "Woh bina khana khaye khamoshi se uth kar bahar nikal jaata hai aur Zareena hairan reh jaati hai. "
        "Bechain qadmon se purani galiyon mein chalte hue Iqbal achanak ruk jaata hai "
        "jab safaid chadar mein lipti ek aurat Shahon ki haveli mein daakhil hoti hai. "
        "Upar khidki par wahi Bilqees khadi hai jiska naam aaj bhi Iqbal ka sukoon chheen leta hai."
    ),
    # PART 8 (07:00 - 08:00)
    (
        "Lekin asli jhatka abhi baqi tha. "
        "Shahon ki haveli ke andar Bilqees ka shohar Nazeer Shah khamosh baitha hai jab ghar ki ek ladki poochti hai "
        "ke kal aap ki shaadi ki saalgirah hai, bhabhi ko kya tohfa denge? "
        "Nazeer ka chehra sakht ho jaata hai aur woh sard lehje mein kehta hai "
        "ke tum ab bachi nahi rahi, achhi tarah jaanti ho ke hamari shaadi ki saalgirah ke din hi Bilqees ke bhai ki barsi hoti hai. "
        "Yeh ek jumla poori kahani ko khoon aur raaz se jod deta hai. "
        "Raat dhalne par Iqbal khamosh ghar lautta hai, apni soti hui biwi aur bache ko dekhta hai, "
        "aur andheri chhat par ja kar maazi ki yaadon mein kho jaata hai. "
        "Wazirabad ki purani hansi, jawan Billo aur Baala ka adhoora ishq, sab uski aankhon mein aag ban kar jalne lagta hai. "
        "Aakhir Bilqees ke bhai ke qatl ka raaz kya hai? Agli qist mein sab khulega. [end]"
    ),
]

# ==============================================================================
# 2. ROMAN ARABIC SCRIPT (Natural Egyptian / White Arabic, ZERO Arabizi digits!)
# ==============================================================================
ARABIC_PARTS = [
    # PART 1 (00:00 - 01:00)
    (
        "Fi set labsa eswed fi eswed, sayma siyam nedr w mestaneya khabar moot ragel wahed bas. "
        "W fi nafs el lahza di, el ragel da beyokhrog men el segn w kol el masageen beyeheyooh kaeno malek mesh mogrem. "
        "Laken awel ma yewsal el maqaber, el rasas beyenzil aaleeh zay el matar. "
        "Meen el set di, w meen el ragel da, w leeh el hob el qadeem ethawel li aadaawa kolaha dam? "
        "Hekayetna el naharda men mosalsal Mitti De Baway, fi ard el Punjab elli mesh bas betezraa el khair, "
        "di kaman betezraa qesas hob aazema w qesas enteqam ma betenteheesh abadan. "
        "Hena el hob aw el korh, el etneen beyetamelou men el qalb b kol sedq. "
        "El qesa betebda sanat alf tisaamiya tisaa w tiseen. "
        "Gowa mamarrat el segn el modlema, ragel b daqn w galabeya soda beyemshi b thabat ghareeb. "
        "Da Iqbal Channan, elli el nas kolaha betkhaf men esmo w betnadeeh Baala."
    ),
    # PART 2 (01:00 - 02:00)
    (
        "El masageen wara el qodban beyehatfou b esm Baala w beyodroboo aala el hadeed kaeno batal qawmi khareg men el harb. "
        "W fi nafs el waqt, el mashhad beyenqelna li makan tani khales, le Bilqees Bano, elli zaman kan esmaha Billo. "
        "Labsa eswed b el kamel gowa el maqam betaaaha, rafaa edeiha b tadaraa w hawalaiha setat keteer beyesmaou kalamha b ehteram w khashya. "
        "Nergaa tani lel segn, el bawaba el hadeed el teqeela betetfeteh w Baala beyokhrog lel noor. "
        "Barrah beyelaqi akhooh el soghayar Jooji w reggalto mestaneyeeno b el ahdan w el farah. "
        "Laken badal ma yerouh beito, Baala beyemshi aala tool aala el maqaber, "
        "beyoshosh mayya aala qabr ahlo w beyerfaa eedo yeqra el fatiha. "
        "W fi nafs el waqt, el khadama betgeeb el akl le Billo, fa betqolaha b broud shadid, "
        "rageei el akl da, ana sayma siyam nedr, w mesh haftar gheir lamma el nedr betaaie yetehaqqaq."
    ),
    # PART 3 (02:00 - 03:00)
    (
        "W Baala lissa waqef odam el qabr beyedee b kol khoshoo, el hodoo betaa el maqaber beyetqeleb fagaah li sahat harb haqiqiya. "
        "Reggala mosallaheen beyotlaou fagaah men wara el qoboor el qadeema w beyewaggeo benadeq el kalashnikov aala Baala mobasharatan. "
        "Baala beyesrakh fi Jooji b aala soto w yeqolo ehreb men hena besoraa, "
        "laken el akh el wafi beyerfod yeseeb akhooh el kebeer lewahdo f el khatar. "
        "El nar betetfeteh men kol etegah w soot el rasas beyemla el sama w beyehaz el ard. "
        "Fi nafs el thaneya di, Billo betokhrog toqaf barrah el maqam el abyad b sokoon moreeb, "
        "w fi aeineiha nazra barda ma feehash la khof wala rahma. "
        "Gowa el maqaber, el rasas beyeseeb Jooji w beyoqaa aala el ard gharaqan fi dammo, "
        "w baadaha Baala nafso beyetdarab w beyoqaa aala wesho f el torab. "
        "W henak odam el maqam, Billo betghammad aeineiha b raha ghareeba, "
        "kaen el dam elli saal f el maqaber kan egaba le doaaaha men seneen taweela."
    ),
    # PART 4 (03:00 - 04:00)
    (
        "El kamira betetlaa fooq el maqaber el hadya w betergaa bina seneen keteera lewara f el madi, "
        "qabl el segn w qabl el selah w qabl kol el dam w el enteqam da. "
        "Hena benshoof Iqbal Channan el haqiqi qabl ma yebqa Baala el ragel el mokheef, "
        "tager qomash tayeb w mohtaram beyeshtaghal b aaraq gabeeno aashan yebni hayat hadea w sharifa. "
        "Akhooh el soghayar Jooji shab tayesh w dammo khafeef beyerakab el motosikl b farha w beyesaed akhooh f kol shoghl el mahal. "
        "F el beit, merato Zareena elli bethebbo geddan betfakaro b waado el qadeem enno yegiblaha ghawayesh dahab arbaa tola kamleen. "
        "Iqbal beyerod aaleiha b hodoo w haniya enno awel ma yekhalas gawaz okhto Kausar hayeamilaha el ghawayesh maaa shabket okhto. "
        "Lamma Zareena betezal shwaya, Iqbal beyefahimha b kol saraaha enno mesh bas gozha, "
        "howa el ab w el om le ekhwato, w kol kheir howa feeh el naharda sababo waqfet ekhwato ganbo tool aomro."
    ),
    # PART 5 (04:00 - 05:00)
    (
        "Baad keda benshoof Iqbal w Jooji gowa mahal el qomash el zahma, "
        "w fagaah beyedkhol aaleihom baltagiya men el mantaqa talbeen felous zyada men gheir haq. "
        "Jooji beyetganen w beyesrakh feehom enno kol awwel shahr el etaawa betewsalhom kamla men gheir taakheer, "
        "f leeh gayeen delwaqti yaklou taab gheirhom b el haram w el baltaga? "
        "El kalam beyekbar w el khinaqa beteqarab men el darb, w el baltagiya beyehaddedoo Jooji b kol waqaha. "
        "Laken Iqbal beyedkhol f el noss b aql w hodoo shadid, "
        "beyebed akhooh w beyekallem kebeer el baltagiya b ehteram aashan yenhi el moshkela qabl ma tekbar. "
        "Baad ma yemshou, Jooji beyetadeq enno akhooh zaalo odamhom, "
        "fa Iqbal beyeqolo gomla hatetradad f balna tool el qesa, "
        "ehna aadeen hena aashan netager mesh aashan naamel baltaga, "
        "warana gawaz Kausar w el hag el sana el gayya w ma yenfaash naadi had. "
        "Ya tara eih elli hayehawel el ragel el mosalem da li akhtar mogrem f el Punjab?"
    ),
    # PART 6 (05:00 - 06:00)
    (
        "Barrah f el sharee, fagaah el hara kolaha betetqeleb lamma mawkeb arabeyat beida kebeer beyewsal odam qasr aaelet el Shah el ghaniya. "
        "El setat f el shawaree beyegrou yeshofou meen elli gah, w beyetlaa enno el sheikh el mashhoor Wadde Sarkar "
        "zaar beit el Shah elli homma men aham w aqdam morideenoh. "
        "Gowa beit Iqbal, Iqbal beyergaa mel shoghl taaban w beyetassab aala ebno el soghayar Ibrahim aashan beyesmaa aghani, "
        "leanno dayman khayef el nas taayro b madi aaeleto el qadeem f el ghona w el tarab. "
        "Zareena betedhak w betqool enno Ibrahim talee aaneed zay aammo Jooji b el zabt, "
        "w kanet tetmanna takhdo men wedno le Wadde Sarkar yeqra aaleeh w yebareklo. "
        "W gowa qasr el Shah, Wadde Sarkar beyemdah merat ebn el Shah el gedida aala taqwaha w ebadetha, "
        "w beyehazarha enno elli beyemshi f el tareeq da beyewageh ekhtebarat saaba geddan, "
        "laken lazem tesbot aashan el ekhtebarat di hatkhaleeha dahab safi."
    ),
    # PART 7 (06:00 - 07:00)
    (
        "El kalam el basiit da hayeqleb hayat Iqbal ras aala aaqab baad daqayeq waheda bas men gheir ma yehses. "
        "Gowa hosh beit Iqbal, Zareena betehki b hamas enno Wadde Sarkar edda baraka khasa le aarouset beit el Shah, "
        "el set el saleha elli kol banat el mantaqa beyerouhou yetalemou minha el Quran kol youm. "
        "Iqbal kan samee w mesh markez abadan, laken fagaah Zareena betentaq el esm elli beyewaqaf qalbo f thaneya, "
        "Bilqees, Bilqees Bano elli gat aarousa men Wazirabad le beit el Shah. "
        "Awel ma yesmaa el esm, wesh Iqbal beyesfar w eedo betewqaf f el hawa kaen el zaman weqef. "
        "Beyeqoom men gheir ma yakol wala loqma w beyokhrog men el beit sakt, w Zareena waqfa mesh fahma eih elli hasal. "
        "Iqbal beyemshi dayekh f el shawaree el qadeema lehad ma yelmaa set labsa shaal abyad dakhlah bawabet beit el Shah. "
        "Beyewqaf metsammar w beyebos aala el shebbak, henak waqfa Bilqees elli wogoudha lesa beyehaz kayano."
    ),
    # PART 8 (07:00 - 08:00)
    (
        "Laken el mofagaa el akbar w el asdam kanet lissa mestaneyana gowa qasr el Shah. "
        "Nazeer Shah, goz Bilqees, aaeed sakt w sharid lamma bent men el aaila betesaalo b kol baraaa, "
        "bokra aeed gawazkom ya Nazeer, ya tara hatgeeb eih hedia helwa le meratak? "
        "Wesh Nazeer beyetqeleb f lahza w beyerod aaleiha b ghadab maktoum w soot bared, "
        "enti ma baqeeteesh tefla soghayara, w aarfa kwayes enno nafs youm aeed gawazna howa youm zekra wafat akhou Bilqees. "
        "El gomla di betefaggar alf soaal w betorbot kol el kheyout b baad, hob mamnoo, sharaf magrouh, w dam aomro ma etnasa. "
        "B el leil, Iqbal beyergaa beito b hodoo, beyebos aala merato w ebno el naymeen, "
        "w beyetlaa el balakona f el dalma wahdo. "
        "Zekrayat Wazirabad betehgem aaleeh, dehk Billo w Baala zaman qabl el firaq w el nar elli fi aeineeh delwaqti. "
        "Eih serr qatl akhou Bilqees w ezzay el hob da wesselhom lel maqaber? Estannou el halaqa el gayya. [end]"
    ),
]


def count_spoken_words(text: str) -> int:
    # Exclude trailing [end] marker when counting spoken words
    cleaned = re.sub(r"\[end\]", "", text).strip()
    return len([w for w in cleaned.split() if w])


def validate_script(name: str, parts: list[str]) -> list[dict]:
    assert len(parts) == 8, f"{name}: expected 8 parts, got {len(parts)}"
    records = []
    total_words = 0
    for idx, text in enumerate(parts, 1):
        # Check trailing [end]
        if idx == 8:
            assert text.endswith("[end]"), f"{name} Part 8 must end with [end]"
            check_body = text[:-5]
        else:
            assert "[end]" not in text, f"{name} Part {idx} must not contain [end]"
            check_body = text

        # Strictly ZERO digits 0-9 (no regular numbers, no Arabizi digits)
        digits = re.findall(r"[0-9]", check_body)
        assert not digits, f"{name} Part {idx} contains forbidden digits: {digits}"

        # Strictly ZERO brackets/parentheses/stage directions
        brackets = re.findall(r"[\[\]\(\)\{\}<>]", check_body)
        assert not brackets, f"{name} Part {idx} contains forbidden brackets: {brackets}"

        # Pure English letters + basic punctuation only
        non_ascii = re.findall(r"[^\x20-\x7E]", check_body)
        assert not non_ascii, f"{name} Part {idx} contains non-ASCII characters: {non_ascii}"

        wc = count_spoken_words(text)
        total_words += wc
        print(f"  [{name}] Part {idx} ({TIME_RANGES[idx-1][0]}-{TIME_RANGES[idx-1][1]}): {wc} words")
        assert 150 <= wc <= 165, f"{name} Part {idx} word count {wc} outside strict 150-165 range!"

        records.append({
            "part_number": idx,
            "label": f"PART {idx} ({TIME_RANGES[idx-1][0]} - {TIME_RANGES[idx-1][1]})",
            "start_time": TIME_RANGES[idx - 1][0],
            "end_time": TIME_RANGES[idx - 1][1],
            "start_sec": (idx - 1) * 60,
            "end_sec": idx * 60,
            "word_count": wc,
            "target_wpm": 160,
            "spoken_text": text,
        })
    print(f"  => [{name}] TOTAL: {total_words} words (avg {total_words/8:.1f} WPM) - ALL CHECKS PASSED!\n")
    return records


def save_outputs(slug: str, title: str, language: str, records: list[dict]) -> None:
    txt_lines = []
    for rec in records:
        txt_lines.append(f"--- {rec['label']} ---")
        txt_lines.append(rec["spoken_text"])
        txt_lines.append("")
    txt_path = ROOT / f"script_{slug}.txt"
    txt_path.write_text("\n".join(txt_lines).strip() + "\n", encoding="utf-8")

    payload = {
        "title": title,
        "episode": "Mitti De Baway - Episode 1",
        "style": "@film.feel.50 (Fast-paced, suspenseful, emotional drama recap)",
        "language": language,
        "total_parts": 8,
        "total_duration_sec": 480,
        "total_words": sum(r["word_count"] for r in records),
        "avg_wpm": round(sum(r["word_count"] for r in records) / 8.0, 1),
        "elevenlabs_notes": (
            "Generate 8 separate MP3 files (part1.mp3 through part8.mp3) by pasting each part's "
            "spoken_text into ElevenLabs. Drop them into elevenlabs_audio/ and run merge_audio.bat."
        ),
        "parts": records,
    }
    json_path = ROOT / f"script_{slug}.json"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Saved {txt_path.name} and {json_path.name}")


def main():
    print("Validating Roman Urdu/Hindi script...")
    urdu_records = validate_script("Roman Urdu/Hindi", URDU_PARTS)
    save_outputs(
        "roman_urdu_hindi",
        "Mitti De Baway Episode 1 Recap (Roman Urdu/Hindi)",
        "Roman Urdu / Hindi (Pure Latin Letters)",
        urdu_records,
    )

    print("Validating Roman Arabic script...")
    arabic_records = validate_script("Roman Arabic", ARABIC_PARTS)
    save_outputs(
        "roman_arabic",
        "Mitti De Baway Episode 1 Recap (Roman Arabic)",
        "Roman Arabic - Egyptian/White Dialect (Pure Latin Letters)",
        arabic_records,
    )


if __name__ == "__main__":
    main()
