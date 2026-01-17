from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, HttpUrl, PositiveInt

from src.aliases.affect import AFFECT_TOKEN_ALIASES
from src.aliases.generic import NONE_MAP
from src.models.attribute_models.affects import (
    AffectsExtractOptionsStage,
    AffectsModel,
    AffectsOrchestrator,
)
from src.models.attribute_models.angle import (
    AngleExtractOptionsStage,
    AngleOrchestrator,
    AngleParseDegreesStage,
    AngleStrToFloatCorrection,
)
from src.models.attribute_models.angle import (
    TrimCorrection as AngleTrimCorrection,
)
from src.models.attribute_models.attribute_models_abstracts import (
    AliasCorrection as GenericAliasCorrection,
)
from src.models.attribute_models.attribute_models_abstracts import (
    TrimCorrection as GenericTrimCorrection,
)
from src.models.attribute_models.cast_time import (
    CastTimeCoreAndContextStage,
    CastTimeExtractOptionsStage,
    CastTimeModel,
    CastTimeOrchestrator,
    CastTimeParseContextStage,
    CastTimeParseCoreStage,
)
from src.models.attribute_models.collision_radius import (
    CollisionRadiusExtractOptionsStage,
    CollisionRadiusOrchestrator,
    CollisionRadiusStrToFloatCorrection,
    CollisionRadiusTrimCorrection,
)
from src.models.attribute_models.inner_radius import (
    InnerRadiusExtractOptionsStage,
    InnerRadiusModel,
    InnerRadiusOrchestrator,
    InnerRadiusTransformValuesStage,
)
from src.models.attribute_models.cast_time import (
    NoneTypeCorrection as CastTimeNoneTypeCorrection,
)
from src.models.attribute_models.cast_time import (
    NormaliseWhitespaceCorrection as CastTimeNormaliseWhitespaceCorrection,
)
from src.models.attribute_models.cast_time import (
    TrimCorrection as CastTimeTrimCorrection,
)
from src.models.attribute_models.modifiers import (
    EmptyUnitCorrection,
    ModifierCollectAttributesStage,
    ModifierExtractBracketStatsStage,
    ModifierNormalizeUnitsStage,
    ModifiersModel,
    ModifiersOrchestrator,
    ModifierSplitBaseEnhancementsStage,
    TrimUnitCorrection,
)

