import unicodedata, re, json, base64, io, html, sys
from pathlib import Path
from PIL import Image
import markdown

S = Path(__file__).parent
PAGES = S / 'pages'
IMGS = S / 'images'

def webp_uri(im, maxw, q=82):
    im = im.copy()
    im.thumbnail((maxw, maxw * 4))
    b = io.BytesIO()
    im.save(b, 'WEBP', quality=q, method=6)
    return 'data:image/webp;base64,' + base64.b64encode(b.getvalue()).decode()

# logos
def logo(name, w, q=88):
    im = Image.open(IMGS / 'logos' / name).convert('RGBA')
    im = im.crop(im.split()[3].getbbox())
    return webp_uri(im, w, q)
LOGO = logo('logo.png', 1028, 90)
LOGOM = logo('logo-petit.png', 300, 90)
EMB = {k: logo(f, 300, 80) for k, f in [('sasp', 'sasp.png'), ('ems', 'ems.png'), ('gouv', 'gouv.png'), ('avocat', 'avocat.png'), ('interim', 'jobsinterims.png')]}

# images des pages : chemin dans le dépôt (images/xxx.jpg) ou adresse web
IMG = {}
def img_for(url):
    if url not in IMG:
        if url.startswith('http'):
            IMG[url] = url
        else:
            f = S / url.lstrip('./')
            if not f.exists():
                print('ATTENTION image introuvable :', url); IMG[url] = url
            else:
                IMG[url] = webp_uri(Image.open(f).convert('RGBA'), 900, 80)
    return IMG[url]

# sommaire : fichier | titre | partie
ORDER = []
for line in (S / 'sommaire.txt').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    parts = [x.strip() for x in line.split('|')]
    if len(parts) != 3:
        sys.exit('Ligne mal écrite dans sommaire.txt : ' + line)
    ORDER.append(('', *parts))
CHANGED = {'reprise-d-entreprise', 'police', 'patch-note-du-reglement', 'defcon', 'general-legal-et-illegal'}
SASP_PAGES = {'defcon', 'general-legal-et-illegal', 'groupes-illegaux', 'mort-rp', 'permis-de-port-darmes', 'code-penal'}

MD = markdown.Markdown(extensions=['tables', 'sane_lists', 'md_in_html', 'attr_list'])

def md(text):
    MD.reset()
    text = re.sub(r'<br>[ \t]*\n([ \t]*)([*-]|\d+\.) ', r'\n\n\1\2 ', text)
    text = re.sub(r'\\[ \t]*$', '  ', text, flags=re.M)
    text = re.sub(r'^( +)', lambda m: ' ' * (len(m.group(1)) * 2), text, flags=re.M)
    # task list
    text = re.sub(r'^(\s*)[*-] \[x\] ', r'\1* <span class="tick" aria-hidden="true"></span>', text, flags=re.M)
    text = re.sub(r'^(\s*)[*-] \[ \] ', r'\1* <span class="tick off" aria-hidden="true"></span>', text, flags=re.M)
    return MD.convert(text)

TAG = re.compile(r'^[ \t]*\{%\s*(\w[\w-]*)([^%]*)%\}[ \t]*', re.M)

def parse(text):
    """Return a tree of ('text', str) / (tag, attrs, children)."""
    pos = 0
    stack = [('root', '', [])]
    for m in TAG.finditer(text):
        stack[-1][2].append(('text', text[pos:m.start()]))
        name, attrs = m.group(1), m.group(2)
        pos = m.end()
        if name.startswith('end'):
            node = stack.pop()
            assert node[0] == name[3:], (node[0], name)
            stack[-1][2].append(node)
        elif name in ('embed',):
            stack[-1][2].append((name, attrs, []))
        else:
            stack.append((name, attrs, []))
    stack[-1][2].append(('text', text[pos:]))
    assert len(stack) == 1, [s[0] for s in stack]
    return stack[0]

def dedent(t):
    lines = t.split('\n')
    ind = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
    if not ind:
        return t
    k = min(ind)
    return '\n'.join(l[k:] for l in lines)

