"""Xiringuito la Sal · genera la web estàtica per idiomes.

Font:   src/index.html (català, amb el diccionari T dels 4 idiomes dins el <script>)
        src/carta.json  (la carta transcrita dels PDF, sense preus)
Surt:   index.html (CA), es/, fr/, en/  ·  carta/, es/carta/, fr/carte/, en/menu/
        sitemap.xml, robots.txt, llms.txt

Cada idioma té la seva adreça (Google i ChatGPT el poden llegir sense JavaScript),
amb canonical, hreflang i dades estructurades (Restaurant, preguntes, carta).
Ús:  python src/build.py      (des de la carpeta Web-simple)
"""
import html, json, os, posixpath, re, subprocess
from urllib.parse import quote

ARREL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ARREL, 'src')
BASE = 'https://www.xiringuitolasal.com/'          # domini definitiu (canviar si la web viu en una altra adreça)
LANGS = ['ca', 'es', 'fr', 'en']
HOME = {'ca': '', 'es': 'es/', 'fr': 'fr/', 'en': 'en/'}
CARTA = {'ca': 'carta/', 'es': 'es/carta/', 'fr': 'fr/carte/', 'en': 'en/menu/'}
LOCALE = {'ca': 'ca_ES', 'es': 'es_ES', 'fr': 'fr_FR', 'en': 'en_GB'}
PDF = {'ca': 'assets/carta/carta-ca-es.pdf', 'es': 'assets/carta/carta-ca-es.pdf', 'fr': 'assets/carta/carta-fr-en.pdf', 'en': 'assets/carta/carta-fr-en.pdf'}
PDF_ALTRA = {'ca': PDF['fr'], 'es': PDF['fr'], 'fr': PDF['ca'], 'en': PDF['ca']}
MAPS = 'https://maps.app.goo.gl/VqkFJobXDxhRsfKD7'
CUINA = {'ca': ['Mediterrània', 'Peix i marisc', 'Arrossos', 'Tapes'], 'es': ['Mediterránea', 'Pescado y marisco', 'Arroces', 'Tapas'],
         'fr': ['Méditerranéenne', 'Poisson et fruits de mer', 'Riz', 'Tapas'], 'en': ['Mediterranean', 'Seafood', 'Paella and rice', 'Tapas']}

PAG_CARTA = {
    'ca': dict(ey='La carta', h1='La carta de Xiringuito la Sal', intro='Cuina de mar a la platja de Ses Oliveres, Cadaqués. Els preus i la carta de vins sencera són al PDF.',
               pdf='Obrir la carta en PDF', title='Carta · Xiringuito la Sal, xiringuito a Cadaqués',
               desc="La carta de Xiringuito la Sal, a la platja de Ses Oliveres de Cadaqués: paella i arrossos, peix fresc, coses per picar, amanides i postres.", tornar="Tornar a l'inici"),
    'es': dict(ey='La carta', h1='La carta de Xiringuito la Sal', intro='Cocina de mar en la playa de Ses Oliveres, Cadaqués. Los precios y la carta de vinos completa están en el PDF.',
               pdf='Abrir la carta en PDF', title='Carta · Xiringuito la Sal, chiringuito en Cadaqués',
               desc='La carta de Xiringuito la Sal, en la playa de Ses Oliveres de Cadaqués: paella y arroces, pescado fresco, cosas para picar, ensaladas y postres.', tornar='Volver al inicio'),
    'fr': dict(ey='La carte', h1='La carte de Xiringuito la Sal', intro='Cuisine de la mer sur la plage de Ses Oliveres, à Cadaqués. Les prix et la carte des vins complète sont dans le PDF.',
               pdf='Ouvrir la carte en PDF', title='Carte · Xiringuito la Sal, restaurant de plage à Cadaqués',
               desc='La carte de Xiringuito la Sal, sur la plage de Ses Oliveres à Cadaqués : paella et riz, poisson frais, petites assiettes, salades et desserts.', tornar="Retour à l'accueil"),
    'en': dict(ey='Menu', h1='Xiringuito la Sal menu', intro='Seafood on Ses Oliveres beach, Cadaqués. Prices and the full wine list are in the PDF.',
               pdf='Open the menu (PDF)', title='Menu · Xiringuito la Sal, beach bar in Cadaqués',
               desc='The menu at Xiringuito la Sal, on Ses Oliveres beach in Cadaqués: paella and rice dishes, fresh fish, small plates, salads and desserts.', tornar='Back to home'),
}

