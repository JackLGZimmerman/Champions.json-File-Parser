# Next Changes

- abilities -> effects
- abilities -> cost
- abilities -> cooldown

# Example

## Affects

```json
    "affects": {
      "types": [
        "offensive"
      ],
      "cardinalities": [
        "multiple"
      ],
      "domains": [
        "players"
      ],
      "summons": [],
      "specials": [],
      "values": [
        "Enemies"
      ]
    },
```

### Thoughts

- (STRONG) Thinking that summons and specials should probably be a bool to indicate they are somthing special
- (CONSIDERATION) Combine summons and specials into 1 since they are so rare as it is.
