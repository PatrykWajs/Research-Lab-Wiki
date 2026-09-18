#!/usr/bin/env python3
"""Translate the English MkDocs Markdown pages to Greek (docs/el/, greeklish slugs).

Markdown-aware: translates only prose (headings, paragraphs, list items, table cells,
admonition bodies + titles, frontmatter description). Keeps verbatim: footnote
DEFINITIONS (the references stay English), fenced code, table separators, HR rules,
and all inline tokens — footnote refs [^S#], markdown links, code spans, emoji
shortcodes, HTML entities, numbers/units, acronyms/chemicals, proper names, brand.
Single-pass placeholder protection (no nesting). Re-runnable.

Run: python3 translate_md_to_greek.py
"""
import os, re, json, pathlib
from openai import OpenAI

ROOT = pathlib.Path(__file__).resolve().parent
DOCS = ROOT / "docs"
MODEL = "gpt-4o"

# EN file -> EL output (greeklish slug) + per-file link rewrites applied AFTER translation
PAGES = {
    # 2026-09-18: new Alpha-GPC page + index card only (everything else already translated).
    "alpha-gpc.md": ("el/alfa-gpc.md", {"](methodology.md)": "](methodologia.md)"}),
    "index.md":     ("el/index.md", {
        "](bpa-thermal-receipts.md)": "](bpa-thermikes-apodeixeis.md)",
        "](collagen.md)":             "](kollagono.md)",
        "](testosterone.md)":         "](testosteroni.md)",
        "](seed-oils.md)":            "](sporelaia.md)",
        "](creatine.md)":             "](kreatini.md)",
        "](omega-3-fish-oil.md)":     "](omega-3-ichthelaio.md)",
        "](vitamin-d.md)":            "](vitamini-d.md)",
        "](magnesium.md)":            "](magnisio.md)",
        "](zinc.md)":                 "](psevdargyros.md)",
        "](vitamin-k2.md)":           "](vitamini-k2.md)",
        "](ashwagandha.md)":          "](asvagkanta.md)",
        "](melatonin.md)":            "](melatonini.md)",
        "](pomegranate.md)":          "](rodi.md)",
        "](alpha-gpc.md)":            "](alfa-gpc.md)",
        "](methodology.md)":          "](methodologia.md)",
    }),
}

