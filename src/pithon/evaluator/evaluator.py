from pithon.evaluator.envframe import EnvFrame
from pithon.evaluator.primitive import check_type, get_primitive_dict
from pithon.syntax import (
    PiAssignment, PiBinaryOperation, PiNumber, PiBool, PiStatement, PiProgram, PiSubscript, PiVariable,
    PiIfThenElse, PiNot, PiAnd, PiOr, PiWhile, PiNone, PiList, PiTuple, PiString,
    PiFunctionDef, PiFunctionCall, PiFor, PiBreak, PiContinue, PiIn, PiReturn, PiClassDef, PiAttribute, PiAttributeAssignment, PiRaise, PiJoinedStr, PiTry, PiExceptHandler
)
from pithon.evaluator.envvalue import EnvValue, VFunctionClosure, VList, VNone, VTuple, VNumber, VBool, VString, VClassDef, VMethodClosure, VObject
from pithon.evaluator.class_evaluator import (
    evaluate_class_def, evaluate_attribute, evaluate_attribute_assignment, 
    instantiate_class, call_method
)


def initial_env() -> EnvFrame:
    """Crée et retourne l'environnement initial avec les primitives."""
    env = EnvFrame()
    env.vars.update(get_primitive_dict())
    return env

def lookup(env: EnvFrame, name: str) -> EnvValue:
    """Recherche une variable dans l'environnement."""
    return env.lookup(name)

def insert(env: EnvFrame, name: str, value: EnvValue) -> None:
    """Insère une variable dans l'environnement."""
    env.insert(name, value)

def evaluate(node: PiProgram, env: EnvFrame) -> EnvValue:
    """Évalue un programme ou une liste d'instructions."""
    if isinstance(node, list):
        last_value = VNone(value=None)
        for stmt in node:
            last_value = evaluate_stmt(stmt, env)
        return last_value
    elif isinstance(node, PiStatement):
        return evaluate_stmt(node, env)
    else:
        raise TypeError(f"Type de nœud non supporté : {type(node)}")