NonNegativeFloat = Annotated[float, Field(ge=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]

Role = Literal[
    "TANK",
    "FIGHTER",
    "ASSASSIN",
    "VANGUARD",
    "SUPPORT",
    "DIVER",
    "CATCHER",
    "SKIRMISHER",
    "SPECIALIST",
    "ENCHANTER",
    "MAGE",
    "JUGGERNAUT",
    "WARDEN",
    "ARTILLERY",
    "MARKSMAN",
    "BURST",
    "BATTLEMAGE",
]
Resource = Literal[
    "MANA_PER_SECOND",
    "FLOW",
    "FURY",
    "GRIT",
    "CHARGE",
    "HEALTH",
    "CURRENT_HEALTH",
    "CRIMSON_RUSH",
    "ENERGY",
    "OTHER",
    "NONE",
    "COURAGE",
    "SHIELD",
    "FRENZY",
    "BLOOD_WELL",
    "FEROCITY",
    "RAGE",
    "MANA",
    "MAXIMUM_HEALTH",
    "HEAT",
]
AttackType = Literal["MELEE", "RANGED"]
AdaptiveType = Literal["MAGIC_DAMAGE", "PHYSICAL_DAMAGE"]
DamageType = Literal[
    "TRUE_DAMAGE",
    "MAGIC_DAMAGE",
    "PHYSICAL_DAMAGE",
    "MIXED_DAMAGE",
    "OTHER_DAMAGE",
]
Projectile = Literal["FALSE", "UNKNOWN", "TRUE", "SPECIAL"]


class Position(str, Enum):
    TOP = "TOP"
    JUNGLE = "JUNGLE"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"
    SUPPORT = "SUPPORT"


class AttributeMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    flat: float
    percent: float
    perLevel: NonNegativeFloat
    percentPerLevel: float


class Stats(BaseModel):
    model_config = ConfigDict(extra="forbid")
    health: AttributeMetric
    healthRegen: AttributeMetric
    mana: AttributeMetric
    manaRegen: AttributeMetric
    armor: AttributeMetric
    magicResistance: AttributeMetric
    attackDamage: AttributeMetric
    movespeed: AttributeMetric
    acquisitionRadius: AttributeMetric
    selectionRadius: AttributeMetric
    pathingRadius: AttributeMetric
    gameplayRadius: AttributeMetric
    criticalStrikeDamage: AttributeMetric
    criticalStrikeDamageModifier: AttributeMetric
    attackSpeed: AttributeMetric
    attackSpeedRatio: AttributeMetric
    attackCastTime: AttributeMetric
    attackTotalTime: AttributeMetric
    attackDelayOffset: AttributeMetric
    attackRange: AttributeMetric
    aramDamageTaken: AttributeMetric
    aramDamageDealt: AttributeMetric
    aramHealing: AttributeMetric
    aramShielding: AttributeMetric
    aramTenacity: AttributeMetric
    aramAbilityHaste: AttributeMetric
    aramAttackSpeed: AttributeMetric
    aramEnergyRegen: AttributeMetric
    urfDamageTaken: AttributeMetric
    urfDamageDealt: AttributeMetric
    urfHealing: AttributeMetric
    urfShielding: AttributeMetric


class AttributeRating(BaseModel):
    model_config = ConfigDict(extra="forbid")
    damage: NonNegativeInt
    toughness: NonNegativeInt
    control: NonNegativeInt
    mobility: NonNegativeInt
    utility: NonNegativeInt
    abilityReliance: NonNegativeInt
    difficulty: NonNegativeInt


class Modifier(BaseModel):
    model_config = ConfigDict(extra="forbid")
    values: list[float]
    units: list[str]


class Cooldown(BaseModel):
    model_config = ConfigDict(extra="forbid")
    modifiers: Annotated[
        ModifiersModel,
        BeforeValidator(
            ModifiersOrchestrator(
                ModifierNormalizeUnitsStage(
                    EmptyUnitCorrection(), TrimUnitCorrection()
                ),
                ModifierSplitBaseEnhancementsStage(),
                ModifierExtractBracketStatsStage(),
                ModifierCollectAttributesStage(),
            )
        ),
    ]
    affectedByCdr: bool


class Cost(BaseModel):
    model_config = ConfigDict(extra="forbid")
    modifiers: Annotated[
        ModifiersModel,
        BeforeValidator(
            ModifiersOrchestrator(
                ModifierNormalizeUnitsStage(
                    EmptyUnitCorrection(), TrimUnitCorrection()
                ),
                ModifierSplitBaseEnhancementsStage(),
                ModifierExtractBracketStatsStage(),
                ModifierCollectAttributesStage(),
            )
        ),
    ]


class Leveling(BaseModel):
    attribute: str  # TODO: Will need a Literal
    modifiers: Annotated[
        ModifiersModel,
        BeforeValidator(
            ModifiersOrchestrator(
                ModifierNormalizeUnitsStage(
                    EmptyUnitCorrection(), TrimUnitCorrection()
                ),
                ModifierSplitBaseEnhancementsStage(),
                ModifierExtractBracketStatsStage(),
                ModifierCollectAttributesStage(),
            )
        ),
    ]


class Effect(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str
    leveling: list[Leveling]


class Ability(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    icon: HttpUrl
    effects: list[Effect]
    cost: Cost | None
    cooldown: Cooldown | None
    targeting: Any
    affects: Annotated[
        AffectsModel,
        BeforeValidator(
            AffectsOrchestrator(
                AffectsExtractOptionsStage(
                    GenericTrimCorrection(),
                    GenericAliasCorrection(AFFECT_TOKEN_ALIASES, NONE_MAP),
                ),
            )
        ),
    ]
    spellshieldable: Any | None
    resource: Resource | None
    damageType: DamageType | None
    spellEffects: Any | None
    projectile: Projectile | None
    onHitEffects: Any | None
    occurrence: Any | None
    notes: Any | None
    blurb: Any | None
    missileSpeed: Any | None
    rechargeRate: Any | None
    collisionRadius: Annotated[
        list[float | None],
        BeforeValidator(
            CollisionRadiusOrchestrator(
                CollisionRadiusExtractOptionsStage(
                    CollisionRadiusTrimCorrection(),
                ),
                CollisionRadiusStrToFloatCorrection(),
            )
        ),
    ]
    tetherRadius: Any | None
    onTargetCdStatic: Any | None
    innerRadius: Annotated[
        InnerRadiusModel,
        BeforeValidator(
            InnerRadiusOrchestrator(
                InnerRadiusExtractOptionsStage(),
                InnerRadiusTransformValuesStage(),
            )
        ),
    ]
    speed: str | None  # To be annotated
    width: str | None  # To be annotated
    angle: Annotated[
        list[float | None],
        BeforeValidator(
            AngleOrchestrator(
                AngleExtractOptionsStage(AngleTrimCorrection()),
                AngleParseDegreesStage(AngleStrToFloatCorrection()),
            )
        ),
    ]
    castTime: Annotated[
        CastTimeModel,
        BeforeValidator(
            CastTimeOrchestrator(
                CastTimeExtractOptionsStage(
                    CastTimeTrimCorrection(),
                    CastTimeNoneTypeCorrection(),
                    CastTimeNormaliseWhitespaceCorrection(),
                ),
                CastTimeCoreAndContextStage(),
                CastTimeParseCoreStage(),
                CastTimeParseContextStage(),
            )
        ),
    ]  # To be annotated
    effectRadius: str | None  # To be annotated
    targetRange: Any | None


class Abilities(BaseModel):
    P: list[Ability]
    Q: list[Ability]
    W: list[Ability]
    E: list[Ability]
    R: list[Ability]


class PriceOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blueEssence: NonNegativeInt
    rp: NonNegativeInt
    saleRp: NonNegativeInt


# Doesn't represent the exact structure, but since it was to be discarded we went with the minimum structure required for the parsing to run
class SkinAttributes(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    id: int
    isBase: bool
    availability: str
    formatName: str
    lootEligible: bool
    cost: NonNegativeInt | Literal["Special", "Battle Pass", "Sanctum"] | None
    sale: NonNegativeInt
    distribution: str | None
    rarity: str
    chromas: list[Any]
    lore: str | None
    release: str
    set: list[Any]
    splashPath: HttpUrl
    uncenteredSplashPath: HttpUrl
    tilePath: HttpUrl
    loadScreenPath: HttpUrl
    loadScreenVintagePath: HttpUrl | None
    newEffects: bool
    newAnimations: bool
    newRecall: bool
    newVoice: bool
    newQuotes: bool
    voiceActor: list[str]
    splashArtist: list[str]


class ChampionInformation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: PositiveInt
    key: str
    name: str
    title: str
    fullName: str
    icon: HttpUrl
    resource: Resource | None
    attackType: AttackType | None
    adaptiveType: AdaptiveType | None
    stats: Stats
    positions: list[Position]
    roles: list[Role]
    attributeRatings: AttributeRating
    abilities: Abilities
    releaseDate: str
    releasePatch: str
    patchLastChanged: str
    price: PriceOptions
    lore: str
    faction: str
    skins: list[SkinAttributes]
