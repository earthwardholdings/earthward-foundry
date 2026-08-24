"""
Earthward Rescue Task Force — incident data models.

Mirrors the foundry traceability pattern:
  - every object is a dataclass with no external dependencies
  - status is always derived from event history, never stored directly
  - escalations are explicit typed objects, never silent
  - human sign-off events are enumerated and enforced upstream

The mapping from foundry concepts to rescue concepts:
  Part            -> Incident
  Part event      -> Incident action
  Acceptance      -> Incident closure (human-only)
  NCR             -> Hazard / blocker
  House agent     -> Rescue function (assessment, ops, logistics, etc.)
  Process plan    -> Operational plan
  Traceability    -> Incident log (append-only chain of custody)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class IncidentType(str, Enum):
    URBAN_SAR        = "urban_sar"          # structural collapse, confined space
    WILDERNESS_SAR   = "wilderness_sar"     # backcountry, missing persons
    DISASTER         = "disaster"           # flood, earthquake, wildfire
    MARITIME         = "maritime"           # water rescue
    HAZMAT           = "hazmat"             # chemical/biological/radiological
    MEDICAL_MASS_CAS = "medical_mass_cas"   # mass casualty incident


class IncidentPriority(str, Enum):
    LIFE_THREAT  = "life_threat"    # immediate rescue required
    URGENT       = "urgent"         # hours, not minutes
    STANDARD     = "standard"       # no immediate life threat confirmed
    MONITOR      = "monitor"        # watching, not yet active


class ActionType(str, Enum):
    # Assessment (Metrology house equivalent)
    SITUATION_REPORT   = "situation_report"
    HAZARD_IDENTIFIED  = "hazard_identified"
    VICTIM_LOCATED     = "victim_located"
    VICTIM_ASSESSED    = "victim_assessed"

    # Operational planning (Engineering house equivalent)
    OPERATIONAL_PLAN_DRAFTED   = "operational_plan_drafted"
    OPERATIONAL_PLAN_APPROVED  = "operational_plan_approved"   # human-only

    # Resource management (Materials house equivalent)
    RESOURCE_ASSIGNED  = "resource_assigned"
    RESOURCE_RELEASED  = "resource_released"
    RESOURCE_REQUESTED = "resource_requested"

    # Field operations (Forge house equivalent)
    TEAM_DEPLOYED      = "team_deployed"
    EXTRACTION_STARTED = "extraction_started"
    EXTRACTION_COMPLETE = "extraction_complete"

    # Victim handoff (Assembly house equivalent)
    VICTIM_STABILIZED  = "victim_stabilized"
    VICTIM_TRANSFERRED = "victim_transferred"   # to medical — human-only

    # Verification (Validation house equivalent)
    OBJECTIVE_VERIFIED = "objective_verified"

    # Hazard / blockers (NCR equivalent)
    HAZARD_OPENED      = "hazard_opened"
    HAZARD_MITIGATED   = "hazard_mitigated"    # human-only
    HAZARD_CLEARED     = "hazard_cleared"      # human-only

    # Incident lifecycle (Acceptance / Shipment equivalent)
    INCIDENT_OPENED    = "incident_opened"
    INCIDENT_CLOSED    = "incident_closed"     # human-only
    AFTER_ACTION_FILED = "after_action_filed"

    # Corrections (mirrors traceability pattern)
    CORRECTION         = "correction"


# Action types that carry authority-bearing weight — require human source.
HUMAN_ONLY_ACTION_TYPES: frozenset[ActionType] = frozenset({
    ActionType.OPERATIONAL_PLAN_APPROVED,
    ActionType.VICTIM_TRANSFERRED,
    ActionType.HAZARD_MITIGATED,
    ActionType.HAZARD_CLEARED,
    ActionType.INCIDENT_CLOSED,
})


class IncidentStatus(str, Enum):
    """Derived from action history — never stored directly."""
    REPORTED       = "reported"
    ASSESSING      = "assessing"
    PLANNING       = "planning"
    OPERATIONS     = "operations"
    HAZARD_BLOCKED = "hazard_blocked"
    EXTRACTING     = "extracting"
    TRANSFERRING   = "transferring"
    CLOSED         = "closed"


class PersonnelRole(str, Enum):
    INCIDENT_COMMANDER   = "incident_commander"
    OPERATIONS_SECTION   = "operations_section"
    PLANNING_SECTION     = "planning_section"
    LOGISTICS_SECTION    = "logistics_section"
    SAFETY_OFFICER       = "safety_officer"
    RESCUE_TEAM_LEADER   = "rescue_team_leader"
    RESCUE_TECHNICIAN    = "rescue_technician"
    MEDICAL_TEAM_LEADER  = "medical_team_leader"
    PARAMEDIC            = "paramedic"
    HAZMAT_SPECIALIST    = "hazmat_specialist"
    STRUCTURAL_SPECIALIST = "structural_specialist"
    LOGISTICS_COORDINATOR = "logistics_coordinator"


class ResourceType(str, Enum):
    RESCUE_TEAM      = "rescue_team"
    MEDICAL_UNIT     = "medical_unit"
    HAZMAT_UNIT      = "hazmat_unit"
    AERIAL_ASSET     = "aerial_asset"
    WATER_RESCUE     = "water_rescue"
    HEAVY_EQUIPMENT  = "heavy_equipment"
    CANINE_TEAM      = "canine_team"
    COMMAND_POST     = "command_post"
    SUPPLY_CACHE     = "supply_cache"


# ---------------------------------------------------------------------------
# Source — who submitted this action (agent or named human)
# ---------------------------------------------------------------------------

@dataclass
class ActionSource:
    """
    Mirrors traceability.Source exactly.
    type: 'agent' | 'human'
    id:   agent name (e.g. 'assessment-agent') or human ID (callsign, badge)
    """
    type: str
    id: str

    def __post_init__(self):
        if self.type not in ("agent", "human"):
            raise ValueError(
                f"source.type must be 'agent' or 'human', got {self.type!r}"
            )

    def is_human(self) -> bool:
        return self.type == "human"


# ---------------------------------------------------------------------------
# Personnel and resources
# ---------------------------------------------------------------------------

@dataclass
class Personnel:
    person_id: str
    callsign: str
    role: PersonnelRole
    certifications: list[str] = field(default_factory=list)
    available: bool = True
    assigned_incident_id: Optional[str] = None


@dataclass
class Resource:
    resource_id: str
    name: str
    resource_type: ResourceType
    capacity: int = 1           # e.g. seats in a helicopter, team size
    available: bool = True
    assigned_incident_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Hazard — the NCR equivalent
# ---------------------------------------------------------------------------

@dataclass
class Hazard:
    hazard_id: str
    description: str
    severity: str               # "critical" | "high" | "moderate" | "low"
    opened_at: str
    opened_by: ActionSource
    mitigated_at: Optional[str] = None
    cleared_at: Optional[str] = None
    cleared_by: Optional[ActionSource] = None
    notes: str = ""

    @property
    def is_open(self) -> bool:
        return self.cleared_at is None


# ---------------------------------------------------------------------------
# Victim record
# ---------------------------------------------------------------------------

@dataclass
class Victim:
    victim_id: str
    description: str            # "adult male, approximate 40s" — no PII in scaffold
    location_description: str
    triage_category: str        # "immediate" | "delayed" | "minimal" | "expectant"
    located_at: Optional[str] = None
    extracted_at: Optional[str] = None
    transferred_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Incident action — the append-only event log entry
# ---------------------------------------------------------------------------

@dataclass
class IncidentAction:
    action_id: str
    incident_id: str
    timestamp: str
    action_type: ActionType
    source: ActionSource
    reference: str              # report ID, radio log entry, order number — never free text alone
    corrects_action_id: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Escalation — explicit, named, never "notify a human"
# ---------------------------------------------------------------------------

@dataclass
class Escalation:
    escalation_id: str
    incident_id: str
    timestamp: str
    raised_by: str              # agent name
    escalate_to: str            # named human role or callsign
    reason: str
    action_required: str
    resolved: bool = False
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None


# ---------------------------------------------------------------------------
# Operational plan — the process plan equivalent
# ---------------------------------------------------------------------------

@dataclass
class OperationalPlan:
    plan_id: str
    incident_id: str
    drafted_by: str             # agent name
    objectives: list[str] = field(default_factory=list)
    team_assignments: dict[str, str] = field(default_factory=dict)  # team_id -> objective
    resource_assignments: dict[str, str] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)   # always explicit, never silent
    open_questions: list[str] = field(default_factory=list)
    status: str = "draft"       # "draft" | "approved" — approved only by human
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Incident — the top-level record (the "part" equivalent)
# ---------------------------------------------------------------------------

@dataclass
class Incident:
    incident_id: str
    incident_type: IncidentType
    priority: IncidentPriority
    location: str
    reported_at: str
    reported_by: ActionSource
    description: str
    actions: list[IncidentAction] = field(default_factory=list)
    victims: list[Victim] = field(default_factory=list)
    hazards: list[Hazard] = field(default_factory=list)
    escalations: list[Escalation] = field(default_factory=list)
    operational_plans: list[OperationalPlan] = field(default_factory=list)
    assigned_personnel: list[str] = field(default_factory=list)   # person_ids
    assigned_resources: list[str] = field(default_factory=list)   # resource_ids

    @property
    def current_status(self) -> IncidentStatus:
        """
        Derived from action history — never stored directly.
        Mirrors traceability._derive_status() exactly.
        """
        if not self.actions:
            return IncidentStatus.REPORTED

        types_seen = [a.action_type for a in self.actions]
        open_hazards = sum(
            1 for h in self.hazards if h.is_open and h.severity in ("critical", "high")
        )

        if ActionType.INCIDENT_CLOSED in types_seen:
            return IncidentStatus.CLOSED

        if ActionType.VICTIM_TRANSFERRED in types_seen:
            return IncidentStatus.TRANSFERRING

        if ActionType.EXTRACTION_STARTED in types_seen:
            return IncidentStatus.EXTRACTING

        if open_hazards > 0:
            return IncidentStatus.HAZARD_BLOCKED

        if ActionType.TEAM_DEPLOYED in types_seen:
            return IncidentStatus.OPERATIONS

        if ActionType.OPERATIONAL_PLAN_APPROVED in types_seen:
            return IncidentStatus.PLANNING

        if ActionType.SITUATION_REPORT in types_seen:
            return IncidentStatus.ASSESSING

        return IncidentStatus.REPORTED

    @property
    def open_hazards(self) -> list[Hazard]:
        return [h for h in self.hazards if h.is_open]

    @property
    def open_escalations(self) -> list[Escalation]:
        return [e for e in self.escalations if not e.resolved]

    @property
    def unextracted_victims(self) -> list[Victim]:
        return [v for v in self.victims if v.extracted_at is None]


# ---------------------------------------------------------------------------
# Errors — every rejection is explicit, nothing is silent
# ---------------------------------------------------------------------------

class RescueError(Exception):
    """Base class for all rescue layer rejections."""


class UnknownIncidentError(RescueError):
    pass


class InvalidSequenceError(RescueError):
    pass


class UnauthorizedSourceError(RescueError):
    """Agent attempted a human-only action type."""


class HazardBlockError(RescueError):
    """Operation blocked by an open critical/high hazard."""


class MissingReferenceError(RescueError):
    pass


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
