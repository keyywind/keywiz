from typing import Union, Tuple, Type
import pyautogui, tesserocr, datetime, numpy, time, json, sys, cv2, PIL, os

from keyio.windowutils import WindowUtils
from keyio.mouseutils import MouseUtils
from keyio.keyutils import KeyUtils 

class GearSeller:
    
    SLEEP_PREEMPTIVE           = True 
    
    PAD_LENGTH                 = 45
    
    CONFIG_FOLDER_NAME         = "keywizardConfig"
    
    window_controller          = WindowUtils()
    mouse_controller           = MouseUtils()
    key_controller             = KeyUtils()
    
    auction_settings_filename  = os.path.join(os.path.join(os.path.dirname(__file__), CONFIG_FOLDER_NAME), "seller_config.json")
    
    auction_settings           = None
    window_start_coord         = None 
    
    box_window                 = None 
    box_section_sell           = None
    box_section_sell_bank      = None 
    box_section_gear           = None
    box_section_item           = None 
    box_button_sell            = None
    box_button_next_page       = None 
    box_button_next_tab        = None
    box_button_exit            = None
    box_button_sell_yes        = None
    box_button_sell_no         = None
    box_quantity_items         = None
    
    coord_section_sell         = None
    coord_section_sell_bank    = None 
    coord_section_gear         = None
    coord_section_item         = None 
    coord_button_sell          = None
    coord_button_next_page     = None
    coord_button_next_tab      = None 
    coord_button_exit          = None
    coord_button_sell_yes      = None
    coord_button_sell_no       = None 
    
    screenshot_base            = None
    screenshot_background      = None
    screenshot_next_page       = None 
    screenshot_yellow_text     = None 
    screenshot_select_color    = None 
    
    counter_sect               = None 
    counter_tab                = None
    counter_page               = None 
    counter_item               = None 
    
    tesseract_api              = None 
    
    @staticmethod 
    def divide_bounding_box(bounding_box : Tuple[ int, int, int, int ], sections : int, axis : int = 1) -> numpy.ndarray: 
        (x, y, w, h) = bounding_box 
        if (axis == 1):
            d = w / sections 
            return numpy.stack([
                (x + int(d * u), y, int(d), h) for u in range(sections)
            ])
        else:
            d = h / sections 
            return numpy.stack([
                (x, y + int(d * u), w, int(d)) for u in range(sections)
            ])
    
    @staticmethod 
    def sleep(sleep_time : Union[ float, int ], preemptive : bool = True) -> bool:
        if (preemptive):
            time.sleep(sleep_time)
        else:
            SOT = datetime.datetime.now()
            while ((datetime.datetime.now() - SOT).total_seconds() <= sleep_time):
                pass 
        return preemptive 
    
    @classmethod 
    def _set_screenshots(class_) -> Type[ "GearSeller" ]:
        class_.screenshot_base       = cv2.cvtColor(cv2.cvtColor(numpy.uint8(pyautogui.screenshot()), cv2.COLOR_RGB2BGR), cv2.COLOR_BGR2HSV)
        
        temp                         = class_.auction_settings["color-hsv-range"]["section-item"]
        class_.screenshot_background = cv2.inRange(class_.screenshot_base, tuple(temp["threshold"][0]), tuple(temp["threshold"][1]))
        if (temp["morphology"].__len__()):
            for morph_type, struct_shape, iters in temp["morphology"]:
                SE = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, tuple(struct_shape))
                morph_type = ((cv2.dilate) if (morph_type == "D") else (cv2.erode))
                class_.screenshot_background = morph_type(class_.screenshot_background, SE, iterations = iters)
            
        temp                        = class_.auction_settings["color-hsv-range"]["button-next-page"]
        class_.screenshot_next_page = cv2.inRange(class_.screenshot_base, tuple(temp["threshold"][0]), tuple(temp["threshold"][1]))
        if (temp["morphology"].__len__()):
            for morph_type, struct_shape, iters in temp["morphology"]:
                SE = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, tuple(struct_shape))
                morph_type = ((cv2.dilate) if (morph_type == "D") else (cv2.erode))
                class_.screenshot_next_page = morph_type(class_.screenshot_next_page, SE, iterations = iters)
                
        temp                          = class_.auction_settings["color-hsv-range"]["yellow-text"]
        class_.screenshot_yellow_text = cv2.inRange(class_.screenshot_base, tuple(temp["threshold"][0]), tuple(temp["threshold"][1]))
        if (temp["morphology"].__len__()):
            for morph_type, struct_shape, iters in temp["morphology"]:
                SE = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, tuple(struct_shape))
                morph_type = ((cv2.dilate) if (morph_type == "D") else (cv2.erode))
                class_.screenshot_yellow_text = morph_type(class_.screenshot_yellow_text, SE, iterations = iters)
                
        temp                           = class_.auction_settings["color-hsv-range"]["select-color"]
        class_.screenshot_select_color = cv2.inRange(class_.screenshot_base, tuple(temp["threshold"][0]), tuple(temp["threshold"][1]))
        if (temp["morphology"].__len__()):
            for morph_type, struct_shape, iters in temp["morphology"]:
                SE = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, tuple(struct_shape))
                morph_type = ((cv2.dilate) if (morph_type == "D") else (cv2.erode))
                class_.screenshot_select_color = morph_type(class_.screenshot_select_color, SE, iterations = iters)
        return class_ 
    
    @classmethod 
    def tab_selected(class_, tab_index : int) -> bool:
        (*_, w, h) = box = class_.box_section_gear[tab_index]
        src_region         = class_.crop_region(class_.screenshot_select_color, box)
        SE                 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (h, h))
        mask               = numpy.ones(shape = (h, w), dtype = numpy.uint8) * 255
        sx                 = (w - h) // 2
        mask[:, sx:sx+h ]  = SE
        dst_region         = cv2.bitwise_and(src_region, mask)
        return ((numpy.sum(dst_region != 0) / numpy.sum(mask != 0)) <= class_.auction_settings["constants"]["select-thresh"])
    
    @staticmethod
    def crop_region(src_image : numpy.ndarray, bounding_box : Union[ numpy.ndarray, Tuple[ int, int, int, int ]]) -> numpy.ndarray:
        (x, y, w, h) = bounding_box 
        return src_image[ y : y + h, x : x + w ]
    
    @classmethod 
    def _initialize_window_coord(class_, window_start_coord : Union[ type(None), Tuple[ int, int ] ] = None) -> Type[ "GearSeller" ]:
        if (window_start_coord is None):
            
            print("")
            
            sys.stdout.write(class_.pad_string("\r[ Press F8 to confirm window ]", class_.PAD_LENGTH))
            sys.stdout.flush()
            
            keep_running = True 
            @class_.key_controller.monitor(KeyUtils.Key.KEY_F8)
            def monitor_set(key_code : int, key_pressed : bool) -> None:
                nonlocal keep_running, class_ 
                if ((keep_running) and (key_pressed)):
                    window_coord = class_.window_controller.get_foreground_window()
                    class_.window_start_coord = (window_coord[0], window_coord[1] + 30)
                    class_.box_window = (*class_.window_start_coord, 800, 600)
                    keep_running = False 
            class_.key_controller.initialize_monitors()
            class_.key_controller.start_thread()
            while (keep_running):
                class_.sleep(0.25, class_.SLEEP_PREEMPTIVE)
            class_.key_controller.stop_thread()
            class_.key_controller = KeyUtils() 
            
            sys.stdout.write(class_.pad_string("\r[ Window Selected ]", class_.PAD_LENGTH))
            sys.stdout.flush()
            
            print("")
            
        else:
            class_.window_start_coord = tuple( u for u in window_start_coord )
        return class_ 
    
    @classmethod 
    def _initialize_settings(class_) -> Type[ "GearSeller" ]:
        class_.auction_settings = {
            "bounding-boxes" : {
                "section-sell"      : [ 193,  58,  80,  40 ],
                "section-sell-bank" : [ 279,  56, 165,  40 ],
                "section-gear"      : [  95, 123, 490,  50 ],
                "section-item"      : [ 445, 190, 215, 288 ],
                "button-sell"       : [ 186, 410, 115,  25 ],
                "button-next-page"  : [ 670, 299,  33,  70 ],
                "button-next-tab"   : [ 654, 122,  50,  50 ],
                "button-exit"       : [ 667, 489,  40,  40 ],
                "button-sell-yes"   : [ 355, 358, 100,  25 ],
                "button-sell-no"    : [ 460, 358, 100,  25 ],
                "quantity-items"    : [ 138, 500, 115,  25 ]
            },
            "color-hsv-range" : {
                "section-item" : {
                    "threshold"  : [ [ 163, 206,  70], [ 180, 255, 203 ] ],
                    "morphology" : [ [ "D", [ 3, 3 ], 1 ] ]
                },
                "button-next-page" : {
                    "threshold"  : [ [   0, 195, 106], [  22, 246, 215 ] ],
                    "morphology" : [ [ "D", [ 4, 4 ], 1 ] ]
                },
                "yellow-text" : {
                    "threshold"  : [ [  26, 246, 218 ], [  33, 255, 255 ] ],
                    "morphology" : []
                },
                "select-color" : {
                    "threshold"  : [ [  51,   0,   1 ], [  68,  20, 255 ] ],
                    "morphology" : [ [ "D", [ 7, 7 ], 2 ] ]
                }
            },
            "constants" : {
                "auction-sections" : [ 0, 1 ],
                "auction-tabs"     : [ 0, 1, 2, 3, 4, 5, 6, 7 ],
                "item-thresh"      : 0.5,
                "select-thresh"    : 0.5
            }
        }
        return class_ 
    
    @staticmethod 
    def get_absolute_box(base_box : Tuple[ int, int, int, int ], ref_box : Tuple[ int, int, int, int ]) -> Tuple[ int, int, int, int ]:
        return (
            ref_box[0] + base_box[0],
            ref_box[1] + base_box[1],
            ref_box[2],
            ref_box[3]
        )
    
    @staticmethod 
    def get_coord(bounding_box : Tuple[ int, int, int, int ]) -> Tuple[ int, int ]:
        (x, y, w, h) = bounding_box 
        return (
            x + w // 2,
            y + h // 2
        )
    
    @classmethod 
    def initialize(class_, window_start_coord : Union[ type(None), Tuple[ int, int ] ] = None) -> Type[ "GearSeller" ]:
        
        os.system("title Keywizard - Gear Auction Off")
        os.system("mode 100")
        os.system("color 1f")
        os.system("cls")
        class_.sleep(0.10, class_.SLEEP_PREEMPTIVE)
        
        if (os.path.isfile(class_.auction_settings_filename)):
            with open(class_.auction_settings_filename, "r", encoding = "utf-8") as read_file:
                class_.auction_settings = json.loads(read_file.read())
        else:
            class_._initialize_settings()
            if (os.path.isdir(class_.CONFIG_FOLDER_NAME) == False):
                os.makedirs(os.path.join(os.path.dirname(__file__), class_.CONFIG_FOLDER_NAME))
            with open(class_.auction_settings_filename, "w", encoding = "utf-8") as write_file:
                write_file.write(json.dumps(class_.auction_settings, indent = 4))
                
        class_._initialize_window_coord(window_start_coord)
        
        class_.box_section_sell           = class_.get_absolute_box(class_.box_window, class_.auction_settings["bounding-boxes"]["section-sell"])
        class_.box_section_sell_bank      = class_.get_absolute_box(class_.box_window, class_.auction_settings["bounding-boxes"]["section-sell-bank"])
        
        class_.box_section_gear           = class_.divide_bounding_box(
            class_.get_absolute_box(class_.box_window, class_.auction_settings["bounding-boxes"]["section-gear"]), sections = 8, axis = 1)
        
        class_.box_section_item           = class_.divide_bounding_box(
            class_.get_absolute_box(class_.box_window, class_.auction_settings["bounding-boxes"]["section-item"]), sections = 8, axis = 0)
        
        class_.box_button_sell            = class_.get_absolute_box(class_.box_window, class_.auction_settings["bounding-boxes"]["button-sell"])
        class_.box_button_next_page       = class_.get_absolute_box(class_.box_window, class_.auction_settings["bounding-boxes"]["button-next-page"])
        class_.box_button_next_tab        = class_.get_absolute_box(class_.box_window, class_.auction_settings["bounding-boxes"]["button-next-tab"])
        class_.box_button_exit            = class_.get_absolute_box(class_.box_window, class_.auction_settings["bounding-boxes"]["button-exit"])
        class_.box_button_sell_yes        = class_.get_absolute_box(class_.box_window, class_.auction_settings["bounding-boxes"]["button-sell-yes"])
        class_.box_button_sell_no         = class_.get_absolute_box(class_.box_window, class_.auction_settings["bounding-boxes"]["button-sell-no"])
        class_.box_quantity_items         = class_.get_absolute_box(class_.box_window, class_.auction_settings["bounding-boxes"]["quantity-items"])
        
        class_.coord_section_sell         = class_.get_coord(class_.box_section_sell)
        class_.coord_section_sell_bank    = class_.get_coord(class_.box_section_sell_bank)
        class_.coord_section_gear         = numpy.stack([ class_.get_coord(each_box) for each_box in class_.box_section_gear ])
        class_.coord_section_item         = numpy.stack([ class_.get_coord(each_box) for each_box in class_.box_section_item ])
        class_.coord_button_sell          = class_.get_coord(class_.box_button_sell)
        class_.coord_button_next_page     = class_.get_coord(class_.box_button_next_page)
        class_.coord_button_next_tab      = class_.get_coord(class_.box_button_next_tab)
        class_.coord_button_exit          = class_.get_coord(class_.box_button_exit)
        class_.coord_button_sell_yes      = class_.get_coord(class_.box_button_sell_yes)
        class_.coord_button_sell_no       = class_.get_coord(class_.box_button_sell_no)
        
        class_.tesseract_api              = tesserocr.PyTessBaseAPI(oem = tesserocr.OEM.LSTM_ONLY, psm = 6)
        class_.tesseract_api.SetVariable("tessedit_char_whitelist", "0123456789/ ")
        
        return class_ 
    
    @classmethod 
    def click_talk_x(class_) -> Type[ "GearSeller" ]:
        class_.key_controller.press_key(KeyUtils.KeyCode.CHAR_X)
        class_.sleep(0.10, class_.SLEEP_PREEMPTIVE)
        class_.key_controller.release_key(KeyUtils.KeyCode.CHAR_X)
        return class_ 
    
    @classmethod 
    def get_remaining_quantity(class_) -> int:
        src_image = class_.crop_region(class_.screenshot_yellow_text, class_.box_quantity_items)
        src_image = cv2.bitwise_not(src_image)
        class_.tesseract_api.SetImage(PIL.Image.fromarray(src_image))
        prediction_result = class_.tesseract_api.GetUTF8Text()
        prediction_result = prediction_result.replace(" ", "")
        prediction_result = prediction_result.split("/")[0]
        return ((int(prediction_result)) if (prediction_result.__len__()) else (-1)) 
    
    @classmethod 
    def click_sell_sect(class_) -> Type[ "GearSeller" ]:
        (x, y) = class_.coord_section_sell 
        class_.mouse_controller.set_mouse_coord(x + 5, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.set_mouse_coord(x, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
        class_.sleep(0.10)
        class_.mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
        return class_ 
    
    @classmethod 
    def click_sell_bank_sect(class_) -> Type[ "GearSeller" ]:
        (x, y) = class_.coord_section_sell_bank 
        class_.mouse_controller.set_mouse_coord(x + 5, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.set_mouse_coord(x, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
        class_.sleep(0.10)
        class_.mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
        return class_ 
    
    @classmethod 
    def click_tab(class_, tab_index : int) -> Type[ "GearSeller" ]:
        (x, y) = class_.coord_section_gear[tab_index]
        class_.mouse_controller.set_mouse_coord(x + 5, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.set_mouse_coord(x, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
        class_.sleep(0.10)
        class_.mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
        return class_ 
    
    @classmethod 
    def click_item(class_, item_index : int) -> Type[ "GearSeller" ]:
        (x, y) = class_.coord_section_item[item_index]
        class_.mouse_controller.set_mouse_coord(x + 5, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.set_mouse_coord(x, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
        class_.sleep(0.10)
        class_.mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
        return class_ 
    
    @classmethod 
    def click_next_page(class_) -> Type[ "GearSeller" ]:
        (x, y) = class_.coord_button_next_page 
        class_.mouse_controller.set_mouse_coord(x + 5, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.set_mouse_coord(x, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
        class_.sleep(0.10)
        class_.mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
        return class_ 
    
    @classmethod 
    def click_sell(class_) -> Type[ "GearSeller" ]:
        (x, y) = class_.coord_button_sell
        class_.mouse_controller.set_mouse_coord(x + 5, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.set_mouse_coord(x, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
        class_.sleep(0.10)
        class_.mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
        return class_ 
    
    @classmethod 
    def click_confirm(class_, yes : bool = True) -> Type[ "GearSeller" ]:
        (x, y) = ((class_.coord_button_sell_yes) if (yes) else (class_.coord_button_sell_no))
        class_.mouse_controller.set_mouse_coord(x + 5, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.set_mouse_coord(x, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
        class_.sleep(0.10)
        class_.mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
        return class_ 
    
    @classmethod 
    def click_exit(class_) -> Type[ "GearSeller" ]:
        (x, y) = class_.coord_button_exit
        class_.mouse_controller.set_mouse_coord(x + 5, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.set_mouse_coord(x, y)
        class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        class_.mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
        class_.sleep(0.10)
        class_.mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
        return class_ 
    
    @staticmethod 
    def pad_string(string : str, length : int) -> str:
        str_len = len(string)
        return string + " " * (length - str_len)
    
    @classmethod 
    def countdown(class_, duration : Union[ float, int ]) -> Type[ "GearSeller" ]:
        print("")
        SOT = datetime.datetime.now()
        while True:
            elapsed   = (datetime.datetime.now() - SOT).total_seconds()
            if (elapsed >= duration):
                break 
            remaining = int(duration - elapsed)
            sys.stdout.write(class_.pad_string("\r[ Starting in {} seconds ]".format(remaining), class_.PAD_LENGTH))
            sys.stdout.flush()
            class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
        sys.stdout.write(class_.pad_string("\r[ Bot Initiated ]", class_.PAD_LENGTH))
        sys.stdout.flush()
        print("\n")
        return class_ 
    
    @classmethod 
    def get_item_quantity(class_) -> int:
        def is_full(src_image : numpy.ndarray) -> bool:
            return ((numpy.sum(src_image == 0) / numpy.prod(src_image.shape[0:2])) >= class_.auction_settings["constants"]["item-thresh"])
        for item_index in range(8):
            src_image = class_.crop_region(class_.screenshot_background, class_.box_section_item[item_index])
            if (is_full(src_image) == False):
                return item_index 
        return 8
    
    @classmethod 
    def more_pages(class_) -> bool:
        def not_empty(src_image : numpy.ndarray) -> bool:
            return numpy.any(src_image == 255)
        src_image = class_.crop_region(class_.screenshot_next_page, class_.box_button_next_page)
        return not_empty(src_image)
    
    @classmethod 
    def confirm_present(class_) -> bool:
        def not_empty(src_image : numpy.ndarray) -> bool:
            return numpy.any(src_image == 255)
        src_image = class_.crop_region(class_.screenshot_yellow_text, class_.box_button_sell_yes)
        return not_empty(src_image)
    
    @classmethod 
    def sell_present(class_) -> bool:
        def not_empty(src_image : numpy.ndarray) -> bool:
            return numpy.any(src_image == 255)
        src_image = class_.crop_region(class_.screenshot_yellow_text, class_.box_button_sell)
        return not_empty(src_image)
    
    @classmethod 
    def update_sect(class_) -> bool:
        num_sects = class_.auction_settings["constants"]["auction-sections"].__len__()
        if (num_sects):
            if (class_.counter_sect is None):
                class_.counter_sect = class_.auction_settings["constants"]["auction-sections"][0]
            else:
                cur_index = class_.auction_settings["constants"]["auction-sections"].index(class_.counter_sect)
                cur_index += 1
                if (cur_index >= num_sects):
                    return False 
                class_.counter_sect = class_.auction_settings["constants"]["auction-sections"][cur_index]
            if (class_.counter_sect == 0):
                class_.click_sell_sect()
            elif (class_.counter_sect == 1):
                class_.click_sell_bank_sect()
            return True 
        else:
            return False 
    
    @classmethod 
    def update_tab(class_, init : bool = False) -> bool:
        num_tabs = class_.auction_settings["constants"]["auction-tabs"].__len__()
        if (num_tabs):
            if ((class_.counter_tab is None) or (init)):
                class_.counter_tab = class_.auction_settings["constants"]["auction-tabs"][0]
            else:
                cur_index = class_.auction_settings["constants"]["auction-tabs"].index(class_.counter_tab)
                cur_index += 1
                if (cur_index >= num_tabs):
                    return False 
                class_.counter_tab = class_.auction_settings["constants"]["auction-tabs"][cur_index]
            class_.click_tab(tab_index = class_.counter_tab)
            return True 
        else:
            return False 
    
    @classmethod 
    def update_page(class_, init : bool = False) -> bool:
        if ((class_.counter_page is None) or (init)):
            class_.counter_page = 0
            return True 
        class_._set_screenshots()
        if (class_.more_pages()):
            class_.counter_page += 1
            class_.click_next_page()
            return True 
        return False 
    
    @classmethod 
    def update_item(class_, init : bool = False) -> bool:
        if ((class_.counter_item is None) or (init)):
            class_.counter_item = 0
            return True 
        class_._set_screenshots()
        num_items  = class_.get_item_quantity()
        item_index = class_.counter_item + 1
        if (item_index >= num_items):
            return False 
        class_.counter_item = item_index 
        class_.click_item(class_.counter_item)
        class_.set_exit_coord()
        return True 
    
    @classmethod 
    def set_exit_coord(class_) -> Type[ "GearSeller" ]:
        (x, y) = class_.coord_button_exit
        class_.mouse_controller.set_mouse_coord(x, y)
        return class_ 

    @classmethod 
    def start_selling(class_) -> Type[ "GearSeller" ]:
        terminate = False 
        @class_.key_controller.monitor(KeyUtils.Key.KEY_F10)
        def monitor_terminate(key_code : int, key_pressed : bool) -> None:
            nonlocal terminate 
            if ((terminate == False) and (key_pressed)):
                terminate = True 
        class_.key_controller.initialize_monitors()
        class_.key_controller.start_thread()
        (init_tab, init_page, init_item) = (True, True, True)
        class_.countdown(3)
        class_.click_talk_x()
        class_.sleep(0.30, class_.SLEEP_PREEMPTIVE)
        while (class_.update_sect()):
            class_.sleep(1.00, class_.SLEEP_PREEMPTIVE)
            init_tab = True 
            while (class_.update_tab(init_tab)):
                init_tab = False 
                class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
                class_._set_screenshots()
                if (class_.tab_selected(class_.counter_tab) == False):
                    if (terminate):
                        class_.click_exit()
                        class_.key_controller.stop_thread()
                        return class_ 
                    continue 
                init_page = True 
                while (class_.update_page(init_page)):
                    init_page = False 
                    class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
                    init_item = True 
                    while (class_.update_item(init_item)):
                        if (terminate):
                            class_.click_exit()
                            class_.key_controller.stop_thread()
                            return class_ 
                        init_item = False 
                        class_.sleep(0.20, class_.SLEEP_PREEMPTIVE)
                        
                        SOT = datetime.datetime.now() 
                        
                        while True:
                            
                            class_._set_screenshots()
                            if (class_.sell_present()):
                                stock = class_.get_remaining_quantity()
                                class_.click_sell()
                                class_.counter_item -= 1
                                SOT = datetime.datetime.now() 
                                while True:
                                    class_._set_screenshots()
                                    if (class_.confirm_present()):
                                        break
                                    elif ((class_.sell_present()) and ((datetime.datetime.now() - SOT).total_seconds() >= 0.50)):
                                        SOT = datetime.datetime.now() 
                                        class_.click_sell()
                                    class_.sleep(0.10, class_.SLEEP_PREEMPTIVE)
                                class_.click_confirm()
                                class_.sleep(0.10, class_.SLEEP_PREEMPTIVE)
                                while True:
                                    class_._set_screenshots()
                                    new_stock = class_.get_remaining_quantity()
                                    if (new_stock == -1):
                                        class_.sleep(1.00, class_.SLEEP_PREEMPTIVE)
                                        break 
                                    elif (new_stock == (stock - 1)):
                                        break 
                                    class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
                                break 
                            elif ((datetime.datetime.now() - SOT).total_seconds() >= 0.75):
                                break 
                            class_.sleep(0.05, class_.SLEEP_PREEMPTIVE)
                            
        class_.click_exit()
        class_.key_controller.stop_thread()
        return class_ 

if (__name__ == "__main__"):
    
    n = 1
    
    if (n == 1):
        
        GearSeller.initialize()
        
        GearSeller.start_selling()