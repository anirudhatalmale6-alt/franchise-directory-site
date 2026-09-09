# -*- coding: utf-8 -*-
"""
Le site moderne de l'annuaire de franchises.

Il est GENERE a partir du catalogue deja construit et deja verifie
(../franchises/demo/catalogue.json). Le moteur de donnees ne change pas : ce
qui change, c'est que l'annuaire cesse d'etre UNE page et devient un SITE.

Pourquoi ca compte, et ce n'est pas cosmetique : une page unique avec des
filtres en JavaScript n'a qu'une seule adresse. Personne ne peut lier
« franchises de restauration rapide en Espagne », aucun moteur de recherche
ne peut l'indexer, et c'est exactement par la qu'arrive le trafic d'un
annuaire. Chaque categorie, chaque pays et chaque enseigne a donc desormais sa
propre page.

  python3 build.py     -> ecrit les .html a cote de ce fichier

NE JAMAIS modifier un .html a la main : il est ecrase a la generation suivante.
"""
import html
import json
import os
import re

RACINE = os.path.dirname(os.path.abspath(__file__))
CATALOGUE = os.path.normpath(os.path.join(RACINE, "..", "franchises", "demo",
                                          "catalogue.json"))
VERSION_CSS = 2

E = html.escape

with open(CATALOGUE, encoding="utf-8") as f:
    CAT = json.load(f)

FICHES = CAT["fiches"]
CATEGORIES = CAT["categories"]
PAYS = CAT["pays"]
REGIONS = CAT["regions"]
FORMATS = CAT["formats"]
TRANCHES = CAT["tranches"]

MARQUE = "Franchise Directory"

# Le vocabulaire du vide de CE produit. Il en a un a lui, comme chaque produit
# du client, et il ne se melange avec aucun autre.
VIDE = "Not published"


def libelle(objet, cle=None):
    """Les libelles du catalogue sont bilingues, portes par les cles « fr » et
    « en » de l'objet lui-meme. Ce site est en anglais."""
    if cle is not None:
        v = objet.get(cle)
        if isinstance(v, dict):
            return v.get("en") or v.get("fr") or ""
        return v or ""
    return objet.get("en") or objet.get("fr") or objet.get("nom") or ""


CAT_PAR_CLE = {c["cle"]: c for c in CATEGORIES}
PAYS_PAR_CODE = {p["cle"]: p for p in PAYS}
REG_PAR_CLE = {r["cle"]: r for r in REGIONS}
FMT_PAR_CLE = {f["cle"]: f for f in FORMATS}
TR_PAR_CLE = {t["cle"]: t for t in TRANCHES}

COULEURS = ["#1D4FD8", "#0F8A5F", "#B4690E", "#9333EA", "#0E7490", "#BE123C",
            "#4338CA", "#15803D", "#A16207", "#7C2D91"]


def couleur(cle):
    return COULEURS[sum(ord(c) for c in cle) % len(COULEURS)]


def initiales(nom):
    bouts = [b for b in re.split(r"[\s\-']", nom) if b]
    if len(bouts) == 1:
        return bouts[0][:2].upper()
    return (bouts[0][0] + bouts[1][0]).upper()


def montant(valeur, devise):
    """Chaque fiche s'affiche DANS SA DEVISE. La regle a ne pas perdre :
    l'affichage utilise la devise de l'enseigne, mais le filtre et le tri par
    investissement se font sur eur_bas, une reference commune. Sans ca,
    « moins de 250 000 » ne veut rien dire d'un pays a l'autre."""
    symboles = {"EUR": "€", "USD": "$", "CAD": "C$", "GBP": "£",
                "CHF": "CHF ", "SEK": "kr ", "NOK": "kr ", "DKK": "kr ",
                "PLN": "zł ", "CZK": "Kč ", "HUF": "Ft ", "RON": "lei "}
    s = symboles.get(devise, devise + " ")
    return f"{s}{valeur:,.0f}".replace(",", " ")


def fourchette(fiche):
    i = fiche["investissement"]
    d = fiche["devise"]
    return f"{montant(i['bas'], d)} – {montant(i['haut'], d)}"


# ---------------------------------------------------------------------------
LOGO = ('<svg viewBox="0 0 32 32" aria-hidden="true">'
        '<rect x="3" y="14" width="7" height="15" rx="2" fill="#1D4FD8"/>'
        '<rect x="12.5" y="8" width="7" height="21" rx="2" fill="#1D4FD8" opacity=".72"/>'
        '<rect x="22" y="3" width="7" height="26" rx="2" fill="#1D4FD8" opacity=".45"/>'
        '</svg>')