def render(node):
    kind = node[0]
    if kind == 'text':
        return md(dedent(node[1]))
    name, attrs, kids = node
    inner = lambda: ''.join(render(k) for k in kids)
    if name == 'root':
        return inner()
    if name == 'hint':
        style = re.search(r'style="(\w+)"', attrs)
        style = style.group(1) if style else 'info'
        label = {'info': 'Conseil', 'warning': 'Important', 'danger': 'Attention', 'success': 'À retenir'}.get(style, 'Note')
        return f'<aside class="hint hint-{style}"><span class="hint-k">{label}</span><div class="hint-b">{inner()}</div></aside>'
    if name == 'stepper':
        return f'<ol class="steps">{inner()}</ol>'
    if name == 'step':
        return f'<li class="step"><div class="step-b">{inner()}</div></li>'
    if name == 'columns':
        cols = [k for k in kids if k[0] == 'column']
        if len(cols) == 2:
            a, b = (''.join(render(k) for k in c[2]) for c in cols)
            if not re.sub(r'<[^>]+>|\s', '', a + b):
                return ''
            return f'<section class="rule"><div class="rule-k">{a}</div><div class="rule-b">{b}</div></section>'
        return '<div class="cols">' + ''.join(f'<div class="col">{render(c)}</div>' for c in cols) + '</div>'
    if name == 'column':
        return inner()
    if name == 'content-ref':
        return f'<div class="ref">{inner()}</div>'
    if name == 'embed':
        url = re.search(r'url="<?([^">]+)>?"', attrs).group(1)
        label = 'Rejoindre le Discord' if 'discord' in url else url
        return f'<a class="embed" href="{html.escape(url)}" target="_blank" rel="noopener"><span class="embed-k">Lien</span><span class="embed-t">{html.escape(label)}</span><span class="embed-u">{html.escape(url)}</span></a>'
    raise ValueError(name)

def clean_html(h, slug):
    h = re.sub(r' align="center"', '', h)
    h = re.sub(r'</?sub>', '', h)
    h = re.sub(r'<mark style="color:\w+;?">', '<mark>', h)
    h = re.sub(r'<p>\s*(&#x20;|\s)*</p>', '', h)
    # links to other pages
    def link(m):
        href = m.group(1)
        mm = re.match(r'(?:/mirage-wl-reglement/)?(?:[\w-]+/)*([\w-]+)\.md(#[\w-]*)?$', href)
        if mm:
            return f'href="#{mm.group(1)}" data-page="{mm.group(1)}"'
        if href.startswith('broken://') or href.startswith('/pages/'):
            return 'data-broken="1"'
        if href.startswith('#'):
            return f'href="#{slug}" data-anchor="{href[1:]}"'
        return f'href="{href}" target="_blank" rel="noopener"'
    h = re.sub(r'href="([^"]*)"', link, h)
    h = re.sub(r'<a data-broken="1">(.*?)</a>', r'<span>\1</span>', h)
    # images
    def img(m):
        url = html.unescape(m.group(1))
        return f'<img src="{img_for(url)}" alt="" loading="lazy"'
    h = re.sub(r'<img src="([^"]*)"', img, h)
    h = re.sub(r'<hr ?/?>', '', h)
    h = re.sub(r'<figcaption>\s*</figcaption>', '', h)
    # tables scroll
    h = h.replace('<table>', '<div class="tbl"><table>').replace('</table>', '</table></div>')
    # highlight SASP mentions
    return h

V2_MARKS = {
  'reprise-d-entreprise': ["Important : l'illégal est autorisé", "Engagement à ne jamais utiliser", "Il n'y a aucune limite au nombre", "Activités illégales au sein", "Salaires et primes", '<div class="tbl">', "Pour repère : l'intérim", "En cas de blanchiment d'argent via"],
  'police': ["Perquisition QG, entrepôt ou entreprise", "Si vous obtenez un mandat pour perquisitionner un QG, un entrepôt"],
  'patch-note-du-reglement': ["V2 (06/10/2026)"],
}
OPEN = re.compile(r'<(li|p|h[2-4]|div class="tbl"|aside class="hint[^"]*")')
def mark_v2(h, slug):
    for ph in V2_MARKS.get(slug, []):
        i = h.find(ph)
        if i < 0:
            continue
        if ph.startswith('<div class="tbl"'):
            j = i
        else:
            js = [m.start() for m in OPEN.finditer(h, 0, i)]
            j = js[-1]
            if h[max(0, j-5):j] == '<li>\n':
                j -= 5
        tag_end = h.index('>', j)
        tag = h[j:tag_end]
        if 'class="' in tag:
            new = tag.replace('class="', 'class="v2 ', 1)
        else:
            new = tag + ' class="v2"'
        h = h[:j] + new + h[tag_end:]
    return h