CSS_CARTA = '''
/* ---------- Pàgina de la carta en text ---------- */
.carta-pag{padding-top:calc(var(--nav-h) + var(--s6))}
.carta-pag h1{font-size:var(--fs-3xl);max-width:20ch}
.carta-seccions{columns:2;column-gap:var(--s6)}
.carta-sec{break-inside:avoid;margin-bottom:var(--s5)}
.carta-sec h2{font-size:var(--fs-xl);padding-bottom:var(--s1);border-bottom:2px solid var(--text)}
.carta-sec ul{list-style:none;margin:0;padding:0}
.carta-sec li{padding:12px 0;border-bottom:1px solid var(--line)}
.carta-sec .carta-nota{margin-top:var(--s1);color:var(--accent-text);font-size:var(--fs-sm);font-weight:600}
.carta-sec p.vins{margin-top:var(--s2);color:var(--text-2)}
.carta-peu{margin-top:var(--s4);color:var(--text-2);font-size:var(--fs-sm)}
@media (max-width:760px){ .carta-seccions{columns:1} }
'''


def llegeix(nom):
    return open(os.path.join(SRC, nom), encoding='utf-8').read()


def diccionari(font):
    """Treu l'objecte T del <script> amb Node (és JavaScript, no JSON)."""
    i = font.index('var T = {'); j = font.index('\n  };', i)
    codi = 'process.stdout.write(JSON.stringify((' + font[i + 8:j + 4] + ')))'
    r = subprocess.run(['node', '-e', codi], capture_output=True, encoding='utf-8', check=True)
    return json.loads(r.stdout)


def rel(des_de, cap_a):
    """Enllaç relatiu entre dues carpetes de la web ('' = arrel)."""
    r = posixpath.relpath('/' + cap_a, '/' + des_de) if des_de or cap_a else '.'
    return ('./' if r == '.' else r + '/')


def esc(t):
    return html.escape(t, quote=False)


def ressenyes(s, lang):
    """Només les ressenyes de l'idioma de la pàgina (data-r)."""
    return re.sub(r'\n\s*<li class="ressenya" data-r="(?!%s")[a-z]+">.*?</li>' % lang, '', s, flags=re.S)


def tradueix(s, d):
    def txt(m):
        k = m.group('k')
        return m.group(1) + esc(d[k]) + m.group(5) if k in d else m.group(0)
    s = re.sub(r'(<(?P<tag>[a-z0-9]+)\b[^>]*?\sdata-i18n="(?P<k>[^"]+)"[^>]*>)(?P<in>.*?)(</(?P=tag)>)', txt, s, flags=re.S)

    def attr(nom, clau):
        def f(m):
            t = m.group(0); k = re.search(clau + r'="([^"]+)"', t).group(1)
            if k not in d: return t
            return re.sub(r'\s' + nom + r'="[^"]*"', ' ' + nom + '="' + html.escape(d[k]) + '"', t, count=1)
        return f
    s = re.sub(r'<[a-z0-9]+\b[^>]*\sdata-i18n-alt="[^"]+"[^>]*>', attr('alt', 'data-i18n-alt'), s)
    s = re.sub(r'<[a-z0-9]+\b[^>]*\sdata-i18n-aria="[^"]+"[^>]*>', attr('aria-label', 'data-i18n-aria'), s)
    s = re.sub(r'<[a-z0-9]+\b[^>]*\sdata-i18n-msg="[^"]+"[^>]*>', attr('data-msg', 'data-i18n-msg'), s)

    # WhatsApp: l'enllaç ja porta el missatge escrit en l'idioma de la pàgina
    def wa(m):
        t = m.group(0); num = re.search(r'data-wa="(\d+)"', t).group(1); msg = html.unescape(re.search(r'data-msg="([^"]+)"', t).group(1))
        return re.sub(r'\shref="[^"]*"', ' href="%s"' % html.escape('https://wa.me/%s?text=%s' % (num, quote(msg))), t, count=1)
    s = re.sub(r'<a\b[^>]*\sdata-wa="[^"]+"[^>]*>', wa, s)
    return s