MENU = [("index.html", "Home"), ("directory.html", "Directory"),
        ("categories.html", "Categories"), ("countries.html", "Countries"),
        ("list-your-brand.html", "List your brand"),
        ("about-the-data.html", "About the data")]


def page(fichier, titre, description, corps, actuel=None, fil=None):
    nav = "".join(
        f'<a href="{f}"{" aria-current=\"page\"" if f == (actuel or fichier) else ""}>{E(t)}</a>'
        for f, t in MENU)
    ariane = ""
    if fil:
        bouts = " <span aria-hidden=\"true\">&rsaquo;</span> ".join(
            (f'<a href="{u}">{E(t)}</a>' if u else E(t)) for t, u in fil)
        ariane = f'<div class="wrap"><nav class="fil">{bouts}</nav></div>'

    cat_pied = "".join(f'<li><a href="category-{E(c["cle"])}.html">{E(libelle(c))}</a></li>'
                       for c in CATEGORIES[:6])
    pays_pied = "".join(f'<li><a href="country-{E(p["cle"]).lower()}.html">{E(libelle(p))}</a></li>'
                        for p in PAYS[:6])

    doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(titre)}</title>
<meta name="description" content="{E(description)}">
<meta name="robots" content="noindex,nofollow">
<link rel="stylesheet" href="assets/site.css?v={VERSION_CSS}">
</head>
<body>

<div class="avert"><div class="wrap">
  <b>Preview.</b> Every brand on this site is invented, and so is every figure.
  Real franchise listings belong to the companies that publish them &mdash;
  <a href="about-the-data.html">why, and what replaces them</a>.
</div></div>

<header class="top"><div class="wrap bar">
  <a class="marque" href="index.html">{LOGO}<span>{E(MARQUE)}</span></a>
  <nav class="nav">{nav}</nav>
</div></header>

{ariane}
<main>
{corps}
</main>

<footer class="pied"><div class="wrap">
  <div class="cols">
    <div><h4>Browse</h4><ul>
      <li><a href="directory.html">All franchises</a></li>
      <li><a href="categories.html">By category</a></li>
      <li><a href="countries.html">By country</a></li>
    </ul></div>
    <div><h4>Categories</h4><ul>{cat_pied}</ul></div>
    <div><h4>Countries</h4><ul>{pays_pied}</ul></div>
    <div><h4>Franchisors</h4><ul>
      <li><a href="list-your-brand.html">List your brand</a></li>
      <li><a href="about-the-data.html">About the data</a></li>
    </ul></div>
  </div>
  <p style="margin:26px 0 0">{E(MARQUE)} &mdash; design preview.
  {len(FICHES)} invented brands, {len(CATEGORIES)} categories,
  {len(PAYS)} countries. No account, no payment, no tracker; every form is
  inert.</p>
</div></footer>

</body>
</html>
"""
    with open(os.path.join(RACINE, fichier), "w", encoding="utf-8") as f:
        f.write(doc)
    return len(doc)


# ---------------------------------------------------------------------------
def carte_enseigne(f):
    c = CAT_PAR_CLE[f["categorie"]]
    p = PAYS_PAR_CODE[f["pays_origine"]]
    puces = [E(libelle(c)), E(libelle(FMT_PAR_CLE[f["format"]])),
             f'{f["unites"]} units']
    if f["financement"]:
        puces.append("Financing offered")
    puces_html = "".join(f'<span class="puce">{x}</span>' for x in puces[:3])
    if f["financement"]:
        puces_html += '<span class="puce ok">Financing offered</span>'
    return f"""<a class="ens" href="brand-{E(f['id'])}.html">
  <span class="logo" style="background:{couleur(f['id'])}">{E(initiales(f['nom']))}</span>
  <span>
    <h3>{E(f['nom'])}</h3>
    <span class="meta">{E(libelle(f['resume'], 'en') if isinstance(f['resume'], dict) else f['resume'])}
      &middot; {E(libelle(p))}</span>
    <span class="puces">{puces_html}</span>
  </span>
  <span class="invest">
    <span class="v">{fourchette(f)}</span><br>
    <span class="l">Total investment</span>
  </span>