def chip_sasp(h):
    return re.sub(r'>([^<]*)', lambda m: '>' + re.sub(r'\bSASP\b', '<span class="sasp">SASP</span>', m.group(1)), h)

pages = []
for folder, slug, title, group in ORDER:
    p = PAGES / f'{slug}.md'
    if not p.exists():
        sys.exit(f'Page introuvable : pages/{slug}.md (voir sommaire.txt)')
    t = p.read_text(encoding='utf-8')
    t = re.sub(r'^# .*\n', '', t, count=1, flags=re.M)
    t = re.sub(r'^\\\[Mirage WL\].*\n', '', t, flags=re.M)
    if slug == 'readme':
        # drop V1 banner image
        t = re.sub(r'<figure>.*?</figure>', '', t, flags=re.S)
    h = clean_html(render(parse(t)), slug)
    # ids on headings
    n = [0]
    def hid(m):
        n[0] += 1
        txt = re.sub(r'<[^>]+>', '', m.group(3))
        sid = re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', txt.lower()).encode('ascii', 'ignore').decode()).strip('-') or f'h{n[0]}'
        return f'<h{m.group(1)}{m.group(2)} id="{slug}--{sid}">{m.group(3)}</h{m.group(1)}>'
    h = re.sub(r'<h([2-4])([^>]*)>(.*?)</h\1>', hid, h)
    h = mark_v2(h, slug)
    h = chip_sasp(h)
    heads = re.findall(r'<h([23]) [^>]*id="([^"]+)"[^>]*>(.*?)</h\1>', h)
    if not heads:
        heads = re.findall(r'<h(4) [^>]*id="([^"]+)"[^>]*>(.*?)</h4>', h)
    toc = [dict(l=int(a), id=b, t=html.unescape(re.sub(r'<[^>]+>', '', c)).strip()) for a, b, c in heads]
    pages.append(dict(toc=toc, slug=slug, title=title, group=group, html=h,
                      changed=slug in CHANGED, sasp=slug in SASP_PAGES,
                      text=re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h))).strip()))

tplsrc = (S / 'modele.html').read_text(encoding='utf-8')
EMO = {}
for f in sorted((IMGS / 'emojis').glob('*.png')):
    if re.search(r"['\"]" + f.stem + r"['\"]", tplsrc):
        EMO[f.stem] = webp_uri(Image.open(f).convert('RGBA'), 180, 80)
ICO = {}
for f in sorted((IMGS / 'icones').glob('*.svg')):
    inner = re.search(r'<svg[^>]*>(.*)</svg>', f.read_text(), re.S).group(1)
    inner = re.sub(r'\s+', ' ', inner).strip().replace(' />', ' pathLength="1"/>')
    if re.search(r"['\"]" + f.stem + r"['\"]", tplsrc): ICO[f.stem] = inner
import shutil
LEX = []
lp = PAGES / 'lexique.md'
if lp.exists():
    for m in re.finditer(r'^\s*[-*]\s+\*\*(.+?)\*\*\s*:\s*(.+)$', lp.read_text(encoding='utf-8'), re.M):
        LEX.append([m.group(1).strip(), m.group(2).strip()])
CONSEILS = []
cp = S / 'conseils.txt'
if cp.exists():
    CONSEILS = [l.strip() for l in cp.read_text(encoding='utf-8').splitlines() if l.strip() and not l.strip().startswith('#')]
GAL = sorted(f.name for f in (IMGS / 'galerie').glob('*') if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')) if (IMGS / 'galerie').exists() else []
out = dict(pages=pages, emb=EMB, emo=EMO, ico=ICO, three={}, models={}, galerie=['galerie/' + n for n in GAL], lexique=LEX, conseils=CONSEILS)
page = tplsrc.replace('__LOGO__', LOGO).replace('__LOGOM__', LOGOM).replace('__DATA__', json.dumps(out, ensure_ascii=False).replace('</', '<\\/'))
site = S / 'site'
site.mkdir(exist_ok=True)
if GAL:
    shutil.copytree(IMGS / 'galerie', site / 'galerie', dirs_exist_ok=True)
(site / 'index.html').write_text(page, encoding='utf-8')
print('Site généré :', len(page) // 1024, 'Ko,', len(pages), 'pages')
