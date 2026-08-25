"""Strict typed authoring model for the `fisl/v1` POC subset (schema §2–§17).

Scope note (GitHub Issue #2): demand/service, objectives, external scheduled
supply buffers beyond the spike's needs, and most metric types are deferred.
Unknown fields are rejected (`extra="forbid"`) so typos cannot silently become
experiment changes (schema §2). Fields belonging to deferred v1 features fail
validation with a clear message rather than being half-implemented.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScenarioMeta(_Strict):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9\-]*$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    title: str
    description: str | None = None


class FactorioVersion(_Strict):
    minimum: str
    maximum_exclusive: str | None = None


class FactorioSection(_Strict):
    version: FactorioVersion
    baseline_save: str
    required_mods: dict[str, str] = Field(default_factory=dict)


class GameSpeed(_Strict):
    policy: Literal["fixed"] = "fixed"
    value: float = 1.0


class TimePolicy(_Strict):
    game_speed: GameSpeed = Field(default_factory=GameSpeed)
    # ADR 0018 §1: the canonical interactive POC profile supports only
    # `prohibited`; `allowed` is reserved for a future controlled pause/resume
    # ADR and is rejected here rather than silently accepted.
    pause_policy: Literal["prohibited"] = "prohibited"


class Phase(_Strict):
    id: str = Field(pattern=r"^[a-z0-9_][a-z0-9_\-]*$")
    duration: str | int


class ExperimentSection(_Strict):
    seed: int = 1
    time: TimePolicy = Field(default_factory=TimePolicy)
    phases: list[Phase] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_phase_ids(self) -> "ExperimentSection":
        ids = [p.id for p in self.phases]
        if len(ids) != len(set(ids)):
            raise ValueError(f"phase ids must be unique, got {ids}")
        return self


class ZoneArea(_Strict):
    left_top: tuple[int, int]
    right_bottom: tuple[int, int]

    @model_validator(mode="after")
    def _nonempty(self) -> "ZoneArea":
        if not (self.left_top[0] < self.right_bottom[0] and self.left_top[1] < self.right_bottom[1]):
            raise ValueError(f"zone area is empty or inverted: {self.left_top} .. {self.right_bottom}")
        return self


class Zone(_Strict):
    surface: str
    area: ZoneArea


class System(_Strict):
    primary_zone: str
    boundary_integrity: dict[str, str] = Field(default_factory=lambda: {"entity_containment": "flag"})


class EntitySet(_Strict):
    zone: str
    types: list[str] = Field(default_factory=list)
    prototypes: list[str] = Field(default_factory=list)
    include_roles: list[str] = Field(default_factory=list)
    exclude_roles: list[str] = Field(default_factory=lambda: ["fisl_apparatus"])
    membership: Literal["dynamic"] = "dynamic"

    @model_validator(mode="after")
    def _positive_scope(self) -> "EntitySet":
        if not self.types and not self.prototypes:
            raise ValueError("entity_set needs at least one positive selector (types or prototypes)")
        return self


class PortBinding(_Strict):
    surface: str
    position: tuple[float, float]
    prototype: str


class PortMaterial(_Strict):
    item: str
    quality: str = "normal"


class ReplenishSupply(_Strict):
    mode: Literal["replenish"]
    target: int = Field(gt=0)
    active_phases: list[str] | None = None


class ConstantSchedule(_Strict):
    type: Literal["constant"]
    rate: str


class ExternalBuffer(_Strict):
    capacity: int | Literal["unbounded"] = "unbounded"


class ScheduledSupply(_Strict):
    mode: Literal["scheduled"]
    schedule: ConstantSchedule
    initial_quantity: int = Field(default=0, ge=0)
    active_phases: list[str] | None = None
    external_buffer: ExternalBuffer = Field(default_factory=ExternalBuffer)


class Port(_Strict):
    system: str
    direction: Literal["source", "sink"]
    binding: PortBinding
    material: PortMaterial
    supply: ReplenishSupply | ScheduledSupply | None = None

    @model_validator(mode="after")
    def _direction_rules(self) -> "Port":
        if self.direction == "source" and self.supply is None:
            raise ValueError("source port requires a supply declaration")
        if self.direction == "sink" and self.supply is not None:
            raise ValueError("sink port cannot declare supply")
        return self


class FlowBasis(_Strict):
    type: Literal["conserved_work_unit"]
    materials: dict[str, int]

    @field_validator("materials")
    @classmethod
    def _positive_coefficients(cls, value: dict[str, int]) -> dict[str, int]:
        if not value:
            raise ValueError("conserved_work_unit basis requires at least one material mapping")
        for item, coefficient in value.items():
            if coefficient <= 0:
                raise ValueError(f"work-unit coefficient for {item!r} must be positive")
        return value


class Flow(_Strict):
    system: str
    unit: str
    basis: FlowBasis
    entry_ports: list[str] = Field(min_length=1)
    completion_ports: list[str] = Field(min_length=1)
    loss_ports: list[str] = Field(default_factory=list)


class PhysicalCensus(_Strict):
    required: bool = True
    every: str | int = "60t"
    discrepancy_tolerance: int = 0
    include_player_inventory: bool = True


class WipValidation(_Strict):
    physical_census: PhysicalCensus = Field(default_factory=PhysicalCensus)


class WipMetric(_Strict):
    type: Literal["wip"]
    flow: str
    method: Literal["conservation_ledger"] = "conservation_ledger"
    validation: WipValidation = Field(default_factory=WipValidation)


class CurrentValueMetric(_Strict):
    type: Literal["current_value"]
    source: str


class PhaseWindow(_Strict):
    phase: str


class AggregateMetric(_Strict):
    type: Literal["aggregate"]
    source: str
    aggregation: Literal["time_mean", "time_integral", "min", "max"]
    window: PhaseWindow


class ThroughputMetric(_Strict):
    type: Literal["throughput"]
    flow: str
    window: PhaseWindow
    display_unit: str | None = None


class CycleTimeMetric(_Strict):
    type: Literal["cycle_time"]
    flow: str
    method: Literal["little_law_derived"]
    wip_metric: str
    throughput_metric: str
    interpretation: dict[str, str] = Field(default_factory=dict)


Metric = WipMetric | CurrentValueMetric | AggregateMetric | ThroughputMetric | CycleTimeMetric


class VisibilityAudience(_Strict):
    metrics: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)


class Visibility(_Strict):
    learner_live: VisibilityAudience = Field(default_factory=VisibilityAudience)
    learner_post_run: VisibilityAudience = Field(default_factory=VisibilityAudience)
    instructor: VisibilityAudience = Field(default_factory=VisibilityAudience)


class AuthorScenario(_Strict):
    spec: Literal["fisl/v1"]
    scenario: ScenarioMeta
    factorio: FactorioSection
    experiment: ExperimentSection
    zones: dict[str, Zone]
    systems: dict[str, System]
    entity_sets: dict[str, EntitySet] = Field(default_factory=dict)
    ports: dict[str, Port] = Field(default_factory=dict)
    flows: dict[str, Flow] = Field(default_factory=dict)
    metrics: dict[str, Metric] = Field(default_factory=dict)
    visibility: Visibility = Field(default_factory=Visibility)
    # Explanatory course metadata; excluded from resolved scenario identity
    # (schema §17). Free-form on purpose.
    learning: dict = Field(default_factory=dict)