PROTECT_WORDS = ["Research Lab Wiki","GlyNAC","UC-II","Pro-Hyp","Hyp-Gly","GLP-1","MPS","SMD","BMD",
    "WOMAC","VISA-A","PINP","P1NP","CTX","NAC","DIAAS","PDCAAS","AMSTAR","GRADE","NMDA","CONSIST","ApoE",
    "Rousselot","Gelita","GELITA","TENDOFORTE","Nitta","Nippi","InterHealth","Myung","Park","Konig","König",
    "Liang","Oikawa","Yamadera","Sugaya","Grasset","Reynolds","Ravindran","Yuenyongviwat","Bischof","Sugihara",
    "BPAF","BPA","BPS","BPF","EFSA","FDA","ECHA","NHANES","NTP",
    "REACH","SVHC","TDI","HPG","DNA","CLARITY","SHBG","Pergafast","Biedermann","Tschudin","Grob",
    "Hormann","Ehrlich","Swan","Huberman","Varghese","Hall","Alharbi","Barakat","BfR","DOI","PMID",
    "JEG-Tox","EPIC-Norfolk","Th17","8-OHdG","NaN",
    "GAIT","mTORC1","Clegg","Aussieker","McKendry","Buchanan","Kumar","Hazen","Biswas","Hilser","Jerger","Lee SK",
    "Travison","Mazur","Corona","Leproult","Van Cauter","Pilz","Lerchbaum","Abu-Zaid","Prasad","Koehler","Morgado",
    "Fornalik","Lopresti","Leisegang","Neychev","Melville","Volek","Whittaker","Reed","Santi","Maldonado-Cárceles",
    "Krüger","Exton","Geniole","Hayes","Myerson","Neustadt","Senathirajah","Al-Dujaili","Jiang","Fui","Grossmann",
    "EMAS","MMAS","DEHP","PUFA","SFA","MUFA","DHEA","StAR","Withania","Eurycoma","Tribulus","Arjuna","Natural Ltd",
    "DHT","LH","FSH","OSA","CPAP","DINP","AGD","Caronia","Iranmanesh","Whirledge","Zueger","Friedl","Nattiv","Hackney",
    "van der Merwe","Merwe","Lak","Antonio","D'Andrea","Jorde","Naghii","Abbott","Chauhan","Pandit","Gonzales","Yakubu",
    "Radke","Henrotin","Meeker","Hamed","Levine","Skakkebaek","Skakkebæk","Travison","Bhasin","Nieschlag","Vorona",
    "Lokeshwar","Wittert","Cignarelli","Barrett-Connor","Lepidium","maca","shilajit","fadogia","Fadogia","boron",
    "Eriksson","Rajaie","Woodward","Furini","Wankhede","Steels","Su","Wang","Smith","Food Frontiers",
    "VERISOL","Jellice","Newtree","Nextida","Meléndez-Hevia","Lugo","Froh","Soh","Thomas","PDCAAS/DIAAS",
    "PubMed","Crossref","Pergafast","CLARITY-BPA","EPIC-Norfolk","Nurses'","Biedermann","Hormann","Melzer",
    # seed-oils project — acronyms/terms/brands + author surnames (keep Latin)
    "LA","ALA","EPA","DHA","OXLAM","OXLAMs","HODE","4-HNE","HNE","CRP","IL-6","TNF","LDL","HDL","HbA1c","CVD",
    "CHD","T2D","FADS","FADS1","FADS2","LIPOGAIN","MAHA","HPFS","NHS","FEDIOL","AHA","Unilever","GRAS","EPIC",
    "Rett","Whelan","Su","Fritsche","Simopoulos","Turpeinen","Ramsden","Hooper","Sacks","Mozaffarian","Marklund",
    "Mousavi","Zhang","Liang","Jäger","Jager","Imamura","Rosqvist","Bjermo","Luukkonen","Vessby","Mensink",
    "Grootveld","Cam","Cahill","Qin","Pelucchi","Deol","Alvheim","Knobbe","Guyenet","Pearce","Dayton","Zock",
    "Katan","de Pablo","Tjonneland","Tjønneland","de Silva","de Oliveira Otto","Blasbalg","Shanahan","O'Keefe",
    "Csala","Santoro","Ganesan","Micha","Wallace","Carlson","Whigham","Cate","Nextida","Steak",
    # creatine project — acronyms/terms/brands + author surnames (keep Latin)
    "GFR","GLUT4","GLUT-4","PCr","ATP","AGAT","GAMT","CreaT1","SAM","ISSN","Creapure","Kre-Alkalyn",
    "CEE","HCl","HAM-D","PFS-R","TBI","MDD","SSRI","CKD","IGF-1","GH","BBB","RAPM","BDS","FotoFinder","Trichogram",
    "Kreider","Candow","Forbes","Stout","Branch","Lanhers","Delpino","Chilibeck","Devries","Rawson","Desai",
    "Powers","Olsen","Safdar","Buford","Hultman","Wyss","Kaddurah-Daouk","Brosnan","Persky","Greenhaff","Casey",
    "Syrotuik","Spillane","Jagim","Galvan","de Souza","Naeini","Tsiaras","Gualano","Lugaresi","Poortmans","Francaux",
    "Schilling","Farquhar","Longobardi","Pritchard","Kalra","Koshy","Kim","Lopez","Watson","Greenwood","Dalbo",
    "Groeneveld","Bender","Guingand","Warrier","Eghbali","Avgerinos","Prokopidis","Xu","Sandkühler","Sandkuhler",
    "Dechent","Yazigi","Solis","Rae","Benton","Donohoe","Watanabe","McMorris","Turner","Gordji-Nejad","Lyoo","Kious",
    "Roitman","Bakian","Sakellaris","Dolan","Moriarty","Naddafha","Chrusch","Lobo","Dickinson","Derave","Pinto",
    "Mancini","Camargo","Bassit","Santos","Slankamenac","Gordon","Andrews","Cornelissen","Jatoi","Norman",
    "Vandenberghe","Trexler","Elosegui","Geyer","Ziegenfuss","Kalman","Wildman","Almada","Alzchem",
    # creatine deepen pass — new author surnames + acronyms
    "GAMT","AGAT","SLC6A8","CreaT","NET-PD","CREST-E","NAFLD","UPDRS","NINDS","NREM","RMSSD","HRV","GATM","RTD","RTDs",
    "Kieburtz","Hersch","Kley","Vorgerd","Stöckler","Stockler","Stöckler-Ipsiroglu","Salomons","Item","Klopstock",
    "Turck","Eckert","Toniolo","Barranco-Gil","Barranco","Dworak","Maaoui","Deminice","Arciero","Rockwell","Sales",
    "Moore","Alraddadi","Ganguly","Kazeminasab","Pashayee-Khamene","Pashayee","Rubinchuk","Ellery","Muccini",
    "Cordingley","Salem","Ganesan","Watt","Guerrero-Ontiveros","Oliveira","Korovljev","Aguiar","Ben Maaoui","Cochrane",
    # omega-3 / fish oil project — trials/acronyms/brands (keep Latin)
    "DPA","VITAL","VITAL-DEP","VITAL-DKD","ASCEND","REDUCE-IT","STRENGTH","GISSI","GISSI-Prevenzione","JELIS","ORIGIN",
    "OMEGA","DREAM","DOMInO","ORIP","ADORE","KUDOS","INFAT","AREDS2","NAT2","COPSAC","OPERA","FORCE","PURE","USPSTF",
    "NICE","ESC","SELECT","Vascepa","IPE","TOTOX","SPM","SPMs","MACE","AFib","apoB","Lp(a)","IL-1β","eGFR","SBP","DBP",
    "mTOR","p70S6K","OSDI","ADAS-Cog","MMSE","PHQ-8","HOMA-IR","APOE4","APOE","OmegaQuant","ISSFAL","GOED","Omacor",
    "Lovaza","Pronova","Amarin","Martek","MRI-PDFF","rTG","GrimAge","PhenoAge","CANTAB","Bayley","WPPSI","OAT",
    # omega-3 project — author surnames (keep Latin)
    "Burdge","Brenna","Serhan","Dyerberg","Ulven","Ramprasath","Arterburn","Papanikolaou","Yokoyama","Rauch","Roncaglioni",
    "Manson","Bhatt","Nicholls","Aung","Abdelhamid","Gencer","Liao","Mocking","Appleton","Okereke","Bloch","Hawkey","Quinn",
    "Freund-Levi","Chew","Andrieu","Yurko-Mauro","Yassine","Arellanes","Ostadrahimi","Goldberg","Senftleber","Hahn",
    "Costenbader","Asbell","Giannaccare","Middleton","Makrides","Simmonds","Gould","Colombo","Jasani","Hauner","Much",
    "Hibbeln","McGlory","Santo André","Therdyothin","Akinkuolie","Khalafi","Bird","Nichols","Ottestad","Foran","Mozaffarian",
    "Akintoye","Skulas-Ray","Choi","Bailey","Brasky","Aucoin","Grey","O'Keefe","McBurney","Fabian","Miller","Allaire",
    "Hidayat","Simental-Mendía","Jensen","Abbott","Safarinejad","Hosseini","Michaelsen","Falsig","Abdollahzadeh",
    "Nadjarzadeh","Huang","Snipe","Pan","Naghshi","Rodriguez-Leyva","Ursoniu","Hadi","Simon","Carayol","Brouwer","Azrad",
    "Bisgaard","Souied","Xue","de Boer","Chewcharat","Xie","Hong","Abbasi","Kong","Dyall","Carnegie","Mohan","Javaid",
    "Assadourian","Mangione",
    # vitamin-D project — acronyms/terms/trials/agencies (keep Latin)
    "IU","IOM","USPSTF","ViDA","D-Health","DO-HEALTH","D2d","DPVD","MAVIDOS","VDAART","CORONAVIT","VITAL","VDBP",
    "25(OH)D","25(OH)","CYP2R1","DHCR7","NADSYN1","CYP24A1","CYP","QUICKI","BDI","FAS","QFT","IGT","eldecalcitol",
    "calcifediol","calcitriol","nmol","SAD","Pharmavite","Decalyos","CopD","NHMRC","NIDDK","NHLBI","GC1F",
    # vitamin-D project — author surnames (keep Latin)
    "Neale","Scragg","Barbarawi","Keum","Chowdhury","Bjelakovic","Wactawski-Wende","Bolland","Bischoff-Ferrari",
    "Chapuy","Trivedi","Sanders","Burt","Billington","Khaw","Demay","Holick","Ross","Cashman","Ginde","Autier",
    "Powe","Nielson","Vimaleswaran","Drincic","Butler-Laporte","Murai","Ganmaa","de Koning","Vellekkatt","Menon",
    "Nowak","Gloth","Navale","Malihi","Durup","Vieth","Araki","Marcinowska-Suchowierska","Sofianopoulou","Hyppönen",
    "Hypponen","Sutherland","Tian","Ye","Dimitrakopoulou","Afzal","Mokry","Manousaki","Revez","Munger","Pittas",
    "Kawahara","Palacios","Chawes","Terushkin","Reid","Kang","Costenbader","Manson","Chandler","Brenner","Cooper",
    # magnesium project — acronyms/terms/trials/forms (keep Latin)
    "MAGPIE","MgSO4","Mg-ATP","ATP","PPI","PPIs","SGLT2","SGLT2i","ZMA","MMFS-01","Magtein","AIDP","TRPM6","MDS",
    "HOMA-IR","ISI","SBP","DBP","RR","HR","OR","mmHg","mmol","AGA","ACG","Cochrane","NAKO","KORA","WHI","RDA","EAR",
    "L-threonate","Epsom","CSF","Naveh","CMER","PharmaNutra","Alesco","CELLg8","Threotech","Neurocentria","Magceutics",
    # magnesium project — author surnames (keep Latin)
    "de Baaij","Jahnen-Dechent","Altman","Tzivoni","Shepherd","Rosanoff","Workinger","Pitliya","Garrison","Roguin Maor",
    "Kuusipalo","Barna","Torigoe","Mori","Morishita","Chang","Firoz","Pardo","Tinsley","Argeros","Dong","Maqrashi","Amiri",
    "Bagheri","Yin","Jiang","von Luckner","Moabedi","Tarleton","Cheungpasitporn","Tang","Mah","Schuster","Slutsky",
    "Hausenblas","Boyle","Orchard","Cinar","Excoffon","Wilborn","Gallagher","Kass","Gröber","Grober","Marles","Sakaguchi",
    "Kew","Powell","Rouse","Doyle","Vanoni","Pham","Barbagallo","Dibaba","Khan","Hruby","Farsinejad-Marj","Facchinetti",
    "Costello","Elin","Witkowski","Gullestad","DiNicolantonio","Schuchardt","Kappeler","Brilli","Edwards","Khalid",
    "Kessoku","Tepper","Moslehi","Secondulfo","Ayub","Jesus","Hernández-Rubio","Floris","Jafar","Behers","Mohammadi",
    "Basit","Adomako","Krishnan","Léonard","Shah","Cepeda","Fong","Talandashti","Abhishek","Helte","Shugaa Addin","Maggio",
    # zinc project — acronyms/terms/trials/brands (>=3 char, keep Latin)
    "AREDS2","AREDS","FAZST","ZMA","ZnT","ZIP","SLC39","SLC30","IZiNCG","UNICEF","WHO","IOM","BOND","BRINDA",
    "Cochrane","Zicam","Fixodent","Poligrip","Galzin","OptiZinc","RdRp","HCQ","BPH","AMD","B12","Wilson","COVID","RDA","Cu-Zn-SOD","Galzin",
    # zinc project — author surnames (keep Latin)
    "Andreini","Vallee","Falchuk","Kambe","Wessells","Hennigar","Marles","Reider","Wegmüller","Wegmuller","Barrie",
    "Gandia","Yadrick","Eby","Hemilä","Hemila","Nault","Lazzerini","Dhingra","Lassi","Meydani","Wilkinson","Velthuis",
    "Carlucci","Netter","Leake","Schisterman","Wong","Kılıç","Kilic","Wilborn","Brilla","Conte","Yee","Dréno","Dreno",
    "Heckmann","Mozaffar","Swardfager","Karashima","Person","Brewer","Camarata","Nations","Hedera","Jafek","Alexander",
    "Chandra","Fosmire","Leitzmann","Duncan","Jayawardena","Hunter","Davis","King","Brown","Singh",
    # vitamin-K2 project — acronyms/terms/trials/brands (>=3 char, keep Latin; K1/K2/K3 NOT added — 2-char, and gpt-4o keeps them)
    "MGP","dp-ucMGP","ucMGP","ucOC","cOC","PIVKA-II","PIVKA","VKOR","VKORC1","UBIAD1","GGCX","Gla","VKA","VKAs",
    "MK-4","MK-7","MK-8","MK-9","MK-13","INR","DOAC","DOACs","AVADEC","ECKO","Trevasc-HDK","iPACK-HD","K4Kidneys",
    "Valkyrie","VitaVasK","VitaK-CAC","MenaQ7","K2VITAL","NattoPharma","Gnosis","Glakay","GPRC6A","Leydig","HCC",
    "menatetrenone","phylloquinone","menaquinone","menadione","natto","Bruneck","PREVEND","EPIC-Heidelberg",
    "PROSPECT-EPIC","Rotterdam","CAC","NaF","18F-NaF",
    # vitamin-K2 project — author surnames (keep Latin)
    "Rost","Schurgers","Sato","Nakagawa","Okano","Conly","Halder","Schwalfenberg","Berenjian","Szterk","Shiraki",
    "Knapen","Inoue","Cockayne","Avenell","Mott","Stevenson","Cheung","Binkley","Luo","Rennenberg","Geleijnse",
    "Gast","Willeit","Witham","De Vriese","Vriese","Vossen","Hasific","Zwakenberg","Diederichsen","Vlasschaert",
    "van Ballegooijen","Ballegooijen","Masterjohn","Scheiber","Kuang","Bolton-Smith","Haroon","Holden","Saritas",
    "Krueger","Diegel","Moriishi","Beulens","Shahdadian","Nikpayam","Shea","Nimptsch","Habu","Yoshida","Neogi",
    "McFarlin","Dofferhoff","Visser","Theuwissen","Sconce","Rombouts","Violi","Caluwé","Caluwe","Dalmeijer",
    # ashwagandha project — extracts/brands/chemicals/acronyms (>=3 char, keep Latin; 2-char skipped)
    "KSM-66","Sensoril","Shoden","Ixoreal","Natreon","NooGandha","Prolanza","Inventia","Specnova","Arjuna Natural",
    "somnifera","withanolide","withanolides","withaferin","withanone","withanoside","withanosides","sitoindoside","sitoindosides",
    "triethylene","rasayana","adaptogen","LiverTox","RUCAM","DILIN","DILI","Ayurveda","Ayurvedic","HPA","GABA","GABAergic",
    "DHEA","DHEA-S","HAM-A","DASS","DASS-21","PSQI","STAI","GAD","FSFI","FSDS","WHOQOL","CANTAB","VO2max","TSH","EMA","HMPC",
    "RIVM","Lareb","5xFAD","Th1","PSG","Fodevarestyrelsen",
    # ashwagandha project — author surnames (keep Latin)
    "Chandrasekhar","Salve","Gopukumar","Fuladi","Remenapp","Akhgarjand","Arumugam","Albalawi","Della Porta","Pratte",
    "Marchi","Fatima","Ambiye","Mahdi","Ahmad","Nasimi","Azgomi","Bonilla","Dongre","Khanna","Langade","Deshpande",
    "Kelgane","Cheah","Kaushik","Choudhary","Chengappa","Pingali","Sandhu","Shenoy","Sharma","Vollmer","Björnsson","Bjornsson",
    "Philips","Suryawanshi","Bokan","Sriperumbuduri","Saper","Tallon","Brendler","Williamson","Coope","Candelario","Kuboyama",
    "Vaishnavi","Panossian","Patil","Bashir","Lazarev","Diederichsen",
    # melatonin project - acronyms, trials, drug names (>=3 char, distinctive; no common-word substrings)
    "AASM","CHMP","IARC","EFSA","MTNR1B","CYP1A2","DLMO","AANAT","PubMed","Cochrane","Parkinson","Tanner",
    "COVID-19","TNF-alpha","I-squared","SMD","AUC","BMI","ICU","USP","NSF","ADHD","RCT","RCTs","PMID","PMIDs",
    "MT1","MT2","Circadin","Slenyto","ramelteon","tasimelteon","agomelatine","fluvoxamine","citalopram",
    "nifedipine","zolpidem","eszopiclone","zopiclone","dexmedetomidine","amitriptyline","Pro-MEDIC",
    "6-sulfatoxymelatonin","Withania",
    # --- pomegranate (project 14, 2026-09-15): authors, trials, compounds, acronyms.
    # All >=3 chars; the COMBINED regex is substring-matching, so a <=2-char token here
    # would glue onto ordinary Greek words (the "ng" -> mega-dosing bug).
    "Pantuck","Aviram","Davidson","Seeram","Heber","Paller","Stenner-Liewen","Freedland",
    "Sahebkar","Ghaemi","Bahari","Tomas-Barberan","Andreux","Smail","punicalagin","punicalin",
    "punicic","ellagitannin","ellagitannins","ellagic","urolithin","urolithins","Urolithin",
    "POMx","Mitopure","Amazentis","Timeline","Punica","granatum","PSADT","PSA","MnSOD","PON1",
    "FTC","IMT","FMD","NMR","Gordonibacter","Ellagibacter","metabotype","anthocyanin","Lanham",
    "Anthocyanins","Ellagic","Ellagitannins","Metabotype","Metabotypes","Punicalagin","Urolithins","metabotypes","punicalagins",
    # alpha-GPC page (2026-09-18): chemical synonyms, drug and brand names, trial acronyms
    "Alpha-GPC", "alpha-GPC", "GPC", "L-alpha-glycerylphosphorylcholine", "glycerylphosphorylcholine", "glycerophosphocholine", "alfoscerate", "alphoscerate", "TMAO", "FMO3", "PET", "ICD", "MRS", "Alzheimer", "donepezil", "citicoline", "nimodipine", "oxiracetam", "Gliatilin", "AlphaSize", "GeniusPure", "ASCOMALVA", "CONIVaD", "Chemi", "Nutra", "NNB", "Neopharmed", "Gentili", "Italfarmaco", "Daewoong", "Suheung", "Otsuka", "Kewpie", "Ajinomoto", "Balchem", "Gatti", "Kerksick", "Bellar", "Tamura", "Canal", "Marcus", "L-carnitine", "NHIS", "MFDS", "HIRA", "Stroop", "Flanker", "N-Back"]