def evaluate_stmt(node: PiStatement, env: EnvFrame) -> EnvValue:
    """Évalue une instruction ou expression Pithon."""

    if isinstance(node, PiNumber):
        return VNumber(node.value)

    elif isinstance(node, PiBool):
        return VBool(node.value)

    elif isinstance(node, PiNone):
        return VNone(node.value)

    elif isinstance(node, PiString):
        return VString(node.value)

    elif isinstance(node, PiJoinedStr):
        # Évaluer et concaténer toutes les parties de la f-string
        result = ""
        for part in node.parts:
            part_value = evaluate_stmt(part, env)
            # Convertir en string
            if isinstance(part_value, VString):
                result += part_value.value
            elif isinstance(part_value, VNumber):
                result += str(part_value.value)
            elif isinstance(part_value, VBool):
                result += str(part_value.value)
            elif isinstance(part_value, VNone):
                result += "None"
            else:
                result += str(part_value)
        return VString(result)

    elif isinstance(node, PiList):
        elements = [evaluate_stmt(e, env) for e in node.elements]
        return VList(elements)

    elif isinstance(node, PiTuple):
        elements = tuple(evaluate_stmt(e, env) for e in node.elements)
        return VTuple(elements)

    elif isinstance(node, PiVariable):
        return lookup(env, node.name)

    elif isinstance(node, PiBinaryOperation):
        # Traite l'opération binaire comme un appel de fonction
        fct_call = PiFunctionCall(
            function=PiVariable(name=node.operator),
            args=[node.left, node.right]
        )
        return evaluate_stmt(fct_call, env)

    elif isinstance(node, PiAssignment):
        value = evaluate_stmt(node.value, env)
        insert(env, node.name, value)
        return value

    elif isinstance(node, PiIfThenElse):
        cond = evaluate_stmt(node.condition, env)
        cond = check_type(cond, VBool)
        branch = node.then_branch if cond.value else node.else_branch
        last_value = evaluate(branch, env)
        return last_value

    elif isinstance(node, PiNot):
        operand = evaluate_stmt(node.operand, env)
        # Vérifie le type pour l'opérateur 'not'
        _check_valid_piandor_type(operand)
        return VBool(not operand.value) # type: ignore

    elif isinstance(node, PiAnd):
        left = evaluate_stmt(node.left, env)
        _check_valid_piandor_type(left)
        if not left.value: # type: ignore
            return left
        right = evaluate_stmt(node.right, env)
        _check_valid_piandor_type(right)
        return right

    elif isinstance(node, PiOr):
        left = evaluate_stmt(node.left, env)
        _check_valid_piandor_type(left)
        if left.value: # type: ignore
            return left
        right = evaluate_stmt(node.right, env)
        _check_valid_piandor_type(right)
        return right

    elif isinstance(node, PiWhile):
        return _evaluate_while(node, env)

    elif isinstance(node, PiFunctionDef):
        closure = VFunctionClosure(node, env)
        insert(env, node.name, closure)
        return VNone(value=None)

    elif isinstance(node, PiReturn):
        value = evaluate_stmt(node.value, env)
        raise ReturnException(value)

    elif isinstance(node, PiFunctionCall):
        return _evaluate_function_call(node, env)

    elif isinstance(node, PiFor):
        return _evaluate_for(node, env)

    elif isinstance(node, PiBreak):
        raise BreakException()

    elif isinstance(node, PiContinue):
        raise ContinueException()

    elif isinstance(node, PiIn):
        return _evaluate_in(node, env)

    elif isinstance(node, PiSubscript):
        return _evaluate_subscript(node, env)
    
    elif isinstance(node, PiClassDef):
        return evaluate_class_def(node, env)
    
    elif isinstance(node, PiAttribute):
        return evaluate_attribute(node, env, evaluate_stmt)
    
    elif isinstance(node, PiAttributeAssignment):
        return evaluate_attribute_assignment(node, env, evaluate_stmt)

    elif isinstance(node, PiRaise):
        exception_value = evaluate_stmt(node.exception, env)
        # Pour l'instant, on lève une RuntimeError avec le message de l'exception
        if isinstance(exception_value, VObject):
            # Si c'est un objet exception, essayer de récupérer son message
            if "args" in exception_value.attributes and isinstance(exception_value.attributes["args"], VTuple):
                args = exception_value.attributes["args"].value
                if args and isinstance(args[0], VString):
                    raise PiException(exception_value.class_def.name, args[0].value, exception_value)
            raise PiException(exception_value.class_def.name, f"Exception {exception_value.class_def.name}", exception_value)
        else:
            raise PiException("RuntimeError", str(exception_value), None)

    elif isinstance(node, PiTry):
        return _evaluate_try(node, env)

    else:
        raise TypeError(f"Type de nœud non supporté : {type(node)}")

def _check_valid_piandor_type(obj):
    """Vérifie que le type est valide pour 'and'/'or'."""
    if not isinstance(obj, VBool | VNumber | VString | VNone | VList | VTuple):
        raise TypeError(f"Type non supporté pour l'opérateur 'and': {type(obj).__name__}")

def _evaluate_while(node: PiWhile, env: EnvFrame) -> EnvValue:
    """Évalue une boucle while."""
    last_value = VNone(value=None)
    while True:
        cond = evaluate_stmt(node.condition, env)
        cond = check_type(cond, VBool)
        if not cond.value:
            break
        try:
            last_value = evaluate(node.body, env)
        except BreakException:
            break
        except ContinueException:
            continue
    return last_value

def _evaluate_for(node: PiFor, env: EnvFrame) -> EnvValue:
    """Évalue une boucle for."""
    iterable_val = evaluate_stmt(node.iterable, env)
    if not isinstance(iterable_val, (VList, VTuple)):
        raise TypeError("La boucle for attend une liste ou un tuple.")
    last_value = VNone(value=None)
    iterable = iterable_val.value
    for item in iterable:
        env.insert(node.var, item)  # Pas de nouvel environnement pour la variable de boucle
        try:
            last_value = evaluate(node.body, env)
        except BreakException:
            break
        except ContinueException:
            continue
    return last_value

def _evaluate_subscript(node: PiSubscript, env: EnvFrame) -> EnvValue:
    """Évalue une opération d'indexation (subscript)."""
    collection = evaluate_stmt(node.collection, env)
    index = evaluate_stmt(node.index, env)
    # Indexation pour liste, tuple ou chaîne
    if isinstance(collection, VList):
        idx = check_type(index, VNumber)
        return collection.value[int(idx.value)]
    elif isinstance(collection, VTuple):
        idx = check_type(index, VNumber)
        return collection.value[int(idx.value)]
    elif isinstance(collection, VString):
        idx = check_type(index, VNumber)
        return VString(collection.value[int(idx.value)])
    else:
        raise TypeError("L'indexation n'est supportée que pour les listes, tuples et chaînes.")