def schema(lang, d, pagina, carta=None):
    url_home = BASE + HOME[lang]; url_carta = BASE + CARTA[lang]
    rest = {
        '@type': 'Restaurant', '@id': BASE + '#restaurant', 'name': 'Xiringuito la Sal',
        'alternateName': ['La Sal Es Xiringuito Ses Oliveres', 'Xiri la Sal'],
        'description': d['page_desc'], 'url': url_home, 'telephone': '+34872204041',
        'image': [BASE + 'assets/img/hero-2400.webp', BASE + 'assets/logo/og-terrassa-1200x630.jpg'],
        'logo': BASE + 'assets/logo/favicon-512.png',
        'address': {'@type': 'PostalAddress', 'streetAddress': 'Avinguda Víctor Rahola, 25', 'addressLocality': 'Cadaqués',
                    'postalCode': '17488', 'addressRegion': 'Girona', 'addressCountry': 'ES'},
        'geo': {'@type': 'GeoCoordinates', 'latitude': 42.2857466, 'longitude': 3.2851119},
        'hasMap': MAPS, 'servesCuisine': CUINA[lang], 'priceRange': '€€', 'acceptsReservations': True,
        'hasMenu': url_carta + '#menu',
        # Sense horari fix: canvia segons la temporada (decisió del client, 28-10-2026)
        'sameAs': ['https://www.instagram.com/xiringuitolasal/',
                   'https://www.tripadvisor.es/Restaurant_Review-g580326-d12834000-Reviews-Xiringuito_La_Sal-Cadaques_Costa_Brava_Province_of_Girona_Catalonia.html'],
    }
    graf = [rest, {'@type': 'WebSite', '@id': BASE + '#web', 'name': 'Xiringuito la Sal', 'url': BASE, 'inLanguage': LANGS}]
    if pagina == 'home':
        graf.append({'@type': 'FAQPage', '@id': url_home + '#preguntes', 'inLanguage': lang,
                     'mainEntity': [{'@type': 'Question', 'name': d['q%d' % i],
                                     'acceptedAnswer': {'@type': 'Answer', 'text': d['a%d' % i]}} for i in range(1, 6)]})
    else:
        graf.append({'@type': 'Menu', '@id': url_carta + '#menu', 'name': PAG_CARTA[lang]['h1'], 'inLanguage': lang, 'url': url_carta,
                     'hasMenuSection': [{'@type': 'MenuSection', 'name': sec['t'][lang],
                                         'hasMenuItem': [{'@type': 'MenuItem', 'name': p[lang]} for p in sec['plats']]}
                                        for sec in carta['seccions']]})
    return '<script type="application/ld+json">\n' + json.dumps({'@context': 'https://schema.org', '@graph': graf}, ensure_ascii=False, indent=1) + '\n</script>'