</a>"""


# ---------------------------------------------------------------------------
def accueil():
    par_cat = {}
    for f in FICHES:
        par_cat.setdefault(f["categorie"], []).append(f)
    vedettes = sorted(CATEGORIES, key=lambda c: -len(par_cat.get(c["cle"], [])))[:8]
    cartes_cat = "".join(f"""<a class="carte" href="category-{E(c['cle'])}.html">
      <h3>{E(libelle(c))}</h3>
      <p>{len(par_cat.get(c['cle'], []))} brands</p></a>""" for c in vedettes)

    par_pays = {}
    for f in FICHES:
        for code in f["pays"]:
            par_pays.setdefault(code, set()).add(f["id"])
    top_pays = sorted(PAYS, key=lambda p: -len(par_pays.get(p["cle"], ())))[:8]
    cartes_pays = "".join(f"""<a class="carte" href="country-{E(p['cle']).lower()}.html">
      <h3>{E(libelle(p))}</h3>
      <p>{len(par_pays.get(p['cle'], ()))} brands recruiting</p></a>""" for p in top_pays)

    recents = sorted(FICHES, key=lambda f: -f["annee_franchisage"])[:4]
    abordables = sorted(FICHES, key=lambda f: f["investissement"]["eur_bas"])[:4]

    return f"""
<section class="hero"><div class="wrap">
  <h1>Find the franchise that fits</h1>
  <p class="lede">Compare {len(FICHES)} brands across {len(PAYS)} countries by
  investment, sector, format and financing &mdash; then request information
  directly from the franchisor. Free for candidates; brands list themselves.</p>
  <div class="actions">
    <a class="btn" href="directory.html">Browse the directory</a>
    <a class="btn btn-b" href="list-your-brand.html">List your brand</a>
  </div>
  <div class="chiffres">
    <div class="chiffre"><div class="v">{len(FICHES)}</div><div class="l">Brands</div></div>
    <div class="chiffre"><div class="v">{len(PAYS)}</div><div class="l">Countries</div></div>
    <div class="chiffre"><div class="v">{len(CATEGORIES)}</div><div class="l">Sectors</div></div>
    <div class="chiffre"><div class="v">{sum(1 for f in FICHES if f['financement'])}</div>
      <div class="l">Offer financing</div></div>
  </div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-h"><h2>Browse by sector</h2>
    <a class="plus" href="categories.html">All {len(CATEGORIES)} sectors &rarr;</a></div>
  <div class="grille g4">{cartes_cat}</div>
</div></section>

<section class="sec" style="background:var(--fond-2);border-top:1px solid var(--trait);
  border-bottom:1px solid var(--trait)"><div class="wrap">
  <div class="sec-h"><h2>Browse by country</h2>
    <a class="plus" href="countries.html">All {len(PAYS)} countries &rarr;</a></div>
  <div class="grille g4">{cartes_pays}</div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="grille g2" style="gap:34px">
    <div>
      <div class="sec-h"><h2>Lowest investment</h2></div>
      {''.join(carte_enseigne(f) for f in abordables)}
    </div>
    <div>
      <div class="sec-h"><h2>Newest to franchising</h2></div>
      {''.join(carte_enseigne(f) for f in recents)}
    </div>
  </div>
</div></section>

<section class="sec"><div class="wrap">
  <div class="sec-h"><h2>How it works</h2>
    <p>The product is the introduction, not the list.</p></div>
  <div class="grille g3">
    <div class="carte"><h3>1. Filter</h3><p>Narrow by sector, country, total
    investment, format and whether the brand offers financing.</p></div>
    <div class="carte"><h3>2. Compare</h3><p>Every brand page shows the same
    figures in the same order &mdash; investment, franchise fee, royalty,
    liquidity required, unit counts, training and lead time.</p></div>
    <div class="carte"><h3>3. Request information</h3><p>One form goes to the
    franchisor. That request is what a directory actually sells, so it is the
    part built first.</p></div>
  </div>
</div></section>
"""


# ---------------------------------------------------------------------------
def annuaire():
    charge = [{
        "i": f["id"], "n": f["nom"], "c": f["categorie"], "r": f["region"],
        "p": f["pays"], "po": f["pays_origine"], "t": f["investissement"]["tranche"],
        "e": f["investissement"]["eur_bas"], "fo": f["format"],
        "fi": 1 if f["financement"] else 0, "u": f["unites"],
        "an": f["annee_franchisage"],
        "d": montant(f["investissement"]["bas"], f["devise"]) + " – " +
             montant(f["investissement"]["haut"], f["devise"]),
        "s": libelle(f["resume"], "en") if isinstance(f["resume"], dict) else f["resume"],
        "co": couleur(f["id"]), "in": initiales(f["nom"]),
        "pn": libelle(PAYS_PAR_CODE[f["pays_origine"]]),
        "cn": libelle(CAT_PAR_CLE[f["categorie"]]),
        "fn": libelle(FMT_PAR_CLE[f["format"]]),
    } for f in FICHES]

    o_cat = "".join(f'<option value="{E(c["cle"])}">{E(libelle(c))}</option>' for c in CATEGORIES)
    o_reg = "".join(f'<option value="{E(r["cle"])}">{E(libelle(r))}</option>' for r in REGIONS)
    o_pays = "".join(f'<option value="{E(p["cle"])}">{E(libelle(p))}</option>' for p in PAYS)
    o_tr = "".join(f'<option value="{E(t["cle"])}">{E(libelle(t))}</option>' for t in TRANCHES)
    o_fmt = "".join(f'<option value="{E(f["cle"])}">{E(libelle(f))}</option>' for f in FORMATS)

    return f"""
