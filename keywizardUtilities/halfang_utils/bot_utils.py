from typing import Tuple, List, Type 
import ctypes, os

class BotUtils:
        
    library_name = os.path.join(os.path.dirname(__file__), "bot_utils.dll")
    
    library      = ctypes.cdll.LoadLibrary(library_name)
    
    library.determine_moves.argtypes = [  
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int32, ctypes.c_int32  ]
    
    library.determine_moves.restype  = ctypes.c_int32 
    
    @classmethod 
    def initialize_library(class_) -> Type[ "BotUtils" ]:
        class_.library.initialize_library()
        return class_ 
    
    @classmethod 
    def determine_moves(class_, card_list : List[ int ], should_heal : int) -> Tuple[ int, Tuple[ int ] ]:
        if not (isinstance(should_heal, int)):
            should_heal = int(should_heal)
        __card_list = (ctypes.c_int32 * len(card_list))(*card_list)
        first_card  = (ctypes.c_int32 * 1)(-1)
        second_card = (ctypes.c_int32 * 1)(-1)
        action_type = class_.library.determine_moves(
            first_card, second_card, __card_list, card_list.__len__(), should_heal)
        return (int(action_type), (int(list(first_card)[0]), int(list(second_card)[0])))
    
if (__name__ == "__main__"):
    
    n = 1
    
    if (n == 1):
        
        BotUtils.initialize_library()
        
        card_list   = [  0, 1, 0, 2, 3, 3, 1  ]
        
        should_heal = 0
        
        result      = BotUtils.determine_moves(card_list, should_heal)
        
        print(result)