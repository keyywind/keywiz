from typing import Union, Tuple, List, Type
import pyautogui, datetime, numpy, json, time, cv2, sys, os

from keywizardUtilities.potion_utils.potion_utils import PotionMotion

from keyio.keyutils import KeyUtils 
from keyio.mouseutils import MouseUtils 
from keyio.windowutils import WindowUtils 


__key_controller = KeyUtils()

__mouse_controller = MouseUtils()

__window_controller = WindowUtils()


def bounding_box_centroid(bounding_box : Tuple[ int ]) -> Tuple[ int ]:
    return (bounding_box[0] + bounding_box[2] // 2, bounding_box[1] + bounding_box[3] // 2)


def scroll(grid_coord   :             Tuple[ int ], 
           bottle_slots : List[ List[ Tuple[ int ] ] ], 
           bottle_size  :             Tuple[ int ], 
           action       :             Tuple[ int ], 
           idle_coord   :             Tuple[ int ]     = (0, 0)) -> None:
    global __mouse_controller 
    
    first_coord = (
        grid_coord[0] + bottle_slots[action[0]][action[1]][0],    
        grid_coord[1] + bottle_slots[action[0]][action[1]][1], 
        bottle_size[0],
        bottle_size[1]
    )
    second_coord = (
        grid_coord[0] + bottle_slots[action[2]][action[3]][0], 
        grid_coord[1] + bottle_slots[action[2]][action[3]][1],     
        bottle_size[0],
        bottle_size[1]
    )
    __mouse_controller.set_mouse_coord(first_coord[0] - 5, first_coord[1])
    time.sleep(0.05)
    __mouse_controller.set_mouse_coord(*first_coord[0:2])
    __mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
    second_coord = bounding_box_centroid(second_coord)
    first_coord  = bounding_box_centroid(first_coord)
    ( x,  y) = first_coord[0:2]
    (cx, cy) = first_coord[0:2]
    (dx, dy) = (second_coord[0] - first_coord[0], second_coord[1] - first_coord[1])
    for i in range(21):
        (cx, cy) = (x + dx * i / 20, y + dy * i / 20)
        __mouse_controller.set_mouse_coord(cx, cy)
        time.sleep(0.03)
    __mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
    time.sleep(0.1)
    __mouse_controller.set_mouse_coord(*idle_coord)


class PotionMotionPlayer:
    
    POTION_SIZE = (55, 55)
    
    POTION_GRID = {
        "size"  : (380, 330),
        "coord" : (220, 180),
        "slot"  : [    9,  60, 112, 163, 215, 265, 317  ]
    }
    
    POTION_PREDICTOR_MODEL_NAME = os.path.join(os.path.join(os.path.dirname(__file__), "keywizardModel"), "potion_predictor.pb")
    
    POTION_RECOGNIZER = None
    
    GRID_ROWS = 6
    
    GRID_COLS = 7
    
    CONFIGURE_WINDOW_NAME = "Configure"
    
    CONFIGURE_WINDOW_RESIZE_RATIO = 0.5
    
    CONFIGURE_FILE = "./potion_motion_configure.txt"
    
    CONFIGURE_FILE = os.path.join(os.path.join(os.path.dirname(__file__), "keywizardConfig"), "potion_config.json")
    
    EXIT_BUTTON = {
        "coord" : (452, 350),
        "size"  : ( 45,  45)
    }
    
    CONTINUE_BUTTON = {
        "coord" : (135,  78),
        "size"  : (110,  40)
    }
    
    START_BUTTON = {
        "coord" : (135, 350),
        "size"  : (110,  40)
    }
    
    BOTTLE_RED         = 0
    BOTTLE_ORANGE      = 1
    BOTTLE_YELLOW      = 2
    BOTTLE_GREEN_LIGHT = 3
    BOTTLE_GREEN_DARK  = 4
    BOTTLE_BLUE_LIGHT  = 5
    BOTTLE_BLUE_DARK   = 6
    BOTTLE_PURPLE      = 7
    BOTTLE_PINK        = 8
    BOTTLE_BROWN       = 9
    
    player_settings    = {
        "constants" : {
            "num_games" : 1    
        }
    }
    
    @classmethod
    def _initialize_grid(class_) -> Type[ "PotionMotionPlayer" ]:
        potion_grid = [  [  (0, 0) for _ in range(class_.GRID_COLS)  ] for _ in range(class_.GRID_ROWS)  ]
        for row_index in range(class_.GRID_ROWS):
            for col_index in range(class_.GRID_COLS):
                potion_grid[row_index][col_index] = (
                    class_.POTION_GRID["slot"][col_index], 
                    class_.POTION_GRID["slot"][row_index]
                )
        class_.POTION_GRID["slot"] = potion_grid
        return class_ 
    
    @classmethod
    def _initialize_predictor(class_) -> Type[ "PotionMotionPlayer" ]:
        class_.POTION_RECOGNIZER = cv2.dnn.readNetFromTensorflow(
            class_.POTION_PREDICTOR_MODEL_NAME)
        return class_ 
    
    @classmethod
    def save_configuration(class_) -> Type[ "PotionMotionPlayer" ]:
        with open(class_.CONFIGURE_FILE, "w") as write_file:
            write_file.write(json.dumps(class_.player_settings, indent = 4))
        """
        with open(class_.CONFIGURE_FILE, 'w') as write_file:
            write_file.write("{}\n".format(class_.POTION_GRID["coord"][0]))
            write_file.write("{}\n".format(class_.POTION_GRID["coord"][1]))
        """
        return class_
    
    @classmethod 
    def initialize(class_) -> Type[ "PotionMotionPlayer" ]:
        def parse() -> None:
            if (os.path.isfile(class_.CONFIGURE_FILE)):
                """
                with open(class_.CONFIGURE_FILE, 'r') as read_file:
                    new_coord = (
                        int(read_file.readline()),
                        int(read_file.readline())
                    )
                    class_.POTION_GRID["coord"] = new_coord
                """
                with open(class_.CONFIGURE_FILE, "r") as read_file:
                    class_.player_settings = json.loads(read_file.read())
            else:
                class_.save_configuration()
        parse()
        return class_._initialize_grid()._initialize_predictor()
    
    @classmethod
    def _classify_bottles(class_, bottle_images : Union[ List[ numpy.ndarray ], numpy.ndarray ]) -> numpy.ndarray:
        bottle_classifier = class_.POTION_RECOGNIZER
        
        def predict_blob(blob_image : numpy.ndarray) -> numpy.ndarray:
            nonlocal bottle_classifier 
            bottle_classifier.setInput(blob_image)
            return bottle_classifier.forward()
        
        def decode(one_hot_encoding : numpy.ndarray) -> int:
            return int(numpy.argmax(one_hot_encoding))
        
        blob_list = [
            cv2.dnn.blobFromImage(__image, 1.0, class_.POTION_SIZE)
                for __image in numpy.float32(bottle_images) / 255.0
        ]
        return numpy.stack([
            decode(predict_blob(__image))
                for __image in blob_list
        ])
    
    @classmethod 
    def _bottles2matrix(class_, bottle_images : Union[ List[ numpy.ndarray ], numpy.ndarray ]) -> numpy.ndarray:
        
        # bottle_images : (6, 7, 55, 55, 3)
        
        return numpy.int32(class_._classify_bottles(bottle_images).reshape(class_.GRID_ROWS, class_.GRID_COLS))
    
    @classmethod
    def _take_screenshot(class_) -> numpy.ndarray:
        return cv2.cvtColor(numpy.uint8(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
    
    @classmethod
    def _crop_bottles(class_, full_screenshot : numpy.ndarray) -> numpy.ndarray:
        (x, y, w, h)    = (*class_.POTION_GRID["coord"], *class_.POTION_GRID["size"])
        grid_screenshot = full_screenshot[ y : y + h, x : x + w ]
        bottle_images   = []
        for row_index in range(class_.GRID_ROWS):
            for col_index in range(class_.GRID_COLS):
                (_x, _y) = class_.POTION_GRID["slot"][row_index][col_index]
                bottle_images.append(grid_screenshot[  _y : _y + class_.POTION_SIZE[1], _x : _x + class_.POTION_SIZE[0]  ])
        return numpy.stack(bottle_images)
    
    @classmethod
    def screenshot2matrix(class_, full_screenshot : numpy.ndarray) -> numpy.ndarray:
        return class_._bottles2matrix(class_._crop_bottles(full_screenshot))
    
    @classmethod
    def test_grid_coord(class_, screenshot : numpy.ndarray, grid_coord : Tuple[ int ]) -> numpy.ndarray:
        (x, y, w, h)   = (*grid_coord, *class_.POTION_GRID["size"])
        (_w, _h) = class_.POTION_SIZE
        mask     = numpy.copy(screenshot)
        for row_index in range(class_.GRID_ROWS):
            for col_index in range(class_.GRID_COLS):
                (_x, _y) = class_.POTION_GRID["slot"][row_index][col_index]
                (_x, _y) = (_x + x, _y + y)
                mask = cv2.rectangle(mask, (_x, _y), (_x + _w, _y + _h), (0, 0, 255), 2)
        mask = cv2.rectangle(mask, (x, y), (x + w, y + h), (0, 0, 255), 5)
        E    = (*class_.EXIT_BUTTON["coord"], *class_.EXIT_BUTTON["size"])
        mask = cv2.rectangle(mask, (E[0] + x, E[1] + y), (E[0] + E[2] + x, E[1] + E[3] + y), (0, 255, 0), 1)
        C    = (*class_.CONTINUE_BUTTON["coord"], *class_.CONTINUE_BUTTON["size"])
        mask = cv2.rectangle(mask, (C[0] + x, C[1] + y), (C[0] + C[2] + x, C[1] + C[3] + y), (0, 255, 0), 1)
        S    = (*class_.START_BUTTON["coord"], *class_.START_BUTTON["size"])
        mask = cv2.rectangle(mask, (S[0] + x, S[1] + y), (S[0] + S[2] + x, S[1] + S[3] + y), (0, 255, 0), 1)
        return mask 
    
    @classmethod 
    def configure_grid_coord(class_) -> Tuple[ int ]:
        def mouse_callback(event : int, x : int, y : int, * args, ** kwargs):
            nonlocal should_save, cur_x, cur_y
            if (event == cv2.EVENT_LBUTTONDOWN):
                should_save = True
            elif ((not should_save) and (event == cv2.EVENT_MOUSEMOVE)):
                (cur_x, cur_y) = (
                    int(x / class_.CONFIGURE_WINDOW_RESIZE_RATIO), 
                    int(y / class_.CONFIGURE_WINDOW_RESIZE_RATIO)
                )
        should_save = False
        terminate   = False
        cur_x       = 0
        cur_y       = 0
        cv2.namedWindow(class_.CONFIGURE_WINDOW_NAME)
        cv2.setMouseCallback(class_.CONFIGURE_WINDOW_NAME, mouse_callback)
        
        while not (terminate):
            
            screenshot = class_._take_screenshot()
            mask       = class_.test_grid_coord(screenshot, (cur_x, cur_y))
            mask       = cv2.resize(mask, None, None, 
                fx = class_.CONFIGURE_WINDOW_RESIZE_RATIO, 
                fy = class_.CONFIGURE_WINDOW_RESIZE_RATIO
            )
            
            cv2.imshow(class_.CONFIGURE_WINDOW_NAME, mask)
            
            wait_key   = cv2.waitKey(1)
            if (wait_key == 27):
                terminate   = True 
            elif (wait_key == ord('r')):
                should_save = False
                
        cv2.destroyWindow(class_.CONFIGURE_WINDOW_NAME)
        return (cur_x, cur_y)
    
    @classmethod
    def display_configuration(class_) -> Type[ "PotionMotionPlayer" ]:
        
        (cur_x, cur_y) = class_.POTION_GRID["coord"]
        
        while True:
            
            screenshot = class_._take_screenshot()
            mask       = class_.test_grid_coord(screenshot, (cur_x, cur_y))
            mask       = cv2.resize(mask, None, None, 
                fx = class_.CONFIGURE_WINDOW_RESIZE_RATIO, 
                fy = class_.CONFIGURE_WINDOW_RESIZE_RATIO
            )
            
            cv2.imshow(class_.CONFIGURE_WINDOW_NAME, mask)
            
            wait_key   = cv2.waitKey(1)
            
            if (wait_key == 27):
                break
                
        cv2.destroyWindow(class_.CONFIGURE_WINDOW_NAME)
        
        return class_
    
def pad_length(string : str, length : int) -> str:
    str_len = len(string)
    return string + " " * (length - str_len)
    
def countdown(duration : Union[ int, float ], padding_len : int = 50) -> None:
    DT = datetime.datetime 
    SOT = DT.now()
    while True:
        elapsed = (DT.now() - SOT).total_seconds()
        if (elapsed >= duration):
            break 
        remaining_secs = int(numpy.ceil((duration - elapsed)))
        sys.stdout.write(pad_length("\r[ Starting in {} seconds ]".format(remaining_secs), padding_len))
        sys.stdout.flush()
        time.sleep(0.05)
    sys.stdout.write(pad_length("\r[ Bot Initiated ]", padding_len))
    sys.stdout.flush()
    print("\n")
    
def execute_bot(terminate_bottle : int = -1, game_rounds : int = 1) -> None:
    global __mouse_controller     
    
    if (game_rounds == -1):
        game_rounds = PotionMotionPlayer.player_settings["constants"]["num_games"]
    
    def click_coord(coord : Tuple[ int ]) -> None:
        
        start_coord = (coord[0] - 20, coord[1])

        (x, y)      = start_coord[0:2]
        
        (cx, cy)    = start_coord[0:2]
        
        (dx, dy)    = (coord[0] - x, coord[1] - y)
        
        __mouse_controller.set_mouse_coord(*start_coord)
        
        for i in range(21):
            
            (cx, cy) = (x + dx * (i / 20), y + dy * (i / 20))
            
            __mouse_controller.set_mouse_coord(cx, cy)
            
            time.sleep(0.03)
            
        __mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
        
        time.sleep(0.3)
        
        __mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
    
    countdown(duration = 3)
    
    time.sleep(3)
          
    for _ in range(game_rounds):
            
        time.sleep(2)
        
        begin_coord  = (*PotionMotionPlayer.START_BUTTON["coord"], *PotionMotionPlayer.START_BUTTON["size"])
        
        begin_coord  = (
            PotionMotionPlayer.POTION_GRID["coord"][0] + begin_coord[0],
            PotionMotionPlayer.POTION_GRID["coord"][1] + begin_coord[1],
            *begin_coord[2:4]    
        )
        
        begin_coord     = bounding_box_centroid(begin_coord)
        
        click_coord(begin_coord)
        
        time.sleep(1)
        
        keep_running = 1
    
        key_controller = KeyUtils()
        
        @key_controller.monitor(KeyUtils.Key.KEY_F10)
        def monitor_terminate(key_code : int, key_pressed : bool) -> None:
            nonlocal keep_running
            if (key_pressed):
                keep_running = 0
                
        key_controller.initialize_monitors()
        
        key_controller.start_thread()
        
        while (keep_running == 1):
    
            matrix = PotionMotionPlayer.screenshot2matrix(PotionMotionPlayer._take_screenshot())
            
            if (numpy.any(matrix == terminate_bottle)):
                keep_running = -1
            
            next_move = PotionMotion.find_optimal_move(matrix)
            
            scroll(
                PotionMotionPlayer.POTION_GRID["coord"], 
                PotionMotionPlayer.POTION_GRID["slot"], 
                PotionMotionPlayer.POTION_SIZE, 
                next_move
            )
            
            time.sleep(0.75)
            
        key_controller.stop_thread()
            
        if (keep_running == 0):
            return
        
        exit_coord     = (*PotionMotionPlayer.EXIT_BUTTON["coord"], *PotionMotionPlayer.EXIT_BUTTON["size"])
        
        exit_coord     = (
            PotionMotionPlayer.POTION_GRID["coord"][0] + exit_coord[0],
            PotionMotionPlayer.POTION_GRID["coord"][1] + exit_coord[1],
            *exit_coord[2:4]    
        )
        
        exit_coord     = bounding_box_centroid(exit_coord)
        
        click_coord(exit_coord)
        
        time.sleep(10)
        
        continue_coord = (
            *PotionMotionPlayer.CONTINUE_BUTTON["coord"], *PotionMotionPlayer.CONTINUE_BUTTON["size"])
        
        continue_coord = (
            PotionMotionPlayer.POTION_GRID["coord"][0] + continue_coord[0],
            PotionMotionPlayer.POTION_GRID["coord"][1] + continue_coord[1],
            *continue_coord[2:4]    
        )
        
        continue_coord = bounding_box_centroid(continue_coord)
        
        click_coord(continue_coord)
    
    time.sleep(4)
    
    click_coord(exit_coord)
        
def main():
    
    while True:
        print("Potion Motion Game")
        print("[ P ] Play")
        print("[ C ] Configure")
        print("[ D ] Display Configuration")
        print("[ S ] Save")
        print("[ E ] Exit")    
        print("")
        user_input = input("> ").lower()
        if (user_input.startswith('p')):
            execute_bot(terminate_bottle = PotionMotionPlayer.BOTTLE_PINK, game_rounds = 2)
        elif (user_input.startswith('c')):
            PotionMotionPlayer.configure_grid_coord()
        elif (user_input.startswith('d')):
            PotionMotionPlayer.display_configuration()
        elif (user_input.startswith('s')):
              PotionMotionPlayer.save_configuration()
        elif (user_input.startswith('e')):
            return     
        
def main2():
    global __key_controller, __window_controller, PotionMotionPlayer 
    os.system("title Keywizard - Potion Motion")
    os.system("mode 100")
    os.system("color 1f")
    os.system("cls")
    print("")
    sys.stdout.write(pad_length("\r[ Press F8 to confirm selected window ]", 50))
    sys.stdout.flush()
    keep_running = True 
    @__key_controller.monitor(KeyUtils.Key.KEY_F8)
    def monitor_exit(key_code : int, key_pressed : bool) -> None:
        nonlocal keep_running
        if (key_pressed):
            (sx, sy, ex, ey) = __window_controller.get_foreground_window()
            PotionMotionPlayer.POTION_GRID["coord"] = (sx + 211, sy + 172)
            PotionMotionPlayer.save_configuration()
            keep_running = False 
    __key_controller.initialize_monitors()
    __key_controller.start_thread()
    while (keep_running):
        time.sleep(0.05)
    __key_controller.stop_thread()
    __key_controller = KeyUtils()
    execute_bot(terminate_bottle = PotionMotionPlayer.BOTTLE_PINK, game_rounds = PotionMotionPlayer.player_settings["constants"]["num_games"])

if (__name__ == "__main__"):
    
    PotionMotionPlayer.initialize()
    
    n = 4
    
    if (n == 1):
    
        keep_running = True
        
        @__key_controller.monitor(KeyUtils.Key.KEY_ESC)
        def monitor_terminate(key_code : int, key_pressed : bool) -> None:
            global keep_running
            if (key_pressed):
                keep_running = False 
                
        __key_controller.initialize_monitors()
        
        __key_controller.start_thread()
        
        while (keep_running):
                
            matrix = PotionMotionPlayer.screenshot2matrix(PotionMotionPlayer._take_screenshot())
            
            print(matrix)
            
            next_move = PotionMotion.find_optimal_move(matrix)
            
            print(next_move)
            
            scroll(
                PotionMotionPlayer.POTION_GRID["coord"], 
                PotionMotionPlayer.POTION_GRID["slot"], 
                PotionMotionPlayer.POTION_SIZE, 
                next_move
            )
            
            time.sleep(0.75)
            
        __key_controller.stop_thread()
        
        __key_controller = KeyUtils()
        
    elif (n == 2):
        
        (x, y) = PotionMotionPlayer.configure_grid_coord()
        
        print(x, y)
        
    elif (n == 3):
        
        main()
        
    elif (n == 4):
        
        main2()