<section class="sec"><div class="wrap">
  <h1 class="titre">Franchise directory</h1>
  <p class="chapeau">{len(FICHES)} brands. Filter on the left; results update as
  you change them.</p>
</div></section>

<section class="sec" style="padding-top:0"><div class="wrap">
  <div class="deux-col">
    <form class="filtres" id="filtres" onsubmit="return false">
      <div class="champ"><label for="fCat">Sector</label>
        <select id="fCat"><option value="">All sectors</option>{o_cat}</select></div>
      <div class="champ"><label for="fReg">Region</label>
        <select id="fReg"><option value="">All regions</option>{o_reg}</select></div>
      <div class="champ"><label for="fPays">Country</label>
        <select id="fPays"><option value="">All countries</option>{o_pays}</select></div>
      <div class="champ"><label for="fTr">Total investment</label>
        <select id="fTr"><option value="">Any</option>{o_tr}</select></div>
      <div class="champ"><label for="fFmt">Format</label>
        <select id="fFmt"><option value="">Any format</option>{o_fmt}</select></div>
      <div class="champ"><label for="fFin">Financing</label>
        <select id="fFin"><option value="">Any</option>
          <option value="1">Offered by the franchisor</option></select></div>
      <div class="champ"><label for="fUn">Minimum units</label>
        <input id="fUn" type="number" min="0" placeholder="any"></div>
      <div class="champ"><label for="fNom">Name contains</label>
        <input id="fNom" type="search" placeholder="any"></div>
      <div class="champ"><label for="fTri">Sort by</label>
        <select id="fTri">
          <option value="rel">Most units</option>
          <option value="inv+">Investment, low to high</option>
          <option value="inv-">Investment, high to low</option>
          <option value="new">Newest to franchising</option>
          <option value="az">Name A&ndash;Z</option>
        </select></div>
      <button class="btn btn-b" type="button" id="raz" style="width:100%">Reset</button>
    </form>

    <div>
      <p class="compte" id="compte"></p>
      <div id="res"></div>
      <p class="rien" id="rien" hidden>No brand matches these filters.</p>
    </div>
  </div>
</div></section>

