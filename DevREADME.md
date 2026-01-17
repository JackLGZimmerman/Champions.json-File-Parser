# Attributes

## Effects

### Special Issues

Akshan has a very dodgy unit:

- [25 / 35 / 45 (+ 15% AD)] × [1 + 0 – 0.5 (based on critical strike chance) + An icon for the item Infinity Edge 0.2]

Which is split up into the following modifiers:

- "[25 / 30 / 35 / 40 / 45 ] \u00d7 [1"
- "0 : 0.5 "
- "]"
- "% AD"
- "based on critical strike chance"

Akshans modifiers are a bit bugged, seems like the values should be [25,35,45], however

After we create the unit, enhanced split.

We need a new pipeline for

- Everything in brackets is an enhancement on the base value UNLESS

  - It is the only thing present (1) then it becomes the base unit

- Typically everything is simple the base unit using some form of long text (1 attribute)
  - That is usually supported by N brackets which provide enhancements in damage (N attributes)

#### Plan

- We will collect everything outside of brackets and call that the base_unit
- We will collect every bracket group and call them the enhancements
  - If we only have the bracket group that will be the base_unit
- We will create a dictionary of attributes (AD, attack speed, % HP, % AP, etc...) this will be collected in a modifer wide attribute field
- Akshan Modifiers will just be concatenated into a single one.
  - We will still use the dictionary on the full unit to collect the attributes list
  - No enhancements
  - Will be checked for attributes
- Operations are base units, generally fine as is
  - May include additional clear descriptor E.G "This is capped at 67% reduction at 111.1% bonus attack speed" or ", capped at 120 bonus resistances"

### Information

- Description
  Each description is a mutually exclusive element of the ability, that provides detail on a different aspect of its use.

- Leveling
  - Attribute
    Each attribute is a mutually exclusive element of an aspect of an ability. For example Aatrox Q has 3 phases, during Q3 there is a sweet spot that deals extra damage,
    and zone that deals normal damage. These will be classified as 2 attributes of this ability aspect.
  - Modifiers
    If a description is purly contextual or remains fixed during leveling, there will not be anything in the leveling list to describe how it changes per level.

# Modifer Stages

- Units: They (so far) are always the same, so we can unify them under a single value -> Unit

**Initial Value**

```json
[
  {
    "values": [36, 60, 84, 108, 132],
    "units": ["", "", "", "", ""]
  },
  {
    "values": [6.4, 6.4, 6.4, 6.4, 6.4],
    "units": [
      "% (+ 1.6% per 100 bonus armor) (+ 1.6% per 100 bonus magic resistance) of target's maximum health",
      "% (+ 1.6% per 100 bonus armor) (+ 1.6% per 100 bonus magic resistance) of target's maximum health",
      "% (+ 1.6% per 100 bonus armor) (+ 1.6% per 100 bonus magic resistance) of target's maximum health",
      "% (+ 1.6% per 100 bonus armor) (+ 1.6% per 100 bonus magic resistance) of target's maximum health",
      "% (+ 1.6% per 100 bonus armor) (+ 1.6% per 100 bonus magic resistance) of target's maximum health"
    ]
  }
]
```

**Compress Units**

```json
[
  {
    "values": [36, 60, 84, 108, 132],
    "units": ""
  },
  {
    "values": [6.4, 6.4, 6.4, 6.4, 6.4],
    "units": "% (+ 1.6% per 100 bonus armor) (+ 1.6% per 100 bonus magic resistance) of target's maximum health"
  }
]
```

**Base and Enhanced Split**

```json
{
  "base": {
    "values": [36, 60, 84, 108, 132],
    "unit": None
  },
  "enhancements": [
    {
      "values": [6.4, 6.4, 6.4, 6.4, 6.4],
      "unit": "% (+ 1.6% per 100 bonus armor) (+ 1.6% per 100 bonus magic resistance) of target's maximum health" ,
    },
  ]
}
```

**Parse Unit**

```json
{
  "base": {
    "values": [36, 60, 84, 108, 132],
    "base_unit": None,
    "enhancement_stats": []
  },
  "enhancements": [
    {
      "values": [6.4, 6.4, 6.4, 6.4, 6.4],
      "base_unit": "% of target's maximum health",
      "enhancement_stats": [
        "+ 1.6% per 100 bonus armor",
        "+ 1.6% per 100 bonus magic resistance"]
    },
  ]
}
```

**Attribute List**

```json
{
  "attributes": ["% maximum health", "bonus armor", "bonus magic resistance"],
  "base": {
    "values": [36, 60, 84, 108, 132],
    "base_unit": None,
    "enhancement_stats": []
  },
  "enhancements": [
    {
      "values": [6.4, 6.4, 6.4, 6.4, 6.4],
      "base_unit": "% of target's maximum health",
      "enhancement_stats": [
        "+ 1.6% per 100 bonus armor",
        "+ 1.6% per 100 bonus magic resistance"]
    },
  ]
}
```

**Empty Modifer**

```json
{
  "attributes": ["% AD", "critical strike chance"]
  "base": {
    "values": [0, 0, 0],
    "unit": "[375 / 630 / 945 ] × [1 + 0 : 0.5 ] % AD based on critical strike chance"
  },
  "enhancements": []
}
```

# Cast Time Stages

```json
"0.35 : 0.175 (based on bonus attack speed) / 0.35 : 0.28 (based on bonus attack speed)"
```

```json
[
  "0.35 : 0.175 (based on bonus attack speed)",
  "0.35 : 0.28 (based on bonus attack speed)"
]
```

```json
[
  { "upper": 0.35, "lower": 0.175, "context": "based on bonus attack speed" },
  { "upper": 0.35, "lower": 0.28, "context": "based on bonus attack speed" }
]
```

What are all of the single item structures with text, like 'based on':

- 140% of Viego's windup time (0.35 at base attack speed)
- 0.175 (based on bonus attack speed)
- Basic Attack Timer

```json
{
  "attributes": ["attack speed"],
  "values": [
    {
      "upper": 0.35,
      "lower": 0.175,
      "context": "based on bonus attack speed"
    },
    {
      "upper": 0.35,
      "lower": 0.28,
      "context": "based on bonus attack speed"
    }
  ]
}
```

```json
{
  "values": [
    {
      "value": {
        "kind": "range",
        "from": 0.35,
        "to": 0.175
      },
      "condition": {
        "kind": "scales_with",
        "attribute": "bonus_attack_speed"
      }
    }
  ]
}
```

```json
{
  "values": [
    {
      "value": {
        "kind": "reference",
        "reference": {
          "kind": "windup_time",
          "owner": "Viego"
        },
        "multiplier": 1.4
      },
      "example": {
        "value": 0.35,
        "at": "base_attack_speed"
      }
    }
  ]
}
```

- (based on bonus attack speed)
- (0.23 at base attack speed)