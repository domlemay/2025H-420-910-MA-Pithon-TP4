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
        if self.nbr_students <= 0:
            print("Le nombre d'étudiants doit etre plus grand que 0.")
        return self.nbr_of_exam * self.nbr_students

cp = Class_of_prog_one("Professeur X", 3, 2, 30)
    
print (cp.nbr_exam_a_corriger())  # Affiche le nombre d'examens à corriger