_WORD_ALT = '|'.join(re.escape(w) for w in sorted(PROTECT_WORDS, key=len, reverse=True))
# one left-to-right pass: footnote ref | md link | code span | emoji | entity | acronym | digit-token
COMBINED = re.compile(
    r'(\[\^[A-Za-z0-9]+\]|\[[^\]]*\]\([^)]*\)|`[^`]+`|:[a-z0-9_+-]+:|&[#A-Za-z0-9]+;|'
    # word-boundary-wrapped: without \b a protected word matches INSIDE ordinary words
    # (e.g. "Conte" inside "Contested"/"Content"), which corrupts the translation.
    + r'\b(?:' + _WORD_ALT + r')\b'
    + r'|\d[\d.,:%°+/×]*(?:[-–]\d[\d.,:%°+/×]*)*)')
L, R = '⟦', '⟧'

SYS = ("You are a professional EN→EL (Greek) translator for a scientific health-research website "
       "written in Markdown. Translate each given snippet into natural, fluent Greek. HARD RULES: "
       "(1) Some snippets contain placeholder tokens — a private-use bracket char, a number, a closing "
       "bracket char. Keep EVERY placeholder EXACTLY as written, in a natural position; never drop, "
       "translate, space-out, merge, or renumber them. CRITICAL: translate EVERY other word into Greek, INCLUDING any English word sitting immediately before or after a placeholder — a placeholder is only a marker and never means leave the neighbouring word in English. (2) PRESERVE all Markdown formatting exactly: "
       "**bold**, *italic*, `code`. Do not add or remove markup. (3) Do NOT translate chemical names, "
       "acronyms, proper names, units, numbers, DOIs or URLs. (4) Keep the brand 'Research Lab Wiki' in "
       "Latin script. (5) Do not add, drop, or merge content. Return JSON {\"t\":[...]} with exactly the "
       "same number of strings, in order.")