<script id="donnees" type="application/json">{json.dumps(charge, ensure_ascii=False)}</script>
<script>
(function () {{
  var TOUT = JSON.parse(document.getElementById('donnees').textContent);
  var res = document.getElementById('res'), compte = document.getElementById('compte'),
      rien = document.getElementById('rien'), MAX = 30;
  var TRANCHES = {json.dumps({t["cle"]: [t.get("bas"), t.get("haut")] for t in TRANCHES})};

  function v(id) {{ var e = document.getElementById(id); return e.value === '' ? null : e.value; }}

  function filtrer() {{
    var cat = v('fCat'), reg = v('fReg'), pays = v('fPays'), tr = v('fTr'),
        fmt = v('fFmt'), fin = v('fFin'), tri = v('fTri') || 'rel',
        un = v('fUn') === null ? null : parseInt(v('fUn'), 10),
        nom = (v('fNom') || '').toLowerCase();

    var g = TOUT.filter(function (f) {{
      if (cat  && f.c !== cat) return false;
      if (reg  && f.r !== reg) return false;
      /* Un pays coche veut dire « recrute dans ce pays », pas « vient de ce
         pays » : c'est la question que se pose un candidat. */
      if (pays && f.p.indexOf(pays) === -1) return false;
      if (tr   && f.t !== tr) return false;
      if (fmt  && f.fo !== fmt) return false;
      if (fin  && f.fi !== 1) return false;
      if (un !== null && f.u < un) return false;
      if (nom && f.n.toLowerCase().indexOf(nom) === -1) return false;
      return true;
    }});

    /* Le tri par investissement se fait sur eur_bas, PAS sur le montant
       affiche : sinon un forint hongrois passerait devant un euro. */
    g.sort(function (a, b) {{
      if (tri === 'inv+') return a.e - b.e || a.n.localeCompare(b.n);
      if (tri === 'inv-') return b.e - a.e || a.n.localeCompare(b.n);
      if (tri === 'new')  return b.an - a.an || a.n.localeCompare(b.n);
      if (tri === 'az')   return a.n.localeCompare(b.n);
      return b.u - a.u || a.n.localeCompare(b.n);
    }});

    res.innerHTML = g.slice(0, MAX).map(function (f) {{
      return '<a class="ens" href="brand-' + f.i + '.html">' +
        '<span class="logo" style="background:' + f.co + '">' + f['in'] + '</span>' +
        '<span><h3>' + f.n + '</h3><span class="meta">' + f.s + ' &middot; ' + f.pn +
        '</span><span class="puces"><span class="puce">' + f.cn + '</span>' +
        '<span class="puce">' + f.fn + '</span>' +
        '<span class="puce">' + f.u + ' units</span>' +
        (f.fi ? '<span class="puce ok">Financing offered</span>' : '') +
        '</span></span>' +
        '<span class="invest"><span class="v">' + f.d + '</span><br>' +
        '<span class="l">Total investment</span></span></a>';
    }}).join('');

    /* Ce qui est CACHE est ecrit. Une liste coupee en silence se lit comme une
       liste complete, et un candidat conclurait qu'il a tout vu. */
    compte.textContent = g.length > MAX
      ? g.length + ' brands match — showing the first ' + MAX + ', ' +
        (g.length - MAX) + ' more not shown'
      : g.length + (g.length === 1 ? ' brand matches' : ' brands match');
    compte.hidden = g.length === 0;
    rien.hidden = g.length > 0;
  }}

  var form = document.getElementById('filtres');
  form.addEventListener('input', filtrer);
  form.addEventListener('change', filtrer);
  document.getElementById('raz').addEventListener('click', function () {{
    form.reset(); filtrer();
  }});
  filtrer();
}})();
</script>
"""


# ---------------------------------------------------------------------------
def page_categorie(c):
    fiches = [f for f in FICHES if f["categorie"] == c["cle"]]
    fiches.sort(key=lambda f: -f["unites"])
    pays_ici = sorted({p for f in fiches for p in f["pays"]})
    liens = " &middot; ".join(
        f'<a href="country-{E(code).lower()}.html">{E(libelle(PAYS_PAR_CODE[code]))}</a>'
        for code in pays_ici[:12])
    bas = min((f["investissement"]["eur_bas"] for f in fiches), default=0)
    bas_txt = f"{bas:,.0f}".replace(",", " ")
    return f"""
<section class="sec"><div class="wrap">
  <h1 class="titre">{E(libelle(c))} franchises</h1>
  <p class="chapeau">{len(fiches)} brands in this sector, from
  &euro;{bas_txt} upwards. Sorted by network size.</p>
  <div class="actions"><a class="btn btn-b btn-s" href="directory.html">Open the full directory</a></div>
</div></section>
<section class="sec" style="padding-top:0"><div class="wrap">
  {''.join(carte_enseigne(f) for f in fiches[:40])}
  {'<p class="compte" style="margin-top:14px">Showing the first 40 of %d — the '
   'full list is in the directory.</p>' % len(fiches) if len(fiches) > 40 else ''}
  <div class="encadre" style="margin-top:26px"><b>Countries in this sector:</b><br>{liens}</div>
</div></section>
"""


def page_pays(p):
    fiches = [f for f in FICHES if p["cle"] in f["pays"]]
    fiches.sort(key=lambda f: -f["unites"])
    cats_ici = sorted({f["categorie"] for f in fiches})
    liens = " &middot; ".join(
        f'<a href="category-{E(k)}.html">{E(libelle(CAT_PAR_CLE[k]))}</a>' for k in cats_ici)
    return f"""
<section class="sec"><div class="wrap">
  <h1 class="titre">Franchises recruiting in {E(libelle(p))}</h1>
  <p class="chapeau">{len(fiches)} brands say they are opening units in
  {E(libelle(p))}. Each shows its investment in its own currency.</p>
  <div class="actions"><a class="btn btn-b btn-s" href="directory.html">Open the full directory</a></div>
</div></section>
<section class="sec" style="padding-top:0"><div class="wrap">
  {''.join(carte_enseigne(f) for f in fiches[:40])}
  {'<p class="compte" style="margin-top:14px">Showing the first 40 of %d — the '
   'full list is in the directory.</p>' % len(fiches) if len(fiches) > 40 else ''}
  <div class="encadre" style="margin-top:26px"><b>Sectors present here:</b><br>{liens}</div>
