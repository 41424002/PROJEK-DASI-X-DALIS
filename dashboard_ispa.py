"""
Dasbor Analisis ISPA Balita - 125 desa, 16 kecamatan (data dummy TOBA)

Cara pakai:
  pip install streamlit plotly pandas numpy
  streamlit run dashboard_ispa.py        -> dasbor interaktif (ada filter)
  python dashboard_ispa.py               -> ekspor dashboard_ispa.html (file mandiri)

Letakkan Dummy_Dataset_25Kolom_125Baris.csv di folder yang sama dengan skrip ini.
Semua angka dan grafik dihitung langsung dari dataset tersebut.
"""
import html
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

DATA_PATH = Path(__file__).with_name("Dummy_Dataset_25Kolom_125Baris.csv")
Y, YL = "rasio_ISPA_per_1000_balita", "Rasio ISPA per 1.000 balita"
COL = {"Rendah": "#2a9d8f", "Tinggi": "#e76f51"}
FAKTOR = {
    "persen_RT_kayu_bakar": "% RT pakai kayu bakar",
    "persen_RT_LPG": "% RT pakai LPG",
    "persen_RT_minyak_tanah": "% RT pakai minyak tanah",
    "persen_RT_ada_perokok": "% RT ada perokok",
    "persen_dapur_terpisah": "% dapur terpisah",
    "jarak_ke_puskesmas_km": "Jarak ke puskesmas (km)",
    "ketinggian_mdpl": "Ketinggian (mdpl)",
    "persen_keluarga_miskin": "% keluarga miskin",
    "rata_rata_pendidikan_ibu_tahun": "Pendidikan ibu (tahun)",
    "kepadatan_penduduk_per_km2": "Kepadatan (jiwa/km²)",
}
KORELASI = {**FAKTOR, Y: "Rasio ISPA", "kasus_ISPA_balita": "Kasus ISPA",
            "kasus_pneumonia_balita": "Kasus pneumonia", "kasus_asma_balita": "Kasus asma"}


# ----------------------------------------------------------------- data
NUMERIC_COLUMNS = [
    "id_desa", "tahun_data", "jumlah_penduduk", "jumlah_balita_0_59bln",
    "jumlah_rumah_tangga", "persen_RT_kayu_bakar", "persen_RT_LPG",
    "persen_RT_minyak_tanah", "persen_RT_ada_perokok", "persen_dapur_terpisah",
    "jarak_ke_puskesmas_km", "kasus_ISPA_balita", "kasus_pneumonia_balita",
    "kasus_asma_balita", "luas_wilayah_km2", "ketinggian_mdpl",
    "persen_keluarga_miskin", "rata_rata_pendidikan_ibu_tahun",
    "rasio_ISPA_per_1000_balita", "kepadatan_penduduk_per_km2", "is_dummy",
]


