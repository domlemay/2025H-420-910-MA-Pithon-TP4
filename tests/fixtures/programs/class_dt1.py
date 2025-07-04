class Class_of_prog_one:
    def __init__(self, teacher_name: str, nbr_of_exam: int, nbr_of_project: int, nbr_students: int):
        self.teacher_name = teacher_name
        self.nbr_of_exam = nbr_of_exam
        self.nbr_of_project = nbr_of_project
        self.nbr_students = nbr_students
        

    def nbr_exam_a_corriger(self) -> int:
        """Retourne le nombre d'examens à corriger."""
        if self.nbr_of_exam <= 0:        
            print("Le nombre d'examens doit etre plus grand que 0.")
            return 0
        if self.nbr_students <= 0:
            print("Le nombre d'étudiants doit etre plus grand que 0.")
            return 0
        return self.nbr_of_exam * self.nbr_students
    
    def get_teacher_info(self) -> str:
        """Retourne les informations du professeur."""
        return f"Professeur: {self.teacher_name}, Examens: {self.nbr_of_exam}, Projets: {self.nbr_of_project}, Étudiants: {self.nbr_students}"
    
    # def raise_test(self):
    #     """Teste la gestion des exceptions."""
    #     print("Lancement de l'exception de test...")
    #     raise ValueError("Ceci est une exception de test.")
    
    # def try_catch_test(Class_of_prog_one):
    #     """Teste la gestion des exceptions avec try-except."""
    #     try:
    #         Class_of_prog_one.nbr_exam_a_corriger() > 0
    #         print(f"Il y a {Class_of_prog_one.nbr_exam_a_corriger()} examens à corriger.")   
    #     except:
    #         print("Aucun examen à corriger.")


cp = Class_of_prog_one("Professeur X", 3, 2, 30)
cp0 = Class_of_prog_one("Professeur Y", 0, 2, 30)
    
print (cp.nbr_exam_a_corriger())  # Affiche le nombre d'examens à corriger
# cp.try_catch_test()
# cp0.try_catch_test()