def load_key():
    k = os.environ.get("OPENAI_API_KEY")
    if k:
        return k
    try:                       # fall back to a local .env (not committed)
        for ln in open(ROOT / ".env"):
            if ln.startswith("OPENAI_API_KEY="):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return None

client = OpenAI(api_key=load_key())

def protect(text):
    store = []
    def stash(m):
        store.append(m.group(0)); return f'{L}{len(store)-1}{R}'
    return COMBINED.sub(stash, text), store

def restore(text, store):
    for i in range(len(store) - 1, -1, -1):
        text = text.replace(f'{L}{i}{R}', store[i])
    return text

def translate_batch(strings):
    if not strings:
        return []
    def call(items):
        try:
            r = client.chat.completions.create(model=MODEL, temperature=0,
                max_tokens=16384, response_format={"type": "json_object"},
                messages=[{"role": "system", "content": SYS},
                          {"role": "user", "content": json.dumps({"strings": items}, ensure_ascii=False)}])
            o = json.loads(r.choices[0].message.content)
            res = o.get("t") or o.get("translations") or o.get("strings")
            return res if isinstance(res, list) and len(res) == len(items) else None
        except Exception:      # truncated/invalid JSON, rate limit, etc. -> signal caller to split
            return None
    out = call(strings)
    if out is not None:
        return out
    # A batch too large to return valid JSON in one shot: split and recurse.
    # A single string that still fails is kept verbatim (English) rather than crashing the run.
    if len(strings) == 1:
        return list(strings)
    mid = len(strings) // 2
    return translate_batch(strings[:mid]) + translate_batch(strings[mid:])

