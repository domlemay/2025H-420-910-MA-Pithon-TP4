"""
Évaluateur pour les fonctionnalités de classe dans Pithon.
Contient toutes les fonctions d'évaluation liées aux classes, objets, attributs et méthodes.
"""

from pithon.evaluator.envframe import EnvFrame
from pithon.syntax import PiClassDef, PiAttribute, PiAttributeAssignment, PiFunctionCall # a la place de PiFunctionCall, j'ai utiliser PiAttribute pour mieux comprendre la structure et le niveau de parallelisme avec les fonctions hors des classes.
from pithon.evaluator.envvalue import (
    EnvValue, VFunctionClosure, VClassDef, VMethodClosure, VObject, VNone, VList
)
#J'ai utiliser method pour mieux comprendre la structure et le niveau de parallelisme avec les fonctions hors des classes.


   # Instanciation d'une classe
# Cette fonction est appelée lors de l'instanciation d'une classe dans le code Pithon.
# Elle crée un nouvel objet de la classe et appelle la méthode __init__ si elle existe
def instantiate_class(class_def: VClassDef, args: list[EnvValue], evaluate_stmt_func) -> EnvValue:
    """Instancie une classe en créant un nouvel objet."""
    # Créer une nouvelle instance de la classe
    instance = VObject(class_def, {})
    
    # Appeler __init__ si elle existe
    if "__init__" in class_def.methods:
        init_method = class_def.methods["__init__"]
        # Créer un environnement pour l'appel de méthode avec 'self'
        call_env = EnvFrame(parent=init_method.closure_env)
        call_env.insert("self", instance)
        
        # Lier les arguments (en sautant 'self' qui est déjà lié)
        for i, arg_name in enumerate(init_method.funcdef.arg_names[1:]):  # Skip 'self'
            if i < len(args):
                call_env.insert(arg_name, args[i])
            else:
                raise TypeError("Argument manquant pour __init__.")
        
        # Vérifier qu'il n'y a pas trop d'arguments
        if len(args) > len(init_method.funcdef.arg_names) - 1:
            raise TypeError("Trop d'arguments pour __init__.")
        
        # Exécuter __init__
        try:
            for stmt in init_method.funcdef.body:
                evaluate_stmt_func(stmt, call_env)
        except Exception as e:
            # Vérifier si c'est une ReturnException (éviter l'import circulaire)
            if e.__class__.__name__ == 'ReturnException':
                pass  # __init__ ne retourne rien d'utile
            else:
                raise TypeError(f"Erreur lors de l'appel de __init__: {str(e)}")
    
    return instance  # Retourne l'instance créée

    # Évalue une définition de classe et stocke la classe dans l'environnement via le dictionnaire methods.
# Cette fonction est appelée lors de la rencontre d'une définition de classe dans le code Pithon.
def evaluate_class_def(node: PiClassDef, env: EnvFrame) -> EnvValue:
    """Évalue une définition de classe."""
    methods = {}
    
    # Traiter chaque méthode de la classe
    for method in node.methods:
        method_closure = VFunctionClosure(method, env)
        methods[method.name] = method_closure
    
    # Créer la définition de classe
    class_def = VClassDef(node.name, methods)
    
    # Stocker la classe dans l'environnement
    env.insert(node.name, class_def)
    
    return VNone(value=None)

# Évalue l'appel de fonction ou de méthode de la classe
def evaluate_attribute(node: PiAttribute, env: EnvFrame, evaluate_stmt_func) -> EnvValue:
    """Évalue l'accès à un attribut d'un objet (obj.attr)."""
    obj = evaluate_stmt_func(node.object, env)
    
    if isinstance(obj, VObject):
        # Vérifier d'abord les attributs de l'instance
        if node.attr in obj.attributes:
            return obj.attributes[node.attr]
        
        # Ensuite vérifier les méthodes de la classe
        if node.attr in obj.class_def.methods:
            method = obj.class_def.methods[node.attr]
            return VMethodClosure(method, obj)
        
        raise AttributeError(f"L'objet '{obj.class_def.name}' n'a pas d'attribut '{node.attr}'")
    
    else:
        raise TypeError(f"L'objet de type '{type(obj).__name__}' n'a pas d'attributs")

   # Évalue l'assignation à un attribut d'un objet (obj.attr = value)
def evaluate_attribute_assignment(node: PiAttributeAssignment, env: EnvFrame, evaluate_stmt_func) -> EnvValue:
    """Évalue l'assignation à un attribut d'un objet (obj.attr = value)."""
    obj = evaluate_stmt_func(node.object, env)
    value = evaluate_stmt_func(node.value, env)
    
    if isinstance(obj, VObject):
        # Assigner l'attribut à l'instance
        obj.attributes[node.attr] = value
        return value
    else:
        raise TypeError(f"Impossible d'assigner un attribut à un objet de type '{type(obj).__name__}'")

 

 # Appel de méthode sur une instance d'une classe.
# Cette fonction est appelée lors de l'appel d'une méthode sur une instance d'une classe.
def call_method(method_closure: VMethodClosure, args: list[EnvValue], evaluate_stmt_func) -> EnvValue:
    """Appelle une méthode liée à une instance."""
    method = method_closure.function
    instance = method_closure.instance
    
    # Créer un environnement pour l'appel de méthode avec 'self'
    call_env = EnvFrame(parent=method.closure_env)
    call_env.insert("self", instance)
    
    # Lier les arguments (en sautant 'self' qui est déjà lié)
    for i, arg_name in enumerate(method.funcdef.arg_names[1:]): 
        if i < len(args):
            call_env.insert(arg_name, args[i])
        else:
            raise TypeError("Argument manquant pour la méthode.")
    
    # Gérer varargs si nécessaire
    if method.funcdef.vararg:
        varargs = VList(args[len(method.funcdef.arg_names)-1:])
        call_env.insert(method.funcdef.vararg, varargs)
    elif len(args) > len(method.funcdef.arg_names) - 1:
        raise TypeError("Trop d'arguments pour la méthode.")
    
    # Exécuter la méthode
    result = VNone(value=None)
    try:
        for stmt in method.funcdef.body:
            result = evaluate_stmt_func(stmt, call_env)
    except Exception as e:
        # Vérifier si c'est une ReturnException (éviter l'import circulaire)
        if e.__class__.__name__ == 'ReturnException':
            return e.value
        else:
            raise TypeError(f"Erreur lors de l'appel de la méthode '{method.funcdef.name}': {str(e)}")
    return result