</div></section>
"""


def index_categories():
    par_cat = {}
    for f in FICHES:
        par_cat.setdefault(f["categorie"], []).append(f)
    cartes = "".join(f"""<a class="carte" href="category-{E(c['cle'])}.html">
      <h3>{E(libelle(c))}</h3><p>{len(par_cat.get(c['cle'], []))} brands</p></a>"""
                     for c in sorted(CATEGORIES, key=lambda c: -len(par_cat.get(c["cle"], []))))
    return f"""
<section class="sec"><div class="wrap">
  <h1 class="titre">All sectors</h1>
  <p class="chapeau">Every sector has its own page, with its own address. That
  is what a directory is indexed on.</p>
  <div class="grille g4" style="margin-top:24px">{cartes}</div>
</div></section>
"""


def index_pays():
    par_pays = {}
    for f in FICHES:
        for code in f["pays"]:
            par_pays.setdefault(code, set()).add(f["id"])
    par_region = {}
    for p in PAYS:
        par_region.setdefault(p["region"], []).append(p)
    blocs = ""
    for r in REGIONS:
        dedans = sorted(par_region.get(r["cle"], []), key=lambda p: -len(par_pays.get(p["cle"], ())))
        if not dedans:
            continue
        cartes = "".join(f"""<a class="carte" href="country-{E(p['cle']).lower()}.html">
          <h3>{E(libelle(p))}</h3><p>{len(par_pays.get(p['cle'], ()))} brands</p></a>"""
                         for p in dedans)
        blocs += f'<div class="sec-h" style="margin-top:30px"><h2>{E(libelle(r))}</h2></div>' \
                 f'<div class="grille g4">{cartes}</div>'
    return f"""
<section class="sec"><div class="wrap">
  <h1 class="titre">All countries</h1>
  <p class="chapeau">A country page lists the brands that say they are
  recruiting there &mdash; not the brands headquartered there. That is the
  question a candidate actually asks.</p>
  {blocs}
</div></section>
"""


# ---------------------------------------------------------------------------
def page_enseigne(f):
    c = CAT_PAR_CLE[f["categorie"]]
    p = PAYS_PAR_CODE[f["pays_origine"]]
    d = f["devise"]
    pays_liens = " &middot; ".join(
        f'<a href="country-{E(code).lower()}.html">{E(libelle(PAYS_PAR_CODE[code]))}</a>'
        for code in f["pays"])

    chiffres = [
        ("Total investment", fourchette(f)),
        ("Franchise fee", montant(f["droit_entree"], d)),
        ("Liquidity required", montant(f["liquidites"], d)),
        ("Net worth required", montant(f["avoir_net"], d)),
        ("Royalty", f'{f["redevance"]}% of revenue'),
        ("Marketing fund", f'{f["fonds_pub"]}% of revenue'),
        ("Franchisor financing", "Yes" if f["financement"] else "No"),
        ("Format", E(libelle(FMT_PAR_CLE[f["format"]]))),
    ]
    reseau = [
        ("Founded", str(f["annee_creation"])),
        ("Franchising since", str(f["annee_franchisage"])),
        ("Total units", str(f["unites"])),
        ("Franchised units", str(f["unites_franchisees"])),
        ("Company-owned", str(f["unites_corpo"])),
        ("Initial training", f'{f["formation_semaines"]} weeks'),
        ("Time to opening", f'about {f["delai_semaines"]} weeks'),
        ("Home country", E(libelle(p))),
    ]

    def paires(liste):
        return "".join(f'<div class="paire"><dt>{l}</dt><dd>{v}</dd></div>' for l, v in liste)

    return f"""
<section class="sec" style="padding-bottom:0"><div class="wrap">
  <div class="entete-fiche">
    <span class="logo" style="background:{couleur(f['id'])}">{E(initiales(f['nom']))}</span>
    <div style="flex:1 1 260px">
      <h1 class="titre" style="margin-bottom:4px">{E(f['nom'])}</h1>
      <p style="margin:0;color:var(--gris)">
        {E(libelle(f['resume'], 'en') if isinstance(f['resume'], dict) else f['resume'])}
        &middot; <a href="category-{E(c['cle'])}.html">{E(libelle(c))}</a></p>
      <div class="puces" style="margin-top:10px">
        <span class="puce">{f['unites']} units</span>
        <span class="puce">Franchising since {f['annee_franchisage']}</span>
        {'<span class="puce ok">Financing offered</span>' if f['financement'] else ''}
      </div>
    </div>
    <div style="text-align:right">
      <div style="font-family:var(--mono);font-weight:700;font-size:19px">{fourchette(f)}</div>
      <div style="font-size:12.5px;color:var(--gris-c);text-transform:uppercase;
        letter-spacing:.05em">Total investment</div>
    </div>
  </div>
