## `app.py`
import json
import pandas as pd
import streamlit as st

from core.models import Node, Member, Material, Section, Support, Load, LoadCase
from core.project_io import new_project, dump_model
from visualizer.geometry_plot import plot_geometry
from solver.validation import validate_project
from solver.frame_solver import solve_2d_frame
from reports.report_builder import build_html_report
from glossary.glossary_lookup import search_glossary

st.set_page_config(page_title="Articulated Structures Studio", layout="wide")
st.title("Articulated Structures Studio")
st.caption("Educational / preliminary articulated-structures modelling prototype")

if "project" not in st.session_state:
    st.session_state.project = new_project()

project = st.session_state.project

page = st.sidebar.radio(
    "Navigation",
    [
        "Project", "Geometry", "Materials and Sections", "Supports", "Releases",
        "Loads", "Check Model", "Results", "Glossary", "Report"
    ],
)

def dataframe_from_models(items):
    return pd.DataFrame([dump_model(item) for item in items]) if items else pd.DataFrame()

if page == "Project":
    st.header("Project Setup")
    project.project_name = st.text_input("Project name", value=project.project_name)
    project.structure_type = st.selectbox(
        "Structure type",
        ["beam", "truss", "frame", "arch", "bearing system", "deployable system"],
        index=2,
    )
    project.unit_system = st.selectbox("Unit system", ["kN-m", "N-mm", "SI"], index=0)
    st.info("MVP target: 2D frame/truss/beam workflow with support, release, load, result, and warning panels.")
    st.download_button(
        "Download project JSON",
        json.dumps(dump_model(project), indent=2),
        "project.json",
        "application/json",
    )

elif page == "Geometry":
    st.header("Geometry Builder")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Nodes")
        node_df = dataframe_from_models(project.nodes)
        edited_nodes = st.data_editor(node_df, num_rows="dynamic", key="nodes_editor")
        if st.button("Update nodes"):
            project.nodes = [Node(**row.dropna().to_dict()) for _, row in edited_nodes.iterrows()]
            st.success("Nodes updated.")

    with col2:
        st.subheader("Members")
        member_rows = []
        for m in project.members:
            d = dump_model(m)
            d["release_i_moment"] = m.release_i.moment
            d["release_j_moment"] = m.release_j.moment
            d.pop("release_i", None)
            d.pop("release_j", None)
            member_rows.append(d)

        member_df = pd.DataFrame(member_rows)
        edited_members = st.data_editor(member_df, num_rows="dynamic", key="members_editor")

        if st.button("Update members"):
            new_members = []
            for _, row in edited_members.iterrows():
                data = row.dropna().to_dict()
                release_i_moment = bool(data.pop("release_i_moment", False))
                release_j_moment = bool(data.pop("release_j_moment", False))
                m = Member(**data)
                m.release_i.moment = release_i_moment
                m.release_j.moment = release_j_moment
                new_members.append(m)
            project.members = new_members
            st.success("Members updated.")

    st.subheader("Preview")
    st.pyplot(plot_geometry(project))

elif page == "Materials and Sections":
    st.header("Materials and Sections")
    col1, col2 = st.columns(2)

    with col1:
        mat_df = dataframe_from_models(project.materials)
        edited = st.data_editor(mat_df, num_rows="dynamic", key="materials_editor")
        if st.button("Update materials"):
            project.materials = [Material(**row.dropna().to_dict()) for _, row in edited.iterrows()]
            st.success("Materials updated.")

    with col2:
        sec_df = dataframe_from_models(project.sections)
        edited = st.data_editor(sec_df, num_rows="dynamic", key="sections_editor")
        if st.button("Update sections"):
            project.sections = [Section(**row.dropna().to_dict()) for _, row in edited.iterrows()]
            st.success("Sections updated.")

elif page == "Supports":
    st.header("Support Editor")
    support_df = dataframe_from_models(project.supports)
    edited = st.data_editor(support_df, num_rows="dynamic", key="supports_editor")
    if st.button("Update supports"):
        project.supports = [Support(**row.dropna().to_dict()) for _, row in edited.iterrows()]
        st.success("Supports updated.")
    st.caption("Use ux/uy/rz values as fixed or free. Spring states are reserved for expansion.")

elif page == "Releases":
    st.header("Release Editor")
    rows = []
    for m in project.members:
        rows.append({
            "member_id": m.member_id,
            "release_i_moment": m.release_i.moment,
            "release_j_moment": m.release_j.moment,
        })

    edited = st.data_editor(pd.DataFrame(rows), num_rows="fixed")

    if st.button("Update releases"):
        lookup = {m.member_id: m for m in project.members}
        for _, row in edited.iterrows():
            m = lookup.get(row["member_id"])
            if m:
                m.release_i.moment = bool(row["release_i_moment"])
                m.release_j.moment = bool(row["release_j_moment"])
        st.success("Releases updated.")

elif page == "Loads":
    st.header("Load Editor")

    if not project.load_cases:
        project.load_cases.append(LoadCase(load_case_id="LC1", name="Default Load Case"))

    load_case = project.load_cases[0]
    load_df = dataframe_from_models(load_case.loads)

    if load_df.empty:
        load_df = pd.DataFrame([
            {
                "load_id": "L1",
                "load_type": "nodal_force",
                "target_type": "node",
                "target_id": "N2",
                "direction": "global_y",
                "magnitude": -10.0,
                "position": None,
            }
        ])

    edited = st.data_editor(load_df, num_rows="dynamic", key="loads_editor")

    if st.button("Update loads"):
        load_case.loads = [Load(**row.dropna().to_dict()) for _, row in edited.iterrows()]
        st.success("Loads updated.")

elif page == "Check Model":
    st.header("Model Checks")
    warnings = validate_project(project)

    if warnings:
        for warning in warnings:
            st.warning(warning)
    else:
        st.success("No critical pre-solve warnings detected.")

elif page == "Results":
    st.header("Results")

    if st.button("Run Solver"):
        st.session_state.result = solve_2d_frame(project)

    result = st.session_state.get("result")

    if result:
        if result.solved:
            st.success("Analysis completed.")
            st.subheader("Reactions")
            st.dataframe(pd.DataFrame(result.reactions))

            st.subheader("Displacements")
            st.dataframe(pd.DataFrame(result.displacements))

            st.subheader("Member End Forces")
            st.dataframe(pd.DataFrame(result.member_forces))

            if result.warnings:
                st.subheader("Warnings")
                for w in result.warnings:
                    st.warning(w)

            st.subheader("Deformed Preview")
            st.pyplot(plot_geometry(project, result=result, deformation_scale=200))
        else:
            st.error("Analysis could not be completed.")
            for warning in result.warnings:
                st.warning(warning)

elif page == "Glossary":
    st.header("Glossary")
    q = st.text_input("Search", value="hinge")
    cards = search_glossary(q)

    for card in cards:
        with st.expander(card["term"], expanded=True):
            st.write(card["definition"])
            st.caption(card["app_relevance"])

elif page == "Report":
    st.header("Report Builder")
    result = st.session_state.get("result")
    html = build_html_report(project, result)

    st.download_button(
        "Download HTML report",
        html,
        "articulated_structure_report.html",
        "text/html",
    )

    st.download_button(
        "Download project JSON",
        json.dumps(dump_model(project), indent=2),
        "articulated_structure_project.json",
        "application/json",
    )