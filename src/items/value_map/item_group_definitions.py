from collections.abc import Callable
from typing import Any

ItemGroupFactory = Callable[[str, list[int], dict[str, float]], Any]
BuildValuesFactory = Callable[..., dict[str, float]]


def build_item_group_definitions(
    item_group: ItemGroupFactory,
    build_values: BuildValuesFactory,
) -> tuple[Any, ...]:
    return (
        item_group(
            "Pure AP Items",
            [
                2503,  # Blackfire Torch
                2522,  # Actualizer
                3003,  # Archangel's Staff
                3040,  # Seraph's Embrace
                3100,  # Lich Bane
                3118,  # Malignance
                3135,  # Void Staff
                4645,  # Shadowflame
                4646,  # Stormsurge
                6655,  # Luden's Echo
            ],
            build_values(ability_power=1.0),
        ),
        item_group(
            "Lethality Items",
            [
                2520,  # Bastionbreaker
                3142,  # Youmuu's Ghostblade
                3179,  # Umbral Glaive
                6696,  # Axiom Arc
                6697,  # Hubris
                6698,  # Profane Hydra
                6699,  # Voltaic Cyclosword
                6701,  # Opportunity
            ],
            build_values(attack_damage=0.51, lethality=1.0),
        ),
        item_group(
            "AP Bruiser Items",
            [
                3152,  # Hextech Rocketbelt
                4629,  # Cosmic Drive
                4633,  # Riftmaker
                6653,  # Liandry's Torment
                6657,  # Rod of Ages
                8010,  # Bloodletter's Curse
            ],
            build_values(ability_power=0.51, ap_off_tank=1.0),
        ),
        item_group(
            "AD Bruiser Items",
            [
                2501,  # Overlord's Bloodmail
                3053,  # Sterak's Gage
                3073,  # Experimental Hexplate
                3078,  # Trinity Force
                3161,  # Spear of Shojin
                3181,  # Hullbreaker
                6610,  # Sundered Sky
                6631,  # Stridebreaker
            ],
            build_values(attack_damage=0.51, ad_off_tank=1.0),
        ),
        item_group(
            "Armor Tank Items",
            [
                3068,  # Sunfire Aegis
                3742,  # Dead Man's Plate
                6662,  # Iceborn Gauntlet
            ],
            build_values(ar_tank=1.0),
        ),
        item_group(
            "AD Crit Items",
            [
                2523,  # Hexoptics C44
                3032,  # Yun Tal Wildarrows
                3033,  # Mortal Reminder
                3036,  # Lord Dominik's Regards
                3097,  # Stormrazor
                6673,  # Immortal Shieldbow
            ],
            build_values(attack_damage=0.51, crit=1.0),
        ),
        item_group(
            "Full Tank Items",
            [
                6665,  # Jak'Sho, The Protean
            ],
            build_values(ar_tank=1.0, mr_tank=1.0),
        ),
        item_group(
            "Unending Despair",
            [2502],
            build_values(ar_tank=1.0),
        ),
        item_group(
            "Protoplasm Harness",
            [2525],
            build_values(
                ar_tank=0.51,
                mr_tank=0.51,
                ad_off_tank=0.51,
                ap_off_tank=0.51,
            ),
        ),
        item_group(
            "Warmog's Armor",
            [3083],
            build_values(
                ar_tank=0.51,
                mr_tank=0.51,
                ad_off_tank=0.26,
                ap_off_tank=0.26,
            ),
        ),
        item_group(
            "Heartsteel",
            [3084],
            build_values(
                ar_tank=1.0,
                mr_tank=1.0,
                ad_off_tank=0.51,
                ap_off_tank=0.51,
            ),
        ),
        item_group(
            "Light Mixed Tank Items",
            [
                3119,  # Winter's Approach
                3121,  # Fimbulwinter
            ],
            build_values(ar_tank=0.51, mr_tank=0.51),
        ),
        item_group(
            "MR Tank Items",
            [
                2504,  # Kaenic Rookern
                3065,  # Spirit Visage
                4401,  # Force of Nature
                6664,  # Hollow Radiance
            ],
            build_values(mr_tank=1.0),
        ),
        item_group(
            "Utility Enchanter Items",
            [
                2065,  # Shurelya's Battlesong
                3504,  # Ardent Censer
                4005,  # Imperial Mandate
                6616,  # Staff of Flowing Water
            ],
            build_values(ability_power=0.51, utility_enchanter=1.0),
        ),
        item_group(
            "Dawncore",
            [6621],
            build_values(ability_power=0.51, utility_protection=1.0),
        ),
        item_group(
            "Pure AD Items",
            [
                2517,  # Endless Hunger
                3072,  # Bloodthirster
                6692,  # Eclipse
                6694,  # Serylda's Grudge
            ],
            build_values(attack_damage=1.0),
        ),
        item_group(
            "Crit Items",
            [
                2512,  # Fiendhunter Bolts
                3046,  # Phantom Dancer
                3094,  # Rapid Firecannon
                6675,  # Navori Flickerblade
            ],
            build_values(crit=1.0),
        ),
        item_group(
            "Pure Protection Items",
            [
                2526,  # Whispering Circlet
                2530,  # Diadem of Songs,
                3107,  # Redemption
                3222,  # Mikael's Blessing
                3870,  # Dream Maker
                6617,  # Moonstone Renewer
                6620,  # Echoes of Helia
            ],
            build_values(utility_protection=1.0),
        ),
        item_group(
            "Bandlepipes",
            [
                2524,  # Bandlepipes
            ],
            build_values(ar_tank=0.51, mr_tank=0.51, utility_enchanter=1.0),
        ),
        item_group(
            "Utility Protection Items",
            [
                3050,  # Zeke's Convergence
                3190,  # Locket of the Iron Solari
            ],
            build_values(ar_tank=0.51, mr_tank=0.51, utility_protection=1.0),
        ),
        item_group(
            "On-Hit Items",
            [
                3153,  # Blade of The Ruined King
                3302,  # Terminus
                6672,  # Kraken Slayer
            ],
            build_values(on_hit=1.0, ar_tank=0.26, mr_tank=0.26),
        ),
        item_group(
            "Berserker Boot Pair",
            [
                3006,  # Berserker's Greaves
                3172,  # Gunmetal Greaves
            ],
            build_values(crit=0.51, on_hit=0.26, attack_damage=0.26),
        ),
        item_group(
            "Gluttonous Boot Pair",
            [
                3008,  # Gluttonous Greaves
                3168,  # Immortal Path
            ],
            build_values(attack_damage=0.26, ability_power=0.26, on_hit=0.26),
        ),
        item_group(
            "No Op Items",
            [
                3009,  # Boots of Swiftness
                3013,  # Synchronized Souls
                3117,  # Mobility Boots
                3158,  # Ionian Boots of Lucidity
                3170,  # Swiftmarch
                3171,  # Crimson Lucidity
                3176,  # Forever Forward
            ],
            build_values(),
        ),
        item_group(
            "Sorcerer Boot Pair",
            [
                3020,  # Sorcerer's Shoes
                3175,  # Spellslinger's Shoes
            ],
            build_values(ability_power=0.51),
        ),
        item_group(
            "Plated Boot Pair",
            [
                3047,  # Plated Steelcaps
                3174,  # Armored Advance
            ],
            build_values(ar_tank=0.51),
        ),
        item_group(
            "Mercury Boot Pair",
            [
                3111,  # Mercury's Treads
                3173,  # Chainlaced Crushers
            ],
            build_values(mr_tank=0.51),
        ),
        item_group(
            "Light Utility Protection Items",
            [
                3109,  # Knight's Vow
            ],
            build_values(utility_protection=1.0, ar_tank=0.51),
        ),
        item_group(
            "Light Utility Enchanter Items",
            [
                3002,  # Trailblazer
            ],
            build_values(utility_enchanter=1.0, ar_tank=0.51),
        ),
        item_group(
            "AP Utility Enchanter Items",
            [
                4628,  # Horizon Focus
            ],
            build_values(ability_power=1.0, utility_enchanter=0.51),
        ),
        item_group(
            "AP Utility Protection Items",
            [
                3137,  # Cryptbloom
            ],
            build_values(ability_power=1.0, utility_protection=0.51),
        ),
        item_group(
            "AP Bruiser Utility Enchanter Items",
            [
                3116,  # Rylai's Crystal Scepter
                3165,  # Morellonomicon
            ],
            build_values(ability_power=0.51, ap_off_tank=1.0, utility_enchanter=0.26),
        ),
        item_group(
            "AD Bruiser Utility Enchanter Items",
            [
                3071,  # Black Cleaver
                6609,  # Chempunk Chainsword
            ],
            build_values(attack_damage=0.51, ad_off_tank=1.0, utility_enchanter=0.26),
        ),
        item_group(
            "Lethality Utility Enchanter Items",
            [
                6695,  # Serpent's Fang
            ],
            build_values(attack_damage=0.51, lethality=1.0, utility_enchanter=0.51),
        ),
        item_group(
            "Armor Utility Enchanter Items",
            [
                3075,  # Thornmail
            ],
            build_values(ar_tank=1.0, utility_enchanter=0.51),
        ),
        item_group(
            "Light Armor Utility Enchanter Items",
            [
                3110,  # Frozen Heart
                3143,  # Randuin's Omen
            ],
            build_values(ar_tank=1.0, utility_enchanter=0.26),
        ),
        item_group(
            "MR Utility Enchanter Items",
            [
                8020,  # Abyssal Mask
            ],
            build_values(mr_tank=1.0, utility_enchanter=0.51),
        ),
        item_group(
            "Minor Utility Enchanter Items",
            [
                3877,  # Bloodsong
            ],
            build_values(utility_enchanter=0.51),
        ),
        item_group(
            "AD MR Items",
            [
                3139,  # Mercurial Scimitar
                3156,  # Maw of Malmortius
            ],
            build_values(attack_damage=1.0, mr_tank=0.51),
        ),
        item_group(
            "Heavy AD On-Hit Items",
            [
                3004,  # Manamune
                3042,  # Muramana
                3074,  # Ravenous Hydra
            ],
            build_values(attack_damage=1.0, on_hit=0.51),
        ),
        item_group(
            "Dusk and Dawn",
            [2510],
            build_values(ability_power=1.0, on_hit=1.0, ap_off_tank=0.51),
        ),
        item_group(
            "Guardian Angel",
            [3026],
            build_values(attack_damage=0.51, ar_tank=0.51),
        ),
        item_group(
            "Infinity Edge",
            [3031],
            build_values(attack_damage=0.51, crit=2.0),
        ),
        item_group(
            "Mejai's Soulstealer",
            [3041],
            build_values(ability_power=0.51, ap_off_tank=0.51, utility_enchanter=0.51),
        ),
        item_group(
            "Runaan's Hurricane",
            [3085],
            build_values(on_hit=0.51, crit=1.0),
        ),
        item_group(
            "Statikk Shiv",
            [3087],
            build_values(attack_damage=0.51, on_hit=0.51, ability_power=0.51),
        ),
        item_group(
            "Rabadon's Deathcap",
            [3089],
            build_values(ability_power=2.0),
        ),
        item_group(
            "Wit's End",
            [3091],
            build_values(on_hit=1.0, mr_tank=0.51),
        ),
        item_group(
            "Banshee's Veil",
            [3102],
            build_values(ability_power=1.0, mr_tank=0.51),
        ),
        item_group(
            "Nashor's Tooth",
            [3115],
            build_values(ability_power=1.0, on_hit=0.51),
        ),
        item_group(
            "Guinsoo's Rageblade",
            [3124],
            build_values(on_hit=2.0),
        ),
        item_group(
            "Hextech Gunblade",
            [3146],
            build_values(attack_damage=0.51, ability_power=1.0),
        ),
        item_group(
            "Zhonya's Hourglass",
            [3157],
            build_values(ability_power=1.0, ar_tank=0.51),
        ),
        item_group(
            "Essence Reaver",
            [3508],
            build_values(attack_damage=0.51, on_hit=0.51, crit=1.0),
        ),
        item_group(
            "Titanic Hydra",
            [3748],
            build_values(attack_damage=0.51, on_hit=0.51, ad_off_tank=1.0),
        ),
        item_group(
            "Edge of Night",
            [3814],
            build_values(attack_damage=0.51, lethality=1.0, ad_off_tank=1.0),
        ),
        item_group(
            "Celestial Opposition Protection",
            [3869],
            build_values(ar_tank=0.26, mr_tank=0.26, utility_enchanter=0.26),
        ),
        item_group(
            "Zaz'Zak's Realmspike Enchanter",
            [3871],
            build_values(ability_power=0.51),
        ),
        item_group(
            "Solstice Sleigh Protection",
            [3876],
            build_values(utility_protection=0.51),
        ),
        item_group(
            "Death's Dance",
            [6333],
            build_values(attack_damage=1.0, ad_off_tank=0.51),
        ),
        item_group(
            "The Collector",
            [6676],
            build_values(attack_damage=0.51, lethality=0.51, crit=1.0),
        ),
    )
