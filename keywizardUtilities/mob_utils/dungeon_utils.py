from typing import Callable, Union, Tuple, List
import pynput, numpy, time, cv2
class DungeonUtils:
    
    __SLEEP_QUANTUM = 0.1
    
    @staticmethod
    def move_mouse(start_coordinate : Tuple[ int ], end_coordinate : Tuple[ int ], interval : Union[ float, int ]) -> None:
        offset = (
            end_coordinate[0] - start_coordinate[0],
            end_coordinate[1] - start_coordinate[1]
        )
        
        quantum = 0.01
        
        units = int(interval / quantum)
        
        offset_unit = (
            offset[0] / units,
            offset[1] / units
        )
        
        for unit in range(units):
            cur_coordinate = (
                start_coordinate[0] + int(offset_unit[0] * unit),
                start_coordinate[1] + int(offset_unit[1] * unit)
            )
            pynput.mouse.Controller().position = cur_coordinate 
            time.sleep(quantum)
            
    @classmethod 
    def enter_dungeon(class_, stop_waiting : Callable) -> None:
        pynput.keyboard.Controller().press("x")
        time.sleep(0.15)
        pynput.keyboard.Controller().release("x")
        while not (stop_waiting()):
            time.sleep(class_.__SLEEP_QUANTUM)
            
    @classmethod
    def enter_battle(class_, stop_running : Callable) -> None:
        pynput.keyboard.Controller().press("w")
        while not (stop_running()):
            time.sleep(class_.__SLEEP_QUANTUM)
        pynput.keyboard.Controller().release("w")
    
class HalfangUtils(DungeonUtils):
    
    __TURN_MOUSE_OFFSET = (-4, 0)    
    
    @classmethod
    def exit_halfang(class_, start_coordinate : Tuple[ int ], stop_exiting : Callable) -> None:
        offset = class_.__TURN_MOUSE_OFFSET
        pynput.mouse.Controller().position = start_coordinate
        pynput.mouse.Controller().press(pynput.mouse.Button.right)
        class_.move_mouse(
            start_coordinate, 
            (
                start_coordinate[0] + offset[0],
                start_coordinate[1] + offset[1]
            ),
            interval = 2
        )
        pynput.mouse.Controller().release(pynput.mouse.Button.right)
        class_.enter_battle(stop_exiting)
        
    @classmethod
    def exit_halfang_2(class_, stop_exiting : Callable) -> None:
        pynput.keyboard.Controller().press("a")
        time.sleep(0.68)
        pynput.keyboard.Controller().release("a")
        class_.enter_battle(stop_exiting)
                
if (__name__ == "__main__"):
    
    time.sleep(5)
    
    HalfangUtils.exit_halfang(start_coordinate = (400, 300))