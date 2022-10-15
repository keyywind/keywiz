from typing import Union, Tuple, List, Type
import tesserocr, pyautogui, datetime, numpy, json, sys, cv2, PIL, os, gc

from keyio.windowutils import WindowUtils 
from keyio.mouseutils import MouseUtils 
from keyio.keyutils import KeyUtils 

from keywizardUtilities.bazaar_utils.bot_utils import DigitUtils, BotUtils

os.environ['OMP_THREAD_LIMIT'] = '2'

class WizardBot:
    
    settings_name     = os.path.join(os.path.join(os.path.dirname(__file__), "keywizardConfig"), "bazaar_config.json")
    
    farmer_settings   = None
    
    window_controller = None
    
    mouse_controller  = None
    
    key_controller    = None
    
    MAX_ITEM_NUMS     = 10
    
    @classmethod 
    def _initialize_farmer_settings(class_) -> Type[ "WizardBot" ]:
        class_.farmer_settings = {
            "bounding_boxes" : {
                "window"          : [   6,  30, 800, 600 ],
                "reagent"         : [ 100, 120,  55,  55 ],
                "buy_more"        : [ 135, 470, 115,  25 ],
                "next_page"       : [ 564, 443,  35,  35 ],
                "next_tab"        : [ 653, 122,  50,  50 ],
                "loading"         : [ 334, 274, 122,  33 ],
                "sect_name"       : [ 292, 206, 220, 230 ],
                "sect_quantity"   : [ 513, 206,  46, 230 ],
                "confirm_buy"     : [ 268, 456, 100,  25 ],
                "quantity_bar"    : [ 405, 345, 130,  25 ],
                "confirm_receipt" : [ 463, 345, 100,  40 ]
            },
            "color_thresh" : {
                "black_text"      : [ [ 000, 000, 175 ], [ 157, 255, 255 ] ],
                "yellow_text"     : [ [  30, 219, 148 ], [  30, 255, 255 ] ],
                "yellow_text_inv" : [ [  30, 219, 148 ], [  30, 255, 255 ] ],
                "red_text"        : [ [ 000, 195, 145 ], [  14, 243, 230 ] ]
            },
            "constants" : {
                "LCS_thresh"     : 0.78,
                "empty_timeout"  :    5,
                "retry_patience" :    3,
                "gc_interval"    :   10
            },
            "reagents" : [
                [ "SYNTHONIUM",        0 ],
                [ "OLD ONE ARTIFACTS", 0 ],
                [ "BLUEPRINT TOKEN",   0 ],
                [ "PLATINUM",          0 ],
                [ "FLYING SQUID INK",  0 ],
                [ "DIAMOND",           0 ],
                [ "NIGHTSHADE",        0 ],
                [ "IRIDIUM",           0 ],
                [ "AGAVE NECTAR",      0 ],
                [ "STAR IRON",         0 ],
                [ "SHARK TOOTH",       0 ],
                [ "STEEL",             0 ],
                [ "BLOOD MOSS",        0 ],
                [ "GRENDELWEED",       2 ],
                [ "STONE BLOCK",      10 ],
                [ "AGAVE LEAVES",      2 ],
                [ "SANDSTONE",        10 ],
                [ "RED MANDRAKE",     10 ],
                [ "FROST FLOWER",     10 ],
                [ "ORE",              20 ],
                [ "BLACK LOTUS",      20 ],
                [ "DEEP MUSHROOM",    20 ],
                [ "MIST WOOD",        20 ]
            ]
        }
        
    @classmethod 
    def save_settings(class_) -> Type[ "WizardBot" ]:
        with open(class_.settings_name, "w") as write_file:
            write_file.write(json.dumps(class_.farmer_settings, indent = 4))
        return class_ 
    
    @classmethod 
    def pad_string(class_, string : str, length : int = 50) -> str:
        str_len = len(string)
        return string + " " * (length - str_len)
        
    @classmethod 
    def initialize_bot(class_) -> Type[ "WizardBot" ]:
        
        def load_settings() -> None:
            nonlocal class_ 
            with open(class_.settings_name, "r") as read_file:
                class_.farmer_settings = json.loads(read_file.read())
                
        def save_settings() -> None:
            nonlocal class_ 
            class_.save_settings()
            
        if (os.path.isfile(class_.settings_name)):
            load_settings()
        else:
            class_._initialize_farmer_settings()
            save_settings()
        
        class_.tess_api                 = tesserocr.PyTessBaseAPI(oem = tesserocr.OEM.LSTM_ONLY, psm = 6)
        class_.tess_api.SetVariable("tessedit_char_whitelist", 
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' ")
        
        class_.window_controller        = WindowUtils()
        class_.mouse_controller         = MouseUtils()
        class_.key_controller           = KeyUtils() 
        
        KeyUtils.configure_quantum(0, True)
        
        os.system("title Keywizard Bazaar Farmer")
        os.system("color 1f")
        os.system("mode 100")
        os.system("cls")
        
        print("")
        sys.stdout.write(class_.pad_string("\r[ Press F8 to confirm selected window ]"))
        sys.stdout.flush()
        
        keep_running = True 
        @class_.key_controller.monitor(KeyUtils.Key.KEY_F8)
        def monitor_F8(key_code : int, key_pressed : bool):
            nonlocal keep_running, class_ 
            if (key_pressed):
                (sx, sy, ex, ey) = class_.window_controller.get_foreground_window()
                sy               = sy + 30
                class_.farmer_settings["bounding_boxes"]["window"] = [ sx, sy, 800, 600 ]
                keep_running = False 
        class_.key_controller.initialize_monitors()
        class_.key_controller.start_thread()
        while (keep_running):
            class_.sleep(0.10)
        class_.key_controller.stop_thread()
        
        sys.stdout.write(class_.pad_string("\r[ Window Selected ]"))
        sys.stdout.flush()
        print("\n")
        
        class_.key_controller           = KeyUtils() 
        
        class_.next_tab_box             = class_.get_abs_box(class_.farmer_settings["bounding_boxes"]["window"], class_.farmer_settings["bounding_boxes"]["next_tab"])
        class_.reagent_box              = class_.get_abs_box(class_.farmer_settings["bounding_boxes"]["window"], class_.farmer_settings["bounding_boxes"]["reagent"])
        class_.loading_box              = class_.get_abs_box(class_.farmer_settings["bounding_boxes"]["window"], class_.farmer_settings["bounding_boxes"]["loading"])
        class_.item_name_box            = class_.get_abs_box(class_.farmer_settings["bounding_boxes"]["window"], class_.farmer_settings["bounding_boxes"]["sect_name"])
        class_.item_name_boxes          = class_.unpack_vertical_boxes(class_.item_name_box)
        class_.next_page_box            = class_.get_abs_box(class_.farmer_settings["bounding_boxes"]["window"], class_.farmer_settings["bounding_boxes"]["next_page"])
        class_.item_quantity_box        = class_.get_abs_box(class_.farmer_settings["bounding_boxes"]["window"], class_.farmer_settings["bounding_boxes"]["sect_quantity"])
        class_.item_quantity_boxes      = class_.unpack_vertical_boxes(class_.item_quantity_box)
        class_.buy_more_box             = class_.get_abs_box(class_.farmer_settings["bounding_boxes"]["window"], class_.farmer_settings["bounding_boxes"]["buy_more"])
        class_.quantity_bar_box         = class_.get_abs_box(class_.farmer_settings["bounding_boxes"]["window"], class_.farmer_settings["bounding_boxes"]["quantity_bar"])
        class_.confirm_buy_box          = class_.get_abs_box(class_.farmer_settings["bounding_boxes"]["window"], class_.farmer_settings["bounding_boxes"]["confirm_buy"])
        class_.confirm_receipt_box      = class_.get_abs_box(class_.farmer_settings["bounding_boxes"]["window"], class_.farmer_settings["bounding_boxes"]["confirm_receipt"])
        
        class_.next_tab_centroid        = class_.get_centroid(class_.next_tab_box)
        class_.reagent_centroid         = class_.get_centroid(class_.reagent_box)
        class_.item_name_centroids      = numpy.stack([ class_.get_centroid(bbox) for bbox in class_.item_name_boxes  ])
        class_.next_page_centroid       = class_.get_centroid(class_.next_page_box)
        class_.item_quant_centroids     = numpy.stack([ class_.get_centroid(bbox) for bbox in class_.item_quantity_boxes  ])
        class_.sort_quant_centroid      = (class_.item_quant_centroids[0][0], class_.item_quant_centroids[0][1] - class_.item_quantity_boxes[0][3])
        class_.buy_more_centroid        = class_.get_centroid(class_.buy_more_box)  
        class_.confirm_buy_centroid     = class_.get_centroid(class_.confirm_buy_box)
        class_.confirm_receipt_centroid = class_.get_centroid(class_.confirm_receipt_box)
        
        class_.color_text_thresh        = class_.farmer_settings["color_thresh"]
        
        class_.screenshot_colored       = None
        class_.screenshot_black         = None
        class_.screenshot_yellow        = None
        class_.screenshot_yellow_inv    = None
        class_.screenshot_red           = None
        
        class_.item_name_bounds         = None 
        
        class_.wanted_item_names        = [  item[0] for item in class_.farmer_settings["reagents"]  ]
        class_.wanted_item_quantities   = [  item[1] for item in class_.farmer_settings["reagents"]  ]
        
    @classmethod 
    def get_item_names(class_, item_name_images : numpy.ndarray) -> List[ str ]:
        def crop_boundary(image : numpy.ndarray, sx : int, ex : int, dx : int = 5) -> numpy.ndarray:
            return image[ : , sx - dx : ex + dx ]
        image_names = []
        for i, image in enumerate(item_name_images):
            __image   = crop_boundary(image, * class_.item_name_bounds[i])
            class_.tess_api.SetImage(PIL.Image.fromarray(__image))
            __predict = class_.tess_api.GetUTF8Text()
            image_names.append(__predict)
        return image_names 
        
    @classmethod 
    def set_name_bounds(class_, name_image_list : numpy.ndarray) -> Type[ "WizardBot" ]:
        class_.item_name_bounds = BotUtils.get_multiple_boundary(name_image_list)
        return class_ 
        
    @classmethod 
    def unpack_vertical_boxes(class_, bounding_box : Tuple[ int, int, int, int ]) -> numpy.ndarray:
        bounding_boxes = []
        height_step    = int(bounding_box[3] / class_.MAX_ITEM_NUMS)
        for dy in range(0, bounding_box[3], height_step):
            bounding_boxes.append((bounding_box[0], bounding_box[1] + dy, bounding_box[2], height_step))
        return numpy.stack(bounding_boxes)
        
    @classmethod 
    def get_abs_box(class_, base_box : Tuple[ int, int, int, int ], child_box : Tuple[ int, int, int, int ]) -> Tuple[ int, int, int, int ]:
        (x, y, w, h) = child_box 
        return (
            int(base_box[0] + x), int(base_box[1] + y), int(w), int(h)    
        )
        
    @classmethod 
    def sleep(class_, sleep_duration : Union[ float, int ]) -> Type[ "WizardBot" ]:
        DT  = datetime.datetime 
        SOT = DT.now()
        while ((DT.now() - SOT).total_seconds() <= sleep_duration):
            pass
        return class_ 
    
    @classmethod 
    def get_centroid(class_, bounding_box : Tuple[ int, int, int, int ]) -> Tuple[ int, int ]:
        (x, y, w, h) = bounding_box
        return (
            int(x + w // 2),
            int(y + h // 2)
        )
        
    @classmethod 
    def talk_bazaar(class_) -> Type[ "WizardBot" ]:
        class_.key_controller.press_key(KeyUtils.KeyCode.CHAR_X)
        class_.sleep(0.10)
        class_.key_controller.release_key(KeyUtils.KeyCode.CHAR_X)
        return class_ 
    
    @classmethod 
    def click_coord(class_, coordinates : Tuple[ int, int ]) -> Type[ "WizardBot" ]:
        (x, y) = coordinates 
        class_.mouse_controller.set_mouse_coord(x + 5, y)
        class_.sleep(0.05)
        class_.mouse_controller.set_mouse_coord(x, y)
        class_.mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
        class_.sleep(0.10)
        class_.mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
        return class_ 
    
    @classmethod 
    def click_next_tab(class_) -> Type[ "WizardBot" ]:
        (x, y) = class_.next_tab_centroid 
        class_.click_coord((x, y))
        return class_ 
    
    @classmethod 
    def goto_reagent_tab(class_) -> Type[ "WizardBot" ]:
        for _ in range(3):
            class_.click_next_tab()
            class_.sleep(0.20)
        return class_ 
    
    @classmethod 
    def refresh_reagents(class_) -> Type[ "WizardBot" ]:
        (x, y) = class_.reagent_centroid 
        class_.click_coord((x, y))
        return class_ 
    
    @classmethod 
    def crop_image(class_, image : numpy.ndarray, bounding_box : Tuple[ int, int, int, int ]) -> numpy.ndarray:
        (x, y, w, h) = bounding_box 
        return image[ y : y + h, x : x + w ]
    
    @classmethod 
    def screenshot(class_) -> numpy.ndarray:
        return cv2.cvtColor(numpy.uint8(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
    
    @classmethod 
    def thresh_colors(class_, image : numpy.ndarray, thresh_bounds : List[ Tuple[ Tuple[ int, int, int ], Tuple[ int, int, int ] ] ]) -> numpy.ndarray:
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        return numpy.stack([
            cv2.inRange(hsv_image, tuple(thresh_bounds[i][0]), tuple(thresh_bounds[i][1])) for i in range(thresh_bounds.__len__())  
        ])
    
    @classmethod 
    def update_screenshot(class_) -> Type[ "WizardBot" ]:
        class_.screenshot_colored = class_.screenshot()
        (class_.screenshot_black, class_.screenshot_yellow, class_.screenshot_yellow_inv, class_.screenshot_red) = class_.thresh_colors(
            class_.screenshot_colored, list(class_.color_text_thresh.values())
        )
        class_.screenshot_yellow_inv = cv2.bitwise_not(class_.screenshot_yellow_inv)
        return class_ 
    
    @classmethod 
    def is_loading(class_) -> bool:
        image = PIL.Image.fromarray(class_.crop_image(class_.screenshot_black, class_.loading_box))
        class_.tess_api.SetImage(image)
        text  = class_.tess_api.GetUTF8Text()
        load  = ("load" in text.lower())
        return load 
    
    @classmethod 
    def is_page_empty(class_) -> bool:
        return (class_.item_name_bounds.__len__() < 1)
    
    @classmethod 
    def more_pages_available(class_) -> bool:
        return numpy.any(class_.crop_image(class_.screenshot_red, class_.next_page_box))
    
    @classmethod 
    def click_next_page(class_) -> Type[ "WizardBot" ]:
        class_.click_coord(class_.next_page_centroid)
        class_.mouse_controller.set_mouse_coord(*class_.reagent_centroid)
        return class_ 
    
    @classmethod 
    def click_sort_quantity(class_) -> Type[ "WizardBot" ]:
        class_.click_coord(class_.sort_quant_centroid)
        return class_ 
    
    @classmethod 
    def get_wanted_indices(class_, item_name_list : List[ str ]) -> List[ Tuple[ int, int ] ]:
        item_name_list = [  "".join(filter(lambda x : x.isalnum(), string.upper())) for string in item_name_list  ]
        return BotUtils.select_items_by_name(class_.wanted_item_names, item_name_list, class_.farmer_settings["constants"]["LCS_thresh"])
    
    @classmethod 
    def get_wanted_quantities(class_, item_indices : List[ Tuple[ int, int ] ]) -> List[ int ]:
        indices          = [  item_index[1] for item_index in item_indices  ]
        quantity_regions = [
            class_.crop_image(class_.screenshot_yellow, class_.item_quantity_boxes[index])
                for index in indices 
        ]
        return [
            DigitUtils.image_to_integer(image) for image in quantity_regions 
        ]
    
    @classmethod 
    def get_wanted_indices_part2(class_, quantity_wanted : List[ int ], quantity_found : List[ int ], indices_found : List[ int ]) -> List[ int ]:
        return BotUtils.select_items_by_quantity(quantity_wanted, quantity_found, indices_found)
    
    @classmethod 
    def click_selected_item(class_, item_index : int) -> Type[ "WizardBot" ]:
        coordinates = class_.item_name_centroids[item_index]
        class_.click_coord(coordinates)
        return class_ 
    
    @classmethod 
    def click_buy_more(class_) -> Type[ "WizardBot" ]:
        coordinates = class_.buy_more_centroid 
        class_.click_coord(coordinates)
        return class_ 
    
    @classmethod 
    def click_confirm_buy(class_) -> Type[ "WizardBot" ]:
        coordinates = class_.confirm_buy_centroid 
        class_.click_coord(coordinates)
        return class_ 
    
    @classmethod 
    def click_confirm_receipt(class_) -> Type[ "WizardBot" ]:
        coordinates = class_.confirm_receipt_centroid
        class_.click_coord(coordinates)
        return class_ 
    
    @classmethod 
    def maximize_quantity(class_) -> Type[ "WizardBot" ]:
        (x, y, w, h) = class_.quantity_bar_box 
        (start_x, start_y) = (x, y + h // 2)
        (stop_x, stop_y)   = (x + w, y + h // 2)
        (dx, dy)           = (stop_x - start_x, stop_y - start_y)
        class_.mouse_controller.set_mouse_coord(start_x - 5, start_y)
        class_.sleep(0.01)
        class_.mouse_controller.press_button(MouseUtils.LEFT_BUTTON)
        for i in range(21):
            cx = start_x + int(dx * i / 20)
            cy = start_y + int(dy * i / 20)
            class_.mouse_controller.set_mouse_coord(cx, cy)
            class_.sleep(0.01)
        class_.sleep(0.01)
        class_.mouse_controller.release_button(MouseUtils.LEFT_BUTTON)
        return class_ 
    
    @classmethod 
    def confirm_present(class_) -> bool:
        image_region = class_.crop_image(class_.screenshot_yellow_inv, class_.confirm_receipt_box)
        class_.tess_api.SetImage(PIL.Image.fromarray(image_region))
        text         = class_.tess_api.GetUTF8Text()
        return ("ok" in text.lower())
    
    @classmethod 
    def item_affordable(class_) -> bool:
        buy_more_region = class_.crop_image(class_.screenshot_yellow, class_.buy_more_box)
        return numpy.any(buy_more_region)
    
    @classmethod 
    def purchase_reagents(class_) -> Type[ "WizardBot" ]:
        
        keep_running = True 
        
        @class_.key_controller.monitor(KeyUtils.Key.KEY_F10)
        def monitor_exit(*args):
            nonlocal keep_running
            keep_running = False 
            
        class_.key_controller.initialize_monitors()
        
        class_.key_controller.start_thread()
        
        class_.talk_bazaar()
        
        class_.sleep(0.30)
        
        class_.goto_reagent_tab()
        
        gc_counter = 0
        
        while (keep_running):
            
            if ((gc_counter + 1) % (class_.farmer_settings["constants"]["gc_interval"]) == 0):
                gc.collect()
                gc_counter = 0
            else:
                gc_counter += 1
            
            class_.sleep(0.30)
            
            SOT_EMPTY = SOT_EXIT = datetime.datetime.now()
            
            while True:
                
                if (keep_running == False):
                    class_.key_controller.stop_thread()
                    return class_ 
                
                class_.update_screenshot()
                
                NAME_IMAGE_LIST = numpy.stack([  class_.crop_image(class_.screenshot_yellow, bounding_box) for bounding_box in class_.item_name_boxes  ])
                
                class_.set_name_bounds(NAME_IMAGE_LIST)
                
                if (class_.is_loading()):
                    SOT_EMPTY = SOT_EXIT = datetime.datetime.now()
                    
                elif (class_.is_page_empty()):
                    if ((datetime.datetime.now() - SOT_EMPTY).total_seconds() >= class_.farmer_settings["constants"]["empty_timeout"]):
                        REFRESH = True 
                        break 
                    
                else:
                    if ((datetime.datetime.now() - SOT_EXIT).total_seconds() >= 0.10):
                        REFRESH = False 
                        break 
                    
                class_.sleep(0.01)
            
            if (keep_running == False):
                class_.key_controller.stop_thread()
                return class_ 
            
            if (REFRESH == False):
                
                class_.update_screenshot()
                
                MORE_PAGES = class_.more_pages_available()
                
                if (MORE_PAGES):
                    class_.click_sort_quantity()
                    class_.sleep(0.01)
                
                if (keep_running == False):
                    class_.key_controller.stop_thread()
                    return class_ 
                
                previous_indices = []
                item_patience    = class_.farmer_settings["constants"]["retry_patience"]
                
                while True:
                    
                    class_.sleep(0.05)
                    
                    class_.update_screenshot()
                        
                    NAME_IMAGE_LIST = numpy.stack([  
                        class_.crop_image(class_.screenshot_yellow, bounding_box) 
                            for bounding_box in class_.item_name_boxes  ])
                    
                    class_.set_name_bounds(NAME_IMAGE_LIST)
                    
                    NAME_IMAGE_LIST = numpy.stack([  
                        class_.crop_image(class_.screenshot_yellow_inv, bounding_box) 
                            for bounding_box in class_.item_name_boxes  ])[:class_.item_name_bounds.__len__()]
                    
                    ITEM_NAME_LIST  = class_.get_item_names(NAME_IMAGE_LIST)
                    
                    ITEM_LIST       = class_.get_wanted_indices(ITEM_NAME_LIST)
                    
                    if (ITEM_LIST.__len__()):
                        
                        ITEM_QUANTITIES = class_.get_wanted_quantities(ITEM_LIST)
                        
                        WANT_L, FOUND_L = zip(*ITEM_LIST)
                        
                        WANT_L, FOUND_L = list(WANT_L), list(FOUND_L)
                        
                        WANTED_QUANT    = [  class_.wanted_item_quantities[i] for i in WANT_L  ]
                        
                        FIN_ITEM_LIST   = class_.get_wanted_indices_part2(WANTED_QUANT, ITEM_QUANTITIES, FOUND_L)
                        
                        if (FIN_ITEM_LIST.__len__()):
                        
                            FIN_INDEX = -1
                            
                            for index in FIN_ITEM_LIST:
                                if (index in previous_indices):
                                    if (item_patience > 0):
                                        FIN_INDEX = index 
                                        item_patience -= 1
                                        break 
                                else:
                                    FIN_INDEX = index 
                                    break 
                                
                            if (FIN_INDEX != -1):
                                
                                previous_indices.append(FIN_INDEX)
                                
                                class_.click_selected_item(FIN_INDEX)
                                
                                class_.sleep(0.05)
                                
                                class_.update_screenshot()
                                
                                if (class_.item_affordable()):
                                                                    
                                    class_.click_buy_more()
                                    
                                    class_.sleep(0.01)
                                    
                                    for index, (wanted_index, found_index) in enumerate(ITEM_LIST):
                                        if (found_index == FIN_INDEX):
                                            FIN_QUANTITY = ITEM_QUANTITIES[index]
                                            break 
                                    
                                    if (FIN_QUANTITY > 1):
                                        class_.maximize_quantity()
                                        class_.sleep(0.01)
                                        
                                    class_.click_confirm_buy()
                                    
                                    SOT_EXIT = datetime.datetime.now()
                                    
                                    while True:
                                        
                                        class_.update_screenshot()
                                        
                                        if (class_.confirm_present()):
                                            if ((datetime.datetime.now() - SOT_EXIT).total_seconds() >= 0.05):
                                                break 
                                        else:
                                            SOT_EXIT = datetime.datetime.now() 
                                        
                                        class_.sleep(0.01)
                                        
                                    class_.click_confirm_receipt()
                                    
                                class_.mouse_controller.set_mouse_coord(*class_.reagent_centroid)
                                
                            else:
                                
                                if (keep_running == False):
                                    class_.key_controller.stop_thread()
                                    return class_ 
                                
                                class_.sleep(0.01)
                                            
                                class_.update_screenshot()
                                            
                                if (class_.more_pages_available()):
                                    class_.click_next_page()
                                    class_.mouse_controller.set_mouse_coord(*class_.reagent_centroid)
                                    
                                    previous_indices = []
                                    item_patience    = class_.farmer_settings["constants"]["retry_patience"]
                                else:
                                    break 
                                
                        else:
                            
                            if (keep_running == False):
                                class_.key_controller.stop_thread()
                                return class_ 
                            
                            class_.sleep(0.01)
                                        
                            class_.update_screenshot()
                                        
                            if (class_.more_pages_available()):
                                class_.click_next_page()
                                class_.mouse_controller.set_mouse_coord(*class_.reagent_centroid)
                                
                                previous_indices = []
                                item_patience    = class_.farmer_settings["constants"]["retry_patience"]
                            else:
                                break 
                        
                    else:
                        
                        if (keep_running == False):
                            class_.key_controller.stop_thread()
                            return class_ 
                        
                        class_.sleep(0.01)
                                    
                        class_.update_screenshot()
                                    
                        if (class_.more_pages_available()):
                            class_.click_next_page()
                            class_.mouse_controller.set_mouse_coord(*class_.reagent_centroid)
                            
                            previous_indices = []
                            item_patience    = class_.farmer_settings["constants"]["retry_patience"]
                        else:
                            break 
                
            class_.refresh_reagents()
        
        class_.key_controller.stop_thread() 
        
        return class_ 


if (__name__ == "__main__"):
    
    n = 1
    
    if (n == 1):
                
        WizardBot.initialize_bot()
        
        WizardBot.purchase_reagents()