def capcalera(s, lang, d, carpeta, pagina, titol, desc):
    pre = rel(carpeta, '')[:-1] if carpeta else ''
    pre = '' if pre in ('.', '') else pre + '/'
    s = re.sub(r'(?<=["\'(\s,])assets/', pre + 'assets/', s)                     # rutes dels fitxers
    s = s.replace('<html lang="ca">', '<html lang="%s">' % lang, 1)
    s = re.sub(r'<title>.*?</title>', '<title>' + esc(titol) + '</title>', s, count=1)
    s = re.sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + html.escape(desc), s, count=1)
    s = re.sub(r'(<meta property="og:title" content=")[^"]*', lambda m: m.group(1) + html.escape(titol), s, count=1)
    s = re.sub(r'(<meta property="og:description" content=")[^"]*', lambda m: m.group(1) + html.escape(desc), s, count=1)
    s = re.sub(r'(<meta property="og:image" content=")[^"]*', lambda m: m.group(1) + BASE + 'assets/logo/og-terrassa-1200x630.jpg', s, count=1)
    mapa = HOME if pagina == 'home' else CARTA
    links = ['<link rel="canonical" href="%s">' % (BASE + mapa[lang])]
    links += ['<link rel="alternate" hreflang="%s" href="%s">' % (l, BASE + mapa[l]) for l in LANGS]
    links.append('<link rel="alternate" hreflang="x-default" href="%s">' % (BASE + mapa['en']))
    links.append('<meta property="og:url" content="%s">' % (BASE + mapa[lang]))
    links.append('<meta property="og:locale" content="%s">' % LOCALE[lang])
    s = s.replace('<meta property="og:type"', '\n'.join(links) + '\n<meta property="og:type"', 1)
    # Selector d'idioma: enllaços a la mateixa pàgina en cada idioma (com Polylang)
    # Banderes en lloc de CA ES FR EN (el nom de l'idioma, per als lectors de pantalla)
    BAND = json.loads(llegeix('banderes.json'))
    botons = ''.join('\n      <a href="%s" lang="%s" hreflang="%s"%s>%s<span class="visually-hidden">%s</span></a>' % (
        rel(carpeta, mapa[l].rstrip('/')), l, l, ' aria-current="page"' if l == lang else '', BAND[l][1], BAND[l][0]) for l in LANGS)
    s = re.sub(r'(<div class="lang"[^>]*>).*?(\n    </div>)', lambda m: m.group(1) + botons + m.group(2), s, count=1, flags=re.S)
    # Carta: el botó obre el PDF de l'idioma; l'altre botó, l'altre PDF; l'enllaç de text, la carta HTML
    s = re.sub(r'href="[^"]*"(?=[^>]*\sdata-carta\b(?!-))', 'href="%s"' % (pre + PDF[lang]), s)
    s = re.sub(r'href="[^"]*"(?=[^>]*\sdata-carta-altra)', 'href="%s"' % (pre + PDF_ALTRA[lang]), s)
    s = re.sub(r'href="[^"]*"(?=[^>]*\sdata-carta-html)', 'href="%s"' % rel(carpeta, CARTA[lang].rstrip('/')), s)
    # El diccionari ja no cal: el text ja és a l'HTML de cada idioma
    i = s.index('var T = {'); j = s.index('\n  };', i) + 5
    s = s[:i] + 'var T = {};  /* textos ja aplicats a cada idioma per src/build.py */' + s[j:]
    s = re.sub(r'<script type="application/ld\+json">.*?</script>', '@@SCHEMA@@', s, count=1, flags=re.S)
    return s


def pagina_carta(base_home, lang, d, carta):
    c = PAG_CARTA[lang]; carpeta = CARTA[lang].rstrip('/'); casa = rel(carpeta, HOME[lang].rstrip('/'))
    s = base_home
    s = re.sub(r'<link rel="preload" as="image"[^>]*>\n', '', s)
    s = s.replace('</style>', CSS_CARTA + '</style>', 1)
    seccions = []
    for sec in carta['seccions']:
        nota = '<p class="carta-nota">%s</p>' % esc(sec['nota'][lang]) if sec.get('nota') else ''
        plats = ''.join('<li>%s</li>' % esc(p[lang]) for p in sec['plats'])
        seccions.append('      <section class="carta-sec" aria-labelledby="c-%s"><h2 id="c-%s">%s</h2>%s<ul>%s</ul></section>' % (
            sec['id'], sec['id'], esc(sec['t'][lang]), nota, plats))
    v = carta['vins']
    seccions.append('      <section class="carta-sec" aria-labelledby="c-vins"><h2 id="c-vins">%s</h2><p class="vins">%s</p></section>' % (esc(v['t'][lang]), esc(v['p'][lang])))
    main = '''<main id="main">
<section class="sec carta-pag" aria-labelledby="carta-h1">
  <div class="wrap">
    <div class="cap">
      <div>
        <span class="eyebrow">%s</span>
        <h1 id="carta-h1">%s</h1>
        <p>%s</p>
      </div>
      <div class="cap-accions">
        <a class="btn btn-accent" href="%s" target="_blank" rel="noopener" data-carta>%s<span class="visually-hidden">%s</span></a>
        <a class="btn btn-line" href="tel:+34872204041">872 20 40 41</a>
      </div>
    </div>
    <div class="carta-seccions">
%s
    </div>
    <p class="carta-peu">%s</p>
    <p><a class="link" href="%s">← %s</a></p>
  </div>
</section>
</main>''' % (esc(c['ey']), esc(c['h1']), esc(c['intro']), '@@PDF@@', esc(c['pdf']), esc(d['pdf_nova']),
              '\n'.join(seccions), esc(carta['alergies'][lang]), casa, esc(c['tornar']))
    s = re.sub(r'<main id="main">.*?</main>', lambda m: main, s, count=1, flags=re.S)
    # Menú i peu: les àncores tornen a la portada de l'idioma
    s = re.sub(r'href="#(inici|xiringuito|carta|samarreta|arribar|main)"',
               lambda m: 'href="%s"' % ('#main' if m.group(1) == 'main' else casa + ('' if m.group(1) == 'inici' else '#' + m.group(1))), s)
    return s