def prepare_data(df):
    """Validate editable input and refresh columns calculated by the dashboard."""
    required = {"nama_kecamatan", "nama_desa", "jumlah_balita_0_59bln",
                "kasus_ISPA_balita", "persen_RT_kayu_bakar"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError("Kolom wajib tidak ditemukan: " + ", ".join(missing))
    result = df.copy()
    for column in NUMERIC_COLUMNS:
        if column in result:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    if result[["jumlah_balita_0_59bln", "kasus_ISPA_balita",
               "persen_RT_kayu_bakar"]].isna().any().any():
        raise ValueError("Jumlah balita, kasus ISPA, dan persentase kayu bakar harus berupa angka.")
    balita = result["jumlah_balita_0_59bln"].replace(0, np.nan)
    result[Y] = (result["kasus_ISPA_balita"] / balita * 1000).fillna(0).round(1)
    result["kategori_kayu_bakar"] = np.where(
        result["persen_RT_kayu_bakar"] >= 50, "Tinggi", "Rendah"
    )
    return result


def load_data(path=DATA_PATH):
    return prepare_data(pd.read_csv(path))


def save_data(df):
    prepare_data(df).to_csv(DATA_PATH, index=False)


def rate(d):
    return d.kasus_ISPA_balita.sum() / d.jumlah_balita_0_59bln.sum() * 1000


def agg_kec(d):
    g = d.groupby("nama_kecamatan").agg(
        desa=("id_desa", "count"), penduduk=("jumlah_penduduk", "sum"),
        balita=("jumlah_balita_0_59bln", "sum"), ispa=("kasus_ISPA_balita", "sum"),
        pneumonia=("kasus_pneumonia_balita", "sum"), asma=("kasus_asma_balita", "sum"),
    ).reset_index()
    g["rasio"] = g.ispa / g.balita * 1000
    return g


def kpis(d):
    return [
        ("Jumlah desa", f"{len(d):,}"), ("Penduduk", f"{d.jumlah_penduduk.sum():,}"),
        ("Balita (0-59 bln)", f"{d.jumlah_balita_0_59bln.sum():,}"),
        ("Kasus ISPA", f"{d.kasus_ISPA_balita.sum():,}"),
        ("Rasio ISPA /1.000 balita", f"{rate(d):.0f}"),
        ("Pneumonia / Asma", f"{d.kasus_pneumonia_balita.sum()} / {d.kasus_asma_balita.sum()}"),
    ]


def insights(d):
    if len(d) < 3:
        return []
    k = agg_kec(d).sort_values("rasio")
    hi, lo = k.iloc[-1], k.iloc[0]
    top = d.loc[d[Y].idxmax()]
    out = [
        f"Rasio ISPA keseluruhan **{rate(d):.0f}** per 1.000 balita "
        f"({d.kasus_ISPA_balita.sum():,} kasus pada {d.jumlah_balita_0_59bln.sum():,} balita).",
        f"Kecamatan dengan rasio tertinggi: **{hi.nama_kecamatan}** ({hi.rasio:.0f}); "
        f"terendah: **{lo.nama_kecamatan}** ({lo.rasio:.0f}).",
        f"Desa dengan rasio tertinggi: **{top.nama_desa}** ({top.nama_kecamatan}) = {top[Y]:.0f}.",
    ]
    s = d.groupby("kategori_kayu_bakar")[["kasus_ISPA_balita", "jumlah_balita_0_59bln"]].sum()
    if {"Rendah", "Tinggi"} <= set(s.index):
        r = s.kasus_ISPA_balita / s.jumlah_balita_0_59bln * 1000
        out.append(f"Desa kategori kayu bakar **Tinggi** rasionya {r['Tinggi']:.0f} vs **Rendah** "
                   f"{r['Rendah']:.0f} ({(r['Tinggi'] / r['Rendah'] - 1) * 100:+.0f}%).")
    c = d[list(FAKTOR)].corrwith(d[Y]).dropna()
    if len(c):
        f = c.abs().idxmax()
        kuat = "lemah" if abs(c[f]) < 0.3 else "sedang/kuat"
        out.append(f"Faktor dengan korelasi terkuat terhadap rasio: **{FAKTOR[f]}** (r = {c[f]:.2f}, {kuat}).")
    out.append(f"**{(d.jarak_ke_puskesmas_km > 15).mean() * 100:.0f}%** desa berjarak lebih dari 15 km "
               f"dari puskesmas (rata-rata {d.jarak_ke_puskesmas_km.mean():.1f} km).")
    return out


# --------------------------------------------------------------- grafik
def _fmt(f, h=380):
    f.update_layout(height=h, margin=dict(l=10, r=10, t=55, b=10), title_font_size=15,
                    legend=dict(orientation="h", y=-0.2))
    return f


def fig_hist(d):
    f = px.histogram(d, x=Y, nbins=20, color_discrete_sequence=["#457b9d"],
                     title="Sebaran rasio ISPA antar desa", labels={Y: YL})
    f.add_vline(x=rate(d), line_dash="dash", line_color="#e76f51",
                annotation_text=f"Gabungan: {rate(d):.0f}")
    return _fmt(f.update_layout(yaxis_title="Jumlah desa"))


def fig_kec_rasio(d):
    k = agg_kec(d).sort_values("rasio")
    f = px.bar(k, x="rasio", y="nama_kecamatan", orientation="h", color="rasio",
               color_continuous_scale="YlOrRd", text=k.rasio.round(0),
               title="Rasio ISPA per 1.000 balita menurut kecamatan",
               labels={"rasio": YL, "nama_kecamatan": ""})
    f.add_vline(x=rate(d), line_dash="dash", line_color="gray")
    return _fmt(f.update_layout(coloraxis_showscale=False), 520)


def fig_donut(d):
    c = d.kategori_kayu_bakar.value_counts().reset_index()
    f = px.pie(c, names="kategori_kayu_bakar", values="count", hole=0.55, color="kategori_kayu_bakar",
               color_discrete_map=COL, title="Proporsi desa menurut kategori kayu bakar")
    return _fmt(f.update_traces(textinfo="label+value+percent"))


def fig_top(d, n=10):
    t = d.nlargest(n, Y).iloc[::-1]
    f = px.bar(t, x=Y, y=t.nama_desa + " (" + t.nama_kecamatan + ")", orientation="h",
               color="kategori_kayu_bakar", color_discrete_map=COL, text=t[Y].round(0),
               title=f"{n} desa dengan rasio ISPA tertinggi", labels={Y: YL, "y": ""})
    return _fmt(f, 460)


def fig_kasus_kec(d):
    k = agg_kec(d).sort_values("ispa", ascending=False)
    f = px.bar(k, x="nama_kecamatan", y="ispa", color_discrete_sequence=["#457b9d"],
               title="Total kasus ISPA balita per kecamatan", labels={"ispa": "Kasus ISPA", "nama_kecamatan": ""})
    return _fmt(f.update_xaxes(tickangle=-40), 420)


def fig_pneu_asma(d):
    k = agg_kec(d).sort_values("pneumonia", ascending=False)
    f = px.bar(k, x="nama_kecamatan", y=["pneumonia", "asma"], barmode="stack",
               title="Kasus pneumonia dan asma balita per kecamatan",
               color_discrete_sequence=["#e63946", "#f4a261"],
               labels={"value": "Kasus", "nama_kecamatan": "", "variable": ""})
    return _fmt(f.update_xaxes(tickangle=-40), 420)


def fig_treemap(d):
    f = px.treemap(d, path=[px.Constant("Toba"), "nama_kecamatan", "nama_desa"],
                   values="jumlah_balita_0_59bln", color=Y, color_continuous_scale="YlOrRd",
                   title="Peta pohon: ukuran = jumlah balita, warna = rasio ISPA",
                   labels={Y: "Rasio ISPA"})
    return _fmt(f, 520)


def fig_energi(d):
    k = d.groupby("nama_kecamatan")[["persen_RT_kayu_bakar", "persen_RT_LPG", "persen_RT_minyak_tanah"]].mean().reset_index()
    k = k.sort_values("persen_RT_kayu_bakar", ascending=False)
    f = px.bar(k, x="nama_kecamatan", y=["persen_RT_kayu_bakar", "persen_RT_LPG", "persen_RT_minyak_tanah"],
               barmode="group", title="Rata-rata bahan bakar memasak per kecamatan (% RT)",
               labels={"value": "% RT", "nama_kecamatan": "", "variable": ""},
               color_discrete_sequence=["#e76f51", "#2a9d8f", "#8d99ae"])
    f.for_each_trace(lambda t: t.update(name=FAKTOR[t.name]))
    return _fmt(f.update_xaxes(tickangle=-40), 440)


def fig_scatter(d, x):
    log = x == "kepadatan_penduduk_per_km2"
    f = px.scatter(d, x=x, y=Y, color="kategori_kayu_bakar", size="jumlah_balita_0_59bln",
                   hover_name="nama_desa", hover_data=["nama_kecamatan"], color_discrete_map=COL,
                   log_x=log, labels={x: FAKTOR[x], Y: YL, "kategori_kayu_bakar": "Kategori kayu bakar"})
    r = d[x].corr(d[Y])
    lx = np.log10(d[x]) if log else d[x]
    m, b = np.polyfit(lx, d[Y], 1)
    xs = np.linspace(lx.min(), lx.max(), 50)
    f.add_trace(go.Scatter(x=10 ** xs if log else xs, y=m * xs + b, mode="lines", name="Tren linear",
                           line=dict(color="gray", dash="dash")))
    f.update_layout(title=f"{FAKTOR[x]} vs rasio ISPA (r = {r:.2f})")
    return _fmt(f)


def fig_box(d):
    f = px.box(d, x="kategori_kayu_bakar", y=Y, color="kategori_kayu_bakar", points="all",
               color_discrete_map=COL, title="Rasio ISPA: kategori kayu bakar Rendah vs Tinggi",
               labels={Y: YL, "kategori_kayu_bakar": "Kategori kayu bakar"},
               hover_name="nama_desa", category_orders={"kategori_kayu_bakar": ["Rendah", "Tinggi"]})
    return _fmt(f.update_layout(showlegend=False))


def fig_corr(d):
    c = d[list(KORELASI)].corr().rename(index=KORELASI, columns=KORELASI)
    f = px.imshow(c, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                  title="Matriks korelasi variabel utama", aspect="auto")
    return _fmt(f, 560)


def fig_bin(d, col, bins, labels, title, xlab):
    t = d.assign(g=pd.cut(d[col], bins=bins, labels=labels, right=False)).groupby("g", observed=True).agg(
        ispa=("kasus_ISPA_balita", "sum"), balita=("jumlah_balita_0_59bln", "sum"), desa=("id_desa", "count")).reset_index()
    t["rasio"] = t.ispa / t.balita * 1000
    f = px.bar(t, x="g", y="rasio", text=t.rasio.round(0), hover_data=["desa"],
               color_discrete_sequence=["#457b9d"], title=title, labels={"g": xlab, "rasio": YL})
    return _fmt(f, 340)


def fig_miskin_pendidikan(d):
    f = px.scatter(d, x="persen_keluarga_miskin", y="rata_rata_pendidikan_ibu_tahun", color=Y,
                   size="jumlah_balita_0_59bln", hover_name="nama_desa", color_continuous_scale="YlOrRd",
                   title="Kemiskinan vs pendidikan ibu (warna = rasio ISPA)",
                   labels={"persen_keluarga_miskin": "% keluarga miskin",
                           "rata_rata_pendidikan_ibu_tahun": "Pendidikan ibu (tahun)", Y: "Rasio ISPA"})
    return _fmt(f)


def fig_jarak_kasus(d):
    f = px.scatter(d, x="jarak_ke_puskesmas_km", y="kasus_pneumonia_balita", color="kategori_kayu_bakar",
                   color_discrete_map=COL, hover_name="nama_desa", opacity=0.7,
                   title="Jarak ke puskesmas vs kasus pneumonia balita",
                   labels={"jarak_ke_puskesmas_km": "Jarak ke puskesmas (km)",
                           "kasus_pneumonia_balita": "Kasus pneumonia", "kategori_kayu_bakar": "Kategori kayu bakar"})
    return _fmt(f)


def sections(d, xs):
    """Susunan tampilan: {nama tab: [baris grafik]} (dipakai Streamlit & HTML)."""
    scat = [fig_scatter(d, x) for x in xs]
    scat_rows = [scat[i:i + 2] for i in range(0, len(scat), 2)]
    return {
        "Ringkasan": [[fig_hist(d), fig_donut(d)], [fig_kec_rasio(d), fig_top(d)]],
        "Per Kecamatan": [[fig_kasus_kec(d), fig_pneu_asma(d)], [fig_treemap(d)], [fig_energi(d)]],
        "Faktor Risiko": scat_rows + [[fig_box(d), fig_corr(d)],
            [fig_bin(d, "persen_RT_kayu_bakar", [0, 25, 50, 75, 101], ["<25%", "25-50%", "50-75%", "≥75%"],
                     "Rasio ISPA menurut % RT kayu bakar", "% RT kayu bakar")]],
        "Akses & Sosial-Ekonomi": [
            [fig_bin(d, "jarak_ke_puskesmas_km", [0, 5, 10, 15, 20, 26], ["0-5", "5-10", "10-15", "15-20", "20-25"],
                     "Rasio ISPA menurut jarak ke puskesmas", "Jarak (km)"),
             fig_bin(d, "rata_rata_pendidikan_ibu_tahun", [0, 6, 8, 10, 99], ["<6", "6-8", "8-10", "≥10"],
                     "Rasio ISPA menurut pendidikan ibu", "Pendidikan ibu (tahun)")],
            [fig_miskin_pendidikan(d), fig_jarak_kasus(d)]],
    }


# ---------------------------------------------------------- ekspor HTML
def export_html(df, out="dashboard_ispa.html"):
    data_json = json.dumps(df.to_dict(orient="records"), ensure_ascii=True)
    kec_options = "".join(f'<option value="{html.escape(v)}" selected>{html.escape(v)}</option>' for v in sorted(df.nama_kecamatan.unique()))
    factor_options = "".join(f'<option value="{html.escape(k)}">{html.escape(v)}</option>' for k, v in FAKTOR.items())
    plotly_bootstrap = fig_hist(df).to_html(full_html=False, include_plotlyjs=True)
    page = f"""<!doctype html><html lang="id"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dasbor ISPA Balita</title>
<style>
:root{{--navy:#17324d;--ink:#203040;--muted:#667788;--line:#dbe3e9;--paper:#f3f6f8;--white:#fff;--teal:#2a9d8f;--coral:#e76f51}}
*{{box-sizing:border-box}}body{{font-family:Inter,ui-sans-serif,system-ui,sans-serif;margin:0;background:var(--paper);color:var(--ink)}}
header{{background:linear-gradient(120deg,#17324d,#286b73);color:white;padding:26px clamp(18px,4vw,56px)}}header h1{{margin:0 0 6px;font-size:clamp(24px,3vw,36px)}}header p{{margin:0;opacity:.82}}
main{{max-width:1550px;margin:auto;padding:20px clamp(16px,3vw,44px) 44px}}h2{{font-size:18px;margin:30px 0 10px}}
.filter-panel{{background:var(--white);border:1px solid var(--line);border-radius:10px;padding:16px;box-shadow:0 5px 18px #17324d0d}}.filter-head{{display:flex;justify-content:space-between;gap:16px;align-items:center;margin-bottom:14px}}.filter-head strong{{font-size:15px}}.filter-head span{{display:block;color:var(--muted);font-size:12px;margin-top:3px}}.control-actions{{display:flex;gap:7px;flex-wrap:wrap}}.control-actions button{{background:#edf3f5;color:var(--navy);min-height:32px;padding:6px 10px;font-size:12px}}.control-actions button:last-child{{background:var(--navy);color:white}}
.filters{{display:grid;grid-template-columns:1.4fr 1fr 1fr 1.2fr;gap:12px;align-items:end}}label{{display:grid;gap:6px;font-size:12px;font-weight:700;color:var(--muted)}}select,input{{width:100%;min-height:38px;border:1px solid #c9d5dd;border-radius:6px;padding:8px;background:white;color:var(--ink)}}select[multiple]{{min-height:105px}}
button{{min-height:38px;border:0;border-radius:6px;padding:8px 14px;background:var(--navy);color:white;font-weight:700;cursor:pointer}}button:hover{{background:#245579}}
.kpis{{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-top:16px}}.kpi,.ins,.card,.table-wrap{{background:var(--white);border:1px solid var(--line);border-radius:10px}}.kpi{{padding:14px}}.kpi span{{display:block;font-size:12px;color:var(--muted)}}.kpi b{{display:block;margin-top:6px;font-size:23px}}
.ins{{padding:8px 22px;line-height:1.65}}.ins li{{margin:5px 0}}.chart-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}.card{{min-width:0;padding:6px}}.chart{{height:420px}}.table-wrap{{overflow:auto;max-height:480px}}table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:nowrap}}th{{position:sticky;top:0;background:#edf3f5;color:var(--muted)}}td input{{min-width:110px;padding:5px;font-size:12px}}.status{{color:var(--muted);font-size:13px;margin:12px 0}}
.tab-nav{{display:flex;gap:4px;overflow-x:auto;border-bottom:2px solid #dbe3e9;margin-top:24px}}.tab-button{{border-radius:0;background:transparent;color:var(--ink);white-space:nowrap;border-bottom:3px solid transparent;padding:12px 14px;margin-bottom:-2px}}.tab-button:hover{{background:#edf3f5;color:var(--navy)}}.tab-button.active{{color:#e63946;border-bottom-color:#e63946;background:transparent}}.tab-panel{{display:none}}.tab-panel.active{{display:block}}
.dropdown{{position:relative}}.dropdown-toggle{{width:100%;text-align:left;background:white;color:var(--ink);border:1px solid #c9d5dd;font-weight:400}}.dropdown-toggle::after{{content:'▾';float:right;color:var(--muted)}}.dropdown-menu{{display:none;position:absolute;z-index:20;top:calc(100% + 4px);left:0;right:0;max-height:240px;overflow:auto;background:white;border:1px solid #c9d5dd;border-radius:6px;padding:8px;box-shadow:0 8px 20px #17324d22}}.dropdown.open .dropdown-menu{{display:block}}.check-option{{display:flex;grid-template-columns:none;align-items:center;gap:8px;padding:7px 5px;font-weight:400;color:var(--ink);cursor:pointer}}.check-option:hover{{background:#edf3f5}}.check-option input{{width:16px;min-height:16px;margin:0;accent-color:#e63946}}
@media(max-width:1050px){{.filters{{grid-template-columns:1fr 1fr}}.kpis{{grid-template-columns:repeat(3,1fr)}}}}@media(max-width:700px){{.chart-grid{{grid-template-columns:1fr}}.kpis{{grid-template-columns:repeat(2,1fr)}}.filters{{grid-template-columns:1fr}}}}
</style></head><body><header><h1>Dasbor Analisis ISPA Balita</h1><p id="subtitle"></p></header><main>
<section class="filter-panel"><div class="filter-head"><div><strong>Kontrol analisis</strong><span>Perubahan filter langsung memperbarui indikator, grafik, dan tabel.</span></div><div class="control-actions"><button id="allKec">Semua kecamatan</button><button id="clearKec">Kosongkan kecamatan</button><button id="allKat">Semua kategori</button><button id="download">Unduh CSV</button><button id="reset">Reset</button></div></div><div class="filters"><label>Kecamatan<div class="dropdown" id="kecDropdown"><button type="button" class="dropdown-toggle" id="kecToggle">Semua kecamatan</button><div class="dropdown-menu" id="kec"></div></div></label><label>Kategori kayu bakar<div class="dropdown" id="katDropdown"><button type="button" class="dropdown-toggle" id="katToggle">Semua kategori</button><div class="dropdown-menu" id="kat"></div></div></label><label>Jarak maksimum (km)<input id="jarak" type="range" step="0.1"><output id="jarakValue"></output></label><label>Faktor scatter<select id="factor">{factor_options}</select></label></div></section>
<div class="status" id="status"></div><section class="kpis" id="kpis"></section><h2>Temuan utama dari data terfilter</h2><ul class="ins" id="insights"></ul>
<nav class="tab-nav" aria-label="Menu analisis"><button class="tab-button active" data-tab="ringkasan">Ringkasan</button><button class="tab-button" data-tab="kecamatan">Per Kecamatan</button><button class="tab-button" data-tab="risiko">Faktor Risiko</button><button class="tab-button" data-tab="akses">Akses &amp; Sosial-Ekonomi</button><button class="tab-button" data-tab="data">Data</button></nav>
<section id="ringkasan" class="tab-panel active"><h2>Ringkasan visualisasi</h2><section class="chart-grid"><div class="card"><div id="hist" class="chart"></div></div><div class="card"><div id="top" class="chart"></div></div></section></section>
<section id="kecamatan" class="tab-panel"><h2>Analisis per kecamatan</h2><section class="chart-grid"><div class="card"><div id="kecChart" class="chart"></div></div></section></section>
<section id="risiko" class="tab-panel"><h2>Faktor risiko</h2><section class="chart-grid"><div class="card"><div id="scatter" class="chart"></div></div></section></section>
<section id="akses" class="tab-panel"><h2>Akses &amp; sosial-ekonomi</h2><section class="chart-grid"><div class="card"><div id="access" class="chart"></div></div></section></section>
<section id="data" class="tab-panel"><h2>Data desa</h2><section class="filter-panel"><div class="filter-head"><div><strong>Edit data langsung</strong><span>Ubah sel di tabel, unggah CSV pengganti, atau unduh salinan data terbaru.</span></div><div class="control-actions"><input id="upload" type="file" accept=".csv,text/csv"><button id="downloadAll">Unduh semua data</button></div></div><div class="table-wrap"><table><thead id="tableHead"></thead><tbody id="tableBody"></tbody></table></div></section></section></main>
<div hidden>{plotly_bootstrap}</div><script>let DATA={data_json};const FACTORS={json.dumps(FAKTOR, ensure_ascii=True)};const COLORS={{Rendah:'#2a9d8f',Tinggi:'#e76f51'}};
const $=id=>document.getElementById(id), num=n=>Number(n).toLocaleString('id-ID'), selected=id=>[...$(id).querySelectorAll('input[type="checkbox"]:checked')].map(o=>o.value);
const layoutBase={{paper_bgcolor:'white',plot_bgcolor:'white',font:{{family:'Inter, system-ui',color:'#203040'}},margin:{{l:55,r:20,t:55,b:55}},legend:{{orientation:'h',y:-.2}}}};
function filterData(){{const kec=selected('kec'),kat=selected('kat'),max=Number($('jarak').value);return DATA.filter(d=>kec.includes(d.nama_kecamatan)&&kat.includes(d.kategori_kayu_bakar)&&d.jarak_ke_puskesmas_km<=max)}}
function rate(d){{const balita=d.reduce((s,x)=>s+x.jumlah_balita_0_59bln,0);return balita?d.reduce((s,x)=>s+x.kasus_ISPA_balita,0)/balita*1000:0}}
function aggregate(d){{const m={{}};d.forEach(x=>{{const k=x.nama_kecamatan;m[k]??={{desa:0,balita:0,ispa:0}};m[k].desa++;m[k].balita+=x.jumlah_balita_0_59bln;m[k].ispa+=x.kasus_ISPA_balita}});return Object.entries(m).map(([nama_kecamatan,x])=>({{nama_kecamatan,desa:x.desa,rasio:x.ispa/x.balita*1000}})).sort((a,b)=>a.rasio-b.rasio)}}
function render(d){{const r=rate(d), totalBalita=d.reduce((s,x)=>s+x.jumlah_balita_0_59bln,0),ispa=d.reduce((s,x)=>s+x.kasus_ISPA_balita,0);$('status').textContent=`Menampilkan ${{num(d.length)}} dari ${{num(DATA.length)}} desa`;$('subtitle').textContent=`${{num(d.length)}} desa terpilih · ${{new Set(d.map(x=>x.nama_kecamatan)).size}} kecamatan · tahun ${{DATA[0].tahun_data}} · data dummy`;
$('kpis').innerHTML=[['Jumlah desa',num(d.length)],['Penduduk',num(d.reduce((s,x)=>s+x.jumlah_penduduk,0))],['Balita (0-59 bln)',num(totalBalita)],['Kasus ISPA',num(ispa)],['Rasio ISPA /1.000',r.toFixed(0)],['Pneumonia / Asma',`${{num(d.reduce((s,x)=>s+x.kasus_pneumonia_balita,0))}} / ${{num(d.reduce((s,x)=>s+x.kasus_asma_balita,0))}}`]].map(x=>`<div class="kpi"><span>${{x[0]}}</span><b>${{x[1]}}</b></div>`).join('');
const groups=aggregate(d),hi=groups.at(-1),lo=groups[0],top=[...d].sort((a,b)=>b.rasio_ISPA_per_1000_balita-a.rasio_ISPA_per_1000_balita)[0];$('insights').innerHTML=d.length?`<li>Rasio ISPA keseluruhan <b>${{r.toFixed(0)}}</b> per 1.000 balita dari ${{num(ispa)}} kasus.</li><li>Kecamatan tertinggi: <b>${{hi?.nama_kecamatan||'-'}}</b> (${{hi?.rasio.toFixed(0)||0}}), terendah: <b>${{lo?.nama_kecamatan||'-'}}</b> (${{lo?.rasio.toFixed(0)||0}}).</li><li>Desa dengan rasio tertinggi: <b>${{top?.nama_desa||'-'}}</b> (${{top?.rasio_ISPA_per_1000_balita?.toFixed(0)||0}}).</li>`:'<li>Tidak ada data yang cocok dengan filter.</li>';
plotCharts(d,groups,r);renderTable(d)}}
function plotCharts(d,groups,r){{Plotly.react('hist',[{{x:d.map(x=>x.rasio_ISPA_per_1000_balita),type:'histogram',marker:{{color:'#457b9d'}},nbinsx:20,name:'Desa'}}],{{...layoutBase,title:'Sebaran rasio ISPA antar desa',xaxis:{{title:'Rasio ISPA per 1.000 balita'}},shapes:[{{type:'line',x0:r,x1:r,y0:0,y1:1,yref:'paper',line:{{dash:'dash',color:'#e76f51'}}}}]}});Plotly.react('kecChart',[{{x:groups.map(x=>x.rasio),y:groups.map(x=>x.nama_kecamatan),type:'bar',orientation:'h',marker:{{color:groups.map(x=>x.rasio),colorscale:'YlOrRd'}},text:groups.map(x=>x.rasio.toFixed(0)),textposition:'auto'}}],{{...layoutBase,title:'Rasio ISPA menurut kecamatan',xaxis:{{title:'Rasio per 1.000 balita'}}}});const factor=$('factor').value;const colors=d.map(x=>COLORS[x.kategori_kayu_bakar]);Plotly.react('scatter',[{{x:d.map(x=>x[factor]),y:d.map(x=>x.rasio_ISPA_per_1000_balita),mode:'markers',type:'scatter',marker:{{color:colors,size:d.map(x=>Math.max(7,Math.sqrt(x.jumlah_balita_0_59bln))) }},text:d.map(x=>x.nama_desa),hovertemplate:'%{{text}}<br>%{{x}}<br>Rasio: %{{y:.0f}}<extra></extra>'}}],{{...layoutBase,title:`${{FACTORS[factor]}} vs rasio ISPA`,xaxis:{{title:FACTORS[factor]}},yaxis:{{title:'Rasio ISPA per 1.000 balita'}}}});const tops=[...d].sort((a,b)=>b.rasio_ISPA_per_1000_balita-a.rasio_ISPA_per_1000_balita).slice(0,10).reverse();Plotly.react('top',[{{x:tops.map(x=>x.rasio_ISPA_per_1000_balita),y:tops.map(x=>x.nama_desa),type:'bar',orientation:'h',marker:{{color:tops.map(x=>COLORS[x.kategori_kayu_bakar])}},text:tops.map(x=>x.rasio_ISPA_per_1000_balita.toFixed(0)),textposition:'auto'}}],{{...layoutBase,title:'10 desa dengan rasio tertinggi',xaxis:{{title:'Rasio ISPA per 1.000 balita'}}}});Plotly.react('access',[{{x:d.map(x=>x.jarak_ke_puskesmas_km),y:d.map(x=>x.kasus_pneumonia_balita),mode:'markers',type:'scatter',marker:{{color:d.map(x=>COLORS[x.kategori_kayu_bakar]),size:9}},text:d.map(x=>x.nama_desa),hovertemplate:'%{{text}}<br>Jarak: %{{x}} km<br>Pneumonia: %{{y}}<extra></extra>'}}],{{...layoutBase,title:'Jarak ke puskesmas vs kasus pneumonia',xaxis:{{title:'Jarak ke puskesmas (km)'}},yaxis:{{title:'Kasus pneumonia'}}}})}}
function renderTable(d){{const cols=Object.keys(DATA[0]||{{}});$('tableHead').innerHTML='<tr>'+cols.map(c=>`<th>${{c.replaceAll('_',' ')}}</th>`).join('')+'</tr>';$('tableBody').innerHTML=d.map(x=>{{const i=DATA.indexOf(x);return `<tr>${{cols.map(c=>`<td><input data-index="${{i}}" data-column="${{c}}" value="${{String(x[c]??'').replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;')}}"></td>`).join('')}}</tr>`}}).join('')}}
function refreshDerived(){{DATA.forEach(x=>{{const balita=Number(x.jumlah_balita_0_59bln)||0;const kasus=Number(x.kasus_ISPA_balita)||0;const kayu=Number(x.persen_RT_kayu_bakar)||0;x.rasio_ISPA_per_1000_balita=balita?kasus/balita*1000:0;x.kategori_kayu_bakar=kayu>=50?'Tinggi':'Rendah'}})}}
function csvText(rows){{const cols=Object.keys(rows[0]||{{}}),quote=v=>`"${{String(v??'').replaceAll('"','""')}}"`;return [cols.join(','),...rows.map(row=>cols.map(c=>quote(row[c])).join(','))].join('\\n')}}
function downloadRows(rows,name){{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csvText(rows)],{{type:'text/csv'}}));a.download=name;a.click();URL.revokeObjectURL(a.href)}}
function parseCsv(text){{const lines=text.trim().split(/\\r?\\n/),parse=line=>{{const out=[],re=/(,|\\r?\\n|\\r|^)(?:"([^"]*(?:""[^"]*)*)"|([^",\\r\\n]*))/gi;let m;while((m=re.exec(line))!==null)out.push(m[2]!==undefined?m[2].replaceAll('""','"'):m[3]);return out}},headers=parse(lines.shift());return lines.filter(Boolean).map(line=>Object.fromEntries(parse(line).map((v,i)=>[headers[i],v])))}}
function csvDownload(d){{const cols=Object.keys(DATA[0]);const quote=v=>`"${{String(v??'').replaceAll('"','""')}}"`;const csv=[cols.join(','),...d.map(row=>cols.map(c=>quote(row[c])).join(','))].join('\\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{{type:'text/csv'}}));a.download='data_ispa_terfilter.csv';a.click();URL.revokeObjectURL(a.href)}}
function updateLabels(){{const kec=selected('kec'),kat=selected('kat');$('kecToggle').textContent=kec.length?`${{kec.length}} kecamatan dipilih`:'Pilih kecamatan';$('katToggle').textContent=kat.length?`${{kat.length}} kategori dipilih`:'Pilih kategori'}}function setAll(id,value){{$(id).querySelectorAll('input[type="checkbox"]').forEach(o=>o.checked=value);updateLabels();update()}}function update(){{updateLabels();render(filterData())}}document.querySelectorAll('.dropdown-toggle').forEach(button=>button.addEventListener('click',e=>{{e.stopPropagation();const dropdown=button.parentElement;document.querySelectorAll('.dropdown.open').forEach(item=>{{if(item!==dropdown)item.classList.remove('open')}});dropdown.classList.toggle('open')}}));document.addEventListener('click',()=>document.querySelectorAll('.dropdown.open').forEach(item=>item.classList.remove('open')));document.querySelectorAll('.tab-button').forEach(button=>button.addEventListener('click',()=>{{document.querySelectorAll('.tab-button,.tab-panel').forEach(element=>element.classList.remove('active'));button.classList.add('active');$(button.dataset.tab).classList.add('active');window.dispatchEvent(new Event('resize'))}}));$('tableBody').addEventListener('change',e=>{{if(!e.target.matches('input[data-index]'))return;const i=Number(e.target.dataset.index),c=e.target.dataset.column;DATA[i][c]=e.target.value;refreshDerived();update()}});$('kec').addEventListener('change',update);$('kat').addEventListener('change',update);$('upload').addEventListener('change',e=>{{const file=e.target.files[0];if(!file)return;const reader=new FileReader();reader.onload=()=>{{try{{const rows=parseCsv(reader.result);if(!rows.length)throw Error('CSV kosong');DATA=rows;refreshDerived();buildFilters();update()}}catch(error){{alert('CSV tidak dapat dibaca: '+error.message)}}}};reader.readAsText(file)}});function buildFilters(){{const values=[...new Set(DATA.map(x=>x.nama_kecamatan))].sort();$('kec').innerHTML=values.map(v=>`<label class="check-option"><input type="checkbox" value="${{v}}" checked>${{v}}</label>`).join('');$('kat').innerHTML=['Rendah','Tinggi'].map(v=>`<label class="check-option"><input type="checkbox" value="${{v}}" checked>${{v}}</label>`).join('');$('jarak').max=Math.max(...DATA.map(x=>Number(x.jarak_ke_puskesmas_km)||0));$('jarak').value=$('jarak').max;updateLabels()}}$('factor').addEventListener('change',update);$('jarak').addEventListener('input',()=>{{$('jarakValue').value=`hingga ${{$('jarak').value}} km`;update()}});$('allKec').onclick=()=>setAll('kec',true);$('clearKec').onclick=()=>setAll('kec',false);$('allKat').onclick=()=>setAll('kat',true);$('download').onclick=()=>downloadRows(filterData(),'data_ispa_terfilter.csv');$('downloadAll').onclick=()=>downloadRows(DATA,'data_ispa_diperbarui.csv');$('reset').onclick=()=>{{setAll('kec',true);setAll('kat',true);$('jarak').value=$('jarak').max;$('jarakValue').value=`hingga ${{$('jarak').value}} km`;update()}};buildFilters();$('jarak').dispatchEvent(new Event('input'));update();</script></body></html>"""
    Path(out).write_text(page, encoding="utf-8")
    print("Tersimpan:", out)


# ------------------------------------------------------------ Streamlit
def run_app():
    import streamlit as st

    st.set_page_config(page_title="Dasbor ISPA Balita", page_icon="🫁", layout="wide")

    if "dashboard_data" not in st.session_state:
        st.session_state.dashboard_data = load_data()
    df = st.session_state.dashboard_data
    st.title("🫁 Dasbor Analisis ISPA Balita")
    st.caption(f"{len(df)} desa · {df.nama_kecamatan.nunique()} kecamatan · tahun {df.tahun_data.iloc[0]} · data dummy")

    with st.sidebar:
        st.header("Filter")
        uploaded = st.file_uploader("Ganti dataset (CSV)", type="csv")
        if uploaded is not None and st.button("Muat dataset pengganti"):
            try:
                st.session_state.dashboard_data = load_data(uploaded)
                st.rerun()
            except (pd.errors.ParserError, ValueError) as error:
                st.error(f"Dataset tidak valid: {error}")
        if st.button("Muat ulang dari file sumber"):
            st.session_state.dashboard_data = load_data()
            st.rerun()
        kec = st.multiselect("Kecamatan", sorted(df.nama_kecamatan.unique()), default=sorted(df.nama_kecamatan.unique()))
        kat = st.multiselect("Kategori kayu bakar", ["Rendah", "Tinggi"], default=["Rendah", "Tinggi"])
        jmin, jmax = float(df.jarak_ke_puskesmas_km.min()), float(df.jarak_ke_puskesmas_km.max())
        jr = st.slider("Jarak ke puskesmas (km)", jmin, jmax, (jmin, jmax))
        x = st.selectbox("Faktor untuk scatter plot", list(FAKTOR), format_func=FAKTOR.get)

    d = df[df.nama_kecamatan.isin(kec)]
    d = d[d.kategori_kayu_bakar.isin(kat) & d.jarak_ke_puskesmas_km.between(*jr)]
    if d.empty:
        st.warning("Tidak ada desa yang cocok dengan filter.")
    else:
        for col, (k, v) in zip(st.columns(6), kpis(d)):
            col.metric(k, v)
        with st.expander("Temuan utama (otomatis dari data terfilter)", expanded=True):
            for t in insights(d):
                st.markdown(f"- {t}")

        secs = sections(d, [x])
        tabs = st.tabs(list(secs) + ["Data"])
        for tab, rows in zip(tabs, secs.values()):
            with tab:
                for row in rows:
                    for c, f in zip(st.columns(len(row)), row):
                        c.plotly_chart(f, width="stretch")
    if d.empty:
        tabs = st.tabs(["Data"])
    with tabs[-1]:
        edited = st.data_editor(
            df, width="stretch", hide_index=True, num_rows="dynamic",
            key="data_editor",
        )
        if not edited.equals(df):
            try:
                st.session_state.dashboard_data = prepare_data(edited)
                st.rerun()
            except ValueError as error:
                st.error(f"Perubahan tidak valid: {error}")
        if st.button("Simpan perubahan ke CSV sumber", type="primary"):
            try:
                save_data(st.session_state.dashboard_data)
                st.success(f"Data tersimpan di {DATA_PATH.name}.")
            except (OSError, ValueError) as error:
                st.error(f"Data gagal disimpan: {error}")
        st.download_button("Unduh data terfilter (CSV)", d.to_csv(index=False).encode(), "data_terfilter.csv", "text/csv")
        if not d.empty:
            st.subheader("Statistik deskriptif")
            st.dataframe(d.drop(columns=["id_desa", "tahun_data", "is_dummy"]).describe().T.round(2), width="stretch")


if __name__ == "__main__":
    try:
        from streamlit.runtime import exists
        in_streamlit = exists()
    except Exception:
        in_streamlit = False
    if in_streamlit:
        run_app()
    else:
        export_html(load_data(), str(Path(__file__).with_name("dashboard_ispa.html")))
        print("Untuk versi interaktif: streamlit run dashboard_ispa.py")