</div></section>

<section class="sec" style="padding-top:0"><div class="wrap">
  <div class="deux-col" style="grid-template-columns:minmax(0,1fr) minmax(0,380px)">
    <div>
      <div class="sec-h"><h2>Investment</h2></div>
      <dl class="paires" style="margin:0">{paires(chiffres)}</dl>

      <div class="sec-h" style="margin-top:32px"><h2>The network</h2></div>
      <dl class="paires" style="margin:0">{paires(reseau)}</dl>

      <div class="sec-h" style="margin-top:32px"><h2>Where it is recruiting</h2></div>
      <div class="encadre">{pays_liens}</div>

      <div class="sec-h" style="margin-top:32px"><h2>Not published by this brand</h2></div>
      <div class="encadre"><p style="margin:0;color:var(--gris)">
        Average unit revenue, the franchise agreement term, renewal terms and
        territory protection are <b>{E(VIDE)}</b>. A directory that fills those
        in with plausible numbers is the reason nobody trusts directories; they
        appear here only when the franchisor supplies them.</p></div>
    </div>

    <div>
      <form class="form" onsubmit="return false">
        <h3 style="margin:0 0 4px;font-size:18px">Request information</h3>
        <p style="margin:0 0 14px;color:var(--gris);font-size:14.5px">Sent to
        {E(f['nom'])}. No cost, no obligation.</p>
        <p class="note-form">This form is a mockup. It has no action and no
        script &mdash; it sends nothing anywhere, and nothing you type is
        stored.</p>
        <div class="deux">
          <div class="champ"><label for="q-fn">First name</label><input id="q-fn" disabled></div>
          <div class="champ"><label for="q-ln">Last name</label><input id="q-ln" disabled></div>
        </div>
        <div class="champ"><label for="q-country">Country of interest</label>
          <select id="q-country" disabled>{''.join(
            f'<option>{E(libelle(PAYS_PAR_CODE[code]))}</option>' for code in f['pays'])}</select></div>
        <div class="champ"><label for="q-cap">Capital available</label>
          <select id="q-cap" disabled>{''.join(
            f'<option>{E(libelle(t))}</option>' for t in TRANCHES)}</select></div>
        <div class="champ"><label for="q-msg">Message</label>
          <textarea id="q-msg" disabled></textarea></div>
        <button class="btn" type="button" disabled style="width:100%">Send request</button>
      </form>
    </div>
  </div>
</div></section>
"""


# ---------------------------------------------------------------------------
def inscription():
    o_cat = "".join(f'<option>{E(libelle(c))}</option>' for c in CATEGORIES)
    return f"""
<section class="sec"><div class="wrap">
  <h1 class="titre">List your brand</h1>
  <p class="chapeau">A directory grows because franchisors put themselves in
  it. That is also the only honest way to hold accurate figures: the brand
  publishes its own, and updates them when they change.</p>
</div></section>
<section class="sec" style="padding-top:0"><div class="wrap">
  <div class="deux-col" style="grid-template-columns:minmax(0,1fr) minmax(0,360px)">
    <form class="form" onsubmit="return false">
      <p class="note-form">Mockup. This form has no action and no script; it
      sends nothing and stores nothing.</p>
      <div class="deux">
        <div class="champ"><label for="b-name">Brand name</label><input id="b-name" disabled></div>
        <div class="champ"><label for="b-cat">Sector</label>
          <select id="b-cat" disabled>{o_cat}</select></div>
      </div>
      <div class="deux">
        <div class="champ"><label for="b-low">Investment from</label><input id="b-low" disabled></div>
        <div class="champ"><label for="b-high">Investment to</label><input id="b-high" disabled></div>
      </div>
      <div class="deux">
        <div class="champ"><label for="b-fee">Franchise fee</label><input id="b-fee" disabled></div>
        <div class="champ"><label for="b-roy">Royalty (%)</label><input id="b-roy" disabled></div>
      </div>
      <div class="champ"><label for="b-desc">One-line description</label>
        <input id="b-desc" disabled></div>
      <div class="champ"><label for="b-countries">Countries you are recruiting in</label>
        <input id="b-countries" disabled></div>
      <button class="btn" type="button" disabled>Submit for review</button>
    </form>
    <div>
      <div class="encadre"><h3 style="margin-top:0">What happens next</h3>
      <p style="margin:0;color:var(--gris);font-size:15px">In the live product a
      submission is reviewed before it appears, because an unreviewed directory
      fills with brokers within a week. Review, the franchisor's own dashboard
      and lead tracking are the next thing to build once you approve this
      design.</p></div>
    </div>
  </div>
