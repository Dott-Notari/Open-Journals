"""Scrittura degli articoli nei formati di output (Word, txt, HTML, Excel, JSONL, T-LAB)."""
import html as H
import io
import json
import re
import unicodedata

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml.ns import qn
from docx.shared import Pt
from openpyxl import Workbook
from openpyxl.styles import Border, Font, Side, Alignment

FONT = "Garamond"


def ascii_slug(s, n=60):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s[:n].rstrip("-") or "senza-titolo"


def nome_file(a):
    return f"{a.id:04d}_{(a.data or '0000-00-00')[:10]}_{ascii_slug(a.titolo, 50)}"


def _data_leggibile(a):
    d = a.dt()
    return d.strftime("%d/%m/%Y %H:%M") if d else "data non disponibile"


def righe_meta(a):
    r = [f"Testata: {a.testata}", f"Data: {_data_leggibile(a)}"]
    if a.autori:
        r.append("Autore: " + ", ".join(a.autori))
    if a.sezione:
        r.append(f"Sezione: {a.sezione}")
    if a.tag:
        r.append("Tag: " + ", ".join(a.tag))
    r.append(f"URL: {a.url}")
    if a.note:
        r.append(f"Note: {a.note}")
    return r


# ------------------------------------------------------------------ Word
def _documento():
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    pf = st.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.15
    return doc


def _scrivi_articolo(doc, a):
    p = doc.add_paragraph()
    run = p.add_run(a.titolo or "(senza titolo)")
    run.bold = True
    run.font.size = Pt(13)
    for riga in righe_meta(a):
        r = doc.add_paragraph().add_run(riga)
        r.font.size = Pt(9.5)
    doc.add_paragraph()
    if a.sommario:
        doc.add_paragraph().add_run(a.sommario).italic = True
        doc.add_paragraph()
    for par in a.testo.split("\n"):
        if par.strip():
            doc.add_paragraph(par)


def docx_articolo(a):
    doc = _documento()
    _scrivi_articolo(doc, a)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def docx_corpus(articoli, titolo):
    doc = _documento()
    t = doc.add_paragraph().add_run(titolo)
    t.bold = True
    t.font.size = Pt(14)
    doc.add_paragraph(f"{len(articoli)} articoli")
    for a in articoli:
        doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        _scrivi_articolo(doc, a)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ------------------------------------------------------------------ testo e HTML
def txt_articolo(a):
    return "\n".join([a.titolo, *righe_meta(a), "", a.sommario, "", a.testo]).strip() + "\n"


def html_articolo(a):
    meta = "".join(f"<li>{H.escape(r)}</li>" for r in righe_meta(a))
    corpo = "".join(f"<p>{H.escape(p)}</p>" for p in a.testo.split("\n") if p.strip())
    return (f"<!DOCTYPE html><html lang=\"it\"><head><meta charset=\"utf-8\">"
            f"<title>{H.escape(a.titolo)}</title><style>body{{font-family:Garamond,serif;"
            f"font-size:11pt;max-width:42em;margin:2em auto;line-height:1.4}}p{{margin:0}}"
            f"ul{{font-size:9.5pt;color:#444}}</style></head><body>"
            f"<h1>{H.escape(a.titolo)}</h1><ul>{meta}</ul>"
            f"<p><em>{H.escape(a.sommario)}</em></p><br>{corpo}</body></html>")


# ------------------------------------------------------------------ Excel
COLONNE = [("ID", 6), ("Testata", 16), ("Data", 11), ("Ora", 7), ("Titolo", 60),
           ("Sommario", 50), ("Autori", 22), ("Sezione", 16), ("Tag", 30), ("Parole", 8),
           ("Virgolettati", 11), ("Riservato agli abbonati", 11), ("Testo parziale", 9),
           ("Coerenza titolo/testo", 10), ("Da controllare", 9), ("Note", 30),
           ("Estrazione", 20), ("File", 40), ("URL", 60)]


def xlsx_indice(articoli):
    wb = Workbook()
    ws = wb.active
    ws.title = "Articoli"
    sottile = Side(style="thin", color="000000")
    f_norm, f_int = Font(name=FONT, size=11), Font(name=FONT, size=11, bold=True)
    for c, (nome, larg) in enumerate(COLONNE, 1):
        cell = ws.cell(row=1, column=c, value=nome)
        cell.font, cell.border = f_int, Border(top=sottile, bottom=sottile)
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[cell.column_letter].width = larg
    si_no = lambda v: "" if v is None else ("sì" if v else "no")
    for r, a in enumerate(articoli, 2):
        d = a.dt()
        valori = [a.id, a.testata, d.strftime("%Y-%m-%d") if d else "",
                  d.strftime("%H:%M") if d else "", a.titolo, a.sommario, ", ".join(a.autori),
                  a.sezione, ", ".join(a.tag), a.parole(), len(a.virgolettati),
                  si_no(None if a.accesso_libero is None else not a.accesso_libero), si_no(a.parziale), a.coerenza, si_no(a.sospetto),
                  a.note, a.metodo, nome_file(a), a.url]
        for c, v in enumerate(valori, 1):
            cell = ws.cell(row=r, column=c, value=v)
            cell.font = f_norm
        ws.cell(row=r, column=len(COLONNE)).hyperlink = a.url
    ultima = len(articoli) + 1
    if articoli:
        for c in range(1, len(COLONNE) + 1):
            ws.cell(row=ultima, column=c).border = Border(bottom=sottile)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ------------------------------------------------------------------ JSONL e T-LAB
def jsonl(articoli):
    return "".join(json.dumps(a.to_dict(), ensure_ascii=False) + "\n" for a in articoli)


def _var(v, n=20):
    v = unicodedata.normalize("NFKD", str(v)).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", v).strip("_").lower()[:n] or "nd"


def tlab(articoli):
    """Corpus con righe di intestazione **** e variabili *NOME_valore per T-LAB."""
    blocchi = []
    for a in articoli:
        d = a.giorno()
        variabili = [f"*TESTATA_{_var(a.testata)}",
                     f"*ANNO_{d.year if d else 'nd'}",
                     f"*MESE_{d.strftime('%Y_%m') if d else 'nd'}",
                     f"*SEZIONE_{_var(a.sezione)}",
                     f"*ID_{a.id:04d}"]
        testo = "\n".join(x for x in (a.titolo, a.sommario, a.testo) if x)
        testo = testo.replace("*", "")
        blocchi.append("**** " + " ".join(variabili) + "\n" + testo)
    return "\n\n".join(blocchi) + "\n"
