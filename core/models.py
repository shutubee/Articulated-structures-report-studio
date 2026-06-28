from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class Node(BaseModel):
    node_id: str
    x: float
    y: float
    z: float = 0.0


class Material(BaseModel):
    material_id: str
    name: str
    E: float
    G: Optional[float] = None
    density: Optional[float] = None
    fy: Optional[float] = None


class Section(BaseModel):
    section_id: str
    name: str
    area: float
    Ixx: float
    Iyy: Optional[float] = None
    J: Optional[float] = None


class EndRelease(BaseModel):
    axial: bool = False
    shear: bool = False
    moment: bool = False


class Member(BaseModel):
    member_id: str
    start_node: str
    end_node: str
    member_type: str = "frame"
    material_id: str = "MAT1"
    section_id: str = "SEC1"
    release_i: EndRelease = Field(default_factory=EndRelease)
    release_j: EndRelease = Field(default_factory=EndRelease)
    tension_only: bool = False
    compression_only: bool = False


class Support(BaseModel):
    support_id: str
    node_id: str
    support_type: str
    ux: str = "free"
    uy: str = "free"
    rz: str = "free"
    kx: Optional[float] = None
    ky: Optional[float] = None
    krz: Optional[float] = None
    uplift_allowed: bool = False


class Load(BaseModel):
    load_id: str
    load_type: str = "nodal_force"
    target_type: str = "node"
    target_id: str
    direction: str = "global_y"
    magnitude: float
    position: Optional[float] = None


class LoadCase(BaseModel):
    load_case_id: str
    name: str
    loads: List[Load] = Field(default_factory=list)


class Project(BaseModel):
    project_id: str = "AS-001"
    project_name: str = "Untitled Articulated Structure"
    structure_type: str = "frame"
    model_dimension: Literal["2D", "3D"] = "2D"
    unit_system: str = "kN-m"
    nodes: List[Node] = Field(default_factory=list)
    members: List[Member] = Field(default_factory=list)
    materials: List[Material] = Field(default_factory=list)
    sections: List[Section] = Field(default_factory=list)
    supports: List[Support] = Field(default_factory=list)
    load_cases: List[LoadCase] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    solved: bool = False
    warnings: List[str] = Field(default_factory=list)
    reactions: list = Field(default_factory=list)
    member_forces: list = Field(default_factory=list)
    displacements: list = Field(default_factory=list)