# A line decomposes into (prefix_kept, translatable, suffix_kept) or None to keep verbatim.
RE_FOOTNOTE_DEF = re.compile(r'^\[\^[^\]]+\]:')
RE_HEADING      = re.compile(r'^(#{1,6}\s+)(.*)$')
RE_ADMON_TITLE  = re.compile(r'^(\s*(?:!!!|\?\?\?)\s+[\w-]+\s+")([^"]*)(".*)$')
RE_LIST         = re.compile(r'^(\s*(?:[-*+]|\d+\.)\s+)(.*)$')
RE_BLOCKQUOTE   = re.compile(r'^(>\s?)(.*)$')
RE_TABLE_SEP    = re.compile(r'^\s*\|[\s:\-|]+\|\s*$')
RE_TABLE_ROW    = re.compile(r'^\s*\|.*\|\s*$')

def translate_md(text):
    lines = text.split('\n')
    in_front = lines and lines[0].strip() == '---'
    front_end = -1
    if in_front:
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                front_end = i; break
    in_code = False
    # collect translatable pieces with a way to rebuild
    pieces = []          # list of dicts describing each line's plan
    to_send = []         # protected cores to translate
    send_map = []        # (piece_index, slot) -> position in to_send

    def add_send(core):
        prot, store = protect(core.strip())
        if not re.search(r'[A-Za-z]', re.sub(rf'{L}\d+{R}', '', prot)):
            return None  # nothing translatable
        lead = core[:len(core) - len(core.lstrip())]
        trail = core[len(core.rstrip()):]
        idx = len(to_send); to_send.append(prot.strip())
        return (idx, store, lead, trail)

    for i, line in enumerate(lines):
        if in_front and i <= front_end:
            m = re.match(r'^(description:\s*)(.+)$', line)
            if m:
                s = add_send(m.group(2))
                pieces.append({'k':'desc','pre':m.group(1),'s':s} if s else {'k':'raw','t':line})
            else:
                pieces.append({'k':'raw','t':line})
            continue
        if line.strip().startswith('```'):
            in_code = not in_code; pieces.append({'k':'raw','t':line}); continue
        if in_code or RE_FOOTNOTE_DEF.match(line) or RE_TABLE_SEP.match(line) \
           or line.strip() == '' or line.strip() == '---':
            pieces.append({'k':'raw','t':line}); continue
        m = RE_ADMON_TITLE.match(line)
        if m:
            s = add_send(m.group(2))
            pieces.append({'k':'wrap','pre':m.group(1),'suf':m.group(3),'s':s} if s else {'k':'raw','t':line}); continue
        m = RE_HEADING.match(line)
        if m:
            s = add_send(m.group(2)); pieces.append({'k':'wrap','pre':m.group(1),'suf':'','s':s} if s else {'k':'raw','t':line}); continue
        if RE_TABLE_ROW.match(line):
            cells = line.split('|')
            cellplan = []
            for c in cells:
                s = add_send(c) if c.strip() else None
                cellplan.append(('s', s) if s else ('raw', c))
            pieces.append({'k':'table','cells':cellplan}); continue
        m = RE_BLOCKQUOTE.match(line)
        if m:
            s = add_send(m.group(2)); pieces.append({'k':'wrap','pre':m.group(1),'suf':'','s':s} if s else {'k':'raw','t':line}); continue
        m = RE_LIST.match(line)
        if m:
            s = add_send(m.group(2)); pieces.append({'k':'wrap','pre':m.group(1),'suf':'','s':s} if s else {'k':'raw','t':line}); continue
        # plain paragraph line (may be indented admonition body)
        s = add_send(line)
        pieces.append({'k':'wrap','pre':'','suf':'','s':s} if s else {'k':'raw','t':line})

    translated = translate_batch(to_send)

    def render(s):
        idx, store, lead, trail = s
        return lead + restore(translated[idx], store) + trail

    out = []
    for p in pieces:
        if p['k'] == 'raw':
            out.append(p['t'])
        elif p['k'] == 'desc':
            out.append(p['pre'] + render(p['s']))
        elif p['k'] == 'wrap':
            out.append(p['pre'] + render(p['s']) + p['suf'])
        elif p['k'] == 'table':
            out.append('|'.join(render(s) if kind == 's' else s for kind, s in p['cells']))
    return '\n'.join(out)

def main():
    for en_rel, (el_rel, link_fixes) in PAGES.items():
        src = (DOCS / en_rel).read_text(encoding='utf-8')
        el = translate_md(src)
        for a, b in link_fixes.items():
            el = el.replace(a, b)
        out = DOCS / el_rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(el, encoding='utf-8')
        en_ft = src.count('[^'); el_ft = el.count('[^')
        print(f"{en_rel:28s} -> {el_rel:34s} footnote-tokens EN={en_ft} EL={el_ft} {'OK' if en_ft==el_ft else 'CHECK'}")

if __name__ == "__main__":
    main()
