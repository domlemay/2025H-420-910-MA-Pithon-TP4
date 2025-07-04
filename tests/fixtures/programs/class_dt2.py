name = "Nom de test declarer"

class ChekerDouble:
    def __init__(self, value: int, name: str):
        self.value = value
        self.name = name
        
    def printer(self) -> None:
        print(f"Value: {self.value}, Name: {self.name}")
        
CKDO1 = ChekerDouble(10, "Nom qui provient de la classe ChekerDouble")

CKDO1.printer()  # Affiche "Value: 10, Nom: Nom qui provient de la classe ChekerDouble"

print(CKDO1.value)  # Affiche 10

print(CKDO1.name)  # Affiche "Nom qui provient de la classe ChekerDouble"

print(name) # Affiche "Nom de test declarer"