def main():
    font = llegeix('index.html'); carta = json.loads(llegeix('carta.json')); T = diccionari(font)
    sitemap = []
    for lang in LANGS:
        d = T[lang]
        # Portada
        carpeta = HOME[lang].rstrip('/')
        s = capcalera(ressenyes(tradueix(font, d), lang), lang, d, carpeta, 'home', d['page_title'], d['page_desc'])
        s = s.replace('@@SCHEMA@@', schema(lang, d, 'home'))
        desti = os.path.join(ARREL, carpeta, 'index.html') if carpeta else os.path.join(ARREL, 'index.html')
        os.makedirs(os.path.dirname(desti), exist_ok=True); open(desti, 'w', encoding='utf-8').write(s)
        # Carta en text
        c = PAG_CARTA[lang]; carpeta = CARTA[lang].rstrip('/')
        s = capcalera(tradueix(font, d), lang, d, carpeta, 'carta', c['title'], c['desc'])
        s = pagina_carta(s, lang, d, carta)
        pre = '../' * carpeta.count('/') + '../'
        s = s.replace('@@PDF@@', pre + PDF[lang]).replace('@@SCHEMA@@', schema(lang, d, 'carta', carta))
        desti = os.path.join(ARREL, carpeta, 'index.html')
        os.makedirs(os.path.dirname(desti), exist_ok=True); open(desti, 'w', encoding='utf-8').write(s)
    # sitemap amb les versions d'idioma de cada pàgina
    urls = []
    for mapa in (HOME, CARTA):
        for l in LANGS:
            alt = ''.join('\n    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (x, BASE + mapa[x]) for x in LANGS)
            urls.append('  <url>\n    <loc>%s</loc>%s\n  </url>' % (BASE + mapa[l], alt))
    open(os.path.join(ARREL, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + '\n'.join(urls) + '\n</urlset>\n')
    open(os.path.join(ARREL, 'robots.txt'), 'w', encoding='utf-8').write('User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n' % BASE)
    open(os.path.join(ARREL, 'llms.txt'), 'w', encoding='utf-8').write('''# Xiringuito la Sal

> Beach bar and restaurant on Ses Oliveres beach in Cadaqués (Costa Brava, Catalonia). Paella-style rice, fresh fish, tapas and desserts on a wood-and-wicker terrace facing the bay.

- Address: Avinguda Víctor Rahola, 25, 17488 Cadaqués, Girona, Spain
- Phone: +34 872 20 40 41 (no booking needed; call to make sure of a table, especially in summer)
- Opening hours: they change with the season, spring to autumn (call to check; the beach bar is taken down in winter)
- Google Maps: %s (4.2 stars from 1,826 Google reviews, October 2026)
- Instagram: https://www.instagram.com/xiringuitolasal/

## Pages
- [Home (English)](%sen/): who we are, menu highlights, reviews, FAQ and how to get here
- [Menu (English)](%sen/menu/): the full menu as text
- [Carta (català)](%scarta/) · [Carta (español)](%ses/carta/) · [Carte (français)](%sfr/carte/)
''' % (MAPS, BASE, BASE, BASE, BASE, BASE))
    print('Fet: 4 portades, 4 cartes, sitemap.xml, robots.txt, llms.txt')


if __name__ == '__main__':
    main()
