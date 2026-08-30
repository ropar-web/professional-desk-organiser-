from __future__ import annotations

import io
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from generator import OrganizerConfig, PROFESSION_PRESETS, build_models, export_models


st.set_page_config(page_title="Professional Desk Organiser Builder", page_icon="🧰", layout="wide")

st.title("Professional Desk Organiser Builder")
st.caption("Create personalised 3D-printable desk organisers for teachers, nurses and other professionals. Export STL files for the organiser, nameplate and assembled preview.")

if "profession" not in st.session_state:
    st.session_state.profession = "Teacher"

with st.sidebar:
    st.header("Personalisation")
    profession = st.selectbox("Profession preset", list(PROFESSION_PRESETS.keys()), index=list(PROFESSION_PRESETS.keys()).index(st.session_state.profession))
    preset = PROFESSION_PRESETS[profession]

    name = st.text_input("Name", "Miss Parker")
    title = st.text_input("Job title", preset["title"])
    show_title = st.toggle("Show job title", True)

    st.header("Style")
    front_styles = ["Rounded", "Pencil", "Cloud", "Arch", "Capsule", "Name Shape"]
    default_style = front_styles.index(preset["front_style"]) if preset["front_style"] in front_styles else 0
    front_style = st.selectbox("Front/nameplate shape", front_styles, index=default_style)

    icons = ["None", "Apple", "Heart", "Medical Cross", "Flower", "Paw", "Tooth", "Speech Bubble", "Scissors", "Star"]
    default_icon = icons.index(preset["icon"]) if preset["icon"] in icons else 0
    icon = st.selectbox("Profession icon", icons, index=default_icon)
    add_second_icon = st.toggle("Icon on both sides", True)
    if front_style == "Name Shape":
        name_shape_border = st.slider("Name backing border", 1.5, 6.0, 3.2, 0.2, help="Makes the backing slightly larger than the raised name, like a layered personalised sign.")
        st.caption("Name Shape makes the word itself the main front silhouette, with a connected backing for easier printing.")
    else:
        name_shape_border = 3.2

    st.header("Organiser dimensions (mm)")
    width = st.slider("Width", 140, 280, 220, 5)
    depth = st.slider("Depth", 70, 150, 100, 5)
    height = st.slider("Height", 55, 110, 78, 2)
    columns = st.slider("Compartments across", 1, 6, 4)
    rows = st.slider("Rows", 1, 3, 1)

    with st.expander("Advanced print settings"):
        wall = st.slider("Wall thickness", 2.0, 4.0, 2.6, 0.2)
        floor = st.slider("Floor thickness", 2.0, 5.0, 3.0, 0.2)
        plate_height = st.slider("Nameplate height", 38, 70, 55, 1)
        plate_thickness = st.slider("Nameplate base thickness", 1.6, 3.5, 2.2, 0.1)
        text_raise = st.slider("Raised text height", 0.6, 2.2, 1.2, 0.1)
        corner_radius = st.slider("Corner radius", 2, 12, 7, 1)
        font_name = st.selectbox("Font", ["DejaVu Sans", "Liberation Sans", "Lato"], index=0)

cfg = OrganizerConfig(
    name=name,
    title=title,
    profession=profession,
    width=float(width),
    depth=float(depth),
    height=float(height),
    wall=float(wall),
    floor=float(floor),
    columns=int(columns),
    rows=int(rows),
    front_style=front_style,
    icon=icon,
    plate_height=float(plate_height),
    plate_thickness=float(plate_thickness),
    text_raise=float(text_raise),
    corner_radius=float(corner_radius),
    font_name=font_name,
    show_title=show_title,
    add_second_icon=add_second_icon,
    name_shape_border=float(name_shape_border),
)

@st.cache_data(show_spinner=False)
def generate_cached(cfg_tuple):
    cfg = OrganizerConfig(**dict(cfg_tuple))
    models = build_models(cfg)
    preview = models["assembled_preview"].val()
    vertices, triangles = preview.tessellate(0.9)
    verts = np.array([[v.x, v.y, v.z] for v in vertices], dtype=float)
    faces = np.array(triangles, dtype=int)

    with tempfile.TemporaryDirectory() as td:
        paths = export_models(models, td)
        mem = io.BytesIO()
        with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for key, p in paths.items():
                zf.write(p, arcname=p.name)
            readme = f"""Professional Desk Organiser Builder export\n\nName: {cfg.name}\nTitle: {cfg.title}\nProfession: {cfg.profession}\nSize: {cfg.width:.0f} x {cfg.depth:.0f} x {cfg.height:.0f} mm\nCompartments: {cfg.columns} across x {cfg.rows} rows\n\nFILES\norganizer_body.stl - main organiser\nnameplate_complete.stl - flat nameplate with raised text/icons; ideal for a filament change by layer\nnameplate_base.stl - base only\nnameplate_text_icons.stl - raised text/icons only\nassembled_preview.stl - combined preview / optional one-piece print\n\nTIP FOR NO AMS\nPrint nameplate_complete.stl flat. Change filament when the base plate finishes and the raised text/icon layer begins. Then glue the finished plate to the organiser front.\n"""
            zf.writestr("PRINT_ME_FIRST.txt", readme)
        zip_bytes = mem.getvalue()
    return verts, faces, zip_bytes

cfg_tuple = tuple(cfg.__dict__.items())

try:
    with st.spinner("Building your organiser…"):
        verts, faces, zip_bytes = generate_cached(cfg_tuple)

    left, right = st.columns([1.6, 1])
    with left:
        st.subheader("3D preview")
        fig = go.Figure(data=[go.Mesh3d(
            x=verts[:,0], y=verts[:,1], z=verts[:,2],
            i=faces[:,0], j=faces[:,1], k=faces[:,2],
            opacity=1.0,
            flatshading=False,
            lighting=dict(ambient=0.55, diffuse=0.75, roughness=0.8, specular=0.15),
            lightposition=dict(x=150, y=-200, z=250),
        )])
        fig.update_layout(
            scene=dict(aspectmode="data", xaxis_visible=False, yaxis_visible=False, zaxis_visible=False),
            margin=dict(l=0, r=0, t=0, b=0),
            height=620,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

    with right:
        st.subheader("Your model")
        st.metric("Overall size", f"{width} × {depth} × {height} mm")
        st.metric("Compartments", f"{columns} × {rows}")
        st.write(f"**Front style:** {front_style}")
        if front_style == "Name Shape":
            st.write(f"**Name backing border:** {name_shape_border:.1f} mm")
        st.write(f"**Icon:** {icon}")
        st.write(f"**Name:** {name}")
        if show_title:
            st.write(f"**Title:** {title}")

        safe_name = "".join(ch if ch.isalnum() else "_" for ch in name).strip("_") or "custom"
        st.download_button(
            "Download STL pack (.zip)",
            data=zip_bytes,
            file_name=f"{safe_name}_desk_organiser_STL_pack.zip",
            mime="application/zip",
            use_container_width=True,
        )

        st.info("For easy two-colour printing without AMS, print `nameplate_complete.stl` flat and insert a filament change when the raised lettering starts. With **Name Shape**, the backing follows the name rather than using a normal rectangle/capsule plate.")

    st.divider()
    st.subheader("Built-in profession presets")
    st.write("Teacher • Registered Nurse • Early Childhood Educator • Occupational Therapist • Physiotherapist • Doctor • Dentist • Veterinarian • Speech Pathologist • Reception/Admin • Hairdresser • Beauty Therapist")

except Exception as exc:
    st.error("The model could not be generated with this combination of settings.")
    st.exception(exc)
