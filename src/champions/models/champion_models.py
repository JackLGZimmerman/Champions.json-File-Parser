from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, PositiveInt

NonNegativeFloat = Annotated[float, Field(ge=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]

Role = str
Resource = str
AttackType = str
AdaptiveType = str
DamageType = str
Projectile = str
Position = str


class AttributeMetric(BaseModel):
    model_config = ConfigDict(extra="forbid")
    flat: float
    percent: float
    perLevel: NonNegativeFloat
    percentPerLevel: float


class Stats(BaseModel):
    model_config = ConfigDict(extra="allow")
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
    modifiers: Any
    affectedByCdr: bool


class Cost(BaseModel):
    model_config = ConfigDict(extra="forbid")
    modifiers: Any


class Leveling(BaseModel):
    attribute: str
    modifiers: Any


class Effect(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str
    leveling: list[Leveling]


class Ability(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str
    icon: HttpUrl
    effects: list[Effect]
    cost: Cost | None = None
    cooldown: Cooldown | None = None
    targeting: Any
    affects: Any
    spellshieldable: Any | None = None
    resource: Resource | None = None
    damageType: DamageType | None = None
    spellEffects: Any | None = None
    projectile: Projectile | None = None
    onHitEffects: Any | None = None
    occurrence: Any | None = None
    notes: Any | None = None
    blurb: Any | None = None
    missileSpeed: Any | None = None
    rechargeRate: Any | None = None
    collisionRadius: Any
    tetherRadius: Any | None = None
    onTargetCdStatic: Any | None = None
    innerRadius: Any
    speed: str | None = None
    width: str | None = None
    angle: Any
    castTime: Any
    effectRadius: str | None = None
    targetRange: Any | None = None


class Abilities(BaseModel):
    model_config = ConfigDict(extra="allow")
    P: list[Ability] = Field(default_factory=list)
    Q: list[Ability] = Field(default_factory=list)
    W: list[Ability] = Field(default_factory=list)
    E: list[Ability] = Field(default_factory=list)
    R: list[Ability] = Field(default_factory=list)


class PriceOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")
    blueEssence: NonNegativeInt
    rp: NonNegativeInt
    saleRp: NonNegativeInt


class SkinAttributes(BaseModel):
    model_config = ConfigDict(extra="allow")
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
    model_config = ConfigDict(extra="allow")
    id: PositiveInt
    key: str
    name: str
    title: str
    fullName: str
    icon: HttpUrl
    resource: Resource | None = None
    attackType: AttackType | None = None
    adaptiveType: AdaptiveType | None = None
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