</div></section>
"""


def page_donnees():
    return f"""
<section class="sec"><div class="wrap">
  <h1 class="titre">About the data</h1>
  <p class="chapeau">Every brand here is invented. This page says why, because
  the reason decides how the real directory gets filled.</p>

  <div class="sec-h" style="margin-top:30px"><h2>Why not real brands</h2></div>
  <div class="grille g2">
    <div class="carte"><h3>A competitor's database is their asset</h3>
      <p>Copying listings out of an existing directory takes their work, and a
      copied listing is wrong the day the brand changes a fee &mdash; without
      anyone noticing.</p></div>
    <div class="carte"><h3>Invented figures under a real name are worse</h3>
      <p>Publishing a franchise fee or a required net worth for a company that
      exists, when nobody told you the number, is false financial information
      published under their name.</p></div>
  </div>

  <div class="sec-h" style="margin-top:30px"><h2>What the numbers here are</h2></div>
  <div class="encadre"><p style="margin:0">{len(FICHES)} invented brands, drawn
  <b>inside the real ranges of each sector</b> so the filters behave as they
  will in production, from a fixed seed so the file is reproducible to the
  character. Each brand shows its investment in its own currency; filtering and
  sorting run on a single common reference value, otherwise &ldquo;under
  250,000&rdquo; would mean something different in every country and a
  high-to-low sort would put the weakest currency on top.</p></div>

  <div class="sec-h" style="margin-top:30px"><h2>How the real one fills</h2></div>
  <div class="encadre"><p style="margin:0">Franchisors list themselves, through
  <a href="list-your-brand.html">the form</a>, and a CSV import exists for the
  brands you already hold. The engine does not change &mdash; only the file it
  reads.</p></div>
</div></section>
"""


# ===========================================================================
if __name__ == "__main__":
    with open(os.path.join(RACINE, "assets", "site.css"), encoding="utf-8") as f:
        css = f.read()
    assert css.count("/*") == css.count("*/"), "site.css : commentaires desequilibres"

    total = 0
    total += page("index.html", f"{MARQUE} — find the franchise that fits",
                  f"Compare {len(FICHES)} franchise brands across {len(PAYS)} "
                  "countries by investment, sector, format and financing.", accueil())
    total += page("directory.html", f"Directory — {MARQUE}",
                  "Filter franchise brands by sector, country, investment and format.",
                  annuaire())
    total += page("categories.html", f"All sectors — {MARQUE}",
                  "Every franchise sector, each with its own page.", index_categories())
    total += page("countries.html", f"All countries — {MARQUE}",
                  "Franchise brands by country of recruitment.", index_pays())
    total += page("list-your-brand.html", f"List your brand — {MARQUE}",
                  "Franchisors submit their own listing.", inscription())
    total += page("about-the-data.html", f"About the data — {MARQUE}",
                  "Why every brand in this preview is invented.", page_donnees())

    for c in CATEGORIES:
        total += page(f"category-{c['cle']}.html", f"{libelle(c)} franchises — {MARQUE}",
                      f"Franchise brands in the {libelle(c)} sector.",
                      page_categorie(c), actuel="categories.html",
                      fil=[("Home", "index.html"), ("Sectors", "categories.html"),
                           (libelle(c), None)])
    for p in PAYS:
        total += page(f"country-{p['cle'].lower()}.html",
                      f"Franchises in {libelle(p)} — {MARQUE}",
                      f"Franchise brands recruiting in {libelle(p)}.",
                      page_pays(p), actuel="countries.html",
                      fil=[("Home", "index.html"), ("Countries", "countries.html"),
                           (libelle(p), None)])
    for f in FICHES:
        total += page(f"brand-{f['id']}.html", f"{f['nom']} — {MARQUE}",
                      f"Investment, fees and network for {f['nom']}.",
                      page_enseigne(f), actuel="directory.html",
                      fil=[("Home", "index.html"), ("Directory", "directory.html"),
                           (libelle(CAT_PAR_CLE[f["categorie"]]),
                            f"category-{f['categorie']}.html"), (f["nom"], None)])

    n = 6 + len(CATEGORIES) + len(PAYS) + len(FICHES)
    print(f"{MARQUE} — {n} pages, {total:,} octets".replace(",", " "))
    print("  categories :", len(CATEGORIES), "| pays :", len(PAYS),
          "| enseignes :", len(FICHES))
