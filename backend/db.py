"""SQLite database layer and statutory seed data for VALENCE."""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DB_PATH = (
    Path("/tmp/valence.db")
    if os.getenv("VERCEL")
    else Path(__file__).resolve().parent / "valence.db"
)

SEED_STATUTES: list[dict[str, Any]] = [
    {
        "slug": "electricity-disconnection",
        "department": "Electricity Board / DISCOM",
        "violation_title": "Unlawful Power Disconnection Without Prior Written Notice",
        "statute_ref": "Electricity Act 2003, Section 56 & State Supply Code Clause 5.4",
        "sla_days": 1,
        "penalty_note": "Mandatory 15-day prior written notice required before disconnection; ₹250/day officer liability under RTI Act Sec 20.",
        "pio_designation": "Executive Engineer / Public Information Officer, Electricity Distribution Division",
        "keywords": json.dumps([
            "electricity", "power", "meter", "bijli", "wire", "lineman", "current",
            "light", "disconnection", "kaat", "minsaaram", "vidyut", "bijuli", "bill"
        ]),
        "rti_questions": json.dumps([
            "Provide certified copy of the mandatory 15-day prior written disconnection notice served under Section 56 of the Electricity Act, 2003.",
            "Provide the daily work order and field inspection diary of the concerned lineman/Junior Engineer for the date of disconnection.",
            "State the exact recorded consumer ledger balance on the date of disconnection and name/designation of the authorizing officer."
        ]),
        "in_ear_templates": json.dumps({
            "en-IN": "Under Section 56 of the Electricity Act, disconnecting power without a 15-day written notice is illegal. Tell the lineman: I have logged case {case_code} and filed an RTI for today's work order. Restore connection or Section 20 penalties apply.",
            "hi-IN": "बिजली अधिनियम धारा 56 के तहत, 15 दिन के लिखित नोटिस के बिना कनेक्शन काटना गैरकानूनी है। लाइनमैन से कहें: मैंने केस {case_code} दर्ज किया है और आज के वर्क ऑर्डर की आरटीआई दाखिल की है। तुरंत बिजली जोड़ें।",
            "hinglish": "Electricity Act Section 56 ke hisaab se bina 15-day written notice power kaatna illegal hai. Lineman ko bolein: Maine case {case_code} log kar diya hai aur aaj ke work order ki RTI file kar di hai.",
            "ta-IN": "மின்சார சட்டம் பிரிவு 56-ன் படி 15 நாள் எழுத்துப்பூர்வ அறிவிப்பு இல்லாமல் மின் இணைப்பை துண்டிப்பது சட்டவிரோதம். வழக்கு {case_code} மற்றும் தகவல் அறியும் உரிமை மனு பதிவு செய்யப்பட்டுள்ளது என்று கூறுங்கள்.",
            "mr-IN": "वीज कायदा कलम ५६ नुसार १५ दिवसांच्या लेखी नोटीसशिवाय वीज खंडित करणे बेकायदेशीर आहे. लाइनमनला सांगा: मी केस {case_code} नोंदवली आहे आणि आजच्या वर्क ऑर्डरची आरटीआय दाखल केली आहे.",
            "te-IN": "విద్యుత్ చట్టం సెక్షన్ 56 ప్రకారం 15 రోజుల లిఖితపూర్వక నోటీసు లేకుండా కనెక్షన్ కట్ చేయడం చట్టవిరుద్ధం. కేసు {case_code} మరియు RTI దాఖలు చేశానని చెప్పండి.",
            "bn-IN": "বিদ্যুৎ আইন ধারা ৫৬ অনুযায়ী ১৫ দিনের লিখিত নোটিশ ছাড়া সংযোগ কাটা বেআইনি। লাইনম্যানকে বলুন: আমি কেস {case_code} নথিভুক্ত করেছি এবং আজকের ওয়ার্ক অর্ডারের আরটিআই দাখিল করেছি।"
        }),
    },
    {
        "slug": "municipal-water-cut",
        "department": "Municipal Water Supply Department",
        "violation_title": "Arbitrary Water Cutoff & Unreceipted Fee Demand",
        "statute_ref": "Municipal Corporation Act, Section 178 & Citizen Charter Clause 3",
        "sla_days": 2,
        "penalty_note": "7-day written notice mandatory prior to water cutoff; unreceipted cash demands violate Prevention of Corruption Act Sec 7.",
        "pio_designation": "Assistant Engineer / PIO, Water Works & Municipal Supply Zone",
        "keywords": json.dumps([
            "water", "paani", "pani", "pipeline", "tap", "nal", "valve", "tanker",
            "drain", "sewer", "thanni", "neeru", "jol", "jal"
        ]),
        "rti_questions": json.dumps([
            "Provide certified copies of the 7-day prior written notice issued before disconnecting the municipal water supply.",
            "Provide the official receipt register and daily field inspection log of the ward water inspector for the date of action.",
            "State the statutory provision permitting any cash collection without a machine-generated municipal receipt."
        ]),
        "in_ear_templates": json.dumps({
            "en-IN": "Under Municipal Act Section 178, water supply cannot be cut without prior written notice, and cash fees without receipts are illegal. Tell the official: I have logged case {case_code} and filed an RTI for your ward inspection diary.",
            "hi-IN": "नगर निगम अधिनियम धारा 178 के तहत बिना लिखित नोटिस पानी बंद करना और बिना रसीद पैसे मांगना गैरकानूनी है। अधिकारी से कहें: मैंने केस {case_code} और आरटीआई दर्ज कर दी है।",
            "hinglish": "Municipal Act Section 178 ke under bina written notice paani band karna aur bina receipt cash maangna illegal hai. Officer ko bolein: Maine case {case_code} log karke inspection log ki RTI daal di hai.",
            "ta-IN": "நகராட்சி சட்டம் பிரிவு 178-ன் படி எழுத்துப்பூர்வ அறிவிப்பு இல்லாமல் குடிநீர் இணைப்பை துண்டிப்பது சட்டவிரோதம். ரசீது இல்லாமல் பணம் கேட்க முடியாது. வழக்கு {case_code} பதிவு செய்யப்பட்டுள்ளது.",
            "mr-IN": "महापालिका कायदा कलम १७८ नुसार लेखी नोटीसशिवाय पाणीपुरवठा बंद करणे बेकायदेशीर आहे. पावतीशिवाय पैसे मागता येत नाहीत. मी केस {case_code} आणि आरटीआय दाखल केली आहे.",
            "te-IN": "మున్సిపల్ చట్టం సెక్షన్ 178 ప్రకారం నోటీసు లేకుండా నీటి సరఫరా ఆపడం మరియు రసీదు లేకుండా డబ్బు అడగడం చట్టవిరుద్ధం. కేసు {case_code} నమోదైంది అని చెప్పండి.",
            "bn-IN": "পৌর আইন ধারা ১৭৮ অনুযায়ী লিখিত নোটিশ ছাড়া জল সরবরাহ বন্ধ করা এবং রসিদ ছাড়া টাকা চাওয়া বেআইনি। বলুন: আমি কেস {case_code} এবং আরটিআই দায়ের করেছি।"
        }),
    },
    {
        "slug": "traffic-rto-extortion",
        "department": "Traffic Police / Regional Transport Office (RTO)",
        "violation_title": "Illegal Key Seizure or Unreceipted Challan Demand",
        "statute_ref": "Motor Vehicles Act 1988, Sections 130, 158 & Prevention of Corruption Act Sec 7",
        "sla_days": 3,
        "penalty_note": "Officers cannot remove vehicle keys or demand cash without an official e-Challan receipt; DigiLocker documents are legally valid.",
        "pio_designation": "Public Information Officer, Office of DCP Traffic / Regional Transport Officer",
        "keywords": json.dumps([
            "traffic", "police", "cop", "rto", "license", "licence", "challan", "bike",
            "car", "vehicle", "key", "keys", "chabi", "helmet", "signal", "gaadi", "bribe"
        ]),
        "rti_questions": json.dumps([
            "Provide the official duty roster, body-cam status, and handheld e-Challan machine log for the intersection/counter at the stated time.",
            "Clarify under which rule of the Motor Vehicles Act an officer is empowered to confiscate ignition keys or refuse DigiLocker digital records.",
            "Provide the current pendency and processing log of the applicant's driving license / RC service request."
        ]),
        "in_ear_templates": json.dumps({
            "en-IN": "Under the Motor Vehicles Act, officers cannot seize your vehicle keys or force cash without an official e-Challan receipt. Tell the officer calmly: Please issue a formal digital e-Challan. Case {case_code} and an RTI for today's duty log are active.",
            "hi-IN": "मोटर वाहन अधिनियम के तहत कोई भी अधिकारी आपकी गाड़ी की चाबी नहीं निकाल सकता और बिना ई-चालान रसीद के नकद पैसे नहीं ले सकता। शांत होकर कहें: कृपया आधिकारिक ई-चालान दें, केस {case_code} दर्ज है।",
            "hinglish": "Motor Vehicles Act ke under police aapki gaadi ki chabi nahi nikal sakti aur bina e-Challan cash nahi maang sakti. Calmly bolein: Sir, official digital e-Challan issue kijiye, mera case {case_code} log ho chuka hai.",
            "ta-IN": "மோட்டார் வாகன சட்டத்தின் கீழ் உங்கள் வாகன சாவியை பறிக்கவோ, இ-சலான் ரசீது இல்லாமல் பணம் கேட்கவோ முடியாது. அதிகாரப்பூர்வ இ-சலான் வழங்குங்கள், வழக்கு {case_code} பதிவாகியுள்ளது என்று கூறுங்கள்.",
            "mr-IN": "मोटार वाहन कायद्यानुसार पोलीस तुमच्या गाडीची चावी काढू शकत नाहीत किंवा ई-चलनशिवाय रोख रक्कम मागू शकत नाहीत. शांतपणे सांगा: कृपया अधिकृत ई-चलन द्या, केस {case_code} नोंदवली आहे.",
            "te-IN": "మోటారు వాహన చట్టం ప్రకారం పోలీసులు మీ వాహనం తాళాలు తీసుకోలేరు, ఈ-చలాన్ లేకుండా నగదు అడగలేరు. అధికారిక ఈ-చలాన్ ఇవ్వండి, కేసు {case_code} నమోదైంది అని చెప్పండి.",
            "bn-IN": "মোটরযান আইন অনুযায়ী কোনো পুলিশ গাড়ির চাবি কেড়ে নিতে বা ই-চালান রসিদ ছাড়া নগদ টাকা চাইতে পারে না। শান্তভাবে বলুন: অনুগ্রহ করে অফিসিয়াল ই-চালান দিন, কেস {case_code} নথিভুক্ত হয়েছে।"
        }),
    },
    {
        "slug": "certificate-office-bribe",
        "department": "Revenue / Tehsil / Municipal Licensing Desk",
        "violation_title": "Delay Beyond Citizen Charter SLA & Informal Fee Demand",
        "statute_ref": "Right to Public Services Act & Prevention of Corruption Act, Section 7",
        "sla_days": 7,
        "penalty_note": "Delayed certificates beyond statutory Citizen Charter window attract daily officer fines; cash demands carry criminal liability.",
        "pio_designation": "Sub-Divisional Magistrate / PIO, Public Service Delivery Cell",
        "keywords": json.dumps([
            "certificate", "bribe", "cash", "babu", "clerk", "tehsil", "passport",
            "income", "caste", "domicile", "birth", "death", "delay", "pending",
            "rishwat", "ghoos", "paisa", "paise", "lancham", "lanj"
        ]),
        "rti_questions": json.dumps([
            "Provide the file movement register showing exact date-wise movement and officer remarks on the applicant's pending request.",
            "Provide reasons on record under Section 4(1)(d) of the RTI Act for delaying disposal beyond the notified Citizen Charter SLA.",
            "List the names and designations of every clerk/officer who handled this file since submission."
        ]),
        "in_ear_templates": json.dumps({
            "en-IN": "Under the Right to Public Services Act, clerks cannot hold your file past the Charter SLA or ask for cash. Tell the desk: Please give any objection in writing with your desk ID. I have logged case {case_code} and filed a file-movement RTI.",
            "hi-IN": "लोक सेवा गारंटी कानून के तहत बाबू आपकी फाइल तय समय से ज्यादा नहीं रोक सकते। काउंटर पर कहें: अगर कोई कमी है तो अपनी डेस्क आईडी के साथ लिखित में दें, मैंने केस {case_code} और आरटीआई दर्ज कर दी है।",
            "hinglish": "Right to Public Services Act ke under clerk aapki file SLA ke baad rok nahi sakta. Desk par bolein: Koi objection hai toh desk ID ke saath writing mein dijiye, maine case {case_code} aur file-movement RTI file kar di hai.",
            "ta-IN": "பொது சேவை உரிமைச் சட்டத்தின் கீழ் உங்கள் கோப்பை காலதாமதம் செய்யவோ பணம் கேட்கவோ முடியாது. குறைபாடு இருந்தால் எழுத்துப்பூர்வமாக தாருங்கள், வழக்கு {case_code} பதிவு செய்யப்பட்டுள்ளது என்று கூறுங்கள்.",
            "mr-IN": "सेवा हक्क कायद्यानुसार लिपिक तुमची फाईल मुदतीपेक्षा जास्त काळ अडवू शकत नाही. काउंटरवर सांगा: काही त्रुटी असल्यास लेखी द्या, मी केस {case_code} आणि आरटीआय दाखल केली आहे.",
            "te-IN": "ప్రజా సేవా హక్కు చట్టం ప్రకారం మీ ఫైలును గడువు దాటి ఆపలేరు. ఏదైనా అభ్యంతరం ఉంటే డెస్క్ ఐడీతో లిఖితపూర్వకంగా ఇవ్వండి, కేసు {case_code} నమోదైంది అని చెప్పండి.",
            "bn-IN": "জনসেবা অধিকার আইন অনুযায়ী কোনো কর্মী নির্ধারিত সময়ের বেশি ফাইল আটকে রাখতে পারেন না। বলুন: কোনো আপত্তি থাকলে ডেস্ক আইডিসহ লিখিত দিন, আমি কেস {case_code} ও আরটিআই করেছি।"
        }),
    },
    {
        "slug": "police-fir-refusal",
        "department": "Local Police Station / Home Department",
        "violation_title": "Refusal to Register Mandatory FIR / Zero FIR",
        "statute_ref": "Bharatiya Nagarik Suraksha Sanhita (BNSS) Section 173 & Lalita Kumari Supreme Court Mandate",
        "sla_days": 1,
        "penalty_note": "Refusal to register a cognizable offence or Zero FIR regardless of jurisdiction violates mandatory Supreme Court law.",
        "pio_designation": "Public Information Officer, Office of the Superintendent of Police (SP / DCP)",
        "keywords": json.dumps([
            "fir", "thana", "station", "complaint", "theft", "stolen", "assault",
            "harass", "threat", "scam", "fraud", "refused", "report", "cyber"
        ]),
        "rti_questions": json.dumps([
            "Provide the certified extract of the Station House General Diary (GD) entry recorded during the applicant's visit.",
            "State the statutory basis under BNSS Section 173 for declining immediate registration of a Zero FIR / cognizable complaint.",
            "Provide the name of the Duty Officer on shift at the specified date and time."
        ]),
        "in_ear_templates": json.dumps({
            "en-IN": "Under BNSS Section 173 and the Lalita Kumari Supreme Court ruling, police must register a Zero FIR regardless of jurisdiction. Tell the Duty Officer: Please record my complaint in the General Diary and provide an acknowledgment receipt for case {case_code}.",
            "hi-IN": "बीएनएसएस धारा 173 और सुप्रीम कोर्ट के आदेश के अनुसार पुलिस क्षेत्राधिकार का बहाना बनाकर जीरो एफआईआर से मना नहीं कर सकती। कहें: कृपया जनरल डायरी में शिकायत दर्ज कर रसीद दें, केस {case_code} लॉग है।",
            "hinglish": "BNSS Section 173 aur Supreme Court Lalita Kumari ruling ke hisaab se police Zero FIR lene se mana nahi kar sakti. Officer se bolein: Please General Diary mein entry karke receipt dijiye, case {case_code} logged hai.",
            "ta-IN": "BNSS பிரிவு 173 மற்றும் உச்ச நீதிமன்ற தீர்ப்பின் படி எல்லைக் காரணம் காட்டி Zero FIR மறுக்க முடியாது. பொது நாட்குறிப்பில் பதிவு செய்து ரசீது தாருங்கள், வழக்கு {case_code} பதிவு செய்யப்பட்டுள்ளது.",
            "mr-IN": "BNSS कलम १७३ आणि सर्वोच्च न्यायालयाच्या निर्णयानुसार पोलीस झिरो एफआयआर नाकारू शकत नाहीत. अधिकाऱ्याला सांगा: कृपया जनरल डायरीत नोंद करून पावती द्या, केस {case_code} नोंदवली आहे.",
            "te-IN": "BNSS సెక్షన్ 173 మరియు సుప్రీంకోర్టు తీర్పు ప్రకారం పోలీసులు జీరో ఎఫ్ఐఆర్ నమోదు చేయడానికి నిరాకరించలేరు. జనరల్ డైరీలో నమోదు చేసి రసీదు ఇవ్వండి, కేసు {case_code} నమోదైంది.",
            "bn-IN": "BNSS ধারা ১৭৩ এবং সুপ্রিম কোর্টের নির্দেশ অনুযায়ী পুলিশ জিরো এফআইআর নিতে অস্বীকার করতে পারে না। বলুন: জেনারেল ডায়েরিতে অভিযোগ নথিভুক্ত করে রসিদ দিন, কেস {case_code} নথিভুক্ত হয়েছে।"
        }),
    },
    {
        "slug": "civic-sanitation-road",
        "department": "Municipal Engineering & Sanitation Wing",
        "violation_title": "Unresolved Road Hazard, Garbage Dumping, or Open Drain",
        "statute_ref": "Solid Waste Management Rules 2016 & Municipal Citizen Charter",
        "sla_days": 3,
        "penalty_note": "Civic works exceeding 72-hour charter SLA require contractor quality audit and daily supervisor verification under RTI.",
        "pio_designation": "Executive Engineer / PIO, Municipal Public Works & Sanitation Circle",
        "keywords": json.dumps([
            "pothole", "road", "garbage", "trash", "kachra", "drain", "gutter",
            "streetlight", "street", "lamp", "broken", "flood", "sanitation", "sadak"
        ]),
        "rti_questions": json.dumps([
            "Provide the contractor name, tender work order value, and defect-liability warranty period for the mentioned road/ward stretch.",
            "Provide certified copies of quality inspection certificates and payments released to the contractor over the last 6 months.",
            "Provide the ward sanitary/engineering supervisor log for complaints closed without site rectification."
        ]),
        "in_ear_templates": json.dumps({
            "en-IN": "Under the Municipal Citizen Charter, hazardous roads and waste must be cleared within 72 hours. I have compiled case {case_code} with an RTI demanding the contractor's defect-liability warranty and inspection payouts.",
            "hi-IN": "नगर निगम चार्टर के अनुसार खराब सड़क या कचरे का निपटारा 72 घंटे में होना अनिवार्य है। मैंने केस {case_code} तैयार कर लिया है और ठेकेदार की वारंटी व भुगतान जांच की आरटीआई दाखिल कर दी है।",
            "hinglish": "Municipal Citizen Charter ke hisaab se 72 hours mein road aur sanitation action mandatory hai. Maine case {case_code} log karke contractor warranty aur payment ki RTI ready kar di hai.",
            "ta-IN": "நகராட்சி சாசனத்தின் படி 72 மணி நேரத்தில் சாலை மற்றும் சுகாதார பணிகள் முடிக்கப்பட வேண்டும். ஒப்பந்ததாரர் ஆய்வு அறிக்கைக்கான தகவல் அறியும் உரிமை மனு {case_code} தயாராக உள்ளது.",
            "mr-IN": "महापालिका सनदेनुसार ७२ तासांत रस्ता आणि स्वच्छतेची तक्रार सोडवणे बंधनकारक आहे. मी केस {case_code} नोंदवून कंत्राटदाराच्या तपासणीची आरटीआय तयार केली आहे.",
            "te-IN": "మున్సిపల్ చార్టర్ ప్రకారం 72 గంటల్లో రోడ్డు మరియు పారిశుధ్య సమస్యను పరిష్కరించాలి. కాంట్రాక్టర్ తనిఖీ వివరాలపై RTI కేసు {case_code} సిద్ధమైంది.",
            "bn-IN": "পৌর সনদ অনুযায়ী ৭২ ঘণ্টার মধ্যে রাস্তা ও আবর্জনা সমস্যার সমাধান বাধ্যতামূলক। ঠিকাদারের পরিদর্শন নথি চেয়ে কেস {case_code} ও আরটিআই প্রস্তুত করা হয়েছে।"
        }),
    },
]


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create SQLite tables and seed statutory knowledge base if empty."""
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS statutes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                violation_title TEXT NOT NULL,
                statute_ref TEXT NOT NULL,
                sla_days INTEGER NOT NULL,
                penalty_note TEXT NOT NULL,
                pio_designation TEXT NOT NULL,
                keywords TEXT NOT NULL,
                rti_questions TEXT NOT NULL,
                in_ear_templates TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_code TEXT UNIQUE NOT NULL,
                language TEXT NOT NULL,
                transcript TEXT NOT NULL,
                department TEXT NOT NULL,
                violation_title TEXT NOT NULL,
                statute_ref TEXT NOT NULL,
                sla_days INTEGER NOT NULL,
                extortion_amount TEXT,
                location_hint TEXT,
                in_ear_script TEXT NOT NULL,
                rti_draft TEXT NOT NULL,
                grievance_draft TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Drafted',
                engine_mode TEXT NOT NULL DEFAULT 'statutory-rag',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS case_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
            );
            """
        )

        count = conn.execute("SELECT COUNT(*) FROM statutes").fetchone()[0]
        if count == 0:
            for item in SEED_STATUTES:
                conn.execute(
                    """
                    INSERT INTO statutes (
                        slug, department, violation_title, statute_ref, sla_days,
                        penalty_note, pio_designation, keywords, rti_questions, in_ear_templates
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["slug"],
                        item["department"],
                        item["violation_title"],
                        item["statute_ref"],
                        item["sla_days"],
                        item["penalty_note"],
                        item["pio_designation"],
                        item["keywords"],
                        item["rti_questions"],
                        item["in_ear_templates"],
                    ),
                )

        case_count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        if case_count == 0:
            now = datetime.now(timezone.utc).isoformat()
            demo_cases = [
                (
                    "VLC-4092",
                    "hinglish",
                    "Subah municipal lineman ne bina notice water connection kaat diya aur 3000 cash maanga jabki bill paid hai.",
                    "Municipal Water Supply Department",
                    "Arbitrary Water Cutoff & Unreceipted Fee Demand",
                    "Municipal Corporation Act, Section 178 & Citizen Charter Clause 3",
                    2,
                    "₹3,000",
                    "Ward Office",
                    "Municipal Act Section 178 ke under bina written notice paani band karna aur bina receipt cash maangna illegal hai. Officer ko bolein: Maine case VLC-4092 log karke inspection log ki RTI daal di hai.",
                    "FORM A — APPLICATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005\n\nTo,\nThe Public Information Officer (PIO),\nAssistant Engineer, Water Works & Municipal Supply Zone\n\nCase Ref: VLC-4092 | Statutory SLA: 30 Days (Section 7(1)) | Personal Officer Penalty: ₹250/day (Section 20)\n\nSubject: Mandatory Disclosure of Disconnection Order & Inspection Diary\n\nSir/Madam,\nPursuant to Section 6(1) of the RTI Act, 2005, kindly provide:\n1. Certified copies of the 7-day prior written notice issued before disconnecting the municipal water supply.\n2. The official receipt register and daily field inspection log of the ward water inspector.\n3. Statutory provision permitting cash demand of ₹3,000 without machine receipt.\n\nNotice: Non-compliance beyond 30 days attracts personal financial penalty of ₹250/day up to ₹25,000 from the PIO's salary under Section 20(1) of the RTI Act.",
                    "CPGRAMS STATUTORY GRIEVANCE DOSSIER [VLC-4092]\nDepartment: Municipal Water Supply Department\nStatute Invoked: Municipal Corporation Act, Section 178\n\nSummary of Incident:\nSubah municipal lineman ne bina notice water connection kaat diya aur 3000 cash maanga jabki bill paid hai.\n\nImmediate Relief Sought:\nRestore essential water service within 48 hours per Citizen Charter SLA and initiate vigilance check on unreceipted ₹3,000 cash demand.",
                    "RTI Filed",
                    "statutory-rag",
                    now,
                ),
            ]
            for c in demo_cases:
                cur = conn.execute(
                    """
                    INSERT INTO cases (
                        case_code, language, transcript, department, violation_title,
                        statute_ref, sla_days, extortion_amount, location_hint,
                        in_ear_script, rti_draft, grievance_draft, status, engine_mode, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    c,
                )
                conn.execute(
                    "INSERT INTO case_events (case_id, event_type, note, created_at) VALUES (?, ?, ?, ?)",
                    (cur.lastrowid, "RTI Filed", "Seeded verification case", now),
                )


def list_statutes() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM statutes ORDER BY id ASC").fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["keywords"] = json.loads(item["keywords"])
        item["rti_questions"] = json.loads(item["rti_questions"])
        item["in_ear_templates"] = json.loads(item["in_ear_templates"])
        result.append(item)
    return result


def create_case(payload: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO cases (
                case_code, language, transcript, department, violation_title,
                statute_ref, sla_days, extortion_amount, location_hint,
                in_ear_script, rti_draft, grievance_draft, status, engine_mode, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["case_code"],
                payload["language"],
                payload["transcript"],
                payload["department"],
                payload["violation_title"],
                payload["statute_ref"],
                payload["sla_days"],
                payload.get("extortion_amount"),
                payload.get("location_hint"),
                payload["in_ear_script"],
                payload["rti_draft"],
                payload["grievance_draft"],
                payload.get("status", "Drafted"),
                payload.get("engine_mode", "statutory-rag"),
                now,
            ),
        )
        case_id = cur.lastrowid
        conn.execute(
            "INSERT INTO case_events (case_id, event_type, note, created_at) VALUES (?, ?, ?, ?)",
            (case_id, "Case Created", f"Generated via {payload.get('engine_mode', 'statutory-rag')}", now),
        )
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    return dict(row)


def list_cases() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM cases ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def get_case(case_id: int) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        if not row:
            return None
        events = conn.execute(
            "SELECT * FROM case_events WHERE case_id = ? ORDER BY id DESC", (case_id,)
        ).fetchall()
    item = dict(row)
    item["events"] = [dict(e) for e in events]
    return item


def update_case_status(case_id: int, status: str) -> dict[str, Any] | None:
    now = datetime.now(timezone.utc).isoformat()
    with get_conn() as conn:
        conn.execute("UPDATE cases SET status = ? WHERE id = ?", (status, case_id))
        conn.execute(
            "INSERT INTO case_events (case_id, event_type, note, created_at) VALUES (?, ?, ?, ?)",
            (case_id, f"Status → {status}", "Updated from citizen ledger", now),
        )
        row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    return dict(row) if row else None


def delete_case(case_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))
        return cur.rowcount > 0
