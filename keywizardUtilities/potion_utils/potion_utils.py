from typing import Union, Tuple, List
import ctypes, numpy, os
class PotionMotion:
    library_name = os.path.join(os.path.dirname(__file__), "potion_utils.dll")
    library = ctypes.cdll.LoadLibrary(library_name)
    library.find_optimal_move.argtypes = [  
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p  
    ]
    BOARD_ROWS = 6
    BOARD_COLS = 7
    @classmethod
    def find_optimal_move(class_, target_board : numpy.ndarray) -> Tuple[ int ]:
        target_board = numpy.int32(target_board)
        (sr, sc, er, ec) = (
            (ctypes.c_int32 * 1)(),
            (ctypes.c_int32 * 1)(),
            (ctypes.c_int32 * 1)(),
            (ctypes.c_int32 * 1)()
        )
        class_.library.find_optimal_move(sr, sc, er, ec, target_board.ctypes.data)
        return (
            list(sr)[0],
            list(sc)[0],
            list(er)[0],
            list(ec)[0]
        )
if (__name__ == "__main__"):
    board = numpy.int32([
        [  0, 0, 1, 1, 2, 2, 3  ],
        [  3, 3, 2, 2, 1, 1, 3  ],
        [  0, 0, 1, 4, 2, 2, 4  ],
        [  1, 0, 3, 1, 2, 2, 3  ],
        [  0, 1, 1, 2, 1, 1, 2  ],
        [  1, 0, 2, 3, 3, 2, 3  ]
    ])
    result = (sr, sc, er, ec) = PotionMotion.find_optimal_move(board)
    print(result)