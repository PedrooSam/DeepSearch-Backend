import pandas as pd
import re
from pathlib import Path

# ── Mapeamento: substring (lower) → categoria final ──────────────────────────
# A ordem importa: mais específico primeiro!
RULES = [
    # Shark Interaction — intenção direta com tubarão
    ("Shark Interaction", ["feed.*shark", "touch.*shark", "pett.*shark",
               "lasso", "wrangl", "tagg.*shark", "chum",
               "diving / kiss", "selfie", "attempt.*shark",
               "remov.*hook", "free.*shark", "rescue.*shark", "kill.*shark",
               "shark fish", "shark diving", "finning the shark",
               "dragging.*shark", "moving.*shark", "reviving.*shark",
               "remov.*shark", "watching.*shark", "photographing.*shark",
               "filming.*shark", "filming.*blue shark", "inspecting.*shark",
               "attempt.*crocodile", "observing.*shark", "feeding.*shark",
               "watching.*seal", "watching the shark", "feeding fish",
               "attempt.*free", "attempt.*rescue.*shark",
               "fell.*dead shark", "hooked.*shark"]),

    # Spearfishing — pesca com arpão
    ("Spearfishing", ["spearfish", "spear fish"]),

    # Scuba / Tech Diving
    ("Scuba Diving", ["scuba", "tech div", "wreck.*div"]),

    # Free Diving / Apneia
    ("Free Diving", ["free div", "free-div", "freediv", "skindiv",
                     "hookah div", "abalone div", "abalone diving"]),

    # Snorkeling
    ("Snorkeling", ["snorkel"]),

    # Diving (genérico — o que sobrar de dive)
    ("Diving", ["diving", "cage div"]),

    # Surfing — surfe convencional
    ("Surfing", ["surfing", "surfng", "surfboard", "night surf",
                 "tandem surf", "surf paddl", "surf ski", "surf-ski",
                 "surfski", "scurf", "windsur", "kite surf", "kitesur",
                 "kite-surf", "board sail", "sailboard"]),

    # Bodyboarding — body board / body surf / boogie board
    ("Bodyboarding", ["body board", "bodyboard", "body-board",
                      "boogie board", "boogie-board", "bogieboard",
                      "body surf", "bodysurf", "body-surf",
                      "kneeboard"]),

    # Stand-Up Paddle / Paddle Boarding
    ("Paddleboarding", ["paddle board", "paddleboard", "paddle-board",
                        "stand-up paddle", "stand up paddle",
                        "paddle ski", "paddleski", "paddle-ski",
                        "paddle-surf", "sup foil", "^sup$"]),

    # Kayaking
    ("Kayaking", ["kayak", "kakay", "canoe", "outrigger"]),

    # Fishing (qualquer forma)
    ("Fishing", ["fishing", "fisherman", "fishingat", "trawl",
                 "casting a net", "gill net", "surf fish", "wade fish",
                 "wade-fish", "drift fish", "crabbing", "shrimping",
                 "lobster", "crayfis", "abalone", "scallop", "prawn"]),

    # Kite sports — antes de Wading/Swimming
    ("Surfing", ["kite surf", "kitesur", "kite-surf", "kite board",
                 "kiteboard", "kite-board"]),

    # Wading
    ("Wading", ["wading", "wade", "standing", "kneeling", "crouching",
                "sitting in the water", "in waist-deep", "in water",
                "splashing", "walking", "crawling", "hiking on the beach",
                "skimboard", "picking opihi", "returning to shore"]),

    # Swimming
    ("Swimming", ["swimming", "bathing", "batin", "treading water",
                  "floating", "marathon swim", "playing", "jumping",
                  "fell.*water", "fell overboard", "adrift", "paddling",
                  "rowing", "water-ski", "wakeboard", "jet ski",
                  "dived naked", "jumped.*water", "jumped.*rocks",
                  "riding floatation", "on a float", "towing her sister",
                  "lifesaving", "exercising his dog", "catching sardines",
                  "fell into", "riding waves", "lying prone"]),

    # Boat / Vessel
    ("Boat / Vessel", ["boat", "vessel", "yacht", "capsiz", "shipwreck",
                       "sea disaster", "air disaster", "sailing",
                       "sailing on catamaran", "cruising", "overboard",
                       "life jacket", "raft", "refugee raft", "disaster",
                       "dropping anchor", "attempting to fix motor",
                       "murder victim", "nsb mesh", "steinhart",
                       "attempting to illegally"]),

    # Research / Filming
    ("Research / Filming", ["conducting research", "scientific research",
                             "filming", "photo shoot", "photographing fish",
                             "racing ski"]),

    # Fishing (complementar — cleaning, removing)
    ("Fishing", ["cleaning fish", "removing fish", "washing.*fish",
                 "catching sardines", "fell.*fishing"]),
]

# Categorias que devem ser tratadas como "Shark Interaction" por nome exato
SHARK_INTERACTION_EXACT = {
    "Chumming for sharks", "Chumming for white sharks",
    "Feeding sharks", "Tagging sharks", "Teasing a shark",
    "Touching a shark", "Touching sharks", "Petting a shark",
    "Petting captive sharks", "Wrangling a shark", "Shark watching",
    "Killing sharks", "Measuring sharks",
}

def classify_activity(raw: str) -> str:
    """Classifica uma string de atividade na categoria padronizada."""
    if pd.isna(raw) or str(raw).strip() == "":
        return "Unknown"

    raw_stripped = str(raw).strip()

    # Checagem exata primeiro
    if raw_stripped in SHARK_INTERACTION_EXACT:
        return "Shark Interaction"

    low = raw_stripped.lower()

    for category, keywords in RULES:
        for kw in keywords:
            pattern = kw
            if re.search(pattern, low):
                return category

    return "Other / Unknown"


def main():
    BASE   = Path(__file__).parent
    INPUT  = BASE / "dataset_filtrado_enriquecido.csv"
    OUTPUT = BASE / "dataset_padronizado.csv"

    df = pd.read_csv(INPUT)

    print(f"Linhas totais      : {len(df)}")
    print(f"Valores únicos (antes): {df['Activity'].nunique()}")
    print(f"Nulos em Activity  : {df['Activity'].isna().sum()}\n")

    # Mantém original para auditoria
    df["Activity_original"] = df["Activity"]
    df["Activity"] = df["Activity_original"].apply(classify_activity)

    print("Distribuição após padronização:")
    print(df["Activity"].value_counts().to_string())
    print(f"\nValores únicos (depois): {df['Activity'].nunique()}")

    # ── Auditoria: mostra o que foi para Other / Unknown ─────────────────────
    outros = df[df["Activity"] == "Other / Unknown"]["Activity_original"].dropna().unique()
    if len(outros):
        print(f"\nAtividades não classificadas ({len(outros)}):")
        for v in sorted(outros):
            print(f"   {repr(v)}")

    df.to_csv(OUTPUT, index=False)
    print(f"\nArquivo salvo em: {OUTPUT}")


if __name__ == "__main__":
    main()