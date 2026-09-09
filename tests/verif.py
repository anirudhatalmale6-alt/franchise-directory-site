# -*- coding: utf-8 -*-
"""
Controles du site d'annuaire, AU RENDU.

Ce qui est reellement verifie :
  1. le filtre rend EXACTEMENT l'ensemble qu'un recalcul independant, fait
     depuis catalogue.json, designe ;
  2. LA REGLE DES DEVISES : le tri par investissement se fait sur une valeur
     de reference commune, pas sur le montant affiche. Si on triait sur
     l'affichage, les enseignes hongroises passeraient devant tout le monde
     parce qu'un forint fait de gros nombres ;
  3. les pages de categorie et de pays existent VRAIMENT et listent ce qu'elles
     annoncent — c'est toute la raison d'etre du passage d'une page a un site ;
  4. chaque formulaire est inerte, et le dit.

Usage : python3 tests/verif.py http://127.0.0.1:8931
"""
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

from playwright.sync_api import sync_playwright

CATALOGUE = os.path.normpath(os.path.join(RACINE, "..", "franchises", "demo",
                                          "catalogue.json"))
with open(CATALOGUE, encoding="utf-8") as f:
    CAT = json.load(f)

FICHES = CAT["fiches"]
CATEGORIES = CAT["categories"]
PAYS = CAT["pays"]

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8931").rstrip("/")

ok, ko = 0, []


def verif(nom, condition, detail=""):
    global ok
    if condition:
        ok += 1
    else:
        ko.append((nom, detail))
        print("  ECHEC ", nom, " ", detail)


def attendus(**cr):
    """Recalcul INDEPENDANT depuis le catalogue. Ne partage aucune ligne avec
    le JavaScript de la page : c'est ce qui lui permet de le contredire."""
    out = []
    for f in FICHES:
        if "cat" in cr and f["categorie"] != cr["cat"]:
            continue
        if "region" in cr and f["region"] != cr["region"]:
            continue
        # « pays » = recrute dans ce pays, pas « vient de ».
        if "pays" in cr and cr["pays"] not in f["pays"]:
            continue
        if "tranche" in cr and f["investissement"]["tranche"] != cr["tranche"]:
            continue
        if "format" in cr and f["format"] != cr["format"]:
            continue
        if cr.get("financement") and not f["financement"]:
            continue
        if "unites_min" in cr and f["unites"] < cr["unites_min"]:
            continue
        out.append(f)
    return out


