from rdkit.Chem import Draw
from rdkit.Chem.Draw import rdMolDraw2D
from xml.sax.saxutils import escape
import base64

def svg_to_text(svg):
    if isinstance(svg, str):
        return svg
    if hasattr(svg, "data"):
        return svg.data
    return str(svg)


def draw_mol_sequence(
    mols,
    mol_legends=None,
    arrow_tops=None,
    arrow_bottoms=None,
    svg_file="scheme.svg",
    subImgSize=(250, 200),
    atom_font_size=18,
    mol_font_size=20,
    arrow_font_size=16,
    font_family="sans-serif",
):
    n = len(mols)

    if n == 0:
        raise ValueError("mols が空です。")

    mol_legends = mol_legends or [""] * n
    arrow_tops = arrow_tops or [""] * (n - 1)
    arrow_bottoms = arrow_bottoms or [""] * (n - 1)

    if len(mol_legends) != n:
        raise ValueError("mol_legends の長さは len(mols) と一致させてください。")
    if len(arrow_tops) != n - 1:
        raise ValueError("arrow_tops の長さは len(mols)-1 にしてください。")
    if len(arrow_bottoms) != n - 1:
        raise ValueError("arrow_bottoms の長さは len(mols)-1 にしてください。")

    mol_w, mol_h = subImgSize
    arrow_w = 180
    margin = 20

    top_space = arrow_font_size + 25
    bottom_space = mol_font_size + 25

    height = top_space + mol_h + bottom_space + 20
    total_width = 2 * margin + n * mol_w + (n - 1) * arrow_w

    y_img = top_space
    y_arrow = y_img + mol_h / 2
    y_legend = y_img + mol_h + mol_font_size + 5

    # 各分子をSVGとして取得
    mol_svgs = []

    for mol in mols:
        opts = rdMolDraw2D.MolDrawOptions()
        opts.fixedFontSize = atom_font_size

        svg = Draw.MolsToGridImage(
            [mol],
            legends=[""],
            molsPerRow=1,
            subImgSize=subImgSize,
            useSVG=True,
            drawOptions=opts,
        )

        svg = svg_to_text(svg)

        encoded = base64.b64encode(
            svg.encode("utf-8")
        ).decode("utf-8")

        mol_svgs.append(encoded)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{total_width}" height="{height}" '
        f'viewBox="0 0 {total_width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>'
    ]

    x = margin

    for i in range(n):

        # 分子
        parts.append(
            f'<image x="{x}" y="{y_img}" '
            f'width="{mol_w}" height="{mol_h}" '
            f'href="data:image/svg+xml;base64,{mol_svgs[i]}"/>'
        )

        # 分子の凡例
        if mol_legends[i]:
            parts.append(
                f'<text '
                f'x="{x + mol_w / 2}" '
                f'y="{y_legend}" '
                f'text-anchor="middle" '
                f'font-size="{mol_font_size}" '
                f'font-family="{font_family}">'
                f'{escape(mol_legends[i])}'
                f'</text>'
            )

        x += mol_w

        # 矢印
        if i < n - 1:
            x1 = x + 15
            x2 = x + arrow_w - 15
            xm = (x1 + x2) / 2

            parts.append(
                f'<line '
                f'x1="{x1}" y1="{y_arrow}" '
                f'x2="{x2}" y2="{y_arrow}" '
                f'stroke="black" stroke-width="2.5"/>'
            )

            parts.append(
                f'<polygon '
                f'points="{x2},{y_arrow} '
                f'{x2-14},{y_arrow-7} '
                f'{x2-14},{y_arrow+7}" '
                f'fill="black"/>'
            )

            # 矢印上
            if arrow_tops[i]:
                parts.append(
                    f'<text '
                    f'x="{xm}" '
                    f'y="{y_arrow - 18}" '
                    f'text-anchor="middle" '
                    f'font-size="{arrow_font_size}" '
                    f'font-family="{font_family}">'
                    f'{escape(arrow_tops[i])}'
                    f'</text>'
                )

            # 矢印下
            if arrow_bottoms[i]:
                parts.append(
                    f'<text '
                    f'x="{xm}" '
                    f'y="{y_arrow + arrow_font_size + 6}" '
                    f'text-anchor="middle" '
                    f'font-size="{arrow_font_size}" '
                    f'font-family="{font_family}">'
                    f'{escape(arrow_bottoms[i])}'
                    f'</text>'
                )

            x += arrow_w

    parts.append("</svg>")

    svg_text = "\n".join(parts)

    with open(svg_file, "w", encoding="utf-8") as f:
        f.write(svg_text)

from rdkit import Chem

mols = [
    Chem.MolFromSmiles("CC(=O)O"),
    Chem.MolFromSmiles("CC(=O)Cl"),
    Chem.MolFromSmiles("CC(=O)NCC"),
]

draw_mol_sequence(
    mols,
    mol_legends=["カルボン酸", "酸塩化物", "アミド"],
    arrow_tops=["SOCl2", "EtNH2"],
    arrow_bottoms=["reflux", "CH2Cl2, rt"],
    svg_file="test.svg",
    mol_font_size=20,
    atom_font_size=40,
    arrow_font_size=20,
)