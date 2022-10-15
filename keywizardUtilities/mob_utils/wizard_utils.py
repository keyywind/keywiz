from typing import Iterator, Callable, Union, Tuple, List
from pyautogui import screenshot as py_screenshot
import datetime, pynput, numpy, time, math, sys, cv2
class WizardUtils:
    
    @staticmethod
    def take_screenshot(resize_ratio : Union[ float, int ] = 1, color_mode : int = cv2.COLOR_RGB2BGR) -> numpy.ndarray:
        
        screenshot = cv2.cvtColor(numpy.uint8(py_screenshot()), color_mode)
        return ((screenshot) if (resize_ratio == 1) else (cv2.resize(screenshot, None, None, fx = resize_ratio, fy = resize_ratio)))
    
    """
    @staticmethod
    def execute_at_interval(function : Callable, execute_interval : Union[ float, int ], * args, ** kwargs) -> None:
        
        while True:
            function(*args, **kwargs)
            time.sleep(execute_interval)
    """
    
    @staticmethod
    def crop_image(source_image : numpy.ndarray, start_point : Tuple[ int ], dimension : Tuple[ int ]) -> numpy.ndarray:
        
        """
            start_point : FORMAT[ (x, y, *_) ]
            dimension   : FORMAT[ (w, h, *_) ]
        """
        
        (x, y, w, h) = (*start_point[ 0:2 ], *dimension[ 0:2 ])
        
        return source_image[  y : y + h, x : x + w  ]
    
    @classmethod
    def take_regional_screenshot(class_, bounding_box : Tuple[        int ], 
                                         resize_ratio : Union[ float, int ] = 1, 
                                         color_mode   : int                 = cv2.COLOR_RGB2BGR) -> numpy.ndarray:
        
        return class_.crop_image(
            class_.take_screenshot(resize_ratio, color_mode), bounding_box[ 0:2 ], bounding_box[ 2:4 ])
    
    @staticmethod
    def fetch_relative_bounding_box(configuration : dict, target_key : str) -> Tuple[ int ]:
        
        relative_bounding_box = (x, y, w, h) = (
            configuration[target_key]["coord"][0],
            configuration[target_key]["coord"][1],
            configuration[target_key]["size"][0],
            configuration[target_key]["size"][1]
        )
        
        return relative_bounding_box
    
    @classmethod
    def fetch_absolute_bounding_box(class_, configuration : dict, target_key : Union[ str, Tuple[ int ] ], C0H1M2 : int = 0) -> Tuple[ int ]:
        
        """
            CASE isinstance(target_key, str) :
                CASE target_key == "window"
                CASE target_key == "book"
                CASE target_key == "pass"
                CASE target_key == "deck"
                CASE target_key == "orbs"
                CASE target_key == "health_panel"
                CASE target_key == "mana_panel"
                
            CASE isinstance(target_key, tuple) and (C0H1M2 == 0) : # card
                CASE target_key == (card_quantity : int, card_number : int)
                
            CASE isinstance(target_key, tuple) and (C0H1M2 == 1) : # health
                CASE target_key == (digit_quantity : int, digit_number : int)
                
            CASE isinstance(target_key, tuple) and (C0H1M2 == 2) : # mana
                CASE target_key == (digit_quantity : int, digit_number : int)    
                
        """
        
        window_bounding_box = class_.fetch_relative_bounding_box(configuration, "window")
        
        if (isinstance(target_key, str)):
        
            if (target_key == "window"):
                return window_bounding_box
            
            relative_bounding_box = class_.fetch_relative_bounding_box(configuration, target_key)
            
            if (target_key in [ "book", "pass", "deck", "orbs" ]):
                return (
                    window_bounding_box[0] + relative_bounding_box[0],
                    window_bounding_box[1] + relative_bounding_box[1],
                    relative_bounding_box[2],
                    relative_bounding_box[3]
                )
            
            elif (target_key in [ "health_panel", "mana_panel" ]):
                
                orbs_bounding_box = class_.fetch_relative_bounding_box(configuration, "orbs")
                
                return (
                    window_bounding_box[0] + orbs_bounding_box[0] + relative_bounding_box[0],
                    window_bounding_box[1] + orbs_bounding_box[1] + relative_bounding_box[1],
                    relative_bounding_box[2],
                    relative_bounding_box[3]
                )
            
            raise Exception("KeyError : \"{}\" is not a valid key.\n".format(target_key))
            
        if (C0H1M2 == 0):
            
            if (  any( isinstance(target_key, __type) for __type in [  tuple, list, numpy.ndarray  ] ) and (target_key.__len__() >= 2)  ):
                    
                deck_bounding_box = class_.fetch_relative_bounding_box(configuration, "deck")
                
                panel_bounding_box = class_.fetch_relative_bounding_box(configuration, "panel")
                
                card_quantity, card_number = target_key[ 0:2 ]
                
                card_bounding_box = (
                    *configuration["panel"]["slot"][ card_quantity - 1 ][ card_number - 1 ],
                    *configuration["card"]["size"]
                )
                
                return (
                    window_bounding_box[0] + deck_bounding_box[0] + panel_bounding_box[0] + card_bounding_box[0],
                    window_bounding_box[1] + deck_bounding_box[1] + panel_bounding_box[1] + card_bounding_box[1],
                    card_bounding_box[2],
                    card_bounding_box[3]
                )
            
        elif (C0H1M2 == 1):
            
            if (  any( isinstance(target_key, __type) for __type in [  tuple, list, numpy.ndarray  ] ) and (target_key.__len__() >= 2)  ):
                    
                orbs_bounding_box = class_.fetch_relative_bounding_box(configuration, "orbs")
                
                health_panel_bounding_box       = class_.fetch_relative_bounding_box(configuration, "health_panel")
                                
                health_digit_panel_bounding_box = class_.fetch_relative_bounding_box(configuration, "health_digit_panel")
                
                digit_quantity, digit_number    = target_key[ 0:2 ]
                
                digit_bounding_box = (
                    *configuration["health_digit_panel"]["slot"][ digit_quantity - 1 ][ digit_number - 1 ],
                    *configuration["digit"]["size"]
                )
                
                return (
                    window_bounding_box[0] + orbs_bounding_box[0] + health_panel_bounding_box[0] + health_digit_panel_bounding_box[0] + digit_bounding_box[0],
                    window_bounding_box[1] + orbs_bounding_box[1] + health_panel_bounding_box[1] + health_digit_panel_bounding_box[1] + digit_bounding_box[1],
                    digit_bounding_box[2],
                    digit_bounding_box[3]
                )
            
        elif (C0H1M2 == 2):
            
            if (  any( isinstance(target_key, __type) for __type in [  tuple, list, numpy.ndarray  ] ) and (target_key.__len__() >= 2)  ):
                    
                orbs_bounding_box = class_.fetch_relative_bounding_box(configuration, "orbs")
                
                mana_panel_bounding_box       = class_.fetch_relative_bounding_box(configuration, "mana_panel")
                
                mana_digit_panel_bounding_box = class_.fetch_relative_bounding_box(configuration, "mana_digit_panel")
                
                digit_quantity, digit_number  = target_key[ 0:2 ]
                
                digit_bounding_box = (
                    *configuration["mana_digit_panel"]["slot"][ digit_quantity - 1 ][ digit_number - 1 ],
                    *configuration["digit"]["size"]
                )
                
                return (
                    window_bounding_box[0] + orbs_bounding_box[0] + mana_panel_bounding_box[0] + mana_digit_panel_bounding_box[0] + digit_bounding_box[0],
                    window_bounding_box[1] + orbs_bounding_box[1] + mana_panel_bounding_box[1] + mana_digit_panel_bounding_box[1] + digit_bounding_box[1],
                    digit_bounding_box[2],
                    digit_bounding_box[3]
                )
        
        raise Exception("KeyError : \"{}\" must be of type [ tuple, list or numpy.ndarray ] and contains at least 2 integers.\n")
        
    @classmethod
    def fetch_card_coordinates(class_, configuration : dict) -> List[ List[ Tuple[ int ] ] ]:
                
        coordinates = []
        
        for card_quantity in range(1, 8):
            row_list = []
            for card_number in range(1, card_quantity + 1):
                row_list.append(class_.fetch_absolute_bounding_box(configuration, (card_quantity, card_number)))
            coordinates.append(row_list)
            
        return coordinates
    
    @classmethod
    def fetch_number_coordinates(class_, configuration : dict) -> Tuple[  List[ List[ Tuple[int] ] ], List[ List[ Tuple[int] ] ]  ]:
        
        health_coordinates = [];  mana_coordinates = []
        
        for digit_quantity in range(1, 5):
            row_list = []
            for digit_number in range(1, digit_quantity + 1):
                row_list.append(class_.fetch_absolute_bounding_box(configuration, (digit_quantity, digit_number), C0H1M2 = 1))
            health_coordinates.append(row_list)
            
        for digit_quantity in range(1, 4):
            row_list = []
            for digit_number in range(1, digit_quantity + 1):
                row_list.append(class_.fetch_absolute_bounding_box(configuration, (digit_quantity, digit_number), C0H1M2 = 2))
            mana_coordinates.append(row_list)
            
        return (health_coordinates, mana_coordinates)
    
    @staticmethod
    def move_mouse(end_point : Tuple[ int ], time_interval : Union[ float, int ]) -> Tuple[ int ]:
        
        start_point = pynput.mouse.Controller().position
        
        quantum = 0.05
        
        steps = math.ceil(time_interval / quantum)
        
        offset = (end_point[0] - start_point[0], end_point[1] - start_point[1])
        
        offset = (offset[0] / steps, offset[1] / steps)
                
        for i in range(steps + 1):
            
            cur_point = (
                start_point[0] + offset[0] * i,
                start_point[1] + offset[1] * i
            )
            
            pynput.mouse.Controller().position = cur_point
            
            time.sleep(quantum)
            
        return start_point
            
    @staticmethod
    def click_mouse(hold_time : Union[ float, int ]) -> Tuple[ int ]:
        
        cur_position = pynput.mouse.Controller().position
        
        pynput.mouse.Controller().position = cur_position
        
        pynput.mouse.Controller().press(pynput.mouse.Button.left)
        
        time.sleep(hold_time)
        
        pynput.mouse.Controller().position = cur_position
        
        pynput.mouse.Controller().release(pynput.mouse.Button.left)
        
        return cur_position
    
    @staticmethod
    def bounding_box_centroid(bounding_box : Tuple[ int ]) -> Tuple[ int ]:
        
        return (bounding_box[0] + bounding_box[2] // 2, bounding_box[1] + bounding_box[3] // 2)
    
    @classmethod
    def click_card(class_, card_bounding_box : List[ List[ Tuple[ int ] ] ], card_quantity : int, card_number : int, move_time : Union[ float, int ] = 0.75) -> None:
        
        bounding_box = card_bounding_box[ card_quantity - 1 ][ card_number - 1 ]
        
        card_centroid = class_.bounding_box_centroid(bounding_box)
        
        class_.move_mouse(class_.point_by_offset(card_centroid, (5, 5)), move_time)
        
        class_.click_mouse(hold_time = 0.25)
        
    @staticmethod
    def sleep(sleep_time : Union[ float, int ]) -> None:
        
        start_of_time = datetime.datetime.now()
        
        while ((datetime.datetime.now() - start_of_time).total_seconds() <= sleep_time):
            
            time.sleep(0.01)
        
    @staticmethod 
    def pad_string(string : str, min_length : int, pad_string : str = ' ') -> str:
        
        string_length = string.__len__()
        
        return string + pad_string * (min_length - string_length) 
    
    @staticmethod
    def point_by_offset(target_point : Tuple[ int ], offset_range : Tuple[ int ]) -> Tuple[ int ]:
        
        return (
            target_point[0] + int(numpy.random.randint(-offset_range[0], offset_range[0])),
            target_point[1] + int(numpy.random.randint(-offset_range[1], offset_range[1]))
        )
    
    @classmethod
    def countdown(class_, message : str = "Starting in {} seconds", countdown_time : Union[ float, int ] = 3) -> None:
        
        #start_of_time = datetime.datetime.now()
        
        while True:
            
            sys.stdout.write("\r" + class_.pad_string(message.format(countdown_time), 30))
            sys.stdout.flush()
            
            countdown_time -= 1
            class_.sleep(1)
            if (countdown_time == 0):
                break
        
        print("\n")
            
                    
if (__name__ == "__main__"):
    pass
    
    #end_point = (1980, 1080)
    
    #WizardUtils.move_mouse(end_point, 1)
    
    #WizardUtils.click_mouse(0.3)
    
    #pynput.mouse.Controller().position = end_point



        