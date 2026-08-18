"""
RDKit Reaction SMILES を、矢印・凡例(日本語可)付きの 300dpi SVG として出力するスクリプト。

- 各分子は RDKit の MolDraw2DSVG で構造式のみ描画(文字ラベルはRDKit組み込みフォントの
  アウトライン化なので日本語は使えない。そのため凡例・矢印テキストはRDKitに任せず、
  自前の <text> 要素として重ねる)
- 凡例・矢印上下のテキストは生の SVG <text> 要素として埋め込むため、
  表示側(ブラウザ/Illustrator等)が持つ日本語フォントでそのまま描画される
- 出力SVGの <svg> ルート要素に width/height を物理単位(mm)、viewBoxをpx単位で指定し、
  px/mm の比率から 300dpi 相当になるよう計算している
"""

import re
from xml.sax.saxutils import escape

from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

# ---- 300dpi 関連の定数 -------------------------------------------------
DPI = 300
MM_PER_INCH = 25.4


def px_to_mm(px, dpi=DPI):
    return px / dpi * MM_PER_INCH


# ---- 個々の分子を SVG 断片として取得 -----------------------------------
def mol_svg_fragment(mol, size_px):
    """RDKitで分子を描画し、(内部SVG要素の文字列, width, height) を返す。
    凡例(legend)はここでは付けない。"""
    w, h = size_px
    d = rdMolDraw2D.MolDraw2DSVG(w, h)
    opts = d.drawOptions()
    opts.clearBackground = False  # 背景は上位のcanvas側で白塗りする
    mol = Chem.Mol(mol)
    for atom in mol.GetAtoms():
        atom.SetAtomMapNum(0)
    rdMolDraw2D.PrepareAndDrawMolecule(d, mol)
    d.FinishDrawing()
    svg = d.GetDrawingText()

    # <svg ...> ... </svg> の中身(<?xml...?>宣言やコメントを除く)だけ取り出す
    body = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    # RDKitが出力するrect(背景)要素があれば消す
    body = re.sub(r"<rect[^>]*/>", "", body, count=1)
    return body, w, h


# ---- SVGパーツ生成ヘルパー ----------------------------------------------
JP_FONT_STACK = "'Noto Sans CJK JP','Yu Gothic','Hiragino Sans','Meiryo',sans-serif"


def svg_text(x, y, text, font_size=16, anchor="middle", font_family=JP_FONT_STACK):
    return (
        f'<text x="{x}" y="{y}" font-size="{font_size}" '
        f'font-family="{font_family}" text-anchor="{anchor}" fill="black">'
        f"{escape(text)}</text>"
    )


def plus_svg(x_offset, height, width=40, font_size=26):
    y = height / 2 + font_size * 0.35
    x = x_offset + width / 2
    return svg_text(x, y, "+", font_size=font_size)


def arrow_svg(x_offset, height, width=200, top_text="", bottom_text="", font_size=15):
    mid_y = height / 2
    x0, x1 = x_offset + 10, x_offset + width - 10
    parts = [
        f'<line x1="{x0}" y1="{mid_y}" x2="{x1}" y2="{mid_y}" '
        f'stroke="black" stroke-width="2"/>',
        f'<polygon points="{x1},{mid_y} {x1-12},{mid_y-6} {x1-12},{mid_y+6}" '
        f'fill="black"/>',
    ]
    cx = x_offset + width / 2
    if top_text:
        parts.append(svg_text(cx, mid_y - 10, top_text, font_size=font_size))
    if bottom_text:
        parts.append(svg_text(cx, mid_y + 10 + font_size, bottom_text, font_size=font_size))
    return "\n".join(parts)


def mol_tile_svg(x_offset, mol, legend, size_px, legend_h=34, font_size=16):
    """分子1個ぶんのSVG(構造式 + 下部に自前描画の凡例)を返す"""
    w, h = size_px
    mol_h = h - legend_h
    body, _, _ = mol_svg_fragment(mol, (w, mol_h))
    parts = [f'<g transform="translate({x_offset},0)">', body]
    if legend:
        parts.append(svg_text(w / 2, mol_h + legend_h * 0.7, legend, font_size=font_size))
    parts.append("</g>")
    return "\n".join(parts)


# ---- メイン: 反応式全体を組み立てる --------------------------------------
def draw_reaction_svg_300dpi(
    rxn,
    reactant_legends=None,
    product_legends=None,
    arrow_top="",
    arrow_bottom="",
    sub_img_size_px=(660, 660),   # 1分子タイルのピクセルサイズ(300dpiだと約2.2インチ角)
    arrow_width_px=260,
    plus_width_px=50,
    legend_h_px=40,
    font_size_px=18,
):
    n_r = rxn.GetNumReactantTemplates()
    n_p = rxn.GetNumProductTemplates()
    reactant_legends = reactant_legends or [""] * n_r
    product_legends = product_legends or [""] * n_p

    height = sub_img_size_px[1]
    x = 0
    fragments = []

    for i in range(n_r):
        if i > 0:
            fragments.append(plus_svg(x, height, plus_width_px))
            x += plus_width_px
        fragments.append(
            mol_tile_svg(
                x, rxn.GetReactantTemplate(i), reactant_legends[i],
                sub_img_size_px, legend_h_px, font_size_px,
            )
        )
        x += sub_img_size_px[0]

    fragments.append(arrow_svg(x, height, arrow_width_px, arrow_top, arrow_bottom, font_size_px))
    x += arrow_width_px

    for j in range(n_p):
        if j > 0:
            fragments.append(plus_svg(x, height, plus_width_px))
            x += plus_width_px
        fragments.append(
            mol_tile_svg(
                x, rxn.GetProductTemplate(j), product_legends[j],
                sub_img_size_px, legend_h_px, font_size_px,
            )
        )
        x += sub_img_size_px[0]

    total_w_px = x
    total_h_px = height

    width_mm = px_to_mm(total_w_px)
    height_mm = px_to_mm(total_h_px)

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width_mm:.2f}mm" height="{height_mm:.2f}mm"
     viewBox="0 0 {total_w_px} {total_h_px}">
<rect x="0" y="0" width="{total_w_px}" height="{total_h_px}" fill="white"/>
{chr(10).join(fragments)}
</svg>
"""
    return svg


if __name__ == "__main__":
    rxn = AllChem.ReactionFromSmarts("CC(=O)O.NCC>>CC(=O)NCC", useSmiles=True)

    svg = draw_reaction_svg_300dpi(
        rxn,
        reactant_legends=["カルボン酸", "アミン"],
        product_legends=["アミド"],
        arrow_top="EDC, HOBt",
        arrow_bottom="DMF, rt, 12 h",
    )

    out_path = "/home/claude/rxn_test/reaction_300dpi_v2.svg"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("saved:", out_path)