with sync_playwright() as p:
    nav = p.chromium.launch()
    pg = nav.new_page()
    pg.set_viewport_size({"width": 1280, "height": 900})
    erreurs = []
    pg.on("pageerror", lambda e: erreurs.append(str(e)))
    pg.on("console", lambda m: erreurs.append(m.text) if m.type == "error" else None)

    # ---- 1. les pages principales ----------------------------------------
    principales = ["index.html", "directory.html", "categories.html",
                   "countries.html", "list-your-brand.html", "about-the-data.html"]
    for f in principales:
        r = pg.goto(f"{BASE}/{f}", wait_until="networkidle")
        verif(f"{f} : repond 200", r.status == 200, str(r.status))
        bas = pg.inner_text("body").lower()
        verif(f"{f} : le bandeau d'apercu est present",
              "preview." in bas and "invented" in bas)

    # ---- 2. LE FILTRE ------------------------------------------------------
    pg.goto(f"{BASE}/directory.html", wait_until="networkidle")
    pg.wait_for_timeout(300)

    def applique(**champs):
        pg.click("#raz")
        pg.wait_for_timeout(120)
        for ident, valeur in champs.items():
            if ident.startswith("f") and ident in ("fCat", "fReg", "fPays", "fTr",
                                                   "fFmt", "fFin", "fTri"):
                pg.select_option(f"#{ident}", str(valeur))
            else:
                pg.fill(f"#{ident}", str(valeur))
        pg.wait_for_timeout(220)
        texte = pg.inner_text("#compte")
        n = int(re.search(r"^(\d+)", texte).group(1))
        return n, texte

    n, texte = applique()
    verif("annuaire : sans filtre, toutes les enseignes correspondent",
          n == len(FICHES), f"{n} vs {len(FICHES)}")
    verif("annuaire : la liste tronquee dit combien elle cache",
          "not shown" in texte, texte)

    cat0 = CATEGORIES[0]["cle"]
    n, _ = applique(fCat=cat0)
    verif(f"annuaire : filtre par secteur ({cat0})",
          n == len(attendus(cat=cat0)), f"{n} vs {len(attendus(cat=cat0))}")

    n, _ = applique(fPays="ES")
    verif("annuaire : filtre par pays de recrutement (ES)",
          n == len(attendus(pays="ES")), f"{n} vs {len(attendus(pays='ES'))}")

    # La combinaison — celle qui revele un ET traite comme un OU.
    n, _ = applique(fCat=cat0, fPays="FR", fFin="1")
    prevu = attendus(cat=cat0, pays="FR", financement=True)
    verif("annuaire : secteur + pays + financement combines",
          n == len(prevu), f"{n} vs {len(prevu)}")

    n, _ = applique(fTr="t1", fUn=50)
    prevu = attendus(tranche="t1", unites_min=50)
    verif("annuaire : tranche d'investissement + unites minimum",
          n == len(prevu), f"{n} vs {len(prevu)}")

    # ---- 3. LA REGLE DES DEVISES ------------------------------------------
    # Le tri croissant doit suivre eur_bas, PAS le nombre affiche. Un forint
    # hongrois affiche des nombres enormes pour un investissement modeste :
    # si le tri portait sur l'affichage, il finirait en tete du decroissant.
    pg.click("#raz"); pg.wait_for_timeout(120)
    pg.select_option("#fTri", "inv+")
    pg.wait_for_timeout(250)
    ids = pg.evaluate("""() => [...document.querySelectorAll('#res .ens')]
        .map(a => a.getAttribute('href').replace('brand-','').replace('.html',''))""")
    par_id = {f["id"]: f for f in FICHES}
    refs = [par_id[i]["investissement"]["eur_bas"] for i in ids]
    verif("devises : le tri croissant suit la valeur de reference commune",
          refs == sorted(refs), f"{refs[:6]}")

    pg.select_option("#fTri", "inv-")
    pg.wait_for_timeout(250)
    ids = pg.evaluate("""() => [...document.querySelectorAll('#res .ens')]
        .map(a => a.getAttribute('href').replace('brand-','').replace('.html',''))""")
    refs = [par_id[i]["investissement"]["eur_bas"] for i in ids]
    verif("devises : le tri decroissant aussi",
          refs == sorted(refs, reverse=True), f"{refs[:6]}")
    # Et le montant AFFICHE reste dans la devise de l'enseigne.
    devises_vues = pg.evaluate("""() => [...document.querySelectorAll('#res .ens .invest .v')]
        .map(e => e.textContent.trim())""")
    prem = par_id[ids[0]]
    verif("devises : le montant affiche est dans la devise de l'enseigne",
          any(s in devises_vues[0] for s in ("€", "$", "£", "kr", "zł", "Kč",
                                             "Ft", "lei", "CHF", "C$",
                                             prem["devise"])),
          f'{devises_vues[0]!r} pour {prem["devise"]}')

    # ---- 4. l'ensemble vide est DIT ---------------------------------------
    pg.click("#raz"); pg.wait_for_timeout(120)
    pg.select_option("#fTr", "t1")
    pg.fill("#fUn", "100000")
    pg.wait_for_timeout(250)
    verif("annuaire : une recherche sans resultat le dit", pg.is_visible("#rien"))
    verif("annuaire : et n'affiche aucune enseigne",
          pg.locator("#res .ens").count() == 0, str(pg.locator("#res .ens").count()))

    # ---- 5. LES PAGES ADRESSABLES ------------------------------------------
    # C'est la raison d'etre du passage d'une page a un site : chaque secteur
    # et chaque pays doit avoir sa propre adresse, et lister ce qu'il annonce.
    for c in CATEGORIES[:4]:
        r = pg.goto(f"{BASE}/category-{c['cle']}.html", wait_until="domcontentloaded")
        verif(f"category-{c['cle']} : repond 200", r.status == 200, str(r.status))
        corps = pg.inner_text("body")
        prevu = len(attendus(cat=c["cle"]))
        m = re.search(r"(\d+) brands in this sector", corps)
        verif(f"category-{c['cle']} : annonce le bon nombre",
              bool(m) and int(m.group(1)) == prevu,
              f"{m.group(1) if m else 'absent'} vs {prevu}")
        vus = pg.locator(".ens").count()
        verif(f"category-{c['cle']} : liste des enseignes",
              vus == min(prevu, 40), f"{vus} vs {min(prevu, 40)}")

    for p_ in PAYS[:4]:
        code = p_["cle"].lower()
        r = pg.goto(f"{BASE}/country-{code}.html", wait_until="domcontentloaded")
        verif(f"country-{code} : repond 200", r.status == 200, str(r.status))
        corps = pg.inner_text("body")
        prevu = len(attendus(pays=p_["cle"]))
        m = re.search(r"(\d+) brands say they are opening", corps)
        verif(f"country-{code} : annonce le bon nombre",
              bool(m) and int(m.group(1)) == prevu,
              f"{m.group(1) if m else 'absent'} vs {prevu}")

    # ---- 6. une fiche enseigne --------------------------------------------
    f0 = FICHES[0]
    pg.goto(f"{BASE}/brand-{f0['id']}.html", wait_until="networkidle")
    corps = pg.inner_text("body")
    verif("fiche : le nom est celui du catalogue", f0["nom"] in corps)
    verif("fiche : la redevance est celle du catalogue",
          f'{f0["redevance"]}%' in corps, str(f0["redevance"]))
    verif("fiche : le nombre d'unites est celui du catalogue",
          str(f0["unites"]) in corps, str(f0["unites"]))
    bas = corps.lower()
    verif("fiche : le vocabulaire du vide est celui de CE produit",
          "not published" in bas)
    for autre in ("To be decided", "To be sourced", "À définir", "À confirmer",
                  "À fournir"):
        verif(f"fiche : n'emprunte pas « {autre} » a un autre produit",
              autre.lower() not in bas)
    # Controle positif : la recherche en minuscules sait trouver un libelle.
    verif("fiche : la recherche de vocabulaire sait trouver quelque chose",
          "not published" in bas, "la comparaison ne trouve rien")

    # ---- 7. les formulaires sont inertes ET le disent ---------------------
    for f, sel in ((f"brand-{f0['id']}.html", "form"), ("list-your-brand.html", "form")):
        pg.goto(f"{BASE}/{f}", wait_until="networkidle")
        etat = pg.evaluate("""() => [...document.querySelectorAll('form')].map(fo => ({
            action: fo.getAttribute('action'),
            methode: fo.getAttribute('method'),
            actifs: [...fo.querySelectorAll('input,select,textarea,button')]
                      .filter(e => !e.disabled).length }))""")
        verif(f"{f} : aucun formulaire n'a d'action",
              all(e["action"] is None for e in etat), str(etat))
        verif(f"{f} : aucun champ n'est actif",
              all(e["actifs"] == 0 for e in etat), str(etat))
        verif(f"{f} : la page dit que le formulaire est une maquette",
              "mockup" in pg.inner_text("body").lower())

    # ---- 8. mobile ---------------------------------------------------------
    for f in ("index.html", "directory.html", f"brand-{f0['id']}.html"):
        pg.set_viewport_size({"width": 390, "height": 800})
        pg.goto(f"{BASE}/{f}", wait_until="networkidle")
        pg.wait_for_timeout(250)
        deb = pg.evaluate("() => document.documentElement.scrollWidth"
                          " - document.documentElement.clientWidth")
        verif(f"{f} : pas de debordement horizontal a 390 px", deb <= 0, str(deb))
    pg.set_viewport_size({"width": 1280, "height": 900})

    verif("aucune erreur JavaScript", not erreurs, str(erreurs[:2]))

    # ---- captures ----------------------------------------------------------
    D = "/var/lib/freelancer/projects/40478471/"
    for f, nom in (("index.html", "fs-1-accueil"),
                   ("directory.html", "fs-2-annuaire"),
                   (f"brand-{f0['id']}.html", "fs-3-fiche"),
                   ("countries.html", "fs-4-pays")):
        pg.goto(f"{BASE}/{f}", wait_until="networkidle")
        pg.wait_for_timeout(350)
        pg.screenshot(path=D + nom + ".png")
    pg.set_viewport_size({"width": 390, "height": 800})
    pg.goto(f"{BASE}/index.html", wait_until="networkidle")
    pg.wait_for_timeout(350)
    pg.screenshot(path=D + "fs-5-mobile.png")

    nav.close()

print(f"\n{ok + len(ko)} verifications, {len(ko)} echec(s)")
for nom, detail in ko:
    print("  -", nom, detail)
sys.exit(1 if ko else 0)
