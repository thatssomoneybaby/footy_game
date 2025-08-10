"""
Enhanced Player Generation Service

Generates realistic AFL players with:
- Diverse name pool from multiple cultures
- Realistic overall ratings with proper distributions
- Age-based skill curves (peak at mid-20s)
- Position-specific attribute weighting
- Fewer elite players, more realistic spread
"""

import random
from typing import List, Tuple, Dict
from app.db.models import Player, Position


class PlayerGenerator:
    """Enhanced player generation with realistic names and ratings."""
    
    # Expanded name pools with cultural diversity
    FIRST_NAMES = [
        # Anglo names
        "Jack", "Tom", "Sam", "Josh", "Luke", "Ben", "Jake", "Matt", "Alex", "Dan",
        "James", "Michael", "David", "Ryan", "Nathan", "Adam", "Chris", "Mark", "Aaron", "Connor",
        "Liam", "Will", "Nick", "Tim", "Josh", "Brad", "Sean", "Kyle", "Jake", "Joel",
        
        # Indigenous Australian names
        "Jarman", "Cyril", "Eddie", "Nicky", "Shane", "Daniel", "Patrick", "Michael", "Steven", "Adam",
        "Lance", "Shaun", "Andrew", "Jason", "Dean", "Paul", "Gavin", "Jeff", "Anthony", "Lindsay",
        
        # European heritage
        "Marco", "Antonio", "Giuseppe", "Francesco", "Paolo", "Giovanni", "Roberto", "Stefano",
        "Andreas", "Dimitri", "Kostas", "Nikola", "Stefan", "Milan", "Luka", "Marko",
        
        # Pacific Islander names  
        "Sione", "Taniela", "Viliami", "Sefa", "Isi", "Junior", "Joseph", "Peter", "John", "Samuel",
        
        # Other multicultural names
        "Hassan", "Omar", "Ahmed", "Ali", "Youssef", "Karim", "Zayed", "Khalil",
        "Hiroshi", "Kenji", "Takeshi", "Akira", "Taro"
    ]
    
    LAST_NAMES = [
        # Anglo surnames
        "Smith", "Johnson", "Brown", "Taylor", "Anderson", "Thomas", "Jackson", "White",
        "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez",
        "Lewis", "Lee", "Walker", "Hall", "Allen", "Young", "Hernandez", "King", "Wright",
        "Campbell", "Mitchell", "Carter", "Parker", "Evans", "Turner", "Diaz", "Edwards",
        "Collins", "Stewart", "Sanchez", "Morris", "Rogers", "Reed", "Cook", "Bailey",
        "Murphy", "Cooper", "Richardson", "Cox", "Howard", "Ward", "Torres", "Peterson",
        "Gray", "Ramirez", "Watson", "Brooks", "Kelly", "Sanders", "Price", "Bennett",
        "Wood", "Barnes", "Ross", "Henderson", "Coleman", "Jenkins", "Perry", "Powell",
        "Long", "Patterson", "Hughes", "Flores", "Washington", "Butler", "Simmons", "Foster",
        
        # Indigenous surnames
        "Rioli", "Pickett", "Hill", "Davis", "Williams", "Wilson", "Jones", "Miller", "Moore",
        "Ryan", "Bell", "Hunt", "Cameron", "Reid", "McDonald", "Graham", "Simpson", "Armstrong",
        "Michael", "Farmer", "Walters", "Matera", "Hunter", "Yarran", "Jetta", "Garlett",
        
        # European surnames
        "Rossi", "Ferrari", "Bianchi", "Romano", "Colombo", "Ricci", "Marino", "Greco",
        "Bruno", "Gallo", "Conti", "De Luca", "Costa", "Giordano", "Rizzo", "Lombardi",
        "Papadopoulos", "Nikolaidis", "Georgiou", "Dimitriou", "Petrov", "Stojanovic", "Novak",
        
        # Pacific Islander surnames
        "Taumalolo", "Fonua", "Tupou", "Fifita", "Pangai", "Ofahengaue", "Kaufusi", "Frizell",
        "Papali'i", "Su'A", "Milford", "Haas", "Carrigan", "Flegler", "Riki", "Piakura",
        
        # Other multicultural surnames
        "Al-Rashid", "Hassan", "Mahmoud", "Ibrahim", "Abdullah", "Rahman", "Ahmed", "Ali",
        "Tanaka", "Suzuki", "Watanabe", "Yamamoto", "Ito", "Kobayashi", "Kato", "Yoshida"
    ]
    
    def __init__(self):
        """Initialize player generator with rating distributions."""
        # Define overall rating distributions (more realistic)
        self.rating_weights = {
            # Elite players (85-99): Very rare, only 2-3 per team
            "elite": {"range": (85, 99), "weight": 0.08},
            # Very good (75-84): Star players, 4-6 per team  
            "very_good": {"range": (75, 84), "weight": 0.15},
            # Good (65-74): Solid contributors, 8-12 per team
            "good": {"range": (65, 74), "weight": 0.35},
            # Average (55-64): Role players, 8-10 per team
            "average": {"range": (55, 64), "weight": 0.30},
            # Below average (45-54): Depth/development, 3-5 per team
            "below_average": {"range": (45, 54), "weight": 0.12}
        }
        
        # Position-specific attribute weightings
        self.position_weights = {
            Position.KPF: {
                "kicking": 1.2, "marking": 1.3, "strength": 1.1, "composure": 1.1,
                "speed": 0.9, "endurance": 0.8, "spoiling": 0.7
            },
            Position.SMALL_FWD: {
                "speed": 1.3, "kicking": 1.2, "decision_making": 1.1, "composure": 1.1,
                "marking": 0.9, "strength": 0.8, "ruck_work": 0.5
            },
            Position.MID: {
                "endurance": 1.3, "decision_making": 1.2, "kicking": 1.1, "handball": 1.2,
                "marking": 0.9, "strength": 0.9, "ruck_work": 0.6
            },
            Position.HALF_BACK: {
                "kicking": 1.2, "spoiling": 1.3, "decision_making": 1.1, "speed": 1.1,
                "marking": 1.0, "ruck_work": 0.5
            },
            Position.KP_BACK: {
                "spoiling": 1.3, "marking": 1.2, "strength": 1.2, "composure": 1.1,
                "speed": 0.8, "endurance": 0.9, "ruck_work": 0.7
            },
            Position.RUCK: {
                "ruck_work": 1.4, "strength": 1.3, "marking": 1.2, "endurance": 1.1,
                "speed": 0.7, "decision_making": 0.9
            },
            Position.UTILITY: {
                # Utility players are more balanced
                "endurance": 1.1, "decision_making": 1.1, "versatility": 1.2
            }
        }

    def generate_player_name(self) -> str:
        """Generate a realistic player name."""
        first = random.choice(self.FIRST_NAMES)
        last = random.choice(self.LAST_NAMES)
        return f"{first} {last}"
    
    def generate_player_age(self) -> int:
        """Generate realistic age distribution (18-35, peak mid-20s)."""
        # Weighted age distribution favoring 20-28 range
        ages = list(range(18, 36))
        weights = [
            0.5,   # 18: rookies/first year
            1.0,   # 19: developing  
            2.0,   # 20: improving
            3.0,   # 21: breakthrough
            4.0,   # 22: rising
            5.0,   # 23: prime entry
            5.5,   # 24: prime
            6.0,   # 25: peak
            6.0,   # 26: peak  
            5.5,   # 27: prime
            5.0,   # 28: still prime
            4.0,   # 29: veteran
            3.0,   # 30: experienced
            2.0,   # 31: older veteran
            1.5,   # 32: late career
            1.0,   # 33: very late career
            0.8,   # 34: rare
            0.5    # 35: very rare
        ]
        return random.choices(ages, weights=weights, k=1)[0]
    
    def determine_base_rating(self) -> int:
        """Determine player's base overall rating using realistic distribution."""
        # Select rating tier based on weights
        tier_choices = list(self.rating_weights.keys())
        tier_weights = [self.rating_weights[tier]["weight"] for tier in tier_choices]
        selected_tier = random.choices(tier_choices, weights=tier_weights, k=1)[0]
        
        # Generate rating within the tier range
        min_rating, max_rating = self.rating_weights[selected_tier]["range"]
        return random.randint(min_rating, max_rating)
    
    def apply_age_curve(self, base_rating: int, age: int) -> int:
        """Apply age-based skill curve to base rating."""
        if age <= 20:
            # Young players haven't reached potential yet
            multiplier = 0.75 + (age - 18) * 0.05  # 0.75 to 0.85
        elif age <= 24:
            # Rapidly improving to peak
            multiplier = 0.85 + (age - 20) * 0.05  # 0.85 to 1.05
        elif age <= 28:
            # Peak years
            multiplier = 1.05 - (age - 24) * 0.0125  # 1.05 to 1.0
        elif age <= 32:
            # Gradual decline
            multiplier = 1.0 - (age - 28) * 0.025  # 1.0 to 0.90
        else:
            # Veteran decline
            multiplier = 0.90 - (age - 32) * 0.05  # 0.90 to 0.75
            
        adjusted_rating = int(base_rating * multiplier)
        return max(25, min(99, adjusted_rating))  # Keep within bounds
    
    def generate_position_specific_attributes(self, position: Position, base_rating: int, age: int) -> Dict[str, int]:
        """Generate position-specific attribute ratings."""
        weights = self.position_weights.get(position, {})
        
        # Base variance for attributes (±10 from base rating)
        base_variance = 12
        
        attributes = {}
        attr_names = ["kicking", "handball", "marking", "spoiling", "ruck_work", 
                     "speed", "endurance", "strength", "decision_making", "leadership", "composure"]
        
        for attr in attr_names:
            # Get position weight (default 1.0 if not specified)
            weight = weights.get(attr, 1.0)
            
            # Calculate attribute rating with position weighting
            variance = random.randint(-base_variance, base_variance)
            attr_rating = int((base_rating + variance) * weight)
            
            # Apply age curve
            attr_rating = self.apply_age_curve(attr_rating, age)
            
            # Keep within bounds
            attributes[attr] = max(20, min(99, attr_rating))
        
        return attributes
    
    def generate_mental_attributes(self, age: int, base_rating: int) -> Dict[str, int]:
        """Generate mental attributes that improve significantly with age."""
        # Mental attributes improve more with age than physical
        age_bonus = max(0, (age - 20) * 2)  # +2 per year after 20
        
        leadership_base = base_rating + age_bonus + random.randint(-8, 8)
        decision_base = base_rating + (age_bonus // 2) + random.randint(-6, 6)  
        composure_base = base_rating + (age_bonus // 2) + random.randint(-6, 6)
        
        return {
            "leadership": max(20, min(99, leadership_base)),
            "decision_making": max(20, min(99, decision_base)), 
            "composure": max(20, min(99, composure_base))
        }
    
    def generate_player(self, club_id: int, position: Position = None) -> Player:
        """Generate a complete realistic player."""
        # Generate basic info
        name = self.generate_player_name()
        age = self.generate_player_age()
        position = position or random.choice(list(Position))
        
        # Generate base rating
        base_rating = self.determine_base_rating()
        
        # Generate position-specific technical and physical attributes
        attributes = self.generate_position_specific_attributes(position, base_rating, age)
        
        # Generate mental attributes (improve with age)
        mental_attrs = self.generate_mental_attributes(age, base_rating)
        attributes.update(mental_attrs)
        
        # Generate hidden attributes
        potential = random.randint(
            max(50, base_rating - 5), 
            min(99, base_rating + 15)
        )
        
        # Morale varies but tends toward positive
        morale = random.choices(
            range(-5, 6), 
            weights=[0.5, 1, 2, 3, 5, 8, 10, 8, 5, 3, 2], 
            k=1
        )[0]
        
        return Player(
            club_id=club_id,
            name=name,
            position=position,
            age=age,
            # Technical attributes
            kicking=attributes["kicking"],
            handball=attributes["handball"], 
            marking=attributes["marking"],
            spoiling=attributes["spoiling"],
            ruck_work=attributes["ruck_work"],
            # Physical attributes
            speed=attributes["speed"],
            endurance=attributes["endurance"],
            strength=attributes["strength"],
            # Mental attributes
            decision_making=attributes["decision_making"],
            leadership=attributes["leadership"],
            composure=attributes["composure"],
            # Hidden attributes
            potential=potential,
            morale=morale
        )
    
    def generate_balanced_roster(self, club_id: int, roster_size: int = 30) -> List[Player]:
        """Generate a balanced roster with proper position distribution."""
        players = []
        
        # Define position distribution for balanced roster
        position_targets = {
            Position.KPF: 3,           # Key forwards
            Position.SMALL_FWD: 4,     # Small forwards  
            Position.MID: 8,           # Midfielders (most important)
            Position.HALF_BACK: 4,     # Half backs
            Position.KP_BACK: 3,       # Key defenders
            Position.RUCK: 2,          # Ruckmen
            Position.UTILITY: 6        # Utility players (flexibility)
        }
        
        # Generate players for each position
        for position, target in position_targets.items():
            for _ in range(target):
                if len(players) < roster_size:
                    player = self.generate_player(club_id, position)
                    players.append(player)
        
        # Fill remaining slots with utility players if needed
        while len(players) < roster_size:
            player = self.generate_player(club_id, Position.UTILITY)
            players.append(player)
            
        return players