def _evaluate_in(node: PiIn, env: EnvFrame) -> EnvValue:
    """Évalue l'opérateur 'in'."""
    container = evaluate_stmt(node.container, env)
    element = evaluate_stmt(node.element, env)
    if isinstance(container, (VList, VTuple)):
        return VBool(element in container.value)
    elif isinstance(container, VString):
        if isinstance(element, VString):
            return VBool(element.value in container.value)
        else:
            return VBool(False)
    else:
        raise TypeError("'in' n'est supporté que pour les listes et chaînes.")

def _evaluate_function_call(node: PiFunctionCall, env: EnvFrame) -> EnvValue:
    """Évalue un appel de fonction (primitive, définie par l'utilisateur, ou instantiation de classe)."""
    func_val = evaluate_stmt(node.function, env)
    args = [evaluate_stmt(arg, env) for arg in node.args]
    
    # Fonction primitive
    if callable(func_val):
        return func_val(args)
    
    # Instantiation de classe
    if isinstance(func_val, VClassDef):
        return instantiate_class(func_val, args, evaluate_stmt)
    
    # Appel de méthode liée
    if isinstance(func_val, VMethodClosure):
        return call_method(func_val, args, evaluate_stmt)
    
    # Fonction utilisateur
    if not isinstance(func_val, VFunctionClosure):
        raise TypeError("Tentative d'appel d'un objet non-fonction.")
    
    funcdef = func_val.funcdef
    closure_env = func_val.closure_env
    call_env = EnvFrame(parent=closure_env)
    
    for i, arg_name in enumerate(funcdef.arg_names):
        if i < len(args):
            call_env.insert(arg_name, args[i])
        else:
            raise TypeError("Argument manquant pour la fonction.")
    
    if funcdef.vararg:
        varargs = VList(args[len(funcdef.arg_names):])
        call_env.insert(funcdef.vararg, varargs)
    elif len(args) > len(funcdef.arg_names):
        raise TypeError("Trop d'arguments pour la fonction.")
    
    result = VNone(value=None)
    try:
        for stmt in funcdef.body:
            result = evaluate_stmt(stmt, call_env)
    except ReturnException as ret:
        return ret.value
    return result

class PiException(Exception):
    """Exception pour gérer les exceptions Pithon."""
    def __init__(self, exception_type: str, message: str, exception_object):
        self.exception_type = exception_type
        self.message = message
        self.exception_object = exception_object
        super().__init__(message)

def _evaluate_try(node: PiTry, env: EnvFrame) -> EnvValue:
    """Évalue un bloc try/except."""
    result = VNone(value=None)
    
    try:
        # Exécuter le bloc try
        for stmt in node.body:
            result = evaluate_stmt(stmt, env)
    except PiException as e:
        # Gérer les exceptions Pithon
        handled = False
        for handler in node.handlers:
            if handler.exception_type is None:
                # Gestionnaire générique (except:)
                handled = True
            else:
                # Vérifier si le type d'exception correspond
                handler_type = evaluate_stmt(handler.exception_type, env)
                if isinstance(handler_type, VClassDef) and handler_type.name == e.exception_type:
                    handled = True
                elif callable(handler_type) and hasattr(handler_type, '__name__') and handler_type.__name__ == e.exception_type:
                    handled = True
            
            if handled:
                # Créer un nouvel environnement pour le gestionnaire
                handler_env = EnvFrame(parent=env)
                
                # Lier la variable d'exception si spécifiée
                if handler.name and e.exception_object:
                    handler_env.insert(handler.name, e.exception_object)
                
                # Exécuter le gestionnaire
                for stmt in handler.body:
                    result = evaluate_stmt(stmt, handler_env)
                break
        
        if not handled:
            # Re-lever l'exception si elle n'est pas gérée
            raise
    
    return result

class ReturnException(Exception):
    """Exception pour retourner une valeur depuis une fonction."""
    def __init__(self, value):
        self.value = value

class BreakException(Exception):
    """Exception pour sortir d'une boucle (break)."""
    pass

class ContinueException(Exception):
    """Exception pour passer à l'itération suivante (continue)."""
    pass
